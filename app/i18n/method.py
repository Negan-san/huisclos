"""Textes de la page Method & limits : méthode, cadre juridique et limites.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets, fusionnés par app.i18n.
Place dans le pipeline : lu par app.i18n, qui fusionne les dictionnaires de tous les modules.
"""

EN: dict[str, str] = {
    "method.title": "Method & limits",
    "method.intro": (
        "This page explains, in plain words, how HuisClos protects a client file before you "
        "use an AI tool: what happens at each step, which technologies do the work, what "
        "never leaves your computer, the legal rules behind the tool, and what it cannot "
        "guarantee."
    ),
    "method.diagram.title": "Pipeline",
    "method.diagram.alt": (
        "Pipeline diagram. On this computer: document, reading, detection, human review, "
        "pseudonymized text. Outside this computer, by your choice: the AI tool. Then back on "
        "this computer: restoration of the real values."
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
        "**1. Import.** You paste the text or open a file: Word (DOCX), PDF that contains "
        "text, or plain text. The file is read on this computer, by HuisClos itself. You "
        "can also load a fictitious sample case to try the tool."
    ),
    "method.how.2": (
        "**2. Detect.** HuisClos searches the text for names of persons and companies, "
        "addresses, email addresses, phone numbers, bank and social security numbers, "
        "company numbers, birth dates and case numbers. Rules find what has a fixed shape; a "
        "language model finds names from the context of the sentence. Each detection "
        "receives a confidence score."
    ),
    "method.how.3": (
        "**3. Review.** Every detection is highlighted in the text with its color and its "
        "type written next to it. You keep, reject or add values, including a value the tool "
        "missed. Nothing is replaced without your decision: the tool proposes, you decide."
    ),
    "method.how.4": (
        "**4. Pseudonymize.** Each validated value is replaced by a token such as "
        "`[PERSONNE_1]`. The same person keeps the same token in the whole document, even "
        "when the name is written in capitals or in a shorter form. HuisClos builds the "
        "mapping table that links each token to its real value; it stays on this computer."
    ),
    "method.how.5": (
        "**5. Ask the AI.** You write your question and HuisClos assembles the message: the "
        "pseudonymized text, then your instruction. A final check searches it for any real "
        "value left in clear. You then copy the message into the AI tool of your choice, or "
        "send it to Mistral if configured. The mapping table is never sent."
    ),
    "method.how.6": (
        "**6. Restore.** You paste the answer of the AI tool. HuisClos puts each real value "
        "back in place of its token, even when the AI tool changed its case or spacing, and "
        "lists the tokens it does not know. You can download the restored text as a text or "
        "Word file."
    ),
    "method.hybrid.title": "Why hybrid AI",
    "method.hybrid.rules": (
        "**Rules with check keys.** Identifiers such as the NIR, the IBAN, the SIREN and the "
        "SIRET carry a check key that a rule can verify. These detections are reliable and "
        "easy to explain. A number with a wrong key is still flagged with a low score, because"
        " a typing error is likely."
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
        "Recall comes first: a name that is missed breaches secrecy, while a word masked by "
        "mistake is only a nuisance. The confidence threshold lets you mask more or less. "
        "Every detection is shown with its type and its source, and you validate each one. The"
        " tool proposes, the lawyer decides."
    ),
    "method.types.title": "What HuisClos looks for",
    "method.types.intro": (
        "Each type has its own color and always a text label, so color is never the only signal."
    ),
    "method.legal.title": "Legal framework",
    "method.legal.secrecy": (
        "**Professional secrecy.** Law no. 71-1130 of 31 December 1971, art. 66-5: "
        "consultations, correspondence, interview notes and, more generally, every document of"
        " the case file are covered by professional secrecy. Penal Code, art. 226-13: "
        "revealing secret information held through one's profession is a criminal offense."
    ),
    "method.legal.gdpr": (
        "**GDPR.** Art. 4(5) defines pseudonymization: data can no longer be attributed to a "
        "person without additional information kept separately. Recital 26: pseudonymized data"
        " remain personal data. Art. 5(1)(c): data minimization. Art. 32: security of "
        "processing, which names pseudonymization as a measure."
    ),
    "method.legal.cnb": (
        "**Professional guidance.** The Conseil national des barreaux published a guide on "
        "professional ethics and artificial intelligence in March 2026. Read it alongside this"
        " tool."
    ),
    "method.limits.title": "Limits",
    "method.limits.context": (
        "**Re-identification by context.** Masking names does not hide the story. A rare job "
        "title, a small town, a date and a court can let a reader identify the person. "
        "Pseudonymized text is still personal data."
    ),
    "method.limits.errors": (
        "**Detection errors.** No detector finds everything. A missed name is a breach of "
        "secrecy. Read the Review step carefully and check the pseudonymized text before you "
        'send it anywhere. The section "How we tested it" below gives the measured results.'
    ),
    "method.limits.tokens": (
        "**Tokens altered by the AI tool.** The AI tool may rewrite, translate or drop a "
        "token. Restoration accepts the common variants but cannot recover a token that was "
        "removed. HuisClos lists unknown and missing tokens so that you can check them."
    ),
    "method.limits.demo": (
        "**Online demo.** The online demo is for fictitious data only. On a hosted server, the"
        " text passes through the machine of the host. To process real client files, install "
        "HuisClos on your computer (see the user guide)."
    ),
    "method.disclaimer": "Decision-support tool, not legal advice.",
}

FR: dict[str, str] = {
    "method.title": "Méthode et limites",
    "method.intro": (
        "Cette page explique simplement comment HuisClos protège un dossier client avant "
        "l'utilisation d'un outil d'IA : ce qui se passe à chaque étape, quelles "
        "technologies font le travail, ce qui ne quitte jamais votre ordinateur, les règles "
        "juridiques qui guident l'outil et ce qu'il ne peut pas garantir."
    ),
    "method.diagram.title": "Pipeline",
    "method.diagram.alt": (
        "Schéma du pipeline. Sur cet ordinateur : document, lecture, détection, revue humaine,"
        " texte pseudonymisé. Hors de cet ordinateur, à votre choix : outil d'IA. Puis retour "
        "sur cet ordinateur : restauration des vraies valeurs."
    ),
    "method.diagram.document": "Document",
    "method.diagram.read": "Lecture locale",
    "method.diagram.detect": "Détection\\n(règles + NER)",
    "method.diagram.review": "Revue humaine",
    "method.diagram.pseudonymize": "Texte pseudonymisé\\n+ table de correspondance",
    "method.diagram.llm": "Outil d'IA\\n(votre choix)",
    "method.diagram.restore": "Restauration",
    "method.diagram.result": "Document restauré",
    "method.diagram.mapping": "table de correspondance",
    "method.diagram.local": "Sur cet ordinateur",
    "method.diagram.remote": "À l'extérieur",
    "method.how.title": "Fonctionnement",
    "method.how.1": (
        "**1. Importer.** Vous collez le texte ou ouvrez un fichier : Word (DOCX), PDF "
        "contenant du texte ou texte brut. Le fichier est lu sur cet ordinateur, par HuisClos "
        "lui-même. Vous pouvez aussi charger un cas fictif pour essayer l'outil."
    ),
    "method.how.2": (
        "**2. Détecter.** HuisClos cherche dans le texte les noms de personnes et de "
        "sociétés, les adresses, courriels, téléphones, numéros bancaires et de sécurité "
        "sociale, numéros d'entreprise, dates de naissance et numéros de dossier. Des règles "
        "trouvent ce qui a une forme fixe ; un modèle de langue trouve les noms d'après le "
        "contexte de la phrase. Chaque détection reçoit un score de confiance."
    ),
    "method.how.3": (
        "**3. Vérifier.** Chaque détection est surlignée dans le texte avec sa couleur et "
        "son type écrit à côté. Vous gardez, rejetez ou ajoutez des valeurs, y compris une "
        "valeur oubliée par l'outil. Rien n'est remplacé sans votre décision : l'outil "
        "propose, vous décidez."
    ),
    "method.how.4": (
        "**4. Pseudonymiser.** Chaque valeur validée est remplacée par un jeton comme "
        "`[PERSONNE_1]`. Une même personne garde le même jeton dans tout le document, même "
        "écrite en majuscules ou sous une forme courte. HuisClos construit la table de "
        "correspondance qui relie chaque jeton à sa vraie valeur ; elle reste sur cet "
        "ordinateur."
    ),
    "method.how.5": (
        "**5. Interroger l'IA.** Vous écrivez votre question et HuisClos compose le message "
        ": le texte pseudonymisé, puis votre consigne. Un contrôle final y cherche toute "
        "vraie valeur restée en clair. Vous copiez ensuite le message dans l'outil d'IA de "
        "votre choix, ou l'envoyez à Mistral s'il est configuré. La table de correspondance "
        "n'est jamais envoyée."
    ),
    "method.how.6": (
        "**6. Restaurer.** Vous collez la réponse de l'outil d'IA. HuisClos remet chaque "
        "vraie valeur à la place de son jeton, même si l'outil d'IA en a changé la casse ou "
        "les espaces, et liste les jetons qu'il ne connaît pas. Vous pouvez télécharger le "
        "texte restauré en fichier texte ou Word."
    ),
    "method.hybrid.title": "Pourquoi une IA hybride",
    "method.hybrid.rules": (
        "**Règles avec clés de contrôle.** Des identifiants comme le NIR, l'IBAN, le SIREN et "
        "le SIRET portent une clé qu'une règle peut vérifier. Ces détections sont fiables et "
        "faciles à expliquer. Un numéro à clé invalide est tout de même signalé avec un score "
        "faible, car une erreur de saisie est probable."
    ),
    "method.hybrid.ner": (
        "**NER préentraîné.** Un modèle de langue française (spaCy) reconnaît les noms et les "
        "organisations dans leur contexte, sans motif fixe. Il fonctionne sur cet ordinateur "
        "et ne donne pas de probabilité ; chaque entité trouvée reçoit donc le même score."
    ),
    "method.hybrid.propagation": (
        "**Propagation.** Une fois un nom trouvé, ses autres mentions dans le document (formes"
        " courtes, majuscules) sont aussi recherchées, pour masquer partout un nom détecté une"
        " fois."
    ),
    "method.human.title": "L'humain dans la boucle",
    "method.human.text": (
        "Le rappel est prioritaire : un nom oublié viole le secret, un mot masqué par erreur "
        "est une gêne. Le seuil de confiance permet de masquer davantage ou moins. Chaque "
        "détection est affichée avec son type et sa source, et vous validez chacune. L'outil "
        "propose, le juriste décide."
    ),
    "method.types.title": "Ce que HuisClos recherche",
    "method.types.intro": (
        "Chaque type a sa couleur et toujours un libellé texte : la couleur n'est jamais le "
        "seul signal."
    ),
    "method.legal.title": "Cadre juridique",
    "method.legal.secrecy": (
        "**Secret professionnel.** Loi n° 71-1130 du 31 décembre 1971, art. 66-5 : les "
        "consultations, correspondances, notes d'entretien et, plus généralement, toutes les "
        "pièces du dossier sont couvertes par le secret professionnel. Code pénal, art. 226-13"
        " : révéler une information secrète détenue dans le cadre de sa profession constitue "
        "une infraction pénale."
    ),
    "method.legal.gdpr": (
        "**RGPD.** L'art. 4(5) définit la pseudonymisation : les données ne peuvent plus être "
        "attribuées à une personne sans information supplémentaire conservée séparément. "
        "Considérant 26 : les données pseudonymisées restent des données personnelles. Art. "
        "5(1)(c) : minimisation des données. Art. 32 : sécurité du traitement, qui cite la "
        "pseudonymisation comme mesure."
    ),
    "method.legal.cnb": (
        "**Recommandations professionnelles.** Le Conseil national des barreaux a publié un "
        "guide sur la déontologie et l'intelligence artificielle en mars 2026. Consultez-le en"
        " complément de cet outil."
    ),
    "method.limits.title": "Limites",
    "method.limits.context": (
        "**Réidentification par le contexte.** Masquer les noms ne cache pas l'histoire. Un "
        "métier rare, une petite ville, une date et une juridiction peuvent permettre "
        "d'identifier la personne. Le texte pseudonymisé reste une donnée personnelle."
    ),
    "method.limits.errors": (
        "**Erreurs de détection.** Aucun détecteur ne trouve tout. Un nom oublié constitue "
        "une violation du secret. Relisez attentivement l'étape Vérifier et contrôlez le "
        'texte pseudonymisé avant tout envoi. La section "Comment nous l\'avons testé" '
        "ci-dessous donne les résultats mesurés."
    ),
    "method.limits.tokens": (
        "**Jetons modifiés par l'outil d'IA.** L'outil d'IA peut réécrire, traduire ou "
        "supprimer un jeton. La restauration accepte les variantes courantes mais ne récupère "
        "pas un jeton supprimé. HuisClos liste les jetons inconnus et absents pour permettre "
        "leur vérification."
    ),
    "method.limits.demo": (
        "**Démonstration en ligne.** La démonstration en ligne est réservée aux données "
        "fictives. Sur un serveur hébergé, le texte passe par la machine de l'hébergeur. Pour "
        "traiter de vrais dossiers clients, installez HuisClos sur votre ordinateur (voir le "
        "guide utilisateur)."
    ),
    "method.disclaimer": "Outil d'aide à la décision, sans valeur de conseil juridique.",
}
