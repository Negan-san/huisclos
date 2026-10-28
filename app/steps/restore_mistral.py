"""Envoi facultatif du message contrôlé à Mistral, depuis l'étape Restore.

Entrées : le contrôle du contenu sortant (message exact, statut, empreinte) et la clé
MISTRAL_API_KEY (secret ou variable d'environnement).
Sorties : la réponse reçue, placée dans llm_response pour la zone de restauration.
Place dans le pipeline : seul appel réseau de l'application, désactivé sans clé et soumis à
une confirmation explicite de l'empreinte du contenu (D-17, D-AF-A3-4).
"""

import os

import streamlit as st

from app.i18n import t
from app.state import KEY_LLM_RESPONSE, KEY_RESTORE_RESULT, KEY_SEND_AUTH
from app.steps.restore_check import CheckOutcome
from huisclos.llm.mistral_client import DEFAULT_MODEL, MistralError, send_outbound
from huisclos.pseudonymize.outbound_check import may_send

# Clé de la zone de réponse de l'étape Restore : elle est retirée pour être réalimentée.
KEY_ANSWER_WIDGET = "restore_answer"
KEY_CONFIRM = "mistral_confirm"


def _api_key() -> str | None:
    """Renvoie la clé Mistral configurée, ou None si aucune clé utilisable n'existe."""
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = None
    api_key = api_key or os.environ.get("MISTRAL_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        return None
    return api_key


def _on_confirm(fingerprint: str) -> None:
    """Rappel de la case de confirmation : l'autorisation porte sur cette empreinte seule."""
    st.session_state[KEY_SEND_AUTH] = fingerprint if st.session_state.get(KEY_CONFIRM) else None


def _send(outcome: CheckOutcome, api_key: str) -> None:
    """Envoie le message si l'autorisation vaut pour son empreinte actuelle, sinon refuse.

    La garde est refaite ici, au clic, avec l'état recalculé dans cette exécution : l'état
    désactivé du bouton ne suffit pas. Le transport reçoit exactement message.content.
    """
    if not may_send(st.session_state.get(KEY_SEND_AUTH), outcome.fingerprint, outcome.status):
        st.session_state[KEY_SEND_AUTH] = None
        st.error(t("mistral.refused"))
        return
    try:
        with st.spinner(t("mistral.spinner")):
            answer = send_outbound(outcome.message.content, api_key, DEFAULT_MODEL)
    except MistralError as error:
        st.error(t(f"mistral.error.{error.code}"))
        return
    # Une confirmation vaut pour un envoi : un nouvel envoi en demande une autre.
    st.session_state[KEY_SEND_AUTH] = None
    st.session_state[KEY_LLM_RESPONSE] = answer
    # La zone de réponse a déjà été créée plus haut dans cette exécution.
    st.session_state.pop(KEY_ANSWER_WIDGET, None)
    st.session_state[KEY_RESTORE_RESULT] = None
    st.rerun()


def render_mistral_slot(outcome: CheckOutcome) -> None:
    """Affiche l'envoi facultatif du message contrôlé, si une clé est configurée.

    La confirmation porte sur l'empreinte du contenu et de tous ses paramètres ; une
    modification la révoque. La réponse remplit la zone de restauration au prochain affichage.
    """
    api_key = _api_key()
    if api_key is None:
        return
    authorized = st.session_state.get(KEY_SEND_AUTH)
    if not outcome.ready or authorized != outcome.fingerprint:
        # Avant la création de la case : une confirmation ancienne ne reste jamais cochée.
        st.session_state[KEY_CONFIRM] = False
        st.session_state[KEY_SEND_AUTH] = None
    with st.container(key="hc-card-mistral"):
        st.subheader(t("mistral.heading"), anchor=False)
        st.warning(t("mistral.warning"))
        st.caption(t("mistral.content"))
        if not outcome.ready:
            st.info(t("mistral.not_ready"))
        st.checkbox(
            t("mistral.confirm"),
            key=KEY_CONFIRM,
            disabled=not outcome.ready,
            on_change=_on_confirm,
            args=(outcome.fingerprint,),
        )
        # Le bouton ne dépend que du statut : sans confirmation valable, la garde de _send
        # refuse le clic et le dit, au lieu de compter sur un bouton désactivé.
        clicked = st.button(
            t("mistral.send"),
            key="mistral_send",
            disabled=not outcome.ready,
            icon=":material/send:",
        )
    if clicked:
        _send(outcome, api_key)
