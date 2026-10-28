"""FIX2 : défaut de substitution du challenge et diagnostic situé du harnais.

Entrées : valeurs entièrement fictives, détections fournies à la main, aucun modèle.
Sorties : preuve du défaut (xfail strict tant que pseudonymize n'est pas corrigé) et
contrats du lieu d'erreur exporté par le worker G8 et par le diagnostic FIX2.
Aucun corpus réservé n'est lu ; le défaut a été reproduit d'après sa seule structure.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.reidentify import restore
from huisclos.pseudonymize.tokens import pseudonymize
from scripts import gate8_measure

ROOT = Path(__file__).resolve().parents[1]


def mention(text: str, value: str, start_at: int, kind: EntityType, source: Source) -> Detection:
    """Détection fictive de value, cherchée à partir de start_at."""
    start = text.index(value, start_at)
    return Detection(start, start + len(value), kind, 0.9, source, value)


def file_name_cases() -> list[tuple[str, list[Detection]]]:
    """Même texte, même type, dans le texte courant et dans un nom de fichier."""
    person = EntityType.PERSON
    french = (
        "M. Lucien FALVERAC conteste. M. FALVERAC signe. Pi\u00e8ce : conclusions_FALVERAC.pdf."
    )
    english = "Mr Nolan FALVERICK disputes. Mr FALVERICK signs. Exhibit: statement_FALVERICK.pdf."
    sigle = (
        "La soci\u00e9t\u00e9 Brivane Logistique SAS (ci-apr\u00e8s \u00ab BL \u00bb) "
        "conteste. Pi\u00e8ce : contrat_BL_2024.pdf."
    )
    org = EntityType.ORGANIZATION
    return [
        (
            french,
            [
                mention(french, "Lucien FALVERAC", 0, person, Source.NER_SPACY),
                mention(french, "FALVERAC", 20, person, Source.HEURISTIC),
                mention(french, "FALVERAC", 40, person, Source.PROPAGATION),
            ],
        ),
        (
            english,
            [
                mention(english, "Nolan FALVERICK", 0, person, Source.HEURISTIC),
                mention(english, "FALVERICK", 20, person, Source.HEURISTIC),
                mention(english, "FALVERICK", 45, person, Source.PROPAGATION),
            ],
        ),
        (
            sigle,
            [
                mention(sigle, "Brivane Logistique SAS", 0, org, Source.NER_SPACY),
                mention(sigle, "BL", 30, org, Source.PROPAGATION),
                mention(sigle, "BL", 60, org, Source.PROPAGATION),
            ],
        ),
    ]


@pytest.mark.xfail(
    strict=True,
    raises=RuntimeError,
    reason="FIX2-01 : grouping.py met la mention du nom de fichier dans un groupe distinct, "
    "tokens._token_tables refuse deux jetons pour un même texte ; correctif hors périmètre FIX2",
)
@pytest.mark.parametrize("case", range(3))
def test_same_value_in_text_and_file_name_is_pseudonymized(case: int) -> None:
    """Chaque mention est remplacée et la restauration exacte rend le texte d'origine."""
    text, detections = file_name_cases()[case]
    result = pseudonymize(text, detections)
    assert len(result.occurrences) == len(detections)
    assert all(detection.text not in result.text for detection in detections)
    assert restore(result.text, result.mapping).text == text


def test_worker_failure_location_comes_from_measured_code_without_message() -> None:
    """Une erreur réelle du code métier est située par fichier, fonction et ligne seulement."""
    text = "Lucien FALVERAC"
    overlapping = [
        Detection(0, 15, EntityType.PERSON, 0.9, Source.PATTERN, text),
        Detection(7, 15, EntityType.PERSON, 0.9, Source.PATTERN, "FALVERAC"),
    ]
    with pytest.raises(ValueError) as caught:
        pseudonymize(text, overlapping)
    location = gate8_measure.code_location(caught.value)
    assert location["path"] == "src/huisclos/pseudonymize/tokens.py"
    assert location["function"] == "_sorted_detections"
    assert type(location["line"]) is int and location["line"] > 0
    assert "FALVERAC" in str(caught.value) and "FALVERAC" not in json.dumps(location)


def test_library_only_failure_has_no_location() -> None:
    """Un cadre de bibliothèque ou de test n'est jamais cité comme lieu."""
    with pytest.raises(ValueError) as caught:
        json.loads("Lucien FALVERAC")
    assert gate8_measure.code_location(caught.value) == gate8_measure.NO_LOCATION


def test_valid_location_is_appended_to_the_failure_detail() -> None:
    """Le message d'échec du parent cite le lieu validé après le stade et la classe."""
    failure = {
        "stage": "pseudonymization",
        "error_type": "RuntimeError",
        "path": "src/huisclos/pseudonymize/tokens.py",
        "function": "_token_tables",
        "line": 140,
    }
    assert gate8_measure.failure_detail(json.dumps({"failure": failure})) == (
        " at stage pseudonymization (RuntimeError) in "
        "src/huisclos/pseudonymize/tokens.py:_token_tables:140"
    )


@pytest.mark.parametrize(
    "forged",
    [
        {"path": "C:/Users/Lucien FALVERAC/x.py"},
        {"path": "src/huisclos/Lucien FALVERAC.py"},
        {"path": "tests/test_fix2.py"},
        {"function": "Lucien FALVERAC"},
        {"line": "140"},
        {"line": -1},
        {"line": True},
    ],
)
def test_forged_location_is_dropped_but_stage_kept(forged: dict[str, object]) -> None:
    """Un lieu non conforme est ignoré ; seuls stade et classe validés restent cités."""
    failure = {
        "stage": "detection",
        "error_type": "OSError",
        "path": "src/huisclos/detection/ner.py",
        "function": "analyze",
        "line": 63,
    } | forged
    detail = gate8_measure.failure_detail(json.dumps({"failure": failure}))
    assert detail == " at stage detection (OSError)"


def diagnostic_module() -> object:
    """Charge le harnais diagnostique archivé dans results/fix2 sans le lancer."""
    path = ROOT / "results/fix2/diagnose_challenge.py"
    spec = importlib.util.spec_from_file_location("fix2_diagnostic", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diagnostic_site_and_forged_worker_answers() -> None:
    """Le diagnostic FIX2 n'exporte ni message ni chaîne libre venue d'un worker."""
    diagnostic = diagnostic_module()
    text = "Lucien FALVERAC"
    with pytest.raises(ValueError) as caught:
        pseudonymize(text, [Detection(0, 3, EntityType.PERSON, 0.9, Source.PATTERN, "xyz")])
    found = diagnostic.site("pseudonymization", caught.value)
    assert found["path"] == "src/huisclos/pseudonymize/tokens.py"
    assert diagnostic.valid_site(found)
    assert text not in json.dumps(found) and "xyz" not in json.dumps(found)
    for forged in (
        found | {"stage": text},
        found | {"function": text},
        found | {"note": text},
        found | {"line": "3"},
        text,
    ):
        assert not diagnostic.valid_site(forged)


@pytest.mark.parametrize("ui", ("fr", "en"))
def test_enhanced_status_is_visible_per_document_language(
    ui: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enhanced EN reste choisi mais porte un avertissement visible ; FR reste expérimental."""
    from streamlit.testing.v1 import AppTest

    from app import i18n

    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    app.selectbox(key="language").select(ui).run()
    app.radio(key="document_language").set_value("en").run()
    app.radio(key="detection_profile").set_value("enhanced").run()
    assert not app.exception
    assert app.session_state["detection_profile"] == "enhanced"
    texts = i18n.FR if ui == "fr" else i18n.EN
    english = texts["sidebar.profile.status.en"]
    assert [item.value for item in app.sidebar.warning] == [english]
    app.radio(key="document_language").set_value("fr").run()
    french = texts["sidebar.profile.status.fr"]
    assert french in [item.value for item in app.sidebar.caption]
    assert english not in [item.value for item in app.sidebar.warning]
    app.radio(key="detection_profile").set_value("standard").run()
    assert french not in [item.value for item in app.sidebar.caption]
    assert not app.sidebar.warning


@pytest.mark.xfail(
    strict=True,
    reason="FIX2-01 : la RuntimeError de tokens._token_tables interrompt Review ; "
    "correctif de pseudonymize hors périmètre FIX2",
)
def test_review_pseudonymizes_a_name_repeated_in_a_file_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le parcours Standard FR atteint Restore avec un nom repris dans un nom de fichier."""
    from streamlit.testing.v1 import AppTest

    from app import i18n

    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    text = file_name_cases()[0][0]
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    app.radio(key="document_language").set_value("fr").run()
    app.text_area(key="paste_widget").set_value(text).run()
    app.button(key="detect").click().run()
    assert app.session_state["step"] == "review"
    app.button(key="review_pseudonymize").click().run()
    assert not app.exception
    assert app.session_state["step"] == "restore"
