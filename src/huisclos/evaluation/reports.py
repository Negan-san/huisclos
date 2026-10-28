"""Écrit les rapports agrégés de l'évaluation locale.

Entrées : lignes de métriques, intervalles et métadonnées sans texte sensible.
Sorties : fichiers JSON, CSV et synthèses Markdown en anglais, dont celle du rapport de
robustesse (couverture complète, alertes, différences appariées).
Place dans le pipeline : export après calcul des mesures par evaluation.run ou par le pilote.
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


def git_commit(root: Path = ROOT) -> str | None:
    """Renvoie le commit courant du dépôt root, ou None si git est indisponible."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def file_sha256(path: Path) -> str:
    """Renvoie l'empreinte SHA-256 du fichier, lu en binaire sans rien afficher."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def metadata(paths: Sequence[Path], names: Sequence[str], threshold: float) -> dict[str, Any]:
    """Décrit versions, fichiers effectivement évalués, réglages, commit et date UTC."""
    commit = git_commit()
    fingerprints = {path.name: file_sha256(path) for path in paths}
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


def cell_text(value: Any) -> str:
    """Écrit un ratio sur quatre décimales, un booléen en yes/no, None en n/a, le reste tel quel."""
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def bounds_text(interval: dict[str, Any]) -> str:
    """Écrit un intervalle [bas, haut] sur quatre décimales, ou n/a sans tirage défini."""
    if interval.get("lower") is None:
        return "n/a"
    return f"[{interval['lower']:.4f}, {interval['upper']:.4f}]"


def markdown_table(header: Sequence[str], rows: Iterable[Sequence[Any]]) -> list[str]:
    """Construit un tableau Markdown ; chaque cellule passe par cell_text."""
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines.extend("| " + " | ".join(cell_text(cell) for cell in row) + " |" for row in rows)
    return lines


ROBUSTNESS_COVERAGE = {
    "Entities": "reference_entities",
    "Fully covered": "entities_fully_covered",
    "Partially exposed": "entities_partially_exposed",
    "Fully exposed": "entities_fully_exposed",
    "Any exposure": "entities_with_any_exposure",
    "Full coverage rate": "full_coverage_rate",
    "Leaked characters": "leaked_characters",
    "Leaked character rate": "leaked_character_rate",
    "Documents with exposure": "documents_with_any_exposure",
    "Non-sensitive masked": "non_sensitive_characters_masked",
    "Over-masking rate": "non_sensitive_masked_rate",
}
ROBUSTNESS_ALERTS = {
    "Alerts": "alerts",
    "Documents with alerts": "documents_with_alerts",
    "On visible references": "alerts_on_visible_references",
    "Elsewhere": "alerts_elsewhere",
    "Exposed entities": "exposed_entities",
    "Exposed entities alerted": "exposed_entities_alerted",
}
ROBUSTNESS_CRITERION = {
    "Lower leakage": "lower_leakage",
    "Higher full coverage": "higher_full_coverage",
    "Precision within 2 points": "precision_within_margin",
    "Over-masking within 1 point": "over_masking_within_margin",
    "Recommended": "met",
}


def _robustness_tables(report: dict[str, Any]) -> list[str]:
    """Construit les tableaux de couverture, d'alertes, d'intervalles et de comparaisons."""
    lines = []
    for scope, title in (
        ("evaluated", "Full coverage, eleven evaluated types"),
        ("custom_location", "CUSTOM and LOCATION, separate scope"),
    ):
        rows = [row for row in report["coverage"] if row["scope"] == scope]
        lines.extend(["", f"## {title}", ""])
        lines.extend(
            markdown_table(
                ("Profile", "Stage", *ROBUSTNESS_COVERAGE),
                (
                    (
                        row["config"],
                        row["stage"],
                        *(row[key] for key in ROBUSTNESS_COVERAGE.values()),
                    )
                    for row in rows
                ),
            )
        )
    lines.extend(["", "## Coverage 95% bootstrap intervals", ""])
    lines.extend(
        markdown_table(
            ("Profile", "Stage", "Metric", "Interval", "Undefined draws"),
            (
                (
                    row["config"],
                    row["stage"],
                    row["metric"],
                    bounds_text(row),
                    row["undefined_draws"],
                )
                for row in report["coverage_intervals"]
            ),
        )
    )
    lines.extend(["", "## Final check alerts (alerts mask nothing)", ""])
    lines.extend(
        markdown_table(
            ("Profile", "Check threshold", *ROBUSTNESS_ALERTS),
            (
                (
                    row["config"],
                    row["check_threshold"],
                    *(row.get(key, "unavailable") for key in ROBUSTNESS_ALERTS.values()),
                )
                for row in report["final_check"]
            ),
        )
    )
    lines.extend(["", "## Paired differences (candidate minus reference, same draws)", ""])
    paired = report["paired_differences"]
    lines.extend(
        markdown_table(
            ("Candidate", "Reference", "Stage", "Metric", "Estimate", "95% interval")
            + ("Undefined draws", "Excludes zero"),
            (
                (row["candidate"], row["reference"], row["stage"], row["metric"], row["estimate"])
                + (bounds_text(row), row["undefined_draws"], row["excludes_zero"])
                for row in paired
            ),
        )
        if paired
        else ["No paired comparison was planned: marginal intervals support no significance claim."]
    )
    lines.extend(["", "## Engineering criterion (not a legal threshold)", ""])
    lines.extend(
        markdown_table(
            ("Candidate", "Reference", *ROBUSTNESS_CRITERION),
            (
                (
                    row["candidate"],
                    row["reference"],
                    *(row.get(key) for key in ROBUSTNESS_CRITERION.values()),
                )
                for row in report["engineering_criteria"]
            ),
        )
        if report["engineering_criteria"]
        else ["No comparison was planned."]
    )
    return lines


def robustness_summary(report: dict[str, Any]) -> list[str]:
    """Renvoie la synthèse anglaise du rapport de robustesse, sans contenu de document."""
    meta = report["metadata"]
    intervals = {row["config"]: row for row in report["bootstrap_intervals"]}
    micro = [
        row
        for row in report["metrics_by_type"]
        if row["mode"] == "partial" and row["type"] == "micro"
    ]
    lines = [
        "# Robustness report",
        "",
        f"Dataset {meta['dataset_id']}: split {meta['split']}, {meta['document_count']} documents, "
        f"document language {meta['document_language']}, mode {meta['mode']}.",
        f"Measurement code commit: {meta['git_commit']}. Plan SHA-256: {meta['plan_sha256']}.",
        f"Corpus SHA-256: {meta['corpus_sha256']}.",
        "",
        *report["notes"],
        "",
        "## Historical metrics (detection stage, partial matching, micro)",
        "",
        *markdown_table(
            ("Profile", "Threshold", "Precision", "Recall", "F2", "Leak rate", "Exposed entities")
            + ("Precision 95%", "Recall 95%", "Leak rate 95%"),
            (
                (row["config"], f"{row['threshold']:.2f}")
                + tuple(
                    row[key]
                    for key in ("precision", "recall", "f2", "leak_rate", "exposed_entities")
                )
                + tuple(
                    bounds_text(intervals[row["config"]][key])
                    for key in ("precision", "recall", "leak_rate")
                )
                for row in micro
            ),
        ),
        *_robustness_tables(report),
        "",
    ]
    return lines
