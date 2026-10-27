"""Tests de detection.propagation et des outils de texte qu'elle utilise."""

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.propagation import (
    matches_case,
    organization_variants,
    person_variants,
    propagate,
)
from huisclos.models import Detection, EntityType, Source
from huisclos.text_utils import fold, fold_same_length, is_capitalized_form

CONFIG = DetectionConfig(threshold=0.40)


def det(text: str, fragment: str, entity_type: EntityType, score: float = 0.85) -> Detection:
    """Détection sur la première occurrence de fragment."""
    start = text.index(fragment)
    return Detection(start, start + len(fragment), entity_type, score, Source.NER_SPACY, fragment)


def found(text: str, detections: list[Detection]) -> list[str]:
    """Textes des détections, dans l'ordre du texte."""
    return [d.text for d in detections]


def test_fold_and_capitalization_helpers() -> None:
    assert fold("  L\u2019Étude   Durand\u2013Roy ") == "l'etude durand-roy"
    assert len(fold_same_length("École  à")) == len("École  à")
    assert is_capitalized_form("Petit") and is_capitalized_form("PETIT")
    assert not is_capitalized_form("petit") and not is_capitalized_form("12")
    assert is_capitalized_form("d\u2019Aubigné") and not is_capitalized_form("l'article")


def test_person_and_organization_variants() -> None:
    assert person_variants("Jean DUPONT") == {"Jean DUPONT", "DUPONT", "DUPONT Jean"}
    assert person_variants("Sophie Petit") == {"Sophie Petit", "Petit", "Petit Sophie"}
    assert "Li" not in person_variants("Anne Li")
    assert person_variants("Dupont") == {"Dupont"}
    assert organization_variants("Garnier Logistique SARL") == {
        "Garnier Logistique SARL",
        "Garnier Logistique",
    }


def test_four_forms_of_jean_dupont_are_covered() -> None:
    text = (
        "Mon client Jean DUPONT conteste. M. Dupont a écrit. "
        "DUPONT n'a rien reçu. Selon lui, Dupont travaillait le samedi. DUPONT Jean signe."
    )
    origin = det(text, "Jean DUPONT", EntityType.PERSON)
    result = propagate(text, [origin], CONFIG)
    assert found(text, result) == ["Jean DUPONT", "Dupont", "DUPONT", "Dupont", "DUPONT Jean"]
    added = [d for d in result if d is not origin]
    assert all(d.source == Source.PROPAGATION for d in added)
    assert all(d.score == origin.score and d.entity_type == EntityType.PERSON for d in added)
    assert all(d.text == text[d.start : d.end] for d in result)


def test_lowercase_common_word_is_never_masked() -> None:
    text = "Mme Sophie Petit a envoyé un petit mot. PETIT confirme, Petit aussi."
    result = propagate(text, [det(text, "Sophie Petit", EntityType.PERSON)], CONFIG)
    assert found(text, result) == ["Sophie Petit", "PETIT", "Petit"]
    assert not matches_case("petit", "Petit")


def test_accents_and_apostrophes_are_ignored_when_searching() -> None:
    text = "M. Lefèvre est venu. LEFEVRE a signé. Maître d\u2019Aubigné et d'Aubigné."
    origins = [
        det(text, "Lefèvre", EntityType.PERSON),
        det(text, "d\u2019Aubigné", EntityType.PERSON),
    ]
    result = propagate(text, origins, CONFIG)
    assert found(text, result) == ["Lefèvre", "LEFEVRE", "d\u2019Aubigné", "d'Aubigné"]


def test_no_propagation_inside_excluded_span() -> None:
    text = "Paul Martin plaide. Le Tribunal judiciaire de Martin statue. Martin conteste."
    court = (text.index("Tribunal"), text.index(" statue"))
    result = propagate(text, [det(text, "Paul Martin", EntityType.PERSON)], CONFIG, [court])
    assert [d.start for d in result] == [0, text.rindex("Martin")]
    no_exclusion = DetectionConfig(threshold=0.40, use_exclusions=False)
    origin = det(text, "Paul Martin", EntityType.PERSON)
    assert len(propagate(text, [origin], no_exclusion, [court])) == 3


def test_occurrences_overlapping_existing_detections_are_skipped() -> None:
    text = "Jean DUPONT et Marie DUPONT. DUPONT est absent."
    jean = det(text, "Jean DUPONT", EntityType.PERSON)
    marie = Detection(15, 27, EntityType.PERSON, 0.70, Source.HEURISTIC, text[15:27])
    result = propagate(text, [jean, marie], CONFIG)
    assert found(text, result) == ["Jean DUPONT", "Marie DUPONT", "DUPONT"]
    assert result[-1].score == 0.85


def test_organization_name_without_legal_form_is_propagated() -> None:
    text = (
        "La société Garnier Logistique SARL emploie Paul. "
        "Garnier Logistique SARL paie. Garnier Logistique aussi."
    )
    origin = det(text, "Garnier Logistique SARL", EntityType.ORGANIZATION)
    result = propagate(text, [origin], CONFIG)
    assert found(text, result) == ["Garnier Logistique SARL"] * 2 + ["Garnier Logistique"]
    assert {d.entity_type for d in result} == {EntityType.ORGANIZATION}


@pytest.mark.parametrize("entity_type", [EntityType.EMAIL, EntityType.ADDRESS])
def test_other_types_are_not_propagated(entity_type: EntityType) -> None:
    text = "Paris Nord, puis Paris Nord."
    assert len(propagate(text, [det(text, "Paris Nord", entity_type)], CONFIG)) == 1


def test_propagation_does_not_partially_overlap_an_exclusion() -> None:
    """Un nom propagé qui traverse la fin d'une juridiction ne doit pas la masquer."""
    text = "Jean DUPONT. Tribunal judiciaire de Jean DUPONT statue."
    court = (text.index("Tribunal"), text.rindex("Jean") + len("Jean"))
    result = propagate(text, [det(text, "Jean DUPONT", EntityType.PERSON)], CONFIG, [court])
    assert not [d for d in result if d.start < court[1] and court[0] < d.end]


def test_propagation_keeps_a_name_containing_an_exclusion() -> None:
    """Une exclusion contenue dans le nom ("SARL") n'empêche pas la propagation."""
    text = "Garnier Logistique SARL emploie Paul. Garnier Logistique SARL paie."
    sarl = (text.rindex("SARL"), text.rindex("SARL") + 4)
    origin = det(text, "Garnier Logistique SARL", EntityType.ORGANIZATION)
    result = propagate(text, [origin], CONFIG, [sarl])
    assert found(text, result) == ["Garnier Logistique SARL"] * 2


@pytest.mark.parametrize(
    "reference",
    ["Cour de cassation", "article L. 1232-6 du Code du travail"],
)
def test_propagation_skips_an_enclosed_legal_reference(reference: str) -> None:
    """Une exclusion forte interne empêche l'ajout, même si les deux bornes sont dépassées."""
    name = f"Atelier {reference} Conseil"
    text = f"{name}. {name}."
    start = text.rindex(reference)
    origin = det(text, name, EntityType.ORGANIZATION)
    result = propagate(text, [origin], CONFIG, [(start, start + len(reference))])
    assert result == [origin]


def test_short_company_form_is_widened_to_the_long_form() -> None:
    """Aucune occurrence de la forme longue ne reste couverte par la seule forme courte."""
    text = "Verrerie Halbarde SARL signe. Puis la Verrerie Halbarde SARL paie Halbarde SARL."
    short_start = text.index("Halbarde SARL", text.index("Puis"))
    short = Detection(
        short_start,
        short_start + 13,
        EntityType.ORGANIZATION,
        0.70,
        Source.HEURISTIC,
        "Halbarde SARL",
    )
    result = propagate(
        text, [det(text, "Verrerie Halbarde SARL", EntityType.ORGANIZATION), short], CONFIG
    )
    assert found(text, result) == [
        "Verrerie Halbarde SARL",
        "Verrerie Halbarde SARL",
        "Halbarde SARL",
    ]
    assert result[1].start == text.index("Verrerie", short_start - 10)
    assert result[1].source == Source.HEURISTIC and result[1].score == 0.70
    assert all(d.text == text[d.start : d.end] for d in result)


def test_widening_never_overlaps_another_detection() -> None:
    """La forme courte reste courte si la forme longue toucherait une autre détection."""
    text = "Verrerie Halbarde SARL. Verrerie Halbarde SARL"
    second = text.rindex("Verrerie")
    detections = [
        det(text, "Verrerie Halbarde SARL", EntityType.ORGANIZATION),
        Detection(second, second + 8, EntityType.PERSON, 1.0, Source.MANUAL, "Verrerie"),
        Detection(
            second + 9, len(text), EntityType.ORGANIZATION, 0.70, Source.HEURISTIC, "Halbarde SARL"
        ),
    ]
    assert found(text, propagate(text, detections, CONFIG)) == [
        "Verrerie Halbarde SARL",
        "Verrerie",
        "Halbarde SARL",
    ]
