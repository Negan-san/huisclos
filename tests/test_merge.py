"""Tests de detection.merge : une fonction par règle, sur des détections construites à la main."""

import random
import re

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


def test_exclusions_also_apply_to_fragments_left_by_a_structured_value() -> None:
    """Le retrait d'une coordonnée ne doit pas laisser un libellé classé comme nom."""
    text = "Courriel testeur@example.org"
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, "testeur@example.org", EntityType.EMAIL, 0.95, Source.PATTERN),
    ]
    assert texts(merge(text, raw, CONFIG, [(0, 8)])) == [("testeur@example.org", EntityType.EMAIL)]


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
    # Un identifiant explicitement libellé prime sur une interprétation comme nom.
    names = "Paul Martin Durand"
    raw = [det(names, "Paul Martin", EntityType.PERSON, 0.70, Source.HEURISTIC)]
    raw.append(det(names, "Martin Durand", EntityType.CUSTOM, 0.95, Source.PATTERN))
    assert texts(merge(names, raw, CONFIG)) == [
        ("Paul", EntityType.PERSON),
        ("Martin Durand", EntityType.CUSTOM),
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
    text = "Paul Martin jean@example.com Marie Durand"
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, "jean@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
    ]
    result = merge(text, raw, CONFIG)
    assert texts(result) == [
        ("Paul Martin", EntityType.PERSON),
        ("jean@example.com", EntityType.EMAIL),
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


@pytest.mark.parametrize(
    "reference",
    ["Cour de cassation", "article L. 1232-6 du Code du travail"],
)
def test_enclosed_legal_reference_is_not_masked(reference: str) -> None:
    """Une référence juridique incluse dans un span NER reste lisible, sans perdre les noms."""
    text = f"Paul Martin {reference} Marie Durand"
    start = text.index(reference)
    end = start + len(reference)
    raw = [det(text, text, EntityType.PERSON)]
    result = merge(text, raw, CONFIG, [(start, end)])
    assert texts(result) == [
        ("Paul Martin", EntityType.PERSON),
        ("Marie Durand", EntityType.PERSON),
    ]
    assert not any(d.start < end and start < d.end for d in result)


def test_merge_keeps_two_companies_joined_by_a_conjunction() -> None:
    """La fusion seule ne réunit jamais "A SARL et B SAS" : ce sont deux sociétés."""
    text = "Halbarde SARL et Vasquelin SAS"
    raw = [
        det(text, "Halbarde SARL", EntityType.ORGANIZATION),
        det(text, "Vasquelin SAS", EntityType.ORGANIZATION),
    ]
    result = merge(text, raw, CONFIG)
    assert [d.text for d in result] == ["Halbarde SARL", "Vasquelin SAS"]


# Arbitrage et seuil (D-AF-A1-1) : un candidat sous le seuil ne retire aucune protection.

LOW = DetectionConfig(threshold=0.30, use_exclusions=False)


def covered(detections: list[Detection]) -> set[int]:
    """Positions des caractères couverts par au moins une détection."""
    return {index for d in detections for index in range(d.start, d.end)}


def visible(text: str) -> set[int]:
    """Positions des caractères autres que les blancs : celles qu'un masque doit couvrir."""
    return {index for index, char in enumerate(text) if not char.isspace()}


def test_inadmissible_candidate_does_not_cut_an_admissible_name() -> None:
    """Reproduction G7 : ORGANIZATION à 0,10 rognait PERSON avant d'être écartée."""
    text = "Paul Martin"
    person = Detection(0, 11, EntityType.PERSON, 0.85, Source.NER_SPACY, text)
    weak = Detection(0, 4, EntityType.ORGANIZATION, 0.10, Source.NER_CAMEMBERT, "Paul")
    alone = merge(text, [person], LOW)
    assert len(covered(alone)) == 11
    both = merge(text, [person, weak], LOW)
    assert covered(both) == covered(alone)
    assert texts(both) == [("Paul Martin", EntityType.PERSON)]


@pytest.mark.parametrize("weak_type", [EntityType.ORGANIZATION, EntityType.ADDRESS])
@pytest.mark.parametrize(
    "fragment", ["Paul", "Martin", "Paul Martin", "Paul Martin Lefort", "Dr Paul", "Martin Lefort"]
)
def test_weak_overlap_keeps_every_protected_character(weak_type: EntityType, fragment: str) -> None:
    """Contenu, englobant, chevauchement à gauche ou à droite : la couverture ne baisse pas."""
    text = "Avis du Dr Paul Martin Lefort reçu."
    person = det(text, "Paul Martin", EntityType.PERSON)
    weak = det(text, fragment, weak_type, 0.10, Source.NER_CAMEMBERT)
    result = merge(text, [weak, person], LOW)
    assert covered(result) >= set(range(person.start, person.end))
    assert covered(result) == covered(merge(text, [person], LOW))
    check_output(text, result)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.29, [("Paul Martin", EntityType.PERSON)]),
        (0.30, [("Paul", EntityType.ORGANIZATION), ("Martin", EntityType.PERSON)]),
        (0.31, [("Paul", EntityType.ORGANIZATION), ("Martin", EntityType.PERSON)]),
    ],
)
def test_threshold_boundary_keeps_type_priority(score: float, expected: list[tuple]) -> None:
    """Sous le seuil, le candidat passe après ; au seuil ou au-dessus, la priorité joue."""
    text = "Paul Martin"
    raw = [det(text, text, EntityType.PERSON), det(text, "Paul", EntityType.ORGANIZATION, score)]
    result = merge(text, raw, LOW)
    assert texts(result) == expected
    assert covered(result) >= visible(text)


def test_full_address_aggregation_survives_a_weak_identifier() -> None:
    """La voie et la ligne postale, chacune sous le seuil, forment encore l'adresse à 0,70."""
    text = "Siège : 12 rue Haute 75011 Paris."
    config = DetectionConfig(threshold=0.60, use_exclusions=False)
    street = det(text, "12 rue Haute", EntityType.ADDRESS, 0.55, Source.PATTERN)
    postal = det(text, "75011 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN)
    weak = det(text, "75011", EntityType.PHONE, 0.10, Source.PATTERN)
    for raw in ([street, postal], [street, postal, weak], [weak, postal, street]):
        result = merge(text, raw, config)
        assert texts(result) == [("12 rue Haute 75011 Paris", EntityType.ADDRESS)]
        assert result[0].score == 0.70


def test_weak_case_number_does_not_split_an_admissible_address() -> None:
    """Un numéro de dossier écarté par le seuil ne laisse pas le code postal en clair."""
    text = "Domicile : 14 rue des Lilas 75011 Paris."
    address = det(text, "14 rue des Lilas 75011 Paris", EntityType.ADDRESS, 0.70, Source.PATTERN)
    weak = det(text, "75011", EntityType.CASE_NUMBER, 0.20, Source.PATTERN)
    assert texts(merge(text, [address, weak], LOW)) == [(address.text, EntityType.ADDRESS)]


def test_unjoined_street_stops_blocking_a_name() -> None:
    """Une voie admise pour sa jonction, privée de son code postal par un ajout manuel,
    ne masque plus le nom qu'elle contenait ; la borne manuelle est conservée."""
    text = "Au 12 rue Victor Hugo 75011 Paris."
    config = DetectionConfig(threshold=0.60, use_exclusions=False)
    raw = [
        det(text, "12 rue Victor Hugo", EntityType.ADDRESS, 0.55, Source.PATTERN),
        det(text, "75011 Paris", EntityType.ADDRESS, 0.45, Source.PATTERN),
        det(text, "Victor Hugo", EntityType.PERSON),
        det(text, "75011", EntityType.CUSTOM, 1.0, Source.MANUAL),
    ]
    assert texts(merge(text, raw, config)) == [
        ("Victor Hugo", EntityType.PERSON),
        ("75011", EntityType.CUSTOM),
    ]


@pytest.mark.parametrize(("threshold", "split"), [(0.50, False), (0.40, True)])
def test_names_around_an_iban_with_a_wrong_key(threshold: float, split: bool) -> None:
    """IBAN à clé fausse (0,40) dans un span NER : sous le seuil, il reste masqué en nom."""
    iban = "FR76 3000 6000 0112 3456 7890 180"
    text = f"Paul Martin {iban} Marie Durand"
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, iban, EntityType.IBAN, 0.40, Source.PATTERN),
    ]
    config = DetectionConfig(threshold=threshold, use_exclusions=False)
    result = merge(text, raw, config)
    assert covered(result) >= visible(text)
    expected = [("Paul Martin", EntityType.PERSON), (iban, EntityType.IBAN)]
    expected.append(("Marie Durand", EntityType.PERSON))
    assert texts(result) == (expected if split else [(text, EntityType.PERSON)])


def test_names_around_an_email_ignore_a_weak_company() -> None:
    """Les deux noms autour d'un e-mail restent entiers malgré une société à 0,10."""
    text = "Paul Martin jean@example.com Marie Durand"
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, "jean@example.com", EntityType.EMAIL, 0.95, Source.PATTERN),
        det(text, "Marie", EntityType.ORGANIZATION, 0.10, Source.NER_CAMEMBERT),
    ]
    assert texts(merge(text, raw, LOW)) == [
        ("Paul Martin", EntityType.PERSON),
        ("jean@example.com", EntityType.EMAIL),
        ("Marie Durand", EntityType.PERSON),
    ]


def test_nearby_legal_reference_stays_readable_with_weak_candidates() -> None:
    """Une juridiction voisine reste lisible ; un candidat faible ne la fait pas masquer."""
    text = "Paul Martin Cour de cassation Marie Durand"
    court = (text.index("Cour"), text.index(" Marie"))
    raw = [
        det(text, text, EntityType.PERSON),
        det(text, "Martin Cour", EntityType.ORGANIZATION, 0.10, Source.NER_CAMEMBERT),
        det(text, "Cour de cassation", EntityType.ADDRESS, 0.10, Source.NER_CAMEMBERT),
    ]
    config = DetectionConfig(threshold=0.30)
    result = merge(text, raw, config, [court])
    assert texts(result) == [
        ("Paul Martin", EntityType.PERSON),
        ("Marie Durand", EntityType.PERSON),
    ]


WORDS = "Paul Martin Anne Morel 75011 Paris Jean Petit Lyon Marie Durand Rose Blanc"
KINDS = [EntityType.PERSON, EntityType.ORGANIZATION, EntityType.ADDRESS, EntityType.PHONE]


def random_candidates(rng: random.Random, low: float, high: float) -> list[Detection]:
    """Tire de un à quatre candidats alignés sur les mots de WORDS, scores dans [low, high]."""
    bounds = [(m.start(), m.end()) for m in re.finditer(r"\S+", WORDS)]
    candidates = []
    for _ in range(rng.randint(1, 4)):
        first = rng.randrange(len(bounds))
        last = min(len(bounds) - 1, first + rng.randrange(3))
        start, end = bounds[first][0], bounds[last][1]
        score = round(rng.uniform(low, high), 2)
        candidates.append(
            Detection(start, end, rng.choice(KINDS), score, Source.NER_SPACY, WORDS[start:end])
        )
    return candidates


def test_weak_candidates_never_reduce_coverage_randomly() -> None:
    """Propriété sur 400 tirages : ajouter des candidats sous le seuil ne découvre aucun
    caractère visible, quel que soit l'ordre d'arrivée, sans chevauchement et avec un texte
    exact. Un candidat faible joint à une adresse admissible peut prendre un mot à un nom
    moins prioritaire : seul l'espace qui les sépare change alors de couverture."""
    rng = random.Random(41)
    for _ in range(400):
        strong = random_candidates(rng, 0.30, 1.0)
        weak = random_candidates(rng, 0.0, 0.29)
        reference = merge(WORDS, strong, LOW)
        result = merge(WORDS, strong + weak, LOW)
        assert covered(result) >= covered(reference) & visible(WORDS), (strong, weak)
        shuffled = strong + weak
        rng.shuffle(shuffled)
        assert merge(WORDS, shuffled, LOW) == result
        check_output(WORDS, result)
