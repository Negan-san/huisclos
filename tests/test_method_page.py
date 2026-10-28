"""Tests de la page Method & limits et de l'accès à la page Evaluation, avec AppTest.

Entrées : l'application complète, lancée sans navigateur, en anglais puis en français.
Sorties : ordre des sections, références juridiques, exemple commenté, lien vers les
résultats détaillés et page Evaluation retirée de la barre de navigation.
Place dans le pipeline : contrôle de présentation, sans détection.
"""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app import i18n
from app.ui_common import ENTITY_STYLES

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT / "streamlit_app.py")
METHOD_PAGE = "app/pages/method.py"
TIMEOUT = 120
SECTIONS = [
    "In short",
    "Pipeline",
    "A worked example",
    "How it works",
    "What leaves your computer, and what does not",
    "Why hybrid AI",
    "Document languages",
    "Technologies used",
    "Human in the loop",
    "What HuisClos looks for",
    "Words used in HuisClos",
    "Legal framework",
    "Limits",
    "Good practices",
    "How we tested it",
]


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def method_page() -> AppTest:
    """Lance l'application puis ouvre la page Method & limits."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    return app.switch_page(METHOD_PAGE).run()


def page_text(app: AppTest) -> str:
    """Rassemble le texte visible de la page : Markdown, légendes, messages et blocs de code."""
    elements = [*app.main.markdown, *app.main.caption, *app.main.info, *app.main.code]
    return " ".join(element.value for element in elements)


def test_method_page_sections_in_reading_order() -> None:
    app = method_page()
    assert not app.exception
    assert len(app.get("graphviz_chart")) == 1
    assert [s.value for s in app.main.subheader] == SECTIONS
    text = page_text(app)
    for reference in ("71-1130", "66-5", "226-13", "4(5)", "recital 26", "5(1)(c)", "Art. 32"):
        assert reference in text
    legend = next(h.value for h in app.get("html") if "hc-legend" in h.value)
    assert all(style.label in legend for style in ENTITY_STYLES.values())


def test_method_page_explains_the_process_in_plain_words() -> None:
    text = page_text(method_page())
    # Exemple commenté : le nom réel figure dans le document et dans la réponse restaurée,
    # jamais dans ce que reçoit l'outil d'IA.
    sent = i18n.EN["method.example.sent"]
    assert "Claire Dumontel" not in sent and "[PERSONNE_1]" in sent
    assert "Claire Dumontel" in i18n.EN["method.example.restored"]
    assert sent in text
    for component in ("Streamlit", "spaCy", "Microsoft Presidio", "CamemBERT", "pypdf"):
        assert component in text
    for word in ("Pseudonymization.", "Anonymization.", "Token.", "Mapping table."):
        assert word in text
    assert "never passes through the AI tool" in text


def test_evaluation_is_hidden_from_navigation_and_linked_from_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list] = []
    real_navigation = st.navigation

    def recording_navigation(pages: list, **options: object) -> object:
        seen.append(list(pages))
        return real_navigation(pages, **options)

    monkeypatch.setattr(st, "navigation", recording_navigation)
    app = method_page()
    assert not app.exception
    visibility = {page.url_path: page.visibility for page in seen[-1]}
    assert visibility == {"": "visible", "evaluation": "hidden", "method": "visible"}
    links = app.get("page_link")
    assert [(link.proto.label, link.proto.page) for link in links] == [
        ("See the detailed results", "evaluation")
    ]
    app.switch_page("app/pages/evaluation.py").run()
    assert not app.exception
    assert app.header[0].value == "Evaluation"


def test_method_page_in_french() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    app.session_state["language"] = "fr"
    app = app.run().switch_page(METHOD_PAGE).run()
    assert not app.exception
    subheaders = [s.value for s in app.main.subheader]
    assert subheaders[0] == "En bref"
    assert subheaders[-1] == "Comment nous l'avons testé"
    assert app.get("page_link")[0].proto.label == "Voir les résultats détaillés"
