"""Vérifie les comparaisons avant/après sur deux dossiers entièrement fictifs.

Entrées : rapports synthétiques anciens ou enrichis, sans texte ni document du corpus.
Sorties : assertions sur les écarts, les intervalles, les absences et la commande CLI.
Place dans le pipeline : validation des exports de comparaison destinés aux gates.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from huisclos.evaluation.comparison import (
    compare_reports,
    compare_result_folders,
    comparison_markdown,
)
from huisclos.evaluation.intervals import BOOTSTRAP_METHOD, INTERVAL_METRICS


def fake_report(current: bool) -> dict[str, Any]:
    """Construit un rapport à deux configurations, au seul seuil retenu, sur challenge fictif."""
    values = (0.9, 0.75, 0.8, 0.1, 1) if current else (0.8, 0.5, 0.6, 0.2, 2)
    rows, intervals = [], []
    for config in ("hybrid", "patterns_only"):
        identity = {
            "split": "challenge",
            "config": config,
            "threshold": 0.3,
            "mode": "partial",
            "type": "micro",
        }
        scores = dict(zip((*INTERVAL_METRICS, "exposed_entities"), values, strict=True))
        rows.append({**identity, **scores})
        intervals.append(
            {
                **identity,
                "documents": 2,
                **{
                    key: {"lower": max(0, scores[key] - 0.1), "upper": min(1, scores[key] + 0.1)}
                    for key in INTERVAL_METRICS
                },
            }
        )
    return {
        "metrics_by_type": rows,
        "bootstrap_intervals": intervals,
        "bootstrap_method": BOOTSTRAP_METHOD,
        "selected_threshold": {"threshold": 0.3},
        "metadata": {
            "git_commit": "after" if current else "before",
            "document_counts": {"challenge": 2},
            "corpus_sha256": {"challenge.jsonl": "fictional-sha256"},
        },
    }


def test_compare_folders_and_cli(tmp_path: Path) -> None:
    """Le CLI produit les mêmes lignes que l'API et n'écrit que les deux fichiers attendus."""
    folders = [tmp_path / name for name in ("reference", "current")]
    for current, folder in enumerate(folders):
        folder.mkdir()
        (folder / "results.json").write_text(
            json.dumps(fake_report(bool(current))), encoding="utf-8"
        )
    snapshots = [(folder / "results.json").read_bytes() for folder in folders]
    out = tmp_path / "results"
    report = compare_result_folders(*folders, "challenge", out)
    assert report["warnings"] == []
    assert len(report["rows"]) == 10
    assert [row["delta"] for row in report["rows"][:5]] == pytest.approx([0.1, 0.25, 0.2, -0.1, -1])
    assert report["rows"][0]["current_interval"]["lower"] == pytest.approx(0.8)
    assert report["rows"][4]["current_interval"] is None
    assert report["sources"]["reference"]["git_commit"] == "before"
    assert json.loads((out / "challenge_comparison.json").read_text(encoding="utf-8")) == report
    assert (out / "challenge_comparison.md").read_text(encoding="utf-8") == comparison_markdown(
        report
    )
    command = [
        sys.executable,
        "scripts/compare_results.py",
        *map(str, folders),
        "--split",
        "challenge",
        "--out",
        str(out),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    assert result.returncode == 0, result.stderr
    assert sorted(path.name for path in out.iterdir()) == [
        "challenge_comparison.json",
        "challenge_comparison.md",
    ]
    assert snapshots == [(folder / "results.json").read_bytes() for folder in folders]


def test_old_reports_missing_intervals_and_configurations() -> None:
    """Les valeurs absentes restent nulles, sans intervalle ou écart inventé."""
    before, after = fake_report(False), fake_report(True)
    del before["bootstrap_intervals"]
    after["metrics_by_type"].pop()
    comparison = compare_reports(before, after, "challenge")
    assert all(row["reference_interval"] is None for row in comparison["rows"])
    missing = [row for row in comparison["rows"] if row["config"] == "patterns_only"]
    assert all(row["current"] is row["delta"] is row["current_interval"] is None for row in missing)
    assert "Not recorded" in comparison_markdown(comparison)
    reverse = compare_reports(after, before, "challenge")
    assert all(
        row["reference"] is None for row in reverse["rows"] if row["config"] == "patterns_only"
    )


def test_different_thresholds_and_corpora_are_disclosed() -> None:
    """Un changement du jeu de documents ou du seuil est enregistré dans les avertissements."""
    before, after = fake_report(False), fake_report(True)
    after["selected_threshold"]["threshold"] = 0.5
    for row in (*after["metrics_by_type"], *after["bootstrap_intervals"]):
        row["threshold"] = 0.5
    after["metadata"]["corpus_sha256"]["challenge.jsonl"] = "changed"
    assert compare_reports(before, after, "challenge")["warnings"] == [
        "threshold_different",
        "corpus_sha256_different",
    ]
    before["metadata"].pop("corpus_sha256")
    assert "corpus_sha256_missing" in compare_reports(before, after, "challenge")["warnings"]


@pytest.mark.parametrize("invalid", ["split", "empty", "duplicate", "nan", "interval"])
def test_invalid_comparisons_fail_without_writing(tmp_path: Path, invalid: str) -> None:
    """Les données impossibles ou ambiguës échouent avant la création du dossier de sortie."""
    report = fake_report(False)
    split = "challenge"
    if invalid == "split":
        split = "../test"
    elif invalid == "empty":
        report["metrics_by_type"] = []
    elif invalid == "duplicate":
        report["metrics_by_type"].append(copy.deepcopy(report["metrics_by_type"][0]))
    elif invalid == "nan":
        report["metrics_by_type"][0]["precision"] = float("nan")
    else:
        report["bootstrap_intervals"][0]["precision"] = {"lower": 0.9, "upper": 0.1}
    (tmp_path / "results.json").write_text(json.dumps(report), encoding="utf-8")
    out = tmp_path / "absent"
    with pytest.raises(ValueError):
        compare_result_folders(tmp_path, tmp_path, split, out)
    assert not out.exists()
