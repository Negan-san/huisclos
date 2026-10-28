"""Regroupement des mentions d'une même entité avant l'attribution des jetons.

Entrées : le texte et ses détections validées (triées, sans chevauchement).
Sorties : une liste d'EntityGroup dans l'ordre de première apparition, jeton encore vide.
Place dans le pipeline : après la revue humaine, avant pseudonymize.tokens. Dans le doute,
un groupe distinct est créé : un jeton de plus vaut mieux qu'une confusion entre personnes.
"""

import datetime
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from huisclos.models import Detection, EntityGroup, EntityType
from huisclos.text_utils import CIVILITIES, LEGAL_FORMS, fold

# Mot d'un nom après repliement : lettres, éventuellement reliées par un trait d'union ou
# une apostrophe ("jean-pierre", "d'aubigne"). Les points des initiales sont ignorés.
_WORD = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*")

_LEGAL_FORMS_FOLDED = frozenset(form.lower() for form in LEGAL_FORMS)
# Mots qui ne distinguent pas une société d'une autre : "la société Atelier Verlaine" et
# "Atelier Verlaine SAS" désignent la même entreprise.
_ORGANIZATION_NOISE = frozenset({"societe", "ste"})
_ARTICLES = frozenset({"la", "le", "les", "l"})

_ADDRESS_ABBREVIATIONS = {
    "av": "avenue",
    "ave": "avenue",
    "bd": "boulevard",
    "bld": "boulevard",
    "bvd": "boulevard",
    "boul": "boulevard",
    "r": "rue",
    "pl": "place",
    "fbg": "faubourg",
    "imp": "impasse",
    "rte": "route",
    "chem": "chemin",
    "sq": "square",
}

_MONTHS = {
    "janvier": 1,
    "janv": 1,
    "fevrier": 2,
    "fevr": 2,
    "fev": 2,
    "mars": 3,
    "avril": 4,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "juil": 7,
    "aout": 8,
    "septembre": 9,
    "sept": 9,
    "octobre": 10,
    "oct": 10,
    "novembre": 11,
    "nov": 11,
    "decembre": 12,
    "dec": 12,
}
_NUMERIC_DATE = re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$")
_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_LONG_DATE = re.compile(r"^(\d{1,2})(?:er)? ([a-z]+)\.? (\d{4})$")


def person_words(text: str) -> tuple[str, ...]:
    """Mots repliés d'un nom de personne, civilités de tête retirées.

    Paramètre : text, une mention de personne.
    Valeur retournée : les mots, sans accents ni majuscules ; une initiale devient une
    lettre seule.
    Exemple : person_words("M. Jean DUPONT") == ("jean", "dupont").
    """
    words = _WORD.findall(fold(text))
    while len(words) > 1 and words[0] in CIVILITIES:
        words = words[1:]
    return tuple(words)


def _organization_key(text: str) -> str:
    """Clé d'une société : sans forme juridique, sans "société", sans ponctuation."""
    # Les points sont supprimés (S.A.S. devient sas) ; les autres signes séparent les mots.
    cleaned = re.sub(r"[^\w ]", " ", fold(text).replace(".", ""))
    words = [w for w in cleaned.split() if w not in _LEGAL_FORMS_FOLDED | _ORGANIZATION_NOISE]
    while len(words) > 1 and words[0] in _ARTICLES:
        words = words[1:]
    return " ".join(words)


def _phone_key(text: str) -> str:
    """Clé d'un téléphone : chiffres seuls, indicatif +33 ou 0033 ramené à 0."""
    digits = re.sub(r"\D", "", text)
    if digits.startswith("0033"):
        digits = digits[4:]
    elif text.lstrip().startswith("+") and digits.startswith("33"):
        digits = digits[2:]
    else:
        return digits
    # "+33 (0)1 23 45 67 89" garde le zéro national entre parenthèses.
    return digits if digits.startswith("0") else "0" + digits


def _date_key(text: str) -> str:
    """Clé d'une date : forme ISO (AAAA-MM-JJ) si la date se lit, sinon le texte replié."""
    folded = fold(text)
    parts: tuple[int, int, int] | None = None
    if match := _NUMERIC_DATE.match(folded):
        parts = (int(match[3]), int(match[2]), int(match[1]))
    elif match := _ISO_DATE.match(folded):
        parts = (int(match[1]), int(match[2]), int(match[3]))
    elif (match := _LONG_DATE.match(folded)) and match[2] in _MONTHS:
        parts = (int(match[3]), _MONTHS[match[2]], int(match[1]))
    if parts is None:
        return folded
    try:
        return datetime.date(*parts).isoformat()
    except ValueError:
        return folded


def _address_key(text: str) -> str:
    """Clé d'une adresse : abréviations de voie développées, virgules et points retirés."""
    words = [w.strip(".") for w in fold(text).replace(",", " ").split()]
    return " ".join(_ADDRESS_ABBREVIATIONS.get(w, w) for w in words if w)


def _alphanumeric_key(text: str) -> str:
    """Clé d'un identifiant : lettres et chiffres seuls, en majuscules."""
    return re.sub(r"[^0-9A-Za-z]", "", text).upper()


_KEY_BUILDERS: dict[EntityType, Callable[[str], str]] = {
    EntityType.PERSON: lambda text: " ".join(person_words(text)),
    EntityType.ORGANIZATION: _organization_key,
    EntityType.EMAIL: lambda text: text.strip().lower(),
    EntityType.PHONE: _phone_key,
    EntityType.IBAN: _alphanumeric_key,
    EntityType.NIR: _alphanumeric_key,
    EntityType.SIREN: _alphanumeric_key,
    EntityType.SIRET: _alphanumeric_key,
    EntityType.CASE_NUMBER: _alphanumeric_key,
    EntityType.BIRTH_DATE: _date_key,
    EntityType.ADDRESS: _address_key,
}


def normalized_key(entity_type: EntityType, text: str) -> str:
    """Forme de comparaison d'une mention : deux mentions de même clé forment un groupe.

    Paramètres : entity_type, le type de la mention ; text, son texte exact.
    Valeur retournée : la clé ; le texte replié si la règle du type ne laisse rien.
    Exemple : normalized_key(EntityType.PHONE, "+33 1 23 45 67 89") == "0123456789".
    """
    key = _KEY_BUILDERS.get(entity_type, fold)(text)
    return key or fold(text)


@dataclass
class _Form:
    """Mentions d'un même type qui partagent la même clé."""

    entity_type: EntityType
    key: str
    mentions: list[Detection]

    @property
    def words(self) -> tuple[str, ...]:
        """Mots de la clé (utile pour les personnes)."""
        return tuple(self.key.split())


@dataclass
class _Bucket:
    """Groupe en construction : ses formes et les groupes avec lesquels il est ambigu."""

    forms: list[_Form]
    ambiguous_with: list["_Bucket"] = field(default_factory=list)

    @property
    def words(self) -> tuple[str, ...]:
        """Mots du nom complet qui a fondé le groupe."""
        return self.forms[0].words

    @property
    def first_start(self) -> int:
        """Position de la première mention du groupe dans le texte."""
        return min(form.mentions[0].start for form in self.forms)


def _is_initial(word: str) -> bool:
    """Une initiale est une lettre seule ("J." replié devient "j")."""
    return len(word) == 1


def _is_complete(form: _Form) -> bool:
    """Nom complet : au moins deux mots, aucun réduit à une initiale."""
    return len(form.words) >= 2 and not any(_is_initial(w) for w in form.words)


def _initials_match(words: tuple[str, ...], full: tuple[str, ...]) -> bool:
    """Dit si une forme à initiales ("j dupont") peut abréger un nom complet.

    Chaque mot entier doit figurer dans le nom complet ; chaque initiale doit être la
    première lettre d'un autre mot (ou d'une partie d'un prénom composé), sans réemploi.
    """
    names = [w for w in words if not _is_initial(w)]
    initials = [w for w in words if _is_initial(w)]
    if not names or not initials:
        return False
    remaining = list(full)
    for name in names:
        if name not in remaining:
            return False
        remaining.remove(name)
    parts = [part for word in remaining for part in word.split("-") if part]
    for initial in initials:
        found = next((part for part in parts if part[0] == initial), None)
        if found is None:
            return False
        parts.remove(found)
    return True


def may_abbreviate(words: tuple[str, ...], full: tuple[str, ...]) -> bool:
    """Dit si une forme partielle d'un nom (mot seul ou initiales) peut renvoyer à full.

    Paramètres : words et full, des mots repliés (voir person_words).
    Valeur retournée : vrai pour un mot seul présent dans full, ou pour une forme à
    initiales compatible. Exemple : may_abbreviate(("dupont",), ("jean", "dupont")) est vrai.
    """
    if len(words) == 1:
        return words[0] in full
    return _initials_match(words, full)


def _surname(bucket: _Bucket) -> str:
    """Nom de famille présumé : le mot écrit en capitales, sinon le dernier mot."""
    for form in bucket.forms:
        for mention in form.mentions:
            for word in mention.text.split():
                letters = [c for c in word if c.isalpha()]
                if len(letters) >= 2 and all(c.isupper() for c in letters):
                    return " ".join(person_words(word))
    return bucket.words[-1]


def _is_surname_elsewhere(word: str, bucket: _Bucket, forms: Sequence[_Form]) -> bool:
    """Dit si word sert de nom à une forme à initiales étrangère à bucket ("P. Martin")."""
    return any(
        word in form.words and not _initials_match(form.words, bucket.words)
        for form in forms
        if not _is_complete(form) and any(_is_initial(w) for w in form.words)
    )


def _candidates(form: _Form, full: Sequence[_Bucket]) -> list[_Bucket]:
    """Noms complets auxquels une forme partielle (initiale ou mot seul) peut renvoyer."""
    if len(form.words) == 1:
        return [bucket for bucket in full if form.words[0] in bucket.words]
    if any(_is_initial(w) for w in form.words):
        return [bucket for bucket in full if _initials_match(form.words, bucket.words)]
    return []


def _group_persons(forms: Sequence[_Form]) -> list[_Bucket]:
    """Applique aux personnes les règles de rattachement, dans l'ordre du prompt S21.

    Mêmes mots dans un autre ordre : même groupe. Initiale et nom, nom seul ou prénom
    seul : rattachés à l'unique nom complet compatible ; sinon groupe distinct, avec
    ambiguous_with renseigné s'il y avait plusieurs candidats.
    """
    by_word_set: dict[tuple[str, ...], _Bucket] = {}
    for form in forms:
        if _is_complete(form):
            by_word_set.setdefault(tuple(sorted(form.words)), _Bucket([])).forms.append(form)
    full = list(by_word_set.values())
    buckets = list(full)
    for form in forms:
        if _is_complete(form):
            continue
        candidates = _candidates(form, full)
        if len(candidates) == 1 and _may_attach(form, candidates[0], forms):
            candidates[0].forms.append(form)
            continue
        # Plusieurs candidats, ou un prénom qui est aussi le nom d'un autre : doute.
        buckets.append(_Bucket([form], ambiguous_with=list(candidates)))
    return buckets


def _may_attach(form: _Form, bucket: _Bucket, forms: Sequence[_Form]) -> bool:
    """Un prénom seul n'est rattaché que s'il n'est le nom de personne d'autre."""
    if len(form.words) != 1:
        return True
    word = form.words[0]
    return word == _surname(bucket) or not _is_surname_elsewhere(word, bucket, forms)


def _word_weight(entity_type: EntityType, text: str) -> int:
    """Nombre de mots significatifs d'une variante, pour choisir la forme canonique."""
    if entity_type is EntityType.PERSON:
        return len(person_words(text))
    words = text.split()
    if entity_type is EntityType.ORGANIZATION:
        noise = _ORGANIZATION_NOISE | _ARTICLES
        words = [w for w in words if fold(w).strip(".,") not in noise]
    return len(words)


def _to_group(bucket: _Bucket, group_ids: dict[int, int]) -> EntityGroup:
    """Construit l'EntityGroup final d'un groupe en construction."""
    mentions = sorted((m for f in bucket.forms for m in f.mentions), key=lambda m: m.start)
    entity_type = bucket.forms[0].entity_type
    # max garde le premier maximum : à égalité, la variante apparue la première l'emporte.
    canonical = max(mentions, key=lambda m: _word_weight(entity_type, m.text)).text
    return EntityGroup(
        group_id=group_ids[id(bucket)],
        entity_type=entity_type,
        canonical=canonical,
        variants=tuple(sorted({m.text for m in mentions})),
        token="",
        mention_spans=tuple((m.start, m.end) for m in mentions),
        ambiguous_with=tuple(sorted(group_ids[id(other)] for other in bucket.ambiguous_with)),
    )


def _forms_by_type(detections: Sequence[Detection]) -> dict[EntityType, list[_Form]]:
    """Réunit les mentions de même type et de même clé, dans l'ordre d'apparition."""
    forms: dict[tuple[EntityType, str], _Form] = {}
    for detection in sorted(detections, key=lambda d: d.start):
        key = normalized_key(detection.entity_type, detection.text)
        form = forms.setdefault((detection.entity_type, key), _Form(detection.entity_type, key, []))
        form.mentions.append(detection)
    by_type: dict[EntityType, list[_Form]] = {}
    for form in forms.values():
        by_type.setdefault(form.entity_type, []).append(form)
    return by_type


def group_mentions(text: str, detections: Sequence[Detection]) -> list[EntityGroup]:
    """Regroupe les détections qui désignent la même entité.

    Paramètres : text, le texte d'origine ; detections, les détections validées.
    Valeur retournée : les groupes, numérotés (group_id à partir de 1) et triés par
    première apparition ; le jeton reste vide, pseudonymize.tokens le fixe.
    Exemple : "Jean DUPONT" et "M. Dupont" forment un seul groupe de canonical
    "Jean DUPONT".
    """
    for detection in detections:
        if text[detection.start : detection.end] != detection.text:
            raise ValueError(f"détection incohérente avec le texte : {detection!r}")
    buckets: list[_Bucket] = []
    for entity_type, forms in _forms_by_type(detections).items():
        if entity_type is EntityType.PERSON:
            buckets.extend(_group_persons(forms))
        else:
            buckets.extend(_Bucket([form]) for form in forms)
    buckets.sort(key=lambda b: b.first_start)
    group_ids = {id(bucket): index for index, bucket in enumerate(buckets, start=1)}
    return [_to_group(bucket, group_ids) for bucket in buckets]
