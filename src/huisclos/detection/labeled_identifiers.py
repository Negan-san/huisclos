"""Repère les identifiants internes annoncés par un libellé explicite.

Entrées : texte à libellés français, aussi lu dans un document anglais, et types demandés.
Sorties : résultats CUSTOM de source pattern, sans le libellé.
Ce complément des motifs structurés intervient avant la fusion des noms.
"""

from collections.abc import Iterator

from huisclos.detection.patterns import _LocalRecognizer
from huisclos.models import EntityType

_NUMBER = r"(?:n[°ºo]\.?|num[eé]ro)"
_LABEL = (
    rf"(?:matricule(?:[ \t]+(?:de[ \t]+salari[eé]|salari[eé]))?|"
    rf"(?:{_NUMBER}[ \t]+(?:de[ \t]+|d['\u2019]))?"
    r"(?:salari[eé]|contrat|police(?:[ \t]+d['\u2019]assurance)?|client|adh[eé]rent)|"
    rf"(?:{_NUMBER}[ \t]+(?:de[ \t]+|d['\u2019]))?"
    r"(?:passeport|carte[ \t]+d['\u2019]identit[eé])|"
    r"identifiant(?:[ \t]+(?:de[ \t]+)?badge)?|"
    rf"{_NUMBER}[ \t]+fiscal|immatricul(?:ation|[eé]e?)"
    r"(?:[ \t]+(?:du|de)[ \t]+v[eé]hicule)?)"
)
# Le libellé et la valeur restent contigus : pas de recherche libre dans une fenêtre.
_GAP = rf"[ \t]{{0,3}}(?:{_NUMBER}[ \t]{{0,3}})?(?:est[ \t]{{1,3}})?[:=]?[ \t]{{0,3}}"
_VALUE = r"[A-Z0-9]{1,20}(?:[-/][A-Z0-9]{1,20}){0,4}"
_PLATE = r"(?:[A-Z]{2}-[0-9]{3}-[A-Z]{2}|[0-9]{1,4}[ \t]{1,3}[A-Z]{1,3}[ \t]{1,3}[0-9]{2,3})"


class LabeledIdentifierRecognizer(_LocalRecognizer):
    """Détecte CUSTOM à 0,90 avec un libellé et une valeur courte contenant un chiffre."""

    entity_type = EntityType.CUSTOM
    default_score = 0.90
    expression = rf"(?<!\w){_LABEL}(?!\w){_GAP}(?P<value>(?:{_PLATE}|{_VALUE}))(?![\w/-])"

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Garde les valeurs complètes de text, au plus à 12 caractères de leur libellé.

        Les mots seuls, montants, factures et commandes ne déclenchent pas le motif.
        Un chiffre est obligatoire pour éviter d'absorber un nom après un champ vide.
        """
        for match in self._regex.finditer(text):
            start, end = match.span("value")
            value = text[start:end]
            if 2 <= len(value) <= 40 and any(char.isdigit() for char in value):
                yield start, end
