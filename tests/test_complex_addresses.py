"""Vérifie les adresses entières et les pièges avec des lieux inventés.

Entrées : voies, compléments postaux, coupures d'extraction et texte ordinaire.
Sorties : assertions sur le span complet et les scores D-07.
Ces cas isolent le motif d'adresse avant le pipeline hybride.
"""

import pytest

from huisclos.detection.patterns import AddressRecognizer
from huisclos.detection.pipeline import detect
from huisclos.models import EntityType


@pytest.mark.parametrize(
    "address",
    [
        "37 bis rue des Cadrans, BP 287, 48730 Griselune Cedex 09",
        "37 ter venelle des Cadrans\nCS 3847\n97280 Cendreval Cedex",
        "37 rue des Cadrans, résidence des Reflets, bâtiment K, appartement 17\n97430 Port-Gris",
        "37 route des Cadrans, lieu-dit Les Reflets Verts, 97670 Baie-Grise",
        "37 rue des Ca-\ndrans, bâtiment H, 48730 Griselune",
        "37 avenue des\nCadrans\n48730 Griselune",
        "BP 387, 48730\nGriselune Cedex 09",
    ],
)
def test_complete_address_has_one_span(address: str, no_network: None) -> None:
    """Inclut tous les compléments et sauts de ligne jusqu'à la ville."""
    text = f"Adresse : {address}. Suite du courrier."
    recognizer = AddressRecognizer()
    results = recognizer.analyze(text, ["ADDRESS"])
    assert [(text[r.start : r.end], r.score) for r in results] == [(address, 0.7)]
    found = detect(text)
    assert [(d.text, d.entity_type) for d in found] == [(address, EntityType.ADDRESS)]


@pytest.mark.parametrize(
    "text",
    ["article 37 bis du Code civil", "BP : budget prévisionnel", "CS 37 sans ville ni code"],
)
def test_address_traps_are_not_postal_addresses(text: str) -> None:
    """Exige les éléments postaux après une boîte et un vrai type de voie après un numéro."""
    assert AddressRecognizer().analyze(text, ["ADDRESS"]) == []


def test_procedure_suffix_is_not_a_postcode_for_the_next_line() -> None:
    """Les cinq chiffres après la barre du RG ne forment pas une adresse avec un titre."""
    text = "RG 26/08371\nAudience du 14 novembre 2026."
    assert AddressRecognizer().analyze(text, ["ADDRESS"]) == []
