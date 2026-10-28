"""Vérifie le pilote de robustesse avec un faux moteur bilingue, sans modèle ni réseau.

Entrées : petits corpus fictifs et plans figés écrits dans un dossier temporaire, faux moteur
en mémoire et faux checkout minimal pour le processus séparé.
Sorties : assertions sur les gardes, la langue, les stades, le rapport et l'appariement.
Place dans le pipeline : validation de scripts/evaluate_robustness.py et du rapport séparé.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from huisclos.config import PRESETS
from huisclos.evaluation import run
from huisclos.evaluation.corpus import load_corpus
from huisclos.evaluation.coverage_reports import ProfileRun, build_report, draw_values, profile_run
from huisclos.evaluation.intervals import bootstrap_intervals, draw_indices, percentile
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.final_check import check_threshold, final_check
from huisclos.pseudonymize.tokens import pseudonymize
from scripts import evaluate_robustness as pilot

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FakeConfig:
    """Configuration d'un faux moteur bilingue qui porte la langue du document (contrat A2)."""

    threshold: float = 0.5
    document_language: str = "fr"
    wide: bool = False


# Valeurs repérées (texte, type, score). Le profil étroit ne voit que le prénom et la rue ;
# le nom de famille n'apparaît qu'au seuil abaissé du contrôle final (0,4 >= 0,3).
NARROW = {
    "fr": (("Léa", "PERSON", 0.9), ("Morvan", "PERSON", 0.4), ("12 rue des Lilas", "ADDRESS", 0.9)),
    "en": (("Ada", "PERSON", 0.9), ("Quill", "PERSON", 0.4), ("4 Elm Street", "ADDRESS", 0.9)),
}
WIDE = {
    "fr": (("Léa Morvan", "PERSON", 0.9), ("12 rue des Lilas 69007 Lyon", "ADDRESS", 0.9)),
    "en": (("Ada Quill", "PERSON", 0.9), ("4 Elm Street, Leeds", "ADDRESS", 0.9)),
}
DOCUMENTS = {
    "fr": (
        ("Maître Léa Morvan, 12 rue des Lilas 69007 Lyon.", WIDE["fr"]),
        ("Léa Morvan signe.", WIDE["fr"][:1]),
        ("Rien à signaler.", ()),
    ),
    "en": (
        ("Ms Ada Quill, 4 Elm Street, Leeds.", WIDE["en"]),
        ("Ada Quill signs.", WIDE["en"][:1]),
        ("Nothing to report.", ()),
    ),
}


def fake_detect(text: str, config: Any) -> list[Detection]:
    """Repère les valeurs fictives de la langue du document au-dessus du seuil."""
    found = []
    for value, kind, score in (WIDE if config.wide else NARROW)[config.document_language]:
        start = text.find(value)
        while start >= 0 and score >= config.threshold:
            found.append(
                Detection(start, start + len(value), EntityType(kind), score, Source.PATTERN, value)
            )
            start = text.find(value, start + 1)
    return sorted(found, key=lambda item: item.start)


FAKE_API = SimpleNamespace(
    presets={"standard": FakeConfig(), "enhanced": FakeConfig(wide=True)},
    detect=fake_detect,
    pseudonymize=pseudonymize,
    check_threshold=check_threshold,
    final_check=final_check,
)


def write_corpus(path: Path, language: str = "fr", split: str = "dev") -> Path:
    """Écrit un corpus JSONL fictif de trois documents, dont un sans annotation."""
    lines = []
    for index, (text, values) in enumerate(DOCUMENTS[language]):
        entities = [
            {"start": text.index(value), "end": text.index(value) + len(value), "type": kind}
            | {"text": value}
            for value, kind, _ in values
        ]
        record = {"id": f"doc-{index}", "doc_type": "letter", "split": split, "title": "Fiction"}
        lines.append(json.dumps(record | {"text": text, "entities": entities}))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_plan(path: Path, language: str = "fr", **profiles: dict[str, Any]) -> Path:
    """Écrit un plan figé ; par défaut standard et enhanced, enhanced comparé à standard."""
    profiles = profiles or {
        "standard": {"preset": "standard", "threshold": 0.5},
        "enhanced": {"preset": "enhanced", "threshold": 0.5},
    }
    comparisons = [["enhanced", "standard"]] if "enhanced" in profiles else []
    plan = {"document_language": language, "profiles": profiles, "comparisons": comparisons}
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def arguments(corpus: Path, plan: Path, out: Path, *extra: str) -> list[str]:
    """Construit la ligne de commande du pilote."""
    return ["--corpus", str(corpus), "--dataset-id", "fixtures-b1", "--plan", str(plan)] + [
        "--out",
        str(out),
        *extra,
    ]


def row(report: dict, key: str, **match: Any) -> dict:
    """Renvoie l'unique ligne de report[key] qui porte les valeurs demandées."""
    rows = [
        item for item in report[key] if all(item[name] == value for name, value in match.items())
    ]
    assert len(rows) == 1
    return rows[0]


def test_french_report_separates_stages_and_measures_gain(tmp_path: Path) -> None:
    """Rappel partiel parfait, fuite réelle ; alertes visibles mais sans effet sur la fuite."""
    corpus, plan = write_corpus(tmp_path / "dev.jsonl"), write_plan(tmp_path / "plan.json")
    out = tmp_path / "out"
    report = pilot.measure(pilot.parse_arguments(arguments(corpus, plan, out)), FAKE_API)
    micro = row(report, "metrics_by_type", config="standard", mode="partial", type="micro")
    assert (micro["tp"], micro["fp"], micro["fn"], micro["recall"]) == (3, 0, 0, 1.0)
    standard = row(
        report, "coverage", config="standard", stage="pseudonymization", scope="evaluated"
    )
    assert standard["entities_partially_exposed"] == 3
    assert standard["leaked_characters"] == 7 + 11 + 7
    assert standard["reference_characters"] == 47
    assert standard["full_coverage_rate"] == 0.0
    assert standard["documents_with_any_exposure"] == 2
    checked = row(report, "coverage", config="standard", stage="final_check", scope="evaluated")
    assert checked["leaked_characters"] == standard["leaked_characters"]
    alerts = row(report, "final_check", config="standard")
    assert (alerts["available"], alerts["check_threshold"]) == (True, 0.3)
    assert (alerts["alerts"], alerts["exposed_entities"], alerts["exposed_entities_alerted"]) == (
        2,
        3,
        2,
    )
    enhanced = row(
        report, "coverage", config="enhanced", stage="pseudonymization", scope="evaluated"
    )
    assert (enhanced["full_coverage_rate"], enhanced["leaked_characters"]) == (1.0, 0)
    criterion = report["engineering_criteria"][0]
    assert (criterion["candidate"], criterion["reference"], criterion["met"]) == (
        "enhanced",
        "standard",
        True,
    )
    leak = row(
        report, "paired_differences", stage="pseudonymization", metric="leaked_character_rate"
    )
    assert leak["estimate"] == pytest.approx(-25 / 47)
    assert leak["excludes_zero"] is True and leak["undefined_draws"] > 0
    profile = report["metadata"]["profiles"]["standard"]
    assert profile["document_language_field"] is True
    assert profile["configuration"]["document_language"] == "fr"
    assert report["selected_threshold"]["threshold"] == 0.5
    assert {"robustness.json", "robustness.md", "coverage_exposures_dev.csv"} <= {
        path.name for path in out.iterdir()
    }
    details = (out / "coverage_exposures_dev.csv").read_text(encoding="utf-8")
    assert " Morvan" in details and " 69007 Lyon" in details
    summary = (out / "robustness.md").read_text(encoding="utf-8")
    assert "n/a" in summary and "Engineering criterion (not a legal threshold)" in summary


def test_english_documents_use_document_language(tmp_path: Path) -> None:
    """Le faux moteur reçoit en ; la mesure anglaise reste séparée et explicite."""
    corpus = write_corpus(tmp_path / "dev_en.jsonl", "en")
    plan = write_plan(tmp_path / "plan.json", "en")
    report = pilot.measure(pilot.parse_arguments(arguments(corpus, plan, tmp_path / "o")), FAKE_API)
    assert report["metadata"]["document_language"] == "en"
    standard = row(
        report, "coverage", config="standard", stage="pseudonymization", scope="evaluated"
    )
    assert (standard["leaked_characters"], standard["reference_characters"]) == (19, 37)
    assert report["metadata"]["profiles"]["enhanced"]["configuration"]["document_language"] == "en"


def test_english_refused_without_document_language_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Le DetectionConfig actuel n'a pas de champ de langue : refus clair avant détection."""

    def forbidden(*_: object) -> list[Detection]:
        raise AssertionError("aucune détection ne doit avoir lieu")

    api = SimpleNamespace(**vars(FAKE_API) | {"presets": PRESETS, "detect": forbidden})
    corpus = write_corpus(tmp_path / "dev_en.jsonl", "en")
    plan = write_plan(tmp_path / "plan.json", "en", hybrid={"preset": "hybrid", "threshold": 0.3})
    assert pilot.main(arguments(corpus, plan, tmp_path / "o"), api) == 2
    assert "document_language" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize(
    "name",
    [
        "corpus/test.jsonl",
        "corpus/../corpus/challenge.jsonl",
        "CORPUS/TEST.JSONL",
        "corpus/blind_post_g7/fr/challenge.jsonl",
        "corpus/blind_post_g7/en/dev.jsonl",
    ],
)
def test_dev_mode_refuses_reserved_paths_before_reading(
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Chemins relatifs, résolus ou en majuscules : refus avant toute lecture du corpus."""

    def forbidden(*_: object, **__: object) -> list:
        raise AssertionError("le corpus réservé ne doit pas être lu")

    monkeypatch.chdir(ROOT)
    monkeypatch.setattr(run, "load_corpus", forbidden)
    assert run.reserved_reason(Path(name))
    plan = write_plan(tmp_path / "plan.json")
    assert pilot.main(arguments(Path(name), plan, tmp_path / "o"), FAKE_API) == 2
    assert "Reserved corpus refused" in capsys.readouterr().err


def test_same_file_through_another_name_is_reserved(tmp_path: Path) -> None:
    """Un lien physique vers un faux corpus test d'une racine fictive reste réservé."""
    reserved = tmp_path / "root" / "corpus" / "test.jsonl"
    reserved.parent.mkdir(parents=True)
    reserved.write_text("{}\n", encoding="utf-8")
    alias = tmp_path / "elsewhere" / "copy.jsonl"
    alias.parent.mkdir()
    try:
        os.link(reserved, alias)
    except OSError:
        pytest.skip("Liens physiques indisponibles sur ce système de fichiers.")
    assert run.reserved_reason(alias, tmp_path / "root") == "test.jsonl"
    assert run.reserved_reason(write_corpus(tmp_path / "dev.jsonl"), tmp_path / "root") is None


def test_dev_mode_refuses_reserved_split_inside_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Une copie renommée d'un split réservé est refusée sur le split de ses documents."""
    corpus = write_corpus(tmp_path / "renamed.jsonl", split="test")
    plan = write_plan(tmp_path / "plan.json")
    assert pilot.main(arguments(corpus, plan, tmp_path / "o"), FAKE_API) == 2
    assert "Reserved split refused" in capsys.readouterr().err


@pytest.mark.parametrize(
    "plan",
    [
        {"profiles": {"a": {"preset": "x", "threshold": 0.3}}},
        {"document_language": "de", "profiles": {"a": {"preset": "x", "threshold": 0.3}}},
        {"document_language": "fr", "profiles": {}},
        {"document_language": "fr", "profiles": {"a": {"preset": "x"}}},
        {"document_language": "fr", "profiles": {"a": {"preset": "x", "threshold": True}}},
        {"document_language": "fr", "profiles": {"a": {"preset": "x", "threshold": 1.5}}},
        {"document_language": "fr", "profiles": {"a": {"preset": "x", "threshold": 0.3, "y": 1}}},
        {"document_language": "fr", "profiles": {"a": {"preset": "x", "threshold": 0.3}}, "z": 1},
        {
            "document_language": "fr",
            "profiles": {"a": {"preset": "x", "threshold": 0.3}},
            "comparisons": [["a", "b"]],
        },
        {
            "document_language": "fr",
            "profiles": {"a": {"preset": "x", "threshold": 0.3}},
            "comparisons": [["a", "a"]],
        },
        {
            "document_language": "fr",
            "profiles": {"a": {"preset": "x", "threshold": 0.3, "checkout": "absent"}},
        },
    ],
)
def test_invalid_plans_are_refused(plan: dict, tmp_path: Path) -> None:
    """Langue, seuil, clé, paire ou chemin non conformes : le plan figé est refusé."""
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError):
        run.load_plan(path)


def test_required_options_identifier_preset_and_existing_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Options exigées, identifiant sobre, préréglage connu, dossier de sortie neuf."""
    with pytest.raises(SystemExit):
        pilot.parse_arguments(["--plan", "plan.json", "--out", "o"])
    corpus, plan = write_corpus(tmp_path / "dev.jsonl"), write_plan(tmp_path / "plan.json")
    wrong_id = arguments(corpus, plan, tmp_path / "o")
    wrong_id[3] = "un jeu"
    assert pilot.main(wrong_id, FAKE_API) == 2
    unknown = write_plan(tmp_path / "p2.json", missing={"preset": "missing", "threshold": 0.5})
    assert pilot.main(arguments(corpus, unknown, tmp_path / "o2"), FAKE_API) == 2
    (tmp_path / "o3").mkdir()
    (tmp_path / "o3" / "robustness.json").write_text("{}", encoding="utf-8")
    assert pilot.main(arguments(corpus, plan, tmp_path / "o3"), FAKE_API) == 2
    error = capsys.readouterr().err
    assert "dataset-id" in error and "Unknown preset" in error and "already holds" in error


def test_paired_differences_share_the_marginal_draws(tmp_path: Path) -> None:
    """Profils identiques : écart nul sur chaque tirage ; précision par tirage = historique."""
    documents = load_corpus(write_corpus(tmp_path / "dev.jsonl"))
    payload = pilot.stage_outputs([d.text for d in documents], "standard", 0.5, "fr", FAKE_API)
    first = profile_run("a", 0.5, documents, payload)
    second = ProfileRun("b", 0.5, first.predictions, first.substituted, first.alerts)
    report = build_report(documents, [first, second], [["a", "b"]], {})
    for item in report["paired_differences"]:
        assert item["estimate"] in (0.0, None)
        assert (item["lower"], item["upper"], item["excludes_zero"]) == (0.0, 0.0, False)
    # Deux documents annotés : aucun tirage sans dénominateur, la fuite varie d'un tirage à
    # l'autre (18/37 puis 7/10) et seuls des types évalués sont prédits.
    two = ProfileRun("a", 0.5, first.predictions[:2], first.substituted[:2], first.alerts[:2])
    samples = draw_values(documents[:2], two, draw_indices(2))
    expected = bootstrap_intervals(documents[:2], two.predictions)["leak_rate"]
    leak = samples[("detection", "leaked_character_rate")]
    assert None not in leak and len(set(leak)) > 1
    assert (percentile(leak, 0.025), percentile(leak, 0.975)) == (
        expected["lower"],
        expected["upper"],
    )


def test_profile_payload_must_match_documents(tmp_path: Path) -> None:
    """Réponse incomplète ou contrôle final partiel : refus explicite."""
    documents = load_corpus(write_corpus(tmp_path / "dev.jsonl"))
    payload = pilot.stage_outputs([d.text for d in documents], "standard", 0.5, "fr", FAKE_API)
    with pytest.raises(ValueError):
        profile_run("a", 0.5, documents[:2], payload)
    payload["documents"][0]["alerts"] = None
    with pytest.raises(ValueError):
        profile_run("a", 0.5, documents, payload)


FAKE_CONFIG = """
from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionConfig:
    threshold: float = 0.5
    spacy_model: str = "none"


PRESETS = {"reference": DetectionConfig()}
"""
FAKE_PIPELINE = """
from types import SimpleNamespace as N


def detect(text, config=None):
    {failure}start = text.find("Morvan")
    if start < 0:
        return []
    kind, source = N(value="PERSON"), N(value="pattern")
    return [N(start=start, end=start + 6, entity_type=kind, score=0.9, source=source)]
"""
FAKE_TOKENS = """
from types import SimpleNamespace as N


def pseudonymize(text, detections):
    pieces, occurrences, cursor, shift = [], [], 0, 0
    for item in detections:
        token, original = "[PERSONNE_1]", text[item.start : item.end]
        pieces += [text[cursor : item.start], token]
        start = item.start + shift
        occurrences.append(N(start=start, end=start + len(token), original=original))
        shift += len(token) - len(original)
        cursor = item.end
    pieces.append(text[cursor:])
    return N(text="".join(pieces), occurrences=occurrences)
"""
FAKE_PACKAGE = {
    "__init__.py": "",
    "config.py": FAKE_CONFIG,
    "detection/__init__.py": "",
    "detection/pipeline.py": FAKE_PIPELINE,
    "pseudonymize/__init__.py": "",
    "pseudonymize/tokens.py": FAKE_TOKENS,
}


def fake_checkout(folder: Path, failure: str = "") -> Path:
    """Écrit un ancien code minimal, sans contrôle final, importé par le processus séparé."""
    for name, content in FAKE_PACKAGE.items():
        path = folder / "src" / "huisclos" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.replace("{failure}", failure), encoding="utf-8")
    return folder


def test_gate_mode_uses_separate_process_without_content(tmp_path: Path) -> None:
    """Gate : processus séparé, corpus réservé accepté, aucun texte, id ou position écrit."""
    checkout = fake_checkout(tmp_path / "reference")
    corpus = write_corpus(tmp_path / "blind" / "challenge.jsonl", split="challenge")
    plan = write_plan(
        tmp_path / "plan.json",
        reference={"preset": "reference", "threshold": 0.5, "checkout": str(checkout)},
    )
    out = tmp_path / "gate"
    assert pilot.main(arguments(corpus, plan, out, "--mode", "gate")) == 0
    assert sorted(path.name for path in out.iterdir()) == ["robustness.json", "robustness.md"]
    raw = (out / "robustness.json").read_text(encoding="utf-8")
    report = json.loads(raw)
    for text in (raw, (out / "robustness.md").read_text(encoding="utf-8")):
        assert "doc-0" not in text and "Morvan" not in text and "Lilas" not in text
        assert '"start"' not in text and "document_id" not in text
    assert row(report, "final_check", config="reference")["available"] is False
    profile = report["metadata"]["profiles"]["reference"]
    assert (profile["document_language_field"], profile["git_commit"]) == (False, None)
    covered = row(
        report, "coverage", config="reference", stage="pseudonymization", scope="evaluated"
    )
    assert (covered["entities_partially_exposed"], covered["entities_fully_exposed"]) == (2, 1)


def test_gate_mode_hides_separate_process_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Une erreur du processus séparé n'est recopiée qu'en dev : en gate, le code seul."""
    failure = "raise ValueError('fragment ' + text[:10])\n    "
    checkout = fake_checkout(tmp_path / "broken", failure)
    corpus = write_corpus(tmp_path / "dev.jsonl")
    plan = write_plan(
        tmp_path / "plan.json",
        reference={"preset": "reference", "threshold": 0.5, "checkout": str(checkout)},
    )
    assert pilot.main(arguments(corpus, plan, tmp_path / "g", "--mode", "gate")) == 2
    gate_error = capsys.readouterr().err
    assert "Separate profile process failed" in gate_error and "Maître" not in gate_error
    assert pilot.main(arguments(corpus, plan, tmp_path / "d")) == 2
    assert "Maître" in capsys.readouterr().err
