"""Point d'entrée de l'application HuisClos.

Ajoute src/ au chemin d'import, charge la feuille de style locale et affiche la page
d'accueil minimale avec les trois étapes du parcours : Import, Review, Restore.
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

STYLE_PATH = ROOT / "app" / "assets" / "style.css"
TAGLINE = "Use generative AI on client files without breaching professional secrecy."
STEPS = ("Import", "Review", "Restore")
LEGAL_NOTE = "Pseudonymization is not anonymization (GDPR art. 4(5), recital 26)."


def load_style() -> None:
    """Injecte la feuille de style locale dans la page."""
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def main() -> None:
    """Affiche la page d'accueil : titre, accroche, étapes en attente et mention légale."""
    st.set_page_config(page_title="HuisClos", layout="wide")
    load_style()
    st.title("HuisClos")
    st.write(TAGLINE)
    columns = st.columns(len(STEPS))
    for number, (column, step) in enumerate(zip(columns, STEPS, strict=True), start=1):
        column.subheader(f"{number}. {step}")
        column.caption("Waiting for the previous step.")
    st.caption(LEGAL_NOTE)


main()
