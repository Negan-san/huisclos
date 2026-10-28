"""Indicateurs de l'écran Review : entités, occurrences, types et faible confiance.

Entrées : les groupes d'entités, les détections de travail et une fonction qui dit si une
mention est masquée.
Sorties : ReviewCounts (les cinq nombres des cartes) et les lignes du décompte par type.
Place dans le pipeline : étape Review, au-dessus du texte surligné ; aucun état de session
n'est lu ici.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.i18n import t
from app.ui_common import entity_label
from huisclos.models import Detection, EntityGroup, EntityType

# En dessous de ce score, une détection mérite d'être relue en premier : ce sont les noms
# trouvés par la seule forme Prénom NOM, les adresses et les numéros à clé fausse (barème
# D-07). Le seuil de la barre latérale, lui, décide de ce qui est détecté.
LOW_CONFIDENCE = 0.75


@dataclass(frozen=True)
class ReviewCounts:
    """Les nombres des cartes d'indicateurs de l'écran Review."""

    entities: int
    masked: int
    rejected: int
    types: int
    low_confidence: int


def review_counts(
    groups: list[EntityGroup],
    detections: list[Detection],
    is_masked: Callable[[Detection], bool],
) -> ReviewCounts:
    """Calcule les cinq indicateurs ; une occurrence est une mention dans le texte.

    Exemple : deux mentions de "Jean DUPONT", dont une rejetée, donnent une entité, une
    occurrence masquée et une rejetée.
    """
    masked = sum(is_masked(d) for d in detections)
    return ReviewCounts(
        entities=len(groups),
        masked=masked,
        rejected=len(detections) - masked,
        types=len({d.entity_type for d in detections}),
        low_confidence=sum(d.score < LOW_CONFIDENCE for d in detections),
    )


def type_rows(
    detections: list[Detection], is_masked: Callable[[Detection], bool]
) -> list[dict[str, object]]:
    """Construit le décompte par type : occurrences masquées et rejetées, dans l'ordre des types."""
    rows = []
    for kind in EntityType:
        of_kind = [d for d in detections if d.entity_type is kind]
        if of_kind:
            kept = sum(is_masked(d) for d in of_kind)
            rows.append(
                {
                    t("review.counts.type"): entity_label(kind),
                    t("review.counts.type_masked"): kept,
                    t("review.counts.type_rejected"): len(of_kind) - kept,
                }
            )
    return rows
