"""Tests de detection.organization_bounds : extension, ancrage et fusion des sociétés.

Les noms de sociétés et de personnes sont inventés et absents du corpus.
"""

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.exclusions import load_exclusions
from huisclos.detection.merge import check_output
from huisclos.detection.organization_bounds import (
    adjust_organizations,
    extended_bounds,
    fuse_organizations,
    merge_civility_names,
)
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Source

CONFIG = DetectionConfig(threshold=0.40)
ORG, PERSON = EntityType.ORGANIZATION, EntityType.PERSON


def det(text: str, fragment: str, entity_type: EntityType = ORG, score: float = 0.85) -> Detection:
    """Détection sur la première occurrence de fragment."""
    start = text.index(fragment)
    return Detection(start, start + len(fragment), entity_type, score, Source.NER_SPACY, fragment)


def extended(text: str, fragment: str) -> str:
    """Texte couvert par extended_bounds à partir de fragment, exclusions comprises."""
    start = text.index(fragment)
    spans = load_exclusions().spans(text)
    new_start, new_end = extended_bounds(text, start, start + len(fragment), spans)
    return text[new_start:new_end]


def adjusted(text: str, detections: list[Detection], config: DetectionConfig = CONFIG) -> list:
    """Applique adjust_organizations, vérifie positions et chevauchements, renvoie (texte, type)."""
    result = adjust_organizations(text, detections, config, load_exclusions().spans(text))
    check_output(text, result)
    return [(d.text, d.entity_type) for d in result]


@pytest.mark.parametrize(
    ("text", "fragment", "expected"),
    [
        (
            "Contrat avec Verrerie Halbarde du Quint SARL.",
            "Quint SARL",
            "Verrerie Halbarde du Quint SARL",
        ),
        ("Employeur : Brasserie Quintelor SARL", "Quintelor SARL", "Brasserie Quintelor SARL"),
        ("travaille chez Comptoir des Ozanes SAS.", "Ozanes SAS", "Comptoir des Ozanes SAS"),
        ("Note\nTuilerie Morvane SAS", "Morvane SAS", "Tuilerie Morvane SAS"),
        ("Courrier du Dr Quintelor SARL", "Quintelor SARL", "Quintelor SARL"),
        ("contrat avec Paul Halbarde, Corbaline SAS", "Corbaline SAS", "Corbaline SAS"),
        ("la société Corbaline Ozanes SAS", "Ozanes SAS", "Corbaline Ozanes SAS"),
        ("Destinataire Corbaline SAS", "Corbaline SAS", "Corbaline SAS"),
        ("paiement de La Verrerie Halbarde SARL", "Halbarde SARL", "Verrerie Halbarde SARL"),
        ("Contre Verrerie Halbarde SARL", "Halbarde SARL", "Verrerie Halbarde SARL"),
        ("Halbarde SARL et Vasquelin SAS", "Vasquelin SAS", "Vasquelin SAS"),
        ("la SAS Corbaline Vasquelin, siège", "SAS Corbaline", "SAS Corbaline Vasquelin"),
        (
            "Un Deux Trois Quatre Cinq Six Sept Huit SA",
            "Huit SA",
            "Deux Trois Quatre Cinq Six Sept Huit SA",
        ),
        ("au capital de 5 000 Halbarde SARL", "Halbarde SARL", "Halbarde SARL"),
    ],
)
def test_extension_rules(text: str, fragment: str, expected: str) -> None:
    """Extension à gauche, ou à droite après une forme en tête, et ses arrêts."""
    assert extended(text, fragment) == expected


def test_court_is_never_absorbed() -> None:
    """Une juridiction exclue arrête l'extension, même suivie d'une société."""
    text = "devant le Tribunal judiciaire de Morvane Corbaline SARL"
    assert extended(text, "Corbaline SARL") == "Corbaline SARL"
    assert adjusted(text, []) == [("Corbaline SARL", ORG)]


def test_no_liaison_heads_the_span() -> None:
    """Une liaison n'ouvre jamais le span, même en majuscule ou en tête de ligne."""
    for head in ("De", "Et", "Les", "des"):
        text = f"{head} Halbarde SARL"
        assert adjusted(text, []) == [("Halbarde SARL", ORG)]


def test_two_companies_stay_distinct() -> None:
    """ "A SARL et B SAS" donne deux sociétés, avec ou sans détection préalable."""
    text = "Halbarde SARL et Vasquelin SAS"
    expected = [("Halbarde SARL", ORG), ("Vasquelin SAS", ORG)]
    assert adjusted(text, []) == expected
    detections = [det(text, "Halbarde SARL"), det(text, "Vasquelin SAS")]
    assert adjusted(text, detections) == expected


def test_fragments_fuse_through_a_liaison() -> None:
    """Deux fragments séparés par une liaison deviennent un span, score du plus fort."""
    text = "travaille chez Comptoir des Ozanes SAS."
    detections = [det(text, "Comptoir", score=0.70), det(text, "Ozanes SAS", score=0.85)]
    result = adjust_organizations(text, detections, CONFIG)
    assert [(d.text, d.score) for d in result] == [("Comptoir des Ozanes SAS", 0.85)]
    text = "Durandel et Fils"
    fused = fuse_organizations(text, [det(text, "Durandel"), det(text, "Fils", score=0.9)])
    assert [(d.text, d.score) for d in fused] == [("Durandel et Fils", 0.9)]


def test_extension_absorbs_contained_names_only() -> None:
    """Un nom contenu est absorbé ; un e-mail ou une adresse arrête l'élargissement."""
    text = "Fournitures Petit des Lorvan SAS"
    detections = [det(text, "Petit", PERSON), det(text, "Lorvan SAS")]
    assert adjusted(text, detections) == [("Fournitures Petit des Lorvan SAS", ORG)]
    text = "Lorvan Halbarde SAS"
    manual = Detection(0, 6, PERSON, 1.0, Source.MANUAL, "Lorvan")
    assert adjusted(text, [manual, det(text, "Halbarde SAS")]) == [
        ("Lorvan", PERSON),
        ("Halbarde SAS", ORG),
    ]


def test_anchor_requires_heuristics_and_a_name() -> None:
    """Une forme juridique seule ou une configuration sans heuristique ne crée rien."""
    assert adjusted("la SARL, puis la SAS.", []) == []
    assert adjusted("Foncière Vasquelin SAS", [], DetectionConfig(use_heuristics=False)) == []
    result = adjust_organizations("Foncière Vasquelin SAS", [], CONFIG)
    assert [(d.text, d.source, d.score) for d in result] == [
        ("Foncière Vasquelin SAS", Source.HEURISTIC, 0.70)
    ]


def test_civility_name_becomes_one_person() -> None:
    """Civilité suivie de Prénom NOM : un seul PERSON, qui l'emporte sur la société."""
    text = "Voir M. Lorvan QUINTELOR, salarié."
    detections = [det(text, "Lorvan", PERSON, 0.70), det(text, "QUINTELOR", ORG, 0.85)]
    result = merge_civility_names(text, detections)
    assert [(d.text, d.entity_type, d.score) for d in result] == [
        ("Lorvan QUINTELOR", PERSON, 0.85)
    ]
    text = "Me Vasquelin.\n"
    assert adjusted(text, [det(text, "Me Vasquelin", ORG)]) == [("Vasquelin", PERSON)]


def test_civility_before_a_company_keeps_the_company() -> None:
    """ "M. Halbarde SARL" reste une société ; un PERSON seul n'est pas modifié."""
    text = "Courrier de M. Halbarde SARL."
    assert adjusted(text, [det(text, "Halbarde SARL")]) == [("Halbarde SARL", ORG)]
    text = "Mme Corbaline signe."
    person = det(text, "Corbaline", PERSON)
    assert merge_civility_names(text, [person]) == [person]


def test_letter_headings_are_excluded_at_line_start_only() -> None:
    """Les intitulés de lettre sont exclus en tête de ligne, pas dans un nom."""
    text = "Bonjour.\nVeuillez agréer.\nCopie : x\nImprimerie Lettre Vive SARL"
    spans = load_exclusions().spans(text)
    excluded = [text[start:end] for start, end in spans]
    assert "Veuillez" in excluded and "Copie" in excluded
    assert "Lettre" not in excluded
    assert adjusted(text, []) == [("Imprimerie Lettre Vive SARL", ORG)]


def test_full_pipeline_keeps_exact_positions(no_network: None) -> None:
    """Le pipeline complet étend la société et garde Detection.text == texte[start:end]."""
    text = "Expéditeur : Ateliers Vermandel des Ozanes SARL, 3 rue des Ormes 75011 Paris."
    result = detect(text)
    check_output(text, result)
    companies = [d.text for d in result if d.entity_type == ORG]
    assert companies == ["Ateliers Vermandel des Ozanes SARL"]
