"""Textes anglais et français de l'étape Restore.

Entrées : valeurs à insérer dans les messages de cette étape.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.workflow.
Place dans le pipeline : affichage local du parcours de pseudonymisation.
"""

EN: dict[str, str] = {
    "restore.title": "Restore real values",
    "restore.empty": (
        "Nothing to restore yet. Complete the Import and Review steps first, or load a saved "
        "mapping table below."
    ),
    "restore.back": "Back to Import",
    "restore.back_review": "Back to Review",
    "restore.send.heading": "Send to your AI tool",
    "restore.send.intro": (
        "Copy this text into the AI tool of your choice. Names and identifiers are replaced by"
        " tokens such as `[PERSONNE_1]`."
    ),
    "restore.send.literal_tokens": (
        "The input text already contains token-like strings. Check the restored text: they may"
        " be confused with the tokens created by HuisClos."
    ),
    "restore.send.leaves": (
        "What leaves your computer: only the text above. The mapping table stays here."
    ),
    "restore.send.check": (
        "Read the text once more before sending it. A value that was not masked leaves your "
        "computer in clear."
    ),
    "restore.send.counts.heading": "Tokens in this text",
    "restore.send.counts.type": "Type",
    "restore.send.counts.tokens": "Tokens",
    "restore.send.counts.occurrences": "Occurrences",
    "restore.send.instruction.heading": "Recommended instruction",
    "restore.send.instruction.help": (
        "Paste one of these lines with the text, so that the AI tool keeps the tokens unchanged."
    ),
    "restore.send.instruction.fr.label": "In French",
    "restore.send.instruction.fr": (
        "Conserve exactement chaque jeton entre crochets, par exemple [PERSONNE_1], sans le "
        "modifier ni le traduire, et n'en invente aucun."
    ),
    "restore.send.instruction.en.label": "In English",
    "restore.send.instruction.en": (
        "Keep every bracketed token exactly as written, for example [PERSON_1]; do not change,"
        " translate or invent tokens."
    ),
    "restore.answer.heading": "Restore the AI answer",
    "restore.answer.label": "Answer from the AI tool",
    "restore.answer.placeholder": "Paste the answer of the AI tool here.",
    "restore.answer.button": "Restore",
    "restore.answer.empty": "Paste the answer of the AI tool first.",
    "restore.answer.restored_heading": "Restored text",
    "restore.mode.exact": (
        "Exact mode: this is the pseudonymized text itself, so every value comes back as it "
        "was written."
    ),
    "restore.mode.tolerant": (
        "Tolerant mode: each token is replaced by the main form of its value. A variant "
        "written differently in the original, such as a name in capitals, comes back in the "
        "main form."
    ),
    "restore.none_found": "No token was found in this answer, so nothing was restored.",
    "restore.unknown": (
        "Unknown tokens were left unchanged ({count}): {forms}. The AI tool may have invented "
        "them, or the mapping table belongs to another document."
    ),
    "restore.altered": (
        "Altered tokens were recognized and restored ({count}): {pairs}. The AI tool wrote "
        "them differently from the original. Check these places."
    ),
    "restore.altered.pair": "{found} read as {token}",
    "restore.missing": "Tokens of the table not found in the answer: {tokens}.",
    "restore.table.heading": "Use a saved mapping table (optional)",
    "restore.table.help": (
        "To restore an answer received later, upload the .mapping.json file downloaded "
        "earlier. It is read on this computer and replaces the table of the current document."
    ),
    "restore.table.upload": "Mapping table (.json)",
    "restore.table.in_use_document": "Table in use: the one built from the current document.",
    "restore.table.in_use_file": "Table in use: the file {name}.",
    "restore.table.error.encoding": (
        "This file is not readable text. Upload the .mapping.json file exactly as HuisClos "
        "saved it."
    ),
    "restore.table.error.invalid": (
        "This file is not a valid HuisClos mapping table. Upload the .mapping.json file "
        "exactly as HuisClos saved it."
    ),
    "restore.download.heading": "Download",
    "restore.download.pseudonymized_txt": "Pseudonymized text (.txt)",
    "restore.download.pseudonymized_docx": "Pseudonymized text (.docx)",
    "restore.download.restored_txt": "Restored text (.txt)",
    "restore.download.restored_docx": "Restored text (.docx)",
    "restore.download.restored_wait": "Restore an answer first to download the restored text.",
    "restore.download.mapping": "Mapping table (.mapping.json)",
    "restore.download.mapping.warning": (
        "Sensitive file: it links tokens to real identities. Keep it on this computer. Never "
        "send it to an AI tool."
    ),
    "restore.docx.title.pseudonymized": "Pseudonymized text",
    "restore.docx.title.restored": "Restored text",
    "restore.new.button": "Start a new document",
    "restore.new.note": (
        "HuisClos does not keep the mapping table. Download it first if you need to restore an"
        " answer later."
    ),
    "restore.new.confirm": (
        "Start a new document? The text, the detections, the pseudonymized text and the "
        "restored text are erased from this session. HuisClos does not keep the mapping table,"
        " so it cannot be recovered afterwards."
    ),
    "restore.new.yes": "Yes, start a new document",
    "restore.new.cancel": "Cancel",
}

FR: dict[str, str] = {
    "restore.title": "Restaurer les vraies valeurs",
    "restore.empty": (
        "Rien à restaurer pour le moment. Terminez les étapes Importer et Vérifier, ou chargez"
        " une table de correspondance enregistrée ci-dessous."
    ),
    "restore.back": "Retour à Importer",
    "restore.back_review": "Retour à Vérifier",
    "restore.send.heading": "Envoyer à votre outil d'IA",
    "restore.send.intro": (
        "Copiez ce texte dans l'outil d'IA de votre choix. Les noms et identifiants sont "
        "remplacés par des jetons comme `[PERSONNE_1]`."
    ),
    "restore.send.literal_tokens": (
        "Le texte d'origine contient déjà des chaînes ressemblant à des jetons. Vérifiez le "
        "texte restauré : elles peuvent être confondues avec les jetons créés par HuisClos."
    ),
    "restore.send.leaves": (
        "Ce qui quitte votre ordinateur : uniquement le texte ci-dessus. La table de "
        "correspondance reste ici."
    ),
    "restore.send.check": (
        "Relisez le texte avant tout envoi. Une valeur non masquée quitte votre ordinateur en "
        "clair."
    ),
    "restore.send.counts.heading": "Jetons de ce texte",
    "restore.send.counts.type": "Type",
    "restore.send.counts.tokens": "Jetons",
    "restore.send.counts.occurrences": "Occurrences",
    "restore.send.instruction.heading": "Consigne recommandée",
    "restore.send.instruction.help": (
        "Collez une de ces consignes avec le texte pour que l'outil d'IA conserve les jetons."
    ),
    "restore.send.instruction.fr.label": "En français",
    "restore.send.instruction.fr": (
        "Conserve exactement chaque jeton entre crochets, par exemple [PERSONNE_1], sans le "
        "modifier ni le traduire, et n'en invente aucun."
    ),
    "restore.send.instruction.en.label": "En anglais",
    "restore.send.instruction.en": (
        "Keep every bracketed token exactly as written, for example [PERSON_1]; do not change,"
        " translate or invent tokens."
    ),
    "restore.answer.heading": "Restaurer la réponse de l'IA",
    "restore.answer.label": "Réponse de l'outil d'IA",
    "restore.answer.placeholder": "Collez ici la réponse de l'outil d'IA.",
    "restore.answer.button": "Restaurer",
    "restore.answer.empty": "Collez d'abord la réponse de l'outil d'IA.",
    "restore.answer.restored_heading": "Texte restauré",
    "restore.mode.exact": (
        "Mode exact : il s'agit du texte pseudonymisé lui-même ; chaque valeur reprend donc sa"
        " forme d'origine."
    ),
    "restore.mode.tolerant": (
        "Mode tolérant : chaque jeton est remplacé par la forme principale de sa valeur. Une "
        "variante écrite différemment dans l'original, comme un nom en majuscules, reprend la "
        "forme principale."
    ),
    "restore.none_found": "Aucun jeton trouvé dans cette réponse ; rien n'a été restauré.",
    "restore.unknown": (
        "Les jetons inconnus sont laissés inchangés ({count}) : {forms}. L'outil d'IA les a "
        "peut-être inventés, ou la table correspond à un autre document."
    ),
    "restore.altered": (
        "Jetons modifiés reconnus et restaurés ({count}) : {pairs}. L'outil d'IA les a écrits "
        "différemment de l'original. Vérifiez ces passages."
    ),
    "restore.altered.pair": "{found} lu comme {token}",
    "restore.missing": "Jetons de la table absents de la réponse : {tokens}.",
    "restore.table.heading": "Utiliser une table enregistrée (facultatif)",
    "restore.table.help": (
        "Pour restaurer une réponse reçue plus tard, téléversez le fichier .mapping.json "
        "téléchargé auparavant. Il est lu sur cet ordinateur et remplace la table du document "
        "actuel."
    ),
    "restore.table.upload": "Table de correspondance (.json)",
    "restore.table.in_use_document": "Table utilisée : celle du document actuel.",
    "restore.table.in_use_file": "Table utilisée : le fichier {name}.",
    "restore.table.error.encoding": (
        "Ce fichier n'est pas un texte lisible. Téléversez le fichier .mapping.json tel que "
        "HuisClos l'a enregistré."
    ),
    "restore.table.error.invalid": (
        "Ce fichier n'est pas une table de correspondance HuisClos valide. Téléversez le "
        "fichier .mapping.json tel que HuisClos l'a enregistré."
    ),
    "restore.download.heading": "Télécharger",
    "restore.download.pseudonymized_txt": "Texte pseudonymisé (.txt)",
    "restore.download.pseudonymized_docx": "Texte pseudonymisé (.docx)",
    "restore.download.restored_txt": "Texte restauré (.txt)",
    "restore.download.restored_docx": "Texte restauré (.docx)",
    "restore.download.restored_wait": (
        "Restaurez d'abord une réponse pour télécharger le texte restauré."
    ),
    "restore.download.mapping": "Table de correspondance (.mapping.json)",
    "restore.download.mapping.warning": (
        "Fichier sensible : il relie les jetons aux identités réelles. Conservez-le sur cet "
        "ordinateur. Ne l'envoyez jamais à un outil d'IA."
    ),
    "restore.docx.title.pseudonymized": "Texte pseudonymisé",
    "restore.docx.title.restored": "Texte restauré",
    "restore.new.button": "Commencer un nouveau document",
    "restore.new.note": (
        "HuisClos ne conserve pas la table de correspondance. Téléchargez-la d'abord si vous "
        "devez restaurer une réponse plus tard."
    ),
    "restore.new.confirm": (
        "Commencer un nouveau document ? Le texte, les détections, le texte pseudonymisé et le"
        " texte restauré seront effacés de cette session. HuisClos ne conserve pas la table de"
        " correspondance ; elle ne pourra pas être récupérée ensuite."
    ),
    "restore.new.yes": "Oui, commencer un nouveau document",
    "restore.new.cancel": "Annuler",
}
