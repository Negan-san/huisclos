"""Classe les erreurs exactes du split de développement.

Entrées : documents dev et prédictions locales déjà calculées.
Sorties : erreurs FN et FP avec catégorie et contexte limité à trente caractères.
Place dans le pipeline : diagnostic dev seulement, après la mesure.
"""

from collections.abc import Sequence
from typing import Any

from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.evaluation.metrics import evaluated_predictions, evaluated_references, match_entities
from huisclos.models import Detection


def dev_errors(
    documents: Sequence[CorpusDocument], predictions: Sequence[Sequence[Detection]]
) -> list[dict[str, Any]]:
    """Exporte les FN et FP exacts de dev, avec trente caractères de chaque côté.

    Un décalage de borne produit un FN et un FP, même si le partiel est correct.
    Le contrôle du split empêche tout export accidentel du jeu test.
    """
    if len(documents) != len(predictions) or any(document.split != "dev" for document in documents):
        raise ValueError("Les erreurs sont réservées aux documents dev appariés.")
    errors = []
    for document, detected in zip(documents, predictions, strict=True):
        references = evaluated_references(document.entities)
        detected = evaluated_predictions(detected)
        pairs = match_entities(references, detected, "exact")
        matched_references = {reference_index for reference_index, _ in pairs}
        matched_predictions = {prediction_index for _, prediction_index in pairs}
        for nature, entities, matched, counterparts in (
            (
                "FN",
                references,
                matched_references,
                [item for index, item in enumerate(detected) if index not in matched_predictions],
            ),
            (
                "FP",
                detected,
                matched_predictions,
                [item for index, item in enumerate(references) if index not in matched_references],
            ),
        ):
            for index, entity in enumerate(entities):
                if index in matched:
                    continue
                kind = entity.type if nature == "FN" else entity.entity_type
                errors.append(
                    {
                        "document_id": document.id,
                        "type": kind.value,
                        "text": document.text[entity.start : entity.end],
                        "context_before": document.text[max(0, entity.start - 30) : entity.start],
                        "context_after": document.text[entity.end : entity.end + 30],
                        "nature": nature,
                        "category": error_category(entity, counterparts, nature),
                    }
                )
    return errors


def error_category(
    entity: GoldEntity | Detection, counterparts: Sequence[GoldEntity | Detection], nature: str
) -> str:
    """Classe un span non apparié : type en priorité, puis bornes, sinon absence ou ajout.

    Seuls les autres spans non appariés sont examinés. Une erreur de bornes ou de type
    peut donc compter deux lignes exactes, une FN et une FP, sans inventer un appariement.
    """
    kind = entity.type if isinstance(entity, GoldEntity) else entity.entity_type
    overlaps = [
        other for other in counterparts if other.end > entity.start and other.start < entity.end
    ]
    if any(
        (other.type if isinstance(other, GoldEntity) else other.entity_type) != kind
        for other in overlaps
    ):
        return "type_confusion"
    if overlaps:
        return "boundary"
    return "missed" if nature == "FN" else "extra"
