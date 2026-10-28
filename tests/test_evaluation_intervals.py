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
    defined_interval,
    document_counts,
    draw_indices,
    paired_differences,
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


def test_draw_indices_reproduce_the_historical_draws() -> None:
    """Les indices tirés sélectionnent exactement les documents de bootstrap_intervals."""
    documents = [document(0, (3, 3, 3)), document(1, (9,)), document(2, (2, 2))]
    predictions = [[detection(0, 3)], [detection(0, 4)], []]
    state = random.getstate()
    draws = draw_indices(len(documents))
    assert random.getstate() == state
    assert draws == draw_indices(len(documents))
    assert len(draws) == BOOTSTRAP_DRAWS and all(len(draw) == 3 for draw in draws)
    counts = document_counts(documents, predictions)
    samples = {name: [] for name in INTERVAL_METRICS}
    for draw in draws:
        total = Counts(
            **{
                key: sum(getattr(counts[i], key) for i in draw)
                for key in Counts.__dataclass_fields__
            }
        )
        for name in INTERVAL_METRICS:
            samples[name].append(total.scores()[name])
    result = bootstrap_intervals(documents, predictions)
    for name in INTERVAL_METRICS:
        assert result[name]["lower"] == percentile(samples[name], 0.025)
        assert result[name]["upper"] == percentile(samples[name], 0.975)
    with pytest.raises(ValueError):
        draw_indices(0)


def test_defined_interval_drops_and_counts_undefined_draws() -> None:
    """Un tirage sans dénominateur est écarté et compté, jamais remplacé par zéro."""
    interval = defined_interval([None, 0.0, 1.0, None])
    assert interval["lower"] == pytest.approx(0.025)
    assert interval["upper"] == pytest.approx(0.975)
    assert interval["undefined_draws"] == 2
    assert defined_interval([None, None]) == {"lower": None, "upper": None, "undefined_draws": 2}


def test_paired_differences_use_the_same_draws() -> None:
    """L'écart se calcule tirage par tirage ; un tirage incomplet est écarté et compté."""
    key = ("pseudonymization", "leaked_character_rate")
    values = {"a": {key: [0.5, 0.0, None]}, "b": {key: [0.1, 0.2, 0.3]}}
    estimates = {"a": {key: 0.4}, "b": {key: 0.1}}
    [row] = paired_differences(values, estimates, [["a", "b"]])
    assert (row["candidate"], row["reference"], row["stage"], row["metric"]) == ("a", "b", *key)
    assert row["estimate"] == pytest.approx(0.3)
    assert row["lower"] == pytest.approx(percentile([0.4, -0.2], 0.025))
    assert row["upper"] == pytest.approx(percentile([0.4, -0.2], 0.975))
    assert (row["undefined_draws"], row["excludes_zero"]) == (1, False)
    same = paired_differences(values, estimates, [["b", "b"]])[0]
    assert (same["lower"], same["upper"], same["excludes_zero"]) == (0.0, 0.0, False)
    [shifted] = paired_differences(
        {"a": {key: [0.5, 0.6]}, "b": {key: [0.1, 0.1]}}, estimates, [["a", "b"]]
    )
    assert shifted["excludes_zero"] is True
