"""Textes de la page Method & limits : méthode, cadre juridique et limites.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets, fusionnés par app.i18n.
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
        "**1. Read.** The document is read on this computer: pasted text, DOCX or text PDF."
    ),
    "method.how.2": (
        "**2. Detect.** Rules and a French language model find names, companies, addresses, "
        "identifiers and dates."
    ),
    "method.how.3": (
        "**3. Review.** You accept, reject or add detections. Nothing is replaced without your"
        " decision."
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
        "**6. Restore.** The mapping table puts the real values back into the answer of the AI"
        " tool."
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
        "send it anywhere. The Evaluation page reports the measured recall."
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
    "method.languages.title": "Document languages",
    "method.languages.supported": (
        "**French and English documents.** You choose the language of the document in the "
        "sidebar. It selects the rules and the local language model (spaCy French or English). "
        "It is separate from the interface language and from the token style; a language is "
        "not a country or a court system."
    ),
    "method.languages.profiles": (
        "**Profiles.** Standard uses rules, spaCy and propagation in both languages. Enhanced "
        "local detection adds the CamemBERT model, for French documents only and only in a "
        "local installation; the model is never downloaded by the application."
    ),
    "method.languages.limits": (
        "**Limits.** The published measures cover French documents only. English support uses "
        "a small spaCy model and has no published measure yet; read every English result "
        "with extra care."
    ),
    "method.disclaimer": "Decision-support tool, not legal advice.",
}

FR: dict[str, str] = {
    "method.title": "Méthode et limites",
    "method.intro": (
        "Comment HuisClos protège un dossier client, ce qu'il ne peut pas garantir et les "
        "règles qui le guident."
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
        "**1. Lire.** Le document est lu sur cet ordinateur : texte collé, DOCX ou PDF texte."
    ),
    "method.how.2": (
        "**2. Détecter.** Des règles et un modèle de langue française repèrent les noms, "
        "sociétés, adresses, identifiants et dates."
    ),
    "method.how.3": (
        "**3. Vérifier.** Vous acceptez, rejetez ou ajoutez des détections. Rien n'est "
        "remplacé sans votre décision."
    ),
    "method.how.4": (
        "**4. Pseudonymiser.** Chaque personne ou société reçoit un jeton stable comme "
        "`[PERSONNE_1]`. La table de correspondance reste sur cet ordinateur."
    ),
    "method.how.5": (
        "**5. Interroger l'IA.** Vous envoyez uniquement le texte pseudonymisé à l'outil d'IA "
        "de votre choix. La table de correspondance n'est jamais envoyée."
    ),
    "method.how.6": (
        "**6. Restaurer.** La table de correspondance remet les vraies valeurs dans la réponse"
        " de l'outil d'IA."
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
        "**Erreurs de détection.** Aucun détecteur ne trouve tout. Un nom oublié constitue une"
        " violation du secret. Relisez attentivement l'étape Vérifier et contrôlez le texte "
        "pseudonymisé avant tout envoi. La page Évaluation présente le rappel mesuré."
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
    "method.languages.title": "Langues des documents",
    "method.languages.supported": (
        "**Documents français et anglais.** Vous choisissez la langue du document dans la "
        "barre latérale. Elle choisit les règles et le modèle de langue local (spaCy français "
        "ou anglais). Elle est distincte de la langue de l'interface et du style des jetons ; "
        "une langue n'est ni un pays ni un système judiciaire."
    ),
    "method.languages.profiles": (
        "**Profils.** Standard utilise les règles, spaCy et la propagation dans les deux "
        "langues. La détection locale renforcée ajoute le modèle CamemBERT, pour les documents "
        "français seulement et en installation locale seulement ; l'application ne télécharge "
        "jamais le modèle."
    ),
    "method.languages.limits": (
        "**Limites.** Les mesures publiées ne portent que sur des documents français. Le "
        "support de l'anglais repose sur un petit modèle spaCy et n'a encore aucune mesure "
        "publiée : relisez chaque résultat anglais avec une attention particulière."
    ),
    "method.disclaimer": "Outil d'aide à la décision, sans valeur de conseil juridique.",
}
