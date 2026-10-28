"""Textes de la page Method & limits pour un lecteur sans formation technique, partie 1.

Entrées : aucune ; le module ne contient que des dictionnaires de textes.
Sorties : dictionnaires EN et FR complets (résumé, exemple commenté, circulation des données,
technologies employées), fusionnés par app.i18n.
Place dans le pipeline : lu par app.i18n ; affiché par app/pages/method.py.
"""

EN: dict[str, str] = {
    "method.summary.title": "In short",
    "method.summary.problem": (
        "**The problem.** AI tools such as ChatGPT, Claude or Mistral can summarise a file, "
        "draft a letter or list the arguments of a case. But the text you paste into them "
        "leaves your computer and is processed on the servers of a company. For a lawyer, "
        "sending the names, addresses or identifiers of a client to such a service can breach "
        "professional secrecy."
    ),
    "method.summary.solution": (
        "**What HuisClos does.** Before the text leaves your computer, HuisClos finds the "
        "information that identifies people and companies and replaces each one with a neutral "
        "label, called a token, such as `[PERSONNE_1]`. You send this masked text to the AI "
        "tool. When the answer comes back, HuisClos puts the real names back in their place. "
        "The list that links each token to its real value never leaves your computer."
    ),
    "method.summary.limits": (
        "**What it does not do.** HuisClos does not make a text anonymous: the facts of the "
        "story stay readable, and a reader who knows the case may still recognise it. It can "
        "also miss a name. That is why you check every detection, and why the tool shows its "
        "limits openly on this page."
    ),
    "method.diagram.how_to_read": (
        'How to read this diagram: everything inside the frame "On this computer" stays on '
        "your machine. Only the pseudonymized text crosses to the AI tool, and only when you "
        "decide to send it. The dashed arrow is the mapping table: it goes directly from "
        "pseudonymization to restoration and never passes through the AI tool."
    ),
    "method.example.title": "A worked example",
    "method.example.intro": (
        "A simplified illustration with a fictitious client. The four boxes follow the text "
        "from the original file to the restored answer."
    ),
    "method.example.original_label": "**1. Your document (stays on your computer)**",
    "method.example.original": (
        "Ms Claire Dumontel, born on 4 March 1981, lives at 12 rue des Lilas, 69003 Lyon. Her "
        "employer, Batiplus SARL, dismissed her on 2 June 2026. Contact: "
        "claire.dumontel@example.com."
    ),
    "method.example.sent_label": "**2. What the AI tool receives**",
    "method.example.sent": (
        "Ms [PERSONNE_1], born on [DATE_NAISSANCE_1], lives at [ADRESSE_1]. Her employer, "
        "[SOCIETE_A], dismissed her on 2 June 2026. Contact: [EMAIL_1].\n\n"
        "Instruction: Summarise the facts in two sentences."
    ),
    "method.example.answer_label": "**3. The answer of the AI tool**",
    "method.example.answer": (
        "[PERSONNE_1] was dismissed by [SOCIETE_A] on 2 June 2026. She can challenge the "
        "dismissal before the labour court."
    ),
    "method.example.restored_label": "**4. The restored answer (on your computer)**",
    "method.example.restored": (
        "Claire Dumontel was dismissed by Batiplus SARL on 2 June 2026. She can challenge the "
        "dismissal before the labour court."
    ),
    "method.example.note": (
        'Points to notice: the title "Ms" stays outside the token, so the AI tool can still '
        "write grammatical sentences. The dismissal date is not masked: HuisClos masks birth "
        "dates, not every date, because dates are often needed to reason about a case. The AI "
        "tool never sees the real name, yet the final answer contains it. Tokens can also be "
        "written in English style ([PERSON_1], [COMPANY_A]) through the sidebar."
    ),
    "method.data.title": "What leaves your computer, and what does not",
    "method.data.stays": (
        "**Stays on your computer.** The original document, the list of detections, your "
        "review decisions, the mapping table and the restored answer. HuisClos keeps them in "
        "memory while the page is open and writes nothing to disk unless you click a download "
        "button."
    ),
    "method.data.leaves": (
        "**Leaves only by your action.** The pseudonymized text and your instruction, once you "
        "copy them into an AI tool or, if you have configured it, send them to Mistral with an "
        "explicit confirmation. Nothing is sent automatically."
    ),
    "method.data.check": (
        "**A last check before sending.** Just before you copy the message, a final check "
        "searches it again for every real value of the mapping table, for a surname left "
        "alone, and for names in your own instruction. As long as an alert is open, copy and "
        "download stay disabled. You decide: mask the value, edit your instruction, or keep "
        "the mention after reading it in context."
    ),
    "method.data.offline": (
        "**No hidden connection.** In a local installation, the application makes no call to "
        "the Internet: no web font, no external script, no usage statistics. An automated test "
        "checks this at every change of the code. The language models are installed once, in "
        "advance, and never downloaded by the application."
    ),
    "method.tech.title": "Technologies used",
    "method.tech.intro": (
        "HuisClos assembles well-known open-source components. None of them needs an account "
        "or an Internet connection, except the optional Mistral connector."
    ),
    "method.tech.table": (
        "| Component | What it does in HuisClos |\n"
        "| --- | --- |\n"
        "| Python 3.12 | The programming language of the whole tool. |\n"
        "| Streamlit | Builds the interface you are using, as a web page served by your own "
        "computer. Usage statistics are turned off. |\n"
        "| Rules (regular expressions) | Recognise text with a fixed shape: email addresses, "
        "phone numbers, IBAN, social security numbers (NIR), SIREN and SIRET, case numbers. |\n"
        "| Check keys (Luhn, modulo 97) | Verify the control digits of IBAN, NIR, SIREN and "
        "SIRET, which makes these detections very reliable. |\n"
        "| Microsoft Presidio | Open-source framework that runs the rules and the language "
        "models together and reports each detection with its position and a score. |\n"
        "| spaCy | Pre-trained language models (French `fr_core_news_md`, English "
        "`en_core_web_sm`) that recognise names of persons and organisations from the "
        "context of the sentence. |\n"
        "| CamemBERT, GLiNER (optional) | Larger neural models for the Enhanced profile, in "
        "French and in English, installed separately and run locally. |\n"
        "| pypdf, python-docx | Read PDF files that contain text and Word files; write the "
        "Word exports. |\n"
        "| Mistral API (optional) | Sends the checked message to Mistral, only if a key is "
        "configured and you confirm each sending. |\n"
        "| pandas, Altair | Tables and charts of the measured results. |"
    ),
    "method.tech.note": (
        "A PDF made from a scan contains an image, not text: HuisClos cannot read it and says "
        "so. Convert it with a text recognition tool first, then check the result."
    ),
}

FR: dict[str, str] = {
    "method.summary.title": "En bref",
    "method.summary.problem": (
        "**Le problème.** Les outils d'IA comme ChatGPT, Claude ou Mistral savent résumer un "
        "dossier, rédiger un courrier ou lister les arguments d'une affaire. Mais le texte "
        "que vous y collez quitte votre ordinateur et il est traité sur les serveurs d'une "
        "entreprise. Pour un avocat, transmettre les noms, adresses ou identifiants d'un "
        "client à un tel service peut violer le secret professionnel."
    ),
    "method.summary.solution": (
        "**Ce que fait HuisClos.** Avant que le texte ne quitte votre ordinateur, HuisClos "
        "repère les informations qui identifient des personnes et des sociétés et remplace "
        "chacune par une étiquette neutre, appelée jeton, comme `[PERSONNE_1]`. Vous envoyez "
        "ce texte masqué à l'outil d'IA. Quand la réponse revient, HuisClos remet les vrais "
        "noms à leur place. La liste qui relie chaque jeton à sa vraie valeur ne quitte "
        "jamais votre ordinateur."
    ),
    "method.summary.limits": (
        "**Ce qu'il ne fait pas.** HuisClos ne rend pas un texte anonyme : les faits restent "
        "lisibles, et un lecteur qui connaît l'affaire peut encore la reconnaître. Il peut "
        "aussi oublier un nom. C'est pourquoi vous vérifiez chaque détection, et pourquoi "
        "l'outil expose ses limites sur cette page."
    ),
    "method.diagram.how_to_read": (
        'Comment lire ce schéma : tout ce qui se trouve dans le cadre "Sur cet ordinateur" '
        "reste sur votre machine. Seul le texte pseudonymisé passe vers l'outil d'IA, et "
        "seulement quand vous décidez de l'envoyer. La flèche en pointillés est la table de "
        "correspondance : elle va directement de la pseudonymisation à la restauration et ne "
        "passe jamais par l'outil d'IA."
    ),
    "method.example.title": "Un exemple commenté",
    "method.example.intro": (
        "Une illustration simplifiée avec une cliente fictive. Les quatre encadrés suivent le "
        "texte, du dossier d'origine à la réponse restaurée."
    ),
    "method.example.original_label": "**1. Votre document (reste sur votre ordinateur)**",
    "method.example.original": (
        "Mme Claire Dumontel, née le 4 mars 1981, demeure 12 rue des Lilas, 69003 Lyon. Son "
        "employeur, la société Batiplus SARL, l'a licenciée le 2 juin 2026. Contact : "
        "claire.dumontel@example.com."
    ),
    "method.example.sent_label": "**2. Ce que reçoit l'outil d'IA**",
    "method.example.sent": (
        "Mme [PERSONNE_1], née le [DATE_NAISSANCE_1], demeure [ADRESSE_1]. Son employeur, la "
        "société [SOCIETE_A], l'a licenciée le 2 juin 2026. Contact : [EMAIL_1].\n\n"
        "Consigne : Résume les faits en deux phrases."
    ),
    "method.example.answer_label": "**3. La réponse de l'outil d'IA**",
    "method.example.answer": (
        "[PERSONNE_1] a été licenciée par [SOCIETE_A] le 2 juin 2026. Elle peut contester ce "
        "licenciement devant le conseil de prud'hommes."
    ),
    "method.example.restored_label": "**4. La réponse restaurée (sur votre ordinateur)**",
    "method.example.restored": (
        "Claire Dumontel a été licenciée par Batiplus SARL le 2 juin 2026. Elle peut contester "
        "ce licenciement devant le conseil de prud'hommes."
    ),
    "method.example.note": (
        "À remarquer : la civilité \"Mme\" reste hors du jeton, pour que l'outil d'IA écrive "
        "des phrases correctes. La date du licenciement n'est pas masquée : HuisClos masque "
        "les dates de naissance, pas toutes les dates, car elles servent souvent à raisonner "
        "sur l'affaire. L'outil d'IA ne voit jamais le vrai nom, et pourtant la réponse finale "
        "le contient. Les jetons peuvent aussi s'écrire en anglais ([PERSON_1], [COMPANY_A]) "
        "depuis la barre latérale."
    ),
    "method.data.title": "Ce qui quitte votre ordinateur, et ce qui y reste",
    "method.data.stays": (
        "**Reste sur votre ordinateur.** Le document d'origine, la liste des détections, vos "
        "décisions de revue, la table de correspondance et la réponse restaurée. HuisClos les "
        "garde en mémoire tant que la page est ouverte et n'écrit rien sur le disque, sauf "
        "quand vous cliquez sur un bouton de téléchargement."
    ),
    "method.data.leaves": (
        "**Ne sort que par votre geste.** Le texte pseudonymisé et votre consigne, quand vous "
        "les copiez dans un outil d'IA ou, si vous l'avez configuré, quand vous les envoyez à "
        "Mistral après une confirmation explicite. Rien n'est envoyé automatiquement."
    ),
    "method.data.check": (
        "**Un dernier contrôle avant l'envoi.** Juste avant la copie du message, un contrôle "
        "final y recherche à nouveau chaque vraie valeur de la table de correspondance, un "
        "nom de famille resté seul et les noms écrits dans votre propre consigne. Tant "
        "qu'une alerte est ouverte, la copie et le téléchargement restent désactivés. Vous "
        "décidez : masquer la valeur, corriger la consigne, ou garder la mention après "
        "l'avoir lue dans son contexte."
    ),
    "method.data.offline": (
        "**Aucune connexion cachée.** En installation locale, l'application n'appelle pas "
        "Internet : ni police web, ni script externe, ni statistiques d'usage. Un test "
        "automatique le vérifie à chaque modification du code. Les modèles de langue sont "
        "installés une fois, à l'avance, et jamais téléchargés par l'application."
    ),
    "method.tech.title": "Technologies employées",
    "method.tech.intro": (
        "HuisClos assemble des composants libres et éprouvés. Aucun ne demande de compte ni "
        "de connexion à Internet, sauf le connecteur Mistral facultatif."
    ),
    "method.tech.table": (
        "| Composant | Son rôle dans HuisClos |\n"
        "| --- | --- |\n"
        "| Python 3.12 | Le langage de programmation de tout l'outil. |\n"
        "| Streamlit | Construit l'interface que vous utilisez, une page web servie par votre "
        "propre ordinateur. Les statistiques d'usage sont coupées. |\n"
        "| Règles (expressions régulières) | Reconnaissent les textes de forme fixe : "
        "courriels, téléphones, IBAN, numéros de sécurité sociale (NIR), SIREN et SIRET, "
        "numéros de dossier. |\n"
        "| Clés de contrôle (Luhn, modulo 97) | Vérifient les chiffres de contrôle des IBAN, "
        "NIR, SIREN et SIRET, ce qui rend ces détections très fiables. |\n"
        "| Microsoft Presidio | Cadre libre qui fait tourner ensemble les règles et les "
        "modèles de langue et rend chaque détection avec sa position et un score. |\n"
        "| spaCy | Modèles de langue préentraînés (français `fr_core_news_md`, anglais "
        "`en_core_web_sm`) qui reconnaissent les noms de personnes et d'organisations "
        "d'après le contexte de la phrase. |\n"
        "| CamemBERT, GLiNER (facultatifs) | Modèles neuronaux plus grands pour le profil "
        "renforcé, en français et en anglais, installés à part et exécutés localement. |\n"
        "| pypdf, python-docx | Lisent les PDF qui contiennent du texte et les fichiers Word ; "
        "écrivent les exports Word. |\n"
        "| API Mistral (facultative) | Envoie le message contrôlé à Mistral, seulement si une "
        "clé est configurée et que vous confirmez chaque envoi. |\n"
        "| pandas, Altair | Tableaux et graphiques des résultats mesurés. |"
    ),
    "method.tech.note": (
        "Un PDF issu d'un scan contient une image, pas du texte : HuisClos ne peut pas le lire "
        "et le signale. Convertissez-le d'abord avec un outil de reconnaissance de texte, puis "
        "vérifiez le résultat."
    ),
}
