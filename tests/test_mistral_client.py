"""Vérifie l'envoi Mistral explicite, avec un transport HTTP entièrement fictif.

Entrées : message pseudonymisé fictif, réponses et erreurs de transport simulées, parcours
réel Import, Review, Restore dans AppTest.
Sorties : charge égale à la chaîne contrôlée, erreurs lisibles, garde Python de l'autorisation
au clic, confirmation périmée après chaque changement, Reset.
Place dans le pipeline : protège la frontière entre traitement local et service externe.
"""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests
from streamlit.testing.v1 import AppTest

from app import i18n
from huisclos.llm.mistral_client import CHAT_URL, DEFAULT_MODEL, MistralError, send_outbound
from huisclos.pseudonymize.outbound_check import SEPARATOR

APP_PATH = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
MESSAGE = "[PERSONNE_1] écrit à [EMAIL_1].\n" + SEPARATOR + "Résume ce texte."
SOURCE = "M. Pierre VERNOLAC écrit à pierre.vernolac@example.com pour son dossier."
ORIGINAL_VALUES = ("Pierre VERNOLAC", "pierre.vernolac@example.com", "VERNOLAC")
INSTRUCTION = "Résume ce texte pour [PERSONNE_1] en trois lignes."
ANSWER = "[PERSONNE_1] demande une réponse."
TIMEOUT = 120
INSTRUCTION_WIDGET = "outbound_instruction_widget"


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente ; démonstration publique désactivée."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)


def _response(payload: object = None, status: int = 200) -> Mock:
    """Renvoie une réponse HTTP fictive portant le statut et le JSON demandés."""
    return Mock(status_code=status, json=Mock(return_value=payload))


def _success() -> Mock:
    """Renvoie une réponse de chat fictive valide avec une seule réponse textuelle."""
    return _response({"choices": [{"message": {"content": ANSWER}}]})


def restore_screen(monkeypatch: pytest.MonkeyPatch, post: Mock, key: bool = True) -> AppTest:
    """Déroule le vrai parcours sur SOURCE, avec un transport simulé et une clé fictive."""
    monkeypatch.setattr(requests, "post", post)
    if key:
        monkeypatch.setenv("MISTRAL_API_KEY", "fake-key")
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    app.secrets = {}
    app.run()
    app.text_area(key="paste_widget").set_value(SOURCE).run()
    app.button(key="detect").click().run()
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
    return app


def set_instruction(app: AppTest, text: str) -> AppTest:
    """Remplace la consigne libre par l'interface."""
    app.text_area(key=INSTRUCTION_WIDGET).set_value(text).run()
    assert not app.exception
    return app


def confirm(app: AppTest) -> AppTest:
    """Coche la confirmation d'envoi."""
    app.checkbox(key="mistral_confirm").check().run()
    assert not app.exception
    return app


def sent_content(post: Mock) -> str:
    """Contenu du seul message envoyé au transport simulé."""
    messages = post.call_args.kwargs["json"]["messages"]
    assert len(messages) == 1 and messages[0]["role"] == "user"
    return messages[0]["content"]


def errors(app: AppTest) -> list[str]:
    """Textes des erreurs affichées."""
    return [element.value for element in app.error]


def test_payload_is_exactly_the_given_content(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contrôle exactement la destination, le contenu, le délai et les redirections."""
    post = Mock(return_value=_success())
    monkeypatch.setattr(requests, "post", post)
    assert send_outbound(MESSAGE, "fake-key", DEFAULT_MODEL) == ANSWER
    post.assert_called_once_with(
        CHAT_URL,
        headers={"Authorization": "Bearer fake-key"},
        json={"model": DEFAULT_MODEL, "messages": [{"role": "user", "content": MESSAGE}]},
        timeout=30,
        allow_redirects=False,
    )


@pytest.mark.parametrize(
    "status, code",
    [(401, "unauthorized"), (429, "quota"), (500, "unexpected"), (302, "unexpected")],
)
def test_http_errors(monkeypatch: pytest.MonkeyPatch, status: int, code: str) -> None:
    """Les erreurs de statut produisent un message public sans le corps serveur."""
    post = Mock(return_value=_response({"error": ORIGINAL_VALUES[0]}, status))
    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(MistralError) as caught:
        send_outbound(MESSAGE, "fake-key", DEFAULT_MODEL)
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
        send_outbound(MESSAGE, "fake-key", DEFAULT_MODEL, timeout=5)
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
        send_outbound(MESSAGE, "fake-key", DEFAULT_MODEL)


def test_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une réponse non JSON ne remonte aucun corps de réponse au client."""
    response = _success()
    response.json.side_effect = ValueError(ORIGINAL_VALUES[0])
    monkeypatch.setattr(requests, "post", Mock(return_value=response))
    with pytest.raises(MistralError, match="unexpected response"):
        send_outbound(MESSAGE, "fake-key", DEFAULT_MODEL)


def test_no_key_hides_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """La vraie étape Restore n'affiche aucun composant Mistral sans clé."""
    post = Mock(return_value=_success())
    app = restore_screen(monkeypatch, post, key=False)
    assert all("Mistral" not in heading.value for heading in app.subheader)
    with pytest.raises(KeyError):
        app.checkbox(key="mistral_confirm")
    post.assert_not_called()


def test_sent_string_is_exactly_the_checked_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """La clé seule n'envoie rien ; le clic consenti envoie la chaîne validée, rien d'autre."""
    post = Mock(return_value=_success())
    app = set_instruction(restore_screen(monkeypatch, post), INSTRUCTION)
    assert "No residual identifier found." in [item.value for item in app.success]
    assert not app.checkbox(key="mistral_confirm").value
    assert any("Experiment" in item.value for item in app.warning)
    post.assert_not_called()
    app = confirm(app)
    assert not app.button(key="mistral_send").disabled
    post.assert_not_called()
    result = app.session_state["pseudo_result"]
    expected = result.text + SEPARATOR + INSTRUCTION
    # Le message affiché à copier est la même chaîne que celle contrôlée puis envoyée.
    assert app.code[0].value == expected.strip()
    app.button(key="mistral_send").click().run()
    assert not app.exception
    post.assert_called_once()
    assert sent_content(post) == expected
    body = json.dumps(post.call_args.kwargs["json"], ensure_ascii=False)
    assert all(value not in body for value in ORIGINAL_VALUES)
    assert result.mapping.to_json() not in body
    assert "pseudonymized_sha256" not in body
    assert app.text_area(key="restore_answer").value == ANSWER
    # Une confirmation vaut pour un envoi.
    assert not app.checkbox(key="mistral_confirm").value


def test_any_change_revokes_the_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Consigne, seuil, langue du document : chaque changement décoche et bloque l'envoi."""
    post = Mock(return_value=_success())
    app = confirm(set_instruction(restore_screen(monkeypatch, post), INSTRUCTION))
    app = set_instruction(app, INSTRUCTION + " Merci.")
    assert not app.checkbox(key="mistral_confirm").value
    assert app.session_state["outbound_send_authorization"] is None
    app = confirm(app)
    app.checkbox(key="check_policy_no_exclusions").check().run()
    assert not app.checkbox(key="mistral_confirm").value
    app.checkbox(key="check_policy_no_exclusions").uncheck().run()
    app = confirm(app)
    app.slider(key="threshold").set_value(0.5).run()
    assert not app.checkbox(key="mistral_confirm").value
    assert app.checkbox(key="mistral_confirm").disabled
    assert app.button(key="mistral_send").disabled
    assert any(item.value.startswith("Not ready to send") for item in app.warning)
    post.assert_not_called()


def test_send_from_an_old_state_is_refused_in_python(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un clic avec une autorisation d'un autre contenu n'appelle jamais le réseau."""
    post = Mock(return_value=_success())
    app = confirm(set_instruction(restore_screen(monkeypatch, post), INSTRUCTION))
    old = app.session_state["outbound_send_authorization"]
    assert old
    # Le contenu change sans passer par le composant, puis l'envoi est tenté dans la même
    # exécution : seule la garde Python peut l'arrêter.
    app.session_state["outbound_instruction"] = "Autre consigne."
    app.button(key="mistral_send").click().run()
    assert not app.exception
    post.assert_not_called()
    assert any("Nothing was sent" in text for text in errors(app))


def test_network_is_never_called_without_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans confirmation, même un clic forcé n'envoie rien."""
    post = Mock(return_value=_success())
    app = restore_screen(monkeypatch, post)
    app.button(key="mistral_send").click().run()
    assert not app.exception
    post.assert_not_called()
    assert any("Nothing was sent" in text for text in errors(app))


def test_identifier_in_instruction_blocks_then_correction_allows_sending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un identifiant fictif seulement dans la consigne bloque ; une fois retiré, l'envoi passe."""
    post = Mock(return_value=_success())
    app = set_instruction(restore_screen(monkeypatch, post), "Écris à alice.fictivel@example.com.")
    assert any("Possible identifiers left in clear: 1" in item.value for item in app.warning)
    assert app.checkbox(key="mistral_confirm").disabled
    assert app.button(key="mistral_send").disabled
    assert app.get("download_button")[0].disabled
    assert not any("alice.fictivel" in block.value for block in app.code)
    post.assert_not_called()
    app = confirm(set_instruction(app, "Écris une réponse courte."))
    app.button(key="mistral_send").click().run()
    post.assert_called_once()
    assert "alice.fictivel" not in sent_content(post)


def test_unknown_token_in_instruction_cannot_be_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un jeton absent de la table se corrige ; aucune case ne permet de le garder."""
    post = Mock(return_value=_success())
    app = set_instruction(restore_screen(monkeypatch, post), "Compare avec [PERSONNE_9].")
    assert any("Possible identifiers left in clear: 1" in item.value for item in app.warning)
    assert not [box for box in app.checkbox if box.key.startswith("check_ack_")]
    assert app.checkbox(key="mistral_confirm").disabled


def test_explicit_decision_on_an_alert_allows_sending(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garder une mention en clair est une décision explicite, jamais précochée."""
    post = Mock(return_value=_success())
    app = set_instruction(restore_screen(monkeypatch, post), "Écris à alice.fictivel@example.com.")
    boxes = [box for box in app.checkbox if box.key.startswith("check_ack_")]
    assert len(boxes) == 1 and not boxes[0].value
    boxes[0].check().run()
    assert any(item.value.startswith("All 1 alerts were reviewed") for item in app.info)
    app = confirm(app)
    app.button(key="mistral_send").click().run()
    post.assert_called_once()
    # Changer la consigne fait oublier la décision : elle portait sur ce contexte.
    app = set_instruction(app, "Écris à alice.fictivel@example.com, vite.")
    assert all(not box.value for box in app.checkbox if box.key.startswith("check_ack_"))


@pytest.mark.parametrize("code, status", [("unauthorized", 401), ("quota", 429), ("timeout", None)])
def test_ui_errors(monkeypatch: pytest.MonkeyPatch, code: str, status: int | None) -> None:
    """Les erreurs HTTP et de délai sont affichées sans effacer la réponse existante."""
    post = (
        Mock(return_value=_response({}, status)) if status else Mock(side_effect=requests.Timeout)
    )
    app = restore_screen(monkeypatch, post)
    app.text_area(key="restore_answer").set_value("Réponse déjà collée").run()
    app = confirm(app)
    app.button(key="mistral_send").click().run()
    assert not app.exception
    assert app.text_area(key="restore_answer").value == "Réponse déjà collée"
    expected = {"unauthorized": "401", "quota": "429", "timeout": "timeout"}[code]
    assert any(expected in text for text in errors(app))


def test_reset_removes_check_and_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset retire contrôle, décisions explicites et autorisation ; rien ne part ensuite."""
    post = Mock(return_value=_success())
    app = confirm(set_instruction(restore_screen(monkeypatch, post), INSTRUCTION))
    assert app.session_state["outbound_send_authorization"]
    app.button(key="reset_session").click().run()
    app.button(key="reset_confirm").click().run()
    assert not app.exception
    for key in (
        "outbound_send_authorization",
        "outbound_check_document",
        "outbound_check_instruction",
        "outbound_check_acks",
        "pseudo_result",
        "pseudo_basis",
        "outbound_instruction",
    ):
        assert app.session_state[key] is None
    post.assert_not_called()
