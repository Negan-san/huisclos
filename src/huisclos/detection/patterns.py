"""Repère les identifiants et coordonnées par motifs locaux et clés de contrôle.

Entrées : texte français et types demandés par Presidio. Sorties : RecognizerResult.
Les scores suivent D-07 ; les libellés restent hors des spans selon D-09.
Ce premier étage de détection ne charge aucun modèle et ne fait aucun appel réseau.
"""

import re
import unicodedata
from collections.abc import Iterator
from datetime import date

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.detection.checksums import (
    digits_only,
    iban_is_valid,
    nir_is_valid,
    nir_structure_is_plausible,
    siren_is_valid,
    siret_is_valid,
)
from huisclos.models import EntityType, Source

_SPACE = r"[ \u00a0\u202f]"
# Chaque remplacement garde un caractère : les positions restent celles du texte original.
_NONBREAKING_SPACES = str.maketrans("\u00a0\u202f", "  ")
_SEPARATOR = r"[ .\u00a0\u202f]?"
_WORD = r"[^\W\d_]{1,40}(?:['\u2019-][^\W\d_]{1,40}){0,4}"
_CAPITAL_WORD = r"(?!CEDEX\b)[A-ZÀ-ÖØ-Þ][^\W\d_]{0,39}(?:['\u2019-][^\W\d_]{1,40}){0,4}"
_CITY = (
    rf"{_CAPITAL_WORD}(?:[ ]{{1,3}}(?:{_CAPITAL_WORD}|sur|sous|en|les|le|la|de|du|aux)){{0,7}}"
    r"(?:[ ]{1,3}CEDEX(?:[ ]{1,3}[0-9]{1,2})?)?"
)
_POSTAL_CITY = rf"[0-9]{{5}}[ \u00a0\u202f]{{1,3}}{_CITY}"
_STREET_TYPE = (
    r"(?:rue|avenue|av\.|boulevard|bd\.?|place|allée|allee|chemin|impasse|quai|cours|"
    r"route|square|villa|passage|voie|sentier|cité|cite|résidence|residence|lieu-dit|"
    r"hameau|faubourg|esplanade|promenade)"
)
_STREET = (
    rf"[0-9]{{1,5}}[ ]{{0,3}}(?:(?:bis|ter|quater)[ ]{{1,3}})?"
    rf"{_STREET_TYPE}[ ]{{1,3}}{_WORD}(?:[ ]{{1,3}}{_WORD}){{0,5}}"
)


def _fold(value: str) -> str:
    """Renvoie value sans accents ni casse pour comparer les mots de contexte."""
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value.lower())
        if not unicodedata.combining(character)
    )


class _LocalRecognizer(EntityRecognizer):
    """Adapte les motifs locaux à Presidio sans amélioration automatique du contexte."""

    entity_type: EntityType
    expression: str
    context_expression: str = r"(?!)"
    default_score: float = 0.90
    regex_flags: int = re.IGNORECASE

    def __init__(self) -> None:
        """Prépare les motifs et déclare le type français pris en charge."""
        self._regex = re.compile(self.expression, self.regex_flags)
        super().__init__(supported_entities=[self.entity_type.value], supported_language="fr")

    def load(self) -> None:
        """Satisfait le contrat Presidio ; aucun fichier ni modèle n'est nécessaire."""

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Renvoie dans text les positions utiles, sans les éventuels libellés."""
        for match in self._regex.finditer(text.translate(_NONBREAKING_SPACES)):
            yield match.span("value") if "value" in match.re.groupindex else match.span()

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Attribue à value le score fixe du motif ; has_context est facultatif."""
        return self.default_score, Source.PATTERN

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        """Renvoie les détections de text demandées par entities ; ignore les données NLP."""
        if self.entity_type.value not in entities:
            return []
        results = []
        for start, end in self._candidates(text):
            # La fenêtre porte sur le texte original pour rester exactement à 40 caractères.
            context = _fold(text[max(0, start - 40) : start])
            has_context = re.search(self.context_expression, context) is not None
            score, source = self._evaluate(
                text[start:end].translate(_NONBREAKING_SPACES), has_context
            )
            if score:
                results.append(
                    RecognizerResult(
                        entity_type=self.entity_type.value,
                        start=start,
                        end=end,
                        score=score,
                        recognition_metadata={
                            "recognizer_name": self.name,
                            "huisclos_source": source.value,
                        },
                    )
                )
        return results


class NirRecognizer(_LocalRecognizer):
    """Repère les NIR, y compris ceux dont la clé est probablement mal recopiée."""

    entity_type = EntityType.NIR
    expression = (
        rf"(?<!\w)[0-9]{_SEPARATOR}[0-9]{{2}}{_SEPARATOR}[0-9]{{2}}{_SEPARATOR}"
        rf"(?:[0-9]{{2}}|2[AB]){_SEPARATOR}[0-9]{{3}}{_SEPARATOR}"
        rf"[0-9]{{3}}{_SEPARATOR}[0-9]{{2}}(?!\w)"
    )
    context_expression = r"\b(?:securite\s+sociale|n[°o]\s*ss|nir|insee|immatriculation)\b"

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value 1 avec clé correcte, 0,40 si plausible, sinon zéro."""
        if nir_is_valid(value):
            return 1.0, Source.CHECKSUM
        return (0.40 if nir_structure_is_plausible(value) else 0.0), Source.PATTERN


class SirenRecognizer(_LocalRecognizer):
    """Repère uniquement les SIREN dont la clé de Luhn est correcte."""

    entity_type = EntityType.SIREN
    expression = (
        rf"(?<![0-9])(?:[0-9]{{9}}|[0-9]{{3}}{_SPACE}[0-9]{{3}}"
        rf"{_SPACE}[0-9]{{3}})(?![0-9])"
    )
    context_expression = r"\b(?:siren|rcs|immatriculee?|registre\s+du\s+commerce)\b"

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value un score selon la clé et la présence du contexte."""
        if siren_is_valid(value):
            return (1.0 if has_context else 0.70), Source.CHECKSUM
        return 0.0, Source.PATTERN


class SiretRecognizer(_LocalRecognizer):
    """Repère les SIRET et les fautes de clé accompagnées d'un libellé."""

    entity_type = EntityType.SIRET
    expression = (
        rf"(?<![0-9])(?:[0-9]{{14}}|[0-9]{{3}}{_SPACE}[0-9]{{3}}"
        rf"{_SPACE}[0-9]{{3}}{_SPACE}[0-9]{{5}})(?![0-9])"
    )
    context_expression = r"\b(?:siret|etablissement)\b"

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value le score D-07, ou zéro sans clé ni contexte."""
        if siret_is_valid(value):
            return (1.0 if has_context else 0.85), Source.CHECKSUM
        return (0.40 if has_context else 0.0), Source.PATTERN


class IbanRecognizer(_LocalRecognizer):
    """Cherche le plus long préfixe IBAN valide, sans absorber le mot suivant."""

    entity_type = EntityType.IBAN
    # La recherche sans consommation préserve le début d'un éventuel second IBAN.
    expression = (
        rf"(?=(?P<value>(?<![A-Za-z0-9])[A-Z]{{2}}[0-9]{{2}}"
        rf"(?:{_SPACE}?[A-Z0-9]){{11,30}}))"
    )
    regex_flags = 0

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Raccourcit chaque candidat de text aux frontières des groupes et des mots."""
        for match in self._regex.finditer(text):
            start, stop = match.span("value")
            fallback = None
            for end in range(stop, start + 14, -1):
                if not text[end - 1].isalnum() or (end < len(text) and text[end].isalnum()):
                    continue
                value = text[start:end]
                if iban_is_valid(value):
                    yield start, end
                    break
                if re.fullmatch(r"FR[0-9]{12}[A-Z0-9]{11}[0-9]{2}", digits_only(value)):
                    fallback = (start, end)
            else:
                if fallback is not None:
                    yield fallback

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie 1 pour la clé correcte de value, sinon 0,40 pour le format FR."""
        return (1.0, Source.CHECKSUM) if iban_is_valid(value) else (0.40, Source.PATTERN)


class EmailRecognizer(_LocalRecognizer):
    """Repère les adresses électroniques sans dépendance aux listes de domaines."""

    entity_type = EntityType.EMAIL
    default_score = 0.95
    expression = (
        r"(?<![\w.!#$%&'*+/=?^`{|}~@-])[A-Z0-9!#$%&'*+/=?^`{|}~-]{1,64}"
        r"(?:\.[A-Z0-9!#$%&'*+/=?^`{|}~-]{1,64}){0,10}@"
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.){1,10}[A-Z]{2,63}"
        r"(?![\w@-])"
    )


class PhoneFrRecognizer(_LocalRecognizer):
    """Repère les téléphones français nationaux et internationaux."""

    entity_type = EntityType.PHONE
    expression = (
        r"(?<![\w+])(?:0|(?:\+33|0033)[ .\u00a0\u202f-]?(?:\(0\)[ .\u00a0\u202f-]?)?)"
        r"[1-9](?:[ .\u00a0\u202f-]?[0-9]{2}){4}(?!\w)"
    )
    context_expression = r"\b(?:tel|telephone|portable|mobile|fixe)\b"

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value 0,90 avec contexte téléphonique, sinon 0,75."""
        return (0.90 if has_context else 0.75), Source.PATTERN


class BirthDateRecognizer(_LocalRecognizer):
    """Repère les dates uniquement après un contexte explicite de naissance."""

    entity_type = EntityType.BIRTH_DATE
    expression = (
        r"(?<!\w)(?:[0-9]{1,2}(?P<separator>[/\.])[0-9]{1,2}(?P=separator)[0-9]{4}|"
        r"(?:1er|[0-9]{1,2})[ ]{1,3}(?:janvier|février|fevrier|mars|avril|mai|juin|"
        r"juillet|août|aout|septembre|octobre|novembre|décembre|decembre)[ ]{1,3}[0-9]{4})(?!\w)"
    )
    context_expression = r"\b(?:ne(?:e|\(e\))?|naissance)(?!\w)"

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Vérifie la date value et renvoie 0,90 seulement avec un contexte de naissance."""
        if not has_context:
            return 0.0, Source.PATTERN
        parts = re.split(r"[/\. ]+", _fold(value).replace("1er", "1"))
        months = (
            "janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre"
        ).split()
        try:
            month = months.index(parts[1]) + 1 if parts[1] in months else int(parts[1])
            date(int(parts[2]), month, int(parts[0]))
        except ValueError:
            return 0.0, Source.PATTERN
        return 0.90, Source.PATTERN


class CaseNumberRecognizer(_LocalRecognizer):
    """Repère les numéros RG et Portalis en laissant leur libellé visible."""

    entity_type = EntityType.CASE_NUMBER
    expression = (
        r"(?:\bR\.?[ ]?G\.?(?:[ ]{0,3}n[°o])?|\bn[°o][ ]{0,3}R\.?[ ]?G\.?|"
        r"(?P<portalis>\bPortalis))[ ]{0,3}:?[ ]{0,3}(?P<value>(?(portalis)"
        r"[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){3}(?![\w-])|"
        r"(?:F[ ]{0,3})?(?:[0-9]{4}|[0-9]{2})/[0-9]{5}(?!\w)))"
    )


class AddressRecognizer(_LocalRecognizer):
    """Repère une voie, une adresse complète ou un couple code postal et ville."""

    entity_type = EntityType.ADDRESS
    # Les quantificateurs sont bornés ; une ville commence par une majuscule.
    expression = (
        rf"(?<!\w)(?:(?i:{_STREET})(?:[ ,\t\r\n]{{1,6}}{_POSTAL_CITY})?|"
        rf"{_POSTAL_CITY})(?!\w)"
    )
    regex_flags = 0

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value 0,70 si complète, 0,55 pour la voie, sinon 0,45."""
        if re.fullmatch(_POSTAL_CITY, value):
            return 0.45, Source.PATTERN
        return (0.70 if re.search(rf"{_POSTAL_CITY}$", value) else 0.55), Source.PATTERN


def build_pattern_recognizers() -> list[EntityRecognizer]:
    """Renvoie les neuf reconnaisseurs français dans un ordre stable entre les appels."""
    return [
        NirRecognizer(),
        SirenRecognizer(),
        SiretRecognizer(),
        IbanRecognizer(),
        EmailRecognizer(),
        PhoneFrRecognizer(),
        BirthDateRecognizer(),
        CaseNumberRecognizer(),
        AddressRecognizer(),
    ]
