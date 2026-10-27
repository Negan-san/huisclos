"""Vérifie l'envoi Mistral explicite, avec un transport HTTP entièrement fictif.

Entrées : texte pseudonymisé fictif, réponses et erreurs de transport simulées.
Sorties : charge limitée au texte et à la consigne, erreurs lisibles et interface contrôlée.
Place dans le pipeline : protège la frontière entre traitement local et service externe.
"""

import json
from unittest.mock import Mock

import pytest
import requests
from streamlit.testing.v1 import AppTest

from huisclos.llm.mistral_client import (
    CHAT_URL,
    DEFAULT_MODEL,
    MistralError,
    send_pseudonymized,
)

PSEUDONYMIZED = "[PERSONNE_1] écrit à [EMAIL_1].\n"
INSTRUCTION = "Résume ce texte en conservant les jetons."
ORIGINAL_VALUES = ("Alice FICTIVEL", "alice@example.invalid")
ANSWER = "[PERSONNE_1] demande une réponse."

# La vraie étape est exercée avec une table fictive contenant les valeurs interdites.
RESTORE_APP = """
import streamlit as st
from types import SimpleNamespace
from app.state import init_state, KEY_PSEUDO_RESULT
from app.steps.restore_step import render
init_state()
st.session_state['source_text'] = 'Alice FICTIVEL écrit à alice@example.invalid.'
mapping = SimpleNamespace(
    pseudonymized_sha256='1234567890',
    to_json=lambda: '{"original": "Alice FICTIVEL", "email": "alice@example.invalid"}',
)
st.session_state[KEY_PSEUDO_RESULT] = SimpleNamespace(
    text=st.session_state.get('test_pseudonymized', "[PERSONNE_1] écrit à [EMAIL_1].\\n"),
    warnings=[],
    groups=[], occurrences=[], mapping=mapping,
)
render()
"""


def _response(payload: object = None, status: int = 200) -> Mock:
    """Renvoie une réponse HTTP fictive portant le statut et le JSON demandés."""
    return Mock(status_code=status, json=Mock(return_value=payload))


def _success() -> Mock:
    """Renvoie une réponse de chat fictive valide avec une seule réponse textuelle."""
    return _response({"choices": [{"message": {"content": ANSWER}}]})


def test_payload_contains_only_pseudonymized_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contrôle exactement la destination, le contenu, le délai et les redirections."""
    post = Mock(return_value=_success())
    monkeypatch.setattr(requests, "post", post)
    assert send_pseudonymized(PSEUDONYMIZED, INSTRUCTION, "fake-key", DEFAULT_MODEL) == ANSWER
    post.assert_called_once_with(
        CHAT_URL,
        headers={"Authorization": "Bearer fake-key"},
        json={
            "model": DEFAULT_MODEL,
            "messages": [{"role": "user", "content": PSEUDONYMIZED + INSTRUCTION}],
        },
        timeout=30,
        allow_redirects=False,
    )
    payload = json.dumps(post.call_args.kwargs["json"])
    assert all(value not in payload for value in ORIGINAL_VALUES)


@pytest.mark.parametrize(
    "status, code",
    [(401, "unauthorized"), (429, "quota"), (500, "unexpected"), (302, "unexpected")],
)
def test_http_errors(monkeypatch: pytest.MonkeyPatch, status: int, code: str) -> None:
    """Les erreurs de statut produisent un message public sans le corps serveur."""
    post = Mock(return_value=_response({"error": ORIGINAL_VALUES[0]}, status))
    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(MistralError) as caught:
        send_pseudonymized(PSEUDONYMIZED, INSTRUCTION, "fake-key", DEFAULT_MODEL)
    assert caught.value.code == code
    assert str(caught.value)
    assert ORIGINAL_VALUES[0] not in str(caught.value)


@pytest.mark.parametrize(
    "error, code", [(requests.Timeout, "timeout"), (requests.ConnectionError, "connection")]
)
def test_transport_errors(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception], code: str
) -> None:
    """Un délai dépassé ou une panne réseau ne révèle pas l'exception du transport."""
    monkeypatch.setattr(requests, "post", Mock(side_effect=error(ORIGINAL_VALUES[0])))
    with pytest.raises(MistralError) as caught:
        send_pseudonymized(PSEUDONYMIZED, INSTRUCTION, "fake-key", DEFAULT_MODEL, timeout=5)
    assert caught.value.code == code
    assert ORIGINAL_VALUES[0] not in str(caught.value)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {},
        {"choices": []},
        {"choices": [None]},
        {"choices": [{"message": {"content": []}}]},
        {"choices": [{"message": {"content": " "}}]},
    ],
)
def test_unexpected_payload(monkeypatch: pytest.MonkeyPatch, payload: object) -> None:
    """Un JSON incomplet ou un contenu non textuel produit une erreur claire."""
    monkeypatch.setattr(requests, "post", Mock(return_value=_response(payload)))
    with pytest.raises(MistralError, match="unexpected response"):
        send_pseudonymized(PSEUDONYMIZED, INSTRUCTION, "fake-key", DEFAULT_MODEL)


def test_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une réponse non JSON ne remonte aucun corps de réponse au client."""
    response = _success()
    response.json.side_effect = ValueError(ORIGINAL_VALUES[0])
    monkeypatch.setattr(requests, "post", Mock(return_value=response))
    with pytest.raises(MistralError, match="unexpected response"):
        send_pseudonymized(PSEUDONYMIZED, INSTRUCTION, "fake-key", DEFAULT_MODEL)


def test_no_key_hides_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """La vraie étape Restore n'affiche aucun composant Mistral sans clé."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    app = AppTest.from_string(RESTORE_APP)
    app.secrets = {}
    app.run()
    assert not app.exception
    assert all("Mistral" not in heading.value for heading in app.subheader)
    assert not app.checkbox


@pytest.mark.parametrize("key_source", ["environment", "secrets"])
def test_consent_and_answer_in_real_restore(
    monkeypatch: pytest.MonkeyPatch, key_source: str
) -> None:
    """La clé seule n'envoie rien ; le clic consenti remplit la vraie zone de réponse."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    post = Mock(return_value=_success())
    monkeypatch.setattr(requests, "post", post)
    app = AppTest.from_string(RESTORE_APP)
    app.secrets = {"MISTRAL_API_KEY": "fake-key"} if key_source == "secrets" else {}
    if key_source == "environment":
        monkeypatch.setenv("MISTRAL_API_KEY", "fake-key")
    app.run()
    assert not app.exception
    assert not app.checkbox(key="mistral_confirm").value
    assert app.button(key="mistral_send").disabled
    assert any(
        "Experiment" in item.value and "fictitious data only" in item.value for item in app.warning
    )
    post.assert_not_called()
    app.text_area(key="mistral_instruction").set_value(INSTRUCTION).run()
    app.checkbox(key="mistral_confirm").check().run()
    assert not app.button(key="mistral_send").disabled
    post.assert_not_called()
    app.button(key="mistral_send").click().run()
    assert not app.exception
    assert app.text_area(key="restore_answer").value == ANSWER
    post.assert_called_once()
    payload = post.call_args.kwargs["json"]
    assert payload["messages"] == [{"role": "user", "content": PSEUDONYMIZED + INSTRUCTION}]
    assert all(value not in json.dumps(payload) for value in ORIGINAL_VALUES)
    app.text_area(key="mistral_instruction").set_value("Une autre consigne").run()
    assert not app.checkbox(key="mistral_confirm").value
    assert app.button(key="mistral_send").disabled
    app.checkbox(key="mistral_confirm").check().run()
    app.session_state["test_pseudonymized"] = "[PERSONNE_2] écrit à [EMAIL_1]."
    app.run()
    assert not app.checkbox(key="mistral_confirm").value
    assert app.button(key="mistral_send").disabled
    post.assert_called_once()


@pytest.mark.parametrize("code, status", [("unauthorized", 401), ("quota", 429), ("timeout", None)])
def test_ui_errors(monkeypatch: pytest.MonkeyPatch, code: str, status: int | None) -> None:
    """Les erreurs HTTP et de délai sont affichées sans effacer la réponse existante."""
    monkeypatch.setenv("MISTRAL_API_KEY", "fake-key")
    post = (
        Mock(return_value=_response({}, status)) if status else Mock(side_effect=requests.Timeout)
    )
    monkeypatch.setattr(requests, "post", post)
    app = AppTest.from_string(RESTORE_APP)
    app.secrets = {}
    app.run()
    app.text_area(key="restore_answer").set_value("Réponse déjà collée").run()
    app.checkbox(key="mistral_confirm").check().run()
    app.button(key="mistral_send").click().run()
    assert not app.exception
    assert app.text_area(key="restore_answer").value == "Réponse déjà collée"
    expected = {"unauthorized": "401", "quota": "429", "timeout": "timeout"}[code]
    assert any(expected in item.value for item in app.error)
