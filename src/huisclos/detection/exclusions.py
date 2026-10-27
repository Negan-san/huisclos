"""Liste d'exclusions : juridictions, institutions, textes, acronymes et mots courants.

Entrées : le fichier data/exclusions_fr.txt et un texte à analyser.
Sorties : les positions (début, fin) des passages à ne jamais signaler comme personne,
société ou lieu, et le jeu d'acronymes connus.
Place dans le pipeline : filtre appliqué après la détection (detection.exclusions), avant la
fusion ; les heuristiques de personnes y lisent aussi les acronymes.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from huisclos.models import Detection, EntityType

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "exclusions_fr.txt"

SECTIONS = ("juridictions", "institutions", "textes", "acronymes", "mots")

# Types que l'on peut écarter. Les identifiants à clé, e-mails et téléphones ne sont jamais
# exclus : les masquer en trop gêne peu, les oublier viole le secret (principe 3).
EXCLUDABLE_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION})

_UPPER = "A-ZÀ-ÖØ-ÞŒ"
_LOWER = "a-zà-öø-ÿœ"
_APOSTROPHE = "['\u2019]"

# Nom de lieu qui remplace le mot isolé X : un article facultatif, puis des mots à initiale
# majuscule reliés par des traits d'union (Aix-en-Provence, La Roche-sur-Yon). Les espaces ne
# relient pas deux majuscules, pour ne pas absorber le mot suivant d'une phrase. Seule
# exception, pour les lieux souvent écrits sans trait d'union comme Saint Denis : Saint,
# Sainte, St ou Ste suivi d'un espace se relie à un seul nom de lieu, pas davantage.
_PLACE_WORD = rf"[{_UPPER}][^\W\d_]*"
_PLACE = (
    rf"(?:(?:Le|La|Les)\s|L{_APOSTROPHE})?(?:(?i:Sainte?|Ste?)\s+)?{_PLACE_WORD}"
    rf"(?:-(?:(?:de|du|des|la|le|les|sur|sous|en|lès|aux|d{_APOSTROPHE}|l{_APOSTROPHE})-?)?"
    rf"{_PLACE_WORD})*"
)

_PLACE_TOKEN = re.compile(r"(?<!\S)X(?!\S)")


@dataclass(frozen=True)
class ExclusionList:
    """Expressions d'exclusion compilées et acronymes connus (en majuscules)."""

    patterns: tuple[re.Pattern[str], ...]
    acronyms: frozenset[str]

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Renvoie les passages exclus du texte, triés et sans chevauchement.

        Paramètre : text, le texte analysé.
        Valeur retournée : liste de (début, fin), fin exclue. Deux passages qui se chevauchent
        sont fusionnés ; un passage simplement voisin reste séparé.
        """
        found = sorted(m.span() for pattern in self.patterns for m in pattern.finditer(text))
        merged: list[tuple[int, int]] = []
        for start, end in found:
            if merged and start < merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        return merged


def _literal_to_regex(entry: str) -> str:
    """Transforme une entrée simple en expression régulière.

    Les espaces valent un ou plusieurs blancs, les apostrophes valent l'apostrophe droite ou
    typographique, la casse est ignorée, et le mot isolé X devient un nom de lieu.
    Devant ce lieu, "de" accepte aussi l'élision "d'" pour couvrir les juridictions.
    """
    pieces: list[str] = []
    parts = _PLACE_TOKEN.split(entry)
    for index, part in enumerate(parts):
        elided_place = index < len(parts) - 1 and part.endswith("de ")
        if elided_place:
            part = part[:-3]
        body: list[str] = []
        for char in part:
            if char in "'\u2019":
                body.append(_APOSTROPHE)
            elif char.isspace():
                if not body or body[-1] != r"\s+":
                    body.append(r"\s+")
            else:
                body.append(re.escape(char))
        if elided_place:
            body.append(rf"(?:de\s+|d{_APOSTROPHE})")
        pieces.append(f"(?i:{''.join(body)})" if body else "")
    return r"(?<!\w)" + _PLACE.join(pieces) + r"(?!\w)"


def _alternation(entries: Sequence[str]) -> str:
    """Assemble des mots en alternance, les plus longs d'abord."""
    return "|".join(re.escape(entry) for entry in sorted(entries, key=len, reverse=True))


def parse_exclusions(content: str) -> ExclusionList:
    """Lit le contenu d'un fichier d'exclusions.

    Paramètre : content, le texte du fichier.
    Valeur retournée : l'ExclusionList compilée.
    Lève ValueError pour une section inconnue, une entrée hors section ou une expression
    régulière invalide.
    """
    entries: dict[str, list[str]] = {name: [] for name in SECTIONS}
    section: str | None = None
    for number, raw in enumerate(content.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            if section not in entries:
                raise ValueError(f"ligne {number} : section inconnue [{section}]")
            continue
        if section is None:
            raise ValueError(f"ligne {number} : entrée avant toute section")
        entries[section].append(line)

    sources: list[str] = []
    for name in ("juridictions", "institutions", "textes"):
        for entry in entries[name]:
            sources.append(entry[3:] if entry.startswith("re:") else _literal_to_regex(entry))
    if entries["acronymes"]:
        sources.append(rf"(?<!\w)(?:{_alternation(entries['acronymes'])})(?!\w)")
    if entries["mots"]:
        sources.append(rf"(?<!\w)(?i:{_alternation(entries['mots'])})(?!\w)")
    try:
        patterns = tuple(re.compile(source) for source in sources)
    except re.error as error:
        raise ValueError(f"expression régulière invalide : {error}") from error
    return ExclusionList(patterns=patterns, acronyms=frozenset(entries["acronymes"]))


@lru_cache(maxsize=4)
def _load(resolved_path: str) -> ExclusionList:
    """Lit et compile le fichier ; le résultat est mis en cache par chemin."""
    return parse_exclusions(Path(resolved_path).read_text(encoding="utf-8"))


def load_exclusions(path: Path | str | None = None) -> ExclusionList:
    """Charge la liste d'exclusions (data/exclusions_fr.txt par défaut), avec cache.

    Paramètre : path, un autre fichier au même format.
    Valeur retournée : l'ExclusionList, partagée entre les appels.
    """
    target = DEFAULT_PATH if path is None else Path(path)
    return _load(str(target.resolve()))


def is_legal_reference(passage: str) -> bool:
    """Dit si un passage exclu est une référence juridique plutôt qu'un mot isolé.

    Une juridiction, un article ou un code compte plusieurs mots ("Cour de cassation") ;
    une forme juridique ou un mot courant ("SARL", "Cabinet") n'en compte qu'un et peut
    appartenir au nom d'une société (D-09). Exemple : is_legal_reference("SARL") est faux.
    """
    return len(passage.split()) > 1


def is_excluded(detection: Detection, spans: Sequence[tuple[int, int]]) -> bool:
    """Dit si une détection doit être écartée.

    Vrai seulement pour une personne, une société ou un lieu entièrement contenu dans un
    passage exclu : un nom qui déborde d'une juridiction reste signalé.
    """
    if detection.entity_type not in EXCLUDABLE_TYPES:
        return False
    return any(start <= detection.start and detection.end <= end for start, end in spans)
