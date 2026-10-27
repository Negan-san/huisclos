# Décisions d'architecture

Format : contexte, choix, raison. D-01 à D-18 viennent du master plan (27 octobre 2026). Les sessions ajoutent leurs décisions en fin de fichier, avec l'identifiant D-<session>-<n> (exemple : D-S12-1), pour éviter les doublons entre les deux pistes.

## D-01 Version de Python
- Contexte : Streamlit Community Cloud fixe Python au déploiement (réglages avancés), 3.12 par défaut ; runtime.txt est ignoré.
- Choix : Python 3.12 en local et en ligne ; repli 3.11.
- Raison : même interpréteur partout ; Presidio 2.2.36x et spaCy 3.8 compatibles.

## D-02 Organisation du code
- Choix : code métier dans src/huisclos/ sans packaging ; pytest via pythonpath = ["src", "."] ; streamlit_app.py ajoute src/ au sys.path.
- Raison : fonctionne à l'identique en local, en test et sur le cloud.

## D-03 Orchestration de la détection
- Contexte : Presidio fournit registre, moteur NLP spaCy et API unique ; ses reconnaisseurs prédéfinis visent surtout l'anglais.
- Choix : presidio-analyzer avec un RecognizerRegistry limité au français et à nos reconnaisseurs. Le contexte (mots proches) est évalué dans nos reconnaisseurs, sur une fenêtre de 40 caractères avant le match, et non par l'améliorateur de contexte de Presidio. Chaque résultat porte recognition_metadata["huisclos_source"].
- Raison : scores explicables et conformes au barème D-07.

## D-04 Substitution
- Choix : presidio-anonymizer avec un opérateur personnalisé qui renvoie le jeton du groupe ; repli sur un remplaçant interne si l'API gêne la restauration exacte (le consigner dans une nouvelle décision).
- Raison : réutiliser l'outil existant tout en gardant la main sur la cohérence des jetons.

## D-05 Modèle spaCy
- Choix : fr_core_news_md, installé par URL de wheel dans requirements.txt ; lg écarté.
- Raison : modèle français pré-entraîné compatible avec la mémoire du cloud (690 Mo à 2,7 Go selon la documentation de Streamlit, chiffres de février 2024).
- Mesuré en S01 (meta.json du modèle installé) : version 3.8.0, compatible avec spaCy 3.8.18 (`spacy validate`) ; licence LGPL-LR (le meta.json ne renseigne pas de champ size) ; 65 163 220 octets sur disque, soit environ 62 Mio ; sources : UD French Sequoia (LGPL-LR), WikiNER (CC BY 4.0), spaCy lookups (MIT), vecteurs fastText (CC0).

## D-06 CamemBERT
- Choix : option locale (requirements-transformers.txt), évaluée en S44, jamais déployée, exécutée hors ligne (HF_HUB_OFFLINE=1).
- Raison : exige PyTorch, trop lourd pour le cloud gratuit ; sert à mesurer l'apport d'un transformeur.

## D-07 Barème de confiance

| Détection | Score |
| --- | --- |
| NIR ou IBAN à clé valide ; SIREN ou SIRET à clé valide près de son libellé ; ajout manuel | 1,00 |
| E-mail | 0,95 |
| Numéro de dossier après "RG" ou "Portalis" ; date après un contexte de naissance | 0,90 |
| SIRET à clé valide sans contexte | 0,85 |
| NER spaCy (score fixe attribué par Presidio, confirmé en S12 : D-S12-1) | 0,85 |
| Civilité suivie d'un nom | 0,80 |
| Téléphone français (0,90 avec "tél.", "téléphone", "portable" ou "mobile" à proximité) | 0,75 |
| SIREN à clé valide sans contexte ; Prénom NOM ; NOM Prénom ; adresse complète | 0,70 |
| Voie sans code postal | 0,55 |
| Code postal et ville seuls | 0,45 |
| NIR ou IBAN au bon format mais à clé fausse (faute de frappe probable, donc sensible) | 0,40 |
| Propagation | score de l'entité d'origine |

Seuil par défaut : 0,40 jusqu'à la gate 4, puis la valeur de results/threshold.json (D-13).

## D-08 Jetons
- Choix : libellés français par défaut, crochets, numérotation par ordre de première apparition ; sociétés indexées par lettres (A à Z, puis AA) ; libellés anglais en option.
- Raison : documents en français ; un jeton lisible aide le LLM ; les lettres distinguent les sociétés des personnes.

## D-09 Conventions de span
- Choix : civilités et libellés hors du span ; forme juridique accolée dans le span d'une société ; adresse en un seul span ; aucun chevauchement après fusion.
- Raison : "M. [PERSONNE_1]" garde le genre grammatical utile au LLM ; fuite résiduelle assumée et documentée.

## D-10 Restauration
- Choix : mode exact par la liste ordonnée des occurrences quand le texte reçu est le texte pseudonymisé (empreinte SHA-256) ; sinon mode tolérant qui restaure la forme canonique du groupe.
- Raison : aller-retour exact garanti ; réponse du LLM restaurée même si les jetons sont altérés.

## D-11 Aucun appel réseau à l'exécution
- Choix : pas d'EmailRecognizer de Presidio (il passe par tldextract, qui peut télécharger la liste des suffixes) ; gatherUsageStats = false ; aucune police web ; HF_HUB_OFFLINE=1 pour CamemBERT ; tests/test_no_network.py bloque les sockets pendant le pipeline complet.
- Raison : principe 1 d'AGENTS.md, démontrable par un test.

## D-12 Corpus d'évaluation
- Choix : sources Markdown avec balisage [[valeur|TYPE]] et marqueurs {{NIR}}, {{SIRET#1}} remplis par scripts/build_corpus.py avec des identifiants fictifs valides ; 12 documents dev, 6 test, 1 démo ; le split test n'est jamais lu par un agent.
- Raison : positions calculées par script, clés de contrôle exactes, séparation entre mise au point et mesure.

## D-13 Choix du seuil
- Choix : seuil qui maximise le F2 du pipeline hybride sur dev ; à égalité, le plus bas ; écrit dans results/threshold.json.
- Raison : F2 pondère le rappel davantage que la précision, à l'image du coût asymétrique des erreurs.

## D-14 Hébergement
- Choix : l'appli en ligne est une démonstration sur données fictives (bandeau si HUISCLOS_PUBLIC_DEMO est défini) ; un usage réel passe par l'installation locale.
- Raison : sur le cloud, le texte transite par le serveur de l'hébergeur.

## D-15 PDF
- Choix : pypdf, texte natif uniquement ; un PDF sans texte exploitable renvoie une erreur claire (pas d'OCR).

## D-16 Langues
- Choix : interface, README, guide, rapport, crédits et journal des prompts en anglais ; AGENTS.md, CLAUDE.md, PROGRESS, DECISIONS, CONTRIBUTIONS et commentaires de code en français.

## D-17 Connecteur Mistral
- Choix : appel HTTP avec requests, désactivé par défaut, visible seulement si une clé est configurée ; n'envoie que le texte pseudonymisé ; avertit que l'offre gratuite Experiment peut servir à entraîner les modèles de Mistral.

## D-18 Coupes
- Choix : GLiNER et Faker retirés du périmètre dès le plan.
- Raison : bénéfice faible pour la note ; Faker complique la réidentification et brouille la démo.

## D-S01-1 Épinglage des dépendances
- Choix : dépendances directes épinglées en == sur les versions installées en S01 (streamlit 1.66.1, presidio 2.2.366, spaCy 3.8.18, pandas 3.1.0, etc.) ; le modèle fr_core_news_md 3.8.0 est lié par URL de wheel (la version 3.8.1 n'existe pas).
- Raison : installation reproductible en local et sur le cloud.

## D-S01-2 Énumérations et règle UP042 de ruff
- Choix : EntityType et Source héritent de (str, Enum), comme l'exige le contrat de models.py, avec `# noqa: UP042` sur la ligne de classe.
- Raison : le contrat est partagé avec les autres sessions ; StrEnum changerait le rendu de str() et de format().

## D-S01-3 Test d'interface sans la fixture no_network
- Choix : l'AppTest de la page d'accueil n'utilise pas no_network, car AppTest ouvre une connexion locale (127.0.0.1) pour son propre fonctionnement.
- Raison : bloquer toutes les connexions rendrait le test impossible ; le test de bout en bout du pipeline (tests/test_no_network.py) portera sur le code métier.

## D-PIL-1 Délégation des tâches humaines
- Choix : pendant le développement, l'humain colle les prompts, relit le code et mène ses recherches pour la vidéo. Les fusions (étape 0 de chaque session), la rédaction des lots 2 et 3 du corpus (session C1, Codex) et les recettes de gate (sessions R0 à R5 et RF, Claude Code, Haiku ou Sonnet) sont confiées aux agents. Les recettes R<N> passent dev dans main, posent le tag et poussent.
- Raison : l'attention de l'humain est la ressource la plus rare ; chaque recette reste tracée dans docs/PROGRESS.md, et le contrôle croisé par une autre famille de modèles est conservé aux gates.

## D-G0-1 Contrôle des chemins externes
- Contexte : --paths acceptait un fichier Python hors du dépôt mais ignorait ses appels print et sa docstring de module.
- Choix : appliquer C5 et C6 aux fichiers Python externes explicitement fournis par --paths ; dans le dépôt, conserver ces règles sur src/ et app/ uniquement.
- Raison : le contrôle de robustesse de Gate 0 doit signaler le tiret interdit et le print du fichier temporaire, sans soumettre les scripts et les tests du dépôt aux règles métier.

## D-S12-1 Score des entités spaCy et chargement du modèle
- Contexte : D-07 annonçait 0,85 pour le NER spaCy, à confirmer. Lecture du code installé (presidio-analyzer 2.2.366) : SpacyNlpEngine._get_scores_for_entities attribue à chaque entité NerModelConfiguration.default_score, soit 0,85 par défaut, et SpacyRecognizer renvoie ce score tel quel. Le modèle spaCy ne fournit aucune probabilité. La même version télécharge le modèle (spacy.cli.download) s'il n'est pas installé.
- Choix : score NER = 0,85, valeur de D-07 confirmée, fixée explicitement dans la configuration (ner.NER_SCORE). Le moteur refuse de se charger si le modèle manque (RuntimeError) au lieu de le télécharger. Les étiquettes PER, ORG et LOC deviennent PERSON, ORGANIZATION et LOCATION ; MISC est ignoré. Le registre ne contient que des reconnaisseurs de langue "fr".
- Raison : principe 1 d'AGENTS.md (aucun appel réseau à l'exécution) ; un score identique pour toutes les entités signifie que le NER ne classe pas ses propres détections, seul le seuil de D-13 les départage des heuristiques (0,70 à 0,80).

## D-S13-1 Arbitrage des chevauchements entre types différents
- Contexte : la règle 5 désigne un gagnant (priorité, puis score, puis longueur) mais laisse ouvert le sort du perdant en cas de chevauchement partiel.
- Choix : les détections sont examinées de la plus forte à la plus faible. Une détection contenue dans une plus forte disparaît ; une détection qui en contient une plus forte ou la chevauche en partie est rognée à sa plus longue partie libre, gardée si elle compte au moins 2 lettres ou chiffres. La priorité inclut le type : deux types différents ne sont donc jamais à égalité, et le score ne départage que des détections de même type, déjà unies en 5a. Un ajout manuel n'est jamais uni à une détection automatique ni supprimé par les exclusions.
- Raison : priorité au rappel (principe 3) : "Paul Martin 14" chevauchant une adresse laisse "Paul Martin" masqué ; le reste chiffré d'un IBAN rogné par un ajout manuel reste sensible.

## D-S13-2 Rognage étendu : civilité seule et passage à la ligne
- Contexte : sur mini_case, spaCy étiquette "Madame" comme personne (ensuite propagé à chaque "Madame") et prolonge "Claire Fontaine" sur la ligne suivante ("Avocate").
- Choix : à la règle 1, une personne réduite à une civilité est supprimée ; un nom de personne, de société ou de lieu qui passe à la ligne est limité à sa plus longue ligne.
- Raison : un nom propre ne passe pas à la ligne dans un en-tête ; la civilité reste visible par convention (D-09).

## D-S13-3 Moteur spaCy commun à toutes les configurations
- Contexte : AnalyzerEngine de Presidio exige un moteur NLP ; sans moteur fourni, il en crée un par défaut (modèle anglais, téléchargement possible).
- Choix : un seul moteur fr_core_news_md en cache (pipeline.get_nlp_engine), partagé par toutes les configurations ; seuls les reconnaisseurs varient d'une configuration à l'autre. CamemBERT est chargé depuis huisclos.detection.camembert (build_camembert_recognizers), avec une RuntimeError claire si l'option est absente.
- Raison : un seul chargement de modèle (3,8 s mesurées) et aucun appel réseau (D-11) ; le surcoût de spaCy pour patterns_only est faible (0,09 s pour mini_case en hybride).

## D-S13-4 Propagation : formes en majuscule et particules élidées
- Choix : une occurrence n'est retenue que si son premier mot, et chaque mot écrit avec une majuscule dans la forme d'origine, commence par une majuscule ; l'initiale se lit après une particule élidée ("d'Aubigné"). Les formes longues sont cherchées d'abord ; pour une forme partagée par des homonymes, l'entité de plus haut score puis la première du texte sert d'origine.
- Raison : "petit" ne doit jamais être masqué pour le nom Petit ; "DUPONT" isolé reçoit le même type et le même score, quel que soit l'homonyme retenu, et le regroupement des jetons reste revu par l'humain.

## D-G1fix-1 Parties libres et passages exclus qui franchissent un nom
- Contexte : la gate G1 a relevé un nom perdu autour d'un identifiant (D-S13-1 ne gardait que la plus longue partie libre) et des noms NER ou propagés qui débordaient dans une juridiction exclue sans y être contenus.
- Choix : une détection rognée garde toutes ses parties libres d'au moins 2 lettres ou chiffres. Un passage exclu qui franchit une borne d'un nom en est retiré à la fusion ; à la propagation, l'occurrence est ignorée et une forme plus courte reste cherchée. Un passage exclu entièrement contenu dans le nom ne le coupe pas. Le filtre des types activés s'applique après la requalification. Une voie suivie de son code postal, réunie à la règle 6, vaut au moins 0,70 (D-07).
- Raison : priorité au rappel (principe 3) sans jamais masquer une juridiction ; "SARL", exclu seul, appartient au span de sa société (D-09).

## D-G1fix-2 Références juridiques contenues dans un nom
- Contexte : la gate G1 rejouée a relevé qu'une juridiction ou un article entièrement contenu dans un span NER ("La société Tribunal judiciaire de Nanterre SARL") restait masqué, et pouvait être propagé ; D-G1fix-1 ne retirait que les passages exclus franchissant une borne. Elle a aussi relevé "Tribunal judiciaire de Saint Denis", exclu seulement jusqu'à "Saint".
- Choix : un passage exclu de plusieurs mots est une référence juridique (juridiction, institution, article, code) ; contenu dans un nom, il en est retiré à la fusion (merge.cutting_spans), les parties libres restent signalées sauf si elles sont elles-mêmes exclues, et la propagation ignore l'occurrence qui le contient. Un passage exclu d'un seul mot ("SARL", "Cabinet") reste dans le span de sa société. Dans les juridictions, "Saint", "Sainte", "St" ou "Ste" suivi d'un espace se relie à un seul nom de lieu.
- Raison : critère de gate "juridiction et article jamais détectés" ; le nombre de mots distingue sans nouvelle donnée les références des formes juridiques (D-09). Limite connue : une référence d'un seul mot (URSSAF, RGPD) contenue dans un nom reste masquée, gêne de précision sans perte de rappel ; un lieu non composé suivant "Saint" peut absorber un prénom ("Saint Paul Martin" exclut "Paul"), le nom restant signalé par soustraction.
