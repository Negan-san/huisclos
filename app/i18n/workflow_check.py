"""Textes anglais et français du contrôle final de l'étape Restore.

Entrées : valeurs à insérer dans les messages du contrôle final.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.workflow.
Place dans le pipeline : affichage local, juste avant l'envoi du message pseudonymisé.
"""

EN: dict[str, str] = {
    "check.neural_threshold": (
        "English Enhanced keeps the validated GLiNER cutoff of 0.70 for this check. "
        "The lower main threshold cannot reveal candidates the models never proposed."
    ),
    "check.heading": "Final check",
    "check.intro": (
        "Before anything leaves your computer, HuisClos checks the exact message: the "
        "pseudonymized text and your instruction. It searches them for the values of the "
        "mapping table, including surnames alone, reads the original text again to find "
        "parts left next to a token, and runs the same detection again with a lower threshold."
    ),
    "check.spinner": "Checking the message to send.",
    "check.clear": "No residual identifier found.",
    "check.clear.note": (
        "This check lowers the risk of a leak, it does not make the text anonymous. The second "
        "detection uses the same engine: it is not an independent review. Read the message "
        "once more before sending it."
    ),
    "check.reviewed": (
        "All {count} alerts were reviewed: you decided to keep each one in clear in its context."
    ),
    "check.found": (
        "Possible identifiers left in clear: {count}. Mask them, edit the instruction, or "
        "decide on each one, before you copy or send the message."
    ),
    "check.origin.table": "A value of the mapping table, or a part of it, is still in clear.",
    "check.origin.detection": "Found by a new detection with a lower threshold.",
    "check.origin.context": (
        "Part of a name found in the original text, next to a masked part (incomplete bounds)."
    ),
    "check.origin.unknown_token": (
        "This looks like a token, but it is not in the mapping table. Use a known token or "
        "remove it: a new token needs a review."
    ),
    "check.segment.document": "Location: pseudonymized text.",
    "check.segment.instruction": "Location: your instruction.",
    "check.instruction.edit": "Edit your instruction below to remove this value.",
    "check.ack": "I reviewed this mention in its context: keep it in clear",
    "check.mask": "Mask everywhere",
    "check.mask.done": (
        "{value} is now masked everywhere ({count} occurrences added). The text was "
        "pseudonymized again."
    ),
    "check.mask.error": (
        "This value could not be masked here. Go back to Review and add it by hand."
    ),
    "check.error": (
        "The final check could not run, because the detection engine did not start or an "
        "error occurred. Nothing is presented as checked."
    ),
    "check.retry": "Run the check again",
    "check.stale.detection": (
        "The text, the document language, the detection profile, the types, the threshold or "
        "the case table changed since the detection. This message is no longer checked: run "
        "the detection again, then review."
    ),
    "check.stale.detection.button": "Back to Import",
    "check.stale.review": (
        "Your review decisions or the token style changed since this text was pseudonymized. "
        "Pseudonymize again from Review before the check."
    ),
    "check.stale.review.button": "Back to Review",
    "check.policy.heading": "Check settings",
    "check.policy.summary": "Types checked: {types}. Exclusion list: {exclusions}.",
    "check.policy.types.sidebar": "those selected in the sidebar",
    "check.policy.types.all": "all types, including those turned off",
    "check.policy.exclusions.on": "applied",
    "check.policy.exclusions.off": "ignored",
    "check.policy.all_types": "Also check the types turned off in the sidebar",
    "check.policy.all_types.help": (
        "Finds more values, such as places, with more false alerts. Nothing is masked "
        "without your action."
    ),
    "check.policy.no_exclusions": "Ignore the exclusion list during the check",
    "check.policy.no_exclusions.help": (
        "Courts, institutions and legal terms are then reported too. Expect false alerts; "
        "nothing is masked without your action."
    ),
}

FR: dict[str, str] = {
    "check.neural_threshold": (
        "Le profil anglais renforc\u00e9 conserve le seuil GLiNER valid\u00e9 de 0,70 pour "
        "ce contr\u00f4le. Le seuil principal abaiss\u00e9 ne r\u00e9v\u00e8le pas les "
        "candidats que les mod\u00e8les n'ont jamais propos\u00e9s."
    ),
    "check.heading": "Contrôle final",
    "check.intro": (
        "Avant que quoi que ce soit ne quitte votre poste, HuisClos contrôle le message exact : "
        "le texte pseudonymisé et votre consigne. Il y recherche les valeurs de la table de "
        "correspondance, noms de famille seuls compris, relit le texte d'origine pour trouver "
        "des parties laissées à côté d'un jeton, et relance la même détection à un seuil plus "
        "bas."
    ),
    "check.spinner": "Contrôle du message à envoyer.",
    "check.clear": "Aucun identifiant résiduel trouvé.",
    "check.clear.note": (
        "Ce contrôle réduit le risque de fuite, il ne rend pas le texte anonyme. La seconde "
        "détection utilise le même moteur : ce n'est pas une relecture indépendante. Relisez "
        "le message avant de l'envoyer."
    ),
    "check.reviewed": (
        "Les {count} alertes ont été examinées : vous avez décidé de garder chacune en clair "
        "dans son contexte."
    ),
    "check.found": (
        "Identifiants possibles restés en clair : {count}. Masquez-les, modifiez la consigne "
        "ou décidez pour chacun, avant de copier ou d'envoyer le message."
    ),
    "check.origin.table": (
        "Une valeur de la table de correspondance, ou une partie de cette valeur, est restée "
        "en clair."
    ),
    "check.origin.detection": "Trouvé par une nouvelle détection à un seuil plus bas.",
    "check.origin.context": (
        "Partie d'un nom trouvée dans le texte d'origine, à côté d'une partie masquée (bornes "
        "incomplètes)."
    ),
    "check.origin.unknown_token": (
        "Cela ressemble à un jeton, mais il n'est pas dans la table de correspondance. "
        "Utilisez un jeton connu ou retirez-le : un nouveau jeton demande une revue."
    ),
    "check.segment.document": "Emplacement : texte pseudonymisé.",
    "check.segment.instruction": "Emplacement : votre consigne.",
    "check.instruction.edit": "Modifiez votre consigne ci-dessous pour retirer cette valeur.",
    "check.ack": "J'ai examiné cette mention dans son contexte : la garder en clair",
    "check.mask": "Masquer partout",
    "check.mask.done": (
        "{value} est désormais masqué partout ({count} occurrences ajoutées). Le texte a été "
        "pseudonymisé à nouveau."
    ),
    "check.mask.error": (
        "Cette valeur n'a pas pu être masquée ici. Revenez à l'étape Vérifier et ajoutez-la à "
        "la main."
    ),
    "check.error": (
        "Le contrôle final n'a pas pu être fait : le moteur de détection n'a pas démarré ou une "
        "erreur est survenue. Rien n'est présenté comme contrôlé."
    ),
    "check.retry": "Relancer le contrôle",
    "check.stale.detection": (
        "Le texte, la langue du document, le profil, les types, le seuil ou la table de "
        "dossier ont changé depuis la détection. Ce message n'est plus contrôlé : relancez la "
        "détection, puis la revue."
    ),
    "check.stale.detection.button": "Retour à Importer",
    "check.stale.review": (
        "Vos décisions de revue ou le style des jetons ont changé depuis la pseudonymisation. "
        "Pseudonymisez à nouveau depuis l'étape Vérifier avant le contrôle."
    ),
    "check.stale.review.button": "Retour à Vérifier",
    "check.policy.heading": "Réglages du contrôle",
    "check.policy.summary": "Types contrôlés : {types}. Liste d'exclusions : {exclusions}.",
    "check.policy.types.sidebar": "ceux choisis dans la barre latérale",
    "check.policy.types.all": "tous les types, y compris ceux désactivés",
    "check.policy.exclusions.on": "appliquée",
    "check.policy.exclusions.off": "ignorée",
    "check.policy.all_types": "Contrôler aussi les types désactivés dans la barre latérale",
    "check.policy.all_types.help": (
        "Trouve davantage de valeurs, comme des lieux, avec plus de fausses alertes. Rien "
        "n'est masqué sans votre action."
    ),
    "check.policy.no_exclusions": "Ignorer la liste d'exclusions pendant le contrôle",
    "check.policy.no_exclusions.help": (
        "Juridictions, institutions et termes juridiques sont alors signalés aussi. Attendez-"
        "vous à de fausses alertes ; rien n'est masqué sans votre action."
    ),
}
