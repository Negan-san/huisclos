"""Point d'entrée de l'application HuisClos.

Ajoute la racine du dépôt et src/ au chemin d'import, charge la feuille de style locale,
affiche l'en-tête et la barre latérale, puis lance la navigation entre les trois pages :
Pseudonymize (le parcours Import, Review, Restore), Evaluation et Method & limits.
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.i18n import t  # noqa: E402  (le chemin d'import doit être complété avant)
from app.sidebar import render_sidebar  # noqa: E402
from app.state import init_state  # noqa: E402
from app.ui_common import inject_style, render_header  # noqa: E402


def main() -> None:
    """Prépare la page puis exécute la page choisie dans la navigation.

    La navigation est placée en haut de page : la barre latérale ne garde que les réglages.
    Sur un écran étroit, Streamlit replie lui-même ces liens dans un menu.
    """
    st.set_page_config(page_title=t("app.title"), page_icon=":material/lock:", layout="wide")
    inject_style()
    init_state()
    pages = [
        st.Page(
            "app/pages/workflow.py",
            title=t("nav.pseudonymize"),
            icon=":material/shield_lock:",
            default=True,
        ),
        st.Page(
            "app/pages/evaluation.py",
            title=t("nav.evaluation"),
            icon=":material/monitoring:",
            url_path="evaluation",
        ),
        st.Page(
            "app/pages/method.py",
            title=t("nav.method"),
            icon=":material/menu_book:",
            url_path="method",
        ),
    ]
    navigation = st.navigation(pages, position="top")
    render_header()
    render_sidebar()
    navigation.run()


main()
