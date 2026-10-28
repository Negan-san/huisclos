"""Recontrôle indépendant de FIX4 sur des valeurs entièrement fictives.

Entrées : parcours AppTest réels, deux langues et deux classes de panne.
Sorties : assertions sur l'invalidation, la revue conservée et la restauration.
Les sondes du worker utilisent les mêmes modèles locaux que la mesure.
"""

import logging
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.steps.restore_step import ActiveTable
from app.steps.review_decisions import Decision
from huisclos.models import EntityType, TokenStyle
from huisclos.pseudonymize import tokens
from huisclos.pseudonymize.mapping import Mapping, MappingEntry
from scripts import gate8_measure

ROOT = Path(__file__).resolve().parents[2]
SENTINEL = "ZELTRAVON_FAILURE_ONLY"
MANUAL = "votrel97"
TEXTS = {
    "fr": "M. Emeric VORLAVEC signe. Pièce : preuve_VORLAVEC.pdf. Code : votrel97. "
    "Contact : emeric.vorlavec@example.org.",
    "en": "Mr Alder QUENRAVIK signs. Exhibit: proof_QUENRAVIK.pdf. Code: votrel97. "
    "Contact: alder.quenravik@example.org.",
}
EMAILS = {"fr": "emeric.vorlavec@example.org", "en": "alder.quenravik@example.org"}
KEEP = (
    "source_text",
    "detections",
    "group_decisions",
    "manual_entities",
    "case_table",
    "case_table_name",
    "outbound_instruction",
    "outbound_check_all_types",
    "outbound_check_no_exclusions",
    "detection_signature",
    "document_language",
    "detection_profile",
    "threshold",
    "token_style",
    "enabled_types",
)
EMPTY = (
    "pseudo_result",
    "pseudo_basis",
    "restore_result",
    "restore_uploaded_table",
    "restore_table_error",
    "outbound_check_document",
    "outbound_check_instruction",
    "outbound_check_acks",
    "final_check_notice",
    "outbound_send_authorization",
)


def start(language: str, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Prépare une vraie détection avec une table de dossier antérieure indépendante."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    app.selectbox(key="language").select(language).run()
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", language)
    app.radio(key="document_language").set_value(language).run()
    app.session_state["case_table"] = Mapping(
        "2026-10-28T12:00:00+00:00",
        TokenStyle(),
        (MappingEntry("[PERSONNE_41]", EntityType.PERSON, "Ilan ZORVELIN", ("ZORVELIN",)),),
        (),
        "0" * 64,
    )
    app.session_state["case_table_name"] = "fictional_case.json"
    app.text_area(key="paste_widget").input(TEXTS[language]).run()
    app.button(key="detect").click().run()
    assert not app.exception and app.session_state["step"] == "review"
    app.text_input(key="review_manual_text").input(MANUAL).run()
    app.button(key="review_add_manual").click().run()
    begin = TEXTS[language].index(EMAILS[language])
    choices = dict(app.session_state["group_decisions"])
    choices[(begin, begin + len(EMAILS[language]))] = Decision(masked=False)
    app.session_state["group_decisions"] = choices
    app.session_state["outbound_instruction"] = "Summarise this fictional file."
    app.session_state["outbound_check_all_types"] = True
    app.session_state["outbound_check_no_exclusions"] = True
    return app


def snapshot(app: Any) -> dict[str, Any]:
    """Relève la revue et la configuration en mémoire, sans les exporter."""
    return {key: app.session_state[key] for key in KEEP}


def restore(app: Any, original: str) -> Any:
    """Utilise Restore pour restaurer exactement le nouveau résultat et le renvoie."""
    result = app.session_state["pseudo_result"]
    assert result is not None and app.session_state["pseudo_basis"] is not None
    assert app.session_state["outbound_check_document"] is not None
    app.text_area(key="restore_answer").input(result.text).run()
    app.button(key="restore_run").click().run()
    assert not app.exception and app.session_state["restore_result"].text == original
    return result


@pytest.mark.parametrize("language", ("fr", "en"))
@pytest.mark.parametrize("error_type", (RuntimeError, ValueError))
@pytest.mark.parametrize("retry", (False, True))
def test_independent_failure_and_recovery(
    language: str,
    error_type: type[Exception],
    retry: bool,
    monkeypatch: pytest.MonkeyPatch,
    caplog: Any,
    capsys: Any,
) -> None:
    """Vérifie un échec, tous les états sensibles, puis une vraie reprise réussie."""
    caplog.set_level(logging.WARNING)
    app = start(language, monkeypatch)
    previous = None
    if retry:
        app.button(key="review_pseudonymize").click().run()
        assert app.session_state["step"] == "restore"
        previous = restore(app, TEXTS[language])
        app.session_state["restore_uploaded_table"] = ActiveTable(previous.mapping, None, "f.json")
        app.session_state["outbound_check_acks"] = ("fictional", frozenset({"fictional"}))
        app.session_state["final_check_notice"] = "fictional"
        app.session_state["outbound_send_authorization"] = "fictional-authorization"
        app.button(key="restore_back_review").click().run()
        assert app.session_state["step"] == "review"
    before = snapshot(app)

    def fail(*args: Any, **kwargs: Any) -> Any:
        """Injecte une panne contenant une mention fictive absente du document."""
        raise error_type(SENTINEL)

    with monkeypatch.context() as failure:
        failure.setattr(tokens, "_substitute", fail)
        app.button(key="review_pseudonymize").click().run()
    assert not app.exception and app.session_state["step"] == "review"
    key = "review.error.substitution" if error_type is RuntimeError else "review.error.pseudonymize"
    dictionary = i18n.FR if language == "fr" else i18n.EN
    assert [item.value for item in app.error] == [dictionary[key]]
    assert all(app.session_state[key] is None for key in EMPTY)
    assert app.session_state["llm_response"] == ""
    assert "restore_answer" not in app.session_state
    assert snapshot(app) == before
    shown = [
        str(item.value)
        for kind in ("error", "warning", "info", "success", "markdown")
        for item in getattr(app, kind)
    ]
    captured = capsys.readouterr()
    assert all(SENTINEL not in value for value in shown)
    assert SENTINEL not in caplog.text + captured.out + captured.err
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception and app.session_state["step"] == "restore"
    assert app.session_state["pseudo_result"] is not previous
    assert app.session_state["restore_result"] is None
    assert app.session_state["restore_uploaded_table"] is None
    assert app.session_state["outbound_send_authorization"] is None
    assert app.session_state["outbound_check_acks"] is None
    assert app.text_area(key="restore_answer").value == ""
    assert MANUAL not in app.session_state["pseudo_result"].text
    assert EMAILS[language] in app.session_state["pseudo_result"].text
    assert snapshot(app) == before
    restore(app, TEXTS[language])


@pytest.mark.parametrize(
    "language,preset",
    (
        ("fr", "hybrid"),
        ("fr", "hybrid_camembert"),
        ("en", "hybrid"),
        ("en", "hybrid_gliner"),
    ),
)
def test_real_worker(language: str, preset: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Vérifie le vrai worker G8 hors ligne, sur un nom dans le texte et le fichier."""
    monkeypatch.setenv("HUISCLOS_MODELS_DIR", str(ROOT.parent / "pilotage/post_g7_assets"))
    text = TEXTS[language]
    payload = gate8_measure.run_separate(
        {"preset": preset, "threshold": 0.3}, [text], language, "gate"
    )
    assert len(payload["documents"]) == 1
    row, metadata = payload["documents"][0], payload["metadata"]
    assert len(row["detections"]) == len(row["occurrences"]) >= 3
    surname = "VORLAVEC" if language == "fr" else "QUENRAVIK"
    for offset in (text.index(surname), text.rindex(surname)):
        assert any(
            begin <= offset and end >= offset + len(surname) for begin, end, *_ in row["detections"]
        )
    assert metadata["configuration"]["document_language"] == language
    assert metadata["resources"]["network_blocked"]
    assert metadata["resources"]["main_detection_calls"] == 1
    assert metadata["final_check"]["available"]
