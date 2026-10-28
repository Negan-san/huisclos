"""Tests des profils Standard et Enhanced, de la langue du document et des résultats périmés.

Entrées : textes fictifs français et anglais, cache local du modèle simulé ou réel.
Sorties : profils par langue, refus clairs sans téléchargement ni repli silencieux, empreintes
complètes, AppTest des deux langues d'interface croisées avec les deux langues de document,
mode de démonstration publique et révocation des résultats après un changement de réglage.
"""

import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest
import spacy.util
from streamlit.testing.v1 import AppTest

from app import i18n
from app.fingerprints import detection_signature
from huisclos.config import (
    CAMEMBERT_REPO,
    CAMEMBERT_REVISION,
    PRESETS,
    profile_config,
    profile_unavailable,
)
from huisclos.detection import camembert, pipeline
from huisclos.detection.pipeline import ModelUnavailableError, detect, model_identity
from huisclos.models import EntityType
from huisclos.pseudonymize.tokens import pseudonymize

APP_PATH = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
TIMEOUT = 120
FRENCH = "M. Pierre VERNOLAC écrit à Mme Hélène QUISTRAL au sujet du contrat."
ENGLISH = "Mr John HARTWELL wrote to Ms Emily CARRAWAY about the lease of the warehouse."
EXPECTED = {
    "fr": "M. [PERSONNE_1] écrit à Mme [PERSONNE_2] au sujet du contrat.",
    "en": "Mr [PERSONNE_1] wrote to Ms [PERSONNE_2] about the lease of the warehouse.",
}
needs_english = pytest.mark.skipif(
    not spacy.util.is_package("en_core_web_sm"), reason="modèle anglais du venv A1 absent"
)


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente ; démonstration publique désactivée."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def test_profiles_by_document_language() -> None:
    standard_fr = profile_config("standard", "fr")
    assert standard_fr == PRESETS["hybrid"]
    standard_en = profile_config("standard", "en")
    assert (standard_en.document_language, standard_en.spacy_model) == ("en", "en_core_web_sm")
    assert not standard_en.use_camembert
    enhanced = profile_config("enhanced", "fr")
    assert enhanced == PRESETS["hybrid_camembert"]
    assert enhanced.use_patterns and enhanced.use_spacy and enhanced.use_propagation
    enhanced_en = profile_config("enhanced", "en")
    assert enhanced_en.use_gliner and not enhanced_en.use_camembert
    assert enhanced_en.gliner_threshold == 0.70


@pytest.mark.parametrize(
    "profile, language, demo, reason",
    [
        ("enhanced", "en", False, None),
        ("enhanced", "fr", True, "public_demo"),
        ("gliner", "fr", False, "unknown"),
        ("standard", "en", True, None),
        ("enhanced", "fr", False, None),
    ],
)
def test_unavailable_profiles_are_refused_without_fallback(
    profile: str, language: str, demo: bool, reason: str | None
) -> None:
    assert profile_unavailable(profile, language, demo) == reason
    if reason is not None:
        with pytest.raises(ValueError):
            profile_config(profile, language, demo)


def test_model_identity_names_language_model_and_revision() -> None:
    standard = model_identity(PRESETS["hybrid"])
    assert standard.startswith("fr;spacy=fr_core_news_md==")
    enhanced = model_identity(PRESETS["hybrid_camembert"])
    assert enhanced.endswith(f"camembert={CAMEMBERT_REPO}@{CAMEMBERT_REVISION}")
    assert model_identity(profile_config("standard", "en")).startswith("en;spacy=en_core_web_sm")
    assert CAMEMBERT_REPO == camembert.MODEL_NAME


def test_signature_covers_every_setting_and_the_table() -> None:
    base = PRESETS["hybrid"]
    reference = detection_signature(FRENCH, base)
    assert detection_signature(FRENCH, replace(base)) == reference
    table = pseudonymize(FRENCH, detect(FRENCH, base)).mapping
    variants = [
        detection_signature(FRENCH + " ", base),
        detection_signature(FRENCH, replace(base, threshold=0.5)),
        detection_signature(FRENCH, replace(base, enabled_types=frozenset({EntityType.EMAIL}))),
        detection_signature(FRENCH, replace(base, document_language="en")),
        detection_signature(FRENCH, PRESETS["hybrid_camembert"]),
        detection_signature(FRENCH, base, table),
    ]
    assert reference not in variants
    assert len(set(variants)) == len(variants)


def fake_cache(paths: dict[tuple[str, str | None], str | None]):
    """Faux try_to_load_from_cache : chemin par (fichier, révision), None sinon."""

    def lookup(repo_id: str, filename: str, revision: str | None = None) -> str | None:
        assert repo_id == CAMEMBERT_REPO
        return paths.get((filename, revision))

    return lookup


def complete_cache(revision: str = CAMEMBERT_REVISION) -> dict[tuple[str, str | None], str]:
    """Cache simulé complet : chaque fichier de la révision, et "main" qui la désigne."""
    paths: dict[tuple[str, str | None], str] = {}
    for name in pipeline.CAMEMBERT_FILES:
        paths[(name, CAMEMBERT_REVISION)] = f"/cache/snapshots/{CAMEMBERT_REVISION}/{name}"
        paths[(name, None)] = f"/cache/snapshots/{revision}/{name}"
    return paths


def test_snapshot_check_never_downloads_and_explains(
    monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    if importlib.util.find_spec("huggingface_hub") is None:
        pytest.skip("option locale absente")
    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "try_to_load_from_cache", fake_cache(complete_cache()))
    assert pipeline.check_camembert_snapshot().endswith(CAMEMBERT_REVISION)
    missing = complete_cache()
    del missing[("sentencepiece.bpe.model", CAMEMBERT_REVISION)]
    monkeypatch.setattr(huggingface_hub, "try_to_load_from_cache", fake_cache(missing))
    with pytest.raises(ModelUnavailableError) as caught:
        pipeline.check_camembert_snapshot()
    assert caught.value.code == "missing"
    other = fake_cache(complete_cache("0" * 40))
    monkeypatch.setattr(huggingface_hub, "try_to_load_from_cache", other)
    with pytest.raises(ModelUnavailableError) as caught:
        pipeline.check_camembert_snapshot()
    assert caught.value.code == "revision"
    monkeypatch.setattr(pipeline.importlib.util, "find_spec", lambda name: None)
    with pytest.raises(ModelUnavailableError) as caught:
        pipeline.check_camembert_snapshot()
    assert caught.value.code == "dependency"


def test_missing_model_stops_before_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent() -> str:
        raise ModelUnavailableError("missing")

    loaded: list[str] = []
    monkeypatch.setattr(pipeline, "check_camembert_snapshot", absent)
    monkeypatch.setattr(pipeline.importlib, "import_module", loaded.append)
    with pytest.raises(ModelUnavailableError):
        pipeline._camembert_recognizers("fr")
    assert loaded == []
    with pytest.raises(ValueError):
        pipeline._camembert_recognizers("en")


def test_public_demo_refuses_the_heavy_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.engine import prepare_engine

    monkeypatch.setenv("HUISCLOS_PUBLIC_DEMO", "true")
    with pytest.raises(ModelUnavailableError) as caught:
        prepare_engine(PRESETS["hybrid_camembert"])
    assert caught.value.code == "public_demo"


@needs_english
def test_standard_english_profile_detects_with_the_a1_model() -> None:
    config = profile_config("standard", "en")
    found = {(d.text, d.entity_type) for d in detect(ENGLISH, config)}
    assert ("John HARTWELL", EntityType.PERSON) in found
    assert ("Emily CARRAWAY", EntityType.PERSON) in found


def journey(ui: str, document: str, text: str) -> AppTest:
    """Parcours complet : Import et Restore dans la langue d'interface ui.

    Review passe par l'anglais : son filtre de types (review_step.py) formate ses libellés
    hors du contexte du script, ce qu'AppTest ne sait pas relire en français.
    """
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.selectbox(key="language").select(ui).run()
    app.radio(key="document_language").set_value(document).run()
    app.text_area(key="paste_widget").set_value(text).run()
    assert not app.exception
    app.selectbox(key="language").select("en").run()
    app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    app.button(key="review_pseudonymize").click().run()
    app.selectbox(key="language").select(ui).run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
    return app


@needs_english
@pytest.mark.parametrize("ui", ["en", "fr"])
@pytest.mark.parametrize("document", ["fr", "en"])
def test_ui_language_and_document_language_are_independent(ui: str, document: str) -> None:
    text = FRENCH if document == "fr" else ENGLISH
    app = journey(ui, document, text)
    result = app.session_state["pseudo_result"]
    # Les jetons suivent leur propre réglage (français par défaut), jamais l'interface.
    assert result.text.count("[PERSONNE_") == 2
    assert app.session_state["document_language"] == document
    clear = {"en": "No residual identifier found.", "fr": "Aucun identifiant résiduel trouvé."}
    assert clear[ui] in [item.value for item in app.success]
    # Même texte attendu quelle que soit la langue de l'interface : jetons stables.
    assert result.text == EXPECTED[document]


def test_sample_case_stays_a_french_document_in_an_english_ui() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.radio(key="document_language").set_value("en").run()
    app.button(key="load_sample").click().run()
    assert not app.exception
    assert app.session_state["document_language"] == "fr"
    assert any("French document" in item.value for item in app.info)


@pytest.mark.parametrize("profile, document", [("enhanced", "fr"), ("enhanced", "en")])
def test_public_demo_ignores_an_old_heavy_session_value(
    monkeypatch: pytest.MonkeyPatch, profile: str, document: str
) -> None:
    # La valeur ancienne est choisie hors démonstration, puis la démonstration est activée.
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.radio(key="detection_profile").set_value(profile).run()
    monkeypatch.setenv("HUISCLOS_PUBLIC_DEMO", "true")
    app.radio(key="document_language").set_value(document).run()
    assert not app.exception
    assert not app.session_state["detection_profile"] == "enhanced"
    assert app.session_state["detection_profile"] == "standard"
    assert app.radio(key="detection_profile").options == ["Standard"]
    assert any("not available on the public demo" in item.value for item in app.sidebar.warning)


def test_enhanced_profile_remains_selected_for_an_english_document() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.radio(key="detection_profile").set_value("enhanced").run()
    app.radio(key="document_language").set_value("en").run()
    assert app.session_state["detection_profile"] == "enhanced"
    assert any("experimental" in item.value for item in app.sidebar.caption)


def test_missing_enhanced_model_shows_a_clear_error_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.engine import _cached_analyzer

    def absent() -> str:
        raise ModelUnavailableError("missing")

    monkeypatch.setattr(pipeline, "check_camembert_snapshot", absent)
    pipeline.build_analyzer.cache_clear()
    _cached_analyzer.clear()
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.radio(key="detection_profile").set_value("enhanced").run()
    app.text_area(key="paste_widget").set_value(FRENCH).run()
    app.button(key="detect").click().run()
    assert not app.exception
    assert app.session_state["step"] == "import"
    assert app.session_state["detections"] is None
    assert any("not in the local cache" in item.value for item in app.error)
    _cached_analyzer.clear()


def test_changed_setting_revokes_review_and_check_but_keeps_the_source() -> None:
    app = journey("en", "fr", FRENCH)
    assert app.get("download_button")[0].disabled is False
    app.slider(key="threshold").set_value(0.6).run()
    assert not app.exception
    assert any("no longer checked" in item.value for item in app.warning)
    assert app.get("download_button")[0].disabled is True
    app.button(key="check_stale_back").click().run()
    assert app.session_state["step"] == "import"
    assert any("Run the detection again" in item.value for item in app.warning)
    assert app.session_state["source_text"] == FRENCH
    app.button(key="detect").click().run()
    # La nouvelle détection repart sans décision ni résultat : rien n'est accepté d'office.
    assert app.session_state["step"] == "review"
    assert app.session_state["pseudo_result"] is None
    assert app.session_state["group_decisions"] == {}
    assert app.session_state["outbound_send_authorization"] is None


def test_missing_english_backend_stops_without_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une option GLiNER absente refuse la détection et conserve le profil choisi."""
    from huisclos.detection import gliner

    def absent() -> None:
        """Simule un paquet local incomplet avant tout chargement lourd."""
        raise ModelUnavailableError("local_missing")

    monkeypatch.setattr(gliner, "prepare", absent)
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.radio(key="document_language").set_value("en").run()
    app.radio(key="detection_profile").set_value("enhanced").run()
    app.text_area(key="paste_widget").set_value(ENGLISH).run()
    app.button(key="detect").click().run()
    assert not app.exception
    assert app.session_state["step"] == "import"
    assert app.session_state["detections"] is None
    assert app.session_state["detection_profile"] == "enhanced"
    assert any("GLiNER package is missing" in item.value for item in app.error)


def test_method_and_evaluation_pages_state_the_supported_languages() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app = app.switch_page("app/pages/method.py").run()
    assert "Document languages" in [item.value for item in app.main.subheader]
    method = " ".join(item.value for item in app.main.markdown)
    assert "French and English documents" in method
    assert "bilingual blind validation is pending G8" in method
    app = app.switch_page("app/pages/evaluation.py").run()
    assert not app.exception
    assert any("historical measures on French documents" in item.value for item in app.info)
