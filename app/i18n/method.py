"""Textes de la page Method & limits : méthode, cadre juridique et limites.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : EN (anglais, obligatoire). FR sera ajouté quand les chaînes françaises existeront.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "method.title": "Method & limits",
    "method.intro": (
        "How HuisClos protects a client file, what it cannot guarantee, and the rules behind it."
    ),
    "method.diagram.title": "Pipeline",
    "method.diagram.alt": (
        "Pipeline diagram. On this computer: document, reading, detection, human review, "
        "pseudonymized text. Outside this computer, by your choice: the AI tool. Then back "
        "on this computer: restoration of the real values."
    ),
    "method.diagram.document": "Document",
    "method.diagram.read": "Local reading",
    "method.diagram.detect": "Detection\\n(rules + NER)",
    "method.diagram.review": "Human review",
    "method.diagram.pseudonymize": "Pseudonymized text\\n+ mapping table",
    "method.diagram.llm": "AI tool\\n(your choice)",
    "method.diagram.restore": "Restoration",
    "method.diagram.result": "Restored document",
    "method.diagram.mapping": "mapping table",
    "method.diagram.local": "On this computer",
    "method.diagram.remote": "Outside",
    "method.how.title": "How it works",
    "method.how.1": (
        "**1. Read.** The document is read on this computer: pasted text, DOCX or text PDF."
    ),
    "method.how.2": (
        "**2. Detect.** Rules and a French language model find names, companies, "
        "addresses, identifiers and dates."
    ),
    "method.how.3": (
        "**3. Review.** You accept, reject or add detections. Nothing is replaced "
        "without your decision."
    ),
    "method.how.4": (
        "**4. Pseudonymize.** Each person or company gets a stable token such as "
        "`[PERSONNE_1]`. The mapping table stays on this computer."
    ),
    "method.how.5": (
        "**5. Ask the AI.** You send only the pseudonymized text to the AI tool of your "
        "choice. The mapping table is never sent."
    ),
    "method.how.6": (
        "**6. Restore.** The mapping table puts the real values back into the answer of "
        "the AI tool."
    ),
    "method.hybrid.title": "Why hybrid AI",
    "method.hybrid.rules": (
        "**Rules with check keys.** Identifiers such as the NIR, the IBAN, the SIREN and "
        "the SIRET carry a check key that a rule can verify. These detections are reliable "
        "and easy to explain. A number with a wrong key is still flagged with a low score, "
        "because a typing error is likely."
    ),
    "method.hybrid.ner": (
        "**Pre-trained NER.** A French language model (spaCy) recognizes names and "
        "organizations from their context, where no fixed pattern exists. It runs on this "
        "computer and gives no probability, so every entity it finds receives the same score."
    ),
    "method.hybrid.propagation": (
        "**Propagation.** Once a name is found, its other mentions in the document (short "
        "forms, capital letters) are found too, so a name detected once is masked everywhere."
    ),
    "method.human.title": "Human in the loop",
    "method.human.text": (
        "Recall comes first: a name that is missed breaches secrecy, while a word masked "
        "by mistake is only a nuisance. The confidence threshold lets you mask more or "
        "less. Every detection is shown with its type and its source, and you validate "
        "each one. The tool proposes, the lawyer decides."
    ),
    "method.types.title": "What HuisClos looks for",
    "method.types.intro": (
        "Each type has its own color and always a text label, so color is never the only signal."
    ),
    "method.legal.title": "Legal framework",
    "method.legal.secrecy": (
        "**Professional secrecy.** Law no. 71-1130 of 31 December 1971, art. 66-5: "
        "consultations, correspondence, interview notes and, more generally, every document "
        "of the case file are covered by professional secrecy. Penal Code, art. 226-13: "
        "revealing secret information held through one's profession is a criminal offense."
    ),
    "method.legal.gdpr": (
        "**GDPR.** Art. 4(5) defines pseudonymization: data can no longer be attributed to "
        "a person without additional information kept separately. Recital 26: pseudonymized "
        "data remain personal data. Art. 5(1)(c): data minimization. Art. 32: security of "
        "processing, which names pseudonymization as a measure."
    ),
    "method.legal.cnb": (
        "**Professional guidance.** The Conseil national des barreaux published a guide on "
        "professional ethics and artificial intelligence in March 2026. Read it alongside "
        "this tool."
    ),
    "method.limits.title": "Limits",
    "method.limits.context": (
        "**Re-identification by context.** Masking names does not hide the story. A rare "
        "job title, a small town, a date and a court can let a reader identify the person. "
        "Pseudonymized text is still personal data."
    ),
    "method.limits.errors": (
        "**Detection errors.** No detector finds everything. A missed name is a breach of "
        "secrecy. Read the Review step carefully and check the pseudonymized text before "
        "you send it anywhere. The Evaluation page reports the measured recall."
    ),
    "method.limits.tokens": (
        "**Tokens altered by the AI tool.** The AI tool may rewrite, translate or drop a "
        "token. Restoration accepts the common variants but cannot recover a token that "
        "was removed. HuisClos lists unknown and missing tokens so that you can check them."
    ),
    "method.limits.demo": (
        "**Online demo.** The online demo is for fictitious data only. On a hosted server, "
        "the text passes through the machine of the host. To process real client files, "
        "install HuisClos on your computer (see the user guide)."
    ),
    "method.disclaimer": "Decision-support tool, not legal advice.",
}
