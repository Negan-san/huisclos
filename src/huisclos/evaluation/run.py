"""Compare les configurations sur les corpus fictifs sans modifier la détection.

Entrées : split demandé, configurations et dossier de sortie ; seuil choisi sur dev.
Sorties : tableaux déterministes, rapport anglais et erreurs réservées à dev.
Place dans le pipeline : orchestration locale de detect, du corpus et des métriques.
"""

import json
import os
from collections.abc import Sequence
from dataclasses import replace
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from huisclos.config import PRESETS, default_threshold
from huisclos.detection.pipeline import detect
from huisclos.evaluation.corpus import ChallengeDocument as ChallengeDocument
from huisclos.evaluation.corpus import CorpusDocument, load_corpus
from huisclos.evaluation.corpus import load_challenge_corpus as load_challenge_corpus
from huisclos.evaluation.errors import dev_errors
from huisclos.evaluation.intervals import BOOTSTRAP_METHOD, bootstrap_intervals
from huisclos.evaluation.metrics import Evaluation
from huisclos.evaluation.reports import metadata, write_csv, write_json, write_summary
from huisclos.models import Detection

ROOT = Path(__file__).resolve().parents[3]
THRESHOLDS = tuple(value / 100 for value in range(30, 96, 5))
CRITERION = "max F2 (partial, micro) on dev"
METRIC_COLUMNS = tuple(
    "split config threshold mode type tp fp fn precision recall f1 f2 leak_rate".split()
)
SWEEP_COLUMNS = ("threshold", "precision", "recall", "f1", "f2", "leak_rate", "exposed_entities")
ERROR_COLUMNS = (
    "document_id",
    "type",
    "text",
    "context_before",
    "context_after",
    "nature",
    "category",
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


def run_evaluation(
    split: str = "dev",
    configs: Sequence[str] | None = None,
    out: Path = ROOT / "results",
    corpus_dir: Path = ROOT / "corpus",
) -> dict[str, Any]:
    """Évalue le split demandé ; seul dev choisit un seuil et exporte les erreurs.

    Challenge conserve le seuil et les mesures dev et test sans nouveau balayage.
    En mode all, dev choisit d'abord le seuil, puis test l'utilise sans l'ajuster.
    """
    if split not in {"dev", "test", "challenge", "all"}:
        raise ValueError("Split attendu : dev, test, challenge ou all.")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    names, notes = available_configs(list(PRESETS) if configs is None else configs)
    if not names:
        raise ValueError("Aucune configuration disponible.")
    out = Path(out)
    threshold_path = out / "threshold.json"
    reserved = split in {"test", "challenge"}
    if reserved and not threshold_path.is_file():
        raise ValueError("Évaluer dev avant test : threshold.json est absent.")
    out.mkdir(parents=True, exist_ok=True)
    splits = ("dev", "test") if split == "all" else (split,)
    paths = [corpus_dir / f"{name}.jsonl" for name in splits]
    threshold = default_threshold(threshold_path) if reserved else THRESHOLDS[0]
    previous = saved_dev_report(out, threshold) if reserved else {}
    preserved_splits = {"dev", "test"} if split == "challenge" else {"dev"}
    sweep: list[dict[str, Any]] = previous.get("threshold_sweep", [])
    rows: list[dict[str, Any]] = [
        row for row in previous.get("metrics_by_type", []) if row["split"] in preserved_splits
    ]
    intervals = [
        row for row in previous.get("bootstrap_intervals", []) if row["split"] in preserved_splits
    ]
    error_counts = previous.get("dev_error_categories", {}) if reserved else {}
    previous_metadata = previous.get("metadata", {})
    document_counts = {
        name: count
        for name, count in previous_metadata.get("document_counts", {}).items()
        if name in preserved_splits
    }
    for split_name, path in zip(splits, paths, strict=True):
        documents = load_challenge_corpus(path) if split_name == "challenge" else load_corpus(path)
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
            errors = dev_errors(documents, hybrid_cache[threshold][1])
            write_csv(out / "errors_dev.csv", ERROR_COLUMNS, errors)
            error_counts = {
                category: sum(error["category"] == category for error in errors)
                for category in ("missed", "extra", "boundary", "type_confusion")
            }
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
                rows = [
                    row
                    for row in rows
                    if row["config"] != name or (split == "challenge" and row["split"] != split)
                ]
                intervals = [
                    row
                    for row in intervals
                    if row["config"] != name or (split == "challenge" and row["split"] != split)
                ]
                continue
            rows.extend(
                {"split": split_name, "config": name, "threshold": threshold, **row}
                for row in result[0]
            )
            intervals.append(
                {
                    "split": split_name,
                    "config": name,
                    "threshold": threshold,
                    "mode": "partial",
                    "type": "micro",
                    **bootstrap_intervals(documents, result[1]),
                }
            )
    if not (out / "threshold_sweep.csv").exists():
        write_csv(out / "threshold_sweep.csv", SWEEP_COLUMNS, [])
    write_csv(out / "metrics_by_type.csv", METRIC_COLUMNS, rows)
    run_metadata = metadata(paths, names, threshold)
    run_metadata["corpus_sha256"] = {
        name: digest
        for name, digest in previous_metadata.get("corpus_sha256", {}).items()
        if name.removesuffix(".jsonl") in preserved_splits
    } | run_metadata["corpus_sha256"]
    if split == "challenge":
        run_metadata["configurations"] = (
            previous_metadata.get("configurations", {}) | run_metadata["configurations"]
        )
    run_metadata["document_counts"] = document_counts
    notes = list(dict.fromkeys([*previous.get("notes", []), *notes]))
    report = {
        "metadata": run_metadata,
        "notes": notes,
        "metrics_by_type": rows,
        "bootstrap_method": BOOTSTRAP_METHOD,
        "bootstrap_intervals": intervals,
        "dev_error_categories": error_counts,
        "threshold_sweep": sweep,
        "selected_threshold": {"threshold": threshold, "criterion": CRITERION},
    }
    write_json(out / "results.json", report)
    write_summary(out / "summary.md", rows, notes, intervals, error_counts)
    return report
