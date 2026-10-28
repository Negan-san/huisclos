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
    "import.upload.note": "PDF text extraction only, without OCR. Check the extracted text.",
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
    "import.detect.step.case": "Known values of the case table found in this text: {count}.",
    "import.case.heading": "Continue a case (optional)",
    "import.case.help": (
        "Upload the .mapping.json file of an earlier document from the same case. Its values "
        "are searched in this text, even where the detection misses them, and keep their "
        "tokens; a new entity takes the next free number. The file is read in memory on this "
        "computer, never saved and never sent."
    ),
    "import.case.upload": "Mapping table of an earlier document (.json)",
    "import.case.loaded": "Case table in use: {name}, {count} known entities.",
    "import.case.style": (
        "Tokens follow the style of this table, so that a known entity keeps exactly the same "
        "token. Download the merged table in the Restore step for the next document."
    ),
    "import.case.remove": "Remove the case table",
    "import.case.kept": "The case table loaded before is still in use.",
    "import.case.error.too_large": (
        "This file is larger than 2 MB, too large for a mapping table. Upload the "
        ".mapping.json file exactly as HuisClos saved it."
    ),
    "import.case.error.encoding": (
        "This file is not readable text. Upload the .mapping.json file exactly as HuisClos "
        "saved it."
    ),
    "import.case.error.invalid": (
        "This file is not a valid HuisClos mapping table. Upload the .mapping.json file "
        "exactly as HuisClos saved it."
    ),
    "import.error.unsupported_type": (
        "This file type is not supported. Use a .txt, .docx or .pdf file."
    ),
    "import.error.too_large": "This file is larger than 5 MB. Split it or paste the relevant part.",
    "import.error.too_long": (
        "This text is too long (over 200,000 characters). Split it into parts."
    ),
    "import.error.empty": "There is no text to process. Paste a text or choose another file.",
    "import.error.previous_kept": "This file was not loaded. The previous text is still shown.",
    "import.error.encoding": "The text could not be decoded. Save the file as UTF-8 and try again.",
    "import.error.docx_invalid": (
        "This Word file cannot be read. Open it in Word and save it again as .docx."
    ),
    "import.error.pdf_encrypted": (
        "This PDF is protected by a password. Remove the protection and upload it again."
    ),
    "import.error.pdf_no_text": (
        "No usable text was extracted from any page of this PDF. It may be blank or contain "
        "images only. OCR is not available. Use a text version or paste verified text."
    ),
    "import.error.pdf_invalid": "This PDF cannot be read. Export it again from its source.",
    "import.error.sample_missing": "The sample case file is missing from this installation.",
    "import.error.engine": (
        "The detection engine could not start. Check that the language model of the document "
        "language is installed (see the user guide)."
    ),
    "import.error.model.dependency": (
        "Enhanced detection needs the optional local packages (requirements-transformers.txt). "
        "Nothing was downloaded. Choose Standard or install the option."
    ),
    "import.error.model.missing": (
        "The validated CamemBERT model is not in the local cache. Nothing was downloaded. "
        "Choose Standard or install the model as described in docs/LOCAL_MODELS.md."
    ),
    "import.error.model.revision": (
        "The local CamemBERT model is not the validated revision. Nothing was downloaded. "
        "Choose Standard or restore the validated revision."
    ),
    "import.error.model.public_demo": (
        "Enhanced detection is not available on the public demo. Choose Standard."
    ),
    "import.stale": (
        "The text, the document language, the detection profile, the types, the threshold or "
        "the case table changed since the last detection. Run the detection again: your "
        "earlier review and final check no longer apply."
    ),
    "import.sample.language": (
        "The sample case is a French document: the document language is now French."
    ),
    "import.detects.profile": "Document language: {language}. Detection profile: {profile}.",
    "import.warning.encoding_cp1252": (
        "This file is not in UTF-8. It was read as Windows-1252, so check the accented letters."
    ),
    "import.warning.pdf_empty_pages": (
        "Document completeness is unknown. No text was extracted from PDF pages: {pages}. "
        "They may be blank or contain content that this reader cannot extract. Check them "
        "against the original; OCR is not available."
    ),
    "import.warning.pdf_short_pages": (
        "Document completeness is unknown. Very little text was extracted from PDF pages: "
        "{pages}. A short page can be legitimate; this does not prove it is a scan. "
        "Check these pages against the original."
    ),
    "import.warning.docx_notes": (
        "Partial Word extraction: footnotes or endnotes were found and are not extracted. "
        "Copy any relevant text into the text to process."
    ),
    "import.warning.docx_comments": (
        "Partial Word extraction: comments were found and are not extracted. Check them in "
        "the original and copy any relevant text into the text to process."
    ),
    "import.warning.docx_text_boxes": (
        "Partial Word extraction: text boxes were found and are not extracted. "
        "Copy any relevant text into the text to process."
    ),
    "import.warning.docx_revisions": (
        "Partial Word extraction: tracked changes were found. Revised passages are not "
        "reliably extracted. Review the changes in a copy of the original, accept or reject "
        "them, then import it again."
    ),
    "import.warning.docx_embedded_content": (
        "Partial Word extraction: embedded content or content controls were found. Their "
        "content is not reliably extracted. Check the original; linked attachments are not read."
    ),
    "import.warning.extraction_scope": (
        "Only the extracted text shown here is processed. Missing content affects document "
        "completeness; it is not silently included in the AI request. Review and "
        "pseudonymize any text you add before sending it."
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
    "import.upload.note": "PDF : texte extrait sans OCR. Vérifiez le résultat.",
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
    "import.detect.step.case": (
        "Valeurs connues de la table de dossier trouvées dans ce texte : {count}."
    ),
    "import.case.heading": "Poursuivre un dossier (facultatif)",
    "import.case.help": (
        "Téléversez le fichier .mapping.json d'un document précédent du même dossier. Ses "
        "valeurs sont recherchées dans ce texte, même là où la détection les manque, et gardent"
        " leur jeton ; une nouvelle entité prend le premier numéro libre. Le fichier est lu en "
        "mémoire sur cet ordinateur, jamais enregistré ni envoyé."
    ),
    "import.case.upload": "Table de correspondance d'un document précédent (.json)",
    "import.case.loaded": "Table de dossier utilisée : {name}, {count} entités connues.",
    "import.case.style": (
        "Les jetons suivent le style de cette table, pour qu'une entité connue garde exactement"
        " le même jeton. Téléchargez la table fusionnée à l'étape Restaurer pour le document "
        "suivant."
    ),
    "import.case.remove": "Retirer la table de dossier",
    "import.case.kept": "La table de dossier chargée auparavant reste utilisée.",
    "import.case.error.too_large": (
        "Ce fichier dépasse 2 Mo, ce qui est trop pour une table de correspondance. Téléversez"
        " le fichier .mapping.json tel que HuisClos l'a enregistré."
    ),
    "import.case.error.encoding": (
        "Ce fichier n'est pas un texte lisible. Téléversez le fichier .mapping.json tel que "
        "HuisClos l'a enregistré."
    ),
    "import.case.error.invalid": (
        "Ce fichier n'est pas une table de correspondance HuisClos valide. Téléversez le "
        "fichier .mapping.json tel que HuisClos l'a enregistré."
    ),
    "import.error.unsupported_type": (
        "Ce type de fichier n'est pas pris en charge. Utilisez un fichier .txt, .docx ou .pdf."
    ),
    "import.error.too_large": "Ce fichier dépasse 5 Mo. Divisez-le ou collez la partie utile.",
    "import.error.too_long": (
        "Ce texte est trop long (plus de 200 000 caractères). Divisez-le en plusieurs parties."
    ),
    "import.error.empty": "Aucun texte à traiter. Collez un texte ou choisissez un autre fichier.",
    "import.error.previous_kept": "Fichier non chargé. Le texte précédent reste affiché.",
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
        "Aucun texte exploitable n'a été extrait des pages de ce PDF. Il peut être vide ou "
        "contenir uniquement des images. L'OCR n'est pas disponible. Utilisez une version "
        "texte ou collez un texte vérifié."
    ),
    "import.error.pdf_invalid": "Ce PDF est illisible. Exportez-le à nouveau depuis sa source.",
    "import.error.sample_missing": "Le fichier du cas d'exemple manque dans cette installation.",
    "import.error.engine": (
        "Le moteur de détection n'a pas pu démarrer. Vérifiez que le modèle de la langue du "
        "document est installé (voir le guide utilisateur)."
    ),
    "import.error.model.dependency": (
        "La détection renforcée exige les paquets locaux facultatifs "
        "(requirements-transformers.txt). Rien n'a été téléchargé. Choisissez Standard ou "
        "installez l'option."
    ),
    "import.error.model.missing": (
        "Le modèle CamemBERT validé manque dans le cache local. Rien n'a été téléchargé. "
        "Choisissez Standard ou installez le modèle comme l'indique docs/LOCAL_MODELS.md."
    ),
    "import.error.model.revision": (
        "Le modèle CamemBERT local n'est pas la révision validée. Rien n'a été téléchargé. "
        "Choisissez Standard ou rétablissez la révision validée."
    ),
    "import.error.model.public_demo": (
        "La détection renforcée n'est pas disponible sur la démonstration publique. "
        "Choisissez Standard."
    ),
    "import.stale": (
        "Le texte, la langue du document, le profil, les types, le seuil ou la table de "
        "dossier ont changé depuis la dernière détection. Relancez la détection : la revue et "
        "le contrôle final précédents ne valent plus."
    ),
    "import.sample.language": (
        "Le cas d'exemple est un document français : la langue du document est maintenant le "
        "français."
    ),
    "import.detects.profile": "Langue du document : {language}. Profil de détection : {profile}.",
    "import.warning.encoding_cp1252": (
        "Ce fichier n'est pas en UTF-8. Il a été lu en Windows-1252 ; vérifiez les lettres "
        "accentuées."
    ),
    "import.warning.pdf_empty_pages": (
        "La complétude du document est inconnue. Aucun texte extrait des pages PDF : {pages}. "
        "Elles peuvent être vides ou contenir des éléments non extractibles par ce lecteur. "
        "Comparez-les à l'original ; l'OCR n'est pas disponible."
    ),
    "import.warning.pdf_short_pages": (
        "La complétude du document est inconnue. Très peu de texte extrait des pages PDF : "
        "{pages}. Une page courte peut être légitime ; ce seuil ne prouve pas un scan. "
        "Comparez ces pages à l'original."
    ),
    "import.warning.docx_notes": (
        "Extraction Word partielle : des notes de bas de page ou de fin sont présentes et "
        "ne sont pas extraites. Copiez les passages utiles dans le texte à traiter."
    ),
    "import.warning.docx_comments": (
        "Extraction Word partielle : des commentaires sont présents et ne sont pas extraits. "
        "Relisez-les dans l'original et copiez les passages utiles dans le texte à traiter."
    ),
    "import.warning.docx_text_boxes": (
        "Extraction Word partielle : des zones de texte sont présentes et ne sont pas "
        "extraites. Copiez les passages utiles dans le texte à traiter."
    ),
    "import.warning.docx_revisions": (
        "Extraction Word partielle : des révisions sont présentes. Leur extraction n'est "
        "pas fiable. Relisez-les dans une copie de l'original, acceptez-les ou rejetez-les, "
        "puis importez cette copie."
    ),
    "import.warning.docx_embedded_content": (
        "Extraction Word partielle : des contenus intégrés ou contrôles de contenu sont "
        "présents. Leur extraction n'est pas fiable. Vérifiez l'original ; les pièces jointes "
        "liées ne sont pas lues."
    ),
    "import.warning.extraction_scope": (
        "Seul le texte extrait affiché ici est traité. Un contenu absent affecte la "
        "complétude du document ; il n'est pas inclus dans la requête IA. Relisez et "
        "pseudonymisez tout texte ajouté avant de l'envoyer."
    ),
}
