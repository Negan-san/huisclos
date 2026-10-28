"""Recette locale R8 : parcours complet de l'interface sur des documents fictifs FR et EN.

Entrées : documents entièrement fictifs écrits pour cette recette, profils Standard et
Enhanced local (modèles déjà présents), langue d'interface distincte de celle du document.
Sorties : assertions AppTest sur Import, Review, contrôle final, envoi simulé, Restore et
second document avec table de dossier ; résumé JSON dans results/recette8/.
Aucun appel réseau : les connexions sont refusées et le transport Mistral est remplacé.
"""

import json
import socket
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.steps import restore_mistral
from app.steps.review_decisions import Decision
from huisclos.pseudonymize.mapping import Mapping

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/recette8"
MODELS_DIR = ROOT.parent / "pilotage/post_g7_assets"
TIMEOUT = 300
# Documents fictifs : chaque nom figure aussi dans un nom de fichier (collision FIX2-01).
DOCS = {
    "fr": (
        "Le 12 février 2026, M. Bastien KORVALEC a saisi le conseil de prud'hommes. "
        "Courriel : bastien.korvalec@example.fr. Mme Ysolde FERNAVIC représente la "
        "société TALMIRAC SARL. Pièce : attestation_KORVALEC.pdf. Code d'accès : quernil42."
    ),
    "en": (
        "On 12 February 2026, Mr Dorian HALVERSTOKE filed the claim. "
        "Email: dorian.halverstoke@example.co.uk. Ms Wrenna CALDOVY acts for "
        "BRAMWICK LIMITED. Exhibit: statement_HALVERSTOKE.pdf. Access code: quernil42."
    ),
}
SECOND = {
    "fr": "Le 3 mars 2026, Mme Ysolde FERNAVIC écrit. M. Roderic VANSELME confirme.",
    "en": "On 3 March 2026, Ms Wrenna CALDOVY writes. Mr Roderic VANSELME confirms.",
}
NAMES = {
    "fr": ("Bastien KORVALEC", "Ysolde FERNAVIC", "bastien.korvalec@example.fr"),
    "en": ("Dorian HALVERSTOKE", "Wrenna CALDOVY", "dorian.halverstoke@example.co.uk"),
}
STABLE = {"fr": "Ysolde FERNAVIC", "en": "Wrenna CALDOVY"}
ORGS = {"fr": "TALMIRAC", "en": "BRAMWICK"}
MANUAL = "quernil42"
CLEAN = "Summarise this fictitious file in three points."
CORRECTED = "Summarise this fictitious file in two points."
SENT: list[str] = []
RECORD: dict[str, Any] = {}


REAL_CONNECT = socket.socket.connect
LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def _guarded_connect(sock: socket.socket, address: Any) -> None:
    """Refuse toute connexion hors de la boucle locale.

    Sous Windows, la boucle asyncio de Streamlit ouvre une paire de sockets sur 127.0.0.1 :
    ce lien interne au processus reste permis, aucun autre hôte ne l'est.
    """
    host = address[0] if isinstance(address, tuple) else address
    if host not in LOOPBACK:
        raise RuntimeError("R8: network access forbidden")
    REAL_CONNECT(sock, address)


def _forbidden(*_: object, **__: object) -> None:
    """Refuse toute ouverture de connexion par nom d'hôte pendant la recette."""
    raise RuntimeError("R8: network access forbidden")


def _fake_send(content: str, api_key: str, model: str) -> str:
    """Transport simulé : garde le message exact et renvoie une réponse à jetons."""
    SENT.append(content)
    return RECORD["answer"]


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Interface stricte, aucun réseau, clé fictive et transport Mistral simulé."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    monkeypatch.setenv("MISTRAL_API_KEY", "cle-fictive-r8")
    for name, value in {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    monkeypatch.setattr(restore_mistral, "send_outbound", _fake_send)
    SENT.clear()


def start(ui: str, doc: str, profile: str, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Ouvre l'application, règle UI, langue du document et profil, sans détection."""
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=TIMEOUT).run()
    app.selectbox(key="language").select(ui).run()
    # Même repli que tests/test_fix4.py : AppTest sérialise les sélecteurs hors session.
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", ui)
    app.radio(key="document_language").set_value(doc).run()
    app.radio(key="detection_profile").set_value(profile).run()
    assert not app.exception and app.session_state["detection_profile"] == profile
    return app


def detect(app: AppTest, text: str) -> list[str]:
    """Colle le texte, lance la détection et renvoie les textes détectés."""
    app.text_area(key="paste_widget").set_value(text).run()
    app.button(key="detect").click().run()
    assert not app.exception and app.session_state["step"] == "review"
    return [item.text for item in app.session_state["detections"]]


def check_state(app: AppTest) -> tuple[str, list[Any]]:
    """Statut et alertes des deux segments du dernier contrôle final."""
    statuses, alerts = [], []
    for key in ("outbound_check_document", "outbound_check_instruction"):
        stored = app.session_state[key]
        assert stored is not None, key
        statuses.append(stored[1].value)
        alerts.extend(stored[2] or [])
    return "+".join(statuses), alerts


def set_instruction(app: AppTest, text: str) -> None:
    """Saisit la consigne libre de l'étape Restore."""
    app.text_area(key="outbound_instruction_widget").input(text).run()
    assert not app.exception


def clear_document_alerts(app: AppTest) -> int:
    """Traite les alertes du document par "Mask everywhere" ; renvoie le nombre de clics."""
    clicks = 0
    while clicks < 6:
        _, alerts = check_state(app)
        if not any(alert.segment == "document" for alert in alerts):
            return clicks
        app.button(key="check_mask_0").click().run()
        assert not app.exception
        clicks += 1
    raise AssertionError("document alerts remain after six masking actions")


def ready(app: AppTest) -> bool:
    """Vrai si le message contrôlé peut être confirmé pour l'envoi simulé."""
    return not app.checkbox(key="mistral_confirm").disabled


def confirm(app: AppTest) -> str:
    """Coche la confirmation d'envoi et renvoie l'empreinte autorisée."""
    app.checkbox(key="mistral_confirm").check().run()
    assert not app.exception
    authorized = app.session_state["outbound_send_authorization"]
    assert authorized
    return authorized


def review(app: AppTest, doc: str) -> str | None:
    """Décisions de Review : ajout manuel réel et société laissée en clair par l'humain.

    Valeur retournée : le texte de la société rejetée, ou None si elle n'a pas été détectée.
    """
    app.text_input(key="review_manual_text").input(MANUAL).run()
    app.button(key="review_add_manual").click().run()
    assert not app.exception
    assert any(item.text == MANUAL for item in app.session_state["manual_entities"])
    found = [d for d in app.session_state["detections"] if ORGS[doc] in d.text]
    if not found:
        return None
    decisions = dict(app.session_state["group_decisions"])
    decisions[(found[0].start, found[0].end)] = Decision(masked=False)
    app.session_state["group_decisions"] = decisions
    return found[0].text


def acknowledge_alerts(app: AppTest) -> int:
    """Tranche explicitement les alertes restantes d'une consigne sans identifiant.

    Seules des consignes écrites sans aucune donnée passent ici : une alerte y est donc une
    fausse alerte de prudence, gardée en clair par décision de l'humain.
    """
    count = 0
    while count < 10:
        boxes = [c for c in app.checkbox if (c.key or "").startswith("check_ack_") and not c.value]
        if not boxes:
            return count
        boxes[0].check().run()
        assert not app.exception
        count += 1
    raise AssertionError("too many alerts on an instruction without identifier")


def outbound_and_send(app: AppTest, doc: str, mapping: Mapping) -> dict[str, Any]:
    """Contrôle, alerte plantée dans la consigne, révocation, correction et envoi simulé."""
    person = next(e for e in mapping.entities if e.canonical == NAMES[doc][0])
    unknown = person.token.rsplit("_", 1)[0] + "_99]"
    RECORD["answer"] = f"Summary: {person.token} filed the claim. See {unknown}."
    set_instruction(app, CLEAN)
    masks = clear_document_alerts(app)
    _, first_alerts = check_state(app)
    acks = acknowledge_alerts(app)
    ready_clean = ready(app)
    authorized = confirm(app)
    set_instruction(app, f"Summarise the file of {NAMES[doc][0]}.")
    _, alerts = check_state(app)
    ready_planted = ready(app)
    assert app.session_state["outbound_send_authorization"] is None
    assert any(NAMES[doc][0] in alert.text or alert.text in NAMES[doc][0] for alert in alerts)
    assert not ready_planted
    assert app.button(key="mistral_send").disabled and SENT == []
    set_instruction(app, CORRECTED)
    acks += acknowledge_alerts(app)
    ready_corrected = ready(app)
    second = confirm(app)
    assert second != authorized
    app.checkbox(key="check_policy_no_exclusions").check().run()
    assert app.session_state["outbound_send_authorization"] is None
    app.checkbox(key="check_policy_no_exclusions").uncheck().run()
    clear_document_alerts(app)
    acks += acknowledge_alerts(app)
    confirm(app)
    app.button(key="mistral_send").click().run()
    assert not app.exception and len(SENT) == 1
    sent = SENT[0]
    assert CORRECTED in sent and app.session_state["pseudo_result"].text in sent
    for value in NAMES[doc]:
        assert value not in sent
    assert app.session_state["outbound_send_authorization"] is None
    return {
        "mask_everywhere_clicks": masks,
        "ready_clean": ready_clean,
        "clean_instruction_alerts": [alert.text for alert in first_alerts],
        "acknowledged_false_alerts": acks,
        "ready_planted": ready_planted,
        "ready_corrected": ready_corrected,
        "planted_alerts": len(alerts),
        "sent_characters": len(sent),
    }


def restore(app: AppTest, doc: str) -> dict[str, Any]:
    """Restaure la réponse simulée puis le texte pseudonymisé lui-même (mode exact)."""
    assert app.session_state["llm_response"] == RECORD["answer"]
    app.button(key="restore_run").click().run()
    assert not app.exception
    simulated = app.session_state["restore_result"]
    assert NAMES[doc][0] in simulated.text
    assert len(simulated.unknown) == 1
    pseudo = app.session_state["pseudo_result"]
    app.text_area(key="restore_answer").set_value(pseudo.text)
    app.button(key="restore_run").click().run()
    exact = app.session_state["restore_result"]
    assert not app.exception and exact.mode == "exact" and exact.text == DOCS[doc]
    return {"unknown_tokens": [form for form, _ in simulated.unknown], "exact": True}


def second_document(
    app: AppTest, ui: str, doc: str, mapping: Mapping, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    """Nouveau document, table de dossier importée à Import, jetons garantis stables.

    "Start a new document" vide toute la session, réglages compris : l'utilisateur
    choisit de nouveau la langue d'interface et celle du document.
    """
    app.button(key="restore_new").click().run()
    app.button(key="restore_new_confirm").click().run()
    assert not app.exception and app.session_state["step"] == "import"
    reset_language = app.session_state["language"]
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", "en")
    app.selectbox(key="language").select(ui).run()
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", ui)
    app.radio(key="document_language").set_value(doc).run()
    uploaders = [u for u in app.get("file_uploader") if u.key.startswith("case_table_upload")]
    assert len(uploaders) == 1
    uploaders[0].upload("dossier-fictif.mapping.json", mapping.to_json().encode("utf-8")).run()
    assert not app.exception and app.session_state["case_table"] is not None
    detect(app, SECOND[doc])
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception and app.session_state["step"] == "restore"
    merged = app.session_state["pseudo_result"].mapping
    old = {e.canonical: e.token for e in mapping.entities}
    new = {e.canonical: e.token for e in merged.entities}
    assert new[STABLE[doc]] == old[STABLE[doc]]
    newcomer = new["Roderic VANSELME"]
    assert newcomer not in old.values()
    for value in (STABLE[doc], "Roderic VANSELME"):
        assert value not in app.session_state["pseudo_result"].text
    return {
        "ui_language_after_reset": reset_language,
        "stable_token": new[STABLE[doc]],
        "new_token": newcomer,
    }


def run_case(ui: str, doc: str, profile: str, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """Parcours complet d'un document, avec résumé conservé dans RECORD."""
    app = start(ui, doc, profile, monkeypatch)
    found = detect(app, DOCS[doc])
    rejected = review(app, doc)
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception and app.session_state["step"] == "restore"
    result = app.session_state["pseudo_result"]
    for value in (*NAMES[doc], MANUAL):
        assert value not in result.text
    assert rejected is None or rejected in result.text
    summary = {
        "ui": ui,
        "document": doc,
        "profile": profile,
        "detections": len(found),
        "detection_sources": sorted({d.source.value for d in app.session_state["detections"]}),
        "sidebar_warnings": len(app.sidebar.warning),
        "tokens": len(result.mapping.entities),
        "rejected_by_reviewer": rejected,
    }
    summary |= outbound_and_send(app, doc, result.mapping)
    summary |= restore(app, doc)
    RECORD.setdefault("cases", []).append(summary)
    RECORD["last_mapping"] = result.mapping
    return app


@pytest.mark.parametrize(("ui", "doc"), [("en", "fr"), ("fr", "en")])
def test_standard_two_documents(ui: str, doc: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Standard, langue UI différente du document, puis second document du dossier."""
    app = run_case(ui, doc, "standard", monkeypatch)
    mapping = RECORD["last_mapping"]
    RECORD["cases"][-1] |= second_document(app, ui, doc, mapping, monkeypatch)


@pytest.mark.parametrize(("ui", "doc"), [("fr", "fr"), ("en", "en")])
def test_enhanced_local(ui: str, doc: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Enhanced local avec les modèles déjà présents, sans téléchargement."""
    if not MODELS_DIR.is_dir():
        pytest.skip("local model package absent")
    monkeypatch.setenv("HUISCLOS_MODELS_DIR", str(MODELS_DIR))
    run_case(ui, doc, "enhanced", monkeypatch)


@pytest.mark.parametrize("ui", ["en", "fr"])
def test_method_and_evaluation_pages(ui: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pages Method et Evaluation sans exception, dans les deux langues d'interface."""
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=TIMEOUT).run()
    app.selectbox(key="language").select(ui).run()
    monkeypatch.setattr(i18n, "DEFAULT_LANGUAGE", ui)
    pages = {}
    for page in ("app/pages/method.py", "app/pages/evaluation.py"):
        app.switch_page(page).run()
        assert not app.exception
        texts = [m.value for m in app.markdown] + [c.value for c in app.caption]
        pages[page] = "\n".join(texts)
    RECORD.setdefault("pages", {})[ui] = pages


def test_write_summary() -> None:
    """Écrit le résumé de la recette, sans texte de document ni table de correspondance."""
    cases = RECORD.get("cases", [])
    payload = {
        "cases": cases,
        "network": "socket connections refused; Mistral transport simulated",
        "models_dir_declared_for_enhanced_only": True,
    }
    (OUT / "apptest-summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    pages = RECORD.get("pages", {})
    (OUT / "pages-text.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    assert cases
