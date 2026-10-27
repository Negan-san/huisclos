"""Tests de l'écran Review avec AppTest : décisions, ajout manuel, pseudonymisation.

AppTest ne sait pas cliquer dans un st.data_editor : les modifications du tableau sont
posées dans l'état du composant (edited_rows), comme le navigateur le ferait, puis la page
est relancée. Les lignes du tableau sont relues dans le message Arrow envoyé au navigateur.
"""

from pathlib import Path

import pyarrow as pa
import pytest
from streamlit.testing.v1 import AppTest

from app import i18n
from app.steps.review_step import KEY_TABLE_VERSION, TABLE_KEY_PREFIX, find_occurrences
from huisclos.models import Detection, EntityType, PseudonymizationResult, Source
from huisclos.pseudonymize.grouping import group_mentions

ROOT = Path(__file__).resolve().parent.parent
APP_PATH = str(ROOT / "streamlit_app.py")
TIMEOUT = 120
COURRIEL = (290, 298)


@pytest.fixture(autouse=True)
def strict_i18n(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fait échouer toute clé de texte absente au lieu de l'afficher."""
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)


def review_app() -> AppTest:
    """Lance l'application, charge le cas d'exemple et détecte : l'écran Review s'affiche."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app = app.button(key="load_sample").click().run()
    app = app.button(key="detect").click().run()
    assert not app.exception
    assert app.session_state["step"] == "review"
    return app


def review_app_with(text: str, detections: list[Detection]) -> AppTest:
    """Ouvre l'écran Review sur un texte et des détections imposés, sans passer par l'import."""
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.session_state["source_text"] = text
    app.session_state["detections"] = detections
    app.session_state["step"] = "review"
    return app.run()


def table_rows(app: AppTest) -> list[dict[str, object]]:
    """Relit les lignes du tableau de décision dans le message Arrow du navigateur."""
    for element in app.get("dataframe"):
        table = pa.ipc.open_stream(element.proto.arrow_data.data).read_all()
        if "Mask" in table.column_names:
            return table.to_pylist()
    return []


def type_counts(app: AppTest) -> dict[str, tuple[int, int]]:
    """Relit le tableau des compteurs par type : libellé du type vers (masqués, rejetés)."""
    for element in app.get("dataframe"):
        table = pa.ipc.open_stream(element.proto.arrow_data.data).read_all()
        if "Masked" in table.column_names:
            return {r["Type"]: (r["Masked"], r["Rejected"]) for r in table.to_pylist()}
    return {}


def metrics(app: AppTest) -> dict[str, str]:
    """Relit les trois totaux affichés en tête d'écran."""
    return {metric.label: metric.value for metric in app.metric}


def edit_row(app: AppTest, canonical: str, **cells: object) -> AppTest:
    """Modifie des cellules de la ligne dont le texte est canonical, puis relance la page."""
    index = [row["Text"] for row in table_rows(app)].index(canonical)
    version = app.session_state[KEY_TABLE_VERSION] if KEY_TABLE_VERSION in app.session_state else 0
    state = {"edited_rows": {index: cells}, "added_rows": [], "deleted_rows": []}
    app.session_state[f"{TABLE_KEY_PREFIX}{version}"] = state
    app.run()
    assert not app.exception
    return app


def pseudonymize(app: AppTest) -> PseudonymizationResult:
    """Clique sur Pseudonymize et renvoie le résultat conservé dans l'état."""
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    return app.session_state["pseudo_result"]


def add_value(app: AppTest, value: str) -> AppTest:
    """Saisit une valeur dans le champ d'ajout manuel et clique sur "Add and mask everywhere"."""
    app.text_input(key="review_manual_text").set_value(value)
    app.button(key="review_add_manual").click().run()
    assert not app.exception
    return app


def html_blocks(app: AppTest) -> list[str]:
    """Rassemble les fragments HTML affichés par la page."""
    return [element.value for element in app.get("html")]


def test_review_screen_shows_counts_table_and_highlighted_text() -> None:
    app = review_app()
    assert metrics(app) == {
        "Masked occurrences": "17",
        "Rejected occurrences": "0",
        "Entities": "13",
    }
    rows = table_rows(app)
    assert len(rows) == 13
    assert list(rows[0]) == [
        "Mask",
        "Text",
        "Type",
        "Occurrences",
        "Variants",
        "Confidence",
        "Source",
        "Note",
    ]
    assert all(row["Mask"] is True for row in rows)
    # Les lignes suivent l'ordre d'apparition dans le texte.
    assert [row["Text"] for row in rows][:3] == [
        "Pierre VERNOLAC",
        "16 février 1988",
        "2 66 06 48 113 562 50",
    ]
    person = rows[0]
    assert (person["Type"], person["Occurrences"], person["Confidence"]) == ("Person", 3, 0.85)
    assert person["Variants"] == "Pierre VERNOLAC, VERNOLAC, Vernolac"
    assert type_counts(app)["Person"] == (7, 0)
    page = html_blocks(app)
    document = next(block for block in page if "hc-document" in block)
    assert ">PERSON</span>" in document
    assert ">CASE</span>" in document
    legend = next(block for block in page if "hc-legend" in block)
    assert "hc-hl-IBAN" in legend
    assert "hc-hl-CUSTOM" not in legend
    assert "hc-hl-LOCATION" not in legend


def test_unchecking_a_group_removes_it_from_the_pseudonymization() -> None:
    app = review_app()
    app = edit_row(app, "Courriel", Mask=False)
    assert app.session_state["group_decisions"][COURRIEL].masked is False
    assert metrics(app)["Rejected occurrences"] == "1"
    assert type_counts(app)["Organization"] == (0, 1)
    assert [row["Mask"] for row in table_rows(app)].count(False) == 1
    assert any(">REJECTED</span>" in block for block in html_blocks(app))
    result = pseudonymize(app)
    assert "Courriel" in result.text
    assert "[SOCIETE_A]" not in result.text
    assert "Pierre VERNOLAC" not in result.text


def test_unchecking_a_group_rejects_every_occurrence_of_it() -> None:
    app = review_app()
    app = edit_row(app, "Pierre VERNOLAC", Mask=False)
    assert metrics(app)["Rejected occurrences"] == "3"
    assert sum(not d.masked for d in app.session_state["group_decisions"].values()) == 3
    assert "".join(html_blocks(app)).count(">REJECTED</span>") == 3
    result = pseudonymize(app)
    assert result.text.lower().count("vernolac") == 3
    assert "Pierre VERNOLAC" in result.text


def test_checking_the_box_again_masks_the_group_again() -> None:
    app = review_app()
    app = edit_row(app, "Courriel", Mask=False)
    app = edit_row(app, "Courriel", Mask=True)
    assert metrics(app)["Rejected occurrences"] == "0"
    assert "Courriel" not in pseudonymize(app).text


def test_changing_a_type_changes_the_token() -> None:
    app = review_app()
    app = edit_row(app, "Courriel", Type="Custom")
    assert app.session_state["group_decisions"][COURRIEL].entity_type is EntityType.CUSTOM
    assert [row["Type"] for row in table_rows(app)].count("Custom") == 1
    result = pseudonymize(app)
    assert "[AUTRE_1]" in result.text
    assert "[SOCIETE_A]" not in result.text
    assert "Courriel" not in result.text


def test_token_style_of_the_sidebar_is_used() -> None:
    app = review_app()
    app.sidebar.radio(key="token_style").set_value("en").run()
    app = edit_row(app, "Courriel", Type="Custom")
    result = pseudonymize(app)
    assert "[OTHER_1]" in result.text
    assert "[PERSON_1]" in result.text
    assert "[PERSONNE_1]" not in result.text


def test_changing_a_type_applies_to_every_occurrence_of_the_group() -> None:
    app = review_app()
    app = edit_row(app, "Pierre VERNOLAC", Type="Organization")
    changed = [d for d in app.session_state["group_decisions"].values() if d.entity_type]
    assert len(changed) == 3
    result = pseudonymize(app)
    assert "vernolac" not in result.text.lower()
    assert result.text.count("[SOCIETE_") >= 4


def test_manual_add_masks_the_three_occurrences_of_a_word() -> None:
    app = review_app()
    assert find_occurrences(app.session_state["source_text"], "client") == [
        (110, 116),
        (856, 862),
        (1227, 1233),
    ]
    app = add_value(app, "client")
    assert any("Added 3 occurrences" in message.value for message in app.success)
    manual = app.session_state["manual_entities"]
    assert len(manual) == 3
    assert {(d.source, d.score, d.entity_type) for d in manual} == {
        (Source.MANUAL, 1.0, EntityType.CUSTOM)
    }
    assert app.text_input(key="review_manual_text").value == ""
    assert metrics(app)["Masked occurrences"] == "20"
    assert metrics(app)["Entities"] == "14"
    assert any(row["Text"] == "Client" and row["Occurrences"] == 3 for row in table_rows(app))
    result = pseudonymize(app)
    assert "client" not in result.text.lower()
    assert result.text.count("[AUTRE_1]") == 3


def test_manual_add_uses_the_chosen_type() -> None:
    app = review_app()
    app.selectbox(key="review_manual_type").set_value(EntityType.ORGANIZATION)
    app = add_value(app, "licenciement")
    result = pseudonymize(app)
    assert "licenciement" not in result.text
    assert "[SOCIETE_" in result.text


def test_manual_add_reports_a_value_that_is_not_in_the_text() -> None:
    app = review_app()
    app = add_value(app, "introuvable")
    assert any("does not appear in the text" in warning.value for warning in app.warning)
    assert app.session_state["manual_entities"] == []
    app = add_value(app, "   ")
    assert any("Type the value to mask first" in warning.value for warning in app.warning)


def test_manual_add_skips_what_a_masked_value_already_covers() -> None:
    app = review_app()
    app = add_value(app, "vernolac")
    assert any("already inside a masked value" in info.value for info in app.info)
    assert app.session_state["manual_entities"] == []


def test_manual_add_replaces_a_rejected_detection() -> None:
    app = review_app()
    app = edit_row(app, "Courriel", Mask=False)
    app = add_value(app, "courriel")
    assert COURRIEL not in app.session_state["group_decisions"]
    assert [d.text for d in app.session_state["manual_entities"]] == ["Courriel"]
    assert metrics(app)["Rejected occurrences"] == "0"
    assert "[AUTRE_1]" in pseudonymize(app).text


def test_find_occurrences_ignores_case_and_accents_and_needs_whole_words() -> None:
    text = "Élodie et ELODIE; élodiette, MÉLODIE. Élodie-Rose. l'Élodie"
    assert [text[a:b] for a, b in find_occurrences(text, "elodie")] == [
        "Élodie",
        "ELODIE",
        "Élodie",
        "Élodie",
    ]
    assert find_occurrences("Jean\nDUPONT et Jean  Dupont", "jean dupont") == [(0, 11), (15, 27)]
    assert find_occurrences("tél : +33 6 12", "+33 6 12") == [(6, 14)]
    assert find_occurrences("abc", "") == []
    assert find_occurrences("abc", "  ") == []
    assert find_occurrences("a.b (a.b)", "a.b") == [(0, 3), (5, 8)]


def test_pseudonymize_goes_to_the_restore_step() -> None:
    app = review_app()
    result = pseudonymize(app)
    assert app.session_state["step"] == "restore"
    assert "3. Restore <span" in app.get("html")[0].value
    assert "[PERSONNE_1]" in result.text
    assert "Pierre" not in result.text
    assert result.mapping is not None
    assert app.session_state["restore_result"] is None


def test_back_to_import_keeps_the_review_available() -> None:
    app = review_app()
    app.button(key="review_back").click().run()
    assert app.session_state["step"] == "import"
    assert app.session_state["detections"] is not None


def test_decisions_survive_reruns_and_a_new_document_clears_them() -> None:
    app = review_app()
    app = edit_row(app, "Courriel", Mask=False)
    app = add_value(app, "client")
    saved = dict(app.session_state["group_decisions"])
    app.run()
    assert app.session_state["group_decisions"] == saved
    assert len(app.session_state["manual_entities"]) == 3
    app.button(key="review_back").click().run()
    app = app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    assert app.session_state["group_decisions"] == saved
    app.button(key="review_back").click().run()
    app.text_area(key="paste_widget").set_value("Mme Rose PETIT habite à Lyon.").run()
    app = app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    assert app.session_state["group_decisions"] == {}
    assert app.session_state["manual_entities"] == []
    assert all(row["Mask"] is True for row in table_rows(app))
    assert not any("Added" in message.value for message in app.success)


def test_a_new_decision_discards_the_previous_pseudonymization() -> None:
    app = review_app()
    pseudonymize(app)
    assert app.session_state["pseudo_result"] is not None
    app.session_state["step"] = "review"
    app.run()
    assert app.session_state["pseudo_result"] is not None
    app = edit_row(app, "Courriel", Mask=False)
    assert app.session_state["pseudo_result"] is None
    assert app.session_state["restore_result"] is None


def test_nothing_masked_is_announced() -> None:
    app = review_app()
    assert not [w for w in app.warning if "No value is masked" in w.value]
    app.session_state[f"{TABLE_KEY_PREFIX}0"] = {
        "edited_rows": {i: {"Mask": False} for i in range(13)},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()
    assert metrics(app)["Masked occurrences"] == "0"
    assert any("No value is masked" in warning.value for warning in app.warning)


def test_filter_shows_only_the_chosen_types() -> None:
    app = review_app()
    app.multiselect(key="review_filter").set_value([EntityType.PERSON]).run()
    assert not app.exception
    rows = table_rows(app)
    assert [row["Type"] for row in rows] == ["Person"] * 3
    app = edit_row(app, "Rose PETIT", Mask=False)
    assert metrics(app)["Rejected occurrences"] == "2"
    assert [row["Mask"] for row in table_rows(app)] == [True, True, False]
    app.multiselect(key="review_filter").set_value([]).run()
    assert len(table_rows(app)) == 13


def test_ambiguous_group_carries_a_warning() -> None:
    text = "Jean DUPONT et Marie DUPONT sont associés. M. Dupont a signé."
    detections = []
    for value in ("Jean DUPONT", "Marie DUPONT", "Dupont"):
        start = text.index(value)
        detections.append(
            Detection(start, start + len(value), EntityType.PERSON, 0.85, Source.NER_SPACY, value)
        )
    assert group_mentions(text, detections)[2].ambiguous_with
    rows = table_rows(review_app_with(text, detections))
    assert [row["Note"] for row in rows] == ["", "", "Check: may refer to another person"]


def test_user_text_cannot_inject_html_into_the_page() -> None:
    text = 'Dossier <script>alert(1)</script> de "Jean DUPONT" <img src=x onerror=alert(2)>'
    start = text.index('"Jean DUPONT"')
    entity = Detection(start, start + 13, EntityType.PERSON, 0.9, Source.MANUAL, '"Jean DUPONT"')
    app = review_app_with(text, [entity])
    assert not app.exception
    document = next(block for block in html_blocks(app) if "hc-document" in block)
    assert "<script" not in document
    assert "<img" not in document
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in document
    assert "&quot;Jean DUPONT&quot;" in document


def test_empty_state_without_detection() -> None:
    app = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT).run()
    app.session_state["step"] = "review"
    app.run()
    assert not app.exception
    assert any("Nothing to review yet" in info.value for info in app.info)
    assert app.button(key="review_back") is not None
    assert table_rows(app) == []
