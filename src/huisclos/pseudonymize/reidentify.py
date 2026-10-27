"""Restauration des vraies valeurs dans un texte à jetons, par exemple la réponse d'un LLM.

Entrées : le texte reçu, la table de correspondance et, si on les a, les occurrences.
Sorties : un RestoreResult (texte restauré, mode, jetons remplacés, formes altérées ou
inconnues, jetons absents du texte).
Place dans le pipeline : dernière étape avant io.writers (décision D-10).
"""

import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from huisclos.models import LETTER_INDEXED, TOKEN_LABELS, EntityType, Occurrence
from huisclos.pseudonymize.mapping import Mapping, sha256_of

EXACT = "exact"
TOLERANT = "tolerant"

# Séparateur accepté entre deux mots du libellé et entre le libellé et l'indice : tiret
# bas, tiret bas échappé par Markdown, espace, espace insécable ou tiret.
_SEP = r"(?:\\?_|[ \u00a0-])"
_LABEL_TYPES: dict[str, EntityType] = {
    label: entity_type for entity_type, labels in TOKEN_LABELS.items() for label in labels
}
_PAIRS = {"[": "]", "(": ")", "{": "}", "<": ">", "\u00ab": "\u00bb"}
_PADDING = " \u00a0\\"
# Le libellé le plus long d'abord, pour que PERSONNE soit essayé avant PERSON.
_LABEL_ALTERNATION = "|".join(
    _SEP.join(re.escape(part) for part in label.split("_"))
    for label in sorted(_LABEL_TYPES, key=len, reverse=True)
)
_TOKEN_FORM = re.compile(
    r"(?P<open>\\?[\[({<\u00ab][ \u00a0]*)?"
    r"(?<![^\W_])(?P<label>(?i:"
    + _LABEL_ALTERNATION
    + r"))"
    + _SEP
    # La borne finale empêche PERSONNE_1 de capturer le début de PERSONNE_12, et
    # SOCIETE_A celui de SOCIETE_AB. Trois lettres suffisent : 18 278 sociétés.
    + r"(?P<index>\d+|[A-Za-z]{1,3})(?![^\W_])"
    r"(?P<close>[ \u00a0]*\\?[\])}>\u00bb])?"
)
# Un nombre qui se poursuit ("SIRET 732 829", "DOSSIER 2024/15") n'est pas un jeton.
_NUMBER_GOES_ON = re.compile(r"[ \u00a0.,/-]?\d")


@dataclass(frozen=True)
class RestoreResult:
    """Résultat d'une restauration.

    text est le texte restauré ; mode vaut "exact" ou "tolerant" ; replaced compte les
    remplacements par jeton ; altered liste les couples (forme rencontrée, jeton) quand
    la forme diffère du jeton ; unknown liste les couples (forme, position dans le texte
    reçu) des jetons absents de la table, laissés tels quels ; missing liste, pour
    information, les jetons de la table que le texte ne contient pas.
    """

    text: str
    mode: str
    replaced: dict[str, int]
    altered: list[tuple[str, str]]
    unknown: list[tuple[str, int]]
    missing: list[str]


@dataclass(frozen=True)
class TokenForm:
    """Une forme de jeton repérée dans un texte, éventuellement abîmée par le LLM.

    start et end délimitent la forme, crochets compris quand ils vont par paire ; un
    crochet isolé reste hors de la forme et donc dans le texte. index est en majuscules.
    """

    text: str
    start: int
    end: int
    entity_type: EntityType
    index: str


def _fold(text: str) -> str:
    """Retire les accents caractère par caractère, sans changer la longueur du texte.

    Garder la même longueur permet d'utiliser les positions trouvées dans la copie sans
    accents directement sur le texte d'origine.
    """
    return "".join(unicodedata.normalize("NFD", char)[0] for char in text)


def _label_type(folded_label: str) -> EntityType:
    """Type d'entité d'un libellé rencontré, quelle que soit sa casse ou son séparateur."""
    return _LABEL_TYPES[re.sub(_SEP, "_", folded_label).upper()]


def _is_paired(open_text: str | None, close_text: str | None) -> bool:
    """Indique si le crochet ouvrant et le crochet fermant forment une paire."""
    if not open_text or not close_text:
        return False
    return _PAIRS[open_text.strip(_PADDING)] == close_text.strip(_PADDING)


def _bare_form_ok(text: str, match: re.Match[str], entity_type: EntityType) -> bool:
    """Décide si une forme sans crochets est bien un jeton et non une phrase ordinaire.

    Il faut un libellé en majuscules ou un tiret bas, pour laisser intacte la phrase
    "aucune personne 1" ; l'indice doit avoir la bonne nature (lettres pour les sociétés)
    et ne pas être le début d'un nombre plus long.
    """
    core = text[match.start("label") : match.end("index")]
    label = text[match.start("label") : match.end("label")]
    if not (label.isupper() or "_" in core):
        return False
    if match["index"].isdigit() == (entity_type in LETTER_INDEXED):
        return False
    return "_" in core or not _NUMBER_GOES_ON.match(text, match.end("index"))


def find_token_forms(text: str) -> list[TokenForm]:
    """Repère les formes de jetons d'un texte, exactes ou altérées.

    Paramètre : text, le texte reçu.
    Valeur retournée : les formes dans l'ordre du texte, sans chevauchement.
    Exemple : find_token_forms("vu ( personne_1 )")[0].text == "( personne_1 )".
    """
    forms = []
    for match in _TOKEN_FORM.finditer(_fold(text)):
        entity_type = _label_type(match["label"])
        if _is_paired(match["open"], match["close"]):
            start, end = match.span()
        elif _bare_form_ok(text, match, entity_type):
            start, end = match.start("label"), match.end("index")
        else:
            continue
        forms.append(TokenForm(text[start:end], start, end, entity_type, match["index"].upper()))
    return forms


def _token_index(token: str, mapping: Mapping) -> str:
    """Indice d'un jeton de la table : "1" pour [PERSONNE_1], "AB" pour [SOCIETE_AB]."""
    style = mapping.token_style
    core = token[len(style.open_bracket) : len(token) - len(style.close_bracket)]
    return core.rpartition("_")[2].upper()


def _splice(text: str, spans: Sequence[tuple[int, int, str]]) -> str:
    """Remplace dans text chaque tranche (début, fin) par sa valeur ; spans est trié."""
    pieces, cursor = [], 0
    for start, end, value in spans:
        pieces.extend((text[cursor:start], value))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def _spans_from_occurrences(
    text: str, occurrences: Sequence[Occurrence]
) -> list[tuple[int, int, str, str]] | None:
    """Tranches (début, fin, jeton, original) tirées des occurrences, ou None si incohérentes."""
    spans, cursor = [], 0
    for occurrence in sorted(occurrences, key=lambda o: o.start):
        if occurrence.start < cursor or text[occurrence.start : occurrence.end] != occurrence.token:
            return None
        spans.append((occurrence.start, occurrence.end, occurrence.token, occurrence.original))
        cursor = occurrence.end
    return spans


def _spans_from_mapping(text: str, mapping: Mapping) -> list[tuple[int, int, str, str]] | None:
    """Tranches tirées des occurrences ordonnées de la table, ou None si ambiguës.

    Sans positions, chaque jeton est cherché dans l'ordre. Si le texte d'origine contenait
    déjà une chaîne identique à un jeton, la recherche pourrait se tromper d'endroit : on
    exige donc que chaque jeton apparaisse exactement autant de fois que dans la table.
    """
    expected = Counter(o.token for o in mapping.occurrences)
    if any(text.count(token) != count for token, count in expected.items()):
        return None
    spans, cursor = [], 0
    for occurrence in mapping.occurrences:
        start = text.find(occurrence.token, cursor)
        if start < 0:
            return None
        cursor = start + len(occurrence.token)
        spans.append((start, cursor, occurrence.token, occurrence.original))
    return spans


def _missing(mapping: Mapping, replaced: dict[str, int]) -> list[str]:
    """Jetons de la table qui n'ont été remplacés nulle part."""
    return [entry.token for entry in mapping.entities if not replaced.get(entry.token)]


def _restore_tolerant(text: str, mapping: Mapping) -> RestoreResult:
    """Mode tolérant : chaque forme est rapprochée de la table par (type, indice).

    La valeur restaurée est la forme canonique du groupe, car le LLM a pu déplacer ou
    reformuler les jetons : leur ordre ne permet plus de retrouver l'écriture exacte.
    """
    table = {(e.entity_type, _token_index(e.token, mapping)): e for e in mapping.entities}
    spans, replaced = [], Counter[str]()
    altered: list[tuple[str, str]] = []
    unknown: list[tuple[str, int]] = []
    for form in find_token_forms(text):
        entry = table.get((form.entity_type, form.index))
        if entry is None:
            unknown.append((form.text, form.start))
            continue
        spans.append((form.start, form.end, entry.canonical))
        replaced[entry.token] += 1
        if form.text != entry.token:
            altered.append((form.text, entry.token))
    return RestoreResult(
        _splice(text, spans),
        TOLERANT,
        dict(replaced),
        altered,
        unknown,
        _missing(mapping, replaced),
    )


def restore(
    text: str, mapping: Mapping, occurrences: Sequence[Occurrence] | None = None
) -> RestoreResult:
    """Remet les vraies valeurs à la place des jetons.

    Paramètres : text, le texte reçu (texte pseudonymisé ou réponse du LLM) ; mapping, la
    table de correspondance ; occurrences, les occurrences positionnées produites par
    pseudonymize, si on les a encore.
    Valeur retournée : un RestoreResult. Le mode exact s'applique quand le texte reçu est
    exactement le texte pseudonymisé (même empreinte SHA-256) : chaque occurrence retrouve
    alors son écriture d'origine. Sinon, le mode tolérant restaure la forme canonique.
    Exemple : restore("Vu [PERSONNE_1].", mapping).text == "Vu Jean DUPONT."
    """
    if sha256_of(text) == mapping.pseudonymized_sha256:
        if occurrences is not None:
            spans = _spans_from_occurrences(text, occurrences)
        else:
            spans = _spans_from_mapping(text, mapping)
        if spans is not None:
            replaced = dict(Counter(token for _, _, token, _ in spans))
            return RestoreResult(
                _splice(text, [(start, end, original) for start, end, _, original in spans]),
                EXACT,
                replaced,
                [],
                [],
                _missing(mapping, replaced),
            )
    return _restore_tolerant(text, mapping)
