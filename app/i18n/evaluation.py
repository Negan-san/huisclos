"""Textes anglais et français de la page des résultats précalculés.

Entrées : aucune ; les valeurs mesurées sont injectées par la page.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.
Place dans le pipeline : présentation de l'évaluation, sans calcul de détection.
"""

EN: dict[str, str] = {
    "evaluation.title": "Evaluation",
    "evaluation.empty": (
        "No evaluation results are available. Add the precomputed evaluation files to the "
        "results folder to display this page."
    ),
    "evaluation.invalid": (
        "The evaluation files are incomplete or unreadable. Replace them with a complete set "
        "of precomputed results."
    ),
    "evaluation.loading": "Loading precomputed evaluation results...",
    "evaluation.split": "Evaluation split",
    "evaluation.lead": (
        "On {split}, hybrid achieves {recall} recall and a {leak_rate} leak rate at the "
        "selected threshold of {threshold} (partial matching, micro averages)."
    ),
    "evaluation.table": "Configuration comparison",
    "evaluation.matching": (
        "Partial matching, micro averages. Leak rate is the share of reference characters left"
        " uncovered; exposed entities have at least one uncovered character. A partial match "
        "can still expose an entity."
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
    "evaluation.recall_label": "{config}: {recall}",
    "evaluation.recall_alt": (
        "Grouped bars show partial recall by entity type and configuration. Each bar has a "
        "configuration name and percentage label."
    ),
    "evaluation.sweep_chart": "Threshold sweep on dev (hybrid)",
    "evaluation.sweep_alt": (
        "Lines show precision, recall, F1 and F2 for hybrid on dev. Line patterns and the "
        "legend identify metrics. The labelled vertical rule marks the selected threshold."
    ),
    "evaluation.choice_title": "How the threshold was chosen",
    "evaluation.choice": (
        "Missing a name can breach professional secrecy; masking an extra word is an "
        "inconvenience. F2 gives recall more weight than precision. The threshold maximising "
        "hybrid F2 on dev was selected, with the lowest threshold used to break ties. The test"
        " split is reserved for a single measurement per evaluation gate, after the choice is "
        "fixed. This page only reads saved results and never runs an evaluation."
    ),
    "evaluation.limits_title": "Limits of this evaluation",
    "evaluation.limits": (
        "This small, fictional corpus was generated with an LLM and then reviewed by humans. "
        "The same authors wrote the corpus and the detection rules, which can bias the "
        "results. Figures are indicative and do not establish performance on real client "
        "files. For {split}, document count: {documents}; reference entity count: {entities}. "
        "Human review remains necessary. Pseudonymisation is not anonymisation."
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

FR: dict[str, str] = {
    "evaluation.title": "Évaluation",
    "evaluation.empty": (
        "Aucun résultat d'évaluation disponible. Ajoutez les fichiers de résultats précalculés"
        " au dossier results pour afficher cette page."
    ),
    "evaluation.invalid": (
        "Les fichiers d'évaluation sont incomplets ou illisibles. Remplacez-les par un "
        "ensemble complet de résultats précalculés."
    ),
    "evaluation.loading": "Chargement des résultats d'évaluation précalculés...",
    "evaluation.split": "Jeu d'évaluation",
    "evaluation.lead": (
        "Sur {split}, hybrid atteint un rappel de {recall} et un taux de fuite de {leak_rate} "
        "au seuil retenu de {threshold} (appariement partiel, moyennes micro)."
    ),
    "evaluation.table": "Comparaison des configurations",
    "evaluation.matching": (
        "Appariement partiel, moyennes micro. Le taux de fuite est la part des caractères de "
        "référence non couverts ; une entité exposée comporte au moins un caractère non "
        "couvert. Un appariement partiel peut encore exposer une entité."
    ),
    "evaluation.config": "Configuration",
    "evaluation.precision": "Précision",
    "evaluation.recall": "Rappel",
    "evaluation.f1": "F1",
    "evaluation.f2": "F2",
    "evaluation.leak_rate": "Taux de fuite",
    "evaluation.exposed_entities": "Entités exposées",
    "evaluation.type": "Type d'entité",
    "evaluation.score": "Score",
    "evaluation.metric": "Mesure",
    "evaluation.threshold": "Seuil",
    "evaluation.selected": "Seuil retenu : {threshold}",
    "evaluation.recall_chart": "Rappel par type d'entité",
    "evaluation.recall_label": "{config} : {recall}",
    "evaluation.recall_alt": (
        "Les barres groupées montrent le rappel partiel par type d'entité et par "
        "configuration. Chaque barre indique le nom de la configuration et un pourcentage."
    ),
    "evaluation.sweep_chart": "Variation du seuil sur dev (hybrid)",
    "evaluation.sweep_alt": (
        "Les courbes montrent la précision, le rappel, F1 et F2 pour hybrid sur dev. Les "
        "styles de ligne et la légende identifient les mesures. La ligne verticale légendée "
        "marque le seuil retenu."
    ),
    "evaluation.choice_title": "Choix du seuil",
    "evaluation.choice": (
        "Oublier un nom peut violer le secret professionnel ; masquer un mot de trop est une "
        "gêne. F2 donne plus de poids au rappel qu'à la précision. Le seuil maximisant F2 pour"
        " hybrid sur dev a été retenu ; en cas d'égalité, le seuil le plus bas est choisi. Le "
        "jeu test est réservé à une seule mesure par gate d'évaluation, après fixation du "
        "choix. Cette page lit uniquement les résultats enregistrés et ne lance jamais "
        "d'évaluation."
    ),
    "evaluation.limits_title": "Limites de cette évaluation",
    "evaluation.limits": (
        "Ce petit corpus fictif a été généré avec un LLM puis relu par des humains. Les mêmes "
        "auteurs ont rédigé le corpus et les règles de détection, ce qui peut biaiser les "
        "résultats. Les chiffres sont indicatifs et ne démontrent pas les performances sur de "
        "vrais dossiers clients. Pour {split}, nombre de documents : {documents} ; nombre "
        "d'entités de référence : {entities}. La revue humaine reste nécessaire. La "
        "pseudonymisation n'est pas une anonymisation."
    ),
    "evaluation.metadata": "Métadonnées de l'évaluation",
    "evaluation.date": "Date",
    "evaluation.commit": "Commit",
    "evaluation.documents": "Documents",
    "evaluation.entities": "Entités de référence",
    "evaluation.versions": "Versions",
    "evaluation.not_recorded": "Non enregistré dans les résultats",
    "evaluation.documents_missing": (
        "Les résultats enregistrés n'indiquent pas le nombre de documents. Cette page n'ouvre "
        "pas le corpus."
    ),
    "evaluation.metadata_line": "{label} : {value}",
    "evaluation.version_line": "{name} : {version}",
    "evaluation.downloads": "Télécharger les fichiers CSV",
    "evaluation.download": "Télécharger {filename}",
}
