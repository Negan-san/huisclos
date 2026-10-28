"""Carte "Final check" de l'étape Restore : identifiants restés en clair dans le texte à envoyer.

Entrées : pseudo_result, les décisions de l'étape Review et la configuration de la barre
latérale.
Sorties : la carte affichée ; "Mask everywhere" ajoute la valeur comme entité manuelle,
relance la pseudonymisation et remplace pseudo_result.
Place dans le pipeline : entre pseudonymize.tokens et l'envoi au LLM (D-S24-3).
"""

from dataclasses import replace

import streamlit as st

from app.components.highlight import render_highlighted
from app.engine import prepare_engine
from app.i18n import t
from app.sidebar import build_config
from app.state import (
    KEY_DETECTIONS,
    KEY_PSEUDO_RESULT,
    KEY_RESTORE_RESULT,
    KEY_SOURCE_TEXT,
)
from app.steps.review_decisions import (
    add_manual,
    current_detections,
    is_masked,
    pseudonymize_session,
)
from app.steps.review_step import KEY_TABLE_VERSION
from app.ui_common import literal_markdown
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, PseudonymizationResult, Source
from huisclos.pseudonymize.final_check import check_threshold, excerpt, final_check
from huisclos.pseudonymize.mapping import sha256_of

# Résultat du contrôle, (empreinte des entrées, restes), pour ne pas refaire la détection à
# chaque affichage ; dernier masquage, (empreinte du texte, valeur, occurrences ajoutées).
KEY_CHECK = "final_check"
KEY_CHECK_NOTICE = "final_check_notice"


def _rejected() -> tuple[list[str], list[tuple[int, int]]]:
    """Écritures et positions rejetées en revue, qui ne doivent déclencher aucune alerte."""
    if st.session_state.get(KEY_DETECTIONS) is None:
        return [], []
    rejected = [d for d in current_detections() if not is_masked(d)]
    return [d.text for d in rejected], [(d.start, d.end) for d in rejected]


def _can_mask() -> bool:
    """Le masquage relance la pseudonymisation : il faut le texte et les détections."""
    return st.session_state.get(KEY_DETECTIONS) is not None and bool(
        st.session_state.get(KEY_SOURCE_TEXT)
    )


def residuals(result: PseudonymizationResult) -> list[Detection] | None:
    """Restes du texte pseudonymisé, recalculés seulement si une entrée a changé.

    Valeur retournée : la liste, vide si rien n'est trouvé, ou None si le moteur de
    détection n'a pas pu démarrer.
    """
    config = build_config()
    values, spans = _rejected()
    kinds = sorted(kind.value for kind in config.enabled_types)
    signature = sha256_of(f"{result.text}\0{config.threshold}\0{kinds}\0{values}\0{spans}")
    cached = st.session_state.get(KEY_CHECK)
    if cached is not None and cached[0] == signature:
        return cached[1]
    lowered = replace(config, threshold=check_threshold(config.threshold))
    try:
        with st.spinner(t("check.spinner")):
            prepare_engine(lowered)
            found = final_check(result, lambda text: detect(text, lowered), values, spans)
    except RuntimeError:
        return None
    st.session_state[KEY_CHECK] = (signature, found)
    return found


def _on_mask(value: str, kind: EntityType) -> None:
    """Rappel de "Mask everywhere" : ajoute la valeur partout, puis pseudonymise à nouveau."""
    added, _ = add_manual(st.session_state[KEY_SOURCE_TEXT], value, kind)
    try:
        result = pseudonymize_session()
    except ValueError:
        st.session_state[KEY_CHECK_NOTICE] = ("", value, -1)
        return
    st.session_state[KEY_PSEUDO_RESULT] = result
    st.session_state[KEY_RESTORE_RESULT] = None
    # Le tableau de Review repart des nouvelles décisions, comme après un ajout manuel.
    st.session_state[KEY_TABLE_VERSION] = st.session_state.get(KEY_TABLE_VERSION, 0) + 1
    st.session_state[KEY_CHECK_NOTICE] = (sha256_of(result.text), value, added)


def _render_notice(result: PseudonymizationResult) -> None:
    """Affiche le résultat du dernier masquage, s'il concerne le texte affiché."""
    notice = st.session_state.get(KEY_CHECK_NOTICE)
    if notice is None:
        return
    signature, value, added = notice
    if added < 0:
        st.error(t("check.mask.error"))
    elif signature == sha256_of(result.text):
        st.success(t("check.mask.done", value=literal_markdown(value), count=added))


def _render_residual(index: int, text: str, residual: Detection, can_mask: bool) -> None:
    """Affiche un reste : extrait surligné, origine de l'alerte et bouton de masquage."""
    piece, local = excerpt(text, residual)
    with st.container(key=f"hc-check-item-{index}", border=True):
        st.html(render_highlighted(piece, [local], {}))
        origin = "table" if residual.source is Source.CASE_TABLE else "detection"
        st.caption(t(f"check.origin.{origin}"))
        if can_mask:
            st.button(
                t("check.mask"),
                key=f"check_mask_{index}",
                on_click=_on_mask,
                args=(residual.text, residual.entity_type),
                icon=":material/visibility_off:",
            )


def render_final_check(result: PseudonymizationResult) -> None:
    """Carte du contrôle final : alertes à traiter, ou aucun reste, sans promettre l'anonymat."""
    with st.container(key="hc-card-check"):
        st.subheader(t("check.heading"), anchor=False)
        st.caption(t("check.intro"))
        _render_notice(result)
        found = residuals(result)
        if found is None:
            st.error(t("check.error"))
            return
        if not found:
            st.success(t("check.clear"), icon=":material/task_alt:")
            st.caption(t("check.clear.note"))
            return
        st.warning(t("check.found", count=len(found)), icon=":material/report:")
        can_mask = _can_mask()
        for index, residual in enumerate(found):
            _render_residual(index, result.text, residual, can_mask)
        if not can_mask:
            st.caption(t("check.mask.unavailable"))
