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
    "restore.empty": (
        "Nothing to restore yet. Complete the Import and Review steps first, or load a saved "
        "mapping table below."
    ),
    "restore.back": "Back to Import",
    "restore.back_review": "Back to Review",
    "restore.send.heading": "Send to your AI tool",
    "restore.send.intro": (
        "Copy this text into the AI tool of your choice. Names and identifiers are replaced "
        "by tokens such as `[PERSONNE_1]`."
    ),
    "restore.send.literal_tokens": (
        "The input text already contains token-like strings. Check the restored text: "
        "they may be confused with the tokens created by HuisClos."
    ),
    "restore.send.leaves": (
        "What leaves your computer: only the text above. The mapping table stays here."
    ),
    "restore.send.check": (
        "Read the text once more before sending it. A value that was not masked leaves your "
        "computer in clear."
    ),
    "restore.send.counts.heading": "Tokens in this text",
    "restore.send.counts.type": "Type",
    "restore.send.counts.tokens": "Tokens",
    "restore.send.counts.occurrences": "Occurrences",
    "restore.send.instruction.heading": "Recommended instruction",
    "restore.send.instruction.help": (
        "Paste one of these lines with the text, so that the AI tool keeps the tokens unchanged."
    ),
    "restore.send.instruction.fr.label": "In French",
    "restore.send.instruction.fr": (
        "Conserve exactement chaque jeton entre crochets, par exemple [PERSONNE_1], sans le "
        "modifier ni le traduire, et n'en invente aucun."
    ),
    "restore.send.instruction.en.label": "In English",
    "restore.send.instruction.en": (
        "Keep every bracketed token exactly as written, for example [PERSON_1]; do not "
        "change, translate or invent tokens."
    ),
    "restore.answer.heading": "Restore the AI answer",
    "restore.answer.label": "Answer from the AI tool",
    "restore.answer.placeholder": "Paste the answer of the AI tool here.",
    "restore.answer.button": "Restore",
    "restore.answer.empty": "Paste the answer of the AI tool first.",
    "restore.answer.restored_heading": "Restored text",
    "restore.mode.exact": (
        "Exact mode: this is the pseudonymized text itself, so every value comes back as it "
        "was written."
    ),
    "restore.mode.tolerant": (
        "Tolerant mode: each token is replaced by the main form of its value. A variant "
        "written differently in the original, such as a name in capitals, comes back in "
        "the main form."
    ),
    "restore.none_found": "No token was found in this answer, so nothing was restored.",
    "restore.unknown": (
        "Unknown tokens were left unchanged ({count}): {forms}. The AI tool may have invented "
        "them, or the mapping table belongs to another document."
    ),
    "restore.altered": (
        "Altered tokens were recognized and restored ({count}): {pairs}. The AI tool wrote "
        "them differently from the original. Check these places."
    ),
    "restore.altered.pair": "{found} read as {token}",
    "restore.missing": "Tokens of the table not found in the answer: {tokens}.",
    "restore.table.heading": "Use a saved mapping table (optional)",
    "restore.table.help": (
        "To restore an answer received later, upload the .mapping.json file downloaded "
        "earlier. It is read on this computer and replaces the table of the current document."
    ),
    "restore.table.upload": "Mapping table (.json)",
    "restore.table.in_use_document": "Table in use: the one built from the current document.",
    "restore.table.in_use_file": "Table in use: the file {name}.",
    "restore.table.error.encoding": (
        "This file is not readable text. Upload the .mapping.json file exactly as HuisClos "
        "saved it."
    ),
    "restore.table.error.invalid": (
        "This file is not a valid HuisClos mapping table. Upload the .mapping.json file "
        "exactly as HuisClos saved it."
    ),
    "restore.download.heading": "Download",
    "restore.download.pseudonymized_txt": "Pseudonymized text (.txt)",
    "restore.download.pseudonymized_docx": "Pseudonymized text (.docx)",
    "restore.download.restored_txt": "Restored text (.txt)",
    "restore.download.restored_docx": "Restored text (.docx)",
    "restore.download.restored_wait": "Restore an answer first to download the restored text.",
    "restore.download.mapping": "Mapping table (.mapping.json)",
    "restore.download.mapping.warning": (
        "Sensitive file: it links tokens to real identities. Keep it on this computer. "
        "Never send it to an AI tool."
    ),
    "restore.docx.title.pseudonymized": "Pseudonymized text",
    "restore.docx.title.restored": "Restored text",
    "restore.new.button": "Start a new document",
    "restore.new.note": (
        "HuisClos does not keep the mapping table. Download it first if you need to restore "
        "an answer later."
    ),
    "restore.new.confirm": (
        "Start a new document? The text, the detections, the pseudonymized text and the "
        "restored text are erased from this session. HuisClos does not keep the mapping "
        "table, so it cannot be recovered afterwards."
    ),
    "restore.new.yes": "Yes, start a new document",
    "restore.new.cancel": "Cancel",
}
