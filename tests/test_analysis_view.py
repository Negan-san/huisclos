"""Vérifie la vue d'analyse projetable : transformations, table monotone et texte exact.

Entrées : textes fictifs avec caractères invisibles, ligatures, formes décomposées et noms
de fichiers. Sorties : assertions sur la vue, la projection et les détections finales.
Le texte canonique n'est jamais modifié ; seules les bornes passent de la vue au texte.
"""

import random
import unicodedata

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.analysis_view import INVISIBLE, LIGATURES, build_view
from huisclos.detection.pipeline import detect
from huisclos.models import EntityType

CONFIG = DetectionConfig(threshold=0.30)


def test_plain_text_is_its_own_view() -> None:
    """Sans caractère particulier, la vue égale le texte et la projection est l'identité."""
    text = "Jean DUPONT habite 12 rue Haute, 75011 Paris."
    view = build_view(text)
    assert view.text == text and view.is_legacy
    assert view.project(0, 11) == (0, 11)


def test_nonbreaking_spaces_keep_the_legacy_analysis() -> None:
    """Les blancs insécables étaient déjà unifiés avant A2 : pas de seconde analyse."""
    view = build_view("Jean\u00a0DUPONT\u202fParis")
    assert view.text == "Jean DUPONT Paris" and view.is_legacy


@pytest.mark.parametrize("invisible", sorted(INVISIBLE))
def test_invisible_characters_are_removed_and_projected(invisible: str) -> None:
    """Un invisible intérieur disparaît de la vue et reste dans le span canonique."""
    text = f"M. GRAND{invisible}CLÉMENT signe."
    view = build_view(text)
    assert view.text == "M. GRANDCLÉMENT signe."
    start = view.text.index("GRANDCLÉMENT")
    assert view.project(start, start + len("GRANDCLÉMENT")) == (3, 16)
    assert text[3:16] == f"GRAND{invisible}CLÉMENT"
    assert not view.is_legacy


@pytest.mark.parametrize(("ligature", "expansion"), sorted(LIGATURES.items()))
def test_ligatures_expand_to_the_same_source_character(ligature: str, expansion: str) -> None:
    """Chaque lettre développée renvoie au caractère de ligature entier."""
    text = f"Le{ligature}x"
    view = build_view(text)
    assert view.text == f"Le{expansion}x"
    assert view.project(2, 3) == (2, 3)
    assert view.project(2 + len(expansion), 3 + len(expansion)) == (3, 4)


def test_decomposed_text_is_composed_in_the_view() -> None:
    """Une lettre décomposée (NFD) devient une lettre composée dans la vue."""
    text = unicodedata.normalize("NFD", "Hélène")
    view = build_view(text)
    assert view.text == "Hélène" and len(text) == 8
    assert view.project(0, 6) == (0, 8)


def test_file_name_underscores_become_spaces() -> None:
    """Seuls les tirets bas d'un nom de fichier deviennent des espaces, à longueur égale."""
    text = "Pièce : attestation_DUPONT_Jean.pdf ; variable_interne reste."
    view = build_view(text)
    assert "attestation DUPONT Jean.pdf" in view.text
    assert "variable_interne" in view.text
    assert len(view.text) == len(text)


def test_projection_is_monotone_on_random_texts() -> None:
    """Sur des textes tirés au hasard, les bornes projetées croissent et restent valides."""
    alphabet = list("abcÉé ,.\n") + sorted(INVISIBLE) + sorted(LIGATURES) + ["é", "\u00a0"]
    rng = random.Random(7)
    for _ in range(200):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 40)))
        view = build_view(text)
        assert list(view.starts) == sorted(view.starts)
        assert list(view.ends) == sorted(view.ends)
        for start in range(len(view.text)):
            begin, end = view.project(start, start + 1)
            assert 0 <= begin < end <= len(text)


def test_empty_or_reversed_span_is_refused() -> None:
    """Une projection vide ou hors de la vue lève une erreur explicite."""
    view = build_view("abc")
    with pytest.raises(ValueError, match="hors de la vue"):
        view.project(2, 2)
    with pytest.raises(ValueError, match="hors de la vue"):
        view.project(0, 4)


@pytest.mark.parametrize(
    "variant",
    [
        lambda s: s.replace("GRANDCLÉMENT", "GRAND\u00adCLÉMENT"),
        lambda s: s.replace("rue de", "rue\u200b de"),
        lambda s: s.replace("Hélène", "Hé\u2060lène"),
        lambda s: unicodedata.normalize("NFD", s),
        lambda s: s.replace(" ", "\u2009"),
    ],
    ids=["trait-conditionnel", "espace-nul", "gluon", "nfd", "espace-fine"],
)
def test_detections_keep_the_canonical_text(variant: object) -> None:
    """La détection finale reprend le texte canonique, invisibles compris."""
    base = "Madame Hélène GRANDCLÉMENT habite 12 rue de la Paix, 75002 Paris."
    text = variant(base)  # type: ignore[operator]
    found = detect(text, CONFIG)
    assert all(d.text == text[d.start : d.end] for d in found)
    kinds = [d.entity_type for d in found]
    assert kinds.count(EntityType.ADDRESS) == 1 and EntityType.PERSON in kinds
    person = next(d for d in found if d.entity_type is EntityType.PERSON)
    assert "CL" in person.text and "l" in person.text


def test_original_view_candidates_are_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un candidat propre au texte d'origine survit même si la vue le perd (garantie A1)."""
    import huisclos.detection.pipeline as pipeline

    original = pipeline.build_view

    def losing_view(text: str):  # type: ignore[no-untyped-def]
        view = original(text)
        return type(view)(view.canonical, view.text.replace("06", "xx"), view.starts, view.ends)

    monkeypatch.setattr(pipeline, "build_view", losing_view)
    text = "Tél. : 06 12 34 56 78\u00ad"
    found = detect(text, CONFIG)
    assert [(d.entity_type, d.text) for d in found] == [(EntityType.PHONE, "06 12 34 56 78")]
