"""Mesure les détections face aux annotations fictives, document par document.

Entrées : références du corpus et prédictions du pipeline au seuil évalué.
Sorties : appariements uniques, scores exacts et partiels, couverture des caractères.
Place dans le pipeline : calcul pur, sans modèle, utilisé par evaluation.run.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from huisclos.evaluation.corpus import GoldEntity
from huisclos.models import Detection, EntityType

Mode = Literal["exact", "partial"]
EVALUATED_TYPES = tuple(
    sorted(kind.value for kind in EntityType if kind.value not in {"LOCATION", "CUSTOM"})
)


def evaluated_references(references: Sequence[GoldEntity]) -> list[GoldEntity]:
    """Renvoie les références dont le type appartient au périmètre évalué."""
    return [reference for reference in references if reference.type.value in EVALUATED_TYPES]


def evaluated_predictions(predictions: Sequence[Detection]) -> list[Detection]:
    """Renvoie les prédictions hors LOCATION et CUSTOM, ignorés par le protocole."""
    return [
        prediction for prediction in predictions if prediction.entity_type.value in EVALUATED_TYPES
    ]


def match_entities(
    references: Sequence[GoldEntity], predictions: Sequence[Detection], mode: Mode
) -> list[tuple[int, int]]:
    """Renvoie les indices des couples uniques de même type dans les listes fournies.

    Le recouvrement le plus long est servi en premier ; les égalités suivent les
    positions puis les indices. Une prédiction ne peut valider deux références.
    LOCATION et CUSTOM sont ignorés sans changer les indices des autres éléments.
    """
    if mode not in {"exact", "partial"}:
        raise ValueError("Mode attendu : exact ou partial.")
    candidates: list[tuple[int, int, int, int, int, int, int]] = []
    for reference_index, reference in enumerate(references):
        if reference.type.value not in EVALUATED_TYPES:
            continue
        for prediction_index, prediction in enumerate(predictions):
            if reference.type != prediction.entity_type:
                continue
            overlap = min(reference.end, prediction.end) - max(reference.start, prediction.start)
            exact = (reference.start, reference.end) == (prediction.start, prediction.end)
            if overlap > 0 and (mode == "partial" or exact):
                candidates.append(
                    (
                        -overlap,
                        reference.start,
                        reference.end,
                        prediction.start,
                        prediction.end,
                        reference_index,
                        prediction_index,
                    )
                )
    matched_references: set[int] = set()
    matched_predictions: set[int] = set()
    pairs: list[tuple[int, int]] = []
    for *_, reference_index, prediction_index in sorted(candidates):
        if (
            reference_index not in matched_references
            and prediction_index not in matched_predictions
        ):
            pairs.append((reference_index, prediction_index))
            matched_references.add(reference_index)
            matched_predictions.add(prediction_index)
    return pairs


def uncovered_characters(reference: GoldEntity, predictions: Sequence[Detection]) -> int:
    """Compte les caractères de référence non couverts, quel que soit le type prédit.

    Les intersections sont réunies pour ne pas compter deux fois une couverture.
    Les prédictions LOCATION et CUSTOM restent hors du périmètre d'évaluation.
    """
    cursor = reference.start
    covered = 0
    for start, end in sorted(
        (max(reference.start, prediction.start), min(reference.end, prediction.end))
        for prediction in evaluated_predictions(predictions)
        if prediction.end > reference.start and prediction.start < reference.end
    ):
        covered += max(0, end - max(cursor, start))
        cursor = max(cursor, end)
    return reference.end - reference.start - covered


@dataclass
class Counts:
    """Cumuls d'un type : appariements, caractères sensibles et entités exposées."""

    tp: int = 0
    fp: int = 0
    fn: int = 0
    reference_characters: int = 0
    leaked_characters: int = 0
    exposed_entities: int = 0

    def scores(self) -> dict[str, int | float]:
        """Renvoie les comptes et ratios ; un dénominateur nul donne zéro."""
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0,
            "recall": self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0,
            "f1": 2 * self.tp / (2 * self.tp + self.fp + self.fn)
            if 2 * self.tp + self.fp + self.fn
            else 0.0,
            "f2": 5 * self.tp / (5 * self.tp + self.fp + 4 * self.fn)
            if 5 * self.tp + self.fp + 4 * self.fn
            else 0.0,
            "leak_rate": self.leaked_characters / self.reference_characters
            if self.reference_characters
            else 0.0,
            "exposed_entities": self.exposed_entities,
            "reference_characters": self.reference_characters,
            "leaked_characters": self.leaked_characters,
        }


@dataclass
class Evaluation:
    """Accumule les documents sans permettre d'appariement entre documents."""

    counts: dict[Mode, dict[str, Counts]] = field(
        default_factory=lambda: {
            mode: {kind: Counts() for kind in EVALUATED_TYPES} for mode in ("exact", "partial")
        }
    )

    def add_document(
        self, references: Sequence[GoldEntity], predictions: Sequence[Detection]
    ) -> None:
        """Ajoute les comptes d'un document à partir des références et prédictions."""
        references = evaluated_references(references)
        predictions = evaluated_predictions(predictions)
        for mode, by_type in self.counts.items():
            pairs = match_entities(references, predictions, mode)
            matched_references = {reference_index for reference_index, _ in pairs}
            matched_predictions = {prediction_index for _, prediction_index in pairs}
            for index, reference in enumerate(references):
                counts = by_type[reference.type.value]
                counts.tp += int(index in matched_references)
                counts.fn += int(index not in matched_references)
                length = reference.end - reference.start
                uncovered = uncovered_characters(reference, predictions)
                counts.reference_characters += length
                counts.leaked_characters += uncovered
                counts.exposed_entities += int(uncovered == length)
            for index, prediction in enumerate(predictions):
                by_type[prediction.entity_type.value].fp += int(index not in matched_predictions)

    def rows(self) -> list[dict[str, str | int | float]]:
        """Renvoie par mode les types, le micro total et la moyenne macro des types.

        La macro inclut les onze types évalués, même absents, et moyenne chaque
        colonne. Les comptes micro sont les sommes ; ses ratios sont recalculés.
        """
        rows: list[dict[str, str | int | float]] = []
        for mode, by_type in self.counts.items():
            scores = [counts.scores() for counts in by_type.values()]
            rows.extend(
                {"mode": mode, "type": kind, **counts.scores()} for kind, counts in by_type.items()
            )
            total = Counts(
                **{
                    key: sum(getattr(counts, key) for counts in by_type.values())
                    for key in Counts.__dataclass_fields__
                }
            )
            rows.append({"mode": mode, "type": "micro", **total.scores()})
            rows.append(
                {
                    "mode": mode,
                    "type": "macro",
                    **{key: sum(score[key] for score in scores) / len(scores) for key in scores[0]},
                }
            )
        return rows
