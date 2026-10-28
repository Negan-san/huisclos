"""Compare deux jeux de résultats enregistrés, sans relire les documents.

Entrées : dossiers de référence et actuel, split demandé et dossier de sortie.
Sorties : tableau avant/après JSON et Markdown, avec intervalles disponibles et écarts.
Place dans le pipeline : analyse après les gates, sans nouvelle évaluation.
"""

import json
import math
from pathlib import Path
from typing import Any

from huisclos.evaluation.intervals import INTERVAL_METRICS
from huisclos.evaluation.reports import write_json

COMPARISON_METRICS = (*INTERVAL_METRICS, "exposed_entities")


def selected_rows(report: dict[str, Any], split: str) -> dict[str, dict[str, Any]]:
    """Retient les lignes micro partielles au seuil propre au rapport, sans doublon."""
    threshold = report["selected_threshold"]["threshold"]
    rows = {}
    for row in report["metrics_by_type"]:
        if (row["split"], row["mode"], row["type"], row["threshold"]) != (
            split,
            "partial",
            "micro",
            threshold,
        ):
            continue
        if row["config"] in rows:
            raise ValueError("Configuration dupliquée au seuil retenu.")
        for name in COMPARISON_METRICS:
            value = row[name]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Une mesure doit être un nombre fini.")
        rows[row["config"]] = row
    if not rows:
        raise ValueError(f"Aucune mesure micro partielle pour {split} au seuil retenu.")
    return rows


def saved_interval(
    report: dict[str, Any], row: dict[str, Any], metric: str
) -> dict[str, float] | None:
    """Renvoie l'intervalle de cette ligne, ou None pour les anciens rapports sans intervalle."""
    for interval in report.get("bootstrap_intervals", []):
        if all(
            interval[key] == row[key] for key in ("split", "config", "threshold", "mode", "type")
        ):
            bounds = interval.get(metric)
            if bounds is None:
                return None
            lower, upper = bounds["lower"], bounds["upper"]
            if not (0 <= lower <= upper <= 1):
                raise ValueError("Intervalle hors de [0, 1] ou bornes inversées.")
            return {"lower": lower, "upper": upper}
    return None


def compare_reports(
    reference: dict[str, Any], current: dict[str, Any], split: str
) -> dict[str, Any]:
    """Compare les configurations des deux rapports ; l'écart vaut actuel moins référence.

    L'union des configurations garde visibles les configurations ajoutées ou retirées.
    Les intervalles manquants restent nuls ; aucun intervalle d'écart ni test de
    significativité n'est déduit de deux intervalles marginaux.
    """
    if split not in {"dev", "test", "challenge"}:
        raise ValueError("Split attendu : dev, test ou challenge.")
    before = selected_rows(reference, split)
    after = selected_rows(current, split)
    rows = []
    for config in sorted(before.keys() | after.keys()):
        old, new = before.get(config), after.get(config)
        for metric in COMPARISON_METRICS:
            rows.append(
                {
                    "config": config,
                    "metric": metric,
                    "reference": old[metric] if old else None,
                    "current": new[metric] if new else None,
                    "reference_interval": saved_interval(reference, old, metric) if old else None,
                    "current_interval": saved_interval(current, new, metric) if new else None,
                    "delta": new[metric] - old[metric] if old and new else None,
                }
            )
    sources = {}
    for name, report in (("reference", reference), ("current", current)):
        metadata = report.get("metadata", {})
        sources[name] = {
            "threshold": report["selected_threshold"]["threshold"],
            "git_commit": metadata.get("git_commit"),
            "date": metadata.get("date"),
            "documents": metadata.get("document_counts", {}).get(split),
            "corpus_sha256": metadata.get("corpus_sha256", {}).get(f"{split}.jsonl"),
            "bootstrap_method": report.get("bootstrap_method"),
        }
    warnings = []
    for field in ("threshold", "corpus_sha256"):
        old_value, new_value = sources["reference"][field], sources["current"][field]
        if old_value is None or new_value is None:
            warnings.append(f"{field}_missing")
        elif old_value != new_value:
            warnings.append(f"{field}_different")
    return {"split": split, "sources": sources, "warnings": warnings, "rows": rows}


def comparison_markdown(comparison: dict[str, Any]) -> str:
    """Rend le tableau anglais avec les bornes disponibles et la provenance des deux mesures."""
    lines = [
        f"# Before/after comparison: {comparison['split']}",
        "",
        "Partial matching, micro averages, each report at its selected threshold.",
        "Delta = current - reference (proportions, except exposed entity counts).",
        "Missing configurations or intervals are marked 'Not recorded'.",
        "Marginal 95% intervals do not provide an interval or a significance test for the delta.",
        "",
    ]
    for name, source in comparison["sources"].items():
        lines.append(
            f"{name}: commit {source['git_commit']}, threshold {source['threshold']}, "
            f"documents {source['documents']}, corpus SHA-256 {source['corpus_sha256']}."
        )
    lines.extend(f"Warning: {warning}." for warning in comparison["warnings"])
    lines.extend(
        [
            "",
            "| Configuration | Metric | Reference | Current | Reference 95% interval | "
            "Current 95% interval | Delta |",
            "| --- | --- | ---: | ---: | --- | --- | ---: |",
        ]
    )
    for row in comparison["rows"]:
        values = [row["config"], row["metric"]]
        for key in ("reference", "current", "reference_interval", "current_interval", "delta"):
            value = row[key]
            if value is None:
                shown = "Not recorded"
            elif isinstance(value, dict):
                shown = f"[{value['lower']:.4f}, {value['upper']:.4f}]"
            else:
                shown = f"{value:+.4f}" if key == "delta" else f"{value:.4f}"
            values.append(shown)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join([*lines, ""])


def compare_result_folders(reference: Path, current: Path, split: str, out: Path) -> dict[str, Any]:
    """Lit deux results.json et écrit uniquement les deux fichiers de comparaison du split."""
    reports = [
        json.loads((folder / "results.json").read_text(encoding="utf-8"))
        for folder in (reference, current)
    ]
    comparison = compare_reports(*reports, split)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / f"{split}_comparison.json", comparison)
    (out / f"{split}_comparison.md").write_text(comparison_markdown(comparison), encoding="utf-8")
    return comparison
