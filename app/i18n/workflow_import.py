"""Textes anglais et français de l'étape Import.

Entrées : valeurs à insérer dans les messages de cette étape.
Sorties : dictionnaires EN et FR fusionnés par app.i18n.workflow.
Place dans le pipeline : affichage local du parcours de pseudonymisation.
"""

EN: dict[str, str] = {
    "import.title": "Import a document",
    "import.intro": (
        "Paste a text or upload a file. HuisClos then looks for names, companies, addresses, "
        "identifiers and dates."
    ),
    "import.empty": "No text yet. Paste a document, upload a file or load the sample case.",
    "import.sample.button": "Load sample case",
    "import.sample.notice": (
        "This is a fictitious case written for demonstration. Every name, number and address "
        "in it is invented."
    ),
    "import.tab.paste": "Paste text",
    "import.tab.upload": "Upload a file",
    "import.paste.label": "Text to process",
    "import.paste.placeholder": "Paste the text of a document here.",
    "import.upload.label": "Choose a file (.txt, .docx or .pdf)",
    "import.upload.note": "Text PDFs only, no scanned documents.",
    "import.upload.loaded": "Loaded {name}.",
    "import.source.pasted": "Pasted text",
    "import.source.summary": "Source: {name}. {count} characters.",
    "import.detect.button": "Detect sensitive data",
    "import.detect.spinner": "Detecting sensitive data. The first run loads the language model.",
    "import.detect.no_types": "Select at least one type to detect in the sidebar.",
    "import.detect.note": "Detection is not repeated when the text and the settings are unchanged.",
    "import.privacy": "Processing happens on this computer. Nothing is sent anywhere.",
    "import.privacy.title": "Stays on this computer",
    "import.privacy.detail": (
        "Only the pseudonymized text leaves, and only when you copy it into your AI tool in the"
        " Restore step."
    ),
    "import.privacy.demo.title": "Public demo",
    "import.privacy.demo": (
        "On this demo, the text is processed by the demo server. Use fictitious data only."
    ),
    "import.card.title": "Your document",
    "import.detects.title": "What HuisClos detects",
    "import.detects.intro": (
        "You review every value found before anything is replaced. These types are searched:"
    ),
    "import.detects.settings": "Change the types and the threshold in the sidebar.",
    "import.detect.step.engine": "Preparing the detection engine.",
    "import.detect.step.search": "Looking for names, companies, addresses and identifiers.",
    "import.detect.done": "Detection complete.",
    "import.error.unsupported_type": (
        "This file type is not supported. Use a .txt, .docx or .pdf file."
    ),
    "import.error.too_large": "This file is larger than 5 MB. Split it or paste the relevant part.",
    "import.error.too_long": (
        "This text is too long (over 200,000 characters). Split it into parts."
    ),
    "import.error.empty": "There is no text to process. Paste a text or choose another file.",
    "import.error.encoding": "The text could not be decoded. Save the file as UTF-8 and try again.",
    "import.error.docx_invalid": (
        "This Word file cannot be read. Open it in Word and save it again as .docx."
    ),
    "import.error.pdf_encrypted": (
        "This PDF is protected by a password. Remove the protection and upload it again."
    ),
    "import.error.pdf_no_text": (
        "This PDF has no selectable text, so it is probably a scan. Scanned documents are not "
        "supported."
    ),
    "import.error.pdf_invalid": "This PDF cannot be read. Export it again from its source.",
    "import.error.sample_missing": "The sample case file is missing from this installation.",
    "import.error.engine": (
        "The detection engine could not start. Check that the French language model is "
        "installed (see the user guide)."
    ),
    "import.warning.encoding_cp1252": (
        "This file is not in UTF-8. It was read as Windows-1252, so check the accented letters."
    ),
}

FR: dict[str, str] = {
    "import.title": "Importer un document",
    "import.intro": (
        "Collez un texte ou téléversez un fichier. HuisClos recherche ensuite les noms, "
        "sociétés, adresses, identifiants et dates."
    ),
    "import.empty": (
        "Aucun texte pour le moment. Collez un document, téléversez un fichier ou chargez le "
        "cas d'exemple."
    ),
    "import.sample.button": "Charger le cas d'exemple",
    "import.sample.notice": (
        "Ce cas fictif a été rédigé pour la démonstration. Chaque nom, numéro et adresse est "
        "inventé."
    ),
    "import.tab.paste": "Coller un texte",
    "import.tab.upload": "Téléverser un fichier",
    "import.paste.label": "Texte à traiter",
    "import.paste.placeholder": "Collez ici le texte d'un document.",
    "import.upload.label": "Choisir un fichier (.txt, .docx ou .pdf)",
    "import.upload.note": (
        "PDF texte uniquement, les documents numérisés ne sont pas pris en charge."
    ),
    "import.upload.loaded": "Fichier {name} chargé.",
    "import.source.pasted": "Texte collé",
    "import.source.summary": "Source : {name}. {count} caractères.",
    "import.detect.button": "Détecter les données sensibles",
    "import.detect.spinner": (
        "Détection des données sensibles. Le premier lancement charge le modèle de langue."
    ),
    "import.detect.no_types": "Sélectionnez au moins un type à détecter dans la barre latérale.",
    "import.detect.note": (
        "La détection n'est pas répétée si le texte et les réglages sont inchangés."
    ),
    "import.privacy": "Le traitement se fait sur cet ordinateur. Rien n'est envoyé à l'extérieur.",
    "import.privacy.title": "Reste sur cet ordinateur",
    "import.privacy.detail": (
        "Seul le texte pseudonymisé sort, et seulement quand vous le copiez dans votre outil d'IA"
        " à l'étape Restaurer."
    ),
    "import.privacy.demo.title": "Démonstration publique",
    "import.privacy.demo": (
        "Sur cette démonstration, le texte est traité par le serveur de démonstration. "
        "Utilisez uniquement des données fictives."
    ),
    "import.card.title": "Votre document",
    "import.detects.title": "Ce que HuisClos détecte",
    "import.detects.intro": (
        "Vous vérifiez chaque valeur trouvée avant tout remplacement. Types recherchés :"
    ),
    "import.detects.settings": "Modifiez les types et le seuil dans la barre latérale.",
    "import.detect.step.engine": "Préparation du moteur de détection.",
    "import.detect.step.search": "Recherche des noms, sociétés, adresses et identifiants.",
    "import.detect.done": "Détection terminée.",
    "import.error.unsupported_type": (
        "Ce type de fichier n'est pas pris en charge. Utilisez un fichier .txt, .docx ou .pdf."
    ),
    "import.error.too_large": "Ce fichier dépasse 5 Mo. Divisez-le ou collez la partie utile.",
    "import.error.too_long": (
        "Ce texte est trop long (plus de 200 000 caractères). Divisez-le en plusieurs parties."
    ),
    "import.error.empty": "Aucun texte à traiter. Collez un texte ou choisissez un autre fichier.",
    "import.error.encoding": (
        "Le texte n'a pas pu être décodé. Enregistrez le fichier en UTF-8 et réessayez."
    ),
    "import.error.docx_invalid": (
        "Ce fichier Word est illisible. Ouvrez-le dans Word et enregistrez-le à nouveau en .docx."
    ),
    "import.error.pdf_encrypted": (
        "Ce PDF est protégé par un mot de passe. Retirez la protection et téléversez-le à nouveau."
    ),
    "import.error.pdf_no_text": (
        "Ce PDF n'a pas de texte sélectionnable ; il s'agit probablement d'un document "
        "numérisé. Les documents numérisés ne sont pas pris en charge."
    ),
    "import.error.pdf_invalid": "Ce PDF est illisible. Exportez-le à nouveau depuis sa source.",
    "import.error.sample_missing": "Le fichier du cas d'exemple manque dans cette installation.",
    "import.error.engine": (
        "Le moteur de détection n'a pas pu démarrer. Vérifiez que le modèle de langue "
        "française est installé (voir le guide utilisateur)."
    ),
    "import.warning.encoding_cp1252": (
        "Ce fichier n'est pas en UTF-8. Il a été lu en Windows-1252 ; vérifiez les lettres "
        "accentuées."
    ),
}
