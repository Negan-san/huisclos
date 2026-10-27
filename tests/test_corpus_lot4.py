"""Contrôle la forme des nouvelles sources de développement difficiles.

Entrées : huit sources dev seulement, sans accès aux sources réservées.
Sorties : assertions sur longueur, annotations, encodage et fins de ligne.
Ces contrôles éditoriaux précèdent toute mesure des règles de détection.
"""

from pathlib import Path

import pytest

from scripts.build_corpus import parse_source

SOURCE_DIR = Path(__file__).resolve().parents[1] / "corpus" / "source"


@pytest.mark.parametrize("number", range(19, 27))
def test_lot4_source_format(number: int) -> None:
    """Vérifie les contraintes A5 sur chaque nouvelle source du lot 4."""
    path = SOURCE_DIR / f"doc_{number}.md"
    assert b"\r" not in path.read_bytes()
    document = parse_source(path)
    assert document.id == f"doc_{number}"
    assert document.split == "dev"
    assert 250 <= len(document.text.split()) <= 500
    assert 12 <= len(document.entities) <= 30
    assert all(document.text[e.start : e.end] == e.text for e in document.entities)
    assert "{{" not in document.text and "[[" not in document.text
