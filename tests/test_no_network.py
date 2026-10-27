"""Vérifie qu'aucune connexion réseau n'est ouverte pendant la détection complète (D-11)."""

from pathlib import Path

import pytest

from huisclos.config import PRESETS
from huisclos.detection.pipeline import build_analyzer, detect, get_nlp_engine
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
