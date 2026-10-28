"""Alias explicites et noms de fichiers : deux formes ne sont reliées que par une mention claire.

Entrées : le texte et ses détections (personnes et sociétés).
Sorties : des AliasLink (alias défini, entité d'origine, ambiguïté) et les positions des noms
de fichiers du texte.
Place dans le pipeline : la propagation retrouve les occurrences d'un alias ; le regroupement
leur donne le jeton de l'entité d'origine si le lien est unique. Aucun dictionnaire de
surnoms ni rapprochement approximatif (D-AF-A2-7).
"""

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from huisclos.detection.analysis_view import FILE_NAME
from huisclos.models import Detection, EntityType
from huisclos.text_utils import fold, letter_count

_ALIAS = r"[\u00ab\"\u201c][ \t\u00a0\u202f]*(?P<alias>[^\u00ab\u00bb\"\u201c\u201d\n]{1,40}?)"
_ALIAS += r"[ \t\u00a0\u202f]*[\u00bb\"\u201d]"
_INTRO = (
    r"(?:ci-apr[eè]s(?:[ \t]+(?:d[ée]nomm[ée]e?s?|d[ée]sign[ée]e?s?|appel[ée]e?s?))?"
    r"(?:[ \t]+(?:la|le|les|l['\u2019]))?[ \t]*:?[ \t]*|"
    r"hereinafter(?:[ \t]+(?:referred[ \t]+to[ \t]+as|called))?[ \t]*(?:the[ \t]+)?|the[ \t]+)"
)
# Définition entre parenthèses juste après le nom : (ci-après "BLX"), ("Northfield").
_PARENTHESIS = re.compile(rf"[ \t]*\([ \t]*{_INTRO}?{_ALIAS}[ \t]*\)", re.IGNORECASE)
# Mention d'alias après une virgule : , dit "Théo" ; , also known as "Jack".
_NAMED = re.compile(
    rf",?[ \t]+(?:dite?s?|alias|also[ \t]+known[ \t]+as|a/?k/?a|known[ \t]+as)[ \t]+{_ALIAS}",
    re.IGNORECASE,
)
# Un alias doit ressembler à un nom : sigle ou mots à majuscule, quatre mots au plus.
_NAME_SHAPE = re.compile(
    r"[A-ZÀ-ÖØ-Þ0-9][\w&'\u2019.-]*"
    r"(?:[ \t](?:[A-ZÀ-ÖØ-Þ0-9&][\w&'\u2019.-]*|de|du|des|la|le|of|and|et)){0,3}"
)
# Rôles contractuels : "la Société", "the Company" désignent une partie, pas un nom propre.
GENERIC_ROLES = frozenset(
    """
    societe employeur salarie salariee client cliente bailleur preneur vendeur acheteur
    prestataire fournisseur demandeur demanderesse defendeur defenderesse partie parties
    contrat acte groupe cabinet company employer employee customer supplier buyer seller
    landlord tenant party agreement contractor licensor licensee claimant defendant
    respondent services consultant purchaser vendor lender borrower
    """.split()
)
_LINKED_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION})


@dataclass(frozen=True)
class AliasLink:
    """Alias défini dans le texte : sa forme, ses bornes, son entité d'origine.

    ambiguous est vrai quand la même forme est définie pour deux entités différentes : ses
    occurrences restent protégées, mais aucun jeton commun n'est imposé.
    """

    alias: str
    start: int
    end: int
    origin: Detection
    ambiguous: bool = False


def is_name_like(alias: str) -> bool:
    """Dit si un alias ressemble à un nom propre et non à un rôle ("la Société")."""
    words = [fold(word) for word in alias.split()]
    if not words or letter_count(alias) < 2 or words[-1] in GENERIC_ROLES:
        return False
    return _NAME_SHAPE.fullmatch(alias) is not None


def _definitions(text: str, detections: Sequence[Detection]) -> list[AliasLink]:
    """Alias définis juste après une personne ou une société détectée."""
    links: list[AliasLink] = []
    for origin in detections:
        if origin.entity_type not in _LINKED_TYPES:
            continue
        for pattern in (_PARENTHESIS, _NAMED):
            match = pattern.match(text, origin.end)
            if match and is_name_like(match["alias"]):
                start, end = match.span("alias")
                if fold(match["alias"]) != fold(origin.text):
                    links.append(AliasLink(match["alias"], start, end, origin))
                break
    return links


def find_aliases(text: str, detections: Sequence[Detection]) -> list[AliasLink]:
    """Renvoie les alias explicitement définis dans text, marqués ambigus si besoin.

    Paramètres : text, le texte ; detections, ses détections.
    Valeur retournée : un AliasLink par définition. Une même forme définie pour deux
    entités de textes différents, ou de types différents, est ambiguë.
    Exemple : "Brightmoor SAS (ci-après \u00ab BLX \u00bb)" relie "BLX" à "Brightmoor SAS".
    """
    links = _definitions(text, detections)
    origins: dict[str, set[tuple[EntityType, str]]] = defaultdict(set)
    for link in links:
        origins[fold(link.alias)].add((link.origin.entity_type, fold(link.origin.text)))
    return [
        AliasLink(link.alias, link.start, link.end, link.origin, len(origins[fold(link.alias)]) > 1)
        for link in links
    ]


def filename_spans(text: str) -> list[tuple[int, int]]:
    """Positions des noms de fichiers ("conclusions_DUPONT.pdf") présents dans text."""
    return [match.span() for match in FILE_NAME.finditer(text)]


def in_filename(detection: Detection, spans: Sequence[tuple[int, int]]) -> bool:
    """Vrai si la détection se trouve entièrement dans un nom de fichier."""
    return any(start <= detection.start and detection.end <= end for start, end in spans)
