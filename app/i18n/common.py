"""Textes communs à toutes les pages : en-tête, navigation, étapes, types et barre latérale.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : EN (anglais, obligatoire). FR sera ajouté quand les chaînes françaises existeront.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "app.title": "HuisClos",
    "app.tagline": "Use generative AI on client files without breaching professional secrecy.",
    "app.legal_note": "Pseudonymization is not anonymization (GDPR art. 4(5), recital 26).",
    "demo.banner": (
        "Public demo: use fictitious data only. To process real client files, install "
        "HuisClos on your computer (see the user guide)."
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
    "sidebar.language.fr": "Français (coming soon)",
    "sidebar.language.notice": "The French interface is not available yet. English is kept.",
    "sidebar.reset": "Reset session",
    "sidebar.reset.confirm": (
        "This clears the text, the detections and the mapping table of this session."
    ),
    "sidebar.reset.yes": "Yes, reset",
    "sidebar.reset.cancel": "Cancel",
}
