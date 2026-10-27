"""Textes anglais de la page des résultats précalculés.

Entrées : aucune ; les valeurs mesurées sont injectées par la page.
Sorties : dictionnaire EN fusionné par app.i18n.
Place dans le pipeline : présentation de l'évaluation, sans calcul de détection.
"""

EN: dict[str, str] = {
    "evaluation.title": "Evaluation",
    "evaluation.empty": (
        "No evaluation results are available. Add the precomputed evaluation files "
        "to the results folder to display this page."
    ),
    "evaluation.invalid": (
        "The evaluation files are incomplete or unreadable. "
        "Replace them with a complete set of precomputed results."
    ),
    "evaluation.loading": "Loading precomputed evaluation results...",
    "evaluation.split": "Evaluation split",
    "evaluation.lead": (
        "On {split}, hybrid achieves {recall} recall and a {leak_rate} leak rate "
        "at the selected threshold of {threshold} (partial matching, micro averages)."
    ),
    "evaluation.table": "Configuration comparison",
    "evaluation.matching": (
        "Partial matching, micro averages. Leak rate is the share of reference "
        "characters left uncovered; exposed entities have at least one uncovered "
        "character. A partial match can still expose an entity."
    ),
    "evaluation.config": "Configuration",
    "evaluation.precision": "Precision",
    "evaluation.recall": "Recall",
    "evaluation.f1": "F1",
    "evaluation.f2": "F2",
    "evaluation.leak_rate": "Leak rate",
    "evaluation.exposed_entities": "Exposed entities",
    "evaluation.type": "Entity type",
    "evaluation.score": "Score",
    "evaluation.metric": "Metric",
    "evaluation.threshold": "Threshold",
    "evaluation.selected": "Selected threshold: {threshold}",
    "evaluation.recall_chart": "Recall by entity type",
    "evaluation.recall_alt": (
        "Grouped bars show partial recall by entity type and configuration. "
        "Each bar has a percentage label; the legend identifies configurations."
    ),
    "evaluation.sweep_chart": "Threshold sweep on dev (hybrid)",
    "evaluation.sweep_alt": (
        "Lines show precision, recall, F1 and F2 for hybrid on dev. "
        "Line patterns and the legend identify metrics. "
        "The labelled vertical rule marks the selected threshold."
    ),
    "evaluation.choice_title": "How the threshold was chosen",
    "evaluation.choice": (
        "Missing a name can breach professional secrecy; masking an extra word "
        "is an inconvenience. F2 gives recall more weight than precision. "
        "The threshold maximising hybrid F2 on dev was selected, with the lowest "
        "threshold used to break ties. The test split is reserved for a single "
        "measurement per evaluation gate, after the choice is fixed. "
        "This page only reads saved results and never runs an evaluation."
    ),
    "evaluation.limits_title": "Limits of this evaluation",
    "evaluation.limits": (
        "This small, fictional corpus was generated with an LLM and then reviewed "
        "by humans. The same authors wrote the corpus and the detection rules, "
        "which can bias the results. Figures are indicative and do not establish "
        "performance on real client files. For {split}, document count: {documents}; "
        "reference entity count: {entities}. Human review remains necessary. "
        "Pseudonymisation is not anonymisation."
    ),
    "evaluation.metadata": "Evaluation metadata",
    "evaluation.date": "Date",
    "evaluation.commit": "Commit",
    "evaluation.documents": "Documents",
    "evaluation.entities": "Reference entities",
    "evaluation.versions": "Versions",
    "evaluation.not_recorded": "Not recorded in results",
    "evaluation.documents_missing": (
        "The saved results do not record the document count. The corpus is not opened by this page."
    ),
    "evaluation.metadata_line": "{label}: {value}",
    "evaluation.version_line": "{name}: {version}",
    "evaluation.downloads": "Download CSV files",
    "evaluation.download": "Download {filename}",
}
