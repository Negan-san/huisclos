"""Tests métamorphiques déterministes : une variante d'écriture garde la même protection.

Entrées : les fixtures françaises post-G7, transformées par des fonctions pures (valeurs
fictives substituées, apostrophes, traits d'union, blancs, NFD, invisibles, coupures,
répétitions). Sorties : couverture, indices, bornes, jetons et aller-retour exact.
Une transformation ambiguë (minuscules d'un nom) n'impose aucune invariance.
"""

import re
import unicodedata
from collections.abc import Callable
from pathlib import Path

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import detect
from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.models import Detection, EntityType
from huisclos.pseudonymize.reidentify import restore
from huisclos.pseudonymize.tokens import pseudonymize
from scripts.build_corpus import parse_source

FIXTURES = Path(__file__).parent / "fixtures" / "post_g7"
CONFIG = DetectionConfig(threshold=0.30)
DOCUMENTS = ["fr_adresses.md", "fr_naissance_procedure.md", "fr_alias_fichiers.md"]
EVALUATED = frozenset(EntityType) - {EntityType.CUSTOM, EntityType.LOCATION}
Piece = Callable[[str, EntityType | None], str]


def rebuild(document: CorpusDocument, change: Piece) -> CorpusDocument:
    """Applique change à chaque morceau du texte et recalcule les annotations.

    change reçoit un morceau et son type (None hors annotation) ; les positions des
    annotations suivent la nouvelle longueur des morceaux, sans recherche de chaîne.
    """
    pieces: list[str] = []
    entities: list[GoldEntity] = []
    cursor = length = 0
    for gold in sorted(document.entities, key=lambda e: e.start):
        outside = change(document.text[cursor : gold.start], None)
        inside = change(gold.text, gold.type)
        pieces += [outside, inside]
        length += len(outside)
        entities.append(GoldEntity(length, length + len(inside), gold.type, inside))
        length += len(inside)
        cursor = gold.end
    pieces.append(change(document.text[cursor:], None))
    return CorpusDocument(
        document.id, document.doc_type, document.split, document.title, "".join(pieces), entities
    )


def _inside(transform: Callable[[str], str]) -> Piece:
    """Change seulement les morceaux annotés."""
    return lambda piece, kind: transform(piece) if kind is not None else piece


def _middle(mark: str) -> Callable[[str], str]:
    """Insère mark au milieu de chaque mot de plus de quatre lettres."""

    def insert(piece: str) -> str:
        words = piece.split(" ")
        return " ".join(
            w[: len(w) // 2] + mark + w[len(w) // 2 :] if sum(c.isalpha() for c in w) > 4 else w
            for w in words
        )

    return insert


SUBSTITUTIONS = {
    "Ysaline": "Gwenaëlle",
    "FERRAND": "VASSEROT",
    "Odilon": "Anatole",
    "MARCHETTI": "LOUVIGNY",
    "ORTEGA": "BRESSOLLE",
    "Basile": "Clotaire",
    "Valbrune": "Morvalon",
}

TRANSFORMS: dict[str, Piece] = {
    "valeurs-substituees": lambda piece, kind: _substitute(piece),
    "apostrophe-typographique": lambda piece, kind: piece.replace("'", "\u2019"),
    "trait-insecable": _inside(lambda p: p.replace("-", "\u2011")),
    "espace-insecable": _inside(lambda p: p.replace(" ", "\u00a0")),
    "espace-fine": _inside(lambda p: p.replace(" ", "\u202f")),
    "nfd": lambda piece, kind: unicodedata.normalize("NFD", piece),
    "trait-conditionnel": _inside(_middle("\u00ad")),
    "espace-nul": _inside(_middle("\u200b")),
    "gluon": _inside(_middle("\u2060")),
    "coupure-adresse": lambda piece, kind: (
        _break_before_city(piece) if kind is EntityType.ADDRESS else piece
    ),
}


def _break_before_city(address: str) -> str:
    """Coupe l'adresse juste avant son code postal, comme une extraction de PDF."""
    return re.sub(r"[ \t](?=[0-9]{5}(?![0-9]))", "\n", address, count=1)


def _substitute(piece: str) -> str:
    """Remplace les valeurs fictives par d'autres valeurs fictives, partout."""
    for old, new in SUBSTITUTIONS.items():
        piece = piece.replace(old, new)
    return piece


def _masked(text: str, detections: list[Detection]) -> set[int]:
    """Positions de text couvertes par une détection."""
    return {i for d in detections for i in range(d.start, d.end)}


def _check(document: CorpusDocument, exact: bool = True) -> list[Detection]:
    """Détecte, puis vérifie indices, couverture, bornes et aller-retour exact."""
    found = detect(document.text, CONFIG)
    assert all(d.text == document.text[d.start : d.end] for d in found)
    masked = _masked(document.text, found)
    bounds = {(d.start, d.end, d.entity_type) for d in found}
    for gold in document.entities:
        if gold.type in EVALUATED:
            assert set(range(gold.start, gold.end)) <= masked, gold.text
            if exact:
                assert (gold.start, gold.end, gold.type) in bounds, gold.text
    result = pseudonymize(document.text, found)
    assert restore(result.text, result.mapping).text == document.text
    return found


@pytest.fixture(scope="module")
def documents() -> dict[str, CorpusDocument]:
    """Fixtures françaises annotées avant les règles de A2."""
    return {name: parse_source(FIXTURES / name) for name in DOCUMENTS}


@pytest.mark.parametrize("name", DOCUMENTS)
def test_base_fixtures_are_fully_covered(name: str, documents: dict[str, CorpusDocument]) -> None:
    """Point de départ : chaque fixture est couverte avec ses bornes exactes."""
    _check(documents[name])


@pytest.mark.parametrize("transform", sorted(TRANSFORMS))
@pytest.mark.parametrize("name", DOCUMENTS)
def test_variants_keep_coverage_bounds_and_roundtrip(
    name: str, transform: str, documents: dict[str, CorpusDocument]
) -> None:
    """Chaque variante d'écriture garde couverture, bornes exactes et restauration exacte."""
    _check(rebuild(documents[name], TRANSFORMS[transform]))


def test_repetition_keeps_tokens_of_certain_identities(
    documents: dict[str, CorpusDocument],
) -> None:
    """Un document répété trois fois : mêmes entités et mêmes jetons dans chaque copie."""
    base = documents["fr_naissance_procedure.md"]
    separator = "\n\n" + "Texte de liaison sans donnée personnelle. " * 40 + "\n\n"
    text = separator.join([base.text] * 3)
    found = detect(text, CONFIG)
    result = pseudonymize(text, found)
    copies = result.text.split("Texte de liaison sans donnée personnelle.")
    first, last = copies[0].strip(), copies[-1].strip()
    assert first == last and "[PERSONNE_1]" in first
    assert restore(result.text, result.mapping).text == text


@pytest.mark.parametrize(
    "change",
    [_middle("\u00ad"), _middle("\u200b"), _middle("\u2060"), lambda p: p.replace(" ", "\u00a0")],
    ids=["shy", "zwsp", "wj", "nbsp"],
)
def test_marks_in_ordinary_words_do_not_create_detections(
    change: Callable[[str], str], documents: dict[str, CorpusDocument]
) -> None:
    """Lisibilité : des marques dans le texte ordinaire n'ajoutent aucune détection."""
    base = documents["fr_naissance_procedure.md"]
    changed = rebuild(base, lambda piece, kind: change(piece) if kind is None else piece)
    before = detect(base.text, CONFIG)
    after = detect(changed.text, CONFIG)
    assert [d.entity_type for d in after] == [d.entity_type for d in before]


def test_lowercased_name_is_not_required_to_be_found(
    documents: dict[str, CorpusDocument],
) -> None:
    """Transformation ambiguë : un nom écrit en minuscules peut devenir un mot ordinaire.

    Seuls l'exactitude des indices et l'aller-retour sont exigés, pas la couverture.
    """
    base = documents["fr_adresses.md"]
    changed = rebuild(
        base, lambda piece, kind: piece.lower() if kind is EntityType.PERSON else piece
    )
    found = detect(changed.text, CONFIG)
    assert all(d.text == changed.text[d.start : d.end] for d in found)
    result = pseudonymize(changed.text, found)
    assert restore(result.text, result.mapping).text == changed.text
