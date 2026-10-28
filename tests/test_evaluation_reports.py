"""Vérifie la conservation des résultats dev lors d'une mesure test.

Entrées : corpus entièrement inventés écrits dans un dossier temporaire, detect simulé.
Sorties : assertions sur les fichiers de résultats, le seuil et les appels de détection.
Place dans le pipeline : régressions de l'orchestrateur d'évaluation, sans modèle ni vrai corpus.
"""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from huisclos.evaluation import reports, run
from huisclos.models import Detection, EntityType, Source

pytestmark = pytest.mark.usefixtures("no_network")

CONFIGS = ["hybrid", "patterns_only"]
DEV_TEXTS = ("Ada writes.", "Bob answers.")
TEST_TEXTS = ("Eva signs.",)
DEV_FILES = ("threshold.json", "threshold_sweep.csv", "errors_dev.csv")


def write_split(corpus: Path, split: str, texts: tuple[str, ...]) -> None:
    """Écrit un fichier JSONL fictif ; le prénom de trois lettres est la seule référence."""
    lines = []
    for index, text in enumerate(texts):
        record = {
            "id": f"{split}-{index}",
            "doc_type": "letter",
            "split": split,
            "title": "Fiction",
            "text": text,
            "entities": [{"start": 0, "end": 3, "type": "PERSON", "text": text[:3]}],
        }
        lines.append(json.dumps(record) + "\n")
    (corpus / f"{split}.jsonl").write_text("".join(lines), encoding="utf-8")


@pytest.fixture
def synthetic_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, list[tuple[str, float]]]:
    """Prépare les corpus fictifs et une détection simulée qui note chaque appel.

    La détection simulée trouve le prénom jusqu'au seuil 0,55, puis plus rien :
    le balayage dev produit ainsi des scores distincts. Le span de "Bob" est
    raccourci d'un caractère pour qu'errors_dev.csv contienne un FN et un FP exacts.
    """
    calls: list[tuple[str, float]] = []

    def fake_detect(text: str, config: Any) -> list[Detection]:
        """Enregistre le texte et le seuil, sans charger aucun modèle."""
        calls.append((text, config.threshold))
        if config.threshold > 0.55:
            return []
        end = 2 if text.startswith("Bob") else 3
        return [Detection(0, end, EntityType.PERSON, 0.8, Source.MANUAL, text[:end])]

    monkeypatch.setattr(run, "detect", fake_detect)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    write_split(corpus, "dev", DEV_TEXTS)
    write_split(corpus, "test", TEST_TEXTS)
    return corpus, tmp_path / "results", calls


def snapshot(out: Path) -> dict[str, bytes]:
    """Renvoie le contenu binaire de chaque fichier du dossier de résultats."""
    return {path.name: path.read_bytes() for path in sorted(out.iterdir())}


def csv_rows(path: Path) -> list[dict[str, str]]:
    """Relit un CSV de résultats sous forme de dictionnaires."""
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    """Calcule l'empreinte attendue d'un corpus fictif."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_test_run_keeps_dev_results_and_uses_saved_threshold(
    synthetic_runs: tuple[Path, Path, list[tuple[str, float]]],
) -> None:
    """Après dev, test ajoute ses lignes au seuil retenu sans toucher aux sorties dev."""
    corpus, out, calls = synthetic_runs
    dev = run.run_evaluation("dev", CONFIGS, out, corpus)
    dev_rows = dev["metrics_by_type"]
    dev_csv = csv_rows(out / "metrics_by_type.csv")
    preserved = {name: (out / name).read_bytes() for name in DEV_FILES}
    threshold = json.loads(preserved["threshold.json"])["threshold"]
    assert threshold == 0.3
    assert csv_rows(out / "errors_dev.csv")
    calls.clear()

    report = run.run_evaluation("test", CONFIGS, out, corpus)
    assert sorted(calls) == sorted((text, threshold) for text in TEST_TEXTS for _ in CONFIGS)
    assert not any(text in DEV_TEXTS for text, _ in calls)
    assert {name: (out / name).read_bytes() for name in DEV_FILES} == preserved
    saved = json.loads((out / "results.json").read_text(encoding="utf-8"))
    for rows in (report["metrics_by_type"], saved["metrics_by_type"]):
        assert [row for row in rows if row["split"] == "dev"] == dev_rows
        assert {row["split"] for row in rows} == {"dev", "test"}
        assert {row["threshold"] for row in rows if row["split"] == "test"} == {threshold}
    written = csv_rows(out / "metrics_by_type.csv")
    assert [row for row in written if row["split"] == "dev"] == dev_csv
    assert {row["split"] for row in written} == {"dev", "test"}
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "| dev | hybrid |" in summary
    assert "| test | hybrid |" in summary
    assert saved["threshold_sweep"] == dev["threshold_sweep"]
    assert len(saved["threshold_sweep"]) == len(run.THRESHOLDS)
    assert saved["metadata"]["corpus_sha256"] == {
        "dev.jsonl": sha256(corpus / "dev.jsonl"),
        "test.jsonl": sha256(corpus / "test.jsonl"),
    }
    assert saved["metadata"]["document_counts"] == {"dev": 2, "test": 1}
    assert saved["selected_threshold"] == dev["selected_threshold"]
    assert [row for row in saved["bootstrap_intervals"] if row["split"] == "dev"] == dev[
        "bootstrap_intervals"
    ]
    assert not (out / "errors_test.csv").exists()


def test_threshold_mismatch_is_rejected_before_any_detection(
    synthetic_runs: tuple[Path, Path, list[tuple[str, float]]],
) -> None:
    """Un threshold.json modifié après dev bloque test sans détection ni écriture."""
    corpus, out, calls = synthetic_runs
    run.run_evaluation("dev", CONFIGS, out, corpus)
    run.write_json(out / "threshold.json", {"threshold": 0.65, "criterion": run.CRITERION})
    before = snapshot(out)
    calls.clear()
    with pytest.raises(ValueError, match="seuils différents"):
        run.run_evaluation("test", CONFIGS, out, corpus)
    assert calls == []
    assert snapshot(out) == before


def test_repeated_test_does_not_duplicate_and_new_dev_drops_stale_test(
    synthetic_runs: tuple[Path, Path, list[tuple[str, float]]],
) -> None:
    """Deux mesures test se remplacent ; un nouveau dev efface les traces test."""
    corpus, out, _ = synthetic_runs
    run.run_evaluation("dev", CONFIGS, out, corpus)
    first = run.run_evaluation("test", CONFIGS, out, corpus)
    first_csv = (out / "metrics_by_type.csv").read_bytes()
    first_summary = (out / "summary.md").read_text(encoding="utf-8")
    second = run.run_evaluation("test", CONFIGS, out, corpus)
    assert second["metrics_by_type"] == first["metrics_by_type"]
    assert (out / "metrics_by_type.csv").read_bytes() == first_csv
    assert (out / "summary.md").read_text(encoding="utf-8") == first_summary
    keys = [
        (row["split"], row["config"], row["mode"], row["type"]) for row in second["metrics_by_type"]
    ]
    assert len(keys) == len(set(keys))
    assert second["metadata"]["document_counts"] == {"dev": 2, "test": 1}

    dev = run.run_evaluation("dev", CONFIGS, out, corpus)
    saved = json.loads((out / "results.json").read_text(encoding="utf-8"))
    for report in (dev, saved):
        assert {row["split"] for row in report["metrics_by_type"]} == {"dev"}
        assert report["metadata"]["corpus_sha256"] == {"dev.jsonl": sha256(corpus / "dev.jsonl")}
        assert report["metadata"]["document_counts"] == {"dev": 2}
    assert {row["split"] for row in csv_rows(out / "metrics_by_type.csv")} == {"dev"}
    assert "| test |" not in (out / "summary.md").read_text(encoding="utf-8")


def test_challenge_preserves_intervals_and_reports_blind_split(
    synthetic_runs: tuple[Path, Path, list[tuple[str, float]]],
) -> None:
    """Challenge fictif conserve les comptes et intervalles antérieurs sans relire leurs corpus."""
    corpus, out, calls = synthetic_runs
    write_split(corpus, "challenge", ("Ivo answers.", "Lia signs."))
    dev = run.run_evaluation("dev", CONFIGS, out, corpus)
    before = run.run_evaluation("test", CONFIGS, out, corpus)
    (corpus / "dev.jsonl").unlink()
    (corpus / "test.jsonl").unlink()
    calls.clear()
    after = run.run_evaluation("challenge", ["hybrid"], out, corpus)
    assert len(calls) == 2
    assert all(text.startswith(("Ivo", "Lia")) and threshold == 0.3 for text, threshold in calls)
    assert [row for row in after["bootstrap_intervals"] if row["split"] != "challenge"] == before[
        "bootstrap_intervals"
    ]
    assert after["dev_error_categories"] == dev["dev_error_categories"]
    assert after["bootstrap_method"] == {
        "method": "document percentile bootstrap",
        "draws": 2000,
        "seed": 45,
        "confidence_level": 0.95,
        "percentile_interpolation": "linear (n - 1) * p",
        "mode": "partial",
        "type": "micro",
    }
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "## 95% bootstrap intervals" in summary
    assert summary.index("## 95% bootstrap intervals") > summary.index("| challenge | hybrid |")
    assert "Challenge was written blind" in summary
    assert "| boundary | 2 |" in summary
    assert not (out / "errors_challenge.csv").exists()
    repeated = run.run_evaluation("challenge", ["hybrid"], out, corpus)
    assert repeated["bootstrap_intervals"] == after["bootstrap_intervals"]


def test_common_challenge_loader_validates_fictional_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le chargeur commun reconnaît challenge et refuse les mêmes spans incohérents."""
    from huisclos.evaluation import corpus

    write_split(tmp_path, "challenge", ("Ivo writes.",))
    monkeypatch.setattr(corpus, "CORPUS_DIR", tmp_path)
    documents = corpus.load_split("challenge")
    assert documents[0].split == "challenge"
    assert documents == run.load_challenge_corpus(tmp_path / "challenge.jsonl")
    record = json.loads((tmp_path / "challenge.jsonl").read_text(encoding="utf-8"))
    record["entities"][0]["end"] = 100
    (tmp_path / "challenge.jsonl").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError):
        corpus.load_split("challenge")


def test_report_helpers_keep_metadata_and_format_robustness_cells(tmp_path: Path) -> None:
    """Empreinte et commit extraits de metadata ; cellules n/a, yes/no et intervalles lisibles."""
    path = tmp_path / "dev.jsonl"
    path.write_bytes(b"{}\n")
    assert reports.file_sha256(path) == hashlib.sha256(b"{}\n").hexdigest()
    commit = reports.git_commit()
    assert commit is None or len(commit) == 40
    assert reports.metadata([path], ["hybrid"], 0.3)["git_commit"] == commit
    assert [reports.cell_text(value) for value in (None, True, 0.25, 3, "x")] == [
        "n/a",
        "yes",
        "0.2500",
        "3",
        "x",
    ]
    assert reports.bounds_text({"lower": None, "upper": None}) == "n/a"
    assert reports.bounds_text({"lower": 0.1, "upper": 0.25}) == "[0.1000, 0.2500]"
    assert reports.markdown_table(("A", "B"), [(None, 1.0)]) == [
        "| A | B |",
        "| --- | --- |",
        "| n/a | 1.0000 |",
    ]
