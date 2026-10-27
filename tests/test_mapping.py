"""Tests de la table de correspondance et de son format JSON (pseudonymize.mapping)."""

import json
from datetime import datetime

import pytest

from huisclos.models import Detection, EntityType, Source, TokenStyle
from huisclos.pseudonymize.mapping import (
    SCHEMA_NAME,
    SENSITIVE_WARNING,
    Mapping,
    MappingEntry,
    MappingError,
    MappingOccurrence,
    sha256_of,
)
from huisclos.pseudonymize.reidentify import EXACT, restore
from huisclos.pseudonymize.tokens import pseudonymize

TEXT = "Hélène LEROY a écrit à Atelier Verlaine SAS. Mme Leroy relance."


def build_mapping(created_at: str | None = "2026-10-27T12:00:00+00:00") -> Mapping:
    """Table fictive produite par la pseudonymisation de TEXT."""
    detections = []
    for fragment, entity_type in [
        ("Hélène LEROY", EntityType.PERSON),
        ("Atelier Verlaine SAS", EntityType.ORGANIZATION),
        ("Leroy", EntityType.PERSON),
    ]:
        start = TEXT.index(fragment)
        detections.append(
            Detection(start, start + len(fragment), entity_type, 1.0, Source.MANUAL, fragment)
        )
    return pseudonymize(TEXT, detections, created_at=created_at).mapping


def as_dict() -> dict:
    """Table fictive sous forme de dictionnaire JSON, prête à être altérée."""
    return json.loads(build_mapping().to_json())


def test_schema_fields() -> None:
    data = as_dict()
    assert list(data) == [
        "schema",
        "version",
        "created_at",
        "warning",
        "token_style",
        "entities",
        "occurrences",
        "pseudonymized_sha256",
    ]
    assert data["schema"] == SCHEMA_NAME
    assert data["version"] == 1
    assert data["warning"] == SENSITIVE_WARNING
    assert data["token_style"] == {"language": "fr", "open_bracket": "[", "close_bracket": "]"}
    assert data["entities"][0] == {
        "token": "[PERSONNE_1]",
        "type": "PERSON",
        "canonical": "Hélène LEROY",
        "variants": ["Hélène LEROY", "Leroy"],
    }
    expected_text = "[PERSONNE_1] a écrit à [SOCIETE_A]. Mme [PERSONNE_1] relance."
    start = expected_text.rindex("[PERSONNE_1]")
    assert data["occurrences"][2] == {
        "token": "[PERSONNE_1]",
        "original": "Leroy",
        "start": start,
        "end": start + len("[PERSONNE_1]"),
    }
    assert data["pseudonymized_sha256"] == sha256_of(expected_text)


def test_json_is_readable_utf8_with_indent_two() -> None:
    raw = build_mapping().to_json()
    assert "Hélène" in raw
    assert raw.splitlines()[1] == '  "schema": "huisclos-mapping",'


def test_round_trip_is_identical() -> None:
    mapping = build_mapping()
    restored = Mapping.from_json(mapping.to_json())
    assert restored == mapping
    assert restored.to_json() == mapping.to_json()


def test_legacy_json_without_positions_remains_readable() -> None:
    """Relit les tables version 1 produites avant la conservation des positions."""
    data = as_dict()
    for occurrence in data["occurrences"]:
        occurrence.pop("start")
        occurrence.pop("end")
    mapping = Mapping.from_json(json.dumps(data))
    assert all(o.start is None and o.end is None for o in mapping.occurrences)
    assert mapping.to_dict() == data
    restored = restore("[PERSONNE_1] a écrit à [SOCIETE_A]. Mme [PERSONNE_1] relance.", mapping)
    assert restored.text == TEXT
    assert restored.mode == EXACT


@pytest.mark.parametrize(
    ("start", "end"),
    [(None, 11), (0, None), (-1, 10), (0, 10), (True, 12), (0, "11")],
)
def test_invalid_occurrence_positions_are_refused(start: object, end: object) -> None:
    """Refuse les positions partielles, négatives, mal typées ou de longueur incorrecte."""
    data = as_dict()
    data["occurrences"][0].update(start=start, end=end)
    with pytest.raises(MappingError, match="positions"):
        Mapping.from_json(json.dumps(data))


def test_default_created_at_is_utc() -> None:
    created_at = build_mapping(created_at=None).created_at
    assert datetime.fromisoformat(created_at).utcoffset().total_seconds() == 0


def test_english_style_round_trip() -> None:
    mapping = build_mapping()
    english = Mapping(
        mapping.created_at,
        TokenStyle(language="en"),
        mapping.entities,
        mapping.occurrences,
        mapping.pseudonymized_sha256,
    )
    assert Mapping.from_json(english.to_json()).token_style.language == "en"


def test_duplicate_token_is_refused() -> None:
    data = as_dict()
    data["entities"][1]["token"] = data["entities"][0]["token"]
    with pytest.raises(MappingError, match="plusieurs fois"):
        Mapping.from_json(json.dumps(data))


@pytest.mark.parametrize("version", [2, 0, "1", True, None])
def test_unknown_version_is_refused(version: object) -> None:
    data = as_dict()
    data["version"] = version
    with pytest.raises(MappingError, match="version"):
        Mapping.from_json(json.dumps(data))


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d.update(schema="autre"), "schéma"),
        (lambda d: d.pop("entities"), "manquant : entities"),
        (lambda d: d.update(entities={}), "entities doit"),
        (lambda d: d["entities"][0].update(type="SECRET"), "type d'entité inconnu"),
        (lambda d: d["entities"][0].update(variants=[1]), "variantes"),
        (lambda d: d["entities"].__setitem__(0, "texte"), "objet JSON"),
        (lambda d: d["occurrences"][0].update(token="[PERSONNE_9]"), "absent des entités"),
        (lambda d: d["occurrences"][0].pop("original"), "manquant : original"),
        (lambda d: d.update(pseudonymized_sha256="abc"), "SHA-256"),
        (lambda d: d.update(created_at="hier"), "ISO 8601"),
        (lambda d: d.update(created_at="2026-10-27T12:00:00"), "fuseau"),
        (lambda d: d["token_style"].update(language="de"), "token_style invalide"),
        (lambda d: d["token_style"].update(open_bracket=""), "token_style invalide"),
    ],
)
def test_invalid_content_is_refused(change: object, message: str) -> None:
    data = as_dict()
    change(data)
    with pytest.raises(MappingError, match=message):
        Mapping.from_json(json.dumps(data))


@pytest.mark.parametrize("raw", ["{", "[]", '"texte"', ""])
def test_invalid_json_is_refused(raw: str) -> None:
    with pytest.raises(MappingError):
        Mapping.from_json(raw)


def test_constructor_refuses_duplicate_tokens() -> None:
    entry = MappingEntry("[PERSONNE_1]", EntityType.PERSON, "Jean DUPONT", ("Jean DUPONT",))
    with pytest.raises(MappingError):
        Mapping(
            "2026-10-27T12:00:00+00:00",
            TokenStyle(),
            (entry, entry),
            (MappingOccurrence("[PERSONNE_1]", "Jean DUPONT"),),
            sha256_of(""),
        )
