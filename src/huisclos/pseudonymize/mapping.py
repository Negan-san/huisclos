"""Table de correspondance entre jetons et valeurs réelles, et son format JSON (version 1).

Entrées : groupes et occurrences produits par pseudonymize.tokens, ou un fichier JSON.
Sorties : un objet Mapping, sa sérialisation JSON et sa relecture validée.
Place dans le pipeline : produite à la pseudonymisation, relue à la restauration. Elle est
sensible : jamais envoyée au LLM, jamais commitée (principe 5 d'AGENTS.md).
"""

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from huisclos.models import EntityGroup, EntityType, Occurrence, TokenStyle

SCHEMA_NAME = "huisclos-mapping"
SCHEMA_VERSION = 1
SENSITIVE_WARNING = (
    "SENSITIVE: this file links tokens to real identities. Keep it on this computer. "
    "Never send it to an AI tool."
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MappingError(ValueError):
    """Table de correspondance illisible ou incohérente ; le message dit pourquoi."""


@dataclass(frozen=True)
class MappingEntry:
    """Une entité de la table : son jeton, son type, sa forme canonique et ses variantes."""

    token: str
    entity_type: EntityType
    canonical: str
    variants: tuple[str, ...]


@dataclass(frozen=True)
class MappingOccurrence:
    """Un remplacement et ses positions ; None pour les anciennes tables sans positions."""

    token: str
    original: str
    start: int | None = None
    end: int | None = None

    def __post_init__(self) -> None:
        """Refuse une paire de positions incomplète, non entière ou hors ordre."""
        if self.start is None and self.end is None:
            return
        if (
            type(self.start) is not int
            or type(self.end) is not int
            or self.start < 0
            or self.end - self.start != len(self.token)
        ):
            raise MappingError("positions d'occurrence invalides : start et end attendus")


def sha256_of(text: str) -> str:
    """Empreinte SHA-256 (hexadécimale) d'un texte encodé en UTF-8.

    Elle permet de savoir, à la restauration, si le texte reçu est exactement le texte
    pseudonymisé (mode exact de D-10).
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> str:
    """Date et heure courantes en UTC, au format ISO 8601 à la seconde près."""
    return datetime.now(UTC).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Mapping:
    """Table de correspondance d'un document.

    Exemple : Mapping.from_json(mapping.to_json()) == mapping.
    """

    created_at: str
    token_style: TokenStyle
    entities: tuple[MappingEntry, ...]
    occurrences: tuple[MappingOccurrence, ...]
    pseudonymized_sha256: str

    def __post_init__(self) -> None:
        """Refuse une table incohérente : jeton en double, jeton inconnu, empreinte invalide."""
        tokens = [entry.token for entry in self.entities]
        duplicates = sorted({token for token in tokens if tokens.count(token) > 1})
        if duplicates:
            raise MappingError(f"jeton présent plusieurs fois : {', '.join(duplicates)}")
        unknown = sorted({o.token for o in self.occurrences} - set(tokens))
        if unknown:
            raise MappingError(f"occurrence d'un jeton absent des entités : {', '.join(unknown)}")
        if not _SHA256.match(self.pseudonymized_sha256):
            raise MappingError("pseudonymized_sha256 doit être une empreinte SHA-256 hexadécimale")

    @classmethod
    def build(
        cls,
        groups: Sequence[EntityGroup],
        occurrences: Sequence[Occurrence],
        pseudonymized_text: str,
        style: TokenStyle,
        created_at: str | None = None,
    ) -> "Mapping":
        """Construit la table à partir du résultat de la pseudonymisation.

        Paramètres : groups et occurrences, issus de pseudonymize.tokens ;
        pseudonymized_text, le texte à jetons ; style, la forme des jetons ; created_at,
        horodatage imposé (utile aux tests), sinon l'heure UTC courante.
        Valeur retournée : la table, entités dans l'ordre des groupes.
        """
        return cls(
            created_at=created_at or utc_now(),
            token_style=style,
            entities=tuple(
                MappingEntry(g.token, g.entity_type, g.canonical, g.variants) for g in groups
            ),
            occurrences=tuple(
                MappingOccurrence(o.token, o.original, o.start, o.end) for o in occurrences
            ),
            pseudonymized_sha256=sha256_of(pseudonymized_text),
        )

    def to_dict(self) -> dict[str, object]:
        """Représentation conforme au schéma JSON version 1, clés dans l'ordre du schéma."""
        return {
            "schema": SCHEMA_NAME,
            "version": SCHEMA_VERSION,
            "created_at": self.created_at,
            "warning": SENSITIVE_WARNING,
            "token_style": {
                "language": self.token_style.language,
                "open_bracket": self.token_style.open_bracket,
                "close_bracket": self.token_style.close_bracket,
            },
            "entities": [
                {
                    "token": e.token,
                    "type": e.entity_type.value,
                    "canonical": e.canonical,
                    "variants": list(e.variants),
                }
                for e in self.entities
            ],
            "occurrences": [
                {
                    "token": o.token,
                    "original": o.original,
                    **({"start": o.start, "end": o.end} if o.start is not None else {}),
                }
                for o in self.occurrences
            ],
            "pseudonymized_sha256": self.pseudonymized_sha256,
        }

    def to_json(self) -> str:
        """Sérialise la table : UTF-8 lisible (ensure_ascii=False), indentation de 2."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "Mapping":
        """Relit et valide une table au format JSON version 1.

        Paramètre : raw, le contenu du fichier.
        Valeur retournée : la table.
        Lève MappingError si le JSON est illisible, si le schéma ou la version ne
        correspondent pas, si un champ manque, si un type est inconnu ou si un jeton est
        en double.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise MappingError(f"le fichier n'est pas un JSON valide ({error.msg})") from error
        if not isinstance(data, dict):
            raise MappingError("le fichier doit contenir un objet JSON")
        if data.get("schema") != SCHEMA_NAME:
            raise MappingError(f"schéma inattendu : {data.get('schema')!r}, {SCHEMA_NAME} attendu")
        version = data.get("version")
        if type(version) is not int or version != SCHEMA_VERSION:
            raise MappingError(f"version non prise en charge : {version!r}")
        return cls(
            created_at=_read_created_at(data),
            token_style=_read_style(_field(data, "token_style", dict)),
            entities=tuple(_read_entry(item) for item in _field(data, "entities", list)),
            occurrences=tuple(
                MappingOccurrence(
                    _field(item, "token", str),
                    _field(item, "original", str),
                    item.get("start"),
                    item.get("end"),
                )
                for item in (_as_dict(x, "occurrences") for x in _field(data, "occurrences", list))
            ),
            pseudonymized_sha256=_field(data, "pseudonymized_sha256", str),
        )


def _field[T](data: dict[str, object], name: str, expected: type[T]) -> T:
    """Lit un champ obligatoire et vérifie son type JSON."""
    if name not in data:
        raise MappingError(f"champ obligatoire manquant : {name}")
    value = data[name]
    if not isinstance(value, expected):
        raise MappingError(f"le champ {name} doit être de type {expected.__name__}")
    return value


def _as_dict(value: object, where: str) -> dict[str, object]:
    """Vérifie qu'un élément de liste est un objet JSON."""
    if not isinstance(value, dict):
        raise MappingError(f"chaque élément de {where} doit être un objet JSON")
    return value


def _read_created_at(data: dict[str, object]) -> str:
    """Lit created_at : date ISO 8601 avec fuseau horaire."""
    created_at = _field(data, "created_at", str)
    try:
        parsed = datetime.fromisoformat(created_at)
    except ValueError as error:
        raise MappingError(f"created_at n'est pas une date ISO 8601 : {created_at!r}") from error
    if parsed.tzinfo is None:
        raise MappingError("created_at doit préciser le fuseau horaire (UTC)")
    return created_at


def _read_style(data: dict[str, object]) -> TokenStyle:
    """Lit token_style et le valide."""
    try:
        return TokenStyle(
            language=_field(data, "language", str),
            open_bracket=_field(data, "open_bracket", str),
            close_bracket=_field(data, "close_bracket", str),
        )
    except MappingError:
        raise
    except ValueError as error:
        raise MappingError(f"token_style invalide : {error}") from error


def _read_entry(item: object) -> MappingEntry:
    """Lit une entité de la table ; son type doit être connu."""
    entry = _as_dict(item, "entities")
    type_name = _field(entry, "type", str)
    if type_name not in EntityType.__members__:
        raise MappingError(f"type d'entité inconnu : {type_name!r}")
    variants = _field(entry, "variants", list)
    if not all(isinstance(v, str) for v in variants):
        raise MappingError("les variantes d'une entité doivent être des chaînes")
    return MappingEntry(
        token=_field(entry, "token", str),
        entity_type=EntityType(type_name),
        canonical=_field(entry, "canonical", str),
        variants=tuple(variants),
    )
