"""Repère les identifiants et coordonnées par motifs locaux et clés de contrôle.

Entrées : texte français ou anglais, langue du document et types demandés par Presidio.
Sorties : RecognizerResult. Les scores suivent D-07 ; les libellés restent hors des spans
selon D-09.
Ce premier étage de détection ne charge aucun modèle et ne fait aucun appel réseau.
"""

import re
import unicodedata
from collections.abc import Iterator

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.detection.address_bounds import SCORES as ADDRESS_SCORES
from huisclos.detection.address_bounds import address_spans
from huisclos.detection.case_patterns import LABEL_GAP, procedure_candidates
from huisclos.detection.checksums import (
    digits_only,
    iban_is_valid,
    nir_is_valid,
    nir_structure_is_plausible,
    siren_is_valid,
    siret_is_valid,
)
from huisclos.models import EntityType, Source
from huisclos.text_utils import full_year, is_calendar_date

_SPACE = r"[ \u00a0\u202f]"
# Chaque remplacement garde un caractère : les positions restent celles du texte original.
_NONBREAKING_SPACES = str.maketrans("\u00a0\u202f", "  ")
_SEPARATOR = r"[ .\u00a0\u202f]?"
# Score d'un numéro au bon format mais à clé fausse, près de son libellé (D-07).
INVALID_KEY_SCORE = 0.40
# Mots de contexte téléphonique, français et anglais, cherchés sans accents ni casse.
PHONE_CONTEXT = r"\b(?:tel|telephone|portable|mobile|fixe|phone|cell|call|fax)\b"
# Portée du contexte de naissance (D-AF-A2-3) : mots, caractères et lignes avant la date.
BIRTH_SCOPE_WORDS = 12
BIRTH_SCOPE_CHARS = 120
_SCOPE_TOKEN = re.compile(r"[^\W\d_]+|[0-9]|[.;!?](?=\s|$)|\n")


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

    def __init__(self, language: str = "fr") -> None:
        """Prépare les motifs et déclare le type pris en charge dans la langue du document."""
        self._regex = re.compile(self.expression, self.regex_flags)
        self.language = language
        super().__init__(supported_entities=[self.entity_type.value], supported_language=language)

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
            context = _fold(text[max(0, start - 40) : start].translate(_NONBREAKING_SPACES))
            has_context = re.search(self.context_expression, context) is not None
            score, source = self._evaluate(
                text[start:end].translate(_NONBREAKING_SPACES), has_context
            )
            if score:
                results.append(self._result(start, end, score, source))
        return results

    def _result(self, start: int, end: int, score: float, source: Source) -> RecognizerResult:
        """Construit le résultat Presidio de [start, end) avec sa source huisclos."""
        return RecognizerResult(
            entity_type=self.entity_type.value,
            start=start,
            end=end,
            score=score,
            recognition_metadata={"recognizer_name": self.name, "huisclos_source": source.value},
        )


class NirRecognizer(_LocalRecognizer):
    """Repère les NIR, y compris ceux dont la clé est probablement mal recopiée."""

    entity_type = EntityType.NIR
    expression = (
        rf"(?<!\w)[0-9]{_SEPARATOR}[0-9]{{2}}{_SEPARATOR}[0-9]{{2}}{_SEPARATOR}"
        rf"(?:[0-9]{{2}}|2[AB]){_SEPARATOR}[0-9]{{3}}{_SEPARATOR}"
        rf"[0-9]{{3}}{_SEPARATOR}[0-9]{{2}}(?!\w)"
    )
    context_expression = (
        r"\b(?:securite\s+sociale|n[°o]\s*ss|nir|insee|immatriculation|social\s+security)\b"
    )

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value 1 avec clé correcte, 0,40 si plausible, sinon zéro."""
        if nir_is_valid(value):
            return 1.0, Source.CHECKSUM
        return (0.40 if nir_structure_is_plausible(value) else 0.0), Source.PATTERN


class SirenRecognizer(_LocalRecognizer):
    """Repère les SIREN à clé de Luhn correcte, et ceux à clé fausse près d'un libellé."""

    entity_type = EntityType.SIREN
    expression = (
        rf"(?<![0-9])(?:[0-9]{{9}}|[0-9]{{3}}{_SPACE}[0-9]{{3}}"
        rf"{_SPACE}[0-9]{{3}})(?![0-9])"
    )
    context_expression = r"\b(?:siren|rcs|immatriculee?|registre\s+du\s+commerce)\b"
    # Libellé exigé, à courte distance, pour un SIREN à clé fausse (D-S35-1).
    label_expression = r"\b(?:siren|rcs)\b"
    label_window = 25

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        """Ajoute aux SIREN à clé correcte ceux à clé fausse précédés d'un libellé.

        Une clé fausse près de "SIREN" ou "RCS" signale une faute de frappe probable, donc
        un numéro encore sensible ; sans libellé, neuf chiffres peuvent être un montant.
        """
        results = super().analyze(text, entities, nlp_artifacts)
        if self.entity_type.value not in entities:
            return results
        found = {(result.start, result.end) for result in results}
        for start, end in self._candidates(text):
            context = _fold(text[max(0, start - self.label_window) : start])
            if (start, end) not in found and re.search(self.label_expression, context):
                results.append(self._result(start, end, INVALID_KEY_SCORE, Source.PATTERN))
        return results

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
        r"(?:\.[A-Z0-9!#$%&'*+/=?^`{|}~-]{1,64}){0,10}"
        r"(?:@|[ \t]{0,3}\[at\][ \t]{0,3})"
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.){1,10}[A-Z]{2,63}"
        r"(?![\w@-])"
    )


class PhoneFrRecognizer(_LocalRecognizer):
    """Repère les téléphones français nationaux et internationaux."""

    entity_type = EntityType.PHONE
    expression = (
        r"(?<![\w+])(?:0|(?:\+33|0033)[ .\u00a0\u202f-]?(?:\(0\)[ .\u00a0\u202f-]?)?)"
        r"[1-9](?:[ .\u00a0\u202f-]?[0-9]{2}){4}(?!\w)"
        r"(?:[ \t]{1,3}(?:poste|ext(?:ension)?\.?)[ \t]{0,3}:?[ \t]{0,3}[0-9]{1,6}(?!\w))?"
    )
    context_expression = PHONE_CONTEXT

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Renvoie pour value 0,90 avec contexte téléphonique, sinon 0,75."""
        return (0.90 if has_context else 0.75), Source.PATTERN


class BirthDateRecognizer(_LocalRecognizer):
    """Repère les dates uniquement dans la portée d'un contexte explicite de naissance."""

    entity_type = EntityType.BIRTH_DATE
    # Une année sur deux chiffres n'est pas suivie d'un autre groupe : "06.12.34.56" est un
    # téléphone, pas une date.
    expression = (
        r"(?<!\w)(?:[0-9]{1,2}(?P<separator>[/.-])[0-9]{1,2}(?P=separator)"
        r"(?:[0-9]{4}|[0-9]{2}(?![./-]?[0-9]))|"
        r"(?:1er|[0-9]{1,2})[ ]{1,3}(?:janvier|février|fevrier|mars|avril|mai|juin|"
        r"juillet|août|aout|septembre|octobre|novembre|décembre|decembre)[ ]{1,3}[0-9]{4})(?!\w)"
    )
    months = (
        "janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre"
    ).split()
    keywords = frozenset({"ne", "nee", "naissance"})
    # Un événement daté entre le contexte et la date coupe la portée (date d'audience).
    stops = frozenset(
        """
        audience audiences jugement arret ordonnance decision delibere convocation signature
        signe signee rendu rendue fait faite courrier lettre requete assignation saisine
        contrat acte reunion entretien licenciement embauche depuis echeance effet livraison
        facture paiement versement notification envoi reception mariage
        """.split()
    )

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Garde les dates de text dont la portée locale contient un mot de naissance."""
        for start, end in super()._candidates(text):
            if self.in_scope(text, start):
                yield start, end

    def window(self, text: str, start: int) -> str:
        """Texte lu avant la date : BIRTH_SCOPE_CHARS caractères au plus."""
        return text[max(0, start - BIRTH_SCOPE_CHARS) : start]

    def in_scope(self, text: str, start: int) -> bool:
        """Dit si un mot de naissance précède la date qui commence à start, dans sa portée.

        La portée remonte au plus BIRTH_SCOPE_WORDS mots et une fin de ligne ; elle s'arrête
        sur un chiffre (autre date ou numéro), une fin de phrase ou un mot d'événement.
        Exemple : "née à Valbrune (Nord) le 3 mars 1981" a un contexte ; "après la
        naissance du litige, l'audience du 3 mai 2026" n'en a pas.
        """
        tokens = list(_SCOPE_TOKEN.finditer(self.window(text, start)))
        words = newlines = 0
        for index in range(len(tokens) - 1, -1, -1):
            value = tokens[index].group()
            if value == "\n":
                newlines += 1
                if newlines > 1:
                    return False
                continue
            folded = _fold(value)
            if value[0].isdigit() or value in ".;!?" or folded in self.stops:
                return False
            words += 1
            if words > BIRTH_SCOPE_WORDS:
                return False
            if folded in self.keywords and self._is_birth_word(value, tokens[index + 1 :]):
                return True
        return False

    @staticmethod
    def _is_birth_word(word: str, following: list[re.Match[str]]) -> bool:
        """Écarte la négation "ne" : seul "né" accentué, ou "ne le", "ne à", est retenu."""
        if _fold(word) != "ne" or word.lower() != "ne":
            return True
        return bool(following) and _fold(following[0].group()) in {"le", "a", "en"}

    def _evaluate(self, value: str, has_context: bool) -> tuple[float, Source]:
        """Vérifie la date value dans le calendrier et renvoie 0,90, sinon zéro."""
        parts = re.split(r"[/.\- ]+", _fold(value).replace("1er", "1"))
        if parts[1] in self.months:
            month = self.months.index(parts[1]) + 1
        else:
            month = int(parts[1])
        valid = is_calendar_date(full_year(parts[2]), month, int(parts[0]))
        return (0.90 if valid else 0.0), Source.PATTERN


class CaseNumberRecognizer(_LocalRecognizer):
    """Repère les numéros RG et Portalis en laissant leur libellé visible."""

    entity_type = EntityType.CASE_NUMBER
    # Le libellé peut être séparé de la valeur par des blancs, un "n°" ou deux lignes au
    # plus, jamais par un mot (D-AF-A2-3) ; "23 / 00045" et "24-01234" restent des RG.
    expression = (
        r"(?:\bR\.?[ ]?G\.?(?:[ ]{0,3}n[°o]\.?)?|\bn[°o]\.?[ ]{0,3}R\.?[ ]?G\.?|"
        rf"(?P<portalis>\bPortalis))(?:{LABEL_GAP}n[°o]\.?)?{LABEL_GAP}:?{LABEL_GAP}"
        r"(?P<value>(?(portalis)"
        r"[A-Z0-9]{1,12}(?:-[A-Z0-9]{1,12}){3}(?![\w-])|"
        r"(?:F[ ]{0,3})?(?:[0-9]{4}|[0-9]{2})[ ]{0,2}[/-][ ]{0,2}[0-9]{5}(?!\w)))"
    )

    def _candidates(self, text: str) -> Iterator[tuple[int, int]]:
        """Complète RG et Portalis par les numéros de parquet et de pourvoi libellés."""
        yield from super()._candidates(text)
        yield from procedure_candidates(text.translate(_NONBREAKING_SPACES))


class AddressRecognizer(_LocalRecognizer):
    """Repère une voie, une adresse complète ou un couple code postal et ville.

    L'assembleur borné de detection.address_bounds remplace une expression unique toujours
    plus large ; les scores D-07 dépendent de la nature de l'adresse trouvée.
    """

    entity_type = EntityType.ADDRESS
    expression = r"(?!)"

    def analyze(
        self, text: str, entities: list[str], nlp_artifacts: NlpArtifacts | None = None
    ) -> list[RecognizerResult]:
        """Renvoie 0,70 pour une adresse complète, 0,55 pour la voie, 0,45 pour la ville."""
        if self.entity_type.value not in entities:
            return []
        spans = address_spans(text.translate(_NONBREAKING_SPACES), self.language)
        return [
            self._result(span.start, span.end, ADDRESS_SCORES[span.kind], Source.PATTERN)
            for span in spans
        ]


def build_pattern_recognizers(language: str = "fr") -> list[EntityRecognizer]:
    """Renvoie les reconnaisseurs de la langue du document dans un ordre stable.

    Les identifiants français (NIR, SIREN, SIRET, IBAN, téléphones, RG) restent reconnus
    dans un document anglais ; celui-ci reçoit en plus les motifs de english_patterns.
    """
    from huisclos.detection.english_patterns import birth_recognizer, language_recognizers
    from huisclos.detection.labeled_identifiers import LabeledIdentifierRecognizer

    return [
        NirRecognizer(language),
        SirenRecognizer(language),
        SiretRecognizer(language),
        IbanRecognizer(language),
        EmailRecognizer(language),
        PhoneFrRecognizer(language),
        birth_recognizer(language),
        CaseNumberRecognizer(language),
        AddressRecognizer(language),
        LabeledIdentifierRecognizer(language),
        *language_recognizers(language),
    ]
