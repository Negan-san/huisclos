"""Tests de l'indicateur d'étapes : états, mention écrite, accessibilité et échappement."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.components.stepper import (
    AVAILABLE,
    CURRENT,
    DONE,
    LOCKED,
    StepView,
    step_states,
    stepper_html,
)
from app.i18n import t
from app.state import STEPS

APP_PATH = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def items(fragment: str) -> list[str]:
    """Découpe l'indicateur en éléments de liste."""
    return re.findall(r"<li .*?</li>", fragment)


@pytest.mark.parametrize(
    ("current", "available", "expected"),
    [
        ("import", {"import": True}, [CURRENT, LOCKED, LOCKED]),
        ("review", {"import": True, "review": True}, [DONE, CURRENT, LOCKED]),
        ("restore", {"import": True, "review": True, "restore": True}, [DONE, DONE, CURRENT]),
        ("import", {"import": True, "review": True}, [CURRENT, AVAILABLE, LOCKED]),
        ("review", {"import": True, "review": True, "restore": True}, [DONE, CURRENT, AVAILABLE]),
    ],
)
def test_states_follow_the_current_step_and_availability(
    current: str, available: dict[str, bool], expected: list[str]
) -> None:
    assert step_states(STEPS, current, available) == expected


def test_an_unavailable_step_is_locked_even_before_the_current_one() -> None:
    assert step_states(("a", "b", "c"), "c", {"a": True, "c": True}) == [DONE, LOCKED, CURRENT]


def test_html_marks_only_the_current_step_and_writes_each_state() -> None:
    views = [
        StepView(1, "Import", DONE, "Completed"),
        StepView(2, "Review", CURRENT, "Current step"),
        StepView(3, "Restore", LOCKED, "Available once the text has been created."),
    ]
    fragment = stepper_html(views, "Steps of the workflow")
    assert fragment.startswith('<ol class="hc-stepper" role="list" aria-label="Steps of')
    done, current, locked = items(fragment)
    assert fragment.count('aria-current="step"') == 1
    assert 'aria-current="step"' in current
    # La pastille d'une étape faite ne porte pas de numéro : la coche est dessinée en CSS.
    assert '<span class="hc-step-dot" aria-hidden="true"></span>' in done
    assert ">Completed</span>" in done
    assert '<span class="hc-step-dot" aria-hidden="true">2</span>' in current
    assert ">Current step</span>" in current
    assert "hc-step-locked" in locked
    assert ">Available once the text has been created.</span>" in locked


def test_texts_are_escaped() -> None:
    views = [StepView(1, "<b>Import</b>", CURRENT, 'say "hi" & <i>go</i>')]
    fragment = stepper_html(views, 'label"><script>')
    assert "<b>" not in fragment
    assert "<i>" not in fragment
    assert "<script>" not in fragment
    assert "&lt;b&gt;Import&lt;/b&gt;" in fragment
    assert "&amp; &lt;i&gt;go&lt;/i&gt;" in fragment


def test_app_stepper_explains_locks_then_marks_import_as_completed() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=120).run()
    stepper = next(b.value for b in app.get("html") if 'class="hc-stepper"' in b.value)
    first, second, third = items(stepper)
    assert "hc-step-current" in first
    assert t("steps.locked.review") in second
    assert t("steps.locked.restore") in third
    app.button(key="load_sample").click().run()
    app.button(key="detect").click().run()
    stepper = next(b.value for b in app.get("html") if 'class="hc-stepper"' in b.value)
    first, second, third = items(stepper)
    assert "hc-step-done" in first
    assert t("steps.state.done") in first
    assert 'aria-current="step"' in second
    assert t("steps.locked.restore") in third
