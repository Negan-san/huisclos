"""Page Pseudonymize : indicateur d'étapes puis étape courante (Import, Review, Restore).

Entrées : l'étape courante, lue dans l'état de session (clé step).
Sorties : l'affichage de l'étape ; les étapes écrivent leurs résultats dans l'état.
Place dans le pipeline : page par défaut de l'application, appelée par st.navigation.
"""

import streamlit as st

from app.state import KEY_STEP, STEP_IMPORT, STEP_RESTORE, STEP_REVIEW
from app.steps import import_step, restore_step, review_step
from app.ui_common import render_steps

RENDERERS = {
    STEP_IMPORT: import_step.render,
    STEP_REVIEW: review_step.render,
    STEP_RESTORE: restore_step.render,
}


def render() -> None:
    """Affiche l'indicateur d'étapes puis l'étape courante."""
    step = st.session_state[KEY_STEP]
    render_steps(step)
    RENDERERS[step]()


render()
