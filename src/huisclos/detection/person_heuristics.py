"""Heuristiques de repérage des personnes : civilité + nom, Prénom NOM, NOM Prénom.

Entrées : un texte français et, en option, l'ensemble des acronymes à ne pas prendre pour un nom.
Sorties : des RecognizerResult PERSON de langue "fr" et de source "heuristic".
Place dans le pipeline : complète le NER spaCy, qui oublie souvent les noms en majuscules ;
les scores suivent le barème D-07 (0,80 avec civilité, 0,70 sans).
"""

import re
from collections.abc import Iterator
from typing import Final

from presidio_analyzer import LocalRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.detection.exclusions import load_exclusions
from huisclos.models import Source
from huisclos.text_utils import CIVILITIES

LANGUAGE: Final = "fr"
CIVILITY_SCORE: Final = 0.80
NAME_PATTERN_SCORE: Final = 0.70

_UPPER = "A-ZÀ-ÖØ-ÞŒ"
_LOWER = "a-zà-öø-ÿœ"
_APOSTROPHE = "['\u2019]"
# Seuls l'espace et les espaces insécables relient les mots d'un nom : un retour à la ligne
# sépare presque toujours deux informations distinctes.
_SPACE = "[ \u00a0\u202f]+"

# Un mot à initiale majuscule (Dupont) ou tout en majuscules (DUPONT), avec traits d'union et
# apostrophes (Jean-Pierre, O'Brien).
_TITLE_PIECE = rf"[{_UPPER}][{_LOWER}]+"
_UPPER_PIECE = rf"[{_UPPER}]{{2,}}"
_ANY_PIECE = rf"(?:{_TITLE_PIECE}|{_UPPER_PIECE})"
_INITIALS = rf"[{_UPPER}]\.(?:-?[{_UPPER}]\.){{0,2}}"
_NAME_WORD = rf"(?:{_INITIALS}|(?:[{_UPPER}]{_APOSTROPHE})?{_ANY_PIECE}(?:-{_ANY_PIECE})*)(?!\w)"
_TITLE_WORD = rf"{_TITLE_PIECE}(?:-{_TITLE_PIECE})*(?!\w)"
_UPPER_WORD = rf"{_UPPER_PIECE}(?:-{_UPPER_PIECE})*(?!\w)"

_CIVILITY = re.compile(
    r"(?<![\w.])(?:M\.|MM\.|(?:Mmes?|Mlle|Me|Dr|Pr)\.?|[Mm]onsieur|[Mm]adame|[Mm]ademoiselle"
    r"|[Mm]aître|[Dd]octeur|[Pp]rofesseur)[ \u00a0\u202f]+"
)
_NAME_WORD_RE = re.compile(_NAME_WORD)
_PARTICLE = r"(?:de|du|des|van|von|der|den|[Ll]e|[Ll]a|les)"
_PARTICLE_RE = re.compile(rf"(?:(?:{_PARTICLE}{_SPACE}){{1,4}}|d{_APOSTROPHE})")
_SPACE_RE = re.compile(_SPACE)
_NAME_SPACE_RE = re.compile(r"[ \u00a0\u202f\t]*(?:\r?\n)?[ \u00a0\u202f\t]*")

_FIRST_UPPER = re.compile(
    rf"(?<![\w'\u2019-])(?P<first>{_TITLE_WORD}|{_INITIALS})"
    rf"(?:{_SPACE}{_PARTICLE}){{0,4}}(?P<upper>(?:{_SPACE}{_UPPER_WORD})+)"
)
_UPPER_RUN = re.compile(rf"(?<![\w'\u2019-])(?P<upper>{_UPPER_WORD}(?:{_SPACE}{_UPPER_WORD})*)")
_TITLE_WORD_RE = re.compile(_TITLE_WORD)
_ROMAN = re.compile(r"[IVXLCDM]+")

# Mots courants qui ouvrent une phrase ou introduisent un texte juridique : ils ne sont pas des
# prénoms. Comparaison en minuscules, sur chaque mot de la candidate.
COMMON_STARTERS: Final = frozenset(
    """
    le la les un une des du de au aux ce cet cette ces son sa ses mon ma mes notre votre leur
    leurs il elle ils elles on nous vous je tu et ou mais donc or ni car si comme lorsque quand
    que qui dont selon par pour dans chez avec sans sur sous entre contre vers dès depuis
    pendant avant après suivant conformément attendu vu considérant article articles alinéa
    chapitre titre section livre annexe pièce pièces page décision jugement arrêt ordonnance
    contrat société cabinet tribunal cour conseil code loi décret dossier affaire monsieur
    madame mademoiselle maître docteur professeur mme mlle me dr pr messieurs mesdames rue
    avenue boulevard place allée impasse chemin quai route cours fait ci fin objet date lieu
    total montant tél tel fax email courriel n siret siren iban bic
    """.split()
)

# Titres de fonction : "Monsieur Le Président" désigne une fonction, pas un nom de famille.
TITLE_WORDS: Final = frozenset(
    """
    président présidente vice-président juge juges procureur directeur directrice maire
    ministre bâtonnier greffier greffière conseiller conseillère rapporteur avocat avocate
    """.split()
)

_ARTICLES: Final = frozenset({"le", "la", "les"})
SURNAME_PARTICLES: Final = frozenset({"de", "du", "des", "le", "la", "les"})


def _is_rejected(lead: str, upper_words: list[str], acronyms: frozenset[str]) -> bool:
    """Vrai si la candidate n'est pas un nom de personne.

    lead est le premier mot significatif (un mot courant de début de phrase l'écarte) ;
    upper_words sont les mots en majuscules (un acronyme connu, ou une suite de chiffres
    romains comme "IV", les écarte).
    """
    if lead.lower() in COMMON_STARTERS or lead.lower().rstrip(".") in CIVILITIES:
        return True
    if any(word in acronyms for word in upper_words):
        return True
    return all(_ROMAN.fullmatch(word) for word in upper_words)


def _result(recognizer: LocalRecognizer, start: int, end: int, score: float) -> RecognizerResult:
    """Fabrique un résultat PERSON marqué de la source heuristic."""
    return RecognizerResult(
        entity_type="PERSON",
        start=start,
        end=end,
        score=score,
        recognition_metadata={
            RecognizerResult.RECOGNIZER_NAME_KEY: recognizer.name,
            RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: recognizer.id,
            "huisclos_source": Source.HEURISTIC.value,
        },
    )


class _PersonHeuristic(LocalRecognizer):
    """Base commune : un reconnaisseur PERSON français dont les spans viennent de _spans."""

    score: float = NAME_PATTERN_SCORE

    def __init__(self, acronyms: frozenset[str] | None = None) -> None:
        """Prépare le reconnaisseur.

        Paramètre : acronyms, les acronymes exclus (ceux de data/exclusions_fr.txt par défaut).
        """
        self.acronyms = load_exclusions().acronyms if acronyms is None else acronyms
        super().__init__(supported_entities=["PERSON"], supported_language=LANGUAGE)

    def load(self) -> None:  # noqa: D102
        pass

    def _spans(self, text: str) -> Iterator[tuple[int, int]]:
        """Produit les positions (début, fin) des noms trouvés dans le texte."""
        raise NotImplementedError

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None = None,
    ) -> list[RecognizerResult]:
        """Renvoie un résultat PERSON par nom trouvé, ou rien si PERSON n'est pas demandé."""
        if entities and "PERSON" not in entities:
            return []
        return [_result(self, start, end, self.score) for start, end in self._spans(text)]


class CivilityPersonRecognizer(_PersonHeuristic):
    """Civilité suivie d'un prénom facultatif et d'un nom : "Monsieur Jean Dupont" (0,80).

    Le span commence après la civilité (D-09). "Monsieur le Président" ou "Maître de stage"
    ne donnent rien, car le mot suivant n'est ni une majuscule ni un nom.
    """

    score = CIVILITY_SCORE
    MAX_WORDS = 4

    def _spans(self, text: str) -> Iterator[tuple[int, int]]:
        for civility in _CIVILITY.finditer(text):
            start = civility.end()
            first = self._word_at(text, start)
            if first is None:
                continue
            end, count = first.end(), 1
            while count < self.MAX_WORDS:
                spaces = _NAME_SPACE_RE.match(text, end)
                following = (
                    self._word_at(text, spaces.end()) if spaces and spaces.end() > end else None
                )
                if following is None:
                    break
                end, count = following.end(), count + 1
            yield start, end

    def _word_at(self, text: str, position: int) -> re.Match[str] | None:
        """Renvoie le mot de nom qui commence à position, après une particule éventuelle.

        Renvoie None si ce n'est pas un nom : mot courant, titre de fonction ou acronyme.
        Le groupe 0 du résultat commence au mot, la particule éventuelle est déjà sautée.
        """
        particle = _PARTICLE_RE.match(text, position)
        word = _NAME_WORD_RE.match(text, particle.end() if particle else position)
        if word is None:
            return None
        lowered = word.group().lower()
        if lowered in _ARTICLES:
            return word if self._article_leads_name(text, word.end()) else None
        if lowered in COMMON_STARTERS or lowered in TITLE_WORDS or word.group() in self.acronyms:
            return None
        return word

    @staticmethod
    def _article_leads_name(text: str, position: int) -> bool:
        """Vrai si l'article est suivi d'un nom : "Le Gall" oui, "Le Président" non."""
        spaces = _SPACE_RE.match(text, position)
        if spaces is None:
            return False
        following = _NAME_WORD_RE.match(text, spaces.end())
        return following is not None and following.group().lower() not in TITLE_WORDS


class FirstNameUpperSurnameRecognizer(_PersonHeuristic):
    """Prénom à initiale majuscule puis nom en majuscules : "Marie-Claire LE GALL" (0,70)."""

    def _spans(self, text: str) -> Iterator[tuple[int, int]]:
        for match in _FIRST_UPPER.finditer(text):
            upper_words = match.group("upper").split()
            if not _is_rejected(match.group("first"), upper_words, self.acronyms):
                yield match.start(), match.end()


class UpperSurnameFirstNameRecognizer(_PersonHeuristic):
    """Nom en majuscules puis prénom à initiale majuscule : "DUPONT Jean" (0,70)."""

    def _spans(self, text: str) -> Iterator[tuple[int, int]]:
        # Consommer la suite une seule fois évite de réessayer tous ses suffixes quand
        # aucun prénom ne suit, ce qui coûtait un temps quadratique sur les actes en capitales.
        for match in _UPPER_RUN.finditer(text):
            spaces = _SPACE_RE.match(text, match.end())
            first = _TITLE_WORD_RE.match(text, spaces.end()) if spaces else None
            if first is None:
                continue
            upper_words = match.group("upper").split()
            # Les particules ("DE LA FONTAINE Jean") ne comptent pas comme premier mot.
            lead = next((w for w in upper_words if w.lower() not in SURNAME_PARTICLES), "")
            if lead and first.group().lower() not in COMMON_STARTERS:
                if not _is_rejected(lead, upper_words, self.acronyms):
                    yield match.start(), first.end()


def build_person_recognizers(acronyms: frozenset[str] | None = None) -> list[LocalRecognizer]:
    """Renvoie les trois reconnaisseurs de personnes.

    Paramètre : acronyms, les acronymes à ne pas prendre pour un nom (par défaut, ceux de
    data/exclusions_fr.txt).
    """
    return [
        CivilityPersonRecognizer(acronyms),
        FirstNameUpperSurnameRecognizer(acronyms),
        UpperSurnameFirstNameRecognizer(acronyms),
    ]
