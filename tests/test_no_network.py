"""Vérifie qu'aucune connexion réseau n'est ouverte pendant la détection complète (D-11)."""

from pathlib import Path

import pytest

from huisclos.config import PRESETS, DetectionConfig
from huisclos.detection.pipeline import analyzer_for, build_analyzer, detect, get_nlp_engine
from huisclos.models import EntityType

TEXT = (Path(__file__).parent / "fixtures" / "mini_case_fr.txt").read_text(encoding="utf-8")


@pytest.mark.usefixtures("no_network")
def test_analyzer_construction_and_detection_without_network() -> None:
    # Les caches sont vidés pour que le modèle et l'analyseur soient construits sous la
    # fixture : un téléchargement caché par Presidio ou spaCy ferait échouer le test.
    build_analyzer.cache_clear()
    get_nlp_engine.cache_clear()
    result = detect(TEXT, PRESETS["hybrid"])
    assert {EntityType.PERSON, EntityType.EMAIL, EntityType.NIR} <= {d.entity_type for d in result}


@pytest.mark.usefixtures("no_network")
@pytest.mark.parametrize("name", ["hybrid", "patterns_only", "ner_only"])
def test_presets_use_only_local_french_recognizers(name: str) -> None:
    """Le registre contient exactement les sources françaises demandées, sans repli."""
    config = PRESETS[name]
    analyzer = analyzer_for(config)
    names = {r.name for r in analyzer.registry.recognizers}
    assert {r.supported_language for r in analyzer.registry.recognizers} == {"fr"}
    assert ("FrenchSpacyRecognizer" in names) == config.use_spacy
    assert ("CivilityPersonRecognizer" in names) == config.use_heuristics
    assert ("NirRecognizer" in names) == config.use_patterns
    assert all(type(r).__module__.startswith("huisclos.") for r in analyzer.registry.recognizers)
    assert detect(TEXT, config)


@pytest.mark.usefixtures("no_network")
def test_empty_sources_never_load_presidio_defaults() -> None:
    """Refuse un registre vide avant le repli Presidio qui chargerait tldextract."""
    config = DetectionConfig(
        use_patterns=False, use_heuristics=False, use_spacy=False, use_propagation=False
    )
    with pytest.raises(ValueError, match="source"):
        analyzer_for(config)
    with pytest.raises(ValueError, match="source"):
        detect("test@example.test", config)
