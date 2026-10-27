"""Tests de detection.merge : une fonction par règle, sur des détections construites à la main."""

import random

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.merge import check_output, crossing_spans, merge, priority
from huisclos.models import DEFAULT_ENABLED_TYPES, Detection, EntityType, Source

CONFIG = DetectionConfig(threshold=0.40)


def det(
    text: str,
    fragment: str,
    entity_type: EntityType,
    score: float = 0.85,
    source: Source = Source.NER_SPACY,
    occurrence: int = 0,
) -> Detection:
    """Construit une détection sur la n-ième occurrence de fragment dans text."""
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(fragment, start + 1)
    end = start + len(fragment)
    return Detection(start, end, entity_type, score, source, text[start:end])


def texts(detections: list[Detection]) -> list[tuple[str, EntityType]]:
    """Résumé lisible d'une liste de détections : (texte, type)."""
    return [(d.text, d.entity_type) for d in detections]


# Règle 1 : rognage.


def test_rule1_trims_borders_and_civility() -> None:
    text = "Selon M. Dupont, rien."
    raw = [det(text, " M. Dupont,", EntityType.PERSON)]
    assert texts(merge(text, raw, CONFIG)) == [("Dupont", EntityType.PERSON)]


def test_rule1_removes_bare_civility_and_cuts_at_line_break() -> None:
    text = "Claire Fontaine\nAvocate\n\nMadame,"
    raw = [
        det(text, "Claire Fontaine\nAvocate", EntityType.PERSON),
        det(text, "Madame", EntityType.PERSON),
    ]
    assert texts(merge(text, raw, CONFIG)) == [("Claire Fontaine", EntityType.PERSON)]


def test_rule1_keeps_civility_inside_organization() -> None:
    text = "Le cabinet Maître Conseil SAS."
    raw = [det(text, "Maître Conseil SAS", EntityType.ORGANIZATION)]
    assert texts(merge(text, raw, CONFIG)) == [("Maître Conseil SAS", EntityType.ORGANIZATION)]


# Règle 2 : types activés.


def test_rule2_drops_disabled_types() -> None:
    text = "Rendez-vous à Lyon avec Paul Martin."
    raw = [det(text, "Lyon", EntityType.LOCATION), det(text, "Paul Martin", EntityType.PERSON)]
    assert texts(merge(text, raw, CONFIG)) == [("Paul Martin", EntityType.PERSON)]
    with_places = DetectionConfig(
        threshold=0.40, enabled_types=DEFAULT_ENABLED_TYPES | {EntityType.LOCATION}
    )
    assert len(merge(text, raw, with_places)) == 2


# Règle 3 : exclusions.


def test_rule3_removes_names_inside_excluded_spans_only() -> None:
    text = "Conseil de prud'hommes de Nanterre, Paul Martin, a@example.com"
    court = (0, len("Conseil de prud'hommes de Nanterre"))
    email_span = (text.index("a@"), len(text))
    raw = [
        det(text, "Nanterre", EntityType.ORGANIZATION),
        det(text, "Nanterre, Paul Martin", EntityType.PERSON, score=0.6),
        det(text, "a@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
        det(text, "Conseil", EntityType.PERSON, 1.0, Source.MANUAL),
    ]
    result = texts(merge(text, raw, CONFIG, [court, email_span]))
    assert ("Nanterre", EntityType.ORGANIZATION) not in result
    assert ("Paul Martin", EntityType.PERSON) in result
    assert ("a@example.com", EntityType.EMAIL) in result
    assert ("Conseil", EntityType.PERSON) in result
    no_exclusion = DetectionConfig(threshold=0.40, use_exclusions=False)
    kept = texts(merge(text, raw[:1], no_exclusion, [court]))
    assert kept == [("Nanterre", EntityType.ORGANIZATION)]


# Règle 4 : requalification en société.


@pytest.mark.parametrize(
    ("text", "fragment", "expected"),
    [
        (
            "Contrat avec Garnier Logistique SARL signé.",
            "Garnier Logistique",
            "Garnier Logistique SARL",
        ),
        ("Contrat avec la SARL Garnier signé.", "Garnier", "SARL Garnier"),
        ("Contrat avec la société Martin signé.", "Martin", "Martin"),
        ("Avis du cabinet Lefort reçu.", "Lefort", "Lefort"),
        ("Le Groupe Bernard investit.", "Bernard", "Bernard"),
    ],
)
def test_rule4_requalifies_person_as_organization(text: str, fragment: str, expected: str) -> None:
    result = merge(text, [det(text, fragment, EntityType.PERSON)], CONFIG)
    assert texts(result) == [(expected, EntityType.ORGANIZATION)]


def test_rule4_ignores_possessive_sa_and_plain_names() -> None:
    text = "Paul Martin sa voiture. Jean Petit arrive."
    raw = [det(text, "Paul Martin", EntityType.PERSON), det(text, "Jean Petit", EntityType.PERSON)]
    assert {t for _, t in texts(merge(text, raw, CONFIG))} == {EntityType.PERSON}


# Règle 5 : chevauchements.


def test_rule5_same_type_union_keeps_max_score() -> None:
    text = "Monsieur Jean DUPONT LEROY est venu."
    raw = [
        det(text, "Jean DUPONT", EntityType.PERSON, 0.70, Source.HEURISTIC),
        det(text, "DUPONT LEROY", EntityType.PERSON, 0.85),
    ]
    result = merge(text, raw, CONFIG)
    assert texts(result) == [("Jean DUPONT LEROY", EntityType.PERSON)]
    assert result[0].score == 0.85


def test_rule5_enclosing_span_wins_when_at_least_as_important() -> None:
    text = "Facture de Garnier Logistique SARL."
    raw = [
        det(text, "Garnier Logistique SARL", EntityType.ORGANIZATION),
        det(text, "Garnier", EntityType.PERSON, 0.90),
    ]
    assert texts(merge(text, raw, CONFIG)) == [("Garnier Logistique SARL", EntityType.ORGANIZATION)]


def test_rule5_more_important_inner_span_cuts_the_enclosing_one() -> None:
    text = "Écrire à Paul Martin jean@example.com demain."
    raw = [
        det(text, "Paul Martin jean@example.com", EntityType.PERSON),
        det(text, "jean@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
    ]
    result = texts(merge(text, raw, CONFIG))
    assert result == [("Paul Martin", EntityType.PERSON), ("jean@example.com", EntityType.EMAIL)]


def test_rule5_enclosing_span_removed_when_free_part_is_too_short() -> None:
    text = "Voir A jean@example.com demain."
    raw = [
        det(text, "A jean@example.com", EntityType.PERSON),
        det(text, "jean@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
    ]
    assert texts(merge(text, raw, CONFIG)) == [("jean@example.com", EntityType.EMAIL)]


def test_rule5_partial_overlap_resolved_by_priority() -> None:
    text = "Siège : Paul Martin 14 rue des Lilas 75011 Paris."
    raw = [
        det(text, "Paul Martin 14", EntityType.PERSON, 0.90),
        det(text, "14 rue des Lilas 75011 Paris", EntityType.ADDRESS, 0.70, Source.PATTERN),
    ]
    result = texts(merge(text, raw, CONFIG))
    assert result == [
        ("Paul Martin", EntityType.PERSON),
        ("14 rue des Lilas 75011 Paris", EntityType.ADDRESS),
    ]
    # Le type prime sur le score : une personne à 0,70 l'emporte sur un CUSTOM à 0,95.
    names = "Paul Martin Durand"
    raw = [det(names, "Paul Martin", EntityType.PERSON, 0.70, Source.HEURISTIC)]
    raw.append(det(names, "Martin Durand", EntityType.CUSTOM, 0.95, Source.PATTERN))
    assert texts(merge(names, raw, CONFIG)) == [
        ("Paul Martin", EntityType.PERSON),
        ("Durand", EntityType.CUSTOM),
    ]


def test_rule5_manual_detection_beats_every_type() -> None:
    text = "IBAN FR76 3000 6000 0112 3456 7890 189"
    iban = det(text, "FR76 3000 6000 0112 3456 7890 189", EntityType.IBAN, 1.0, Source.CHECKSUM)
    manual = det(text, "IBAN FR76", EntityType.CUSTOM, 1.0, Source.MANUAL)
    assert priority(manual) < priority(iban)
    result = texts(merge(text, [iban, manual], CONFIG))
    assert result[0] == ("IBAN FR76", EntityType.CUSTOM)
    assert result[1] == ("3000 6000 0112 3456 7890 189", EntityType.IBAN)


# Règle 6 : adjacence.


def test_rule6_joins_adjacent_persons_and_address_lines() -> None:
    text = "Jean DUPONT et Anne-Marie\n12 rue Haute,\n75001 Paris"
    raw = [
        det(text, "Jean", EntityType.PERSON, 0.70),
        det(text, "DUPONT", EntityType.PERSON, 0.85),
        det(text, "Anne", EntityType.PERSON),
        det(text, "Marie", EntityType.PERSON),
        det(text, "12 rue Haute", EntityType.ADDRESS, 0.55, Source.PATTERN),
        det(text, "75001 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN),
    ]
    result = merge(text, raw, CONFIG)
    assert texts(result) == [
        ("Jean DUPONT", EntityType.PERSON),
        ("Anne-Marie", EntityType.PERSON),
        ("12 rue Haute,\n75001 Paris", EntityType.ADDRESS),
    ]
    assert result[0].score == 0.85


def test_rule6_does_not_join_across_other_separators() -> None:
    text = "Jean, DUPONT\n\n12 rue Haute\n\n75001 Paris"
    raw = [
        det(text, "Jean", EntityType.PERSON),
        det(text, "DUPONT", EntityType.PERSON),
        det(text, "12 rue Haute", EntityType.ADDRESS, 0.55, Source.PATTERN),
        det(text, "75001 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN),
    ]
    assert len(merge(text, raw, CONFIG)) == 4


# Règle 7 : seuil.


def test_rule7_threshold_is_inclusive() -> None:
    text = "Paul Martin et Anne Morel"
    raw = [
        det(text, "Paul Martin", EntityType.PERSON, 0.40, Source.HEURISTIC),
        det(text, "Anne Morel", EntityType.PERSON, 0.39, Source.HEURISTIC),
    ]
    assert texts(merge(text, raw, CONFIG)) == [("Paul Martin", EntityType.PERSON)]
    strict = DetectionConfig(threshold=0.9)
    assert merge(text, raw, strict) == []


# Règle 8 : sortie triée, sans chevauchement, texte exact.


def test_rule8_output_sorted_without_overlap_and_exact_text() -> None:
    text = "Paul Martin, 06 12 34 56 78, Paul Martin"
    raw = [
        det(text, "Martin", EntityType.PERSON, occurrence=1),
        det(text, "06 12 34 56 78", EntityType.PHONE, 0.75, Source.PATTERN),
        det(text, "Paul Martin, 06", EntityType.PERSON),
    ]
    result = merge(text, raw, CONFIG)
    assert [d.start for d in result] == sorted(d.start for d in result)
    check_output(text, result)
    assert all(d.text == text[d.start : d.end] for d in result)
    overlapping = [raw[2], raw[1]]
    with pytest.raises(AssertionError):
        check_output(text, sorted(overlapping, key=lambda d: d.start))


def test_result_does_not_depend_on_input_order() -> None:
    text = "M. Jean DUPONT, Garnier SARL, jean@example.com, 12 rue Haute\n75001 Paris, Jean"
    raw = [
        det(text, "M. Jean", EntityType.PERSON, 0.80, Source.HEURISTIC),
        det(text, "Jean DUPONT", EntityType.PERSON, 0.70, Source.HEURISTIC),
        det(text, "DUPONT, Garnier", EntityType.PERSON),
        det(text, "Garnier", EntityType.ORGANIZATION),
        det(text, "jean@example.com, 12", EntityType.PERSON),
        det(text, "jean@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
        det(text, "12 rue Haute", EntityType.ADDRESS, 0.55, Source.PATTERN),
        det(text, "75001 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN),
        det(text, "Jean", EntityType.PERSON, occurrence=1),
    ]
    reference = merge(text, raw, CONFIG)
    rng = random.Random(13)
    for _ in range(30):
        shuffled = list(raw)
        rng.shuffle(shuffled)
        assert merge(text, shuffled, CONFIG) == reference


def test_all_sensitive_parts_survive_an_inner_identifier() -> None:
    """Les deux parties d'un nom englobant un identifiant restent couvertes."""
    text = "Paul Martin jean@example.test Marie Durand"
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, "jean@example.test", EntityType.EMAIL, 0.95, Source.PATTERN),
    ]
    result = merge(text, raw, CONFIG)
    assert texts(result) == [
        ("Paul Martin", EntityType.PERSON),
        ("jean@example.test", EntityType.EMAIL),
        ("Marie Durand", EntityType.PERSON),
    ]


def test_requalified_organization_respects_disabled_types() -> None:
    """Une société reste désactivée même si sa source la classe comme personne."""
    text = "Paul SARL"
    config = DetectionConfig(enabled_types=frozenset({EntityType.PERSON}), threshold=0.40)
    assert merge(text, [det(text, "Paul", EntityType.PERSON)], config) == []


def test_joined_full_address_gets_d07_score() -> None:
    """Une voie et un code postal réunis valent 0,70 selon D-07."""
    text = "12 rue Haute,\n75001 Paris"
    raw = [
        det(text, "12 rue Haute", EntityType.ADDRESS, 0.55, Source.PATTERN),
        det(text, "75001 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN),
    ]
    result = merge(text, raw, CONFIG)
    assert len(result) == 1 and result[0].text == text
    assert result[0].score == 0.70


def test_exclusion_inside_a_name_does_not_split_it() -> None:
    """Une forme juridique exclue seule reste dans le span de sa société (D-09)."""
    text = "Garnier Logistique SARL paie."
    sarl = (text.index("SARL"), text.index("SARL") + 4)
    raw = [det(text, "Garnier Logistique SARL", EntityType.ORGANIZATION)]
    assert texts(merge(text, raw, CONFIG, [sarl])) == [
        ("Garnier Logistique SARL", EntityType.ORGANIZATION)
    ]
    assert crossing_spans(5, 10, [(0, 7), (6, 8), (10, 12)]) == [(0, 7)]
