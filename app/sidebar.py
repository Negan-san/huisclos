"""Barre latérale : document, détection, style des jetons, langue et remise à zéro.

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
    KEY_DOCUMENT_LANGUAGE,
    KEY_ENABLED_TYPES,
    KEY_LANGUAGE,
    KEY_LANGUAGE_NOTICE,
    KEY_PROFILE,
    KEY_PROFILE_NOTICE,
    KEY_THRESHOLD,
    KEY_TOKEN_STYLE,
    THRESHOLD_MAX,
    THRESHOLD_MIN,
    THRESHOLD_STEP,
    reset_state,
)
from app.ui_common import entity_label, is_public_demo
from huisclos.config import (
    PROFILE_ENHANCED,
    PROFILE_STANDARD,
    PROFILES,
    DetectionConfig,
    profile_config,
    profile_unavailable,
)
from huisclos.detection.languages import DOCUMENT_LANGUAGES
from huisclos.models import EntityType

# L'anglais reste le choix initial ; les deux dictionnaires sont complets.
LANGUAGES = ("en", "fr")
AVAILABLE_LANGUAGES = LANGUAGES
TOKEN_STYLES = ("fr", "en")


def document_language() -> str:
    """Langue du document choisie dans la barre latérale (fr par défaut), jamais celle de l'UI."""
    language = st.session_state.get(KEY_DOCUMENT_LANGUAGE, DOCUMENT_LANGUAGES[0])
    return language if language in DOCUMENT_LANGUAGES else DOCUMENT_LANGUAGES[0]


def selected_profile() -> str:
    """Profil réellement utilisé : celui choisi s'il est disponible ici, sinon Standard.

    Une valeur de session ancienne ne peut pas imposer le modèle lourd sur la démonstration
    publique ni pour un document anglais ; la barre latérale l'affiche (_check_profile).
    """
    profile = st.session_state.get(KEY_PROFILE, PROFILE_STANDARD)
    if profile_unavailable(profile, document_language(), is_public_demo()) is None:
        return profile
    return PROFILE_STANDARD


def build_config() -> DetectionConfig:
    """Construit la configuration de détection choisie dans la barre latérale.

    Le point de départ est le profil (Standard = "hybrid", Enhanced = "hybrid_camembert")
    dans la langue du document ; les types activés et le seuil viennent des réglages.
    """
    return replace(
        profile_config(selected_profile(), document_language(), is_public_demo()),
        enabled_types=frozenset(st.session_state[KEY_ENABLED_TYPES]),
        threshold=round(float(st.session_state[KEY_THRESHOLD]), 2),
    )


def available_profiles() -> tuple[str, ...]:
    """Profils proposés pour la langue du document, hors modèle lourd en démonstration."""
    return tuple(
        profile
        for profile in PROFILES
        if profile_unavailable(profile, document_language(), is_public_demo()) is None
    )


def _check_profile() -> None:
    """Ramène à Standard un profil indisponible ici, et garde la raison pour l'afficher."""
    profile = st.session_state.get(KEY_PROFILE, PROFILE_STANDARD)
    reason = profile_unavailable(profile, document_language(), is_public_demo())
    if reason is not None:
        st.session_state[KEY_PROFILE] = PROFILE_STANDARD
        st.session_state[KEY_PROFILE_NOTICE] = reason


def _clear_profile_notice() -> None:
    """Rappel du choix de profil : un choix explicite remplace l'avis précédent."""
    st.session_state[KEY_PROFILE_NOTICE] = None


def _keep_available_language() -> None:
    """Rappel du choix de langue : garde les réglages choisis, revient à l'anglais au besoin.

    Le navigateur désigne les choix d'une liste par leur libellé affiché. Quand la langue
    change, un libellé traduit ne correspond plus à aucune option et le choix serait perdu :
    tous les types sauf IBAN, SIREN et SIRET, donc les noms laissés en clair. Réécrire ces
    valeurs depuis le serveur les renvoie au navigateur avec les nouveaux libellés.
    """
    st.session_state[KEY_ENABLED_TYPES] = list(st.session_state[KEY_ENABLED_TYPES])
    st.session_state[KEY_TOKEN_STYLE] = st.session_state[KEY_TOKEN_STYLE]
    st.session_state[KEY_DOCUMENT_LANGUAGE] = document_language()
    st.session_state[KEY_PROFILE] = st.session_state[KEY_PROFILE]
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


def _render_document_settings() -> None:
    """Groupe Document : langue du document et profil de détection, distincts de l'interface.

    Le profil Enhanced n'est proposé que là où il fonctionne : document français, installation
    locale. Il se charge au premier usage, jamais à l'ouverture de la page.
    """
    _check_profile()
    language_labels = {code: t(f"sidebar.document_language.{code}") for code in DOCUMENT_LANGUAGES}
    profile_labels = {profile: t(f"sidebar.profile.{profile}") for profile in PROFILES}
    _group("sidebar.group.document")
    st.radio(
        t("sidebar.document_language"),
        options=DOCUMENT_LANGUAGES,
        format_func=language_labels.__getitem__,
        help=t("sidebar.document_language.help"),
        key=KEY_DOCUMENT_LANGUAGE,
        on_change=_check_profile,
    )
    st.radio(
        t("sidebar.profile"),
        options=available_profiles(),
        format_func=profile_labels.__getitem__,
        help=t("sidebar.profile.help"),
        key=KEY_PROFILE,
        on_change=_clear_profile_notice,
    )
    reason = st.session_state.get(KEY_PROFILE_NOTICE)
    if reason is not None:
        st.warning(t(f"sidebar.profile.notice.{reason}"))
    elif is_public_demo():
        st.caption(t("sidebar.profile.demo"))
    elif selected_profile() == PROFILE_ENHANCED:
        st.caption(t("sidebar.profile.french_only"))


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
        _render_document_settings()
        _render_detection_settings()
        _render_display_settings()
        st.divider()
        _render_reset()
