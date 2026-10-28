"""Vue d'analyse projetable : texte normalisé pour les reconnaisseurs, bornes reprojetées.

Entrées : le texte canonique, tel que lu (les lecteurs le mettent déjà en NFC).
Sorties : une AnalysisView, texte de la vue et table monotone vers le texte canonique.
Place dans le pipeline : detect() analyse la vue puis projette chaque span sur le texte
canonique, jamais modifié ; la Detection finale reprend text[start:end] de ce texte.
"""

import re
import unicodedata
from dataclasses import dataclass

# Caractères invisibles retirés de la vue : trait d'union conditionnel, espace et liants de
# largeur nulle, gluon de mot, indicateur d'ordre des octets.
INVISIBLE = frozenset("\u00ad\u200b\u200c\u200d\u2060\ufeff")
# Ligatures typographiques développées : une lettre de la vue vient du même caractère.
LIGATURES = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "st",
    "\ufb06": "st",
}
# Équivalences de même longueur : blancs typographiques et traits d'union insécables. Les
# apostrophes et tirets restent tels quels, les motifs les acceptent déjà (D-AF-A2-5).
SAME_LENGTH = {
    "\u00a0": " ",
    "\u202f": " ",
    "\u2007": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2006": " ",
    "\u2008": " ",
    "\u2010": "-",
    "\u2011": "-",
}
# Les seules transformations de l'ancien pipeline, gardées pour la vue originale.
LEGACY = str.maketrans({"\u00a0": " ", "\u202f": " "})
# Nom de fichier ("attestation_DUPONT_Jean.pdf") : ses tirets bas séparent des mots. Un
# invisible ne coupe pas le nom de fichier.
_FILE_CHAR = r"[\w.\u00ad\u200b\u200c\u200d\u2060\ufeff-]"
FILE_NAME = re.compile(
    rf"(?<!{_FILE_CHAR}){_FILE_CHAR}*[^\W\d_]{_FILE_CHAR}*\."
    r"(?:pdf|docx?|odt|rtf|txt|xlsx?|ods|csv|pptx?|eml|msg|jpe?g|png|tiff?|zip)(?!\w)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AnalysisView:
    """Texte d'analyse et origine de chacun de ses caractères dans le texte canonique.

    starts[i] et ends[i] bornent le passage canonique dont provient le caractère i de la
    vue ; les deux suites sont croissantes au sens large, donc la projection est monotone.
    changed contient les positions canoniques que la vue a retirées ou réécrites, hors
    blancs insécables déjà unifiés avant A2.
    """

    canonical: str
    text: str
    starts: tuple[int, ...]
    ends: tuple[int, ...]
    changed: frozenset[int] = frozenset()

    @property
    def is_legacy(self) -> bool:
        """Vrai si la vue ne diffère du texte que par les blancs déjà remplacés avant A2."""
        return self.text == self.canonical.translate(LEGACY)

    def touches_change(self, start: int, end: int) -> bool:
        """Vrai si le span canonique [start, end) ou ses deux voisins ont été réécrits."""
        return any(index in self.changed for index in range(start - 1, end + 1))

    def project(self, start: int, end: int) -> tuple[int, int]:
        """Bornes canoniques du span [start, end) de la vue.

        Exemple : dans "Jean-\u00adPierre", le span "Jean-Pierre" de la vue (0, 11) devient
        (0, 12) : le trait d'union conditionnel intérieur reste dans le span.
        """
        if not 0 <= start < end <= len(self.text):
            raise ValueError(f"span hors de la vue : ({start}, {end})")
        return self.starts[start], self.ends[end - 1]


def _units(text: str) -> list[tuple[int, int]]:
    """Découpe text en unités : un caractère et ses diacritiques combinants éventuels."""
    units: list[tuple[int, int]] = []
    index = 0
    while index < len(text):
        end = index + 1
        while end < len(text) and unicodedata.combining(text[end]):
            end += 1
        units.append((index, end))
        index = end
    return units


def _file_name_positions(text: str) -> set[int]:
    """Positions des tirets bas situés dans un nom de fichier."""
    return {
        match.start() + offset
        for match in FILE_NAME.finditer(text)
        for offset, char in enumerate(match.group())
        if char == "_"
    }


def build_view(text: str) -> AnalysisView:
    """Construit la vue d'analyse de text.

    Paramètre : text, le texte canonique.
    Valeur retournée : la vue, où les invisibles sont retirés, les ligatures développées,
    les suites décomposées recomposées (NFC), les blancs et traits d'union typographiques
    unifiés et les tirets bas des noms de fichiers changés en espaces. Aucun remplacement
    global de lettres par des chiffres, aucune ligne raccordée.
    """
    underscores = _file_name_positions(text)
    chars: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    changed: set[int] = set()
    for start, end in _units(text):
        unit = text[start:end]
        if unit in INVISIBLE:
            output = ""
        elif unit in LIGATURES:
            output = LIGATURES[unit]
        elif start in underscores:
            output = " "
        elif end - start > 1:
            output = unicodedata.normalize("NFC", unit)
        else:
            output = SAME_LENGTH.get(unit, unit)
        if output != unit.translate(LEGACY):
            changed.update(range(start, end))
        for char in output:
            chars.append(char)
            starts.append(start)
            ends.append(end)
    return AnalysisView(text, "".join(chars), tuple(starts), tuple(ends), frozenset(changed))
