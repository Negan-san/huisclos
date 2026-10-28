"""Vérifie l'assembleur d'adresses : ancrages, bornes, arrêts et adresses anglophones.

Entrées : adresses inventées, pièges de champ voisin, de phrase et de référence.
Sorties : assertions sur les spans, leur nature et les scores D-07.
Ces cas isolent detection.address_bounds avant la fusion et le pipeline complet.
"""

import time

import pytest

from huisclos.detection.address_bounds import (
    MAX_CHARS,
    AddressKind,
    AddressSpan,
    address_spans,
)
from huisclos.detection.patterns import AddressRecognizer


def _texts(text: str, language: str = "fr") -> list[tuple[str, AddressKind]]:
    """Texte et nature de chaque adresse trouvée dans text."""
    return [(text[s.start : s.end], s.kind) for s in address_spans(text, language)]


@pytest.mark.parametrize(
    "address",
    [
        "12 bis, rue du Vieux-Moulin\nRésidence Les Tilleuls, bât. C, appt 14\n"
        "59130 Valbrune-sur-Escaut CEDEX 2",
        "8, place de l'Hôtel de Ville \u2013 69402 CLAIRMONT-LÈS-VIGNES",
        "Lieu-dit La Croix Blanche\n24560 Saint-Aubin-des-Fougerolles",
        "14 rue des Halles, 2e étage, 75001 Paris 1er",
        "14 rue Basse\t75011 Paris",
        "14 rue Basse | 75011 Paris",
        "12 rue du 8 Mai 1945, 37000 Tours",
        "12-14 avenue Albéric Fontanel 21470 Brumefort",
        "Hameau de la Combe\n38410 Vaulnaveys-le-Bas",
        "ZI des Bruyères, 69800 Saint-Priest",
        "TSA 70011, 75901 Paris Cedex 15",
    ],
)
def test_complete_address_is_one_span(address: str) -> None:
    """Une adresse complète va du numéro ou du lieu nommé jusqu'à la ville et ses compléments."""
    text = f"Domicile : {address}\nTél. : 06 12 34 56 78"
    assert _texts(text) == [(address, AddressKind.FULL)]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Expéditeur : 3 rue des Prés 21470 Brumefort "
            "Destinataire : 18 avenue Foch 21470 Brumefort",
            ["3 rue des Prés 21470 Brumefort", "18 avenue Foch 21470 Brumefort"],
        ),
        (
            "Adresse : 5 boulevard Gambetta 59140 Dunquerelle Tel : 03 28 00 00 00",
            ["5 boulevard Gambetta 59140 Dunquerelle"],
        ),
        (
            "Adresse : 7 allée Verte, 44000 Nantes, courriel : a.b@example.com",
            ["7 allée Verte, 44000 Nantes"],
        ),
        (
            "domiciliée 3 chemin des Écoliers, 34170 Castelnau-les-Brumes, puis 9 rue Haute, "
            "34200 Sétival.",
            ["3 chemin des Écoliers, 34170 Castelnau-les-Brumes", "9 rue Haute, 34200 Sétival"],
        ),
    ],
)
def test_next_field_or_next_address_stops_the_span(text: str, expected: list[str]) -> None:
    """Un libellé, une autre coordonnée ou une autre adresse ferme l'adresse en cours."""
    assert [value for value, _kind in _texts(text)] == expected


@pytest.mark.parametrize(
    ("text", "street"),
    [
        (
            "Elle habite au 15 rue Saint-Jacquemart à Valbrune depuis 2019.",
            "15 rue Saint-Jacquemart",
        ),
        ("Elle habite 22 rue du Port. 56100 personnes ont signé.", "22 rue du Port"),
        ("Il vit 12 rue des petits champs, près du marché.", "12 rue des petits champs"),
        ("Rendez-vous 4 place des Prés le 3 mars 2026.", "4 place des Prés"),
    ],
)
def test_street_alone_does_not_swallow_the_sentence(text: str, street: str) -> None:
    """Une voie sans code postal s'arrête avant la suite de la phrase (0,55)."""
    assert _texts(text) == [(street, AddressKind.STREET)]


@pytest.mark.parametrize(
    "text",
    [
        "numéro RG : 23 / 00045\nAudience du 14 novembre 2026.",
        "RG 26/08371\nAudience du 14 novembre 2026.",
        "Dossier n° 13008\nMarseille, le 3 mai 2026",
        "Le code 00045 Valbrune n'existe pas.",
        "Selon l'article L. 1234-5 du Code du travail.",
        "3, rue de la République\n\n13001",
        "Lieu-dit sans ligne postale, puis la suite.",
        "BP : budget prévisionnel",
    ],
)
def test_reference_or_trap_is_not_a_postal_line(text: str) -> None:
    """Une procédure, un code invalide ou un libellé ne deviennent pas une ligne postale."""
    assert all(kind is AddressKind.STREET for _value, kind in _texts(text))


def test_paragraph_break_separates_street_and_city() -> None:
    """Une ligne vide sépare deux informations : voie et ville restent deux spans partiels."""
    text = "3, rue de la République\n\n13001 Marseille"
    assert _texts(text) == [
        ("3, rue de la République", AddressKind.STREET),
        ("13001 Marseille", AddressKind.POSTAL),
    ]


def test_city_alone_is_never_an_address() -> None:
    """Une ville sans code postal ni voie reste visible."""
    assert _texts("Elle vit à Valbrune-sur-Escaut depuis 2019.") == []


def test_bounds_limit_segments_and_characters() -> None:
    """Une suite trop longue de compléments n'atteint pas la ligne postale."""
    complements = ", ".join(f"bâtiment {letter}" for letter in "ABCDEFGH")
    text = f"12 rue Haute, {complements}, 75011 Paris"
    found = address_spans(text)
    assert found[0] == AddressSpan(0, len("12 rue Haute"), AddressKind.STREET)
    assert all(span.end - span.start <= MAX_CHARS for span in found)


@pytest.mark.parametrize(
    ("address", "trailing"),
    [
        ("Flat 3, 17 Kingsmere Road, London SW19 7QD", ", United Kingdom."),
        ("42 Willow Lane, Apt 5B, Springfield, IL 62704", ", USA."),
        ("PO Box 1234, Springfield, IL 62704", "."),
        ("17 Kingsmere Road\nWimbledon\nLondon SW19 7QD", "\nTel: 020 7946 0958"),
        ("12 rue des Lilas, 75011 Paris", ", France."),
    ],
)
def test_english_addresses_end_at_last_postal_component(address: str, trailing: str) -> None:
    """Document anglais : le span s'arrête au code postal ou au ZIP ; le pays reste visible."""
    text = f"Address: {address}{trailing}"
    assert _texts(text, "en") == [(address, AddressKind.FULL)]


def test_english_anchors_stay_off_in_french_documents() -> None:
    """Les ancrages britanniques et américains ne servent qu'aux documents anglais."""
    text = "Adresse : 17 Kingsmere Road, London SW19 7QD."
    assert _texts(text, "fr") == []
    assert _texts("SW19 7QD", "en") == [("SW19 7QD", AddressKind.POSTAL)]


def test_recognizer_scores_follow_d07() -> None:
    """0,70 complète, 0,55 voie seule, 0,45 ligne postale seule."""
    text = "12 rue Haute, 75011 Paris. Puis 4 rue Basse. Enfin 75012 Paris."
    results = AddressRecognizer().analyze(text, ["ADDRESS"])
    assert [(text[r.start : r.end], r.score) for r in results] == [
        ("12 rue Haute, 75011 Paris", 0.70),
        ("4 rue Basse", 0.55),
        ("75012 Paris", 0.45),
    ]


@pytest.mark.parametrize(
    "text",
    ["12 rue " + "Abcd " * 2000, "75011 " * 3000, ("12 rue Haute, bâtiment A, " * 400)],
)
def test_long_adversarial_lines_stay_fast(text: str) -> None:
    """L'assembleur borné garde un temps linéaire sur des lignes adverses."""
    started = time.perf_counter()
    address_spans(text)
    address_spans(text, "en")
    assert time.perf_counter() - started < 2.0
