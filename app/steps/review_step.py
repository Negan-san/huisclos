"""Étape Review : l'humain décide ce qui est masqué, puis lance la pseudonymisation.

Entrées : detections, source_text et les décisions dans l'état de session ; le style de
jetons de la barre latérale.
Sorties : group_decisions (une décision par mention), manual_entities (valeurs ajoutées à la
main), puis pseudo_result et le passage à l'étape Restore.
Place dans le pipeline : entre la détection et pseudonymize.tokens ; c'est l'étape où
l'humain garde la main.
"""

from dataclasses import replace

import streamlit as st

from app.components.entity_table import (
    Row,
    column_names,
    edited_groups,
    group_rows,
    table_config,
    table_height,
)
from app.components.highlight import render_highlighted, render_legend
from app.components.review_summary import LOW_CONFIDENCE, review_counts, type_rows
from app.i18n import t
from app.state import (
    KEY_DETECTIONS,
    KEY_PSEUDO_RESULT,
    KEY_RESTORE_RESULT,
    KEY_SIGNATURE,
    KEY_SOURCE_TEXT,
    KEY_TABLE_ERROR,
    KEY_UPLOADED_TABLE,
    STEP_IMPORT,
    STEP_RESTORE,
    go_to,
)
from app.steps.review_decisions import (
    Decision,
    add_manual,
    current_detections,
    decisions,
    is_masked,
    pseudonymize_session,
)
from app.ui_common import entity_label
from huisclos.models import Detection, EntityGroup, EntityType
from huisclos.pseudonymize.grouping import group_mentions

# Clés propres à cet écran. Le numéro de version fait partie de la clé du tableau : il
# change après chaque modification, ce qui donne un tableau neuf (voir _commit_change).
KEY_TABLE_VERSION = "review_table_version"
TABLE_KEY_PREFIX = "review_table_"
KEY_FILTER = "review_filter"
KEY_MANUAL_TEXT = "review_manual_text"
KEY_MANUAL_TYPE = "review_manual_type"
KEY_MANUAL_NOTICE = "review_manual_notice"
TEXT_HEIGHT = 480


def _bump_table() -> None:
    """Change la clé du tableau, donc repart d'un éditeur sans modification en attente."""
    st.session_state[KEY_TABLE_VERSION] = st.session_state.get(KEY_TABLE_VERSION, 0) + 1


def _commit_change() -> None:
    """Enregistre qu'une décision a changé : tableau neuf, résultats périmés effacés.

    Sans cela, les modifications en attente de l'éditeur, repérées par numéro de ligne,
    s'appliqueraient à des lignes devenues différentes après un nouveau regroupement. La
    pseudonymisation déjà faite ne correspond plus aux décisions : elle est retirée.
    """
    _bump_table()
    st.session_state[KEY_PSEUDO_RESULT] = None
    st.session_state[KEY_RESTORE_RESULT] = None


def _apply_edits(groups: list[EntityGroup], before: list[Row], after: list[Row]) -> bool:
    """Reporte sur toutes les mentions d'un groupe les cases et types modifiés dans le tableau.

    Valeur retournée : vrai si au moins une décision a changé.
    """
    changed = edited_groups(groups, before, after)
    for group, changes in changed:
        for span in group.mention_spans:
            decisions()[span] = replace(decisions().get(span, Decision()), **changes)
    return bool(changed)


def _render_metrics(groups: list[EntityGroup], detections: list[Detection]) -> None:
    """Affiche la rangée de cartes d'indicateurs : entités, occurrences, types, confiance."""
    counts = review_counts(groups, detections, is_masked)
    cards = (
        ("review.counts.groups", counts.entities, ":material/category:", None),
        ("review.counts.masked", counts.masked, ":material/visibility_off:", None),
        ("review.counts.rejected", counts.rejected, ":material/visibility:", None),
        ("review.counts.types", counts.types, ":material/label:", None),
        (
            "review.counts.low",
            counts.low_confidence,
            ":material/priority_high:",
            t("review.counts.low.help", score=f"{LOW_CONFIDENCE:.2f}"),
        ),
    )
    with st.container(key="hc-metrics"):
        for column, (key, value, icon, help_text) in zip(
            st.columns(len(cards)), cards, strict=True
        ):
            column.metric(t(key), value, icon=icon, help=help_text, border=True)


def _render_text(text: str, detections: list[Detection]) -> None:
    """Affiche le texte surligné comme une page de document, avec sa légende compacte."""
    with st.container(key="hc-card-text"):
        st.subheader(t("review.text.heading"), anchor=False)
        st.html(render_legend(detections))
        flags = {span: decision.masked for span, decision in decisions().items()}
        with st.container(height=TEXT_HEIGHT, key="hc-document"):
            st.html(render_highlighted(text, detections, flags))


def _render_side(detections: list[Detection], groups: list[EntityGroup]) -> None:
    """Panneau à droite du texte : résumé et décompte des occurrences par type."""
    with st.container(key="hc-card-types"):
        st.subheader(t("review.counts.heading"), anchor=False)
        st.caption(t("review.summary", count=len(detections), groups=len(groups)))
        rows = type_rows(detections, is_masked)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch", height=table_height(len(rows)))


def _render_table(groups: list[EntityGroup], detections: list[Detection]) -> None:
    """Affiche le tableau de décision et applique les modifications de l'humain.

    Quand une ligne change, les décisions sont mises à jour puis la page est relancée : le
    tableau, le texte surligné et les compteurs repartent alors des mêmes décisions.
    """
    with st.container(key="hc-card-table"):
        st.subheader(t("review.table.heading"), anchor=False)
        st.caption(t("review.table.help"))
        present = [kind for kind in EntityType if any(g.entity_type is kind for g in groups)]
        kept = [k for k in st.session_state.get(KEY_FILTER, []) if k in present]
        st.session_state[KEY_FILTER] = kept
        st.multiselect(
            t("review.filter.label"),
            options=present,
            format_func=entity_label,
            key=KEY_FILTER,
            on_change=_bump_table,
        )
        chosen = st.session_state[KEY_FILTER]
        shown = [g for g in groups if not chosen or g.entity_type in chosen]
        if not shown:
            st.info(t("review.table.nothing"), icon=":material/filter_alt_off:")
            return
        names = column_names()
        rows = group_rows(shown, detections, is_masked)
        edited = st.data_editor(
            rows,
            key=f"{TABLE_KEY_PREFIX}{st.session_state.get(KEY_TABLE_VERSION, 0)}",
            hide_index=True,
            width="stretch",
            height=table_height(len(rows)),
            column_order=list(names.values()),
            column_config=table_config(names),
            disabled=[names[c] for c in names if c not in ("mask", "type")],
        )
    if _apply_edits(shown, rows, edited):
        _commit_change()
        st.rerun()


def _manual_label(kind: EntityType) -> str:
    """Libellé d'un type dans la liste d'ajout manuel : CUSTOM se lit "Other identifier"."""
    return t("review.manual.custom") if kind is EntityType.CUSTOM else entity_label(kind)


def _on_add_manual() -> None:
    """Rappel du bouton d'ajout : cherche la valeur, l'ajoute et garde le résultat à afficher."""
    value = st.session_state[KEY_MANUAL_TEXT].strip()
    signature = st.session_state[KEY_SIGNATURE]
    if not value:
        st.session_state[KEY_MANUAL_NOTICE] = (signature, "empty", 0, 0)
        return
    kind = st.session_state[KEY_MANUAL_TYPE]
    added, covered = add_manual(st.session_state[KEY_SOURCE_TEXT], value, kind)
    if added:
        _commit_change()
        st.session_state[KEY_MANUAL_TEXT] = ""
    outcome = "added" if added else ("covered" if covered else "none")
    st.session_state[KEY_MANUAL_NOTICE] = (signature, outcome, added, covered)


def _render_notice() -> None:
    """Affiche le résultat du dernier ajout manuel, sauf s'il date d'un autre document."""
    notice = st.session_state.get(KEY_MANUAL_NOTICE)
    if not notice or notice[0] != st.session_state[KEY_SIGNATURE]:
        return
    _, outcome, added, covered = notice
    if outcome == "added":
        key = "review.manual.added_covered" if covered else "review.manual.added"
        st.success(t(key, count=added, covered=covered))
    elif outcome == "covered":
        st.info(t("review.manual.covered", covered=covered))
    else:
        st.warning(t(f"review.manual.{outcome}"))


def _render_manual() -> None:
    """Affiche le formulaire d'ajout d'une valeur oubliée par la détection, sur une ligne."""
    st.session_state.setdefault(KEY_MANUAL_TYPE, EntityType.CUSTOM)
    with st.container(key="hc-card-manual"):
        st.subheader(t("review.manual.heading"), anchor=False)
        value, kind, action = st.columns([4, 3, 3], vertical_alignment="bottom")
        value.text_input(t("review.manual.text"), key=KEY_MANUAL_TEXT)
        kind.selectbox(
            t("review.manual.type"),
            options=list(EntityType),
            format_func=_manual_label,
            key=KEY_MANUAL_TYPE,
        )
        action.button(
            t("review.manual.button"),
            key="review_add_manual",
            on_click=_on_add_manual,
            icon=":material/add:",
            width="stretch",
        )
        _render_notice()


def _pseudonymize() -> None:
    """Pseudonymise les mentions masquées, garde le résultat et passe à l'étape Restore."""
    try:
        with st.spinner(t("review.pseudonymize.spinner")):
            result = pseudonymize_session()
    except ValueError:
        st.error(t("review.error.pseudonymize"))
        return
    st.session_state[KEY_PSEUDO_RESULT] = result
    st.session_state[KEY_RESTORE_RESULT] = None
    go_to(STEP_RESTORE)
    st.session_state[KEY_UPLOADED_TABLE] = None
    st.session_state[KEY_TABLE_ERROR] = None
    st.rerun()


def _render_actions(detections: list[Detection]) -> None:
    """Barre d'actions : rappel sur la table, retour à Import et bouton Pseudonymize."""
    with st.container(key="hc-card-actions"):
        if not any(is_masked(d) for d in detections):
            st.warning(t("review.nothing_masked"))
        st.caption(f":material/lock: {t('review.pseudonymize.note')}")
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.button(
                t("review.back"),
                key="review_back",
                on_click=go_to,
                args=(STEP_IMPORT,),
                icon=":material/arrow_back:",
            )
            clicked = st.button(
                t("review.pseudonymize"),
                key="review_pseudonymize",
                type="primary",
                icon=":material/arrow_forward:",
                icon_position="right",
            )
    if clicked:
        _pseudonymize()


def render() -> None:
    """Affiche l'étape Review, ou l'état vide quand aucune détection n'a été faite."""
    st.header(t("review.title"), anchor=False)
    if st.session_state[KEY_DETECTIONS] is None:
        st.info(t("review.empty"), icon=":material/inbox:")
        st.button(t("review.back"), key="review_back", on_click=go_to, args=(STEP_IMPORT,))
        return
    text = st.session_state[KEY_SOURCE_TEXT]
    detections = current_detections()
    groups = group_mentions(text, detections)
    st.markdown(t("review.intro"))
    _render_metrics(groups, detections)
    document, side = st.columns([2, 1], gap="medium")
    with document:
        _render_text(text, detections)
    with side:
        _render_side(detections, groups)
    if groups:
        _render_table(groups, detections)
    _render_manual()
    _render_actions(detections)
