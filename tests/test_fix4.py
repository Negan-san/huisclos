"""FIX4 : invalidation des résultats avant une nouvelle pseudonymisation (FIX3R-01).

Entrées : documents entièrement fictifs, détection Standard réelle, pannes injectées dans
la substitution avec une mention fictive absente du document.
Sorties : contrats de l'étape Review en interface FR et EN : aucun ancien résultat, contrôle
ou autorisation après un échec ; revue et table de dossier conservées ; nouveau succès propre.
"""

import logging
from pathlib import Path
from typing import Any

import pytest

from app.steps.review_decisions import Decision

ROOT = Path(__file__).resolve().parents[1]
# Mention citée par la panne injectée : fictive et absente des documents, pour qu'on ne la
# retrouve nulle part ailleurs que dans le message de l'exception.
LEAK = "VELDRAMOUX"
MANUAL = "zorvel81"
DOCUMENTS = {
    "fr": (
        "M. Octavien BRUMESSAC a vendu le bien à Mme Heloise TRAVENNE. "
        "Contact : octavien.brumessac@example.com. Mot de passe : zorvel81."
    ),
    "en": (
        "Mr Corwin HALDERVY sold the property to Ms Maren OSTVICK. "
        "Contact: corwin.haldervy@example.com. Password: zorvel81."
    ),
}
EMAILS = {"fr": "octavien.brumessac@example.com", "en": "corwin.haldervy@example.com"}
INSTRUCTION = "Résume ce dossier fictif."
ERRORS = (RuntimeError, ValueError)
MESSAGE_KEYS = {RuntimeError: "review.error.substitution", ValueError: "review.error.pseudonymize"}


def start(ui: str, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Ouvre l'application dans la langue d'interface ui et détecte le document fictif."""
    from streamlit.testing.v1 import AppTest

    from app import i18n

    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    app.selectbox(key="language").select(ui).run()
    # Même repli que tests/test_fix2.py : AppTest sérialise les sélecteurs hors session.
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", ui)
    app.radio(key="document_language").set_value(ui).run()
    app.text_area(key="paste_widget").set_value(DOCUMENTS[ui]).run()
    app.button(key="detect").click().run()
    assert app.session_state["step"] == "review" and not app.exception
    return app


def review_choices(app: Any, ui: str) -> None:
    """Fait des choix de revue : ajout manuel réel, courriel non masqué, consigne et politique."""
    app.text_input(key="review_manual_text").input(MANUAL).run()
    app.button(key="review_add_manual").click().run()
    assert any(item.text == MANUAL for item in app.session_state["manual_entities"])
    text = DOCUMENTS[ui]
    start_at = text.index(EMAILS[ui])
    decisions = dict(app.session_state["group_decisions"])
    decisions[(start_at, start_at + len(EMAILS[ui]))] = Decision(masked=False)
    app.session_state["group_decisions"] = decisions
    app.session_state["outbound_instruction"] = INSTRUCTION
    app.session_state["outbound_check_all_types"] = True


def reach_restore_then_review(app: Any, with_case_table: bool) -> Any:
    """Pseudonymise, remplit Restore (réponse, restauration, table, autorisation), puis revient.

    with_case_table pose une table de dossier : elle change la signature de détection, donc
    rend le texte périmé ; seul le test d'échec s'en sert, pour vérifier qu'elle reste.
    Valeur retournée : le premier résultat de pseudonymisation.
    """
    from app.steps.restore_step import ActiveTable

    app.button(key="review_pseudonymize").click().run()
    assert app.session_state["step"] == "restore" and not app.exception
    first = app.session_state["pseudo_result"]
    assert app.session_state["pseudo_basis"] is not None
    assert app.session_state["outbound_check_document"] is not None
    app.text_area(key="restore_answer").input(first.text).run()
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"] is not None
    app.session_state["outbound_send_authorization"] = "empreinte-fictive"
    app.session_state["outbound_check_acks"] = ("portee-fictive", frozenset({"cle-fictive"}))
    app.session_state["restore_uploaded_table"] = ActiveTable(first.mapping, None, "t.json")
    if with_case_table:
        app.session_state["case_table"] = first.mapping
        app.session_state["case_table_name"] = "dossier_fictif.json"
    app.button(key="restore_back_review").click().run()
    assert app.session_state["step"] == "review" and not app.exception
    return first


def review_snapshot(app: Any) -> dict[str, Any]:
    """Relève ce que la revue doit garder : texte, détections, décisions, ajouts, dossier."""
    table = app.session_state["case_table"]
    return {
        "source": app.session_state["source_text"],
        "detections": list(app.session_state["detections"]),
        "decisions": dict(app.session_state["group_decisions"]),
        "manual": list(app.session_state["manual_entities"]),
        "case_table": None if table is None else table.to_json(),
        "case_name": app.session_state["case_table_name"],
        "instruction": app.session_state["outbound_instruction"],
        "policy": app.session_state["outbound_check_all_types"],
    }


def assert_invalidated(app: Any) -> None:
    """Aucun résultat, base, réponse, restauration, table importée, contrôle ni autorisation."""
    for key in (
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
    ):
        assert app.session_state[key] is None, key
    assert app.session_state["llm_response"] == ""
    assert "restore_answer" not in app.session_state


def fail_with(monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]) -> None:
    """Force la substitution à lever error_type avec la mention fictive LEAK."""
    from huisclos.pseudonymize import tokens

    def failing_substitute(*_: object, **__: object) -> Any:
        raise error_type(f"panne fictive pour la mention {LEAK}")

    monkeypatch.setattr(tokens, "_substitute", failing_substitute)


def assert_safe_failure(
    app: Any, ui: str, error_type: type[Exception], caplog: Any, capsys: Any
) -> None:
    """Review reste ouverte avec le bon message, et la mention fictive n'apparaît nulle part."""
    from app import i18n

    texts = i18n.FR if ui == "fr" else i18n.EN
    assert not app.exception
    assert app.session_state["step"] == "review"
    assert [item.value for item in app.error] == [texts[MESSAGE_KEYS[error_type]]]
    shown = [
        str(item.value)
        for kind in ("error", "warning", "info", "success", "markdown")
        for item in getattr(app, kind)
    ]
    assert all(LEAK not in value for value in shown)
    captured = capsys.readouterr()
    assert LEAK not in caplog.text and LEAK not in captured.out and LEAK not in captured.err


@pytest.mark.parametrize("error_type", ERRORS)
@pytest.mark.parametrize("ui", ("fr", "en"))
def test_first_failure_leaves_no_result(
    ui: str, error_type: type[Exception], monkeypatch: pytest.MonkeyPatch, caplog: Any, capsys: Any
) -> None:
    """Un premier échec, sans résultat antérieur, laisse Review sans aucun résultat."""
    caplog.set_level(logging.DEBUG)
    app = start(ui, monkeypatch)
    fail_with(monkeypatch, error_type)
    app.button(key="review_pseudonymize").click().run()
    assert_safe_failure(app, ui, error_type, caplog, capsys)
    assert_invalidated(app)


@pytest.mark.parametrize("error_type", ERRORS)
@pytest.mark.parametrize("ui", ("fr", "en"))
def test_failed_retry_after_restore_drops_previous_result(
    ui: str, error_type: type[Exception], monkeypatch: pytest.MonkeyPatch, caplog: Any, capsys: Any
) -> None:
    """FIX3R-01 : Restore, retour à Review, nouvel échec ; rien de l'ancien essai ne reste."""
    caplog.set_level(logging.DEBUG)
    app = start(ui, monkeypatch)
    review_choices(app, ui)
    reach_restore_then_review(app, with_case_table=True)
    before = review_snapshot(app)
    fail_with(monkeypatch, error_type)
    app.button(key="review_pseudonymize").click().run()
    assert_safe_failure(app, ui, error_type, caplog, capsys)
    assert_invalidated(app)
    assert review_snapshot(app) == before
    assert before["case_table"] is not None and before["policy"] is True


@pytest.mark.parametrize("ui", ("fr", "en"))
def test_successful_retry_renews_result_and_check(ui: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Un nouvel essai réussi donne un résultat neuf, un contrôle refait, aucune autorisation."""
    from app.steps import restore_check

    calls: list[int] = []
    original = restore_check.document_alerts

    def counted(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(restore_check, "document_alerts", counted)
    app = start(ui, monkeypatch)
    review_choices(app, ui)
    first = reach_restore_then_review(app, with_case_table=False)
    before = review_snapshot(app)
    checks_before = len(calls)
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
    second = app.session_state["pseudo_result"]
    assert second is not first
    assert app.session_state["pseudo_basis"] is not None
    assert len(calls) > checks_before
    assert app.session_state["outbound_check_document"] is not None
    assert app.session_state["outbound_send_authorization"] is None
    assert app.session_state["outbound_check_acks"] is None
    assert app.session_state["restore_result"] is None
    assert app.session_state["restore_uploaded_table"] is None
    assert app.session_state["llm_response"] == ""
    assert app.text_area(key="restore_answer").value == ""
    assert review_snapshot(app) == before
    # La revue est appliquée : ajout manuel masqué, courriel laissé en clair.
    assert MANUAL not in second.text and EMAILS[ui] in second.text
    app.text_area(key="restore_answer").input(second.text).run()
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"].text == DOCUMENTS[ui]
