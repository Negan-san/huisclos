"""Vérifie les intervalles par document sur des annotations entièrement fictives.

Entrées : petits documents et prédictions construits sans modèle ni fichier du corpus.
Sorties : assertions sur les percentiles, les ratios micro et les cas dégénérés.
Place dans le pipeline : validation du calcul d'incertitude, sans aucune détection.
"""

import random

import pytest

from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.evaluation.intervals import (
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    INTERVAL_METRICS,
    bootstrap_intervals,
    document_counts,
    percentile,
)
from huisclos.evaluation.metrics import Counts
from huisclos.models import Detection, EntityType, Source


def document(index: int, lengths: tuple[int, ...]) -> CorpusDocument:
    """Crée un document où chaque segment fictif est annoté comme personne."""
    text = " ".join("x" * length for length in lengths)
    entities = []
    start = 0
    for length in lengths:
        entities.append(GoldEntity(start, start + length, EntityType.PERSON, "x" * length))
        start += length + 1
    return CorpusDocument(str(index), "letter", "dev", "Fiction", text, entities)


def detection(start: int, end: int, kind: EntityType = EntityType.PERSON) -> Detection:
    """Construit une prédiction fictive aux bornes fournies."""
    return Detection(start, end, kind, 0.8, Source.MANUAL, "x" * (end - start))


def test_percentile_linear_interpolation() -> None:
    """Les bornes suivent la formule (n - 1) p, y compris aux extrêmes."""
    assert percentile([1, 0, 0.5], 0.025) == pytest.approx(0.025)
    assert percentile([1, 0, 0.5], 0.975) == pytest.approx(0.975)
    assert percentile([0.7], 0.025) == 0.7
    assert percentile([0, 1], 0) == 0
    assert percentile([0, 1], 1) == 1
    for values, probability in (([], 0.5), ([0], -0.1), ([0], 1.1)):
        with pytest.raises(ValueError):
            percentile(values, probability)


def test_bootstrap_reproducible_micro_and_encloses_point() -> None:
    """Un contrôle indépendant recalcule les ratios depuis les documents tirés avec remise."""
    documents = [document(0, (3, 3, 3)), document(1, (9,)), document(2, (2, 2))]
    predictions = [[detection(0, 3)], [detection(0, 4)], []]
    state = random.getstate()
    result = bootstrap_intervals(documents, predictions)
    assert result == bootstrap_intervals(documents, predictions)
    assert random.getstate() == state
    # Comptes indépendants : le second document a un VP partiel mais cinq caractères exposés.
    independent = [(1, 0, 2, 9, 6), (1, 0, 0, 9, 5), (0, 0, 2, 4, 4)]
    rng = random.Random(BOOTSTRAP_SEED)
    samples = {name: [] for name in INTERVAL_METRICS}
    for _ in range(BOOTSTRAP_DRAWS):
        selected = rng.choices(independent, k=3)
        tp, fp, fn, characters, leaked = map(sum, zip(*selected, strict=True))
        values = (
            tp / (tp + fp) if tp + fp else 0,
            tp / (tp + fn),
            5 * tp / (5 * tp + fp + 4 * fn),
            leaked / characters,
        )
        for name, value in zip(INTERVAL_METRICS, values, strict=True):
            samples[name].append(value)
    point = Counts(tp=2, fn=4, reference_characters=22, leaked_characters=15).scores()
    for name in INTERVAL_METRICS:
        bounds = result[name]
        assert bounds == {
            "lower": percentile(samples[name], 0.025),
            "upper": percentile(samples[name], 0.975),
        }
        assert 0 <= bounds["lower"] <= point[name] <= bounds["upper"] <= 1
    assert result["documents"] == 3


@pytest.mark.parametrize("empty", [False, True])
def test_single_document_and_no_entities(empty: bool) -> None:
    """Un seul document répète ses ratios ; sans entité, les quatre intervalles valent zéro."""
    documents = [document(0, () if empty else (5, 3))]
    predictions = [[] if empty else [detection(0, 2), detection(3, 4, EntityType.EMAIL)]]
    point = document_counts(documents, predictions)[0].scores()
    intervals = bootstrap_intervals(documents, predictions)
    for name in INTERVAL_METRICS:
        assert intervals[name] == {"lower": point[name], "upper": point[name]}


def test_no_entity_documents_and_unmatched_predictions() -> None:
    """Les documents vides d'entités restent tirables et ne créent pas de valeur indéfinie."""
    documents = [document(0, ()), document(1, ())]
    intervals = bootstrap_intervals(documents, [[], [detection(0, 3)]])
    assert all(intervals[name] == {"lower": 0.0, "upper": 0.0} for name in INTERVAL_METRICS)


def test_invalid_bootstrap_inputs() -> None:
    """L'absence de document et des listes de tailles différentes sont refusées."""
    with pytest.raises(ValueError):
        bootstrap_intervals([], [])
    with pytest.raises(ValueError):
        bootstrap_intervals([document(0, ())], [])
