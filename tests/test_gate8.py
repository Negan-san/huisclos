"""Contrôle indépendant G8 sur des valeurs fictives nouvelles.

Entrées : langues d'interface et de document croisées, tables et transport simulé.
Sorties : preuves du payload exact, des révocations et de la mémoire de dossier.
Le harnais est vérifié sans consulter les annotations des corpus réservés.
"""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
import requests
from streamlit.testing.v1 import AppTest

from app import i18n
from huisclos.config import profile_config
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.case_memory import find_known
from huisclos.pseudonymize.mapping import Mapping
from huisclos.pseudonymize.outbound_check import (
    CheckStatus,
    check_status,
    compose,
    document_alerts,
    instruction_alerts,
)
from huisclos.pseudonymize.reidentify import restore
from huisclos.pseudonymize.tokens import pseudonymize
from scripts import gate8_measure

ROOT = Path(__file__).resolve().parents[1]
TEXTS = {
    "fr": ("M. Lucien FALVERAC signe.", "M. Lucien FALVERAC appelle Mme Alice BRENOUX."),
    "en": ("Mr Nolan FALVERICK signs.", "Mr Nolan FALVERICK calls Ms Alice BRENWICK."),
}


@pytest.mark.parametrize("ui", ("fr", "en"))
@pytest.mark.parametrize("language", ("fr", "en"))
def test_public_demo_and_absent_model_in_each_language(
    ui: str, language: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le mode public retire Enhanced et un paquet absent ne déclenche aucun repli."""
    from app.engine import _cached_analyzer
    from huisclos.detection import gliner, pipeline
    from huisclos.detection.pipeline import ModelUnavailableError

    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    app.selectbox(key="language").select(ui).run()
    app.radio(key="document_language").set_value(language).run()
    app.radio(key="detection_profile").set_value("enhanced").run()
    monkeypatch.setenv("HUISCLOS_PUBLIC_DEMO", "true")
    app.run()
    assert not app.exception
    assert app.session_state["detection_profile"] == "standard"
    assert len(app.radio(key="detection_profile").options) == 1
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO")
    app.run()
    app.radio(key="detection_profile").set_value("enhanced").run()

    def absent() -> Any:
        """Simule une ressource absente avant toute inférence locale."""
        raise ModelUnavailableError("missing" if language == "fr" else "local_missing")

    monkeypatch.setattr(pipeline, "check_camembert_snapshot", absent)
    monkeypatch.setattr(gliner, "prepare", absent)
    pipeline.build_analyzer.cache_clear()
    _cached_analyzer.clear()
    app.text_area(key="paste_widget").set_value(TEXTS[language][0]).run()
    app.button(key="detect").click().run()
    assert not app.exception
    assert app.error
    assert app.session_state["step"] == "import"
    assert app.session_state["detections"] is None
    assert app.session_state["detection_profile"] == "enhanced"
    _cached_analyzer.clear()


@pytest.fixture(autouse=True)
def strict_local(monkeypatch: pytest.MonkeyPatch) -> None:
    """Impose des traductions connues et aucune clé ni démonstration héritée."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)


def journey(ui: str, language: str, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Traverse les trois étapes dans ui, avec le même formateur hors session AppTest."""
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120)
    app.secrets = {}
    app.run()
    app.selectbox(key="language").select(ui).run()
    # AppTest sérialise les sélecteurs hors du contexte Streamlit. Seul ce repli de test
    # suit la langue choisie ; pendant le script, la vraie session reste la référence.
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", ui)
    app.radio(key="document_language").set_value(language).run()
    app.text_area(key="paste_widget").set_value(TEXTS[language][0]).run()
    app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
    return app


@pytest.mark.parametrize("ui", ("fr", "en"))
@pytest.mark.parametrize("language", ("fr", "en"))
def test_crossed_payload_and_instruction_alerts(
    ui: str, language: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Les quatre parcours contrôlent puis envoient exactement la chaîne approuvée."""
    post = Mock(
        return_value=Mock(
            status_code=200,
            json=Mock(return_value={"choices": [{"message": {"content": "[PERSONNE_1]"}}]}),
        )
    )
    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setenv("MISTRAL_API_KEY", "gate8-fake-key")
    app = journey(ui, language, monkeypatch)
    result = app.session_state["pseudo_result"]
    assert len(result.mapping.entities) == 1
    assert app.session_state["document_language"] == language
    app.text_area(key="outbound_instruction_widget").set_value(
        "Contact gate8.residual@example.org."
    ).run()
    assert app.button(key="mistral_send").disabled
    assert app.get("download_button")[0].disabled
    assert all(not box.value for box in app.checkbox if box.key.startswith("check_ack_"))
    app.text_area(key="outbound_instruction_widget").set_value("[PERSONNE_989]").run()
    assert app.button(key="mistral_send").disabled
    assert not [box for box in app.checkbox if box.key.startswith("check_ack_")]
    instruction = "Use [PERSONNE_1]."
    app.text_area(key="outbound_instruction_widget").set_value(instruction).run()
    app.checkbox(key="mistral_confirm").check().run()
    expected = compose(result.text, instruction).content
    assert app.code[0].value == expected.strip()
    post.assert_not_called()
    app.button(key="mistral_send").click().run()
    assert not app.exception
    post.assert_called_once()
    payload = post.call_args.kwargs["json"]
    assert payload["messages"] == [{"role": "user", "content": expected}]
    body = json.dumps(payload)
    assert result.mapping.to_json() not in body
    assert all(entry.canonical not in body for entry in result.mapping.entities)
    assert "pseudonymized_sha256" not in body
    assert app.session_state["outbound_send_authorization"] is None


@pytest.mark.parametrize("change", ("source", "language", "profile", "table", "review", "tokens"))
def test_python_guard_revokes_every_data_change(
    change: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un clic forcé après modification de l'état ne passe jamais la garde Python."""
    post = Mock()
    monkeypatch.setattr(requests, "post", post)
    monkeypatch.setenv("MISTRAL_API_KEY", "gate8-fake-key")
    app = journey("en", "fr", monkeypatch)
    app.checkbox(key="mistral_confirm").check().run()
    assert app.session_state["outbound_send_authorization"]
    if change == "source":
        app.session_state["source_text"] += " Another paragraph."
    elif change == "language":
        app.session_state["document_language"] = "en"
    elif change == "profile":
        app.session_state["detection_profile"] = "enhanced"
    elif change == "table":
        app.session_state["case_table"] = app.session_state["pseudo_result"].mapping
    elif change == "review":
        app.session_state["manual_entities"] = [
            Detection(0, 2, EntityType.CUSTOM, 1.0, Source.MANUAL, "M.")
        ]
    else:
        app.session_state["token_style"] = "en"
    app.button(key="mistral_send").click().run()
    assert not app.exception
    post.assert_not_called()
    assert app.session_state["outbound_send_authorization"] is None
    assert app.button(key="mistral_send").disabled


@pytest.mark.parametrize("language", ("fr", "en"))
def test_two_documents_and_planted_residuals(language: str, no_network: None) -> None:
    """Deux documents gardent leurs jetons, restaurent une réponse mêlée et alertent par segment."""
    config = profile_config("standard", language)
    first, second = TEXTS[language]
    one = pseudonymize(first, detect(first, config))
    two = pseudonymize(
        second, detect(second, config, find_known(second, one.mapping)), known=one.mapping
    )
    reloaded = Mapping.from_json(two.mapping.to_json())
    assert restore(one.text, one.mapping).text == first
    assert restore(two.text, reloaded).text == second
    assert [e.token for e in reloaded.entities] == ["[PERSONNE_1]", "[PERSONNE_2]"]
    reply = " / ".join(e.token for e in reloaded.entities)
    assert restore(reply, reloaded).text == " / ".join(e.canonical for e in reloaded.entities)
    value = one.mapping.entities[0].canonical
    planted = replace(two, text=two.text + " " + value)
    message = compose(planted.text, "Contact " + value)
    document = document_alerts(message, planted, lambda text: detect(text, config))
    instruction = instruction_alerts(message, planted, lambda text: detect(text, config))
    assert document and instruction
    assert {a.segment for a in document + instruction} == {"document", "instruction"}
    assert check_status(document + instruction, ()) is CheckStatus.ALERTS
    # Un rejet positionnel ne supprime pas la même valeur dans un autre passage.
    original = second + " " + value
    result = pseudonymize(original, [])
    alerts = document_alerts(
        compose(result.text, ""),
        result,
        lambda text: detect(text, config),
        original,
        [(second.index(value), second.index(value) + len(value))],
    )
    assert any(a.start >= len(second) for a in alerts)
    gap = replace(
        one.mapping,
        entities=tuple(replace(entry, token="[PERSONNE_3]") for entry in one.mapping.entities),
        occurrences=(),
    )
    filled = pseudonymize(second, detect(second, config, find_known(second, gap)), known=gap)
    assert [entry.token for entry in filled.mapping.entities] == ["[PERSONNE_3]", "[PERSONNE_1]"]


def test_gate_worker_uses_source_context_and_does_not_mask_alerts(no_network: None) -> None:
    """Le worker corrigé trouve un prénom résiduel seulement visible dans le contexte source."""
    text = "Marc-Etienne FALVERAC"
    start = text.index("FALVERAC")
    partial = Detection(start, len(text), EntityType.PERSON, 0.9, Source.MANUAL, text[start:])
    result = pseudonymize(text, [partial])

    def context_only(value: str, config: Any) -> list[Detection]:
        """Le faux modèle ne connaît que le nom complet dans la phrase intacte."""
        return (
            [Detection(0, len(text), EntityType.PERSON, 0.9, Source.PATTERN, text)]
            if value == text
            else []
        )

    api = SimpleNamespace(detect=context_only, final_check=True)
    before = result.text
    alerts = gate8_measure.final_alerts(api, result, text, object())
    assert alerts == [[0, len("Marc-Etienne")]]
    assert result.text == before


def test_gate_worker_failure_never_discloses_reserved_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un worker en échec ne révèle ni stderr, ni texte d'entrée."""
    monkeypatch.setattr(
        gate8_measure.subprocess,
        "run",
        Mock(
            return_value=SimpleNamespace(
                returncode=7, stderr="private value", stdout="private value"
            )
        ),
    )
    with pytest.raises(RuntimeError, match="exit 7") as caught:
        gate8_measure.run_separate(
            {"preset": "hybrid", "threshold": 0.3}, ["private value"], "en", "gate"
        )
    assert "private value" not in str(caught.value)


def test_gate_worker_reuses_one_main_detection_per_document(
    monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    """Les métriques et les coûts ne provoquent aucune deuxième détection principale."""
    from huisclos.detection import pipeline

    text = "Lucien FALVERAC"
    detection = Detection(0, len(text), EntityType.PERSON, 0.9, Source.PATTERN, text)
    detector = Mock(return_value=[detection])
    api = SimpleNamespace(
        presets={"fake": profile_config("standard", "fr")},
        detect=detector,
        pseudonymize=pseudonymize,
        final_check=None,
    )
    monkeypatch.setattr(pipeline, "analyzer_for", Mock())
    monkeypatch.setattr(gate8_measure.pilot, "measured_metadata", lambda *args: {"versions": {}})
    payload = gate8_measure.stage_outputs([text, text], "fake", 0.3, "fr", api)
    assert detector.call_count == 2
    assert payload["metadata"]["resources"]["main_detection_calls"] == 2
    assert len(payload["documents"]) == 2
    assert all(set(row) == {"detections", "occurrences", "alerts"} for row in payload["documents"])
    assert text not in json.dumps(payload)


@pytest.mark.xfail(
    strict=True, reason="G8-01 : le harnais perd les prédictions si le contrôle échoue"
)
def test_unavailable_final_check_preserves_main_predictions(
    monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    """Une panne finale injectée devrait laisser les métriques principales mesurables.

    Ce défaut de harnais est établi sans corpus ; son lien avec l'échec challenge est inconnu.
    Le contrôle doit rester indisponible, jamais être présenté comme une absence d'alerte.
    """
    from huisclos.detection import pipeline

    text = "Lucien FALVERAC"
    detection = Detection(0, len(text), EntityType.PERSON, 0.9, Source.PATTERN, text)
    api = SimpleNamespace(
        presets={"fake": profile_config("standard", "fr")},
        detect=Mock(return_value=[detection]),
        pseudonymize=pseudonymize,
        final_check=True,
        check_threshold=lambda threshold: 0.1,
    )
    monkeypatch.setattr(pipeline, "analyzer_for", Mock())
    monkeypatch.setattr(
        gate8_measure, "final_alerts", Mock(side_effect=RuntimeError("Fictive outage"))
    )
    payload = gate8_measure.stage_outputs([text], "fake", 0.3, "fr", api)
    assert payload["documents"][0]["detections"]
    assert payload["documents"][0]["alerts"] is None
