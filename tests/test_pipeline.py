"""Tests de detection.pipeline sur la lettre fictive mini_case, et de la configuration."""

import json
import random
import time
from pathlib import Path

import pytest

from huisclos.config import FALLBACK_THRESHOLD, PRESETS, DetectionConfig, default_threshold
from huisclos.detection.pipeline import detect
from huisclos.evaluation.synthetic_ids import format_nir, format_siret, make_nir, make_siret
from huisclos.models import Detection, EntityType

FIXTURES = Path(__file__).parent / "fixtures"
TEXT = (FIXTURES / "mini_case_fr.txt").read_text(encoding="utf-8")
EXPECTED = json.loads((FIXTURES / "mini_case_expected.json").read_text(encoding="utf-8"))
COURT = "Conseil de prud'hommes de Nanterre"
ARTICLE = "l'article L. 1232-6 du Code du travail"


@pytest.fixture(scope="module")
def hybrid_result() -> list[Detection]:
    """Détections du preset hybrid sur mini_case, calculées une seule fois."""
    return detect(TEXT, PRESETS["hybrid"])


def assert_clean(detections: list[Detection]) -> None:
    """Vérifie le texte exact, le tri et l'absence de chevauchement."""
    assert all(d.text == TEXT[d.start : d.end] for d in detections)
    for left, right in zip(detections, detections[1:], strict=False):
        assert left.end <= right.start


def test_expected_spans_match_the_fixture_text() -> None:
    assert 15 <= len(EXPECTED)
    for item in EXPECTED:
        assert TEXT[item["start"] : item["end"]] == item["text"]
        assert item["type"] in EntityType.__members__
    rng = random.Random(18)
    assert format_nir(make_nir(rng)) in TEXT
    assert format_siret(make_siret(rng)) in TEXT


@pytest.mark.parametrize("item", EXPECTED, ids=lambda item: f"{item['type']}:{item['text']}")
def test_hybrid_covers_each_expected_span(hybrid_result: list[Detection], item: dict) -> None:
    covering = [
        d
        for d in hybrid_result
        if d.start <= item["start"] and item["end"] <= d.end and d.entity_type == item["type"]
    ]
    assert covering, f"non couvert : {item}"


def test_no_detection_in_court_or_article(hybrid_result: list[Detection]) -> None:
    for phrase in (COURT, ARTICLE):
        start = TEXT.index(phrase)
        end = start + len(phrase)
        assert not [d for d in hybrid_result if d.start < end and start < d.end], phrase


def test_lowercase_petit_is_not_masked(hybrid_result: list[Detection]) -> None:
    start = TEXT.index("un petit courrier") + 3
    assert not [d for d in hybrid_result if d.start <= start < d.end]


def test_hybrid_output_is_clean(hybrid_result: list[Detection]) -> None:
    assert_clean(hybrid_result)


@pytest.mark.parametrize("separator", ["\u00a0", "\u202f"])
def test_hybrid_covers_typographic_variant_with_original_offsets(separator: str) -> None:
    """Les blancs et apostrophes typographiques gardent le rappel et les positions."""
    text = TEXT.replace(" ", separator).replace("'", "\u2019")
    result = detect(text, PRESETS["hybrid"])
    for item in EXPECTED:
        assert any(
            d.start <= item["start"] and item["end"] <= d.end and d.entity_type == item["type"]
            for d in result
        ), item
    assert all(d.text == text[d.start : d.end] for d in result)
    assert all(left.end <= right.start for left, right in zip(result, result[1:], strict=False))
    for phrase in (COURT, ARTICLE):
        variant = phrase.replace(" ", separator).replace("'", "\u2019")
        start = text.index(variant)
        assert not [d for d in result if d.start < start + len(variant) and start < d.end]


@pytest.mark.parametrize("name", ["patterns_only", "ner_only", "hybrid_no_propagation"])
def test_other_presets_run(name: str) -> None:
    result = detect(TEXT, PRESETS[name])
    assert result
    assert_clean(result)
    sources = {d.source.value for d in result}
    if name == "ner_only":
        assert sources == {"ner_spacy"}
    if name == "patterns_only":
        assert "ner_spacy" not in sources


def test_empty_text_gives_no_detection() -> None:
    assert detect("   \n") == []


def test_ten_thousand_characters_in_less_than_three_seconds(hybrid_result: list[Detection]) -> None:
    long_text = (TEXT + "\n") * (10_000 // len(TEXT) + 1)
    started = time.perf_counter()
    detect(long_text[:10_000], PRESETS["hybrid"])
    assert time.perf_counter() - started < 3.0


def test_presets_flags() -> None:
    assert not PRESETS["patterns_only"].use_spacy and PRESETS["patterns_only"].use_heuristics
    assert not PRESETS["ner_only"].use_patterns and not PRESETS["ner_only"].use_heuristics
    assert (
        PRESETS["hybrid"].use_propagation and not PRESETS["hybrid_no_propagation"].use_propagation
    )
    assert PRESETS["hybrid_camembert"].use_camembert and not PRESETS["hybrid"].use_camembert
    assert all(config.use_exclusions for config in PRESETS.values())
    assert EntityType.LOCATION not in PRESETS["hybrid"].enabled_types


def test_default_threshold_reads_file_or_falls_back(tmp_path: Path) -> None:
    assert default_threshold(tmp_path / "absent.json") == FALLBACK_THRESHOLD == 0.40
    good = tmp_path / "threshold.json"
    good.write_text('{"threshold": 0.55}', encoding="utf-8")
    assert default_threshold(good) == 0.55
    for content in ('{"threshold": 1.5}', '{"seuil": 0.5}', "pas du json", '{"threshold": true}'):
        good.write_text(content, encoding="utf-8")
        with pytest.raises(ValueError):
            default_threshold(good)


def test_config_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError):
        DetectionConfig(threshold=-0.1)


def test_court_is_not_masked_when_a_name_crosses_its_end() -> None:
    """Une mention NER partiellement exclue ne doit pas masquer la juridiction."""
    text = "M. Paul Martin. Tribunal judiciaire de Paul Martin."
    court_start = text.index("Tribunal")
    court_end = text.rindex("Paul") + len("Paul")
    result = detect(text, PRESETS["hybrid_no_propagation"])
    assert any(d.text == "Paul Martin" and d.start == 3 for d in result)
    assert not [d for d in result if d.start < court_end and court_start < d.end]


def test_court_is_not_masked_when_fully_inside_a_ner_name(no_network: None) -> None:
    """Reproduit le défaut de fusion avec le modèle français installé et sans réseau."""
    text = "La société Tribunal judiciaire de Nanterre SARL."
    reference = "Tribunal judiciaire de Nanterre"
    start = text.index(reference)
    result = detect(text, PRESETS["hybrid"])
    assert not any(d.start < start + len(reference) and start < d.end for d in result)
