"""Textes anglais et français du contrôle final de l'étape Restore.

Entrées : valeurs à insérer dans les messages du contrôle final.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.workflow.
Place dans le pipeline : affichage local, juste avant l'envoi du texte pseudonymisé.
"""

EN: dict[str, str] = {
    "check.heading": "Final check",
    "check.intro": (
        "Before you copy the text, HuisClos searches it again for the values of the mapping "
        "table, including surnames alone, and runs a second detection with a lower threshold."
    ),
    "check.spinner": "Checking the pseudonymized text.",
    "check.clear": "No residual identifier found.",
    "check.clear.note": (
        "This check lowers the risk of a leak, it does not make the text anonymous. Read the "
        "text once more before sending it."
    ),
    "check.found": (
        "Possible identifiers left in clear: {count}. Mask them, or check each one, before you"
        " copy the text."
    ),
    "check.origin.table": "A value of the mapping table, or a part of it, is still in clear.",
    "check.origin.detection": "Found by a second detection with a lower threshold.",
    "check.mask": "Mask everywhere",
    "check.mask.done": (
        "{value} is now masked everywhere ({count} occurrences added). The text was "
        "pseudonymized again."
    ),
    "check.mask.error": (
        "This value could not be masked here. Go back to Review and add it by hand."
    ),
    "check.mask.unavailable": (
        "Masking needs the original text of this session. Go back to Import and process the "
        "document again."
    ),
    "check.error": (
        "The final check could not run, because the detection engine did not start. Read the "
        "text carefully before sending it."
    ),
}

FR: dict[str, str] = {
    "check.heading": "Contrôle final",
    "check.intro": (
        "Avant que vous copiiez le texte, HuisClos y recherche à nouveau les valeurs de la "
        "table de correspondance, noms de famille seuls compris, et relance une détection à "
        "un seuil plus bas."
    ),
    "check.spinner": "Contrôle du texte pseudonymisé.",
    "check.clear": "Aucun identifiant résiduel trouvé.",
    "check.clear.note": (
        "Ce contrôle réduit le risque de fuite, il ne rend pas le texte anonyme. Relisez le "
        "texte avant de l'envoyer."
    ),
    "check.found": (
        "Identifiants possibles restés en clair : {count}. Masquez-les, ou vérifiez chacun "
        "d'eux, avant de copier le texte."
    ),
    "check.origin.table": (
        "Une valeur de la table de correspondance, ou une partie de cette valeur, est restée "
        "en clair."
    ),
    "check.origin.detection": "Trouvé par une seconde détection à un seuil plus bas.",
    "check.mask": "Masquer partout",
    "check.mask.done": (
        "{value} est désormais masqué partout ({count} occurrences ajoutées). Le texte a été "
        "pseudonymisé à nouveau."
    ),
    "check.mask.error": (
        "Cette valeur n'a pas pu être masquée ici. Revenez à l'étape Vérifier et ajoutez-la à "
        "la main."
    ),
    "check.mask.unavailable": (
        "Le masquage a besoin du texte d'origine de cette session. Revenez à l'étape Importer "
        "et traitez à nouveau le document."
    ),
    "check.error": (
        "Le contrôle final n'a pas pu être fait, car le moteur de détection n'a pas démarré. "
        "Relisez attentivement le texte avant de l'envoyer."
    ),
}
