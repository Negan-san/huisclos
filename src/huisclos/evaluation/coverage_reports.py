"""Assemble le rapport de robustesse : métriques historiques, couverture, alertes, intervalles.

Entrées : documents annotés, sorties de chaque profil (positions et types seulement), paires
de profils à comparer et métadonnées de la mesure.
Sorties : robustness.json et robustness.md, séparés de results.json mais au même schéma pour
les sections historiques ; expositions détaillées en CSV pour le seul mode dev.
Place dans le pipeline : appelé par scripts/evaluate_robustness.py, sans nouvelle détection.
"""

from collections.abc import Iterable, Sequence
from dataclasses import astuple, dataclass, field
from pathlib import Path
from typing import Any

from huisclos.evaluation.corpus import CorpusDocument
from huisclos.evaluation.coverage import (
    SCOPES,
    AlertCounts,
    CoverageCounts,
    Span,
    detection_spans,
    document_alerts,
    document_coverage,
    exposure_rows,
    original_position,
    ratio,
    substituted_spans,
    sum_counts,
)
from huisclos.evaluation.intervals import (
    BOOTSTRAP_METHOD,
    bootstrap_intervals,
    defined_interval,
    document_counts,
    draw_indices,
    paired_differences,
)
from huisclos.evaluation.metrics import Evaluation
from huisclos.evaluation.reports import robustness_summary, write_csv, write_json
from huisclos.models import Detection, EntityType, Source

Key = tuple[str, str]
COVERAGE_RATIOS = ("full_coverage_rate", "leaked_character_rate", "non_sensitive_masked_rate")
# Marges d'ingénierie du protocole post-G7 (docs/POST_G7_PROTOCOL.md), pas des seuils juridiques.
PRECISION_MARGIN = 0.02
OVER_MASKING_MARGIN = 0.01
# Tolérance des comparaisons de ratios flottants : 0,99 - 0,02 ne vaut pas exactement 0,97.
TOLERANCE = 1e-12
DETAIL_COLUMNS = (
    "config",
    "document_id",
    "type",
    "exposure",
    "reference_text",
    "visible_text",
    "alerted",
)
COVERAGE_BOOTSTRAP = {
    **{key: value for key, value in BOOTSTRAP_METHOD.items() if key not in {"mode", "type"}},
    "shared_draws": "same document draws for every profile and paired difference",
    "undefined_draws": "draws without denominator are dropped and counted, never set to zero",
}
NOTES = [
    "Stages: detection lists proposals; pseudonymization substitutes every proposal "
    "automatically; final check reports alerts on the pseudonymized text.",
    "Alerts do not mask anything: leakage after the final check equals leakage after "
    "pseudonymization. No stage simulates a reviewer who knows the annotations.",
    "Coverage counts characters replaced by any substitution, whatever the predicted type. "
    "Historical metrics are unchanged and never credit a wrong label.",
    "Full coverage means every character of a reference is masked; one visible character "
    "prevents it. Over-masking counts masked characters outside every annotation.",
    "The eleven historical types form the comparison scope; CUSTOM and LOCATION are separate.",
    "n/a means not applicable (no denominator); it is not a guarantee of zero leakage.",
]


@dataclass(frozen=True)
class ProfileRun:
    """Sorties d'un profil sur tous les documents, replacées dans les textes d'origine.

    predictions : stade detection ; substituted : passages remplacés par la pseudonymisation
    automatique de toutes les propositions ; alerts : alertes du contrôle final, ou None si le
    code mesuré n'en dispose pas ; metadata : code, configuration et modèles réellement utilisés.
    """

    name: str
    threshold: float
    predictions: list[list[Detection]]
    substituted: list[list[Span]]
    alerts: list[list[Span]] | None
    metadata: dict[str, Any] = field(default_factory=dict)


def profile_run(
    name: str, threshold: float, documents: Sequence[CorpusDocument], payload: dict[str, Any]
) -> ProfileRun:
    """Reconstruit les sorties d'un profil depuis la réponse du pilote (positions et types).

    Le texte de chaque détection est relu dans le document : la réponse ne transporte aucune
    valeur. Une réponse incomplète ou des alertes présentes pour une partie des documents
    seulement sont refusées.
    """
    outputs = payload["documents"]
    if len(outputs) != len(documents):
        raise ValueError("La réponse du profil ne couvre pas exactement les documents mesurés.")
    if len({output["alerts"] is None for output in outputs}) > 1:
        raise ValueError("Le contrôle final doit être disponible pour tous les documents ou aucun.")
    predictions, substituted, alerts = [], [], []
    for document, output in zip(documents, outputs, strict=True):
        predictions.append(
            [
                Detection(
                    start,
                    end,
                    EntityType(kind),
                    float(score),
                    Source(source),
                    document.text[start:end],
                )
                for start, end, kind, score, source in output["detections"]
            ]
        )
        substituted.append(substituted_spans(output["occurrences"]))
        if output["alerts"] is not None:
            alerts.append(
                [
                    original_position(output["occurrences"], start, end)
                    for start, end in output["alerts"]
                ]
            )
    has_alerts = bool(outputs) and outputs[0]["alerts"] is not None
    return ProfileRun(
        name,
        threshold,
        predictions,
        substituted,
        alerts if has_alerts else None,
        payload["metadata"],
    )


def stage_masks(run: ProfileRun) -> dict[str, list[list[Span]]]:
    """Renvoie les passages masqués de chaque stade ; le contrôle final garde ceux du stade 2."""
    return {
        "detection": [detection_spans(predicted) for predicted in run.predictions],
        "pseudonymization": run.substituted,
        "final_check": run.substituted,
    }


def coverage_by_document(
    documents: Sequence[CorpusDocument], masks: Sequence[Sequence[Span]], scope: frozenset[str]
) -> list[CoverageCounts]:
    """Mesure la couverture de chaque document pour un stade et un périmètre."""
    return [
        document_coverage(len(document.text), document.entities, masked, scope)
        for document, masked in zip(documents, masks, strict=True)
    ]


def draw_values(
    documents: Sequence[CorpusDocument], run: ProfileRun, draws: Sequence[Sequence[int]]
) -> dict[Key, list[float | None]]:
    """Calcule les mesures appariables sur chaque tirage, depuis les comptes par document.

    Précision et rappel suivent l'appariement partiel micro historique ; un tirage sans
    dénominateur donne None au lieu de zéro, pour ne créer aucune différence artificielle.
    """
    historical = [
        (count.tp, count.fp, count.fn) for count in document_counts(documents, run.predictions)
    ]
    masks = stage_masks(run)
    vectors = {
        stage: [
            astuple(count)
            for count in coverage_by_document(documents, masks[stage], SCOPES["evaluated"])
        ]
        for stage in ("detection", "pseudonymization")
    }
    values: dict[Key, list[float | None]] = {}
    for draw in draws:
        tp, fp, fn = (
            sum(column) for column in zip(*(historical[index] for index in draw), strict=True)
        )
        values.setdefault(("detection", "precision"), []).append(ratio(tp, tp + fp))
        values.setdefault(("detection", "recall"), []).append(ratio(tp, tp + fn))
        for stage, rows in vectors.items():
            totals = (sum(column) for column in zip(*(rows[index] for index in draw), strict=True))
            scores = CoverageCounts(*totals).scores()
            for name in COVERAGE_RATIOS:
                values.setdefault((stage, name), []).append(scores[name])
    return values


def point_estimates(
    documents: Sequence[CorpusDocument], run: ProfileRun
) -> dict[Key, float | None]:
    """Renvoie les mêmes mesures que draw_values, calculées une fois sur tous les documents."""
    return {
        key: samples[0]
        for key, samples in draw_values(documents, run, [range(len(documents))]).items()
    }


def historical_rows(
    documents: Sequence[CorpusDocument], run: ProfileRun, split: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Renvoie les lignes metrics_by_type et l'intervalle historique, au schéma de results.json."""
    evaluation = Evaluation()
    for document, predicted in zip(documents, run.predictions, strict=True):
        evaluation.add_document(document.entities, predicted)
    key = {"split": split, "config": run.name, "threshold": run.threshold}
    interval = {
        **key,
        "mode": "partial",
        "type": "micro",
        **bootstrap_intervals(documents, run.predictions),
    }
    return [{**key, **row} for row in evaluation.rows()], interval


def coverage_rows(documents: Sequence[CorpusDocument], run: ProfileRun) -> list[dict[str, Any]]:
    """Renvoie les totaux de couverture par stade et par périmètre de types."""
    rows = []
    for stage, masks in stage_masks(run).items():
        for scope_name, scope in SCOPES.items():
            total = sum_counts(coverage_by_document(documents, masks, scope), CoverageCounts())
            key = {"config": run.name, "threshold": run.threshold, "stage": stage}
            rows.append(key | {"scope": scope_name} | total.scores())
    return rows


def alert_row(documents: Sequence[CorpusDocument], run: ProfileRun) -> dict[str, Any]:
    """Renvoie les totaux des alertes ; available vaut False pour un code sans contrôle final."""
    base = {
        "config": run.name,
        "threshold": run.threshold,
        "check_threshold": run.metadata.get("final_check_threshold"),
        "available": run.alerts is not None,
    }
    if run.alerts is None:
        return base
    total = sum_counts(
        (
            document_alerts(document.entities, masked, alerts)
            for document, masked, alerts in zip(documents, run.substituted, run.alerts, strict=True)
        ),
        AlertCounts(),
    )
    return base | total.scores()


def criterion(
    candidate: str, reference: str, estimates: dict[str, dict[Key, float | None]]
) -> dict[str, Any]:
    """Applique le critère d'ingénierie du protocole post-G7, jamais un seuil juridique.

    Recommander candidate face à reference exige, après pseudonymisation, une fuite plus
    faible et une couverture complète plus élevée, ainsi qu'une précision partielle au moins
    égale à celle de reference moins deux points et un surmasquage au plus égal à reference
    plus un point. Une égalité de fuite ne suffit pas : sans gain mesuré, pas de recommandation.
    """
    keys = {
        "leak": ("pseudonymization", "leaked_character_rate"),
        "coverage": ("pseudonymization", "full_coverage_rate"),
        "precision": ("detection", "precision"),
        "over_masking": ("pseudonymization", "non_sensitive_masked_rate"),
    }
    pairs = {
        name: (estimates[candidate][key], estimates[reference][key]) for name, key in keys.items()
    }
    base = {
        "candidate": candidate,
        "reference": reference,
        "precision_margin": PRECISION_MARGIN,
        "over_masking_margin": OVER_MASKING_MARGIN,
    }
    if any(value is None for pair in pairs.values() for value in pair):
        return base | {"applicable": False, "met": None}
    (leak, leak_ref), (cov, cov_ref) = pairs["leak"], pairs["coverage"]
    (precision, precision_ref), (over, over_ref) = pairs["precision"], pairs["over_masking"]
    checks = {
        "lower_leakage": leak < leak_ref - TOLERANCE,
        "higher_full_coverage": cov > cov_ref + TOLERANCE,
        "precision_within_margin": precision >= precision_ref - PRECISION_MARGIN - TOLERANCE,
        "over_masking_within_margin": over <= over_ref + OVER_MASKING_MARGIN + TOLERANCE,
    }
    return base | {"applicable": True, **checks, "met": all(checks.values())}


def build_report(
    documents: Sequence[CorpusDocument],
    runs: Sequence[ProfileRun],
    comparisons: Sequence[Sequence[str]],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Assemble le rapport complet ; aucun texte, identifiant de document ni position n'y figure."""
    split = documents[0].split
    draws = draw_indices(len(documents))
    metrics, intervals, coverage, alerts, coverage_intervals = [], [], [], [], []
    values: dict[str, dict[Key, list[float | None]]] = {}
    estimates: dict[str, dict[Key, float | None]] = {}
    for run in runs:
        rows, interval = historical_rows(documents, run, split)
        metrics.extend(rows)
        intervals.append(interval)
        coverage.extend(coverage_rows(documents, run))
        alerts.append(alert_row(documents, run))
        values[run.name] = draw_values(documents, run, draws)
        estimates[run.name] = point_estimates(documents, run)
        coverage_intervals.extend(
            {"config": run.name, "threshold": run.threshold, "stage": stage, "metric": metric}
            | defined_interval(samples)
            for (stage, metric), samples in values[run.name].items()
            if metric in COVERAGE_RATIOS
        )
    report = {
        "report": "robustness",
        "schema_version": 1,
        "metadata": metadata,
        "notes": NOTES,
        "metrics_by_type": metrics,
        "bootstrap_method": BOOTSTRAP_METHOD,
        "bootstrap_intervals": intervals,
        "coverage": coverage,
        "coverage_bootstrap": COVERAGE_BOOTSTRAP,
        "coverage_intervals": coverage_intervals,
        "final_check": alerts,
        "paired_differences": paired_differences(values, estimates, comparisons),
        "engineering_criteria": [
            criterion(first, second, estimates) for first, second in comparisons
        ],
    }
    thresholds = {run.threshold for run in runs}
    if len(thresholds) == 1:
        report["selected_threshold"] = {
            "threshold": thresholds.pop(),
            "criterion": "fixed in the robustness plan before measurement",
        }
    return report


def exposure_details(
    documents: Sequence[CorpusDocument], runs: Sequence[ProfileRun]
) -> list[dict[str, Any]]:
    """Renvoie les expositions détaillées après pseudonymisation, pour le seul mode dev."""
    rows = []
    for run in runs:
        for index, document in enumerate(documents):
            alerts = None if run.alerts is None else run.alerts[index]
            rows.extend(
                {"config": run.name} | row
                for row in exposure_rows(document, run.substituted[index], alerts)
            )
    return rows


def write_report(
    out: Path, report: dict[str, Any], details: Iterable[dict[str, Any]] | None
) -> None:
    """Écrit robustness.json, robustness.md et, en dev seulement, les expositions détaillées."""
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "robustness.json", report)
    (out / "robustness.md").write_text("\n".join(robustness_summary(report)), encoding="utf-8")
    if details is not None:
        write_csv(out / "coverage_exposures_dev.csv", DETAIL_COLUMNS, details)
