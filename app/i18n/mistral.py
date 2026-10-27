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
    "mistral.instruction": (
        "Your instruction (sent after the pseudonymized text; use fictitious data only)"
    ),
    "mistral.confirm": "I confirm that only the pseudonymized text above will be sent",
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
    "mistral.instruction": (
        "Votre consigne (envoyée après le texte pseudonymisé ; données fictives uniquement)"
    ),
    "mistral.confirm": "Je confirme que seul le texte pseudonymisé ci-dessus sera envoyé",
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
