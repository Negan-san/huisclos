"""Moteur de détection : assemble les reconnaisseurs, la fusion, les bornes et la propagation.

Entrées : un texte français ou anglais, une DetectionConfig (config.PRESETS["hybrid"] par
défaut, langue du document comprise) et, pour un dossier, les valeurs connues d'une table
précédente.
Sorties : la liste triée des Detection retenues, sans chevauchement, aux positions du texte.
Place dans le pipeline : point d'entrée unique de la détection pour l'interface, les
scripts et l'évaluation ; la revue humaine part de son résultat.
"""

import importlib
from collections.abc import Sequence
from dataclasses import replace
from functools import lru_cache

from presidio_analyzer import AnalyzerEngine, EntityRecognizer, RecognizerRegistry, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngine

from huisclos.config import PRESETS, DetectionConfig
from huisclos.detection.analysis_view import LEGACY, AnalysisView, build_view
from huisclos.detection.exclusions import load_exclusions_for
from huisclos.detection.merge import merge, trim
from huisclos.detection.ner import LANGUAGE, build_ner_recognizers, build_nlp_engine
from huisclos.detection.organization_bounds import adjust_organizations
from huisclos.detection.patterns import build_pattern_recognizers
from huisclos.detection.person_heuristics import build_person_recognizers
from huisclos.detection.propagation import propagate
from huisclos.models import Detection, EntityType, Source

# Module attendu de l'option CamemBERT (D-06) ; il expose build_camembert_recognizers().
CAMEMBERT_MODULE = "huisclos.detection.camembert"


@lru_cache(maxsize=4)
def get_nlp_engine(model_name: str, language: str = LANGUAGE) -> NlpEngine:
    """Charge une seule fois le moteur spaCy de Presidio pour un modèle et une langue.

    Presidio exige un moteur NLP même sans reconnaisseur NER ; le même moteur sert donc à
    toutes les configurations d'une langue, ce qui évite de recharger le modèle.
    """
    return build_nlp_engine(model_name, language)


def _camembert_recognizers(language: str) -> list[EntityRecognizer]:
    """Charge les reconnaisseurs CamemBERT, ou explique pourquoi c'est impossible.

    CamemBERT est un modèle français : il n'est pas proposé pour un document anglais, dont
    la couverture ne peut pas reposer sur lui (D-AF-A2-1).
    """
    if language != "fr":
        raise ValueError("CamemBERT est un modèle français : il ne s'applique pas à ce document.")
    try:
        module = importlib.import_module(CAMEMBERT_MODULE)
    except ImportError as error:
        raise RuntimeError(
            "L'option CamemBERT n'est pas installée (requirements-transformers.txt, D-06)."
        ) from error
    return list(module.build_camembert_recognizers())


@lru_cache(maxsize=16)
def build_analyzer(
    use_patterns: bool,
    use_heuristics: bool,
    use_spacy: bool,
    use_camembert: bool,
    spacy_model: str,
    document_language: str = LANGUAGE,
) -> AnalyzerEngine:
    """Construit, une fois par combinaison de sources et de langue, l'analyseur Presidio.

    Le registre ne contient que nos reconnaisseurs des sources actives, dans la langue du
    document (D-03) : aucun reconnaisseur prédéfini de Presidio, dont l'EmailRecognizer qui
    peut accéder au réseau (D-11).
    """
    recognizers: list[EntityRecognizer] = []
    if use_patterns:
        recognizers.extend(build_pattern_recognizers(document_language))
    if use_heuristics:
        recognizers.extend(build_person_recognizers(language=document_language))
    if use_spacy:
        recognizers.extend(build_ner_recognizers(document_language))
    if use_camembert:
        recognizers.extend(_camembert_recognizers(document_language))
    # Presidio remplit un registre vide avec ses reconnaisseurs prédéfinis, dont celui
    # des e-mails qui peut accéder au réseau. Refuser ce cas préserve le traitement local.
    if not recognizers:
        raise ValueError("Aucune source de détection n'est activée.")
    registry = RecognizerRegistry(recognizers=recognizers, supported_languages=[document_language])
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=get_nlp_engine(spacy_model, document_language),
        supported_languages=[document_language],
    )


def analyzer_for(config: DetectionConfig) -> AnalyzerEngine:
    """Renvoie l'analyseur en cache correspondant aux sources et à la langue de config.

    Pour le français, l'appel garde la forme de l'interface (app/engine.py, cinq valeurs) :
    le cache rend alors le même objet aux deux appelants.
    """
    sources = (
        config.use_patterns,
        config.use_heuristics,
        config.use_spacy,
        config.use_camembert,
        config.spacy_model,
    )
    if config.document_language == LANGUAGE:
        return build_analyzer(*sources)
    return build_analyzer(*sources, config.document_language)


def to_detection(text: str, result: RecognizerResult) -> Detection | None:
    """Convertit un résultat Presidio en Detection ; None pour un type ou un span inconnu.

    La source vient de recognition_metadata["huisclos_source"], posée par chacun de nos
    reconnaisseurs ; à défaut, la détection est comptée comme motif.
    """
    if result.entity_type not in EntityType.__members__ or result.end <= result.start:
        return None
    metadata = result.recognition_metadata or {}
    source = Source(metadata.get("huisclos_source", Source.PATTERN.value))
    return Detection(
        start=result.start,
        end=result.end,
        entity_type=EntityType(result.entity_type),
        score=min(max(float(result.score), 0.0), 1.0),
        source=source,
        text=text[result.start : result.end],
    )


def _projected(text: str, view: AnalysisView, result: RecognizerResult) -> Detection | None:
    """Candidat de la vue rogné dans la vue (règle 1 de la fusion), puis reprojeté.

    Rogner avant de projeter retire une civilité écrite avec un invisible ("Mad\u200bame"),
    que la fusion ne reconnaîtrait plus dans le texte canonique.
    """
    if not 0 <= result.start < result.end <= len(view.text):
        return None
    candidate = to_detection(view.text, result)
    candidate = trim(view.text, candidate) if candidate is not None else None
    if candidate is None:
        return None
    start, end = view.project(candidate.start, candidate.end)
    return replace(candidate, start=start, end=end, text=text[start:end])


def _analyze(text: str, view: AnalysisView, config: DetectionConfig) -> list[Detection]:
    """Candidats de tous les reconnaisseurs, aux positions canoniques de text.

    La vue d'analyse est lue, puis chaque span est reprojeté par sa table monotone. Si la
    vue change plus que les blancs déjà unifiés avant A2, le texte lu à l'ancienne est
    analysé aussi : ses candidats sont gardés, sauf ceux qui touchent un caractère réécrit
    par la vue, dont la lecture d'origine est bruitée (D-AF-A2-5).
    """
    analyzer = analyzer_for(config)
    language = config.document_language
    results = analyzer.analyze(text=view.text, language=language)
    candidates = [d for d in (_projected(text, view, r) for r in results) if d is not None]
    if not view.is_legacy:
        legacy = analyzer.analyze(text=text.translate(LEGACY), language=language)
        original = (to_detection(text, r) for r in legacy)
        candidates += [
            d for d in original if d is not None and not view.touches_change(d.start, d.end)
        ]
    return candidates


def exclusion_spans_for(text: str, view: AnalysisView, language: str) -> list[tuple[int, int]]:
    """Passages exclus du texte, trouvés dans le texte et dans sa vue d'analyse.

    Une juridiction écrite avec un trait d'union conditionnel reste exclue : ses positions
    dans la vue sont reprojetées, puis réunies à celles du texte.
    """
    exclusions = load_exclusions_for(language)
    spans = exclusions.spans(text)
    if view.text != text:
        spans += [view.project(start, end) for start, end in exclusions.spans(view.text)]
    merged: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def add_known(
    text: str, detections: Sequence[Detection], known: Sequence[Detection]
) -> list[Detection]:
    """Ajoute aux détections les valeurs connues d'une table de dossier (D-S24-2).

    Paramètres : text, le texte analysé ; detections, les détections du moteur ; known, les
    valeurs connues retrouvées dans text, sans chevauchement entre elles.
    Valeur retournée : les détections triées, sans chevauchement. Une valeur connue comprise
    dans une détection est déjà couverte ; sinon elle remplace les détections qu'elle
    recouvre et s'étend à leur réunion, pour ne découvrir aucun caractère.
    """
    result = list(detections)
    for value in known:
        overlapping = [d for d in result if d.start < value.end and value.start < d.end]
        if any(d.start <= value.start and value.end <= d.end for d in overlapping):
            continue
        start = min([value.start, *(d.start for d in overlapping)])
        end = max([value.end, *(d.end for d in overlapping)])
        result = [d for d in result if d not in overlapping]
        result.append(replace(value, start=start, end=end, text=text[start:end]))
    return sorted(result, key=lambda d: (d.start, d.end))


def detect(
    text: str, config: DetectionConfig | None = None, known: Sequence[Detection] = ()
) -> list[Detection]:
    """Détecte les données personnelles d'un texte.

    Paramètres : text, le texte brut ; config, la configuration (hybrid par défaut, langue
    du document comprise) ; known, les valeurs d'une table de dossier retrouvées dans text
    (case_memory.find_known).
    Valeur retournée : les détections triées, sans chevauchement, après fusion, bornes
    des sociétés, valeurs connues et, si elle est activée, propagation. Les valeurs
    connues passent avant la propagation : leurs autres formes sont alors retrouvées.
    Chaque Detection reprend text[start:end] du texte reçu, jamais celui de la vue.
    Exemple : detect("Écrire à jean.martin@example.com") renvoie une détection EMAIL.
    """
    config = config or PRESETS["hybrid"]
    if not text.strip():
        return []
    view = build_view(text)
    raw = _analyze(text, view, config)
    language = config.document_language
    exclusion_spans = exclusion_spans_for(text, view, language) if config.use_exclusions else []
    detections = merge(text, raw, config, exclusion_spans)
    detections = adjust_organizations(text, detections, config, exclusion_spans, view)
    detections = add_known(text, detections, known)
    if config.use_propagation:
        detections = propagate(text, detections, config, exclusion_spans, view)
    return detections
