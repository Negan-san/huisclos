"""Textes anglais et français de l'étape Review.

Entrées : valeurs à insérer dans les messages de cette étape.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.workflow.
Place dans le pipeline : affichage local du parcours de pseudonymisation.
"""

EN: dict[str, str] = {
    "review.title": "Review detections",
    "review.empty": "Nothing to review yet. Import a text and run the detection first.",
    "review.intro": (
        "You decide what is masked. Uncheck a row to keep a value in clear, change its type if"
        " it is wrong, and add any value the detection missed. A forgotten name is a breach of"
        " professional secrecy, a name masked by mistake is only a nuisance."
    ),
    "review.summary": "{count} detections are ready for review, grouped into {groups} entities.",
    "review.counts.heading": "By type",
    "review.counts.types": "Types",
    "review.counts.low": "Low confidence",
    "review.counts.low.help": "Occurrences scored below {score}. Check them first.",
    "review.counts.masked": "Masked occurrences",
    "review.counts.rejected": "Rejected occurrences",
    "review.counts.groups": "Entities",
    "review.counts.type": "Type",
    "review.counts.type_masked": "Masked",
    "review.counts.type_rejected": "Rejected",
    "review.text.heading": "Highlighted text",
    "review.text.legend": "Legend",
    "review.table.heading": "Entities",
    "review.table.help": (
        "One row per entity, whatever the number of times it appears. Unchecking Mask rejects "
        "every occurrence; changing the Type applies to all of them."
    ),
    "review.table.nothing": "No entity of the selected types.",
    "review.filter.label": "Show only these types",
    "review.column.mask": "Mask",
    "review.column.mask.help": "Uncheck to keep every occurrence of this entity in clear.",
    "review.column.type.help": "The type sets the token, for example [PERSONNE_1].",
    "review.column.text": "Text",
    "review.column.type": "Type",
    "review.column.occurrences": "Occurrences",
    "review.column.variants": "Variants",
    "review.column.confidence": "Confidence",
    "review.column.source": "Source",
    "review.column.note": "Note",
    "review.variants.more": "+{count} more",
    "review.note.ambiguous": "Check: may refer to another person",
    "review.tag.PERSON": "PERSON",
    "review.tag.ORGANIZATION": "COMPANY",
    "review.tag.ADDRESS": "ADDRESS",
    "review.tag.EMAIL": "EMAIL",
    "review.tag.PHONE": "PHONE",
    "review.tag.IBAN": "IBAN",
    "review.tag.NIR": "NIR",
    "review.tag.SIREN": "SIREN",
    "review.tag.SIRET": "SIRET",
    "review.tag.BIRTH_DATE": "BIRTH DATE",
    "review.tag.CASE_NUMBER": "CASE",
    "review.tag.LOCATION": "PLACE",
    "review.tag.CUSTOM": "OTHER",
    "review.rejected": "REJECTED",
    "review.hover": "{kind}, score {score}, source {source}",
    "review.hover.rejected": "{kind}, score {score}, source {source}, rejected by you",
    "review.manual.heading": "Add a value the detection missed",
    "review.manual.text": "Value to mask",
    "review.manual.type": "Type of this value",
    "review.manual.custom": "Other identifier",
    "review.manual.button": "Add and mask everywhere",
    "review.manual.empty": "Type the value to mask first.",
    "review.manual.none": (
        "This value does not appear in the text. Check the spelling; upper and lower case and "
        "accents are ignored."
    ),
    "review.manual.covered": (
        "All {covered} occurrences are already inside a masked value, so nothing was added."
    ),
    "review.manual.added": "Added {count} occurrences. They are masked everywhere in the text.",
    "review.manual.added_covered": (
        "Added {count} occurrences. {covered} more were already inside a masked value."
    ),
    "review.nothing_masked": (
        "No value is masked, so the pseudonymized text would be identical to the original. "
        "Check at least one row or add a value."
    ),
    "review.pseudonymize": "Pseudonymize",
    "review.pseudonymize.spinner": "Replacing the masked values with tokens.",
    "review.pseudonymize.note": (
        "The correspondence table stays on this computer. Only the pseudonymized text is meant"
        " to be sent to a language model."
    ),
    "review.error.pseudonymize": (
        "The text could not be pseudonymized because two detections overlap. Go back to Import"
        " and run the detection again."
    ),
    "review.error.substitution": (
        "The text could not be pseudonymized: a value was not replaced by the expected token."
        " Nothing was produced and nothing was sent. Go back to Import and run the detection"
        " again."
    ),
    "review.back": "Back to Import",
}

FR: dict[str, str] = {
    "review.title": "Vérifier les détections",
    "review.empty": (
        "Rien à vérifier pour le moment. Importez un texte et lancez d'abord la détection."
    ),
    "review.intro": (
        "Vous décidez des valeurs masquées. Décochez une ligne pour garder une valeur en "
        "clair, corrigez son type si nécessaire et ajoutez les valeurs oubliées. Un nom oublié"
        " viole le secret professionnel ; un nom masqué par erreur est une gêne."
    ),
    "review.summary": "{count} détections à vérifier, regroupées en {groups} entités.",
    "review.counts.heading": "Par type",
    "review.counts.types": "Types",
    "review.counts.low": "Faible confiance",
    "review.counts.low.help": (
        "Occurrences dont le score est inférieur à {score}. À vérifier en premier."
    ),
    "review.counts.masked": "Occurrences masquées",
    "review.counts.rejected": "Occurrences rejetées",
    "review.counts.groups": "Entités",
    "review.counts.type": "Type",
    "review.counts.type_masked": "Masquées",
    "review.counts.type_rejected": "Rejetées",
    "review.text.heading": "Texte surligné",
    "review.text.legend": "Légende",
    "review.table.heading": "Entités",
    "review.table.help": (
        "Une ligne par entité, quel que soit son nombre d'apparitions. Décocher Masquer "
        "rejette toutes les occurrences ; modifier le Type s'applique à toutes."
    ),
    "review.table.nothing": "Aucune entité des types sélectionnés.",
    "review.filter.label": "Afficher uniquement ces types",
    "review.column.mask": "Masquer",
    "review.column.mask.help": (
        "Décochez pour laisser en clair toutes les occurrences de cette entité."
    ),
    "review.column.type.help": "Le type détermine le jeton, par exemple [PERSONNE_1].",
    "review.column.text": "Texte",
    "review.column.type": "Type",
    "review.column.occurrences": "Occurrences",
    "review.column.variants": "Variantes",
    "review.column.confidence": "Confiance",
    "review.column.source": "Source",
    "review.column.note": "Note",
    "review.variants.more": "+{count} autres",
    "review.note.ambiguous": "À vérifier : peut désigner une autre personne",
    "review.tag.PERSON": "PERSONNE",
    "review.tag.ORGANIZATION": "SOCIÉTÉ",
    "review.tag.ADDRESS": "ADRESSE",
    "review.tag.EMAIL": "COURRIEL",
    "review.tag.PHONE": "TÉLÉPHONE",
    "review.tag.IBAN": "IBAN",
    "review.tag.NIR": "NIR",
    "review.tag.SIREN": "SIREN",
    "review.tag.SIRET": "SIRET",
    "review.tag.BIRTH_DATE": "DATE DE NAISSANCE",
    "review.tag.CASE_NUMBER": "DOSSIER",
    "review.tag.LOCATION": "LIEU",
    "review.tag.CUSTOM": "AUTRE",
    "review.rejected": "REJETÉE",
    "review.hover": "{kind}, score {score}, source {source}",
    "review.hover.rejected": "{kind}, score {score}, source {source}, rejetée par vous",
    "review.manual.heading": "Ajouter une valeur oubliée par la détection",
    "review.manual.text": "Valeur à masquer",
    "review.manual.type": "Type de cette valeur",
    "review.manual.custom": "Autre identifiant",
    "review.manual.button": "Ajouter et masquer partout",
    "review.manual.empty": "Saisissez d'abord la valeur à masquer.",
    "review.manual.none": (
        "Cette valeur n'apparaît pas dans le texte. Vérifiez l'orthographe ; la casse et les "
        "accents sont ignorés."
    ),
    "review.manual.covered": (
        "Les {covered} occurrences sont déjà comprises dans une valeur masquée ; aucun ajout."
    ),
    "review.manual.added": (
        "{count} occurrences ajoutées. Elles sont masquées partout dans le texte."
    ),
    "review.manual.added_covered": (
        "{count} occurrences ajoutées. {covered} autres étaient déjà comprises dans une valeur"
        " masquée."
    ),
    "review.nothing_masked": (
        "Aucune valeur n'est masquée ; le texte pseudonymisé serait identique à l'original. "
        "Cochez au moins une ligne ou ajoutez une valeur."
    ),
    "review.pseudonymize": "Pseudonymiser",
    "review.pseudonymize.spinner": "Remplacement des valeurs masquées par des jetons.",
    "review.pseudonymize.note": (
        "La table de correspondance reste sur cet ordinateur. Seul le texte pseudonymisé est "
        "destiné à un modèle de langue."
    ),
    "review.error.pseudonymize": (
        "Le texte n'a pas pu être pseudonymisé car deux détections se chevauchent. Revenez à "
        "Importer et relancez la détection."
    ),
    "review.error.substitution": (
        "Le texte n'a pas pu être pseudonymisé : une valeur n'a pas été remplacée par le jeton "
        "attendu. Aucun texte n'a été produit ni envoyé. Revenez à Importer et relancez la "
        "détection."
    ),
    "review.back": "Retour à Importer",
}
