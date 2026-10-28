"""Barre latérale : réglages de la détection, style des jetons, langue et remise à zéro.

Entrées : st.session_state, initialisé par app.state.init_state().
Sorties : render_sidebar() affiche les réglages ; build_config() en tire la DetectionConfig
que l'étape Import transmet à detect().
Place dans le pipeline : réglages communs à toutes les pages, lus par l'étape Import.
"""

import html
from dataclasses import replace

import streamlit as st

from app.i18n import t
from app.state import (
    KEY_CONFIRM_RESET,
    KEY_ENABLED_TYPES,
    KEY_LANGUAGE,
    KEY_LANGUAGE_NOTICE,
    KEY_THRESHOLD,
    KEY_TOKEN_STYLE,
    THRESHOLD_MAX,
    THRESHOLD_MIN,
    THRESHOLD_STEP,
    reset_state,
)
from app.ui_common import entity_label
from huisclos.config import PRESETS, DetectionConfig
from huisclos.models import EntityType

# L'anglais reste le choix initial ; les deux dictionnaires sont complets.
LANGUAGES = ("en", "fr")
AVAILABLE_LANGUAGES = LANGUAGES
TOKEN_STYLES = ("fr", "en")


def build_config() -> DetectionConfig:
    """Construit la configuration de détection choisie dans la barre latérale.

    Le point de départ est le préréglage "hybrid", celui de l'interface ; seuls les types
    activés et le seuil changent.
    """
    return replace(
        PRESETS["hybrid"],
        enabled_types=frozenset(st.session_state[KEY_ENABLED_TYPES]),
        threshold=round(float(st.session_state[KEY_THRESHOLD]), 2),
    )


def _keep_available_language() -> None:
    """Rappel du choix de langue : revient à l'anglais si la langue choisie n'existe pas."""
    if st.session_state[KEY_LANGUAGE] not in AVAILABLE_LANGUAGES:
        st.session_state[KEY_LANGUAGE] = AVAILABLE_LANGUAGES[0]
        st.session_state[KEY_LANGUAGE_NOTICE] = True


def _ask_reset() -> None:
    """Rappel du bouton de remise à zéro : demande une confirmation."""
    st.session_state[KEY_CONFIRM_RESET] = True


def _cancel_reset() -> None:
    """Rappel du bouton d'annulation : retire la demande de confirmation."""
    st.session_state[KEY_CONFIRM_RESET] = False


def _render_reset() -> None:
    """Affiche la remise à zéro en action secondaire, puis sa confirmation après un clic."""
    if not st.session_state.get(KEY_CONFIRM_RESET):
        st.button(
            t("sidebar.reset"),
            key="reset_session",
            on_click=_ask_reset,
            icon=":material/restart_alt:",
            width="stretch",
        )
        return
    st.warning(t("sidebar.reset.confirm"))
    yes, cancel = st.columns(2)
    yes.button(t("sidebar.reset.yes"), key="reset_confirm", on_click=reset_state, type="primary")
    cancel.button(t("sidebar.reset.cancel"), key="reset_cancel", on_click=_cancel_reset)


def _group(title_key: str) -> None:
    """Affiche le surtitre d'un groupe de réglages, en petites capitales."""
    st.html(f'<p class="hc-overline">{html.escape(t(title_key))}</p>')


def _render_detection_settings() -> None:
    """Groupe Detection : types à rechercher et seuil de confiance."""
    # Les libellés restent ceux de cet affichage, même hors du contexte du script
    # lors de la sérialisation des composants par AppTest.
    type_labels = {kind: entity_label(kind) for kind in EntityType}
    _group("sidebar.group.detection")
    st.multiselect(
        t("sidebar.types"),
        options=list(EntityType),
        format_func=type_labels.__getitem__,
        key=KEY_ENABLED_TYPES,
    )
    st.slider(
        t("sidebar.threshold"),
        min_value=THRESHOLD_MIN,
        max_value=THRESHOLD_MAX,
        step=THRESHOLD_STEP,
        format="%.2f",
        help=t("sidebar.threshold.help"),
        key=KEY_THRESHOLD,
    )


def _render_display_settings() -> None:
    """Groupes Tokens et Interface : style des jetons et langue de l'interface."""
    token_labels = {style: t(f"sidebar.token_style.{style}") for style in TOKEN_STYLES}
    language_labels = {language: t(f"sidebar.language.{language}") for language in LANGUAGES}
    _group("sidebar.group.tokens")
    st.radio(
        t("sidebar.token_style"),
        options=TOKEN_STYLES,
        format_func=token_labels.__getitem__,
        key=KEY_TOKEN_STYLE,
    )
    _group("sidebar.group.interface")
    st.selectbox(
        t("sidebar.language"),
        options=LANGUAGES,
        format_func=language_labels.__getitem__,
        key=KEY_LANGUAGE,
        on_change=_keep_available_language,
    )
    if st.session_state.get(KEY_LANGUAGE_NOTICE):
        st.caption(t("sidebar.language.notice"))
        st.session_state[KEY_LANGUAGE_NOTICE] = False


def render_sidebar() -> None:
    """Affiche les réglages groupés, une aide courte et la remise à zéro de la session."""
    with st.sidebar:
        st.subheader(t("sidebar.settings"))
        st.caption(t("sidebar.help"))
        _render_detection_settings()
        _render_display_settings()
        st.divider()
        _render_reset()
