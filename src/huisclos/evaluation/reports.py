"""Écrit les rapports agrégés de l'évaluation locale.

Entrées : lignes de métriques, intervalles et métadonnées sans texte sensible.
Sorties : fichiers JSON, CSV et synthèse Markdown en anglais.
Place dans le pipeline : export après calcul des mesures par evaluation.run.
"""

import csv
import hashlib
import json
import platform
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from huisclos.config import PRESETS
from huisclos.evaluation.intervals import INTERVAL_METRICS

ROOT = Path(__file__).resolve().parents[3]


def write_csv(path: Path, columns: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    """Écrit les colonnes et lignes ordonnées en UTF-8 avec des fins de ligne fixes."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    """Écrit une valeur JSON lisible en UTF-8 ; ne reçoit aucun texte du corpus."""
    path.write_text(
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def package_version(name: str) -> str | None:
    """Renvoie la version locale du paquet, ou None s'il est absent."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def metadata(paths: Sequence[Path], names: Sequence[str], threshold: float) -> dict[str, Any]:
    """Décrit versions, fichiers effectivement évalués, réglages, commit et date UTC."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    fingerprints = {}
    for path in paths:
        with path.open("rb") as stream:
            fingerprints[path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
    configs = {}
    for name in names:
        values = asdict(replace(PRESETS[name], threshold=threshold))
        values["enabled_types"] = sorted(kind.value for kind in values["enabled_types"])
        configs[name] = values
    model = PRESETS["hybrid"].spacy_model
    return {
        "date": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "versions": {
            "python": platform.python_version(),
            "spacy": package_version("spacy"),
            "presidio_analyzer": package_version("presidio-analyzer"),
            "presidio_anonymizer": package_version("presidio-anonymizer"),
            "model": {"name": model, "version": package_version(model)},
        },
        "corpus_sha256": fingerprints,
        "configurations": configs,
    }


def write_summary(
    path: Path,
    rows: Sequence[dict[str, Any]],
    notes: Sequence[str],
    intervals: Sequence[dict[str, Any]] = (),
    error_counts: dict[str, int] | None = None,
) -> None:
    """Écrit le tableau anglais micro partiel et les conventions de calcul."""
    lines = [
        "# Evaluation summary",
        "",
        "Partial matching, micro averages. Predictions use the selected threshold in detect().",
        "Leakage measures uncovered reference characters across all evaluated prediction types.",
        "LOCATION and CUSTOM are excluded. Macro averages include all eleven evaluated types",
        "with zero for undefined ratios; macro counts are arithmetic means of type counts.",
        "Partial pairs are assigned by descending overlap, then positions, one to one.",
        "Development errors use exact matching and include 30 characters on each side.",
        "",
        "| Split | Configuration | Threshold | Precision | Recall | F2 | "
        "Leak rate | Exposed entities |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        if row["mode"] == "partial" and row["type"] == "micro":
            lines.append(
                f"| {row['split']} | {row['config']} | {row['threshold']:.2f} | "
                f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f2']:.4f} | "
                f"{row['leak_rate']:.4f} | {row['exposed_entities']} |"
            )
    if intervals:
        lines.extend(
            [
                "",
                "## 95% bootstrap intervals",
                "",
                "Document resampling with replacement, 2,000 draws, random.Random seed 45.",
                "Percentiles 2.5 and 97.5 use linear interpolation; the threshold stays fixed.",
                "Ratios are recomputed from summed document counts (partial matching, micro).",
                "Undefined ratios are zero. A single document gives a collapsed interval.",
                "These intervals do not account for corpus bias or threshold selection.",
                "",
                "| Split | Configuration | Threshold | Documents | Precision | Recall | F2 | "
                "Leak rate |",
                "| --- | --- | ---: | ---: | --- | --- | --- | --- |",
            ]
        )
        for row in intervals:
            bounds = " | ".join(
                f"[{row[name]['lower']:.4f}, {row[name]['upper']:.4f}]" for name in INTERVAL_METRICS
            )
            lines.append(
                f"| {row['split']} | {row['config']} | {row['threshold']:.2f} | "
                f"{row['documents']} | {bounds} |"
            )
    if any(row["split"] == "challenge" for row in rows):
        lines.extend(
            [
                "",
                "Challenge was written blind after the detection rules were frozen.",
                "It uses the threshold selected on dev, without tuning on challenge.",
            ]
        )
    if error_counts:
        lines.extend(
            [
                "",
                "## Development error categories",
                "",
                "Exact FN/FP rows for hybrid; one boundary or type error can produce two rows.",
                "Overlapping unmatched spans: type confusion takes priority over boundary errors.",
                "",
                "| Category | Error rows |",
                "| --- | ---: |",
            ]
        )
        lines.extend(f"| {category} | {count} |" for category, count in error_counts.items())
    lines.extend(["", *notes, ""])
    path.write_text("\n".join(lines), encoding="utf-8")
