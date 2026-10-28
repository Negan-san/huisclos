"""Textes de l'interface : fusion des dictionnaires par module et fonction t().

Entrées : les dictionnaires EN (obligatoire) et FR (facultatif) de chaque module du paquet.
Sorties : t(clé, **valeurs), qui renvoie le texte dans la langue de la session.
Place dans le pipeline : tous les textes affichés par app/ passent par t(), jamais en dur.
"""

import os

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from app.i18n import common, evaluation, method, method_glossary, method_guide, mistral, workflow

# Variable d'environnement qui rend une clé absente fatale. Les tests la définissent pour
# qu'une faute de frappe dans une clé échoue au lieu de s'afficher à l'écran.
STRICT_ENV = "HUISCLOS_I18N_STRICT"
DEFAULT_LANGUAGE = "en"
LANGUAGE_KEY = "language"
_MODULES = (common, workflow, method, method_guide, method_glossary, evaluation, mistral)


def _merge(attribute: str) -> dict[str, str]:
    """Fusionne le dictionnaire nommé de chaque module et refuse les clés en double."""
    merged: dict[str, str] = {}
    for module in _MODULES:
        for key, text in getattr(module, attribute, {}).items():
            if key in merged:
                raise ValueError(f"clé de texte en double : {key}")
            merged[key] = text
    return merged


EN: dict[str, str] = _merge("EN")
FR: dict[str, str] = _merge("FR")


def current_language() -> str:
    """Renvoie la langue de la session en cours, ou l'anglais hors d'une session Streamlit."""
    # Lire st.session_state hors d'une exécution de script émet un avertissement : on
    # regarde d'abord s'il existe un contexte d'exécution.
    if get_script_run_ctx() is None:
        return DEFAULT_LANGUAGE
    return st.session_state.get(LANGUAGE_KEY, DEFAULT_LANGUAGE)


def t(key: str, **values: object) -> str:
    """Renvoie le texte de l'interface associé à une clé.

    Paramètres : key, la clé (par exemple "import.detect.button") ; values, les valeurs qui
    remplacent les champs {nom} du texte.
    Valeur retournée : le texte français si la langue est fr et qu'il existe, sinon le texte
    anglais. Une clé absente lève KeyError quand HUISCLOS_I18N_STRICT est défini ; sinon la
    clé elle-même est affichée, pour qu'une erreur de texte ne bloque pas l'application.
    """
    text = FR.get(key) if current_language() == "fr" else None
    if text is None:
        text = EN.get(key)
    if text is None:
        if os.environ.get(STRICT_ENV):
            raise KeyError(key)
        return key
    return text.format(**values) if values else text
