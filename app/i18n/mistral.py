"""Textes du connecteur facultatif Mistral.

Entrées : codes d'erreur publics du client HTTP, sans contenu utilisateur.
Sorties : dictionnaires anglais et français du bloc d'envoi.
Place dans le pipeline : consentement explicite avant l'appel externe.
"""

EN: dict[str, str] = {
    "mistral.heading": "Send to Mistral (optional)",
    "mistral.warning": (
        "On Mistral's free Experiment plan, requests may be used to train Mistral's models. "
        "Use fictitious data only."
    ),
    "mistral.content": (
        "Sends exactly the checked message shown above: the pseudonymized text, the separator "
        "line and your instruction. Never the mapping table."
    ),
    "mistral.not_ready": "Sending is possible once the final check allows it.",
    "mistral.refused": (
        "Nothing was sent: confirm the exact message first. If the message or its settings "
        "changed since your confirmation, check it and confirm again."
    ),
    "mistral.confirm": "I confirm sending exactly the checked message above",
    "mistral.send": "Send to Mistral",
    "mistral.spinner": "Waiting for Mistral's answer...",
    "mistral.error.unauthorized": "Mistral refused the API key (401). Check the configured key.",
    "mistral.error.quota": "Mistral quota exceeded (429). Try again later or check your quota.",
    "mistral.error.timeout": "Mistral did not respond before the timeout. Try again later.",
    "mistral.error.connection": (
        "Mistral could not be reached. Check your connection and try again."
    ),
    "mistral.error.unexpected": "Mistral returned an unexpected response. Try again later.",
}

FR: dict[str, str] = {
    "mistral.heading": "Envoyer à Mistral (facultatif)",
    "mistral.warning": (
        "Avec l'offre gratuite Experiment de Mistral, les requêtes peuvent servir à entraîner "
        "ses modèles. Utilisez uniquement des données fictives."
    ),
    "mistral.content": (
        "Envoie exactement le message contrôlé affiché plus haut : le texte pseudonymisé, la "
        "ligne de séparation et votre consigne. Jamais la table de correspondance."
    ),
    "mistral.not_ready": "L'envoi devient possible dès que le contrôle final le permet.",
    "mistral.refused": (
        "Rien n'a été envoyé : confirmez d'abord le message exact. Si le message ou ses "
        "réglages ont changé depuis votre confirmation, vérifiez-le et confirmez à nouveau."
    ),
    "mistral.confirm": "Je confirme l'envoi exact du message contrôlé ci-dessus",
    "mistral.send": "Envoyer à Mistral",
    "mistral.spinner": "En attente de la réponse de Mistral...",
    "mistral.error.unauthorized": "Mistral a refusé la clé API (401). Vérifiez la clé configurée.",
    "mistral.error.quota": (
        "Le quota Mistral est dépassé (429). Réessayez plus tard ou vérifiez votre quota."
    ),
    "mistral.error.timeout": "Mistral n'a pas répondu dans le délai prévu. Réessayez plus tard.",
    "mistral.error.connection": "Mistral est inaccessible. Vérifiez votre connexion et réessayez.",
    "mistral.error.unexpected": "Mistral a renvoyé une réponse inattendue. Réessayez plus tard.",
}
