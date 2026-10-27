"""Page Evaluation (squelette) : titre et message d'attente.

Entrées : aucune pour l'instant ; la session S43 affichera les résultats de results/.
Sorties : un titre et un message.
Place dans le pipeline : page de mesure, hors du parcours Import, Review, Restore.
"""

import streamlit as st

from app.i18n import t


def render() -> None:
    """Affiche le titre de la page et le message d'attente."""
    st.header(t("evaluation.title"))
    st.info(t("evaluation.placeholder"))


render()
