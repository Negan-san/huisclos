"""Textes de la page Pseudonymize : étapes Import, Review et Restore.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : EN (anglais, obligatoire). FR sera ajouté quand les chaînes françaises existeront.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "import.title": "Import a document",
    "import.intro": (
        "Paste a text or upload a file. HuisClos then looks for names, companies, "
        "addresses, identifiers and dates."
    ),
    "import.empty": "No text yet. Paste a document, upload a file or load the sample case.",
    "import.sample.button": "Load sample case",
    "import.sample.notice": (
        "This is a fictitious case written for demonstration. Every name, number and "
        "address in it is invented."
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
        "This PDF has no selectable text, so it is probably a scan. Scanned documents "
        "are not supported."
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
    "review.title": "Review detections",
    "review.empty": "Nothing to review yet. Import a text and run the detection first.",
    "review.placeholder": (
        "{count} detections are ready. The review controls are not available in this build yet."
    ),
    "review.back": "Back to Import",
    "restore.title": "Restore real values",
    "restore.empty": "Nothing to restore yet. Complete the Import and Review steps first.",
    "restore.back": "Back to Import",
}
