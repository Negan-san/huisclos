"""Envoi facultatif du texte pseudonymisé à Mistral, depuis l'étape Restore.

Entrées : le texte pseudonymisé, la clé MISTRAL_API_KEY (secret ou variable d'environnement)
et la consigne saisie par l'utilisateur.
Sorties : la réponse reçue, placée dans llm_response pour la zone de restauration.
Place dans le pipeline : seul appel réseau de l'application, désactivé sans clé et soumis à
une confirmation explicite (D-17).
"""

import os

import streamlit as st

from app.i18n import t
from app.state import KEY_LLM_RESPONSE, KEY_RESTORE_RESULT
from huisclos.llm.mistral_client import DEFAULT_MODEL, MistralError, send_pseudonymized
from huisclos.pseudonymize.mapping import sha256_of

# Clé de la zone de réponse de l'étape Restore : elle est retirée pour être réalimentée.
KEY_ANSWER_WIDGET = "restore_answer"


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


def render_mistral_slot(pseudonymized_text: str) -> None:
    """Affiche l'envoi facultatif du seul texte fourni, si une clé est configurée.

    La confirmation porte sur ce texte et cette consigne ; une modification la révoque.
    La réponse remplit la zone de restauration au prochain affichage.
    """
    api_key = _api_key()
    if api_key is None:
        return
    with st.container(key="hc-card-mistral"):
        st.subheader(t("mistral.heading"), anchor=False)
        st.warning(t("mistral.warning"))
        instruction = st.text_area(t("mistral.instruction"), key="mistral_instruction")
        signature = sha256_of(pseudonymized_text + "\0" + instruction)
        if st.session_state.get("mistral_signature") != signature:
            st.session_state["mistral_confirm"] = False
            st.session_state["mistral_signature"] = signature
        confirmed = st.checkbox(t("mistral.confirm"), value=False, key="mistral_confirm")
        clicked = st.button(
            t("mistral.send"),
            key="mistral_send",
            disabled=not confirmed,
            icon=":material/send:",
        )
    if clicked and confirmed:
        try:
            with st.spinner(t("mistral.spinner")):
                answer = send_pseudonymized(pseudonymized_text, instruction, api_key, DEFAULT_MODEL)
        except MistralError as error:
            st.error(t(f"mistral.error.{error.code}"))
        else:
            st.session_state[KEY_LLM_RESPONSE] = answer
            # La zone de réponse a déjà été créée plus haut dans cette exécution.
            st.session_state.pop(KEY_ANSWER_WIDGET, None)
            st.session_state[KEY_RESTORE_RESULT] = None
            st.rerun()
