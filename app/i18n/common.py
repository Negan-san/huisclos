"""Textes communs à toutes les pages : en-tête, navigation, étapes, types et barre latérale.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets, fusionnés par app.i18n.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "app.title": "HuisClos",
    "app.tagline": "Use generative AI on client files without breaching professional secrecy.",
    "app.legal_note": "Pseudonymization is not anonymization (GDPR art. 4(5), recital 26).",
    "demo.banner": (
        "Public demo: use fictitious data only. To process real client files, install HuisClos"
        " on your computer (see the user guide)."
    ),
    "nav.pseudonymize": "Pseudonymize",
    "nav.evaluation": "Evaluation",
    "nav.method": "Method & limits",
    "steps.label": "Steps of the workflow",
    "steps.import": "Import",
    "steps.review": "Review",
    "steps.restore": "Restore",
    "steps.current": "(current step)",
    "steps.locked.review": "Available once sensitive data has been detected.",
    "steps.locked.restore": "Available once the pseudonymized text has been created.",
    "entity.PERSON": "Person",
    "entity.ORGANIZATION": "Organization",
    "entity.ADDRESS": "Address",
    "entity.EMAIL": "Email",
    "entity.PHONE": "Phone",
    "entity.IBAN": "IBAN",
    "entity.NIR": "Social security number (NIR)",
    "entity.SIREN": "SIREN",
    "entity.SIRET": "SIRET",
    "entity.BIRTH_DATE": "Birth date",
    "entity.CASE_NUMBER": "Case number",
    "entity.LOCATION": "Place",
    "entity.CUSTOM": "Custom",
    "sidebar.settings": "Settings",
    "sidebar.types": "Types to detect",
    "sidebar.threshold": "Confidence threshold",
    "sidebar.threshold.help": "Lower threshold = more text masked, fewer misses.",
    "sidebar.token_style": "Token style",
    "sidebar.token_style.fr": "French labels [PERSONNE_1]",
    "sidebar.token_style.en": "English labels [PERSON_1]",
    "sidebar.language": "Language",
    "sidebar.language.en": "English",
    "sidebar.language.fr": "Français",
    "sidebar.language.notice": "The French interface is not available yet. English is kept.",
    "sidebar.reset": "Reset session",
    "sidebar.reset.confirm": (
        "This clears the text, the detections and the mapping table of this session."
    ),
    "sidebar.reset.yes": "Yes, reset",
    "sidebar.reset.cancel": "Cancel",
}

FR: dict[str, str] = {
    "app.title": "HuisClos",
    "app.tagline": (
        "Utilisez l'IA générative sur les dossiers clients en préservant le secret professionnel."
    ),
    "app.legal_note": (
        "La pseudonymisation n'est pas une anonymisation (RGPD art. 4(5), considérant 26)."
    ),
    "demo.banner": (
        "Démonstration publique : utilisez uniquement des données fictives. Pour traiter de "
        "vrais dossiers clients, installez HuisClos sur votre ordinateur (voir le guide "
        "utilisateur)."
    ),
    "nav.pseudonymize": "Pseudonymiser",
    "nav.evaluation": "Évaluation",
    "nav.method": "Méthode et limites",
    "steps.label": "Étapes du parcours",
    "steps.import": "Importer",
    "steps.review": "Vérifier",
    "steps.restore": "Restaurer",
    "steps.current": "(étape actuelle)",
    "steps.locked.review": "Disponible après la détection des données sensibles.",
    "steps.locked.restore": "Disponible après la création du texte pseudonymisé.",
    "entity.PERSON": "Personne",
    "entity.ORGANIZATION": "Organisation",
    "entity.ADDRESS": "Adresse",
    "entity.EMAIL": "Courriel",
    "entity.PHONE": "Téléphone",
    "entity.IBAN": "IBAN",
    "entity.NIR": "Numéro de sécurité sociale (NIR)",
    "entity.SIREN": "SIREN",
    "entity.SIRET": "SIRET",
    "entity.BIRTH_DATE": "Date de naissance",
    "entity.CASE_NUMBER": "Numéro de dossier",
    "entity.LOCATION": "Lieu",
    "entity.CUSTOM": "Autre",
    "sidebar.settings": "Réglages",
    "sidebar.types": "Types à détecter",
    "sidebar.threshold": "Seuil de confiance",
    "sidebar.threshold.help": "Un seuil plus bas masque davantage de texte et réduit les oublis.",
    "sidebar.token_style": "Style des jetons",
    "sidebar.token_style.fr": "Libellés français [PERSONNE_1]",
    "sidebar.token_style.en": "Libellés anglais [PERSON_1]",
    "sidebar.language": "Langue",
    "sidebar.language.en": "English",
    "sidebar.language.fr": "Français",
    "sidebar.language.notice": "Cette langue n'est pas disponible. L'anglais est conservé.",
    "sidebar.reset": "Réinitialiser la session",
    "sidebar.reset.confirm": (
        "Le texte, les détections et la table de correspondance de cette session seront effacés."
    ),
    "sidebar.reset.yes": "Oui, réinitialiser",
    "sidebar.reset.cancel": "Annuler",
}
