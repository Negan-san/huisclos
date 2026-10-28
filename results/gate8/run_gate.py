"""Enregistre les prérequis puis autorise une seule mesure réservée par split.

Entrées : rapports dev vérifiés, plans figés et nom explicite du split autorisé.
Sorties : reçus sans contenu et rapports agrégés réutilisant les mêmes prédictions.
Un reçu d'essai est créé avant le lancement ; il interdit tout nouvel essai aveugle.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ASSETS = ROOT.parent / "pilotage/post_g7_assets"


def read(path: Path) -> Any:
    """Lit un rapport agrégé ou un plan ; jamais un corpus."""
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    """Hache le fichier demandé sans en afficher le contenu."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    """Crée un artefact neuf, sans remplacer un rapport ou un reçu."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def prepare() -> None:
    """Vérifie les seuils et résultats dev avant de figer toutes les mesures réservées."""
    assert read(OUT / "historical/threshold.json")["threshold"] == 0.3
    assert read(OUT / "dev_en_threshold/threshold.json")["threshold"] == 0.3
    assert read(OUT / "provenance.json")["c3_logic_changes"] == 0
    assert len(read(OUT / "offline_guarded.json")) == 4
    assert read(OUT / "checks_before_reserved.json")["all_green"] is True
    reports = {}
    for language in ("fr", "en"):
        report = read(OUT / f"dev_{language}/robustness.json")
        plan = read(OUT / f"plan_{language}.json")
        assert report["metadata"]["split"] == "dev"
        assert report["metadata"]["plan_sha256"] == digest(OUT / f"plan_{language}.json")
        assert set(report["metadata"]["profiles"]) == set(plan["profiles"])
        for profile in report["metadata"]["profiles"].values():
            assert profile["configuration"]["threshold"] == 0.3
            if profile["configuration"].get("use_gliner"):
                assert profile["configuration"]["gliner_threshold"] == 0.7
        rows = {
            row["config"]: row
            for row in report["coverage"]
            if row["stage"] == "pseudonymization" and row["scope"] == "evaluated"
        }
        if language == "fr":
            assert all(row["entities_fully_covered"] == 311 for row in rows.values())
            assert all(row["leaked_characters"] == 0 for row in rows.values())
        else:
            assert rows["standard"]["entities_fully_covered"] == 124
            assert rows["enhanced"]["entities_fully_covered"] == 126
            assert rows["standard"]["leaked_characters"] == 105
            assert rows["enhanced"]["leaked_characters"] == 63
        reports[language] = digest(OUT / f"dev_{language}/robustness.json")
    historical = read(OUT / "plan_fr.json")
    historical["profiles"] = {
        name: value
        for name, value in historical["profiles"].items()
        if name in {"standard", "enhanced"}
    }
    historical["comparisons"] = [["enhanced", "standard"]]
    save(OUT / "plan_historical_fr.json", historical)
    paths = [
        ROOT / "scripts/gate8_measure.py",
        ROOT / "scripts/evaluate_robustness.py",
        Path(__file__).resolve(),
        OUT / "plan_fr.json",
        OUT / "plan_en.json",
        OUT / "plan_historical_fr.json",
    ]
    save(
        OUT / "registration.json",
        {
            "registered_at_utc": datetime.now(UTC).isoformat(),
            "dev_reports": reports,
            "artifact_sha256": {str(path.relative_to(ROOT)): digest(path) for path in paths},
            "thresholds": {"fr": 0.3, "en": 0.3, "gliner": 0.7, "final_check": 0.1},
            "bootstrap": {"draws": 2000, "seed": 45, "paired": True},
            "margins": {"partial_precision": 0.02, "overmasking": 0.01},
            "historical_test_measurement_number": 4,
            "historical_predecessors": ["G4", "G4bis", "G7"],
            "g7_english_reference_available": False,
            "reserved_series": ["blind_fr", "blind_en", "test", "challenge"],
            "new_threshold_selection_allowed": False,
            "details_export_allowed": False,
        },
    )
    print("G8 registered: dev thresholds and profiles agree; reserved series may begin.")


def measure(split: str) -> None:
    """Mesure le split une seule fois, avec garde des hashes et reçus persistants."""
    registration = read(OUT / "registration.json")
    for relative, expected in registration["artifact_sha256"].items():
        assert digest(ROOT / relative) == expected, "Frozen measurement artifact changed"
    language = "en" if split == "blind_en" else "fr"
    if split.startswith("blind_"):
        corpus = ROOT / f"corpus/blind_post_g7/{language}/challenge.jsonl"
        plan = OUT / f"plan_{language}.json"
    else:
        corpus = ROOT / f"corpus/{split}.jsonl"
        plan = OUT / "plan_historical_fr.json"
    destination = OUT / split
    assert not destination.exists()
    save(
        OUT / f"attempt_{split}.json",
        {
            "started_at_utc": datetime.now(UTC).isoformat(),
            "split": split,
            "corpus_sha256": digest(corpus),
            "plan_sha256": digest(plan),
            "repeat_forbidden": True,
        },
    )
    environment = os.environ | {
        "HUISCLOS_MODELS_DIR": str(ASSETS),
        "PYTHONUTF8": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "OMP_NUM_THREADS": "2",
        "MKL_NUM_THREADS": "2",
        "TOKENIZERS_PARALLELISM": "false",
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/gate8_measure.py"),
            "--corpus",
            str(corpus),
            "--dataset-id",
            f"gate8_{split}",
            "--plan",
            str(plan),
            "--out",
            str(destination),
            "--mode",
            "gate",
        ],
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Reserved measure failed with exit {completed.returncode}; repeat forbidden"
        )
    report = read(destination / "robustness.json")
    if not split.startswith("blind_"):
        report = json.loads(json.dumps(report))
        names = {"standard": "hybrid", "enhanced": "hybrid_camembert"}
        for key in ("metrics_by_type", "bootstrap_intervals"):
            for row in report[key]:
                row["config"] = names[row["config"]]
        report["metadata"]["document_counts"] = {split: report["metadata"]["document_count"]}
        report["metadata"]["configurations"] = {
            names[name]: value for name, value in report["metadata"]["profiles"].items()
        }
        save(destination / "results.json", report)
        save(
            destination / "threshold.json", {"threshold": 0.3, "criterion": "frozen dev threshold"}
        )
    save(
        OUT / f"complete_{split}.json",
        {
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "report_sha256": digest(destination / "robustness.json"),
            "document_count": report["metadata"]["document_count"],
        },
    )
    print(f"Reserved {split}: one series complete, aggregate report archived.")


def main() -> None:
    """Exige une préparation explicite ou un seul split réservé nommé."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--split", choices=("blind_fr", "blind_en", "test", "challenge"))
    args = parser.parse_args()
    if args.prepare and not args.split:
        prepare()
    elif args.split and not args.prepare:
        measure(args.split)
    else:
        parser.error("Choose --prepare or one explicit --split")


if __name__ == "__main__":
    main()
