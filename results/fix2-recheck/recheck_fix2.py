"""FIX2R : recontrôle indépendant de FIX2 sur des valeurs fictives écrites pour cette session.

Entrées : aucune donnée de corpus ; textes et détections fictifs, modèle spaCy local.
Sorties : un JSON (reproductions FIX2-01, lieu du worker G8, sorties falsifiées, statut de
la barre latérale), écrit dans un fichier neuf passé en argument.
Place : contrôle hors pipeline ; aucun corpus réservé n'est lu, aucun réglage n'est fait.
"""

import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection.pipeline import detect  # noqa: E402
from huisclos.models import Detection, EntityType, Source  # noqa: E402
from huisclos.pseudonymize.reidentify import restore  # noqa: E402
from huisclos.pseudonymize.tokens import pseudonymize  # noqa: E402
from scripts import gate8_measure  # noqa: E402

PERSON, ORG = EntityType.PERSON, EntityType.ORGANIZATION
SECRET = "VARNESSE"


def mention(text: str, value: str, after: int, kind: EntityType, source: Source) -> Detection:
    """Détection fictive de value, cherchée à partir de la position after."""
    start = text.index(value, after)
    return Detection(start, start + len(value), kind, 0.9, source, value)


def outcome(text: str, detections: list[Detection]) -> dict[str, Any]:
    """Pseudonymise puis restaure ; en cas d'erreur, rend le lieu validé du code métier."""
    try:
        result = pseudonymize(text, detections)
    except Exception as error:
        return {"ok": False, "error_type": type(error).__name__} | gate8_measure.code_location(
            error
        )
    leaked = [d.text for d in detections if d.text in result.text]
    restored = restore(result.text, result.mapping).text == text
    return {"ok": True, "text": result.text, "leaked": leaked, "restored": restored}


def manual_cases() -> dict[str, dict[str, Any]]:
    """Trois reproductions et trois témoins, détections fournies à la main."""
    one = "Mme Odile VARNESSE demande. Mme VARNESSE produit attestation_VARNESSE.docx."
    two = "Mme Odile VARNESSE demande. Pi\u00e8ce : attestation_VARNESSE.docx."
    four = "Ms Ada KORVELL objects. Ms KORVELL attaches KORVELL_witness.pdf."
    five = (
        "Quentrel Industrie SA (ci-apr\u00e8s \u00ab QI \u00bb) conteste. "
        "QI verse devis-QI-2025.pdf."
    )
    six = "Pi\u00e8ces : note_VARNESSE.pdf et bilan_VARNESSE.pdf."
    full = mention(one, "Odile VARNESSE", 0, PERSON, Source.HEURISTIC)
    short = mention(one, "VARNESSE", 30, PERSON, Source.PROPAGATION)
    return {
        "R1_fr_short_name_in_text_and_file": outcome(
            one, [full, short, mention(one, SECRET, 50, PERSON, Source.PROPAGATION)]
        ),
        "R2_en_name_at_file_start": outcome(
            four,
            [
                mention(four, "Ada KORVELL", 0, PERSON, Source.HEURISTIC),
                mention(four, "KORVELL", 20, PERSON, Source.PROPAGATION),
                mention(four, "KORVELL", 40, PERSON, Source.PROPAGATION),
            ],
        ),
        "R3_alias_with_hyphens": outcome(
            five,
            [mention(five, "Quentrel Industrie SA", 0, ORG, Source.NER_SPACY)]
            + [mention(five, "QI", after, ORG, Source.PROPAGATION) for after in (25, 50, 60)],
        ),
        "T1_control_different_spellings": outcome(
            two,
            [
                mention(two, "Odile VARNESSE", 0, PERSON, Source.HEURISTIC),
                mention(two, SECRET, 30, PERSON, Source.PROPAGATION),
            ],
        ),
        "T2_control_file_mention_added_manually": outcome(
            one, [full, short, mention(one, SECRET, 50, PERSON, Source.MANUAL)]
        ),
        "T3_control_two_file_names_only": outcome(
            six, [mention(six, SECRET, after, PERSON, Source.PROPAGATION) for after in (0, 25)]
        ),
    }


def pipeline_cases() -> dict[str, dict[str, Any]]:
    """Même structure, détections produites par le vrai pipeline Standard, FR et EN."""
    texts = {
        "fr": "Ma\u00eetre Odile VARNESSE repr\u00e9sente M. Bastien QUERLAIN. M. QUERLAIN "
        "conteste. Pi\u00e8ce n\u00b0 4 : courrier_QUERLAIN.pdf.",
        "en": "Counsel Ada KORVELL acts for Mr Bastien QUERLAIN. Mr QUERLAIN disputes the "
        "claim. Exhibit 4: letter_QUERLAIN.pdf.",
    }
    found = {}
    for language, text in texts.items():
        config = replace(PRESETS["hybrid"], document_language=language)
        detections = detect(text, config)
        found[f"P_{language}_standard"] = {
            "detections": [[d.text, d.entity_type.value, d.source.value] for d in detections]
        } | outcome(text, detections)
    return found


def raised_in(filename: str, function: str, body: str = "") -> BaseException:
    """Erreur levée dans un cadre au nom de fichier et de fonction imposés (code fictif)."""
    body = body or "raise ValueError('Lucien FALVERAC')"
    source = f"def {function}():\n    {body}\n"
    namespace: dict[str, Any] = {}
    exec(compile(source, filename, "exec"), namespace)
    try:
        namespace[function]()
    except (ValueError, ZeroDivisionError) as error:
        return error
    raise AssertionError("aucune erreur levée")


def locations() -> dict[str, Any]:
    """Lieu exporté par le worker pour des cadres réels ou fabriqués."""
    text = "M. VARNESSE signe. Pi\u00e8ce : note_VARNESSE.pdf et M. VARNESSE."
    detections = [mention(text, SECRET, after, PERSON, Source.PROPAGATION) for after in (0, 20, 40)]
    try:
        pseudonymize(text, detections)
    except RuntimeError as error:
        real = gate8_measure.code_location(error)
    return {
        "real_fix2_01_error": real,
        "real_error_contains_value": SECRET in json.dumps(real),
        "library_only": gate8_measure.code_location(json.JSONDecodeError("x", "y", 0)),
        "frame_outside_repo_named_src_huisclos": gate8_measure.code_location(
            raised_in("C:/elsewhere/src/huisclos/forged.py", "forged")
        ),
        "frame_path_with_space": gate8_measure.code_location(
            raised_in("C:/elsewhere/src/huisclos/Lucien FALVERAC.py", "forged")
        ),
        "frame_identifier_shaped_value": gate8_measure.code_location(
            raised_in("C:/elsewhere/src/huisclos/FALVERAC.py", "FALVERAC")
        ),
        "lambda_last_frame_in_src": gate8_measure.code_location(
            raised_in("C:/elsewhere/src/huisclos/forged.py", "outer", "return (lambda: 1 / 0)()")
        ),
        "frame_outside_measured_code": gate8_measure.code_location(
            raised_in(str(ROOT / "results/fix2-recheck/forged.py"), "forged")
        ),
    }


def forged_outputs() -> dict[str, str]:
    """failure_detail sur des sorties de worker falsifiées ; la chaîne rendue est relevée."""
    base = {"stage": "pseudonymization", "error_type": "RuntimeError"}
    good = base | {"path": "src/huisclos/pseudonymize/tokens.py", "function": "f", "line": 9}
    cases: dict[str, Any] = {
        "valid": good,
        "extra_message_key": good | {"message": "Lucien FALVERAC"},
        "absolute_path": good | {"path": "C:/Users/Lucien/src/huisclos/x.py"},
        "dot_dot_path": good | {"path": "src/huisclos/../../secret.py"},
        "tests_path": good | {"path": "tests/test_fix2.py"},
        "results_path": good | {"path": "results/fix2/diagnose_challenge.py"},
        "path_too_long": good | {"path": "src/huisclos/" + "a" * 121 + ".py"},
        "line_zero": good | {"line": 0},
        "line_float": good | {"line": 9.0},
        "line_none": good | {"line": None},
        "line_bool": good | {"line": True},
        "missing_function": {k: v for k, v in good.items() if k != "function"},
        "unknown_stage": good | {"stage": "Lucien FALVERAC"},
        "final_check_stage": good | {"stage": "final_check"},
        "error_type_with_space": good | {"error_type": "Lucien FALVERAC"},
        "identifier_shaped_function": good | {"function": "FALVERAC"},
        "identifier_shaped_path": good | {"path": "src/huisclos/FALVERAC.py"},
        "identifier_shaped_error_type": good | {"error_type": "FALVERAC"},
    }
    found = {
        name: gate8_measure.failure_detail(json.dumps({"failure": failure}))
        for name, failure in cases.items()
    }
    found["earlier_line_ignored"] = gate8_measure.failure_detail(
        json.dumps({"failure": cases["valid"]}) + "\nnot json"
    )
    found["last_line_used"] = gate8_measure.failure_detail(
        "Lucien FALVERAC\n" + json.dumps({"failure": cases["valid"]})
    )
    return found


def sidebar_status() -> dict[str, Any]:
    """Statut Enhanced par langue d'interface et de document, parcours AppTest sans navigateur."""
    from streamlit.testing.v1 import AppTest

    from app import i18n

    os.environ[i18n.STRICT_ENV] = "1"
    os.environ.pop("HUISCLOS_PUBLIC_DEMO", None)
    found: dict[str, Any] = {}
    for ui in ("fr", "en"):
        texts = i18n.FR if ui == "fr" else i18n.EN
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=120).run()
        app.selectbox(key="language").select(ui).run()
        rows = {}
        for document, profile in (("en", "enhanced"), ("fr", "enhanced"), ("en", "standard")):
            app.radio(key="document_language").set_value(document).run()
            app.radio(key="detection_profile").set_value(profile).run()
            rows[f"{document}_{profile}"] = {
                "exception": bool(app.exception),
                "profile_kept": app.session_state["detection_profile"] == profile,
                "warning_is_en_status": [w.value for w in app.sidebar.warning]
                == [texts["sidebar.profile.status.en"]],
                "caption_has_fr_status": texts["sidebar.profile.status.fr"]
                in [c.value for c in app.sidebar.caption],
                "warnings": len(app.sidebar.warning),
            }
        found[f"ui_{ui}"] = rows
    return found


def main() -> int:
    """Lance les quatre contrôles et écrit le JSON dans un fichier neuf."""
    out = Path(sys.argv[1])
    report = {
        "manual": manual_cases(),
        "pipeline": pipeline_cases(),
        "locations": locations(),
        "forged_failure_detail": forged_outputs(),
        "sidebar": sidebar_status(),
    }
    with out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
