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
    "review.intro": (
        "You decide what is masked. Uncheck a row to keep a value in clear, change its type "
        "if it is wrong, and add any value the detection missed. A forgotten name is a "
        "breach of professional secrecy, a name masked by mistake is only a nuisance."
    ),
    "review.summary": "{count} detections are ready for review, grouped into {groups} entities.",
    "review.counts.heading": "Counts",
    "review.counts.masked": "Masked occurrences",
    "review.counts.rejected": "Rejected occurrences",
    "review.counts.groups": "Entities",
    "review.counts.type": "Type",
    "review.counts.type_masked": "Masked",
    "review.counts.type_rejected": "Rejected",
    "review.text.heading": "Highlighted text",
    "review.text.legend": "Legend",
    "review.table.heading": "Entities",
    "review.table.help": (
        "One row per entity, whatever the number of times it appears. Unchecking Mask "
        "rejects every occurrence; changing the Type applies to all of them."
    ),
    "review.table.nothing": "No entity of the selected types.",
    "review.filter.label": "Show only these types",
    "review.column.mask": "Mask",
    "review.column.text": "Text",
    "review.column.type": "Type",
    "review.column.occurrences": "Occurrences",
    "review.column.variants": "Variants",
    "review.column.confidence": "Confidence",
    "review.column.source": "Source",
    "review.column.note": "Note",
    "review.variants.more": "+{count} more",
    "review.note.ambiguous": "Check: may refer to another person",
    "review.tag.PERSON": "PERSON",
    "review.tag.ORGANIZATION": "COMPANY",
    "review.tag.ADDRESS": "ADDRESS",
    "review.tag.EMAIL": "EMAIL",
    "review.tag.PHONE": "PHONE",
    "review.tag.IBAN": "IBAN",
    "review.tag.NIR": "NIR",
    "review.tag.SIREN": "SIREN",
    "review.tag.SIRET": "SIRET",
    "review.tag.BIRTH_DATE": "BIRTH DATE",
    "review.tag.CASE_NUMBER": "CASE",
    "review.tag.LOCATION": "PLACE",
    "review.tag.CUSTOM": "OTHER",
    "review.rejected": "REJECTED",
    "review.hover": "{kind}, score {score}, source {source}",
    "review.hover.rejected": "{kind}, score {score}, source {source}, rejected by you",
    "review.manual.heading": "Add a value the detection missed",
    "review.manual.text": "Value to mask",
    "review.manual.type": "Type of this value",
    "review.manual.custom": "Other identifier",
    "review.manual.button": "Add and mask everywhere",
    "review.manual.empty": "Type the value to mask first.",
    "review.manual.none": (
        "This value does not appear in the text. Check the spelling; upper and lower case "
        "and accents are ignored."
    ),
    "review.manual.covered": (
        "All {covered} occurrences are already inside a masked value, so nothing was added."
    ),
    "review.manual.added": "Added {count} occurrences. They are masked everywhere in the text.",
    "review.manual.added_covered": (
        "Added {count} occurrences. {covered} more were already inside a masked value."
    ),
    "review.nothing_masked": (
        "No value is masked, so the pseudonymized text would be identical to the original. "
        "Check at least one row or add a value."
    ),
    "review.pseudonymize": "Pseudonymize",
    "review.pseudonymize.spinner": "Replacing the masked values with tokens.",
    "review.pseudonymize.note": (
        "The correspondence table stays on this computer. Only the pseudonymized text is "
        "meant to be sent to a language model."
    ),
    "review.error.pseudonymize": (
        "The text could not be pseudonymized because two detections overlap. Go back to "
        "Import and run the detection again."
    ),
    "review.back": "Back to Import",
    "restore.title": "Restore real values",
    "restore.empty": "Nothing to restore yet. Complete the Import and Review steps first.",
    "restore.back": "Back to Import",
}
