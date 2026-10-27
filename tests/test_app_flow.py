"""Contrôle indépendant du parcours complet et des données conservées entre pages.

Entrées : cas fictif chargé par l'interface et tables fictives produites en mémoire.
Sorties : assertions AppTest sur la revue, la restauration et la remise à zéro.
Place dans le pipeline : gate G3, avec surveillance du réseau et des écritures disque.
"""

import builtins
import io
import os
import socket
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

from app.i18n import t
from app.steps.review_step import KEY_TABLE_VERSION, TABLE_KEY_PREFIX
from huisclos.models import EntityType, Source

APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


def start_sample() -> AppTest:
    """Ouvre l'application puis charge et détecte le cas fictif par les boutons."""
    app = AppTest.from_file(APP_PATH, default_timeout=120).run()
    assert not app.exception
    app.button(key="load_sample").click().run()
    assert app.session_state["source_name"] == "demo_case_fr.txt"
    app.button(key="detect").click().run()
    assert not app.exception
    assert app.session_state["step"] == "review"
    return app


def test_sample_complete_flow_without_network_or_disk_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Vérifie toutes les étapes ; seules les connexions locales d'AppTest sont autorisées."""
    monkeypatch.setenv("HUISCLOS_I18N_STRICT", "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    violations: list[str] = []

    def guard_connection(original: Callable[..., Any]) -> Callable[..., Any]:
        """Encadre une API socket et refuse toute destination hors de la boucle locale."""

        def guarded(connection: socket.socket, address: Any, *args: Any) -> Any:
            """Transmet seulement une connexion de contrôle locale d'AppTest."""
            if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
                violations.append("network")
                raise AssertionError("Connexion externe interdite pendant le parcours.")
            return original(connection, address, *args)

        return guarded

    def guard_open(original: Callable[..., Any]) -> Callable[..., Any]:
        """Refuse les ouvertures en écriture, y compris celles de pathlib via io.open."""

        def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            """Transmet uniquement les lectures de fichiers."""
            if any(flag in mode for flag in "wax+"):
                violations.append("disk write")
                raise AssertionError("Écriture disque interdite pendant le parcours.")
            return original(file, mode, *args, **kwargs)

        return guarded

    original_os_open = os.open
    original_getaddrinfo = socket.getaddrinfo
    original_sendto = socket.socket.sendto

    def guard_dns(host: Any, *args: Any, **kwargs: Any) -> Any:
        """Refuse la résolution d'un nom externe, même avant une connexion bloquée."""
        if host not in (None, "localhost", "127.0.0.1", "::1"):
            violations.append("DNS")
            raise AssertionError("Résolution DNS externe interdite pendant le parcours.")
        return original_getaddrinfo(host, *args, **kwargs)

    def guard_sendto(connection: socket.socket, data: bytes, *args: Any) -> int:
        """Refuse aussi un envoi UDP vers une destination externe."""
        address = args[-1]
        if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1"):
            violations.append("UDP")
            raise AssertionError("Envoi UDP externe interdit pendant le parcours.")
        return original_sendto(connection, data, *args)

    def guard_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        """Refuse également les écritures par descripteur de fichier."""
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            violations.append("disk write")
            raise AssertionError("Écriture disque interdite pendant le parcours.")
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guard_connection(socket.socket.connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guard_connection(socket.socket.connect_ex))
    monkeypatch.setattr(socket, "getaddrinfo", guard_dns)
    monkeypatch.setattr(socket.socket, "sendto", guard_sendto)
    monkeypatch.setattr(builtins, "open", guard_open(builtins.open))
    monkeypatch.setattr(io, "open", guard_open(io.open))
    monkeypatch.setattr(os, "open", guard_os_open)

    app = start_sample()
    rows = next(
        table.to_pylist()
        for element in app.get("dataframe")
        if "Mask"
        in (table := pa.ipc.open_stream(element.proto.arrow_data.data).read_all()).column_names
    )
    rejected = next(i for i, row in enumerate(rows) if row["Text"] == "Courriel")
    # AppTest ne propose pas l'édition des cellules ; l'état reproduit le message du navigateur.
    app.session_state[f"{TABLE_KEY_PREFIX}0"] = {
        "edited_rows": {rejected: {"Mask": False}},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()
    decisions = dict(app.session_state["group_decisions"])
    assert any(not decision.masked for decision in decisions.values())
    app.text_input(key="review_manual_text").set_value("client")
    app.button(key="review_add_manual").click().run()
    manual = app.session_state["manual_entities"]
    assert len(manual) == 3
    assert all(d.source is Source.MANUAL and d.score == 1.0 for d in manual)
    version = app.session_state[KEY_TABLE_VERSION]
    app.switch_page("app/pages/evaluation.py").run()
    assert not app.exception
    app.switch_page("app/pages/workflow.py").run()
    assert not app.exception
    assert app.session_state["group_decisions"] == decisions
    assert app.session_state["manual_entities"] == manual
    assert app.session_state[KEY_TABLE_VERSION] == version
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    result = app.session_state["pseudo_result"]
    assert "Courriel" in result.text
    assert "client" not in result.text.lower()
    assert result.text.count("[AUTRE_1]") == 3
    person = next(e for e in result.mapping.entities if e.entity_type is EntityType.PERSON)
    altered = person.token.lower().replace("_", " ")
    answer = f"Réponse : {altered}. Voir [PERSONNE_99]."
    app.text_area(key="restore_answer").set_value(answer)
    app.button(key="restore_run").click().run()
    assert not app.exception
    restored = app.session_state["restore_result"]
    assert restored.text == f"Réponse : {person.canonical}. Voir [PERSONNE_99]."
    assert restored.altered == [(altered, person.token)]
    assert [form for form, _ in restored.unknown] == ["[PERSONNE_99]"]
    downloads = app.get("download_button")
    assert len(downloads) == 5
    assert all(not button.disabled for button in downloads)
    app.switch_page("app/pages/method.py").run()
    app.switch_page("app/pages/workflow.py").run()
    assert not app.exception
    assert app.text_area(key="restore_answer").value == answer
    assert restored.text in [block.value for block in app.code]
    app.button(key="restore_new").click().run()
    app.button(key="restore_new_confirm").click().run()
    assert not app.exception
    assert app.session_state["step"] == "import"
    for key in ("source_text", "source_name", "llm_response"):
        assert app.session_state[key] == ""
    for key in ("detections", "pseudo_result", "restore_result", "detection_signature"):
        assert app.session_state[key] is None
    assert app.session_state["group_decisions"] == {}
    assert app.session_state["manual_entities"] == []
    assert app.session_state["upload_nonce"] == 1
    assert violations == []


def test_uploaded_mapping_survives_navigation() -> None:
    """Une table importée reste active après la disparition temporaire du téléverseur."""
    app = start_sample()
    app.button(key="review_pseudonymize").click().run()
    result = app.session_state["pseudo_result"]
    person = next(e for e in result.mapping.entities if e.entity_type is EntityType.PERSON)
    other = replace(
        result.mapping,
        entities=tuple(
            replace(entry, canonical="Zoé MARTIN") if entry.token == person.token else entry
            for entry in result.mapping.entities
        ),
    )
    app.file_uploader(key="restore_table_upload_0").upload(
        "fictional.mapping.json", other.to_json().encode("utf-8")
    ).run()
    app.text_area(key="restore_answer").set_value(f"Voir {person.token}.")
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"].text == "Voir Zoé MARTIN."
    app.switch_page("app/pages/method.py").run()
    app.switch_page("app/pages/workflow.py").run()
    assert not app.exception
    assert "Voir Zoé MARTIN." in [block.value for block in app.code]
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"].text == "Voir Zoé MARTIN."
    app.button(key="restore_back_review").click().run()
    app.button(key="review_pseudonymize").click().run()
    assert app.session_state["restore_uploaded_table"] is None
    app.text_area(key="restore_answer").set_value(f"Voir {person.token}.")
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"].text == f"Voir {person.canonical}."
    app.button(key="restore_new").click().run()
    app.button(key="restore_new_confirm").click().run()
    assert app.session_state["restore_uploaded_table"] is None


def test_literal_tokens_show_an_english_localized_warning() -> None:
    """Un jeton déjà présent dans le document reçoit un avertissement anglais centralisé."""
    app = AppTest.from_file(APP_PATH, default_timeout=120).run()
    app.text_area(key="paste_widget").set_value("M. Pierre VERNOLAC : [PERSONNE_1].").run()
    app.button(key="detect").click().run()
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["pseudo_result"].warnings
    assert [warning.value for warning in app.warning] == [t("restore.send.literal_tokens")]


def test_uploaded_filename_cannot_embed_an_external_markdown_image() -> None:
    """Le nom du fichier est affiché littéralement, même s'il ressemble à une image Markdown."""
    app = AppTest.from_file(APP_PATH, default_timeout=120).run()
    name = "![tracking](https&#58;&#47;&#47;example.invalid).txt"
    app.file_uploader[0].upload(name, b"Texte fictif.").run()
    assert not app.exception
    caption = next(item.value for item in app.caption if item.value.startswith("Source:"))
    assert name not in caption
    assert r"\!\[tracking\]\(" in caption
    assert "&amp;" in caption
