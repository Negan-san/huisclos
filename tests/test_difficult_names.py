"""Vérifie les noms complexes sans employer les valeurs du corpus.

Entrées : noms fictifs avec particules, initiales et coupures de ligne.
Sorties : assertions sur les personnes complètes, leur score et les pièges.
Ces tests couvrent les heuristiques et la réparation des fragments du NER.
"""

import pytest

from huisclos.detection.merge import check_output
from huisclos.detection.person_heuristics import CivilityPersonRecognizer
from huisclos.detection.pipeline import detect
from huisclos.models import EntityType


@pytest.mark.parametrize(
    "name",
    [
        "Aveline de La ROCHEMONT",
        "Yvan van der RONCIVAL",
        "Sélène du TORVAN",
        "J.-L. VALCORNE",
        "O'Rivel",
        "N'Derlan",
        "RONCIVAL Anna-Lise",
        "Anna-Lise\nde La ROCHEMONT",
        "Aveline\nN'Derlan",
    ],
)
@pytest.mark.parametrize("title", ["Me", "Maître", "Dr", "Pr", "Mme", "Mlle", "MM."])
def test_complex_civility_name_has_exact_bounds(title: str, name: str) -> None:
    """Une civilité protège le nom complet sans entrer dans le span."""
    text = f"Voir {title} {name}, qui confirme."
    results = CivilityPersonRecognizer().analyze(text, ["PERSON"])
    assert [(text[r.start : r.end], r.score) for r in results] == [(name, 0.8)]


@pytest.mark.parametrize("title", ["M.", "Me", "Dr", "MM."])
@pytest.mark.parametrize("following", ["Le Président", "de stage", "le Directeur", "la Juge"])
def test_professional_title_is_not_a_name(title: str, following: str) -> None:
    """Les titres de fonction ne deviennent pas des noms après une civilité."""
    assert CivilityPersonRecognizer().analyze(f"{title} {following}", ["PERSON"]) == []


@pytest.mark.parametrize(
    "name",
    ["Aveline de La ROCHEMONT", "J.-L. VALCORNE", "Aveline\nN'Derlan", "RONCIVAL Anna-Lise"],
)
def test_hybrid_repairs_split_ner_names(name: str, no_network: None) -> None:
    """Le pipeline rend un seul PERSON exact même si le NER propose des fragments."""
    text = f"Mme {name}, témoin."
    detections = detect(text)
    check_output(text, detections)
    assert [(d.text, d.entity_type) for d in detections] == [(name, EntityType.PERSON)]
