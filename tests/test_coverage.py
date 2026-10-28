"""Vérifie la couverture complète sur de petits exemples fictifs calculables à la main.

Entrées : textes courts inventés, annotations et passages masqués écrits à la main.
Sorties : assertions sur les expositions, la fuite, le surmasquage et les alertes.
Place dans le pipeline : validation du calcul pur de evaluation.coverage, sans modèle.
"""

import pytest

from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.evaluation.coverage import (
    SCOPES,
    CoverageCounts,
    detection_spans,
    document_alerts,
    document_coverage,
    exposure_rows,
    merge_spans,
    original_position,
    substituted_spans,
    sum_counts,
)
from huisclos.evaluation.metrics import Evaluation, uncovered_characters
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.final_check import source_span
from huisclos.pseudonymize.tokens import pseudonymize

# "Léa Morvan" occupe les caractères 0 à 10 ; " signe." donne sept caractères non sensibles.
PERSON_TEXT = "Léa Morvan signe."
# L'adresse occupe 11 à 38 ; la rue seule 11 à 27 ; " 69007 Lyon" fait onze caractères.
ADDRESS_TEXT = "Domicile : 12 rue des Lilas 69007 Lyon."


def gold(text: str, value: str, kind: str = "PERSON") -> GoldEntity:
    """Annote la première occurrence de value dans text."""
    start = text.index(value)
    return GoldEntity(start, start + len(value), EntityType(kind), value)


def detection(text: str, value: str, kind: str = "PERSON") -> Detection:
    """Construit une prédiction fictive sur la première occurrence de value."""
    start = text.index(value)
    return Detection(start, start + len(value), EntityType(kind), 0.9, Source.MANUAL, value)


def coverage(text: str, references: list[GoldEntity], masked: list[tuple[int, int]]) -> dict:
    """Renvoie les scores de couverture du périmètre des onze types évalués."""
    return document_coverage(len(text), references, masked).scores()


def micro(evaluation: Evaluation, mode: str = "partial") -> dict:
    """Extrait la ligne micro du mode demandé."""
    return next(row for row in evaluation.rows() if row["mode"] == mode and row["type"] == "micro")


def test_first_name_masked_surname_visible_is_partial_exposure() -> None:
    """Le prénom seul masqué laisse sept caractères visibles malgré un rappel partiel de 1."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    scores = coverage(PERSON_TEXT, [reference], [(0, 3)])
    assert scores["entities_fully_covered"] == 0
    assert scores["entities_partially_exposed"] == 1
    assert scores["entities_fully_exposed"] == 0
    assert scores["entities_with_any_exposure"] == 1
    assert scores["full_coverage_rate"] == 0.0
    assert scores["leaked_characters"] == 7
    assert scores["leaked_character_rate"] == pytest.approx(0.7)
    assert scores["documents_with_any_exposure"] == 1
    assert scores["non_sensitive_characters"] == 7
    assert scores["non_sensitive_characters_masked"] == 0
    evaluation = Evaluation()
    evaluation.add_document([reference], [detection(PERSON_TEXT, "Léa")])
    assert micro(evaluation)["recall"] == 1.0
    assert micro(evaluation)["exposed_entities"] == 0


def test_city_left_visible_is_partial_exposure() -> None:
    """La rue masquée sans la ville laisse " 69007 Lyon" visible : onze caractères."""
    reference = gold(ADDRESS_TEXT, "12 rue des Lilas 69007 Lyon", "ADDRESS")
    street = detection(ADDRESS_TEXT, "12 rue des Lilas", "ADDRESS")
    scores = coverage(ADDRESS_TEXT, [reference], detection_spans([street]))
    assert (reference.start, reference.end, street.end) == (11, 38, 27)
    assert scores["entities_partially_exposed"] == 1
    assert scores["leaked_characters"] == 11
    assert scores["leaked_character_rate"] == pytest.approx(11 / 27)
    assert scores["full_coverage_rate"] == 0.0


def test_wrong_label_covers_without_true_positive() -> None:
    """Une étiquette erronée masque tout, mais ne devient pas un vrai positif historique."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    wrong = detection(PERSON_TEXT, "Léa Morvan", "ORGANIZATION")
    scores = coverage(PERSON_TEXT, [reference], detection_spans([wrong]))
    assert scores["entities_fully_covered"] == 1
    assert scores["leaked_characters"] == 0
    evaluation = Evaluation()
    evaluation.add_document([reference], [wrong])
    for mode in ("exact", "partial"):
        row = micro(evaluation, mode)
        assert (row["tp"], row["fp"], row["fn"]) == (0, 1, 1)


def test_complementary_spans_cover_entirely() -> None:
    """Deux passages contigus, "Léa" puis " Morvan", couvrent l'entité entière."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    parts = [detection(PERSON_TEXT, "Léa"), detection(PERSON_TEXT, " Morvan")]
    assert detection_spans(parts) == [(0, 10)]
    scores = coverage(PERSON_TEXT, [reference], [(0, 3), (3, 10)])
    assert scores["entities_fully_covered"] == 1
    assert scores["full_coverage_rate"] == 1.0
    assert scores["leaked_characters"] == 0
    assert scores["documents_with_any_exposure"] == 0


def test_intersections_are_counted_once() -> None:
    """Les recouvrements se réunissent : (0, 12) masque l'entité et deux caractères en plus."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    masked = [(0, 6), (4, 10), (2, 12)]
    assert merge_spans(masked) == [(0, 12)]
    scores = coverage(PERSON_TEXT, [reference], masked)
    assert scores["entities_fully_covered"] == 1
    assert scores["non_sensitive_characters_masked"] == 2
    assert scores["non_sensitive_masked_rate"] == pytest.approx(2 / 7)


def test_document_without_annotation_is_not_applicable() -> None:
    """Sans annotation, les ratios de couverture n'ont pas de base : None, jamais un succès."""
    text = "Rien à signaler."
    scores = coverage(text, [], [])
    assert scores["reference_entities"] == 0
    assert scores["full_coverage_rate"] is None
    assert scores["leaked_character_rate"] is None
    assert scores["leaked_characters"] == 0
    assert scores["documents_with_references"] == 0
    assert scores["documents_with_any_exposure"] == 0
    assert scores["non_sensitive_characters"] == 16
    assert scores["non_sensitive_masked_rate"] == 0.0
    masked = coverage(text, [], [(0, 4)])
    assert masked["non_sensitive_masked_rate"] == pytest.approx(0.25)
    assert masked["full_coverage_rate"] is None


def test_whole_text_masked_shows_over_masking() -> None:
    """Tout masquer annule la fuite mais le surmasquage atteint 100 % des caractères neutres."""
    scores = coverage(PERSON_TEXT, [gold(PERSON_TEXT, "Léa Morvan")], [(0, len(PERSON_TEXT))])
    assert scores["full_coverage_rate"] == 1.0
    assert scores["leaked_characters"] == 0
    assert scores["non_sensitive_characters_masked"] == 7
    assert scores["non_sensitive_masked_rate"] == 1.0


def test_one_visible_character_prevents_full_coverage() -> None:
    """Un seul caractère sensible visible suffit à refuser la couverture intégrale."""
    scores = coverage(PERSON_TEXT, [gold(PERSON_TEXT, "Léa Morvan")], [(0, 9)])
    assert scores["entities_fully_covered"] == 0
    assert scores["entities_partially_exposed"] == 1
    assert scores["leaked_characters"] == 1


def test_sum_recomputes_ratios_from_counts() -> None:
    """Le cumul additionne les comptes : 1 entité couverte sur 4, pas la moyenne 0,5."""
    first = document_coverage(17, [gold(PERSON_TEXT, "Léa Morvan")], [(0, 10)])
    text = "Ana Roc, Ivo Pic et Eva Lin."
    others = [gold(text, name) for name in ("Ana Roc", "Ivo Pic", "Eva Lin")]
    second = document_coverage(len(text), others, [])
    total = sum_counts([first, second], CoverageCounts()).scores()
    assert total["full_coverage_rate"] == pytest.approx(0.25)
    assert total["entities_fully_exposed"] == 3
    assert total["documents_with_any_exposure"] == 1
    assert total["documents"] == 2


def test_custom_scope_is_separate_and_not_over_masking() -> None:
    """CUSTOM sort du dénominateur des onze types ; le masquer n'est pas du surmasquage."""
    text = "Code ZX-81 de Léa Morvan."
    references = [gold(text, "ZX-81", "CUSTOM"), gold(text, "Léa Morvan")]
    masked = [(5, 10), (14, 24)]
    evaluated = document_coverage(len(text), references, masked, SCOPES["evaluated"]).scores()
    separate = document_coverage(len(text), references, masked, SCOPES["custom_location"])
    assert evaluated["reference_entities"] == 1
    assert separate.scores()["reference_entities"] == 1
    assert evaluated["non_sensitive_characters_masked"] == 0
    assert evaluated["non_sensitive_characters"] == len(text) - 15


def test_any_substitution_covers_even_when_history_ignores_its_type() -> None:
    """Un masquage LOCATION protège ; la fuite historique, elle, ignore toujours ce type."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    place = detection(PERSON_TEXT, "Léa Morvan", "LOCATION")
    assert coverage(PERSON_TEXT, [reference], detection_spans([place]))["leaked_characters"] == 0
    assert uncovered_characters(reference, [place]) == 10


def test_invalid_spans_are_refused() -> None:
    """Passage vide ou négatif, masque ou annotation au-delà du texte : refus explicite."""
    for spans in ([(3, 3)], [(-1, 2)]):
        with pytest.raises(ValueError):
            merge_spans(spans)
    with pytest.raises(ValueError):
        document_coverage(5, [], [(0, 6)])
    with pytest.raises(ValueError):
        document_coverage(5, [gold(PERSON_TEXT, "Léa Morvan")], [])
    with pytest.raises(ValueError):
        substituted_spans([(0, 0, 3)])


def test_substitutions_map_back_to_original_text() -> None:
    """Les jetons réels se replacent dans l'original, comme final_check.source_span."""
    text = "Maître Léa Morvan écrit à Léa Morvan."
    first = text.index("Léa Morvan")
    second = text.index("Léa Morvan", first + 1)
    detections = [
        Detection(start, start + 10, EntityType.PERSON, 0.9, Source.MANUAL, "Léa Morvan")
        for start in (first, second)
    ]
    result = pseudonymize(text, detections)
    occurrences = [(item.start, item.end, len(item.original)) for item in result.occurrences]
    assert substituted_spans(occurrences) == [(first, first + 10), (second, second + 10)]
    after = result.text.index(" écrit")
    assert original_position(occurrences, after, after + 6) == source_span(result, after, after + 6)
    assert text[slice(*original_position(occurrences, after, after + 6))] == " écrit"


def test_alerts_report_visible_values_without_reducing_leakage() -> None:
    """Une alerte sur "Morvan" signale l'exposition ; la fuite reste de sept caractères."""
    reference = gold(PERSON_TEXT, "Léa Morvan")
    alerted = document_alerts([reference], [(0, 3)], [(4, 10)]).scores()
    assert alerted["alerts_on_visible_references"] == 1
    assert alerted["exposed_entities_alerted"] == 1
    assert alerted["exposed_entities_alerted_rate"] == 1.0
    elsewhere = document_alerts([reference], [(0, 3)], [(11, 16)]).scores()
    assert (elsewhere["alerts_elsewhere"], elsewhere["exposed_entities_alerted"]) == (1, 0)
    assert coverage(PERSON_TEXT, [reference], [(0, 3)])["leaked_characters"] == 7
    quiet = document_alerts([reference], [(0, 10)], []).scores()
    assert quiet["exposed_entities_alerted_rate"] is None


def test_exposure_rows_list_only_visible_evaluated_entities() -> None:
    """Les détails dev donnent le morceau visible ; CUSTOM et les entités couvertes sont omis."""
    text = "Code ZX-81 de Léa Morvan."
    entities = [gold(text, "ZX-81", "CUSTOM"), gold(text, "Léa Morvan")]
    document = CorpusDocument("dev-x", "letter", "dev", "Fiction", text, entities)
    rows = exposure_rows(document, [(14, 17)], None)
    assert rows == [
        {
            "document_id": "dev-x",
            "type": "PERSON",
            "exposure": "partial",
            "reference_text": "Léa Morvan",
            "visible_text": " Morvan",
            "alerted": None,
        }
    ]
    assert exposure_rows(document, [(14, 17)], [(18, 24)])[0]["alerted"] is True
    assert exposure_rows(document, [(14, 24)], []) == []
