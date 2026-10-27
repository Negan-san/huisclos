from pathlib import Path

import pytest

from huisclos.detection.exclusions import is_excluded, load_exclusions, parse_exclusions
from huisclos.models import Detection, EntityType, Source


def make(text: str, fragment: str, entity_type: EntityType) -> Detection:
    start = text.index(fragment)
    return Detection(start, start + len(fragment), entity_type, 0.85, Source.NER_SPACY, fragment)


@pytest.mark.parametrize(
    "text",
    [
        "Conseil de prud'hommes de Nanterre",
        "Conseil de prud\u2019hommes de Nanterre",
        "Cour d'appel de Versailles",
        "Cour d\u2019appel de Versailles",
        "Tribunal judiciaire de Aix-en-Provence",
        "Tribunal des activit\u00e9s \u00e9conomiques de Paris",
        "Cour de cassation",
        "article L. 1232-6 du Code du travail",
        "loi n\u00b0 78-17",
        "Cour d'appel d'Angers",
        "Cour d\u2019appel d\u2019Aix-en-Provence",
        "Tribunal judiciaire d'\u00c9vry",
        "ARTICLE L. 1232-6 DU CODE DU TRAVAIL",
        "LOI N\u00b0 78-17",
    ],
)
def test_whole_reference_is_covered(text: str) -> None:
    assert load_exclusions().spans(text) == [(0, len(text))]


def test_place_name_does_not_swallow_next_word() -> None:
    text = "Tribunal de commerce de Lyon Le 12 mars"
    assert load_exclusions().spans(text) == [(0, len("Tribunal de commerce de Lyon"))]


def test_spans_are_sorted_and_merged() -> None:
    text = "La CNIL et l'URSSAF, puis le Code civil."
    spans = load_exclusions().spans(text)
    assert spans == sorted(spans)
    assert [text[s:e] for s, e in spans] == ["CNIL", "URSSAF", "Code civil"]


def test_acronyms_are_exposed() -> None:
    acronyms = load_exclusions().acronyms
    assert {"URSSAF", "SAS", "CDI", "RGPD", "CSE"} <= acronyms


def test_person_inside_excluded_span_is_excluded() -> None:
    text = "Conseil de prud'hommes de Nanterre"
    spans = load_exclusions().spans(text)
    assert is_excluded(make(text, "Nanterre", EntityType.LOCATION), spans)
    assert is_excluded(make(text, text, EntityType.ORGANIZATION), spans)


def test_detection_overflowing_the_span_is_kept() -> None:
    text = "Cour d'appel de Versailles Dupont"
    spans = load_exclusions().spans(text)
    assert not is_excluded(make(text, "Versailles Dupont", EntityType.PERSON), spans)


@pytest.mark.parametrize(
    "entity_type",
    [
        EntityType.NIR,
        EntityType.EMAIL,
        EntityType.PHONE,
        EntityType.IBAN,
        EntityType.SIREN,
        EntityType.SIRET,
    ],
)
def test_keyed_identifiers_are_never_excluded(entity_type: EntityType) -> None:
    text = "article 1240"
    detection = Detection(0, len(text), entity_type, 1.0, Source.CHECKSUM, text)
    assert not is_excluded(detection, [(0, len(text))])


def test_loading_is_cached() -> None:
    assert load_exclusions() is load_exclusions()


def test_custom_file_is_read_as_utf8(tmp_path: Path) -> None:
    path = tmp_path / "exclusions.txt"
    path.write_text(
        "# commentaire\n[mots]\nÉtablissement\n[textes]\nre:Annexe \\d+\n", encoding="utf-8"
    )
    exclusions = load_exclusions(path)
    assert [(s, e) for s, e in exclusions.spans("L'\u00e9tablissement, Annexe 12")] == [
        (2, 15),
        (17, 26),
    ]


@pytest.mark.parametrize(
    "content",
    ["[inconnue]\nx\n", "orpheline\n", "[textes]\nre:(\n"],
)
def test_invalid_file_is_refused(content: str) -> None:
    with pytest.raises(ValueError):
        parse_exclusions(content)


@pytest.mark.parametrize("prefix", ["Saint", "Sainte", "St", "Ste", "SAINT", "SAINTE", "ST", "STE"])
def test_court_with_an_unhyphenated_compound_place_is_fully_excluded(prefix: str) -> None:
    """Une variante de lieu composée reste exclue sans absorber le nom qui suit."""
    reference = f"Tribunal judiciaire de {prefix} Denis"
    text = reference + ", Paul Martin comparaît."
    assert load_exclusions().spans(text) == [(0, len(reference))]
