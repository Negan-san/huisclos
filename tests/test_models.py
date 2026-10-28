import dataclasses

import pytest

from huisclos.models import (
    DEFAULT_ENABLED_TYPES,
    LETTER_INDEXED,
    TOKEN_LABELS,
    Detection,
    EntityType,
    Source,
)


def make_detection(**overrides: object) -> Detection:
    values: dict[str, object] = {
        "start": 3,
        "end": 8,
        "entity_type": EntityType.PERSON,
        "score": 0.8,
        "source": Source.HEURISTIC,
        "text": "Alice",
    }
    values.update(overrides)
    return Detection(**values)  # type: ignore[arg-type]


def test_entity_type_values_equal_names() -> None:
    assert [member.name for member in EntityType] == [
        "PERSON",
        "ORGANIZATION",
        "ADDRESS",
        "EMAIL",
        "PHONE",
        "IBAN",
        "NIR",
        "SIREN",
        "SIRET",
        "BIRTH_DATE",
        "CASE_NUMBER",
        "LOCATION",
        "CUSTOM",
    ]
    assert all(member.value == member.name for member in EntityType)


def test_source_values() -> None:
    assert [member.value for member in Source] == [
        "checksum",
        "pattern",
        "heuristic",
        "ner_spacy",
        "ner_camembert",
        "propagation",
        "manual",
        "case_table",
        "ner_gliner",
    ]


def test_valid_detection() -> None:
    detection = make_detection()
    assert detection.length == 5
    assert detection.entity_type == "PERSON"


def test_detection_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_detection().start = 0  # type: ignore[misc]


@pytest.mark.parametrize(
    "overrides",
    [
        {"start": -1, "end": 4},
        {"end": 3},
        {"end": 2},
        {"score": -0.1},
        {"score": 1.01},
        {"score": float("nan")},
        {"score": float("inf")},
        {"text": "Alic"},
        {"text": "Alicia!"},
    ],
)
def test_invalid_detection_raises(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        make_detection(**overrides)


@pytest.mark.parametrize("score", [0.0, 1.0])
def test_score_bounds_are_accepted(score: float) -> None:
    assert make_detection(score=score).score == score


def test_token_labels_cover_every_type() -> None:
    assert set(TOKEN_LABELS) == set(EntityType)
    assert TOKEN_LABELS[EntityType.PERSON] == ("PERSONNE", "PERSON")
    assert TOKEN_LABELS[EntityType.ORGANIZATION] == ("SOCIETE", "COMPANY")
    assert TOKEN_LABELS[EntityType.PHONE] == ("TELEPHONE", "PHONE")
    assert TOKEN_LABELS[EntityType.BIRTH_DATE] == ("DATE_NAISSANCE", "BIRTH_DATE")
    assert TOKEN_LABELS[EntityType.CASE_NUMBER] == ("DOSSIER", "CASE")
    assert TOKEN_LABELS[EntityType.LOCATION] == ("LIEU", "PLACE")
    assert TOKEN_LABELS[EntityType.CUSTOM] == ("AUTRE", "OTHER")


def test_default_constants() -> None:
    assert LETTER_INDEXED == frozenset({EntityType.ORGANIZATION})
    assert EntityType.LOCATION not in DEFAULT_ENABLED_TYPES
    assert DEFAULT_ENABLED_TYPES == frozenset(EntityType) - {EntityType.LOCATION}
