"""Vérifie les traductions et le changement de langue de l'interface.

Entrées : tous les modules de textes et une session Streamlit simulée.
Sorties : parité des clés, des paramètres et affichage français contrôlés.
Place dans le pipeline : contrôle local de présentation, sans détection.
"""

import importlib
from pathlib import Path
from string import Formatter

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n

MODULE_NAMES = [path.stem for path in Path("app/i18n").glob("*.py")]


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_translation_keys_and_fields(name: str) -> None:
    """Vérifie chaque module : mêmes clés, mêmes champs et aucun texte vide."""
    module = importlib.import_module(f"app.i18n.{name}")
    assert module.FR.keys() == module.EN.keys()
    for key in module.EN:
        assert module.FR[key].strip(), key
        english = {field for _, field, _, _ in Formatter().parse(module.EN[key]) if field}
        french = {field for _, field, _, _ in Formatter().parse(module.FR[key]) if field}
        assert english == french, key


def test_english_default_and_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """L'anglais reste le défaut et les clés manquantes échouent en mode strict."""
    assert i18n.DEFAULT_LANGUAGE == "en"
    monkeypatch.setattr(i18n, "current_language", lambda: "en")
    assert i18n.t("import.title") == "Import a document"
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    with pytest.raises(KeyError):
        i18n.t("missing.test.key")


def test_sidebar_switches_language() -> None:
    """Le vrai sélecteur traduit la barre et le parcours, puis revient en anglais."""
    app = AppTest.from_string(
        "from app.state import init_state\n"
        "from app.sidebar import render_sidebar\n"
        "from app.i18n import t\n"
        "import streamlit as st\n"
        "init_state()\n"
        "render_sidebar()\n"
        "st.header(t('import.title'))\n"
        "st.caption(t('app.legal_note'))\n"
    ).run()
    assert not app.exception
    assert app.header[0].value == "Import a document"
    app.selectbox(key="language").select("fr").run()
    assert not app.exception
    assert app.session_state["language"] == "fr"
    assert app.header[0].value == "Importer un document"
    assert app.sidebar.subheader[0].value == "Réglages"
    assert any("n'est pas une anonymisation" in item.value for item in app.caption)
    app.selectbox(key="language").select("en").run()
    assert not app.exception
    assert app.header[0].value == "Import a document"


def test_main_app_in_french() -> None:
    """La vraie application affiche Import en français après le choix latéral."""
    app = AppTest.from_file(Path("streamlit_app.py").resolve(), default_timeout=15).run()
    assert not app.exception
    app.selectbox(key="language").select("fr").run()
    assert not app.exception
    assert any(header.value == "Importer un document" for header in app.header)
