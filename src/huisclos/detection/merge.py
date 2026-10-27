"""Fusion des détections brutes en une liste propre, triée et sans chevauchement.

Entrées : le texte, les détections de toutes les sources, la configuration et les passages
exclus (detection.exclusions). Sortie : une liste de Detection prête pour la propagation.
Place dans le pipeline : après les reconnaisseurs, avant la propagation et la revue humaine.
Les huit règles sont appliquées dans l'ordre de la fonction merge ; chacune est testée seule.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import replace

from huisclos.config import DetectionConfig
from huisclos.detection.exclusions import EXCLUDABLE_TYPES, is_excluded, is_legal_reference
from huisclos.models import Detection, EntityType, Source
from huisclos.text_utils import CIVILITIES, LEGAL_FORMS, fold, fold_same_length

# Du plus prioritaire au moins prioritaire. Les identifiants à clé de contrôle passent avant
# les noms : un e-mail repéré dans un span NER reste un e-mail. Un ajout manuel passe avant
# tout, quel que soit son type.
TYPE_PRIORITY: tuple[EntityType, ...] = tuple(
    EntityType[name]
    for name in (
        "IBAN NIR SIRET SIREN EMAIL PHONE CASE_NUMBER BIRTH_DATE "
        "ADDRESS ORGANIZATION PERSON LOCATION CUSTOM"
    ).split()
)

# Ponctuation retirée en bordure d'un span (guillemets, parenthèses, tirets, points).
BORDER_PUNCTUATION = frozenset(
    ".,;:!?()[]{}<>\"'/\\-*_|\u00ab\u00bb\u2018\u2019\u201c\u201d\u2013\u2014"
)

_NAME_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION})
_LINE_BOUND_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION})
_LEGAL_ALTERNATION = "|".join(sorted(LEGAL_FORMS, key=len, reverse=True))
# Forme juridique sur la même ligne, juste après ou juste avant le nom ; casse exacte, pour
# ne pas confondre "SA" avec le possessif "sa".
_LEGAL_AFTER = re.compile(rf"[^\S\n]+(?:{_LEGAL_ALTERNATION})\b")
_LEGAL_BEFORE = re.compile(rf"\b(?:{_LEGAL_ALTERNATION})[^\S\n]+$")
_COMPANY_WORD_BEFORE = re.compile(r"(?<!\w)(?:societe|cabinet|groupe)[^\S\n]+$")
_LEADING_WORD = re.compile(r"([^\W\d_]+)(?:\.\s*|\s+)")
_ADDRESS_GAP = re.compile(r"[^\S\n]*,?[^\S\n]*(?:\r?\n[^\S\n]*)?")
_PERSON_GAPS = frozenset({"", " ", "-", "\u00a0"})
_POSTAL_CODE = re.compile(r"[0-9]{5}(?!\w)")
# Score d'une adresse compl\u00e8te, de la voie \u00e0 la ville (D-07).
FULL_ADDRESS_SCORE = 0.70


def priority(detection: Detection) -> tuple[int, int]:
    """Rang de priorité d'une détection : plus il est petit, plus elle l'emporte.

    Exemple : un ajout manuel vaut (0, rang du type), une détection automatique (1, rang).
    """
    manual = 0 if detection.source == Source.MANUAL else 1
    return manual, TYPE_PRIORITY.index(detection.entity_type)


def _with_span(
    text: str, detection: Detection, start: int, end: int, **changes: object
) -> Detection:
    """Copie la détection sur [start, end) avec le texte exact correspondant."""
    return replace(detection, start=start, end=end, text=text[start:end], **changes)


def _strip_borders(text: str, start: int, end: int) -> tuple[int, int]:
    """Retire espaces et ponctuation aux deux bords de [start, end)."""
    while start < end and (text[start].isspace() or text[start] in BORDER_PUNCTUATION):
        start += 1
    while end > start and (text[end - 1].isspace() or text[end - 1] in BORDER_PUNCTUATION):
        end -= 1
    return start, end


def _skip_civilities(text: str, start: int, end: int) -> int:
    """Avance start après les civilités placées en tête ("M.", "Madame", "Maître")."""
    while True:
        match = _LEADING_WORD.match(text, start, end)
        if match is None or fold(match.group(1)) not in CIVILITIES or match.end() >= end:
            return start
        start = match.end()


def _longest_line(text: str, start: int, end: int) -> tuple[int, int]:
    """Garde la plus longue ligne de [start, end) : un nom ne passe pas à la ligne.

    Le NER spaCy prolonge parfois un nom sur la ligne suivante ("Claire Fontaine\\nAvocate").
    """
    lines: list[tuple[int, int]] = []
    cursor = start
    for index in range(start, end):
        if text[index] == "\n":
            lines.append((cursor, index))
            cursor = index + 1
    lines.append((cursor, end))
    return max(lines, key=lambda line: (line[1] - line[0], -line[0]))


def trim(text: str, detection: Detection) -> Detection | None:
    """Règle 1 : rogne espaces et ponctuation en bordure, et la civilité d'une personne.

    Un nom de personne, de société ou de lieu est en outre limité à sa plus longue ligne,
    et une personne réduite à une civilité ("Madame") est supprimée.
    Valeur retournée : la détection rognée, ou None s'il ne reste rien.
    Exemple : "M. Dupont," devient "Dupont" (D-09, la civilité reste visible).
    """
    start, end = _strip_borders(text, detection.start, detection.end)
    if detection.entity_type in _LINE_BOUND_TYPES and "\n" in text[start:end]:
        start, end = _strip_borders(text, *_longest_line(text, start, end))
    if detection.entity_type == EntityType.PERSON and start < end:
        if fold(text[start:end]).rstrip(".") in CIVILITIES:
            return None
        start, end = _strip_borders(text, _skip_civilities(text, start, end), end)
    if start >= end:
        return None
    return _with_span(text, detection, start, end)


def requalify(text: str, detection: Detection) -> Detection:
    """Règle 4 : une personne liée à une forme juridique devient une société.

    "Garnier SARL", "SARL Garnier" ou "société Garnier" désignent une société ; le span
    s'étend à la forme juridique accolée (D-09), mais pas au mot "société".
    """
    if detection.entity_type not in _NAME_TYPES:
        return detection
    start, end = detection.start, detection.end
    company = detection.text.split()[-1] in LEGAL_FORMS or detection.text.split()[0] in LEGAL_FORMS
    after = _LEGAL_AFTER.match(text, end)
    if after:
        end, company = after.end(), True
    window_start = max(0, start - 20)
    before = _LEGAL_BEFORE.search(text, window_start, start)
    if before:
        start, company = before.start(), True
    elif _COMPANY_WORD_BEFORE.search(fold_same_length(text[window_start:start])):
        company = True
    if not company:
        return detection
    return _with_span(text, detection, start, end, entity_type=EntityType.ORGANIZATION)


def _clusters(detections: list[Detection]) -> list[list[Detection]]:
    """Regroupe les détections reliées par une chaîne de chevauchements."""
    clusters: list[list[Detection]] = []
    cluster_end = -1
    for detection in sorted(detections, key=_sort_key):
        if clusters and detection.start < cluster_end:
            clusters[-1].append(detection)
            cluster_end = max(cluster_end, detection.end)
        else:
            clusters.append([detection])
            cluster_end = detection.end
    return clusters


def _union_same_type(text: str, cluster: list[Detection]) -> list[Detection]:
    """Règle 5a : unit les spans chevauchants de même type ; garde le score maximal.

    Un ajout manuel n'est jamais uni à une détection automatique : ses bornes, choisies par
    l'utilisateur, priment.
    """
    united: list[Detection] = []
    for detection in sorted(cluster, key=_sort_key):
        # Le tri par début garantit qu'au plus un span déjà uni chevauche le suivant.
        same = [
            i
            for i, o in enumerate(united)
            if priority(o) == priority(detection) and detection.start < o.end
        ]
        if not same:
            united.append(detection)
            continue
        current = united[same[0]]
        best = current if current.score >= detection.score else detection
        end = max(current.end, detection.end)
        united[same[0]] = _with_span(text, best, current.start, end)
    return united


def _free_parts(
    text: str, detection: Detection, blockers: Iterable[tuple[int, int]]
) -> list[Detection]:
    """Parties de la détection non couvertes par les passages blockers, dans l'ordre.

    Chaque partie doit compter au moins 2 lettres ou chiffres : le reste d'un IBAN rogné par
    un ajout manuel est encore sensible, alors qu'une initiale isolée ne l'est plus. Toutes
    les parties sont gardées : "Paul Martin" et "Marie Durand" autour d'un e-mail sont deux
    noms distincts, et en perdre un laisserait une personne en clair (priorité au rappel).
    """
    parts: list[tuple[int, int]] = []
    cursor = detection.start
    for blocker_start, blocker_end in sorted(blockers):
        if blocker_start > cursor:
            parts.append((cursor, min(blocker_start, detection.end)))
        cursor = max(cursor, blocker_end)
    if cursor < detection.end:
        parts.append((cursor, min(detection.end, len(text))))
    trimmed = [_strip_borders(text, start, end) for start, end in parts]
    return [
        _with_span(text, detection, start, end)
        for start, end in trimmed
        if sum(c.isalnum() for c in text[start:end]) >= 2
    ]


def _resolve_conflicts(text: str, cluster: list[Detection]) -> list[Detection]:
    """Règle 5b : arbitre les chevauchements entre types différents.

    Les détections sont examinées de la plus forte à la plus faible (priorité, puis score,
    puis longueur). Une détection contenue dans une plus forte disparaît ; une détection
    qui en contient une plus forte, ou la chevauche en partie, est réduite à ses parties
    libres, pour ne pas laisser un morceau de nom en clair (priorité au rappel).
    """
    ordered = sorted(cluster, key=lambda d: (priority(d), -d.score, -d.length, _sort_key(d)))
    accepted: list[Detection] = []
    for detection in ordered:
        blockers = [a for a in accepted if a.start < detection.end and detection.start < a.end]
        if not blockers:
            accepted.append(detection)
        elif not any(a.start <= detection.start and detection.end <= a.end for a in blockers):
            accepted.extend(_free_parts(text, detection, [(a.start, a.end) for a in blockers]))
    return accepted


def _joinable(text: str, left: Detection, right: Detection) -> bool:
    """Règle 6 : deux détections voisines forment-elles une seule entité ?"""
    if left.entity_type != right.entity_type or priority(left) != priority(right):
        return False
    gap = text[left.end : right.start]
    if left.entity_type == EntityType.PERSON:
        return gap in _PERSON_GAPS
    if left.entity_type == EntityType.ADDRESS:
        return _ADDRESS_GAP.fullmatch(gap) is not None
    return False


def _joined_score(left: Detection, right: Detection) -> float:
    """Score d'une détection réunie : le plus haut des deux, ou celui d'une adresse complète.

    Une voie (0,55) suivie de son code postal et de sa ville (0,45) forme une adresse
    complète, qui vaut 0,70 selon D-07.
    """
    score = max(left.score, right.score)
    street_then_postal_code = (
        left.entity_type == EntityType.ADDRESS
        and _POSTAL_CODE.match(left.text) is None
        and _POSTAL_CODE.match(right.text) is not None
    )
    return max(score, FULL_ADDRESS_SCORE) if street_then_postal_code else score


def join_adjacent(text: str, detections: list[Detection]) -> list[Detection]:
    """Règle 6 : fusionne "Jean" et "DUPONT", ou une voie et la ligne "92000 Nanterre"."""
    joined: list[Detection] = []
    for detection in sorted(detections, key=_sort_key):
        if joined and _joinable(text, joined[-1], detection):
            left = joined[-1]
            best = left if left.score >= detection.score else detection
            score = _joined_score(left, detection)
            joined[-1] = _with_span(text, best, left.start, detection.end, score=score)
        else:
            joined.append(detection)
    return joined


def _sort_key(detection: Detection) -> tuple[int, int, str, str, float]:
    """Clé de tri totale, qui rend le résultat indépendant de l'ordre d'arrivée."""
    return (
        detection.start,
        detection.end,
        detection.entity_type.value,
        detection.source.value,
        -detection.score,
    )


def crossing_spans(start: int, end: int, spans: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    """Passages qui chevauchent [start, end) en franchissant l'une de ses bornes.

    Un passage entièrement contenu dans [start, end) n'est pas retenu : la forme juridique
    "SARL", exclue seule, fait partie du nom "Garnier Logistique SARL" (D-09).
    Exemple : crossing_spans(5, 10, [(0, 7), (6, 8)]) == [(0, 7)].
    """
    return [(s, e) for s, e in spans if s < end and start < e and not (start <= s and e <= end)]


def cutting_spans(
    text: str, start: int, end: int, spans: Sequence[tuple[int, int]]
) -> list[tuple[int, int]]:
    """Passages exclus à retirer de [start, end) : ceux qui franchissent une borne, et les
    références juridiques entièrement contenues.

    Une juridiction ou un article ne doit jamais être masqué, même quand le NER l'englobe
    dans un nom ("La société Tribunal judiciaire de Nanterre SARL") ; une forme juridique
    contenue ("SARL") reste au contraire dans le span de sa société (D-09).
    """
    inside = [(s, e) for s, e in spans if start <= s and e <= end and is_legal_reference(text[s:e])]
    return sorted([*crossing_spans(start, end, spans), *inside])


def _subtract_exclusions(
    text: str, detection: Detection, exclusion_spans: Sequence[tuple[int, int]]
) -> list[Detection]:
    """Retire d'un nom les passages exclus qui le coupent (cutting_spans) ; garde le reste.

    Un nom entièrement exclu disparaît. Un span NER qui déborde dans une juridiction
    ("Paul Martin" dans "Tribunal judiciaire de Paul Martin") ou qui en contient une ne doit
    pas la masquer, mais les parties hors du passage exclu restent signalées (priorité au
    rappel), sauf celles qui sont elles-mêmes exclues. Un ajout manuel et les types qu'une
    exclusion ne vise pas (e-mail, IBAN, adresse) sont gardés tels quels.
    """
    if detection.source == Source.MANUAL or detection.entity_type not in EXCLUDABLE_TYPES:
        return [detection]
    if is_excluded(detection, exclusion_spans):
        return []
    cutting = cutting_spans(text, detection.start, detection.end, exclusion_spans)
    if not cutting:
        return [detection]
    parts = _free_parts(text, detection, cutting)
    return [part for part in parts if not is_excluded(part, exclusion_spans)]


def check_output(text: str, detections: Sequence[Detection]) -> None:
    """Règle 8 : vérifie l'absence de chevauchement et l'exactitude de chaque texte."""
    for left, right in zip(detections, detections[1:], strict=False):
        assert left.end <= right.start, f"chevauchement : {left} et {right}"
    for detection in detections:
        assert detection.text == text[detection.start : detection.end], detection


def merge(
    text: str,
    raw: Iterable[Detection],
    config: DetectionConfig,
    exclusion_spans: Sequence[tuple[int, int]] = (),
) -> list[Detection]:
    """Applique les règles 1 à 8 et renvoie les détections retenues, triées.

    Paramètres : text, le texte analysé ; raw, les détections de toutes les sources ;
    config, la configuration (types activés, exclusions, seuil) ; exclusion_spans, les
    passages exclus calculés par ExclusionList.spans.
    Valeur retournée : des Detection sans chevauchement, dont text vaut texte[start:end].
    Un ajout manuel n'est jamais supprimé par la liste d'exclusions.
    """
    trimmed = (trim(text, d) for d in sorted(set(raw), key=_sort_key))
    detections = [d for d in trimmed if d is not None]
    if config.use_exclusions:
        detections = [
            part for d in detections for part in _subtract_exclusions(text, d, exclusion_spans)
        ]
    # Le filtre suit la requalification : une personne devenue société relève du type société.
    detections = [requalify(text, d) for d in detections]
    detections = [d for d in detections if d.entity_type in config.enabled_types]
    resolved: list[Detection] = []
    for cluster in _clusters(detections):
        resolved.extend(_resolve_conflicts(text, _union_same_type(text, cluster)))
    detections = join_adjacent(text, resolved)
    detections = sorted((d for d in detections if d.score >= config.threshold), key=_sort_key)
    check_output(text, detections)
    return detections
