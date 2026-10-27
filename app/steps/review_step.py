"""Étape Review (squelette) : état vide clair en attendant l'écran de revue de S32.

Entrées : detections dans l'état de session.
Sorties : un message et un bouton de retour à l'étape Import.
Place dans le pipeline : deuxième étape, entre la détection et la pseudonymisation.
"""

import streamlit as st

from app.i18n import t
from app.state import KEY_DETECTIONS, STEP_IMPORT, go_to


def render() -> None:
    """Affiche l'étape Review : le nombre de détections prêtes, ou l'état vide."""
    st.header(t("review.title"))
    detections = st.session_state[KEY_DETECTIONS]
    if detections is None:
        st.info(t("review.empty"))
    else:
        st.info(t("review.placeholder", count=len(detections)))
    st.button(t("review.back"), key="review_back", on_click=go_to, args=(STEP_IMPORT,))
