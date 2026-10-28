"""Moteur de détection : assemble les reconnaisseurs, la fusion, les bornes et la propagation.

Entrées : un texte français, une DetectionConfig (config.PRESETS["hybrid"] par défaut) et,
pour un dossier, les valeurs connues d'une table précédente.
Sorties : la liste triée des Detection retenues, sans chevauchement.
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
from huisclos.detection.exclusions import load_exclusions
from huisclos.detection.merge import merge
from huisclos.detection.ner import LANGUAGE, build_ner_recognizers, build_nlp_engine
from huisclos.detection.organization_bounds import adjust_organizations
from huisclos.detection.patterns import build_pattern_recognizers
from huisclos.detection.person_heuristics import build_person_recognizers
from huisclos.detection.propagation import propagate
from huisclos.models import Detection, EntityType, Source

# Module attendu de l'option CamemBERT (D-06) ; il expose build_camembert_recognizers().
CAMEMBERT_MODULE = "huisclos.detection.camembert"


@lru_cache(maxsize=2)
def get_nlp_engine(model_name: str) -> NlpEngine:
    """Charge une seule fois le moteur spaCy de Presidio pour un modèle donné.

    Presidio exige un moteur NLP même sans reconnaisseur NER ; le même moteur sert donc à
    toutes les configurations, ce qui évite de recharger le modèle (plusieurs secondes).
    """
    return build_nlp_engine(model_name)


def _camembert_recognizers() -> list[EntityRecognizer]:
    """Charge les reconnaisseurs CamemBERT, ou explique pourquoi c'est impossible."""
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
) -> AnalyzerEngine:
    """Construit, une fois par combinaison de sources, l'analyseur Presidio.

    Le registre ne contient que des reconnaisseurs français des sources actives (D-03) :
    aucun reconnaisseur anglais ni prédéfini de Presidio, dont l'EmailRecognizer qui peut
    accéder au réseau (D-11).
    """
    recognizers: list[EntityRecognizer] = []
    if use_patterns:
        recognizers.extend(build_pattern_recognizers())
    if use_heuristics:
        recognizers.extend(build_person_recognizers())
    if use_spacy:
        recognizers.extend(build_ner_recognizers())
    if use_camembert:
        recognizers.extend(_camembert_recognizers())
    # Presidio remplit un registre vide avec ses reconnaisseurs prédéfinis, dont celui
    # des e-mails qui peut accéder au réseau. Refuser ce cas préserve le traitement local.
    if not recognizers:
        raise ValueError("Aucune source de détection n'est activée.")
    registry = RecognizerRegistry(recognizers=recognizers, supported_languages=[LANGUAGE])
    return AnalyzerEngine(
        registry=registry,
        nlp_engine=get_nlp_engine(spacy_model),
        supported_languages=[LANGUAGE],
    )


def analyzer_for(config: DetectionConfig) -> AnalyzerEngine:
    """Renvoie l'analyseur en cache correspondant aux sources de config."""
    return build_analyzer(
        config.use_patterns,
        config.use_heuristics,
        config.use_spacy,
        config.use_camembert,
        config.spacy_model,
    )


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

    Paramètres : text, le texte brut ; config, la configuration (hybrid par défaut) ; known,
    les valeurs d'une table de dossier retrouvées dans text (case_memory.find_known).
    Valeur retournée : les détections triées, sans chevauchement, après fusion, bornes
    des sociétés, valeurs connues et, si elle est activée, propagation. Les valeurs
    connues passent avant la propagation : leurs autres formes sont alors retrouvées.
    Exemple : detect("Écrire à jean.martin@example.com") renvoie une détection EMAIL.
    """
    config = config or PRESETS["hybrid"]
    if not text.strip():
        return []
    # spaCy traite mal certains blancs typographiques. Le remplacement garde la longueur ;
    # la conversion ci-dessous reprend toujours les valeurs et positions du texte original.
    analysis_text = text.replace("\u00a0", " ").replace("\u202f", " ")
    results = analyzer_for(config).analyze(text=analysis_text, language=LANGUAGE)
    raw = [d for d in (to_detection(text, r) for r in results) if d is not None]
    exclusion_spans = load_exclusions().spans(text) if config.use_exclusions else []
    detections = merge(text, raw, config, exclusion_spans)
    detections = adjust_organizations(text, detections, config, exclusion_spans)
    detections = add_known(text, detections, known)
    if config.use_propagation:
        detections = propagate(text, detections, config, exclusion_spans)
    return detections
