"""Étape Restore (squelette) : état vide clair en attendant l'écran de restauration de S33.

Entrées : pseudo_result dans l'état de session.
Sorties : un message et un bouton de retour à l'étape Import.
Place dans le pipeline : troisième étape, après la réponse du LLM.
"""

import streamlit as st

from app.i18n import t
from app.state import STEP_IMPORT, go_to


def render() -> None:
    """Affiche l'étape Restore : pour l'instant, seulement l'état vide."""
    st.header(t("restore.title"))
    st.info(t("restore.empty"))
    st.button(t("restore.back"), key="restore_back", on_click=go_to, args=(STEP_IMPORT,))
