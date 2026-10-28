"""Bornes des sociétés : complète un nom de société coupé et répare les noms scindés.

Entrées : le texte, les détections fusionnées par detection.merge, la configuration et les
passages exclus. Sortie : une liste de Detection triée et sans chevauchement.
Place dans le pipeline : après detection.merge, avant detection.propagation. Les règles
sont décrites dans docs/DECISIONS.md (D-S35-2).
"""

import re
from collections.abc import Sequence
from dataclasses import replace

from huisclos.config import DetectionConfig
from huisclos.detection.analysis_view import AnalysisView, build_view
from huisclos.detection.exclusions import is_legal_reference
from huisclos.detection.person_heuristics import build_person_recognizers
from huisclos.models import Detection, EntityType, Source
from huisclos.text_utils import (
    CIVILITIES,
    LEGAL_FORMS,
    fold,
    fold_same_length,
    is_capitalized_form,
)

# Mots de liaison admis à l'intérieur d'un nom de société ("Maison des Fils", "A & B").
LIAISONS = frozenset({"de", "des", "du", "d'", "la", "le", "les", "et", "&"})
# Libellés qui annoncent une société sans en faire partie (D-09).
LABEL_WORDS = frozenset({"societe", "employeur", "expediteur", "destinataire"})
# Mots grammaticaux qui portent une majuscule en début de phrase sans appartenir au nom.
GRAMMAR_WORDS = frozenset(
    "a au aux avec ce ces cet cette chez contre dans elle en entre il je leur leurs ma mes "
    "mon nos notre on par pour sa sans selon ses son sous sur vers vos votre vous".split()
)
# Documents anglais : liaisons ("Bank of", "Smith and Sons"), libellés de rôle et mots
# grammaticaux qui ne prolongent jamais un nom de société ("For", "The").
ENGLISH_LIAISONS = frozenset({"of", "and"})
ENGLISH_LABEL_WORDS = frozenset(
    {"company", "employer", "claimant", "defendant", "respondent", "client", "supplier"}
)
ENGLISH_GRAMMAR_WORDS = frozenset(
    "the a an for with by from to at in on as between against versus v vs per via under over "
    "into upon about after before during dear re or but our your their his her its my we they "
    "he she it this that these those which who whom whose when where while if all any each "
    "every such no not only also both either neither nor".split()
)
# Mots de liaison, libellés et mots grammaticaux par langue du document.
WORDS = {
    "fr": (LIAISONS, LABEL_WORDS, GRAMMAR_WORDS),
    "en": (
        LIAISONS | ENGLISH_LIAISONS,
        LABEL_WORDS | ENGLISH_LABEL_WORDS,
        GRAMMAR_WORDS | ENGLISH_GRAMMAR_WORDS,
    ),
}
MAX_EXTENSION_WORDS = 6
# Une forme juridique précédée de mots à majuscule désigne une société (D-S35-2).
LEGAL_FORM_SCORE = 0.70
# Civilité suivie d'un nom (D-07).
CIVILITY_NAME_SCORE = 0.80

_LEGAL_ALTERNATION = "|".join(sorted(LEGAL_FORMS, key=len, reverse=True))
# Casse exacte : "SA" est une forme juridique, "sa" un possessif.
_LEGAL_FORM = re.compile(rf"(?<!\w)(?:{_LEGAL_ALTERNATION})(?!\w)")
_LEGAL_AFTER = re.compile(rf"[^\S\n]+(?:{_LEGAL_ALTERNATION})(?!\w)")
# Un signe de ponctuation forme un mot à lui seul : "Durand," donne "Durand" puis ",".
_TOKEN = re.compile(r"[^\s.,;:()\[\]{}\"\u00ab\u00bb!?]+|\S")
_LIAISON_GAP = re.compile(r"[^\S\n]+(?:de|des|du|la|le|les|et|&)[^\S\n]+|[^\S\n]+d'")
_STOP_CHARACTERS = frozenset('.,;:()[]{}"\u00ab\u00bb!?')
_NAME_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION})


def _span(text: str, detection: Detection, start: int, end: int, **changes: object) -> Detection:
    """Copie la détection sur [start, end) avec le texte exact correspondant."""
    return replace(detection, start=start, end=end, text=text[start:end], **changes)


def _line_tokens(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Positions des mots de text[start:end], sans franchir de saut de ligne."""
    return [m.span() for m in _TOKEN.finditer(text, start, end)]


def _token_kind(token: str, language: str = "fr") -> str:
    """Classe un mot voisin d'une société : "liaison", "name" ou "stop".

    Exemple : _token_kind("des") == "liaison", _token_kind("Atelier") == "name",
    _token_kind("chez") == "stop", _token_kind("SAS") == "stop".
    """
    liaisons, labels, grammar = WORDS[language]
    if any(char in _STOP_CHARACTERS for char in token) or any(c.isdigit() for c in token):
        return "stop"
    folded = fold(token)
    if folded in liaisons:
        return "liaison"
    if folded in CIVILITIES or token in LEGAL_FORMS:
        return "stop"
    if folded in labels or folded in grammar or not is_capitalized_form(token):
        return "stop"
    return "name"


def _in_legal_reference(text: str, start: int, end: int, spans: Sequence[tuple[int, int]]) -> bool:
    """Dit si le mot [start, end) appartient à une juridiction ou un texte exclu."""
    return any(s < end and start < e and is_legal_reference(text[s:e]) for s, e in spans)


def _extend(
    text: str,
    tokens: list[tuple[int, int]],
    exclusion_spans: Sequence[tuple[int, int]],
    language: str = "fr",
) -> int | None:
    """Compte les mots de tokens (les plus proches de la société d'abord) qui la prolongent.

    Valeur retournée : l'indice, dans tokens, du dernier mot de nom retenu, ou None.
    Les liaisons ne sont retenues qu'entre deux mots de nom : aucune n'ouvre le span.
    """
    last_name: int | None = None
    for index, (start, end) in enumerate(tokens[:MAX_EXTENSION_WORDS]):
        kind = _token_kind(text[start:end], language)
        if kind == "stop" or _in_legal_reference(text, start, end, exclusion_spans):
            break
        if kind == "name":
            last_name = index
    return last_name


def _line_start(text: str, position: int) -> int:
    """Début de la ligne qui contient position."""
    return text.rfind("\n", 0, position) + 1


def _line_end(text: str, position: int) -> int:
    """Fin de la ligne qui contient position."""
    newline = text.find("\n", position)
    return len(text) if newline < 0 else newline


def extended_bounds(
    text: str,
    start: int,
    end: int,
    exclusion_spans: Sequence[tuple[int, int]] = (),
    language: str = "fr",
) -> tuple[int, int]:
    """Bornes d'une société étendues aux mots de son nom restés hors du span.

    Une société qui finit par une forme juridique s'étend vers la gauche ; une société qui
    commence par une forme juridique s'étend vers la droite. Arrêt sur ponctuation, saut de
    ligne, mot en minuscule hors liaison, civilité, libellé, autre forme juridique,
    juridiction ou texte exclu, ou au bout de MAX_EXTENSION_WORDS mots.
    Exemple : dans "chez Comptoir des Lilas SAS", (18, 27) devient (5, 27).
    """
    words = text[start:end].split()
    if words and words[-1] in LEGAL_FORMS:
        before = list(reversed(_line_tokens(text, _line_start(text, start), start)))
        last = _extend(text, before, exclusion_spans, language)
        if last is not None:
            return before[last][0], end
    if words and words[0] in LEGAL_FORMS:
        after = _line_tokens(text, end, _line_end(text, end))
        last = _extend(text, after, exclusion_spans, language)
        if last is not None:
            return start, after[last][1]
    return start, end


def _overlapping(detections: Sequence[Detection], start: int, end: int) -> list[Detection]:
    """Détections qui chevauchent [start, end)."""
    return [d for d in detections if d.start < end and start < d.end]


def _absorb(
    text: str, detections: list[Detection], target: Detection, start: int, end: int
) -> list[Detection] | None:
    """Étend target à [start, end) en absorbant les noms contenus ; None en cas de conflit.

    Un identifiant, une adresse ou un nom qui déborde de [start, end) n'est jamais absorbé.
    """
    others = [d for d in _overlapping(detections, start, end) if d is not target]
    for other in others:
        if other.source == Source.MANUAL or other.entity_type not in _NAME_TYPES:
            return None
        if other.start < start or end < other.end:
            return None
    best = max([target, *others], key=lambda d: d.score)
    widened = _span(text, target, start, end, score=best.score)
    return [d for d in detections if d is not target and d not in others] + [widened]


def merge_civility_names(
    text: str,
    detections: list[Detection],
    language: str = "fr",
    view: AnalysisView | None = None,
) -> list[Detection]:
    """Répare les fragments de noms reconnus par une civilité ou leur casse.

    Les mêmes heuristiques, celles de la langue du document, bornent la détection et la
    réparation, particules et initiales comprises ; elles lisent la vue d'analyse, dont
    les spans sont reprojetés. Les identifiants, adresses, ajouts manuels et sociétés
    portant une forme juridique empêchent toute absorption.
    """
    view = view if view is not None and view.canonical == text else build_view(text)
    candidates = [
        (*view.project(start, end), recognizer.score)
        for recognizer in build_person_recognizers(language=language)
        for start, end in recognizer._spans(view.text)
    ]
    for start, end, score in sorted(set(candidates), key=lambda item: (item[0], -item[1])):
        if _LEGAL_AFTER.match(text, end) or any(w in LEGAL_FORMS for w in text[start:end].split()):
            continue
        prefix_start = max(0, start - 20)
        prefix = text[prefix_start:start]
        civility = re.search(r"(?<!\w)([^\W\d_]+)\.?[^\S\n]+$", prefix)
        label_start = start
        if civility and fold(civility[1]) in CIVILITIES:
            label_start = prefix_start + civility.start()
        parts = _overlapping(detections, label_start, end)
        if not parts or any(
            p.source == Source.MANUAL
            or p.entity_type not in {EntityType.PERSON, EntityType.ORGANIZATION}
            or p.start < label_start
            or end < p.end
            for p in parts
        ):
            continue
        best = max(parts, key=lambda d: d.score)
        person = _span(
            text,
            best,
            start,
            end,
            entity_type=EntityType.PERSON,
            score=max(best.score, score),
        )
        detections = [d for d in detections if d not in parts] + [person]
    return detections


def _widen_organizations(
    text: str,
    detections: list[Detection],
    exclusion_spans: Sequence[tuple[int, int]],
    language: str = "fr",
) -> list[Detection]:
    """Étend chaque société à son nom complet (extended_bounds), si rien ne s'y oppose."""
    for target in sorted(detections, key=lambda d: d.start):
        if target.entity_type != EntityType.ORGANIZATION or target not in detections:
            continue
        start, end = extended_bounds(text, target.start, target.end, exclusion_spans, language)
        if (start, end) != (target.start, target.end):
            detections = _absorb(text, detections, target, start, end) or detections
    return detections


def _anchor_legal_forms(
    text: str,
    detections: list[Detection],
    exclusion_spans: Sequence[tuple[int, int]],
    language: str = "fr",
) -> list[Detection]:
    """Crée une société pour chaque forme juridique libre accolée à des mots à majuscule.

    "Foncière Durandel SAS" est une société même si aucun reconnaisseur ne l'a vue ; la
    forme juridique seule ("SARL") ne suffit pas.
    """
    for match in _LEGAL_FORM.finditer(text):
        if _overlapping(detections, *match.span()):
            continue
        seed = Detection(
            match.start(),
            match.end(),
            EntityType.ORGANIZATION,
            LEGAL_FORM_SCORE,
            Source.HEURISTIC,
            match.group(),
        )
        start, end = extended_bounds(text, seed.start, seed.end, exclusion_spans, language)
        if (start, end) != match.span():
            detections = _absorb(text, [*detections, seed], seed, start, end) or detections
    return detections


def _fusable(text: str, left: Detection, right: Detection) -> bool:
    """Deux sociétés séparées par une seule liaison forment-elles un seul nom ?

    Non si la gauche finit ou la droite commence par une forme juridique : "Alpha SARL et
    Beta SAS" désigne deux sociétés complètes.
    """
    if EntityType.ORGANIZATION != left.entity_type or left.entity_type != right.entity_type:
        return False
    if Source.MANUAL in (left.source, right.source):
        return False
    if left.text.split()[-1] in LEGAL_FORMS or right.text.split()[0] in LEGAL_FORMS:
        return False
    gap = fold_same_length(text[left.end : right.start])
    return _LIAISON_GAP.fullmatch(gap) is not None


def fuse_organizations(text: str, detections: list[Detection]) -> list[Detection]:
    """Réunit "Comptoir" et "Lilas" séparés par "des" en un seul span de société.

    La détection réunie couvre l'union et garde la source et le score de la plus forte.
    """
    fused: list[Detection] = []
    for detection in sorted(detections, key=lambda d: (d.start, d.end)):
        if fused and _fusable(text, fused[-1], detection):
            left = fused[-1]
            best = left if left.score >= detection.score else detection
            fused[-1] = _span(text, best, left.start, detection.end)
        else:
            fused.append(detection)
    return fused


def adjust_organizations(
    text: str,
    detections: Sequence[Detection],
    config: DetectionConfig,
    exclusion_spans: Sequence[tuple[int, int]] = (),
    view: AnalysisView | None = None,
) -> list[Detection]:
    """Corrige les bornes des sociétés et des personnes précédées d'une civilité.

    Paramètres : text, le texte analysé ; detections, la sortie de merge ; config, pour les
    types activés, le seuil, les sources et la langue ; exclusion_spans, les passages
    exclus ; view, la vue d'analyse de text (construite si elle manque).
    Valeur retournée : les détections triées, sans chevauchement, dont text vaut
    texte[start:end]. Les sociétés créées à partir d'une forme juridique relèvent des
    heuristiques et n'apparaissent que si celles-ci sont activées.
    """
    spans = exclusion_spans if config.use_exclusions else ()
    language = config.document_language
    result = list(detections)
    if EntityType.PERSON in config.enabled_types:
        result = merge_civility_names(text, result, language, view)
    if EntityType.ORGANIZATION in config.enabled_types:
        result = _widen_organizations(text, result, spans, language)
        if config.use_heuristics and LEGAL_FORM_SCORE >= config.threshold:
            result = _anchor_legal_forms(text, result, spans, language)
        result = fuse_organizations(text, result)
    return sorted(result, key=lambda d: (d.start, d.end))
