import pytest
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

from huisclos.detection.ner import (
    NER_SCORE,
    build_ner_recognizers,
    build_nlp_engine,
)

TEXT = "Monsieur Jean Dupont a été embauché par la société Atelier Verlaine à Lyon."
ENTITIES = ["PERSON", "ORGANIZATION", "LOCATION"]


@pytest.fixture(scope="session")
def registry() -> RecognizerRegistry:
    """Registre français limité à nos reconnaisseurs NER (aucun reconnaisseur prédéfini)."""
    registry = RecognizerRegistry(supported_languages=["fr"])
    for recognizer in build_ner_recognizers():
        registry.add_recognizer(recognizer)
    return registry


@pytest.fixture(scope="session")
def analyzer(registry: RecognizerRegistry) -> AnalyzerEngine:
    """Moteur Presidio chargé une seule fois : le modèle spaCy est lent à charger."""
    return AnalyzerEngine(
        registry=registry, nlp_engine=build_nlp_engine(), supported_languages=["fr"]
    )


def test_person_surname_is_found(analyzer: AnalyzerEngine) -> None:
    results = analyzer.analyze(TEXT, language="fr", entities=ENTITIES)
    persons = [TEXT[r.start : r.end] for r in results if r.entity_type == "PERSON"]
    assert any("Dupont" in person for person in persons)


def test_results_carry_source_and_fixed_score(analyzer: AnalyzerEngine) -> None:
    results = analyzer.analyze(TEXT, language="fr", entities=ENTITIES)
    assert results
    for result in results:
        assert result.recognition_metadata["huisclos_source"] == "ner_spacy"
        assert result.score == pytest.approx(NER_SCORE)
        assert result.entity_type in ENTITIES


def test_registry_has_no_english_recognizer(registry: RecognizerRegistry) -> None:
    languages = {recognizer.supported_language for recognizer in registry.recognizers}
    assert languages == {"fr"}


def test_ner_runs_without_network(analyzer: AnalyzerEngine, no_network: None) -> None:
    results = analyzer.analyze(TEXT, language="fr", entities=ENTITIES)
    assert any(r.entity_type == "PERSON" for r in results)


def test_missing_model_is_not_downloaded() -> None:
    with pytest.raises(RuntimeError, match="n'est pas installé"):
        build_nlp_engine("fr_modele_inexistant")
