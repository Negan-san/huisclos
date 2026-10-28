"""Tests de la charte : jetons de couleur lisibles, thème aligné, aucune ressource externe.

Entrées : app/assets/style.css, .streamlit/config.toml et le HTML produit par l'application
sur tout le parcours du cas fictif.
Sorties : assertions de contraste (WCAG AA) et d'absence de ressource distante.
"""

import re
import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT / "streamlit_app.py")
STYLE = (ROOT / "app" / "assets" / "style.css").read_text(encoding="utf-8")
THEME = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]
TOKENS = dict(re.findall(r"--hc-([\w-]+): (#[0-9A-Fa-f]{6});", STYLE))
EXTERNAL = re.compile(r"https?://|url\(|@import|//[a-z0-9.-]+\.[a-z]{2,}/", re.IGNORECASE)

# Couples texte et fond réellement utilisés : 4,5:1 au moins (texte normal, WCAG AA).
TEXT_PAIRS = [
    (text, background)
    for text in ("ink", "muted", "primary", "accent", "success", "warning", "error")
    for background in ("bg", "card", "surface")
] + [
    ("primary", "primary-soft"),
    ("accent", "accent-soft"),
    ("success", "success-soft"),
    ("warning", "warning-soft"),
    ("error", "error-soft"),
    ("card", "primary"),
]
# Bordures des composants et pastilles d'étape : 3:1 au moins (composants, WCAG AA).
COMPONENT_PAIRS = [("border-strong", "card"), ("primary", "card"), ("accent", "card")]


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def luminance(color: str) -> float:
    """Luminance relative WCAG d'une couleur #RRGGBB."""
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first: str, second: str) -> float:
    """Rapport de contraste WCAG entre deux couleurs."""
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@pytest.mark.parametrize(("text", "background"), TEXT_PAIRS)
def test_text_tokens_reach_aa_contrast(text: str, background: str) -> None:
    assert contrast(TOKENS[text], TOKENS[background]) >= 4.5


@pytest.mark.parametrize(("component", "background"), COMPONENT_PAIRS)
def test_component_tokens_reach_three_to_one(component: str, background: str) -> None:
    assert contrast(TOKENS[component], TOKENS[background]) >= 3


def test_theme_uses_the_same_colors_as_the_tokens() -> None:
    assert THEME["primaryColor"] == TOKENS["primary"]
    assert THEME["backgroundColor"] == TOKENS["bg"]
    assert THEME["secondaryBackgroundColor"] == TOKENS["surface"]
    assert THEME["textColor"] == TOKENS["ink"]
    assert THEME["borderColor"] == TOKENS["border-strong"]
    assert THEME["linkColor"] == TOKENS["accent"]
    assert THEME["redColor"] == TOKENS["error"]
    assert THEME["greenColor"] == TOKENS["success"]
    assert THEME["yellowColor"] == TOKENS["warning"]


def test_theme_and_style_load_nothing_from_the_network() -> None:
    assert not EXTERNAL.search(STYLE)
    for value in THEME.values():
        assert not EXTERNAL.search(str(value)), value
    # Une police nommée dans le thème doit être une police du système, sans adresse.
    assert "sans-serif" in THEME["font"]
    assert "fontFaces" not in THEME


def collected_markup(app: AppTest) -> list[str]:
    """Rassemble le HTML et le Markdown affichés, feuille de style injectée comprise."""
    elements = [*app.get("html"), *app.markdown, *app.caption]
    return [str(element.value) for element in elements]


def test_rendered_pages_contain_no_external_resource() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=120).run()
    seen = collected_markup(app)
    app.button(key="load_sample").click().run()
    app.button(key="detect").click().run()
    seen += collected_markup(app)
    app.button(key="review_pseudonymize").click().run()
    result = app.session_state["pseudo_result"]
    app.text_area(key="restore_answer").set_value(result.text)
    app.button(key="restore_run").click().run()
    seen += collected_markup(app)
    for page in ("app/pages/evaluation.py", "app/pages/method.py"):
        app.switch_page(page).run()
        assert not app.exception
        seen += collected_markup(app)
    assert any("--hc-primary" in block for block in seen)
    assert any('class="hc-stepper"' in block for block in seen)
    offences = [block[:80] for block in seen if EXTERNAL.search(block)]
    assert offences == []
