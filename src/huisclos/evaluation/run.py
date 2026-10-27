"""Compare les configurations sur les corpus fictifs sans modifier la détection.

Entrées : split demandé, configurations et dossier de sortie ; seuil choisi sur dev.
Sorties : tableaux déterministes, rapport anglais et erreurs réservées à dev.
Place dans le pipeline : orchestration locale de detect, du corpus et des métriques.
"""

import csv
import hashlib
import json
import os
import platform
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, replace
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from huisclos.config import PRESETS, default_threshold
from huisclos.detection.pipeline import detect
from huisclos.evaluation.corpus import CorpusDocument, load_corpus
from huisclos.evaluation.metrics import (
    Evaluation,
    evaluated_predictions,
    evaluated_references,
    match_entities,
)
from huisclos.models import Detection

ROOT = Path(__file__).resolve().parents[3]
THRESHOLDS = tuple(value / 100 for value in range(30, 96, 5))
CRITERION = "max F2 (partial, micro) on dev"
METRIC_COLUMNS = tuple(
    "split config threshold mode type tp fp fn precision recall f1 f2 leak_rate".split()
)
SWEEP_COLUMNS = ("threshold", "precision", "recall", "f1", "f2", "leak_rate", "exposed_entities")
ERROR_COLUMNS = ("document_id", "type", "text", "context_before", "context_after", "nature")


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


def choose_threshold(sweep: Sequence[dict[str, Any]]) -> float:
    """Renvoie le seuil de F2 maximal, puis le plus bas ; refuse un balayage vide."""
    if not sweep:
        raise ValueError("Le balayage de seuil est vide.")
    return float(min(sweep, key=lambda row: (-row["f2"], row["threshold"]))["threshold"])


def saved_dev_report(out: Path, threshold: float) -> dict[str, Any]:
    """Relit le rapport dev à conserver avant test, au même seuil uniquement.

    Aucun document n'est relu. Un rapport d'un autre seuil est refusé pour éviter
    de présenter comme comparables des mesures obtenues avec des réglages différents.
    """
    path = out / "results.json"
    if not path.is_file():
        return {}
    report = json.loads(path.read_text(encoding="utf-8"))
    if report["selected_threshold"]["threshold"] != threshold:
        raise ValueError("Le rapport dev et threshold.json utilisent des seuils différents.")
    return report


def micro_partial(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Extrait la ligne micro en mode partiel d'une évaluation."""
    return next(row for row in rows if row["mode"] == "partial" and row["type"] == "micro")


def evaluate_documents(
    documents: Sequence[CorpusDocument], config_name: str, threshold: float
) -> tuple[list[dict[str, Any]], list[list[Detection]]]:
    """Détecte chaque document au seuil fourni et renvoie métriques et prédictions.

    Chaque seuil repasse par detect : filtrer les sorties d'un seul passage
    changerait la fusion ou la propagation et fausserait la comparaison.
    """
    config = replace(PRESETS[config_name], threshold=threshold)
    evaluation = Evaluation()
    predictions = []
    for document in documents:
        detected = detect(document.text, config)
        predictions.append(detected)
        evaluation.add_document(document.entities, detected)
    return evaluation.rows(), predictions


def dev_errors(
    documents: Sequence[CorpusDocument], predictions: Sequence[Sequence[Detection]]
) -> list[dict[str, Any]]:
    """Exporte les FN et FP exacts de dev, avec trente caractères de chaque côté.

    Un décalage de borne produit un FN et un FP, même si le partiel est correct.
    Le contrôle du split empêche tout export accidentel du jeu test.
    """
    if len(documents) != len(predictions) or any(document.split != "dev" for document in documents):
        raise ValueError("Les erreurs sont réservées aux documents dev appariés.")
    errors = []
    for document, detected in zip(documents, predictions, strict=True):
        references = evaluated_references(document.entities)
        detected = evaluated_predictions(detected)
        pairs = match_entities(references, detected, "exact")
        matched_references = {reference_index for reference_index, _ in pairs}
        matched_predictions = {prediction_index for _, prediction_index in pairs}
        for nature, entities, matched in (
            ("FN", references, matched_references),
            ("FP", detected, matched_predictions),
        ):
            for index, entity in enumerate(entities):
                if index in matched:
                    continue
                kind = entity.type if nature == "FN" else entity.entity_type
                errors.append(
                    {
                        "document_id": document.id,
                        "type": kind.value,
                        "text": document.text[entity.start : entity.end],
                        "context_before": document.text[max(0, entity.start - 30) : entity.start],
                        "context_after": document.text[entity.end : entity.end + 30],
                        "nature": nature,
                    }
                )
    return errors


def available_configs(requested: Sequence[str]) -> tuple[list[str], list[str]]:
    """Retient les configurations disponibles ; l'option absente est documentée.

    Aucun chargement de modèle distant n'est tenté : le module local doit exister
    et les appels éventuels sont exécutés avec le mode hors ligne forcé.
    """
    unknown = set(requested) - PRESETS.keys()
    if unknown:
        raise ValueError(f"Configurations inconnues : {', '.join(sorted(unknown))}")
    names = list(dict.fromkeys(requested))
    notes = []
    if "hybrid_camembert" in names and (
        find_spec("transformers") is None or find_spec("huisclos.detection.camembert") is None
    ):
        names.remove("hybrid_camembert")
        notes.append("hybrid_camembert omitted: local recognizer or transformers is unavailable.")
    return names, notes


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


def write_summary(path: Path, rows: Sequence[dict[str, Any]], notes: Sequence[str]) -> None:
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
    lines.extend(["", *notes, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_evaluation(
    split: str = "dev",
    configs: Sequence[str] | None = None,
    out: Path = ROOT / "results",
    corpus_dir: Path = ROOT / "corpus",
) -> dict[str, Any]:
    """Évalue le split demandé ; seul dev choisit un seuil et exporte les erreurs.

    En mode test, le seuil et les mesures dev sont conservés sans nouveau balayage.
    En mode all, dev choisit d'abord le seuil, puis test l'utilise sans l'ajuster.
    """
    if split not in {"dev", "test", "all"}:
        raise ValueError("Split attendu : dev, test ou all.")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    names, notes = available_configs(list(PRESETS) if configs is None else configs)
    if not names:
        raise ValueError("Aucune configuration disponible.")
    out = Path(out)
    threshold_path = out / "threshold.json"
    if split == "test" and not threshold_path.is_file():
        raise ValueError("Évaluer dev avant test : threshold.json est absent.")
    out.mkdir(parents=True, exist_ok=True)
    splits = ("dev", "test") if split == "all" else (split,)
    paths = [corpus_dir / f"{name}.jsonl" for name in splits]
    threshold = default_threshold(threshold_path) if split == "test" else THRESHOLDS[0]
    previous = saved_dev_report(out, threshold) if split == "test" else {}
    sweep: list[dict[str, Any]] = previous.get("threshold_sweep", [])
    rows: list[dict[str, Any]] = [
        row for row in previous.get("metrics_by_type", []) if row["split"] == "dev"
    ]
    previous_metadata = previous.get("metadata", {})
    document_counts = {
        name: count
        for name, count in previous_metadata.get("document_counts", {}).items()
        if name == "dev"
    }
    for split_name, path in zip(splits, paths, strict=True):
        documents = load_corpus(path)
        if not documents or any(document.split != split_name for document in documents):
            raise ValueError(f"Corpus vide ou split incohérent : {path.name}")
        document_counts[split_name] = len(documents)
        hybrid_cache = {}
        if split_name == "dev":
            for candidate in THRESHOLDS:
                result = evaluate_documents(documents, "hybrid", candidate)
                hybrid_cache[candidate] = result
                sweep.append({"threshold": candidate, **micro_partial(result[0])})
            threshold = choose_threshold(sweep)
            write_json(threshold_path, {"threshold": threshold, "criterion": CRITERION})
            write_csv(out / "threshold_sweep.csv", SWEEP_COLUMNS, sweep)
            write_csv(
                out / "errors_dev.csv",
                ERROR_COLUMNS,
                dev_errors(documents, hybrid_cache[threshold][1]),
            )
        for name in names.copy():
            try:
                result = (
                    hybrid_cache[threshold]
                    if name == "hybrid" and hybrid_cache
                    else (evaluate_documents(documents, name, threshold))
                )
            except (ImportError, OSError, RuntimeError) as error:
                if name != "hybrid_camembert":
                    raise
                names.remove(name)
                notes.append(
                    f"hybrid_camembert omitted: local model unavailable ({type(error).__name__})."
                )
                rows = [row for row in rows if row["config"] != name]
                continue
            rows.extend(
                {"split": split_name, "config": name, "threshold": threshold, **row}
                for row in result[0]
            )
    if not (out / "threshold_sweep.csv").exists():
        write_csv(out / "threshold_sweep.csv", SWEEP_COLUMNS, [])
    write_csv(out / "metrics_by_type.csv", METRIC_COLUMNS, rows)
    run_metadata = metadata(paths, names, threshold)
    run_metadata["corpus_sha256"] = {
        name: digest
        for name, digest in previous_metadata.get("corpus_sha256", {}).items()
        if name == "dev.jsonl"
    } | run_metadata["corpus_sha256"]
    run_metadata["document_counts"] = document_counts
    notes = list(dict.fromkeys([*previous.get("notes", []), *notes]))
    report = {
        "metadata": run_metadata,
        "notes": notes,
        "metrics_by_type": rows,
        "threshold_sweep": sweep,
        "selected_threshold": {"threshold": threshold, "criterion": CRITERION},
    }
    write_json(out / "results.json", report)
    write_summary(out / "summary.md", rows, notes)
    return report
