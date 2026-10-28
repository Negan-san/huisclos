"""Motifs propres aux documents anglais, et téléphones internationaux de toute langue.

Entrées : le texte analysé, sa langue et les types demandés par Presidio.
Sorties : RecognizerResult de source pattern : dates de naissance, références privées de
dossier, téléphones, identifiants libellés ; libellés hors des spans (D-09).
Place dans le pipeline : complète detection.patterns, dont les identifiants français restent
actifs dans un document anglais. Une langue ne désigne ni une nationalité ni une juridiction.
"""

import re
from collections.abc import Iterator

from presidio_analyzer import EntityRecognizer

from huisclos.detection.patterns import PHONE_CONTEXT, BirthDateRecognizer, _LocalRecognizer
from huisclos.models import EntityType, Source
from huisclos.text_utils import full_year, is_calendar_date

_MONTHS = (
    "january february march april may june july august september october november december"
).split()
_MONTH = (
    r"(?:january|february|march|april|may|june|july|august|september|october|november|"
    r"december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.?"
)
_ORDINAL = r"[0-9]{1,2}(?:st|nd|rd|th)?"


def digit_count(value: str) -> int:
    """Nombre de chiffres de value, parenthèses, signes et séparateurs ignorés."""
    return sum(char.isdigit() for char in value)


class EnglishBirthDateRecognizer(BirthDateRecognizer):
    """Date de naissance d'un document anglais : "born", "date of birth", "DOB".

    Une date numérique ambiguë (03/04/1985) est masquée si l'une de ses lectures, jour puis
    mois ou mois puis jour, existe : aucune juridiction n'est choisie à la place du texte.
    """

    expression = (
        r"(?<!\w)(?:[0-9]{1,2}(?P<separator>[/.-])[0-9]{1,2}(?P=separator)"
        r"(?:[0-9]{4}|[0-9]{2}(?![./-]?[0-9]))|[0-9]{4}-[0-9]{2}-[0-9]{2}|"
        rf"{_ORDINAL}[ ]{{1,3}}(?:of[ ]{{1,3}})?{_MONTH},?[ ]{{1,3}}[0-9]{{4}}|"
        rf"{_MONTH}[ ]{{1,3}}{_ORDINAL},?[ ]{{1,3}}[0-9]{{4}})(?!\w)"
    )
    keywords = frozenset({"born", "birth", "dob", "birthdate", "birthday"})
    stops = frozenset(
        """
        hearing trial judgment judgement order decision ruling filed signed dated served
        issued meeting interview letter email contract agreement effective commenced
        employment dismissal termination incident accident since until deadline invoice
        payment appointment death died married
        """.split()
    )

    def window(self, text: str, start: int) -> str:
        """Fenêtre de BirthDateRecognizer, où "D.O.B." s'écrit "DOB" pour garder le mot."""
        return re.sub(r"(?i)\bd\.o\.b\.?", "DOB", super().window(text, start))

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie 0,90 si une lecture de la date value existe dans le calendrier."""
        words = re.findall(r"[a-z]+|[0-9]+", value.lower())
        numbers = [word for word in words if word.isdigit()]
        month_names = [w for w in words if w[:3] in {m[:3] for m in _MONTHS} and w != "of"]
        if month_names:
            month = next(i for i, m in enumerate(_MONTHS, 1) if m.startswith(month_names[0][:3]))
            readings = [(full_year(numbers[1]), month, int(numbers[0]))]
        elif len(numbers[0]) == 4:
            readings = [(int(numbers[0]), int(numbers[1]), int(numbers[2]))]
        else:
            first, second, year = int(numbers[0]), int(numbers[1]), full_year(numbers[2])
            readings = [(year, second, first), (year, first, second)]
        valid = any(is_calendar_date(*reading) for reading in readings)
        return (0.90 if valid else 0.0), Source.PATTERN


class EnglishCaseNumberRecognizer(_LocalRecognizer):
    """Référence privée d'un dossier : "Claim No.", "Case No.", "Our ref", "File ref".

    Un mot seul ("case", "file") exige un numéro annoncé ou deux-points : "case law" ou
    "file 2024" ne déclenchent rien. Les références publiques (affaire C-131/12, citations
    neutres) restent visibles.
    """

    entity_type = EntityType.CASE_NUMBER
    expression = (
        r"(?<!\w)(?:(?:claim|case|file|matter|docket|index|reference|ref)"
        r"(?:[ \t]{0,3}(?:no\.?|number|num\.?|#)|[ \t]{0,3}(?=:))|"
        r"(?:our|your|file|matter)[ \t]{1,3}ref(?:erence)?\.?)"
        r"[ \t]{0,3}(?:\r?\n[ \t]{0,3})?[:#]?[ \t]{0,3}"
        r"(?P<value>[A-Z0-9]{1,12}(?:[-/.:][A-Z0-9]{1,12}){0,5})(?![\w/-])"
    )
    _PUBLIC = re.compile(r"[CT]-[0-9]+/[0-9]{2}")

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Garde les valeurs de 3 à 40 caractères avec un chiffre, hors références publiques."""
        for start, end in super()._candidates(text):
            value = text[start:end]
            if 3 <= len(value) <= 40 and any(c.isdigit() for c in value):
                if not self._PUBLIC.fullmatch(value):
                    yield start, end


class InternationalPhoneRecognizer(_LocalRecognizer):
    """Téléphone au format international explicite (+44, +1), hors +33 déjà couvert.

    Le préfixe "+" et l'indicatif suffisent : 0,75, ou 0,90 près d'un mot de téléphone.
    """

    entity_type = EntityType.PHONE
    expression = (
        r"(?<![\w+])\+(?!33)[1-9][0-9]{0,2}(?:[ .\u00a0-]{0,2}\(?[0-9]{1,4}\)?){2,6}(?![\w-])"
    )
    context_expression = PHONE_CONTEXT

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Garde les numéros de 8 à 15 chiffres, longueur admise par la norme E.164."""
        for start, end in super()._candidates(text):
            if 8 <= digit_count(text[start:end]) <= 15:
                yield start, end

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie 0,90 avec un contexte téléphonique, sinon 0,75."""
        return (0.90 if has_context else 0.75), Source.PATTERN


class EnglishLocalPhoneRecognizer(_LocalRecognizer):
    """Téléphone national américain ou britannique, seulement près d'un mot de téléphone.

    Sans indicatif, dix chiffres peuvent être un montant ou une référence : le contexte
    ("Tel", "call", "phone") est exigé, puis le score vaut 0,90.
    """

    entity_type = EntityType.PHONE
    expression = (
        r"(?<![\w+(])(?:\([2-9][0-9]{2}\)[ ]?|[2-9][0-9]{2}[ .-])[0-9]{3}[ .-][0-9]{4}(?![\w-])|"
        r"(?<![\w+])0[1-9][0-9]{1,3}[ ]?[0-9]{3,4}[ ]?[0-9]{3,4}(?![\w-])"
    )
    context_expression = PHONE_CONTEXT

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie 0,90 avec contexte et dix ou onze chiffres, sinon zéro."""
        if has_context and 10 <= digit_count(value) <= 11:
            return 0.90, Source.PATTERN
        return 0.0, Source.PATTERN


_NUMBER_WORD = r"(?:no\.?|number|num\.?|id|#)"
_EN_LABEL = (
    rf"(?:(?:employee|staff|payroll|contract|policy|customer|client|account|member(?:ship)?|"
    rf"passport|badge|licen[cs]e|(?:driver['\u2019]?s|driving)[ \t]+licen[cs]e|"
    rf"national[ \t]+insurance|social[ \t]+security|tax)[ \t]{{0,3}}{_NUMBER_WORD}|"
    r"NINO|SSN|tax[ \t]+(?:id|reference)|TIN|EIN|UTR)"
)


class EnglishLabeledIdentifierRecognizer(_LocalRecognizer):
    """Identifiant interne annoncé par un libellé anglais : "Employee No.", "SSN" (0,90).

    Même règle que D-S14-1 : la valeur suit son libellé, comporte un chiffre et reste
    bornée ; le libellé reste visible.
    """

    entity_type = EntityType.CUSTOM
    expression = (
        rf"(?<!\w){_EN_LABEL}(?!\w)[ \t]{{0,3}}(?:is[ \t]{{1,3}})?[:=#]?[ \t]{{0,3}}"
        r"(?P<value>[A-Z]{2}[ ]?[0-9]{2}[ ]?[0-9]{2}[ ]?[0-9]{2}[ ]?[A-D](?!\w)|"
        r"[0-9]{3}-[0-9]{2}-[0-9]{4}(?![\w-])|"
        r"[A-Z0-9]{1,20}(?:[-/][A-Z0-9]{1,20}){0,4}(?![\w/-]))"
    )

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Garde les valeurs de 2 à 40 caractères qui contiennent un chiffre."""
        for start, end in super()._candidates(text):
            value = text[start:end]
            if 2 <= len(value) <= 40 and any(char.isdigit() for char in value):
                yield start, end


def birth_recognizer(language: str) -> BirthDateRecognizer:
    """Reconnaisseur des dates de naissance de la langue du document."""
    if language == "en":
        return EnglishBirthDateRecognizer(language)
    return BirthDateRecognizer(language)


def language_recognizers(language: str) -> list[EntityRecognizer]:
    """Reconnaisseurs ajoutés à ceux de detection.patterns pour la langue du document.

    Le téléphone international vaut pour les deux langues ; les références de dossier, les
    numéros nationaux et les identifiants libellés anglais ne servent qu'en anglais.
    """
    extra: list[EntityRecognizer] = [InternationalPhoneRecognizer(language)]
    if language == "en":
        extra += [
            EnglishCaseNumberRecognizer(language),
            EnglishLocalPhoneRecognizer(language),
            EnglishLabeledIdentifierRecognizer(language),
        ]
    return extra
