"""Assemble les adresses autour d'ancrages solides, dans des bornes explicites.

Entrées : un texte (la vue d'analyse) et la langue du document.
Sorties : des AddressSpan (début, fin, nature) : adresse complète, voie seule ou ligne
postale seule, aux positions du texte reçu.
Place dans le pipeline : appelé par le reconnaisseur ADDRESS, avant la fusion. Une adresse
complète forme un seul span jusqu'à sa ville et ses compléments postaux (D-09, D-AF-A2-2).
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from huisclos.detection import address_patterns as motifs
from huisclos.text_utils import fold, is_capitalized_form

# Bornes d'une adresse complète : segments après la voie, sauts de ligne et longueur.
MAX_SEGMENTS = 6
MAX_LINES = 4
MAX_CHARS = 220
MAX_NAME_WORDS = 6


class AddressKind(str, Enum):  # noqa: UP042 (même contrat que EntityType)
    """Nature d'une adresse trouvée ; elle fixe le score D-07."""

    FULL = "full"
    STREET = "street"
    POSTAL = "postal"


# Barème D-07 : adresse complète, voie sans code postal, code postal et ville seuls.
SCORES = {AddressKind.FULL: 0.70, AddressKind.STREET: 0.55, AddressKind.POSTAL: 0.45}


@dataclass(frozen=True)
class AddressSpan:
    """Une adresse trouvée : début inclus, fin exclue, nature."""

    start: int
    end: int
    kind: AddressKind


@dataclass(frozen=True)
class AddressRules:
    """Ancrages d'une langue : voies, lieux nommés, compléments et lignes postales.

    street_heads se prolongent par un nom lu mot à mot (voies françaises) ; named_heads
    contiennent déjà leur nom (voies anglaises) ; full_only_heads (boîte postale, lieu-dit)
    ne valent adresse que suivis de leur ligne postale.
    """

    street_heads: tuple[re.Pattern[str], ...]
    named_heads: tuple[re.Pattern[str], ...]
    full_only_heads: tuple[re.Pattern[str], ...]
    complements: tuple[re.Pattern[str], ...]
    postal: tuple[re.Pattern[str], ...]


def _compile(expression: str, ignore_case: bool = False) -> re.Pattern[str]:
    """Compile une expression de motifs, sensible à la casse sauf demande contraire."""
    return re.compile(expression, re.IGNORECASE if ignore_case else 0)


_FRENCH = AddressRules(
    street_heads=(_compile(motifs.STREET_HEAD, True),),
    named_heads=(),
    full_only_heads=(_compile(motifs.POSTBOX, True), _compile(motifs.NAMED_PLACE, True)),
    complements=(_compile(motifs.COMPLEMENT, True),),
    postal=(_compile(motifs.POSTAL_CITY),),
)
RULES = {
    "fr": _FRENCH,
    "en": AddressRules(
        street_heads=_FRENCH.street_heads,
        named_heads=(_compile(motifs.EN_STREET_HEAD),),
        full_only_heads=(*_FRENCH.full_only_heads, _compile(motifs.EN_POSTBOX, True)),
        complements=(*_FRENCH.complements, _compile(motifs.EN_COMPLEMENT)),
        postal=(*_FRENCH.postal, _compile(motifs.US_POSTAL), _compile(motifs.UK_POSTAL)),
    ),
}

# Séparateur de segments : blancs, virgule, barre de tableau, tiret entouré de blancs, puis
# un seul saut de ligne. Un point ou un point-virgule termine l'adresse.
_SEPARATOR = re.compile(
    r"[ \t]*(?:[,|][ \t]*|[-\u2013\u2014](?:[ \t]+|(?=\r?\n)))?(?:\r?\n[ \t]*)?"
)
_LABEL = re.compile(r"[^\W\d_]+\.?[ \t]*:")
_LOCALITY = re.compile(
    r"[A-ZÀ-ÖØ-Þ][^\W\d_'\u2019-]*(?:[ '\u2019-][A-ZÀ-ÖØ-Þ][^\W\d_]*){0,3}(?!\w)"
)
_NAME_TOKEN = re.compile(
    r"[^\W\d_]+(?:['\u2019-](?:[ \t]*\r?\n[ \t]*)?[^\W\d_]+)*|[0-9]{1,5}(?!\w)"
)
_SPACES = re.compile(r"[ \t]{1,3}")
_NEWLINE_SPACES = re.compile(r"[ \t]{0,3}\r?\n[ \t]{0,3}")
# Une ligne postale n'est jamais lue juste après un libellé de référence ou de procédure.
_REFERENCE_BEFORE = re.compile(
    r"(?i)(?:\bRG|n[°o]\.?|\bdossier|\baffaire|\br[ée]f\.?|\bpourvoi|\bparquet|\bportalis)"
    r"[ \t:.]*(?:[0-9]+[ \t]*[/.-][ \t]*)*$"
)
# Mots liés au nom de la voie quand un nom les suit ; mots qui reprennent la phrase.
_PARTICLES = frozenset("de du des la le les l' d' au aux et sur sous les en".split())
# Comparés en minuscules avec leurs accents, et seulement pour un mot sans majuscule :
# "près" arrête la voie, "Prés" (rue des Prés) en fait partie.
_STOP_WORDS = frozenset(
    """
    à a depuis dans pour par avec chez qui que qu dont est sont était sera puis lors pendant
    selon sans entre vers près face avant après jusqu ainsi mais donc car ni si ne se il elle
    ils elles on nous vous je ou où
    """.split()
)


def _read_name(text: str, position: int, allow_newline: bool) -> list[int]:
    """Fins possibles du nom d'une voie française lu à partir de position.

    Paramètres : text, le texte ; position, la fin du type de voie ; allow_newline, vrai
    pour un nom coupé par une fin de ligne avant sa ligne postale.
    Valeur retournée : les positions après chaque mot retenu, dans l'ordre. Le nom s'arrête
    sur une ponctuation, un mot qui reprend la phrase ("à", "depuis"), un libellé suivi de
    deux-points, un code postal ou au bout de MAX_NAME_WORDS mots. Un nombre n'y entre que
    sous forme de date ("rue du 8 Mai 1945").
    """
    ends: list[int] = []
    cursor, previous = position, ""
    while len(ends) < MAX_NAME_WORDS:
        gap = (_NEWLINE_SPACES.match(text, cursor) if allow_newline else None) or _SPACES.match(
            text, cursor
        )
        token = _NAME_TOKEN.match(text, gap.end()) if gap else None
        if token is None or _LABEL.match(text, token.start()):
            break
        word, folded = token.group(), fold(token.group())
        if word.isdigit():
            following = _NAME_TOKEN.match(text, token.end() + 1)
            date_day = len(word) <= 2 and following and is_capitalized_form(following.group())
            year = len(word) == 4 and is_capitalized_form(previous)
            if not (date_day or year):
                break
        elif word.lower() in _STOP_WORDS and not is_capitalized_form(word):
            break
        elif folded in _PARTICLES:
            cursor, previous = token.end(), word
            continue
        cursor, previous = token.end(), word
        ends.append(cursor)
    return ends


def _postal_at(text: str, position: int, rules: AddressRules) -> int | None:
    """Fin de la ligne postale qui commence exactement à position, ou None."""
    for pattern in rules.postal:
        match = pattern.match(text, position)
        if match:
            return match.end()
    return None


def _complement_at(text: str, position: int, rules: AddressRules) -> int | None:
    """Fin du complément (bâtiment, appartement, boîte postale) qui commence à position."""
    for pattern in rules.complements:
        match = pattern.match(text, position)
        if match:
            return match.end()
    return None


def _chain(text: str, start: int, position: int, rules: AddressRules) -> int | None:
    """Suit les compléments après position jusqu'à une ligne postale, dans les bornes.

    Paramètres : start, le début de l'adresse ; position, la fin de la voie.
    Valeur retournée : la fin de la ligne postale atteinte, ou None si un paragraphe, un
    libellé, une autre information ou une borne arrête la lecture avant elle.
    """
    for _ in range(MAX_SEGMENTS):
        following = _SEPARATOR.match(text, position).end()
        if following == position or text.count("\n", start, following) > MAX_LINES:
            return None
        if following - start > MAX_CHARS or _LABEL.match(text, following):
            return None
        postal = _postal_at(text, following, rules)
        if postal is not None:
            return postal if postal - start <= MAX_CHARS else None
        complement = _complement_at(text, following, rules)
        if complement is None:
            # Une localité seule ("Wimbledon") n'est admise que juste avant la ligne postale.
            locality = _LOCALITY.match(text, following)
            if locality is None:
                return None
            after = _SEPARATOR.match(text, locality.end()).end()
            postal = _postal_at(text, after, rules) if after > locality.end() else None
            return postal if postal is not None and postal - start <= MAX_CHARS else None
        position = complement
    return None


def _assemble_street(text: str, start: int, head_end: int, rules: AddressRules) -> AddressSpan:
    """Adresse complète si une ligne postale suit la voie, sinon voie seule."""
    strict = _read_name(text, head_end, allow_newline=False)
    for end in strict or [head_end]:
        full = _chain(text, start, end, rules)
        if full is not None:
            return AddressSpan(start, full, AddressKind.FULL)
    for end in _read_name(text, head_end, allow_newline=True)[len(strict) :]:
        full = _chain(text, start, end, rules)
        if full is not None:
            return AddressSpan(start, full, AddressKind.FULL)
    return AddressSpan(start, strict[-1] if strict else head_end, AddressKind.STREET)


def _heads(text: str, rules: AddressRules) -> Iterator[tuple[int, int, str]]:
    """Ancrages de voie du texte : (début, fin, sorte), sorte street, named ou full_only."""
    groups = (
        ("street", rules.street_heads),
        ("named", rules.named_heads),
        ("full_only", rules.full_only_heads),
    )
    for kind, patterns in groups:
        for pattern in patterns:
            for match in pattern.finditer(text):
                yield match.start(), match.end(), kind


def _assemble(
    text: str, start: int, end: int, kind: str, rules: AddressRules
) -> AddressSpan | None:
    """Assemble l'adresse qui part d'un ancrage, ou None pour un ancrage insuffisant."""
    if kind == "street":
        street = _assemble_street(text, start, end, rules)
        return street if street.kind == AddressKind.FULL or street.end > end else None
    if kind == "named":
        full = _chain(text, start, end, rules)
        return AddressSpan(
            start, full if full else end, AddressKind.FULL if full else AddressKind.STREET
        )
    names = _read_name(text, end, allow_newline=False)
    for name_end in [end, *names]:
        full = _chain(text, start, name_end, rules)
        if full is not None:
            return AddressSpan(start, full, AddressKind.FULL)
    return None


def _isolated_postal(text: str, match: re.Match[str]) -> bool:
    """Vrai si une ligne postale seule n'est pas la suite d'une référence ("RG : 23 / 00045")."""
    line_start = text.rfind("\n", 0, match.start()) + 1
    before = text[max(line_start, match.start() - 40) : match.start()]
    return _REFERENCE_BEFORE.search(before) is None


def address_spans(text: str, language: str = "fr") -> list[AddressSpan]:
    """Adresses de text, triées et sans chevauchement.

    Paramètres : text, le texte analysé ; language, la langue du document (fr ou en ; les
    ancrages français restent actifs dans un document anglais).
    Valeur retournée : les AddressSpan trouvés. Les ancrages sont examinés dans l'ordre du
    texte, le plus long d'abord ; un ancrage pris dans une adresse déjà assemblée est
    ignoré ; une ligne postale isolée forme une adresse partielle.
    Exemple : address_spans("Domicile : 12 bis, rue Haute, 75011 Paris") donne une seule
    adresse complète, de "12" à "Paris".
    """
    rules = RULES[language]
    found: list[AddressSpan] = []
    for start, end, kind in sorted(_heads(text, rules), key=lambda h: (h[0], -h[1])):
        if found and start < found[-1].end:
            continue
        span = _assemble(text, start, end, kind, rules)
        if span is not None:
            found.append(span)
    for pattern in rules.postal:
        for match in pattern.finditer(text):
            overlaps = any(s.start < match.end() and match.start() < s.end for s in found)
            if not overlaps and _isolated_postal(text, match):
                found.append(AddressSpan(match.start(), match.end(), AddressKind.POSTAL))
    return sorted(found, key=lambda span: (span.start, span.end))
