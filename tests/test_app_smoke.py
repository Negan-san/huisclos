"""Tests de l'interface avec AppTest, sans navigateur : navigation, Import, barre latérale."""

import ast
import re
import time
from pathlib import Path
from typing import get_args

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app import i18n
from app.i18n import t
from app.sidebar import AVAILABLE_LANGUAGES, LANGUAGES, TOKEN_STYLES
from app.state import STEPS
from app.steps import import_step
from app.ui_common import ENTITY_STYLES, entity_badge_html, is_public_demo
from huisclos.config import PRESETS, default_threshold
from huisclos.io.readers import ErrorCode
from huisclos.models import EntityType

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT / "streamlit_app.py")
APP_DIR = ROOT / "app"
STYLE = (APP_DIR / "assets" / "style.css").read_text(encoding="utf-8")
TIMEOUT = 120

# Méthodes d'affichage dont le texte doit venir de app/i18n et non d'une chaîne en dur.
TEXT_METHODS = {
    "title",
    "header",
    "subheader",
    "caption",
    "markdown",
    "write",
    "button",
    "info",
    "warning",
    "error",
    "success",
    "text_area",
    "file_uploader",
    "multiselect",
    "slider",
    "radio",
    "selectbox",
    "spinner",
    "tabs",
    "graphviz_chart",
}
TEXT_KEYWORDS = {"help", "placeholder", "alt", "page_title", "label", "title"}


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def start() -> AppTest:
    """Lance l'application et renvoie l'AppTest après sa première exécution."""
    return AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()


def texts(app: AppTest) -> list[str]:
    """Rassemble les textes visibles de la page : Markdown, légendes, titres et messages."""
    elements = [*app.markdown, *app.caption, *app.header, *app.subheader, *app.info, *app.error]
    return [element.value for element in [*elements, *app.warning]]


def load_sample(app: AppTest) -> AppTest:
    """Clique sur "Load sample case"."""
    return app.button(key="load_sample").click().run()


def test_app_starts_with_header_and_steps() -> None:
    app = start()
    assert not app.exception
    assert app.title[0].value == "HuisClos"
    page = texts(app)
    assert any("Use generative AI on client files" in text for text in page)
    assert any("Pseudonymization is not anonymization" in text for text in page)
    steps = app.get("html")[0].value
    assert "1. Import <span" in steps
    assert "(current step)" in steps
    assert 'aria-current="step"' in steps
    assert "Available once sensitive data has been detected." in steps
    assert "Available once the pseudonymized text has been created." in steps


@pytest.mark.parametrize(
    ("page", "header", "expected"),
    [
        ("app/pages/workflow.py", "Import a document", "Processing happens on this computer."),
        ("app/pages/evaluation.py", "Evaluation", "Configuration comparison"),
        ("app/pages/method.py", "Method & limits", "Decision-support tool, not legal advice."),
    ],
)
def test_three_pages_render(page: str, header: str, expected: str) -> None:
    app = start()
    if page != "app/pages/workflow.py":
        app = app.switch_page(page).run()
    assert not app.exception
    assert app.header[0].value == header
    assert any(expected in text for text in texts(app))


def test_method_page_content() -> None:
    app = start().switch_page("app/pages/method.py").run()
    assert not app.exception
    assert len(app.get("graphviz_chart")) == 1
    assert [s.value for s in app.subheader if s.value != "Settings"] == [
        "Pipeline",
        "How it works",
        "Why hybrid AI",
        "Human in the loop",
        "What HuisClos looks for",
        "Legal framework",
        "Limits",
    ]
    page = " ".join(texts(app))
    for reference in ("71-1130", "66-5", "226-13", "4(5)", "recital 26", "5(1)(c)", "Art. 32"):
        assert reference in page
    legend = next(h.value for h in app.get("html") if "hc-legend" in h.value)
    assert all(style.label in legend for style in ENTITY_STYLES.values())


def test_load_sample_case_fills_the_text() -> None:
    app = load_sample(start())
    assert not app.exception
    assert app.session_state["source_text"].startswith("Note de dossier")
    assert app.session_state["source_name"] == "demo_case_fr.txt"
    assert app.text_area[0].value == app.session_state["source_text"]
    assert any("fictitious case" in text for text in texts(app))


def test_detect_on_sample_goes_to_review_quickly() -> None:
    # Le chargement du modèle de langue n'entre pas dans la mesure.
    import_step.detect("M. Pierre VERNOLAC", PRESETS["hybrid"])
    app = load_sample(start())
    started = time.perf_counter()
    app = app.button(key="detect").click().run()
    elapsed = time.perf_counter() - started
    assert not app.exception
    assert elapsed < 5
    assert len(app.session_state["detections"]) >= 1
    assert app.session_state["step"] == "review"
    steps = app.get("html")[0].value
    assert "2. Review <span" in steps
    assert "(current step)" in steps
    assert any("detections are ready" in text for text in texts(app))


def test_detection_is_recomputed_only_when_the_input_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []
    real_detect = import_step.detect

    def counting_detect(text: str, config: object) -> list:
        calls.append(len(text))
        return real_detect(text, config)

    monkeypatch.setattr(import_step, "detect", counting_detect)
    app = load_sample(start())
    app = app.button(key="detect").click().run()
    assert len(calls) == 1
    app = app.button(key="review_back").click().run()
    app = app.button(key="detect").click().run()
    assert len(calls) == 1
    app = app.button(key="review_back").click().run()
    app.sidebar.slider(key="threshold").set_value(0.6).run()
    app = app.button(key="detect").click().run()
    assert len(calls) == 2
    assert not app.exception


def test_detect_without_text_shows_an_error() -> None:
    app = start().button(key="detect").click().run()
    assert app.session_state["step"] == "import"
    assert any("There is no text to process" in error.value for error in app.error)


def test_detect_is_disabled_without_any_type() -> None:
    app = start()
    app.sidebar.multiselect(key="enabled_types").set_value([]).run()
    assert app.button(key="detect").disabled
    assert any("Select at least one type" in warning.value for warning in app.warning)


def test_upload_reads_a_text_file() -> None:
    app = start()
    app.file_uploader[0].upload("note.txt", "Mme Rose PETIT habite à Lyon.".encode()).run()
    assert not app.exception
    assert app.session_state["source_text"] == "Mme Rose PETIT habite à Lyon."
    assert app.session_state["source_name"] == "note.txt"


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("vide.txt", b"", "There is no text to process"),
        ("faux.docx", b"pas un docx", "This Word file cannot be read"),
        ("faux.pdf", b"pas un pdf", "This PDF cannot be read"),
    ],
)
def test_upload_errors_are_explained(filename: str, content: bytes, message: str) -> None:
    app = start()
    app.file_uploader[0].upload(filename, content).run()
    assert not app.exception
    assert any(message in error.value for error in app.error)
    assert app.session_state["source_text"] == ""


def test_cp1252_file_is_read_with_a_warning() -> None:
    app = start()
    app.file_uploader[0].upload("ancien.txt", "Café à Nîmes".encode("cp1252")).run()
    assert app.session_state["source_text"] == "Café à Nîmes"
    assert any("Windows-1252" in warning.value for warning in app.warning)


def test_sidebar_defaults() -> None:
    app = start()
    assert app.sidebar.slider(key="threshold").value == default_threshold()
    assert app.sidebar.slider(key="threshold").min == 0.30
    assert app.sidebar.slider(key="threshold").max == 0.95
    assert app.sidebar.slider(key="threshold").step == 0.05
    assert EntityType.LOCATION not in app.sidebar.multiselect(key="enabled_types").value
    assert len(app.sidebar.multiselect(key="enabled_types").value) == len(EntityType) - 1
    assert app.sidebar.radio(key="token_style").value == "fr"
    assert app.sidebar.selectbox(key="language").value == "en"


def test_french_interface_is_not_available_yet() -> None:
    app = start()
    app.sidebar.selectbox(key="language").select("fr").run()
    assert app.session_state["language"] == "en"
    assert any("not available yet" in caption.value for caption in app.sidebar.caption)


@pytest.mark.parametrize(
    ("value", "expected"), [("true", True), ("TRUE", True), ("false", False), ("", False)]
)
def test_public_demo_banner_follows_the_environment(
    monkeypatch: pytest.MonkeyPatch, value: str, expected: bool
) -> None:
    monkeypatch.setenv("HUISCLOS_PUBLIC_DEMO", value)
    app = start()
    assert not app.exception
    banners = [w.value for w in app.warning if w.value.startswith("Public demo")]
    assert bool(banners) is expected
    if expected:
        assert "use fictitious data only" in banners[0]
        assert "install HuisClos on your computer (see the user guide)" in banners[0]


def test_no_banner_without_the_variable() -> None:
    assert not [w for w in start().warning if "Public demo" in w.value]


class _Secrets:
    """Remplace st.secrets : renvoie une valeur ou lève l'exception d'un fichier absent."""

    def __init__(self, value: object = None, error: Exception | None = None) -> None:
        self.value = value
        self.error = error

    def get(self, key: str) -> object:
        if self.error:
            raise self.error
        return self.value


def test_secrets_never_break_the_banner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(st, "secrets", _Secrets(error=FileNotFoundError("secrets.toml")))
    assert is_public_demo() is False
    monkeypatch.setattr(st, "secrets", _Secrets(value="true"))
    assert is_public_demo() is True
    monkeypatch.setattr(st, "secrets", _Secrets(value=None))
    assert is_public_demo() is False


def test_reset_session_asks_for_confirmation_then_clears_the_state() -> None:
    app = load_sample(start())
    app = app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    app = app.sidebar.button(key="reset_session").click().run()
    assert any("clears the text" in warning.value for warning in app.sidebar.warning)
    assert app.session_state["detections"] is not None
    app = app.sidebar.button(key="reset_confirm").click().run()
    assert not app.exception
    assert app.session_state["source_text"] == ""
    assert app.session_state["source_name"] == ""
    assert app.session_state["detections"] is None
    assert app.session_state["detection_signature"] is None
    assert app.session_state["step"] == "import"
    assert app.session_state["group_decisions"] == {}
    assert app.session_state["manual_entities"] == []
    assert app.text_area[0].value == ""
    assert "Reset session" in [b.label for b in app.sidebar.button]


def test_reset_can_be_cancelled() -> None:
    app = load_sample(start())
    app = app.sidebar.button(key="reset_session").click().run()
    app = app.sidebar.button(key="reset_cancel").click().run()
    assert app.session_state["source_text"] != ""
    assert "Reset session" in [b.label for b in app.sidebar.button]


def i18n_keys_used_in_code() -> tuple[set[str], set[str]]:
    """Relève les clés écrites en dur dans app/ et les préfixes des clés construites."""
    literal_keys: set[str] = set()
    prefixes: set[str] = set()
    namespaces = {key.split(".")[0] for key in i18n.EN}
    pattern = re.compile(rf"^(?:{'|'.join(sorted(namespaces))})\.[\w.]+$")
    for path in APP_DIR.rglob("*.py"):
        if "i18n" in path.parts:
            continue
        nodes = list(ast.walk(ast.parse(path.read_text(encoding="utf-8"))))
        # Les morceaux d'une f-string sont des préfixes de clé, pas des clés complètes.
        pieces = {id(p) for n in nodes if isinstance(n, ast.JoinedStr) for p in n.values}
        for node in nodes:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) not in pieces and pattern.match(node.value):
                    literal_keys.add(node.value)
            elif isinstance(node, ast.JoinedStr):
                first = node.values[0] if node.values else None
                if isinstance(first, ast.Constant) and pattern.match(first.value + "x"):
                    prefixes.add(first.value)
    return literal_keys, prefixes


def test_every_i18n_key_used_in_code_exists_in_english() -> None:
    literal_keys, prefixes = i18n_keys_used_in_code()
    assert literal_keys
    assert {key for key in literal_keys if key not in i18n.EN} == set()
    for prefix in prefixes:
        assert any(key.startswith(prefix) for key in i18n.EN), prefix


def test_dynamic_i18n_keys_are_complete() -> None:
    for code in get_args(ErrorCode):
        assert f"import.error.{code}" in i18n.EN, code
    for key in ("import.error.sample_missing", "import.error.engine"):
        assert key in i18n.EN
    assert "import.warning.encoding_cp1252" in i18n.EN
    for kind in EntityType:
        assert f"entity.{kind.value}" in i18n.EN
    for step in STEPS:
        assert f"steps.{step}" in i18n.EN
    for step in ("review", "restore"):
        assert f"steps.locked.{step}" in i18n.EN
    for style in TOKEN_STYLES:
        assert f"sidebar.token_style.{style}" in i18n.EN
    for language in LANGUAGES:
        assert f"sidebar.language.{language}" in i18n.EN
    assert set(AVAILABLE_LANGUAGES) == {"en"}


def test_missing_key_raises_in_tests_and_shows_the_key_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(KeyError):
        t("no.such.key")
    monkeypatch.delenv(i18n.STRICT_ENV)
    assert t("no.such.key") == "no.such.key"
    assert t("import.upload.loaded", name="a.txt") == "Loaded a.txt."


def test_no_ui_string_is_written_outside_i18n() -> None:
    offences = []
    for path in [*APP_DIR.rglob("*.py"), ROOT / "streamlit_app.py"]:
        if "i18n" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            checked = list(node.args[:1]) if name in TEXT_METHODS else []
            checked += [kw.value for kw in node.keywords if kw.arg in TEXT_KEYWORDS]
            for value in checked:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    offences.append(f"{path.name}:{node.lineno}: {value.value!r}")
    assert offences == []


def luminance(color: str) -> float:
    """Luminance relative WCAG d'une couleur #RRGGBB."""
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first: str, second: str) -> float:
    """Rapport de contraste WCAG entre deux couleurs."""
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_entity_styles_cover_every_type_with_readable_contrast() -> None:
    assert set(ENTITY_STYLES) == set(EntityType)
    for kind, style in ENTITY_STYLES.items():
        assert contrast("#1B1F24", style.color) >= 4.5, kind
        assert style.label
    assert ENTITY_STYLES[EntityType.PERSON].color == "#DCE8F7"
    assert ENTITY_STYLES[EntityType.SIREN].color == ENTITY_STYLES[EntityType.SIRET].color


def test_palette_and_muted_text_are_readable() -> None:
    assert "--hc-ink: #1B1F24" in STYLE
    assert "--hc-primary: #1F3A5F" in STYLE
    assert "--hc-surface: #F4F5F7" in STYLE
    muted = re.search(r"--hc-muted: (#[0-9A-Fa-f]{6})", STYLE)
    assert muted
    assert contrast(muted.group(1), "#FFFFFF") >= 4.5
    assert contrast("#1F3A5F", "#FFFFFF") >= 4.5


def test_css_has_no_external_resource_gradient_or_off_grid_spacing() -> None:
    lowered = STYLE.lower()
    for forbidden in ("http", "url(", "@import", "gradient"):
        assert forbidden not in lowered
    for declaration in re.findall(r"(?:padding|margin|gap)[\w-]*:\s*([^;]+);", STYLE):
        for pixels in re.findall(r"(\d+)px", declaration):
            assert int(pixels) % 8 == 0, declaration


def test_entity_badge_shows_a_text_label() -> None:
    badge = entity_badge_html(EntityType.NIR)
    assert 'class="hc-badge hc-hl-NIR"' in badge
    assert "Social security number (NIR)" in badge
