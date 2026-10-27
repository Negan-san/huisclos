"""Barre latérale : réglages de la détection, style des jetons, langue et remise à zéro.

Entrées : st.session_state, initialisé par app.state.init_state().
Sorties : render_sidebar() affiche les réglages ; build_config() en tire la DetectionConfig
que l'étape Import transmet à detect().
Place dans le pipeline : réglages communs à toutes les pages, lus par l'étape Import.
"""

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

# Langues proposées et langues réellement disponibles : le français s'affiche mais reste
# inactif tant que les chaînes françaises de app/i18n n'existent pas.
LANGUAGES = ("en", "fr")
AVAILABLE_LANGUAGES = ("en",)
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
    """Affiche le bouton de remise à zéro, puis sa confirmation quand il a été cliqué."""
    if not st.session_state.get(KEY_CONFIRM_RESET):
        st.button(t("sidebar.reset"), key="reset_session", on_click=_ask_reset)
        return
    st.warning(t("sidebar.reset.confirm"))
    yes, cancel = st.columns(2)
    yes.button(t("sidebar.reset.yes"), key="reset_confirm", on_click=reset_state, type="primary")
    cancel.button(t("sidebar.reset.cancel"), key="reset_cancel", on_click=_cancel_reset)


def render_sidebar() -> None:
    """Affiche les réglages : types, seuil, style des jetons, langue et remise à zéro."""
    with st.sidebar:
        st.subheader(t("sidebar.settings"))
        st.multiselect(
            t("sidebar.types"),
            options=list(EntityType),
            format_func=entity_label,
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
        st.radio(
            t("sidebar.token_style"),
            options=TOKEN_STYLES,
            format_func=lambda style: t(f"sidebar.token_style.{style}"),
            key=KEY_TOKEN_STYLE,
        )
        st.selectbox(
            t("sidebar.language"),
            options=LANGUAGES,
            format_func=lambda language: t(f"sidebar.language.{language}"),
            key=KEY_LANGUAGE,
            on_change=_keep_available_language,
        )
        if st.session_state.get(KEY_LANGUAGE_NOTICE):
            st.caption(t("sidebar.language.notice"))
            st.session_state[KEY_LANGUAGE_NOTICE] = False
        _render_reset()
