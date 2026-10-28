"""Textes anglais et français de la page des résultats précalculés.

Entrées : aucune ; les valeurs mesurées sont injectées par la page.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.
Place dans le pipeline : présentation de l'évaluation, sans calcul de détection.
"""

EN: dict[str, str] = {
    "evaluation.title": "Evaluation",
    "evaluation.languages": (
        "All measures on this page are historical measures on French documents (gate "
        "G7 and earlier). Post-G7 dev comparisons, including English, are archived "
        "separately and described in docs/LOCAL_MODELS.md. The historical G8 blind results "
        "(code e3d13bd) and the single G8R2 resume of the French challenge are reported in "
        "the README; English remains experimental. Languages are never averaged together. "
        "The interface language does not change any measure."
    ),
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
    "evaluation.challenge_note": (
        "The challenge split was written blind after the detection rules were frozen. "
        "It uses the threshold selected on dev, without tuning on challenge."
    ),
    "evaluation.intervals": "95% bootstrap intervals",
    "evaluation.intervals_note": (
        "Documents were resampled with replacement 2,000 times (fixed seed 45). "
        "The bounds are the 2.5th and 97.5th percentiles of recomputed partial micro ratios, "
        "at a fixed threshold. Undefined ratios are zero. With one document, intervals "
        "collapse. These intervals do not account for corpus bias or threshold selection."
    ),
    "evaluation.intervals_alt": (
        "Each labelled row shows the saved 95% interval as a horizontal line and the point "
        "estimate as a dot. The table provides both bounds and the estimate in text."
    ),
    "evaluation.label": "Configuration / metric",
    "evaluation.estimate": "Point estimate",
    "evaluation.lower": "Lower bound (2.5%)",
    "evaluation.upper": "Upper bound (97.5%)",
    "evaluation.comparison": "Before/after comparison",
    "evaluation.comparison_note": (
        "Delta = current minus reference; ratios are shown as percentages and their deltas "
        "in percentage points. Exposed entities are counts. Missing intervals or "
        "configurations are marked explicitly. Marginal intervals do not establish "
        "statistical significance for the delta."
    ),
    "evaluation.comparison_source": (
        "{side}: commit {commit}, threshold {threshold}, documents {documents}."
    ),
    "evaluation.reference": "Reference",
    "evaluation.current": "Current",
    "evaluation.reference_interval": "Reference 95% interval",
    "evaluation.current_interval": "Current 95% interval",
    "evaluation.delta": "Delta (pp / count)",
    "evaluation.comparison_threshold_different": "The selected thresholds differ between reports.",
    "evaluation.comparison_threshold_missing": "A selected threshold is not recorded.",
    "evaluation.comparison_corpus_sha256_different": (
        "The corpus fingerprints differ. These figures do not compare the same document set."
    ),
    "evaluation.comparison_corpus_sha256_missing": (
        "A corpus fingerprint is missing. The document sets cannot be checked for equality."
    ),
    "evaluation.lead": (
        "On {split}, hybrid achieves {recall} recall and a {leak_rate} leak rate at the "
        "selected threshold of {threshold} (partial matching, micro averages)."
    ),
    "evaluation.kpis": "Hybrid configuration, selected threshold {threshold}.",
    "evaluation.table": "Configuration comparison",
    "evaluation.matching": (
        "Partial matching, micro averages. Leak rate is the share of reference characters left"
        " uncovered; exposed entities have no covered character. A partial match "
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
    "evaluation.languages": (
        "Toutes les mesures de cette page sont des mesures historiques sur des "
        "documents fran\u00e7ais (gate G7 et avant). Les comparaisons dev apr\u00e8s G7, dont "
        "l'anglais, sont archiv\u00e9es s\u00e9par\u00e9ment et d\u00e9crites dans "
        "docs/LOCAL_MODELS.md. Les r\u00e9sultats aveugles historiques de G8 (code "
        "e3d13bd) et la reprise unique du challenge fran\u00e7ais G8R2 figurent dans le "
        "README ; l'anglais reste exp\u00e9rimental. Les langues ne sont jamais "
        "moyenn\u00e9es ensemble. La langue de l'interface ne change aucune mesure."
    ),
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
    "evaluation.challenge_note": (
        "Le jeu challenge a été rédigé à l'aveugle après le gel des règles de détection. "
        "Il utilise le seuil choisi sur dev, sans ajustement sur challenge."
    ),
    "evaluation.intervals": "Intervalles bootstrap à 95 %",
    "evaluation.intervals_note": (
        "Les documents ont été rééchantillonnés avec remise 2 000 fois (graine fixe 45). "
        "Les bornes sont les percentiles 2,5 et 97,5 des ratios micro partiels recalculés, "
        "au seuil fixé. Les ratios indéfinis valent zéro. Avec un document, les intervalles "
        "se réduisent à un point. Ils ne prennent pas en compte le biais du corpus "
        "ni le choix du seuil."
    ),
    "evaluation.intervals_alt": (
        "Chaque ligne libellée montre l'intervalle à 95 % enregistré par un trait horizontal "
        "et la valeur ponctuelle par un point. Le tableau écrit les deux bornes et la valeur."
    ),
    "evaluation.label": "Configuration / mesure",
    "evaluation.estimate": "Valeur ponctuelle",
    "evaluation.lower": "Borne basse (2,5 %)",
    "evaluation.upper": "Borne haute (97,5 %)",
    "evaluation.comparison": "Comparaison avant/après",
    "evaluation.comparison_note": (
        "Écart = actuel moins référence ; les ratios sont en pourcentages et leurs écarts "
        "en points de pourcentage. Les entités exposées sont des comptes. Les intervalles "
        "et configurations absents sont signalés. Les intervalles marginaux ne démontrent "
        "pas la significativité statistique de l'écart."
    ),
    "evaluation.comparison_source": (
        "{side} : commit {commit}, seuil {threshold}, documents {documents}."
    ),
    "evaluation.reference": "Référence",
    "evaluation.current": "Actuel",
    "evaluation.reference_interval": "Intervalle référence à 95 %",
    "evaluation.current_interval": "Intervalle actuel à 95 %",
    "evaluation.delta": "Écart (points / compte)",
    "evaluation.comparison_threshold_different": "Les seuils retenus diffèrent entre les rapports.",
    "evaluation.comparison_threshold_missing": "Un seuil retenu n'est pas enregistré.",
    "evaluation.comparison_corpus_sha256_different": (
        "Les empreintes du corpus diffèrent. Ces chiffres ne comparent pas "
        "le même jeu de documents."
    ),
    "evaluation.comparison_corpus_sha256_missing": (
        "Une empreinte du corpus manque. L'identité des jeux de documents "
        "ne peut pas être vérifiée."
    ),
    "evaluation.lead": (
        "Sur {split}, hybrid atteint un rappel de {recall} et un taux de fuite de {leak_rate} "
        "au seuil retenu de {threshold} (appariement partiel, moyennes micro)."
    ),
    "evaluation.kpis": "Configuration hybrid, seuil retenu {threshold}.",
    "evaluation.table": "Comparaison des configurations",
    "evaluation.matching": (
        "Appariement partiel, moyennes micro. Le taux de fuite est la part des caractères de "
        "référence non couverts ; une entité exposée n'a aucun caractère couvert. "
        "Un appariement partiel peut encore exposer une entité."
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
