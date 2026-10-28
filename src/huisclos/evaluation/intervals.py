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


def draw_indices(size: int) -> list[list[int]]:
    """Renvoie les 2 000 tirages de size indices de documents, avec remise, graine 45.

    random.choices sans poids tire floor(random() * n) : tirer des indices donne la même
    suite de documents que bootstrap_intervals. Les mêmes tirages servent aux intervalles
    marginaux et aux différences appariées de deux profils mesurés sur les mêmes documents.
    """
    if size < 1:
        raise ValueError("Au moins un document est nécessaire au rééchantillonnage.")
    rng = random.Random(BOOTSTRAP_SEED)
    indices = range(size)
    return [rng.choices(indices, k=size) for _ in range(BOOTSTRAP_DRAWS)]


def defined_interval(values: Sequence[float | None]) -> dict[str, float | int | None]:
    """Renvoie les percentiles 2,5 et 97,5 des tirages définis et compte les autres.

    Un tirage sans dénominateur n'a pas de valeur : il est écarté et compté, jamais remplacé
    par zéro. Sans aucun tirage défini, les bornes valent None (not applicable).
    """
    defined = [value for value in values if value is not None]
    return {
        "lower": percentile(defined, 0.025) if defined else None,
        "upper": percentile(defined, 0.975) if defined else None,
        "undefined_draws": len(values) - len(defined),
    }


def paired_differences(
    values: dict[str, dict[tuple[str, str], list[float | None]]],
    estimates: dict[str, dict[tuple[str, str], float | None]],
    comparisons: Sequence[Sequence[str]],
) -> list[dict[str, Any]]:
    """Renvoie les différences candidat moins référence, calculées tirage par tirage.

    values donne, par profil et par (stade, mesure), la valeur de chacun des mêmes tirages
    de documents ; estimates donne la valeur sur tous les documents. Un tirage où l'une des
    deux valeurs manque est écarté et compté. excludes_zero dit si l'intervalle apparié
    exclut zéro ; les intervalles marginaux seuls ne permettent pas cette conclusion.
    """
    rows = []
    for candidate, reference in comparisons:
        for key, samples in values[candidate].items():
            differences = [
                None if first is None or second is None else first - second
                for first, second in zip(samples, values[reference][key], strict=True)
            ]
            first, second = estimates[candidate][key], estimates[reference][key]
            interval = defined_interval(differences)
            lower, upper = interval["lower"], interval["upper"]
            rows.append(
                {"candidate": candidate, "reference": reference, "stage": key[0], "metric": key[1]}
                | {"estimate": None if first is None or second is None else first - second}
                | interval
                | {"excludes_zero": None if lower is None else lower > 0 or upper < 0}
            )
    return rows


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
