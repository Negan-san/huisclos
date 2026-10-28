"""Textes communs à toutes les pages : en-tête, navigation, étapes, types et barre latérale.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets, fusionnés par app.i18n.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "app.title": "HuisClos",
    "app.tagline": "Use generative AI on client files without breaching professional secrecy.",
    "app.legal_note": "Pseudonymization is not anonymization (GDPR art. 4(5), recital 26).",
    "app.local_badge": "Local processing",
    "app.demo_badge": "Public demo",
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
    "steps.state.done": "Completed",
    "steps.state.current": "Current step",
    "steps.state.available": "Available",
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
    "sidebar.help": "Changes apply to the next detection.",
    "sidebar.group.document": "Document",
    "sidebar.document_language": "Document language",
    "sidebar.document_language.fr": "French",
    "sidebar.document_language.en": "English",
    "sidebar.document_language.help": (
        "Language of the text you analyse. It selects the rules and the local language model. "
        "It does not follow the interface language or the token style."
    ),
    "sidebar.profile": "Detection profile",
    "sidebar.profile.standard": "Standard",
    "sidebar.profile.enhanced": "Enhanced local detection",
    "sidebar.profile.help": (
        "Standard: rules, spaCy and propagation. Enhanced adds the local CamemBERT model, for "
        "French documents only: slower, loaded on first use, local installation only."
    ),
    "sidebar.profile.notice.public_demo": (
        "Enhanced detection is not available on the public demo. Standard is used."
    ),
    "sidebar.profile.notice.language": (
        "Enhanced detection supports French documents only for now. Standard is used."
    ),
    "sidebar.profile.notice.unknown": "Unknown detection profile. Standard is used.",
    "sidebar.profile.demo": "Enhanced detection is offered in a local installation only.",
    "sidebar.profile.french_only": "Enhanced detection covers French documents only for now.",
    "sidebar.group.detection": "Detection",
    "sidebar.group.tokens": "Tokens",
    "sidebar.group.interface": "Interface",
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
    "app.local_badge": "Traitement local",
    "app.demo_badge": "Démonstration publique",
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
    "steps.state.done": "Terminée",
    "steps.state.current": "Étape actuelle",
    "steps.state.available": "Disponible",
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
    "sidebar.help": "Les changements s'appliquent à la prochaine détection.",
    "sidebar.group.document": "Document",
    "sidebar.document_language": "Langue du document",
    "sidebar.document_language.fr": "Français",
    "sidebar.document_language.en": "Anglais",
    "sidebar.document_language.help": (
        "Langue du texte analysé. Elle choisit les règles et le modèle de langue local. Elle "
        "ne suit ni la langue de l'interface ni le style des jetons."
    ),
    "sidebar.profile": "Profil de détection",
    "sidebar.profile.standard": "Standard",
    "sidebar.profile.enhanced": "Détection locale renforcée",
    "sidebar.profile.help": (
        "Standard : règles, spaCy et propagation. Le profil renforcé ajoute le modèle local "
        "CamemBERT, pour les documents français seulement : plus lent, chargé au premier usage, "
        "installation locale seulement."
    ),
    "sidebar.profile.notice.public_demo": (
        "La détection renforcée n'est pas disponible sur la démonstration publique. Le profil "
        "Standard est utilisé."
    ),
    "sidebar.profile.notice.language": (
        "La détection renforcée ne prend en charge que les documents français pour le moment. "
        "Le profil Standard est utilisé."
    ),
    "sidebar.profile.notice.unknown": "Profil de détection inconnu. Standard est utilisé.",
    "sidebar.profile.demo": "La détection renforcée n'est proposée qu'en installation locale.",
    "sidebar.profile.french_only": (
        "La détection renforcée ne couvre que les documents français pour le moment."
    ),
    "sidebar.group.detection": "Détection",
    "sidebar.group.tokens": "Jetons",
    "sidebar.group.interface": "Interface",
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
