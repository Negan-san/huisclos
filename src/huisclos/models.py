"""Modèles de données partagés : types d'entités, sources de détection et Detection.

Entrées : aucune. Sorties : énumérations, dataclasses (Detection, groupes, occurrences,
résultat de pseudonymisation) et constantes de jetons.
Place dans le pipeline : contrat commun à la détection, à la revue, à la pseudonymisation
et à l'évaluation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from huisclos.pseudonymize.mapping import Mapping


class EntityType(str, Enum):  # noqa: UP042 (contrat exigé : str + Enum)
    """Type d'entité détectable ; chaque valeur est égale à son nom."""

    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    ADDRESS = "ADDRESS"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    IBAN = "IBAN"
    NIR = "NIR"
    SIREN = "SIREN"
    SIRET = "SIRET"
    BIRTH_DATE = "BIRTH_DATE"
    CASE_NUMBER = "CASE_NUMBER"
    LOCATION = "LOCATION"
    CUSTOM = "CUSTOM"


class Source(str, Enum):  # noqa: UP042 (contrat exigé : str + Enum)
    """Origine d'une détection, utile pour expliquer son score à l'utilisateur."""

    CHECKSUM = "checksum"
    PATTERN = "pattern"
    HEURISTIC = "heuristic"
    NER_SPACY = "ner_spacy"
    NER_CAMEMBERT = "ner_camembert"
    PROPAGATION = "propagation"
    MANUAL = "manual"


@dataclass(frozen=True)
class Detection:
    """Une valeur sensible repérée dans un texte.

    Les positions suivent la convention Python : start inclus, end exclu. Le champ text
    doit être exactement texte[start:end]. Sans le texte source, __post_init__ ne peut
    vérifier que sa longueur ; le pipeline doit vérifier la valeur de la tranche.
    """

    start: int
    end: int
    entity_type: EntityType
    score: float
    source: Source
    text: str

    def __post_init__(self) -> None:
        """Refuse les positions, scores et textes incohérents."""
        if self.start < 0:
            raise ValueError(f"start doit être positif ou nul, reçu {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end ({self.end}) doit dépasser start ({self.start})")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score doit être compris entre 0 et 1, reçu {self.score}")
        if len(self.text) != self.end - self.start:
            raise ValueError("la longueur de text doit être égale à end - start")

    @property
    def length(self) -> int:
        """Nombre de caractères couverts par la détection."""
        return self.end - self.start


# Libellé de jeton par type : (français, anglais). Exemple : [PERSONNE_1] ou [PERSON_1].
TOKEN_LABELS: dict[EntityType, tuple[str, str]] = {
    EntityType.PERSON: ("PERSONNE", "PERSON"),
    EntityType.ORGANIZATION: ("SOCIETE", "COMPANY"),
    EntityType.ADDRESS: ("ADRESSE", "ADDRESS"),
    EntityType.EMAIL: ("EMAIL", "EMAIL"),
    EntityType.PHONE: ("TELEPHONE", "PHONE"),
    EntityType.IBAN: ("IBAN", "IBAN"),
    EntityType.NIR: ("NIR", "NIR"),
    EntityType.SIREN: ("SIREN", "SIREN"),
    EntityType.SIRET: ("SIRET", "SIRET"),
    EntityType.BIRTH_DATE: ("DATE_NAISSANCE", "BIRTH_DATE"),
    EntityType.CASE_NUMBER: ("DOSSIER", "CASE"),
    EntityType.LOCATION: ("LIEU", "PLACE"),
    EntityType.CUSTOM: ("AUTRE", "OTHER"),
}

# Types numérotés par lettres (A, B, ..., AA) plutôt que par chiffres, pour les distinguer
# des personnes : [SOCIETE_A].
LETTER_INDEXED: frozenset[EntityType] = frozenset({EntityType.ORGANIZATION})

# LOCATION est désactivé par défaut : les villes seules gênent plus qu'elles ne protègent.
DEFAULT_ENABLED_TYPES: frozenset[EntityType] = frozenset(EntityType) - {EntityType.LOCATION}


@dataclass(frozen=True)
class TokenStyle:
    """Forme des jetons : langue des libellés et crochets qui les entourent.

    Exemple : TokenStyle() produit [PERSONNE_1] ; TokenStyle(language="en") produit
    [PERSON_1].
    """

    language: str = "fr"
    open_bracket: str = "["
    close_bracket: str = "]"

    def __post_init__(self) -> None:
        """Refuse une langue inconnue et des crochets vides."""
        if self.language not in ("fr", "en"):
            raise ValueError(f"language doit valoir fr ou en, reçu {self.language!r}")
        if not self.open_bracket or not self.close_bracket:
            raise ValueError("les crochets d'un jeton ne peuvent pas être vides")


@dataclass(frozen=True)
class EntityGroup:
    """Ensemble des mentions d'une même entité, remplacées par un même jeton.

    group_id suit l'ordre de première apparition dans le texte. variants contient les
    écritures exactes rencontrées, triées. mention_spans donne les positions (début, fin)
    de chaque mention dans le texte d'origine. ambiguous_with liste les groupes auxquels
    la mention aurait pu être rattachée quand le choix n'était pas sûr. token est vide
    tant que la numérotation n'a pas eu lieu.
    """

    group_id: int
    entity_type: EntityType
    canonical: str
    variants: tuple[str, ...]
    token: str
    mention_spans: tuple[tuple[int, int], ...]
    ambiguous_with: tuple[int, ...] = ()


@dataclass(frozen=True)
class Occurrence:
    """Un remplacement : le jeton, le texte exact remplacé, sa place dans le texte produit."""

    token: str
    original: str
    start: int
    end: int


@dataclass(frozen=True)
class PseudonymizationResult:
    """Résultat de la pseudonymisation d'un texte.

    text est le texte à jetons ; occurrences suit l'ordre de ce texte ; mapping est la
    table de correspondance (huisclos.pseudonymize.mapping.Mapping), sensible, à ne jamais
    envoyer au LLM ; warnings contient des messages destinés à l'utilisateur.
    """

    text: str
    groups: tuple[EntityGroup, ...]
    occurrences: tuple[Occurrence, ...]
    mapping: "Mapping"
    warnings: tuple[str, ...]
