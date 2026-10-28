"""Tests AppTest de S24 : contrôle final avant envoi et mémoire de dossier.

Entrées : textes fictifs collés dans l'interface et tables produites en mémoire.
Sorties : assertions sur la carte "Final check", "Mask everywhere", l'import d'une table de
dossier à l'étape Import, les jetons stables et la restauration d'une réponse mêlée.
"""

import builtins
import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.steps.review_decisions import Decision
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.case_memory import MAX_TABLE_BYTES
from huisclos.pseudonymize.mapping import Mapping
from huisclos.pseudonymize.tokens import pseudonymize

APP_PATH = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
TIMEOUT = 120
CASE_KEY = "case_table_upload_0_0"
PLANTED = "M. Pierre VERNOLAC conteste la rupture. Le dossier vernolac reste ouvert."
DOC1 = (
    "Note du 3 mars 2026. M. Pierre VERNOLAC conteste son licenciement. "
    "Mme Élodie MÉRANSAC témoigne."
)
DOC2 = (
    "Courrier du 9 avril 2026. Le dossier de elodie meransac est complet. "
    "M. Pierre VERNOLAC répond. Mme Hélène QUISTRAL confirme."
)


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def start() -> AppTest:
    """Ouvre l'application sur l'étape Import."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    assert not app.exception
    return app


def detect_text(app: AppTest, text: str) -> AppTest:
    """Colle un texte puis lance la détection."""
    app.text_area(key="paste_widget").set_value(text).run()
    app.button(key="detect").click().run()
    assert not app.exception
    assert app.session_state["step"] == "review"
    return app


def pseudonymize_app(app: AppTest) -> AppTest:
    """Clique sur Pseudonymize et vérifie l'arrivée sur Restore."""
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
    return app


def messages(elements: Any) -> list[str]:
    """Textes d'une liste d'éléments Streamlit (succès, alertes, erreurs, infos)."""
    return [element.value for element in elements]


def token_of(mapping: Mapping, canonical: str) -> str:
    """Jeton de l'entité dont la forme canonique est donnée."""
    return next(entry.token for entry in mapping.entities if entry.canonical == canonical)


def small_table() -> bytes:
    """Table valide d'un document fictif, au format exporté par Restore."""
    text = "M. Pierre VERNOLAC conteste."
    detection = Detection(3, 18, EntityType.PERSON, 1.0, Source.MANUAL, "Pierre VERNOLAC")
    return pseudonymize(text, [detection]).mapping.to_json().encode("utf-8")


def test_demo_case_shows_no_residual_without_promising_anonymity() -> None:
    app = start()
    app.button(key="load_sample").click().run()
    app.button(key="detect").click().run()
    app = pseudonymize_app(app)
    assert "Final check" in messages(app.main.subheader)
    assert "No residual identifier found." in messages(app.success)
    assert not any("Possible identifiers" in text for text in messages(app.warning))
    captions = " ".join(messages(app.caption))
    assert "it does not make the text anonymous" in captions


def test_planted_residual_is_reported_then_masked_everywhere() -> None:
    app = pseudonymize_app(detect_text(start(), PLANTED))
    assert "vernolac" in app.session_state["pseudo_result"].text
    assert any("Possible identifiers left in clear: 1" in w for w in messages(app.warning))
    assert any("vernolac" in block.value for block in app.get("html"))
    app.button(key="check_mask_0").click().run()
    assert not app.exception
    result = app.session_state["pseudo_result"]
    assert "vernolac" not in result.text
    assert result.text.count("[PERSONNE_1]") == 2
    assert "No residual identifier found." in messages(app.success)
    assert any("is now masked everywhere (1 occurrences added)" in s for s in messages(app.success))
    manual = app.session_state["manual_entities"]
    assert [(d.text, d.entity_type) for d in manual] == [("vernolac", EntityType.PERSON)]


def test_rejected_value_raises_no_alert() -> None:
    app = start()
    app.button(key="load_sample").click().run()
    app.button(key="detect").click().run()
    companies = [
        d for d in app.session_state["detections"] if d.entity_type is EntityType.ORGANIZATION
    ]
    assert companies
    app.session_state["group_decisions"] = {
        (d.start, d.end): Decision(masked=False) for d in companies
    }
    app = pseudonymize_app(app.run())
    assert companies[0].text in app.session_state["pseudo_result"].text
    assert "No residual identifier found." in messages(app.success)


def test_case_table_keeps_tokens_and_restores_a_mixed_answer() -> None:
    first = pseudonymize_app(detect_text(start(), DOC1))
    table = first.session_state["pseudo_result"].mapping
    vernolac = token_of(table, "Pierre VERNOLAC")
    meransac = token_of(table, "Élodie MÉRANSAC")
    app = start()
    exported = table.to_json().encode("utf-8")
    app.file_uploader(key=CASE_KEY).upload("huisclos-0a1b2c3d.mapping.json", exported).run()
    assert not app.exception
    assert any("Case table in use" in info for info in messages(app.info))
    app = detect_text(app, DOC2)
    known = [d for d in app.session_state["detections"] if d.source is Source.CASE_TABLE]
    assert "elodie meransac" in [d.text for d in known]
    app = pseudonymize_app(app)
    result = app.session_state["pseudo_result"]
    assert f"Le dossier de {meransac} est complet" in result.text
    assert f"M. {vernolac} répond" in result.text
    assert "Mme [PERSONNE_3] confirme" in result.text
    assert "No residual identifier found." in messages(app.success)
    answer = f"{vernolac} et {meransac} ont rencontré [PERSONNE_3]."
    app.text_area(key="restore_answer").set_value(answer)
    app.button(key="restore_run").click().run()
    assert app.session_state["restore_result"].text == (
        "Pierre VERNOLAC et Élodie MÉRANSAC ont rencontré Hélène QUISTRAL."
    )
    merged = [entry.canonical for entry in result.mapping.entities]
    assert merged == ["Pierre VERNOLAC", "Élodie MÉRANSAC", "Hélène QUISTRAL"]


def test_invalid_case_table_is_refused_and_leaves_the_session_unchanged() -> None:
    app = detect_text(start(), PLANTED)
    detections = app.session_state["detections"]
    signature = app.session_state["detection_signature"]
    app.button(key="review_back").click().run()
    uploader = app.file_uploader(key=CASE_KEY)
    uploader.upload("dossier.mapping.json", b"not json").run()
    assert any("not a valid HuisClos mapping table" in e for e in messages(app.error))
    assert app.session_state["case_table"] is None
    assert app.session_state["detections"] == detections
    assert app.session_state["detection_signature"] == signature
    app.file_uploader(key=CASE_KEY).upload("dossier.mapping.json", small_table()).run()
    table = app.session_state["case_table"]
    assert table is not None
    app.file_uploader(key=CASE_KEY).upload("big.json", b" " * (MAX_TABLE_BYTES + 1)).run()
    assert any("larger than 2 MB" in e for e in messages(app.error))
    assert app.session_state["case_table"] == table
    assert "The case table loaded before is still in use." in messages(app.caption)
    app.button(key="case_remove").click().run()
    assert app.session_state["case_table"] is None
    assert not app.exception


def test_case_table_is_kept_in_memory_only(monkeypatch: pytest.MonkeyPatch) -> None:
    app = start()

    def guard(original: Callable[..., Any]) -> Callable[..., Any]:
        """Refuse toute ouverture de fichier en écriture pendant le chargement de la table."""

        def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
            """Transmet uniquement les lectures."""
            if any(flag in mode for flag in "wax+"):
                raise AssertionError(f"écriture disque interdite : {file}")
            return original(file, mode, *args, **kwargs)

        return guarded

    monkeypatch.setattr(builtins, "open", guard(builtins.open))
    monkeypatch.setattr(io, "open", guard(io.open))
    app.file_uploader(key=CASE_KEY).upload("dossier.mapping.json", small_table()).run()
    assert not app.exception
    assert app.session_state["case_table"] is not None
    app = detect_text(app, "Le dossier de Pierre Vernolac est clos.")
    pseudonymize_app(app)
    assert "Pierre Vernolac" not in app.session_state["pseudo_result"].text


def test_final_check_and_case_block_are_translated_in_french() -> None:
    app = start()
    app.selectbox(key="language").select("fr").run()
    labels = [expander.label for expander in app.expander]
    assert "Poursuivre un dossier (facultatif)" in labels
    # AppTest relit le sélecteur de type de Review hors session, donc en anglais : le
    # parcours se fait en anglais et le français est choisi à l'étape Restore.
    app = start()
    app = pseudonymize_app(detect_text(app, PLANTED))
    app.selectbox(key="language").select("fr").run()
    assert not app.exception
    assert "Contrôle final" in messages(app.main.subheader)
    assert app.button(key="check_mask_0").label == "Masquer partout"
    assert any("Identifiants possibles restés en clair : 1" in w for w in messages(app.warning))
