"""Tests du contrôle final du texte pseudonymisé (pseudonymize.final_check).

Restes plantés dans des textes fictifs : nom de famille oublié en minuscules, valeur
rejetée en revue, détection à cheval sur un jeton ; puis le cas de démonstration, sans alerte.
"""

from dataclasses import replace
from pathlib import Path

from huisclos.config import PRESETS
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.final_check import (
    check_threshold,
    excerpt,
    final_check,
    neutralize_tokens,
    significant_parts,
    source_span,
)
from huisclos.pseudonymize.tokens import pseudonymize

P = EntityType.PERSON
ROOT = Path(__file__).resolve().parents[1]
TEXT = (
    "M. Pierre VERNOLAC conteste la rupture. Le dossier vernolac reste ouvert auprès de "
    "la société Atelier Brunel SARL."
)


def mention(text: str, fragment: str, kind: EntityType = P, start: int = 0) -> Detection:
    """Détection manuelle d'un fragment, cherché à partir de start."""
    begin = text.index(fragment, start)
    return Detection(begin, begin + len(fragment), kind, 0.9, Source.MANUAL, fragment)


def planted():
    """Pseudonymise TEXT en laissant "vernolac" en minuscules hors de la détection."""
    detections = [
        mention(TEXT, "Pierre VERNOLAC"),
        mention(TEXT, "Atelier Brunel SARL", EntityType.ORGANIZATION),
    ]
    return pseudonymize(TEXT, detections)


def test_check_threshold_is_lower_and_never_negative() -> None:
    assert check_threshold(0.30) == 0.1
    assert check_threshold(0.75) == 0.55
    assert check_threshold(0.1) == 0.0


def test_neutralized_text_keeps_length_and_hides_tokens() -> None:
    result = planted()
    neutral = neutralize_tokens(result)
    assert len(neutral) == len(result.text)
    assert "[" not in neutral
    assert neutral.startswith("M." + " " * (len("[PERSONNE_1]") + 2) + "conteste")


def test_significant_parts_of_a_person_and_a_company() -> None:
    assert {"Pierre VERNOLAC", "VERNOLAC"} <= significant_parts(P, "Pierre VERNOLAC")
    assert significant_parts(P, "Wei LI") == {"Wei LI", "LI Wei"}
    # "Conseil" figure dans data/exclusions_fr.txt : seul, il ne serait pas un indice.
    assert "CONSEIL" not in significant_parts(P, "Jean CONSEIL")
    company = significant_parts(EntityType.ORGANIZATION, "Garnier Logistique SARL")
    assert company == {"Garnier Logistique SARL", "Garnier Logistique"}
    assert significant_parts(EntityType.EMAIL, "a@example.com") == {"a@example.com"}


def test_planted_surname_is_reported_from_the_table() -> None:
    result = planted()
    found = final_check(result)
    assert [(d.text, d.entity_type, d.source) for d in found] == [
        ("vernolac", P, Source.CASE_TABLE)
    ]
    assert result.text[found[0].start : found[0].end] == "vernolac"


def test_rejected_value_does_not_raise_an_alert() -> None:
    result = planted()
    assert final_check(result, rejected_values=["Vernolac"]) == []
    start = TEXT.index("vernolac")
    assert final_check(result, rejected_spans=[(start, start + 8)]) == []
    assert final_check(result, rejected_values=["Pierre"]) != []


def test_masking_the_reported_value_clears_the_check() -> None:
    result = planted()
    found = final_check(result)
    added = [
        Detection(
            *source_span(result, found[0].start, found[0].end), P, 1.0, Source.MANUAL, "vernolac"
        )
    ]
    detections = [
        mention(TEXT, "Pierre VERNOLAC"),
        *added,
        mention(TEXT, "Atelier Brunel SARL", EntityType.ORGANIZATION),
    ]
    again = pseudonymize(TEXT, detections)
    assert again.text.count("[PERSONNE_1]") == 2
    assert final_check(again) == []


def test_source_span_maps_back_to_the_original_text() -> None:
    result = planted()
    start = result.text.index("vernolac")
    begin, end = source_span(result, start, start + 8)
    assert TEXT[begin:end] == "vernolac"


def test_detection_residual_is_split_around_tokens() -> None:
    result = planted()
    neutral = neutralize_tokens(result)
    crossing = Detection(0, 30, P, 0.5, Source.HEURISTIC, neutral[:30])
    found = final_check(result, lambda text: [crossing])
    texts = [d.text for d in found]
    assert "M." in texts
    assert all("[" not in text for text in texts)
    assert "vernolac" in texts


def test_detection_receives_the_neutralized_text() -> None:
    result = planted()
    seen: list[str] = []
    final_check(result, lambda text: seen.append(text) or [])
    assert seen == [neutralize_tokens(result)]


def test_excerpt_is_cut_at_blanks_and_relocates_the_residual() -> None:
    result = planted()
    residual = final_check(result)[0]
    piece, local = excerpt(result.text, residual, width=12)
    assert piece[local.start : local.end] == "vernolac"
    assert not piece.startswith(" ") and not piece.endswith(" ")
    assert len(piece) <= len("vernolac") + 24


def test_demo_case_processed_normally_raises_no_alert() -> None:
    text = (ROOT / "data" / "samples" / "demo_case_fr.txt").read_text(encoding="utf-8")
    config = PRESETS["hybrid"]
    result = pseudonymize(text, detect(text, config))
    lowered = replace(config, threshold=check_threshold(config.threshold))
    assert final_check(result, lambda neutral: detect(neutral, lowered)) == []


def test_value_left_in_clear_by_a_high_threshold_is_reported() -> None:
    text = "Adresse : 12 rue des Tilleuls 48360 Ormecendre. Contact : M. Pierre VERNOLAC."
    # Au seuil 0,80, l'adresse complète (0,70 au barème D-07) reste en clair ; le contrôle,
    # à 0,60, la retrouve.
    strict = replace(PRESETS["hybrid"], threshold=0.80)
    detections = detect(text, strict)
    assert not any(d.entity_type is EntityType.ADDRESS for d in detections)
    result = pseudonymize(text, detections)
    lowered = replace(strict, threshold=check_threshold(strict.threshold))
    found = final_check(result, lambda neutral: detect(neutral, lowered))
    assert any(d.entity_type is EntityType.ADDRESS for d in found)
    assert all("[" not in d.text for d in found)
