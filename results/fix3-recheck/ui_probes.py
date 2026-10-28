"""Teste les erreurs de substitution dans les interfaces FR et EN.

Entrées : documents fictifs et erreurs injectées après la détection réelle.
Sorties : seuls booléens et comptes ; les journaux sont examinés en mémoire.
Le second parcours repasse réellement de Restore à Review avant l'échec.
"""

import contextlib
import io
import logging
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from huisclos.pseudonymize import tokens

ROOT = Path(__file__).resolve().parents[2]


def scenario(language: str, error_type: type[Exception], retry: bool) -> dict[str, Any]:
    """Force une erreur et examine messages, résultats et trois canaux de journalisation."""
    name = "ZERQUAVEL" if language == "fr" else "VORQUENICK"
    text = (
        f"M. Lysandre {name} signe. preuve_{name}.pdf."
        if language == "fr"
        else f"Mr Evren {name} signs. exhibit_{name}.pdf."
    )
    stdout, stderr, logs = io.StringIO(), io.StringIO(), io.StringIO()
    handler = logging.StreamHandler(logs)
    logging.getLogger().addHandler(handler)

    def fail(*args: Any, **kwargs: Any) -> Any:
        """Lève une erreur contenant une mention fictive, afin de repérer sa divulgation."""
        raise error_type(f"forced substitution failure {name}")

    try:
        with (
            pytest.MonkeyPatch.context() as patch,
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            patch.setenv(i18n.STRICT_ENV, "1")
            patch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
            app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
            app.selectbox(key="language").select(language).run()
            # Repli existant pour la sérialisation AppTest hors contexte du script.
            patch.setattr(i18n, "DEFAULT_LANGUAGE", language)
            app.radio(key="document_language").set_value(language).run()
            app.text_area(key="paste_widget").set_value(text).run()
            app.button(key="detect").click().run()
            assert app.session_state["step"] == "review" and not app.exception
            previous = None
            if retry:
                app.button(key="review_pseudonymize").click().run()
                assert app.session_state["step"] == "restore" and not app.exception
                previous = app.session_state["pseudo_result"]
                app.button(key="restore_back_review").click().run()
                assert app.session_state["step"] == "review"
            patch.setattr(tokens, "_substitute", fail)
            app.button(key="review_pseudonymize").click().run()
            dictionary = i18n.FR if language == "fr" else i18n.EN
            key = (
                "review.error.substitution"
                if error_type is RuntimeError
                else "review.error.pseudonymize"
            )
            messages = [
                str(item.value)
                for kind in ("error", "warning", "info", "success")
                for item in getattr(app, kind)
            ]
            checks = {
                "correct_message": [item.value for item in app.error] == [dictionary[key]],
                "review_kept": app.session_state["step"] == "review",
                "no_exception": not app.exception,
                "no_pseudo_result": app.session_state["pseudo_result"] is None,
                "no_restore_result": app.session_state["restore_result"] is None,
                "messages_clean": all(name not in message for message in messages),
            }
            old_retained = previous is not None and app.session_state["pseudo_result"] == previous
    finally:
        logging.getLogger().removeHandler(handler)
    checks.update(
        {
            "logs_clean": name not in logs.getvalue(),
            "stderr_clean": name not in stderr.getvalue(),
            "stdout_clean": name not in stdout.getvalue(),
        }
    )
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "retry": retry,
        "error_type": error_type.__name__,
        "ui_language": language,
        "message_key": key,
        "captured_log_characters": len(logs.getvalue()),
        "captured_stderr_characters": len(stderr.getvalue()),
        "previous_result_retained": old_retained,
    }


def ui() -> dict[str, Any]:
    """Exécute quatre erreurs initiales puis deux échecs après un résultat valide."""
    rows = {}
    for language in ("fr", "en"):
        for error_type in (RuntimeError, ValueError):
            rows[f"{language}-{error_type.__name__}-fresh"] = scenario(language, error_type, False)
        rows[f"{language}-RuntimeError-retry"] = scenario(language, RuntimeError, True)
    return rows
