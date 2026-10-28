"""Textes de la page Method & limits pour un lecteur sans formation technique, partie 2.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets (lexique, bonnes pratiques, langues des
documents, méthode de mesure et lien vers les résultats détaillés), fusionnés par app.i18n.
Place dans le pipeline : lu par app.i18n ; affiché par app/pages/method.py.
"""

EN: dict[str, str] = {
    "method.glossary.title": "Words used in HuisClos",
    "method.glossary.pseudonymization": (
        "**Pseudonymization.** Replacing what identifies a person with a label, while keeping "
        "a separate list that allows going back. The data remain personal data under the GDPR."
    ),
    "method.glossary.anonymization": (
        "**Anonymization.** Making identification impossible for anyone, for good. HuisClos "
        "does not do this: the mapping table allows going back, and the context may betray "
        "the person."
    ),
    "method.glossary.token": (
        "**Token.** The neutral label that takes the place of a value, such as `[PERSONNE_1]` "
        "or `[SOCIETE_A]`. The same person keeps the same token everywhere in the document."
    ),
    "method.glossary.mapping": (
        "**Mapping table.** The list that links each token to its real value. It is the key "
        "of the lock: whoever holds it can read the original. Keep it like the file itself."
    ),
    "method.glossary.llm": (
        "**Language model (LLM).** The AI behind tools such as ChatGPT, Claude or Mistral. It "
        "writes text from the text it receives. HuisClos never sends it the mapping table."
    ),
    "method.glossary.ner": (
        "**Named entity recognition (NER).** A technique that finds names of persons, "
        "organisations or places in a sentence, by learning from many annotated examples "
        "rather than from a fixed list."
    ),
    "method.glossary.score": (
        "**Confidence score and threshold.** Each detection receives a score between 0 and 1. "
        "Detections below the threshold (0.30 by default) are not proposed. A lower threshold "
        "masks more, with more false alarms."
    ),
    "method.glossary.metrics": (
        "**Recall and precision.** Recall is the share of the sensitive values that the tool "
        "finds; precision is the share of its detections that are right. For secrecy, recall "
        "counts most: a missed name is a breach, an extra word masked is only a nuisance."
    ),
    "method.practices.title": "Good practices",
    "method.practices.1": "Read every detection in the Review step before pseudonymizing.",
    "method.practices.2": (
        "Add by hand what the tool missed: a nickname, a rare job title, a small village, an "
        "internal reference."
    ),
    "method.practices.3": (
        "Read the full message, including your instruction, before you send it. Never write "
        "a client name in the instruction."
    ),
    "method.practices.4": (
        "Never send the mapping table to an AI tool, by email or in a chat. Store it with the "
        "client file and delete it when it is no longer needed."
    ),
    "method.practices.5": (
        "Check the settings of your AI tool account: some services may use your "
        "conversations to train their models."
    ),
    "method.practices.6": (
        "Use the public demo with fictitious data only. For real files, install HuisClos on "
        "your own computer."
    ),
    "method.testing.title": "How we tested it",
    "method.testing.corpus": (
        "**Fictitious documents written for the test.** Legal documents about invented "
        "people and companies were written for the project, in French and in English, and "
        "every value that must be masked was marked in advance. No real client data was used."
    ),
    "method.testing.protocol": (
        "**Separate sets to avoid fooling ourselves.** One set served to adjust the rules. "
        "Other sets were kept closed and measured only once per milestone, so that the tool "
        "could not be tuned to the answers. A last set was written blind, after the rules "
        "were frozen."
    ),
    "method.testing.results": (
        "**What the measures say.** On the last blind French set (8 documents, 190 sensitive "
        "values), the Standard profile fully masked 157 values before human review and the "
        "Enhanced profile 170. The rest was partly or not masked: the human review is "
        "therefore necessary, not a formality. English remains experimental."
    ),
    "method.testing.link": "See the detailed results",
    "method.languages.title": "Document languages",
    "method.languages.supported": (
        "**French and English documents.** You choose the language of the document in the "
        "sidebar. It selects the rules and the local language model (spaCy French or English). "
        "It is separate from the interface language and from the token style; a language is "
        "not a country or a court system."
    ),
    "method.languages.profiles": (
        "**Profiles.** Standard uses rules, spaCy and propagation in both languages. "
        "Enhanced adds CamemBERT for French or GLiNER for English, in a local "
        "installation only. Models are never downloaded by the application. Both "
        "Enhanced profiles remain experimental; after gate G8, Enhanced English is not "
        "recommended because its precision loss exceeded the pre-registered margin."
    ),
    "method.languages.limits": (
        "**Limits.** Published evaluation tables remain historical French measures. "
        "English uses a small spaCy model; local dev comparisons are documented in "
        "LOCAL_MODELS.md and do not validate generalisation. Gate G8 measured English "
        "once on a small fictional blind set, with a NO-GO verdict. Review every result."
    ),
}

FR: dict[str, str] = {
    "method.glossary.title": "Les mots de HuisClos",
    "method.glossary.pseudonymization": (
        "**Pseudonymisation.** Remplacer ce qui identifie une personne par une étiquette, en "
        "gardant à part une liste qui permet de revenir en arrière. Les données restent des "
        "données personnelles au sens du RGPD."
    ),
    "method.glossary.anonymization": (
        "**Anonymisation.** Rendre l'identification impossible pour quiconque, de façon "
        "définitive. HuisClos ne fait pas cela : la table de correspondance permet le retour "
        "en arrière, et le contexte peut trahir la personne."
    ),
    "method.glossary.token": (
        "**Jeton.** L'étiquette neutre qui prend la place d'une valeur, comme `[PERSONNE_1]` "
        "ou `[SOCIETE_A]`. Une même personne garde le même jeton dans tout le document."
    ),
    "method.glossary.mapping": (
        "**Table de correspondance.** La liste qui relie chaque jeton à sa vraie valeur. "
        "C'est la clé du cadenas : qui la détient peut lire l'original. Conservez-la comme "
        "le dossier lui-même."
    ),
    "method.glossary.llm": (
        "**Modèle de langage (LLM).** L'IA derrière des outils comme ChatGPT, Claude ou "
        "Mistral. Il écrit du texte à partir du texte qu'il reçoit. HuisClos ne lui envoie "
        "jamais la table de correspondance."
    ),
    "method.glossary.ner": (
        "**Reconnaissance d'entités nommées (NER).** Une technique qui repère les noms de "
        "personnes, d'organisations ou de lieux dans une phrase, en apprenant sur de nombreux "
        "exemples annotés plutôt qu'à partir d'une liste fixe."
    ),
    "method.glossary.score": (
        "**Score de confiance et seuil.** Chaque détection reçoit un score entre 0 et 1. Les "
        "détections sous le seuil (0,30 par défaut) ne sont pas proposées. Un seuil plus bas "
        "masque davantage, avec plus de fausses alertes."
    ),
    "method.glossary.metrics": (
        "**Rappel et précision.** Le rappel est la part des valeurs sensibles que l'outil "
        "trouve ; la précision est la part de ses détections qui sont justes. Pour le secret, "
        "le rappel compte le plus : un nom oublié est une violation, un mot masqué en trop "
        "n'est qu'une gêne."
    ),
    "method.practices.title": "Bonnes pratiques",
    "method.practices.1": "Relisez chaque détection à l'étape Vérifier avant de pseudonymiser.",
    "method.practices.2": (
        "Ajoutez à la main ce que l'outil a manqué : un surnom, un métier rare, un petit "
        "village, une référence interne."
    ),
    "method.practices.3": (
        "Relisez le message complet, consigne comprise, avant de l'envoyer. N'écrivez jamais "
        "le nom d'un client dans la consigne."
    ),
    "method.practices.4": (
        "N'envoyez jamais la table de correspondance à un outil d'IA, par courriel ou par "
        "messagerie. Rangez-la avec le dossier client et supprimez-la quand elle ne sert plus."
    ),
    "method.practices.5": (
        "Vérifiez les réglages de votre compte d'outil d'IA : certains services peuvent "
        "utiliser vos conversations pour entraîner leurs modèles."
    ),
    "method.practices.6": (
        "Utilisez la démonstration publique avec des données fictives seulement. Pour de "
        "vrais dossiers, installez HuisClos sur votre propre ordinateur."
    ),
    "method.testing.title": "Comment nous l'avons testé",
    "method.testing.corpus": (
        "**Des documents fictifs écrits pour le test.** Des documents juridiques sur des "
        "personnes et des sociétés inventées ont été rédigés pour le projet, en français et "
        "en anglais, et chaque valeur à masquer a été marquée à l'avance. Aucune donnée "
        "réelle de client n'a servi."
    ),
    "method.testing.protocol": (
        "**Des lots séparés pour ne pas se tromper soi-même.** Un lot a servi à régler les "
        "règles. D'autres lots sont restés fermés et n'ont été mesurés qu'une fois par étape, "
        "pour que l'outil ne puisse pas être ajusté sur les réponses. Un dernier lot a été "
        "rédigé à l'aveugle, après le gel des règles."
    ),
    "method.testing.results": (
        "**Ce que disent les mesures.** Sur le dernier lot aveugle français (8 documents, "
        "190 valeurs sensibles), le profil Standard a entièrement masqué 157 valeurs avant la "
        "revue humaine, et le profil renforcé 170. Le reste était masqué en partie ou pas du "
        "tout : la revue humaine est donc nécessaire, pas une formalité. L'anglais reste "
        "expérimental."
    ),
    "method.testing.link": "Voir les résultats détaillés",
    "method.languages.title": "Langues des documents",
    "method.languages.supported": (
        "**Documents français et anglais.** Vous choisissez la langue du document dans la "
        "barre latérale. Elle choisit les règles et le modèle de langue local (spaCy français "
        "ou anglais). Elle est distincte de la langue de l'interface et du style des jetons ; "
        "une langue n'est ni un pays ni un système judiciaire."
    ),
    "method.languages.profiles": (
        "**Profils.** Standard associe r\u00e8gles, spaCy et propagation dans les deux "
        "langues. Le profil renforc\u00e9 ajoute CamemBERT en fran\u00e7ais ou GLiNER en "
        "anglais, en installation locale seulement. Aucun mod\u00e8le n'est "
        "t\u00e9l\u00e9charg\u00e9 par "
        "l'application. Les deux profils renforc\u00e9s restent exp\u00e9rimentaux ; "
        "apr\u00e8s G8, le profil renforc\u00e9 anglais n'est pas recommand\u00e9, car sa "
        "perte de pr\u00e9cision d\u00e9passe la marge pr\u00e9enregistr\u00e9e."
    ),
    "method.languages.limits": (
        "**Limites.** Les tableaux publi\u00e9s restent des mesures fran\u00e7aises "
        "historiques. L'anglais utilise un petit mod\u00e8le spaCy ; les comparaisons dev "
        "locales d\u00e9crites dans LOCAL_MODELS.md ne valident pas la g\u00e9n\u00e9ralisation. "
        "G8 a mesur\u00e9 l'anglais une fois sur un petit lot aveugle fictif, avec un verdict "
        "NO-GO. Relisez chaque r\u00e9sultat."
    ),
}
