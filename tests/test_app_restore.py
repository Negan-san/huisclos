"""Tests de l'écran Restore avec AppTest : texte à envoyer, restauration, exports, remise à zéro.

Le cas d'exemple est pseudonymisé une seule fois pour tout le module ; chaque test ouvre
ensuite l'écran Restore sur ce résultat, sans refaire la détection. Un seul test déroule le
parcours complet Import, Review, Restore par l'interface.
"""

import re
from dataclasses import replace
from pathlib import Path

import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.steps import restore_step
from app.ui_common import entity_label
from huisclos.models import EntityType, PseudonymizationResult

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT / "streamlit_app.py")
TIMEOUT = 120
SENSITIVE_WARNING = (
    "Sensitive file: it links tokens to real identities. Keep it on this computer. "
    "Never send it to an AI tool."
)
DOWNLOAD_LABELS = [
    "Pseudonymized text (.txt)",
    "Pseudonymized text (.docx)",
    "Restored text (.txt)",
    "Restored text (.docx)",
    "Mapping table (.mapping.json)",
]


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def journey() -> AppTest:
    """Déroule Import, Review puis Pseudonymize sur le cas d'exemple, par l'interface."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app = app.button(key="load_sample").click().run()
    app = app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    app = app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    return app


@pytest.fixture(scope="module")
def sample() -> tuple[str, PseudonymizationResult]:
    """Texte source du cas d'exemple et son résultat de pseudonymisation."""
    app = journey()
    return app.session_state["source_text"], app.session_state["pseudo_result"]


def restore_app(result: PseudonymizationResult | None) -> AppTest:
    """Ouvre l'écran Restore sur un résultat imposé, sans passer par l'import."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.session_state["pseudo_result"] = result
    app.session_state["step"] = "restore"
    app.run()
    assert not app.exception
    return app


def restore_answer(app: AppTest, answer: str) -> AppTest:
    """Colle une réponse puis clique sur Restore."""
    app.text_area(key="restore_answer").set_value(answer)
    app.button(key="restore_run").click().run()
    assert not app.exception
    return app


def upload_table(app: AppTest, content: bytes, name: str = "dossier.mapping.json") -> AppTest:
    """Téléverse un fichier dans le sélecteur de table de correspondance."""
    app.file_uploader(key="restore_table_upload_0").upload(name, content).run()
    assert not app.exception
    return app


def shown_blocks(app: AppTest) -> list[str]:
    """Rassemble le texte des blocs de code affichés par la page."""
    return [block.value for block in app.code]


def restored_text(app: AppTest) -> str | None:
    """Renvoie le texte restauré affiché, ou None tant que rien n'est restauré."""
    blocks = [element for element in app.main if type(element).__name__ in {"Markdown", "Code"}]
    for position, element in enumerate(blocks[:-1]):
        if getattr(element, "value", "") == "**Restored text**":
            return blocks[position + 1].value
    return None


def download_buttons(app: AppTest) -> dict[str, bool]:
    """Relit les boutons de téléchargement : libellé vers état désactivé."""
    return {button.label: button.disabled for button in app.get("download_button")}


def current_step(app: AppTest) -> str:
    """Renvoie l'unique étape de l'indicateur marquée aria-current="step"."""
    stepper = next(b.value for b in app.get("html") if 'class="hc-stepper"' in b.value)
    current = [i for i in re.findall(r"<li .*?</li>", stepper) if 'aria-current="step"' in i]
    assert len(current) == 1
    return current[0]


def token_of(result: PseudonymizationResult, kind: EntityType) -> tuple[str, str]:
    """Renvoie le jeton et la forme canonique de la première entité du type donné."""
    entry = next(e for e in result.mapping.entities if e.entity_type is kind)
    return entry.token, entry.canonical


def altered(token: str) -> str:
    """Abîme un jeton comme le ferait un LLM : minuscules et espace à la place du tiret bas."""
    return token.lower().replace("_", " ")


def test_complete_journey_ends_on_the_restore_step() -> None:
    app = journey()
    assert app.session_state["step"] == "restore"
    assert not app.exception
    assert '<span class="hc-step-name">Restore</span>' in current_step(app)
    assert [element.value for element in app.main.subheader] == [
        "Final check",
        "Send to your AI tool",
        "Restore the AI answer",
        "Download",
    ]


def test_pseudonymized_text_shown_contains_no_detected_value(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_app(result)
    shown = shown_blocks(app)[0]
    assert shown == result.text.strip()
    originals = {occurrence.original for occurrence in result.mapping.occurrences}
    assert originals
    assert [value for value in originals if value in shown] == []
    assert "[PERSONNE_1]" in shown
    assert "What leaves your computer: only the text above. The mapping table stays here." in [
        message.value for message in app.info
    ]


def test_token_counts_by_type_match_the_mapping(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_app(result)
    tables = [
        pa.ipc.open_stream(element.proto.arrow_data.data).read_all()
        for element in app.get("dataframe")
    ]
    rows = tables[0].to_pylist()
    assert list(rows[0]) == ["Type", "Tokens", "Occurrences"]
    assert sum(row["Tokens"] for row in rows) == len(result.mapping.entities)
    assert sum(row["Occurrences"] for row in rows) == len(result.mapping.occurrences)
    assert entity_label(EntityType.PERSON) in {row["Type"] for row in rows}


def test_recommended_instructions_are_offered_in_french_and_english(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    shown = shown_blocks(restore_app(result))
    assert (
        "Conserve exactement chaque jeton entre crochets, par exemple [PERSONNE_1], sans le "
        "modifier ni le traduire, et n'en invente aucun."
    ) in shown
    assert (
        "Keep every bracketed token exactly as written, for example [PERSON_1]; do not "
        "change, translate or invent tokens."
    ) in shown


def test_pasting_the_pseudonymized_text_restores_the_original_exactly(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    source, result = sample
    app = restore_answer(restore_app(result), result.text)
    assert restored_text(app) == source.strip()
    assert [message.value for message in app.warning] == []
    assert any("Exact mode" in caption.value for caption in app.caption)


def test_restored_values_are_highlighted_with_a_type_label(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    person, person_name = token_of(result, EntityType.PERSON)
    app = restore_answer(restore_app(result), f"Note pour {person}. Voir [PERSONNE_99].")
    document = next(h.value for h in app.get("html") if "hc-document" in h.value)
    assert f">{person_name}</mark>" in document
    assert ">PERSON</span>" in document
    assert "[PERSONNE_99]" in document
    assert "[PERSONNE_99]</mark>" not in document


def test_altered_tokens_are_restored_and_an_invented_token_warns(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    person, person_name = token_of(result, EntityType.PERSON)
    email, email_value = token_of(result, EntityType.EMAIL)
    answer = f"Bonjour {altered(person)}, écrivez à ({email.strip('[]')}). Voir [PERSONNE_99]."
    app = restore_answer(restore_app(result), answer)
    text = restored_text(app)
    assert text is not None
    assert text.startswith(f"Bonjour {person_name}, écrivez à {email_value}. Voir ")
    assert text.endswith("[PERSONNE_99].")
    unknown = [message.value for message in app.warning if "Unknown tokens" in message.value]
    assert len(unknown) == 1
    assert "`[PERSONNE_99]`" in unknown[0]
    recognized = [message.value for message in app.info if "Altered tokens" in message.value]
    assert len(recognized) == 1
    assert f"`{altered(person)}` read as `{person}`" in recognized[0]
    assert any("Tolerant mode" in caption.value for caption in app.caption)


def test_an_answer_without_token_is_reported(sample: tuple[str, PseudonymizationResult]) -> None:
    _, result = sample
    app = restore_answer(restore_app(result), "Une réponse sans aucun jeton.")
    assert restored_text(app) == "Une réponse sans aucun jeton."
    assert any("No token was found" in message.value for message in app.info)


def test_restoring_an_empty_answer_asks_to_paste_one(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_app(result)
    app.button(key="restore_run").click().run()
    assert not app.exception
    assert [message.value for message in app.warning] == ["Paste the answer of the AI tool first."]
    assert restored_text(app) is None


def test_changing_the_answer_hides_the_previous_restoration(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_answer(restore_app(result), result.text)
    assert download_buttons(app)["Restored text (.txt)"] is False
    app.text_area(key="restore_answer").set_value("Autre réponse.").run()
    assert restored_text(app) is None
    assert download_buttons(app)["Restored text (.txt)"] is True


def test_five_download_buttons_and_the_warning_comes_before_the_mapping(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_app(result)
    assert list(download_buttons(app)) == DOWNLOAD_LABELS
    assert download_buttons(app) == {
        "Pseudonymized text (.txt)": False,
        "Pseudonymized text (.docx)": False,
        "Restored text (.txt)": True,
        "Restored text (.docx)": True,
        "Mapping table (.mapping.json)": False,
    }
    names = [type(element).__name__ for element in app.main]
    labels = [getattr(element, "label", "") for element in app.main]
    warning_at = [
        i
        for i, element in enumerate(app.main)
        if names[i] == "Error" and element.value == SENSITIVE_WARNING
    ]
    mapping_at = labels.index("Mapping table (.mapping.json)")
    assert len(warning_at) == 1
    assert warning_at[0] < mapping_at
    app = restore_answer(app, result.text)
    assert not any(download_buttons(app)[label] for label in DOWNLOAD_LABELS)


def test_a_valid_table_is_imported_and_used_to_restore(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    source, result = sample
    app = restore_app(None)
    assert [message.value for message in app.info][0].startswith("Nothing to restore yet")
    assert not app.text_area
    app = upload_table(app, result.mapping.to_json().encode("utf-8"))
    assert [message.value for message in app.error] == []
    assert any(r"dossier\.mapping\.json" in caption.value for caption in app.caption)
    person, person_name = token_of(result, EntityType.PERSON)
    app = restore_answer(app, f"Réponse reçue plus tard : {person}.")
    assert restored_text(app) == f"Réponse reçue plus tard : {person_name}."
    app = restore_answer(app, result.text)
    assert restored_text(app) == source.strip()


def test_an_imported_table_replaces_the_one_of_the_document(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    person, _ = token_of(result, EntityType.PERSON)
    entities = tuple(
        replace(entry, canonical="Zoé MARTIN") if entry.token == person else entry
        for entry in result.mapping.entities
    )
    other = replace(result.mapping, entities=entities)
    app = restore_app(result)
    app = upload_table(app, other.to_json().encode("utf-8"))
    app = restore_answer(app, f"Voir {person}.")
    assert restored_text(app) == "Voir Zoé MARTIN."


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"{ceci n'est pas du json", "not a valid HuisClos mapping table"),
        (b'{"schema": "autre", "version": 1}', "not a valid HuisClos mapping table"),
        (b"[1, 2, 3]", "not a valid HuisClos mapping table"),
        (b"[" * 5000, "not a valid HuisClos mapping table"),
        pytest.param(
            b'{"version":' + b"1" * 5000 + b"}",
            "not a valid HuisClos mapping table",
            id="large-integer",
        ),
        (b"\xff\xfe\x00\x01", "not readable text"),
    ],
)
def test_an_invalid_table_shows_a_clear_error_and_no_exception(
    sample: tuple[str, PseudonymizationResult], content: bytes, expected: str
) -> None:
    _, result = sample
    app = upload_table(restore_app(result), content)
    errors = [message.value for message in app.error]
    assert len([message for message in errors if expected in message]) == 1
    assert any("the one built from the current document" in c.value for c in app.caption)
    app = restore_answer(app, result.text)
    assert restored_text(app) is not None


def test_an_invalid_table_without_document_leaves_nothing_to_restore() -> None:
    app = upload_table(restore_app(None), b"{pas du json")
    assert any("not a valid HuisClos mapping table" in m.value for m in app.error)
    assert not app.text_area


def test_back_to_review_returns_to_the_review_step(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_app(result)
    app.button(key="restore_back_review").click().run()
    assert app.session_state["step"] == "review"
    assert app.session_state["pseudo_result"] is not None


def test_start_a_new_document_clears_the_session_after_confirmation(
    sample: tuple[str, PseudonymizationResult],
) -> None:
    _, result = sample
    app = restore_answer(restore_app(result), result.text)
    assert any("does not keep the mapping table" in c.value for c in app.caption)
    app.button(key="restore_new").click().run()
    assert any("cannot be recovered" in message.value for message in app.warning)
    assert app.session_state["pseudo_result"] is not None
    app.button(key="restore_new_cancel").click().run()
    assert app.session_state["pseudo_result"] is not None
    app.button(key="restore_new").click().run()
    app.button(key="restore_new_confirm").click().run()
    assert not app.exception
    assert app.session_state["step"] == "import"
    assert app.session_state["source_text"] == ""
    assert app.session_state["pseudo_result"] is None
    assert app.session_state["restore_result"] is None
    assert app.session_state["llm_response"] == ""
    assert app.session_state["upload_nonce"] == 1


def test_the_mistral_slot_shows_nothing(sample: tuple[str, PseudonymizationResult]) -> None:
    _, result = sample
    assert restore_step.render_mistral_slot(result.text) is None
    app = restore_app(result)
    texts = [str(getattr(element, "value", "")) for element in app.main]
    assert not any("Mistral" in text for text in texts)
