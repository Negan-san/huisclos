"""Estime l'incertitude des scores par rééchantillonnage des documents.

Entrées : documents annotés et prédictions déjà calculées au seuil fixé.
Sorties : intervalles percentiles à 95 % des quatre ratios micro partiels.
Place dans le pipeline : après la mesure, sans nouvelle détection ni lecture du corpus.
"""

import random
from collections.abc import Sequence
from typing import Any

from huisclos.evaluation.corpus import CorpusDocument
from huisclos.evaluation.metrics import Counts, Evaluation
from huisclos.models import Detection

BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 45
INTERVAL_METRICS = ("precision", "recall", "f2", "leak_rate")
BOOTSTRAP_METHOD = {
    "method": "document percentile bootstrap",
    "draws": BOOTSTRAP_DRAWS,
    "seed": BOOTSTRAP_SEED,
    "confidence_level": 0.95,
    "percentile_interpolation": "linear (n - 1) * p",
    "mode": "partial",
    "type": "micro",
}


def percentile(values: Sequence[float], probability: float) -> float:
    """Renvoie le percentile interpolé de valeurs non vides pour une probabilité de 0 à 1."""
    if not values or not 0 <= probability <= 1:
        raise ValueError("Valeurs vides ou probabilité hors de [0, 1].")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    left = int(position)
    right = min(left + 1, len(ordered) - 1)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def document_counts(
    documents: Sequence[CorpusDocument], predictions: Sequence[Sequence[Detection]]
) -> list[Counts]:
    """Renvoie les comptes micro partiels de chaque document, sans croiser leurs spans."""
    if not documents or len(documents) != len(predictions):
        raise ValueError("Documents non vides et prédictions appariées attendus.")
    counts = []
    for document, detected in zip(documents, predictions, strict=True):
        evaluation = Evaluation()
        evaluation.add_document(document.entities, detected)
        row = next(
            row for row in evaluation.rows() if row["mode"] == "partial" and row["type"] == "micro"
        )
        counts.append(Counts(**{key: int(row[key]) for key in Counts.__dataclass_fields__}))
    return counts


def bootstrap_intervals(
    documents: Sequence[CorpusDocument], predictions: Sequence[Sequence[Detection]]
) -> dict[str, Any]:
    """Tire 2 000 échantillons de n documents avec remise et recalcule les ratios micro.

    La graine locale fixe rend chaque split et configuration reproductible, sans toucher
    au générateur global. Le seuil reste fixé ; les dénominateurs nuls donnent zéro,
    comme dans la mesure ponctuelle. Un seul document donne un intervalle réduit.
    """
    counts = document_counts(documents, predictions)
    rng = random.Random(BOOTSTRAP_SEED)
    samples: dict[str, list[float]] = {name: [] for name in INTERVAL_METRICS}
    for _ in range(BOOTSTRAP_DRAWS):
        selected = rng.choices(counts, k=len(counts))
        total = Counts(
            **{
                key: sum(getattr(count, key) for count in selected)
                for key in Counts.__dataclass_fields__
            }
        )
        scores = total.scores()
        for name in INTERVAL_METRICS:
            samples[name].append(float(scores[name]))
    return {
        "documents": len(counts),
        **{
            name: {"lower": percentile(values, 0.025), "upper": percentile(values, 0.975)}
            for name, values in samples.items()
        },
    }
