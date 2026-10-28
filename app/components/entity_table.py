"""Tableau de décision de l'écran Review : une ligne par entité, cases Mask et types.

Entrées : les groupes d'entités, les détections de travail et une fonction qui dit si une
mention est masquée.
Sorties : les lignes à donner à st.data_editor, la configuration des colonnes, et la liste
des groupes que l'humain a modifiés.
Place dans le pipeline : étape Review ; l'étape applique elle-même les changements aux
décisions de la session.
"""

from collections.abc import Callable

import streamlit as st

from app.i18n import t
from app.ui_common import entity_label
from huisclos.models import Detection, EntityGroup, EntityType

COLUMNS = ("mask", "text", "type", "occurrences", "variants", "confidence", "source", "note")
EDITABLE = ("mask", "type")
PREVIEW_VARIANTS = 3
ROW_HEIGHT = 35
MAX_VISIBLE_ROWS = 15

Row = dict[str, object]


def column_names() -> dict[str, str]:
    """Renvoie le titre affiché de chaque colonne du tableau."""
    return {column: t(f"review.column.{column}") for column in COLUMNS}


def variants_preview(variants: tuple[str, ...]) -> str:
    """Résume les variantes d'un groupe : les premières, puis le nombre de celles qui restent."""
    shown = ", ".join(variants[:PREVIEW_VARIANTS])
    hidden = len(variants) - PREVIEW_VARIANTS
    return f"{shown}, {t('review.variants.more', count=hidden)}" if hidden > 0 else shown


def group_rows(
    groups: list[EntityGroup],
    detections: list[Detection],
    is_masked: Callable[[Detection], bool],
) -> list[Row]:
    """Construit une ligne de tableau par groupe, dans l'ordre d'apparition.

    La case Mask n'est cochée que si toutes les mentions du groupe sont masquées ; la
    confiance est le score le plus bas du groupe, celui qui mérite le plus d'attention.
    """
    names = column_names()
    by_span = {(d.start, d.end): d for d in detections}
    rows: list[Row] = []
    for group in groups:
        members = [by_span[span] for span in group.mention_spans]
        rows.append(
            {
                names["mask"]: all(is_masked(d) for d in members),
                names["text"]: group.canonical,
                names["type"]: entity_label(group.entity_type),
                names["occurrences"]: len(members),
                names["variants"]: variants_preview(group.variants),
                names["confidence"]: min(d.score for d in members),
                names["source"]: ", ".join(sorted({d.source.value for d in members})),
                names["note"]: t("review.note.ambiguous") if group.ambiguous_with else "",
            }
        )
    return rows


def table_config(names: dict[str, str]) -> dict[str, object]:
    """Décrit les colonnes : cases, liste de types, nombres formatés, confiance en barre.

    La barre de confiance garde le nombre écrit à côté (format %.2f) : la valeur ne repose
    pas sur la seule longueur de la barre.
    """
    column = st.column_config
    return {
        names["mask"]: column.CheckboxColumn(
            names["mask"], width=72, help=t("review.column.mask.help")
        ),
        names["text"]: column.TextColumn(names["text"], width=176),
        names["type"]: column.SelectboxColumn(
            names["type"],
            options=[entity_label(kind) for kind in EntityType],
            required=True,
            width=148,
            help=t("review.column.type.help"),
        ),
        names["occurrences"]: column.NumberColumn(names["occurrences"], format="%d", width=92),
        names["variants"]: column.TextColumn(names["variants"], width=160),
        names["confidence"]: column.ProgressColumn(
            names["confidence"], format="%.2f", min_value=0.0, max_value=1.0, width=100
        ),
        names["source"]: column.TextColumn(names["source"], width=96),
        names["note"]: column.TextColumn(names["note"], width=144),
    }


def table_height(row_count: int) -> int:
    """Hauteur du tableau en pixels : toutes les lignes jusqu'à quinze, puis défilement."""
    return (min(row_count, MAX_VISIBLE_ROWS) + 1) * ROW_HEIGHT + 3


def edited_groups(
    groups: list[EntityGroup], before: list[Row], after: list[Row]
) -> list[tuple[EntityGroup, dict[str, object]]]:
    """Compare les lignes envoyées à l'éditeur et celles qu'il renvoie.

    Valeur retournée : pour chaque groupe modifié, les champs de décision qui changent
    ("masked" et, si le nouveau type est connu, "entity_type"). Les colonnes en lecture
    seule sont ignorées.
    """
    names = column_names()
    kinds = {entity_label(kind): kind for kind in EntityType}
    changed: list[tuple[EntityGroup, dict[str, object]]] = []
    for group, old, new in zip(groups, before, after, strict=True):
        changes: dict[str, object] = {}
        if new[names["mask"]] != old[names["mask"]]:
            changes["masked"] = bool(new[names["mask"]])
        if new[names["type"]] != old[names["type"]] and new[names["type"]] in kinds:
            changes["entity_type"] = kinds[str(new[names["type"]])]
        if changes:
            changed.append((group, changes))
    return changed
