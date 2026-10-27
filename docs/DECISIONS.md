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

## D-S21-1 Substitution par presidio et relevé des occurrences
- Contexte : l'opérateur custom de presidio-anonymizer ne reçoit que le texte de la mention, et le résultat (EngineResult.items) donne le jeton et sa position dans le texte produit, sans le texte d'origine. Par défaut, presidio réunit deux mentions voisines de même type séparées par une espace.
- Choix : un opérateur custom par type, qui lit une table (texte exact de la mention vers jeton) ; anonymize appelé avec merge_entities_with_spaces=False ; les éléments du résultat, triés par position, sont appariés aux détections triées, puis le nombre et chaque jeton sont contrôlés (erreur sinon). Aucun remplaçant interne n'est nécessaire. Dans le doute sur un rattachement de personne, un groupe distinct est créé avec ambiguous_with renseigné. La table JSON porte created_at, qu'un paramètre permet d'imposer pour un résultat identique octet pour octet.
- Raison : D-04 (réutiliser presidio) sans perdre les occurrences exactes dont la restauration exacte de D-10 a besoin ; deux mentions de même type et de même texte ont la même clé, donc le même jeton, ce qui rend la table sans ambiguïté.

## D-S22-1 Règles de reconnaissance des jetons altérés
- Contexte : un LLM peut réécrire un jeton (casse, accents, espaces, crochets, échappement Markdown) ; une règle trop large restaurerait une phrase ordinaire, une règle trop étroite laisserait un jeton dans la réponse.
- Choix : recherche sur une copie du texte sans accents, de même longueur, pour garder les positions ; libellés FR et EN de TOKEN_LABELS seulement ; crochets retenus seulement s'ils forment une paire, un crochet isolé reste dans le texte. Sans paire de crochets : libellé en majuscules ou tiret bas exigé, indice de la bonne nature (lettres pour les sociétés, chiffres sinon), et refus d'un indice suivi d'un autre groupe de chiffres ("SIRET 732 829"). Indice de société limité à trois lettres. Une forme entre crochets dont l'indice ou le type manque dans la table va dans unknown. Mode exact sans positions : seulement si chaque jeton apparaît dans le texte autant de fois que dans la table.
- Raison : D-10 ; restaurer les altérations courantes sans toucher "aucune personne 1", les numéros officiels précédés de leur libellé ni une chaîne en forme de jeton déjà présente dans le document d'origine.

## D-G2fix-1 Positions persistées et formes de société ambiguës
- Contexte : G2-R1 perdait les positions des occurrences après relecture JSON ; G2-R2 restaurait le verbe A dans une phrase ordinaire ; G2-R3 annonçait le mode exact pour un inventaire incomplet.
- Choix : conserver start et end dans MappingOccurrence et le JSON version 1, avec lecture compatible des anciennes occurrences sans positions et validation des paires présentes. Le mode exact vérifie l'inventaire (jeton, original) contre la table ; une liste incomplète utilise la table. Pour une société sans crochets, exiger un tiret bas ou un tiret entre libellé et indice ; une simple espace reste ambiguë, même en majuscules. Cette règle précise D-S22-1 sans modifier models.py.
- Raison : appliquer D-10 sans transformer les jetons littéraux du document ni les phrases ordinaires. Une ancienne table sans positions ne peut pas retrouver une information déjà perdue ; une société écrite SOCIETE A dans une réponse doit garder des crochets ou un séparateur explicite pour être restaurée.

## D-S31-1 Textes de l'interface et styles par type
- Choix : t(clé) lit le dictionnaire anglais fusionné des modules de app/i18n/ ; une clé absente lève KeyError quand HUISCLOS_I18N_STRICT est défini (les tests le définissent) et affiche la clé sinon. ENTITY_STYLES associe à chaque type une couleur et la clé de son libellé ; la propriété label donne le libellé anglais. Les règles CSS de surlignage sont produites à partir de ENTITY_STYLES, pas écrites deux fois.
- Raison : une faute de clé doit échouer en test sans jamais bloquer l'application en production ; un libellé anglais dans ui_common.py aurait violé la règle de centralisation des textes, et une seconde liste de couleurs dans style.css aurait pu diverger du dictionnaire.

## D-S31-2 État de l'étape Import
- Choix : le texte à traiter vit dans source_text ; la zone de saisie est réalimentée depuis cette clé à chaque affichage (Streamlit oublie l'état d'un composant absent de la page), et chaque chargement (collage, fichier, exemple) passe par des rappels on_change ou on_click qui écrivent les deux. La clé du sélecteur de fichier porte un compteur qui augmente à chaque remise à zéro. La détection n'est refaite que si l'empreinte du texte normalisé et de la configuration change ; elle efface alors les décisions et résultats en aval.
- Raison : seuls les rappels peuvent modifier la valeur d'un composant déjà connu ; supprimer l'état d'un sélecteur de fichier ne vide pas le fichier affiché, alors qu'une remise à zéro doit effacer les documents du client ; des décisions de revue calculées sur d'anciennes positions seraient fausses.

## D-G2fix-2 Les positions de la table font foi en mode exact
- Contexte : G2-R4 a montré qu'une liste d'occurrences complète, mais décalée sur un jeton littéral ou aux écritures permutées, passait le contrôle d'inventaire de D-G2fix-1 et produisait un faux mode exact.
- Choix : quand la table porte des positions, restore les utilise seules et ignore la liste fournie ; la liste fournie, contrôlée par son inventaire, ne sert qu'avec une ancienne table sans positions. Signature de restore et models.py inchangés.
- Raison : la table est produite en même temps que le texte pseudonymisé et vérifiée par son empreinte ; une liste externe n'apporte rien de plus et peut avoir été altérée. Limite connue : une ancienne table sans positions ne peut pas détecter une liste complète mais décalée.

## D-S32-1 Les décisions de revue portent sur les positions des mentions
- Choix : group_decisions associe à chaque position (début, fin) une décision (masquer ou non, type imposé). Les actions du tableau s'appliquent à toutes les positions du groupe affiché ; les groupes sont recalculés par group_mentions à chaque affichage. Un ajout manuel ignore les occurrences déjà comprises dans une valeur masquée, remplace les détections qu'il recouvre autrement (et efface leurs décisions) et ne touche à rien d'autre.
- Raison : un groupe change d'identifiant dès qu'un type ou un ajout modifie le regroupement, alors qu'une position reste la même ; clear_results() vide le tout à chaque nouvelle détection. Remplacer "Jean DUPONT" par "DUPONT" laisserait "Jean" en clair, ce qui est une fuite : la protection existante l'emporte sur l'ajout. La pseudonymisation refuse les chevauchements, d'où le remplacement des détections partiellement recouvertes.

## D-S32-2 Tableau de décision relu par comparaison, avec une clé de composant versionnée
- Choix : st.data_editor reçoit la liste des lignes et renvoie les lignes modifiées ; l'écran compare les deux, reporte les différences dans les décisions, augmente un numéro de version inclus dans la clé du composant, puis relance la page. Aucun rappel on_change n'est utilisé pour le tableau. Une modification efface aussi pseudo_result et restore_result.
- Raison : Streamlit conserve les modifications en attente par numéro de ligne tant que la clé et la forme du tableau sont inchangées ; après un changement de type, le regroupement peut déplacer des lignes et ces modifications s'appliqueraient à la mauvaise ligne. Un tableau neuf après chaque modification évite cette dérive. Un résultat de pseudonymisation antérieur ne correspond plus aux décisions affichées.

## D-S44-1 Apport et coût de CamemBERT local
- Méthode : comparaison hors ligne sur dev seulement, 12 documents et 192 entités évaluées, seuil commun 0,30 retenu par le script, appariement partiel de même type. Commande : `PY scripts/run_evaluation.py --split dev --configs hybrid hybrid_camembert --out C:/Users/nasci/AppData/Local/Temp/huisclos-s44-evaluation`. Les sorties temporaires ne remplacent pas results/ ni les résultats G4 ; aucun split test exécuté ou ouvert. Empreinte SHA-256 dev : e3e4d0f02387670ca8d86b1ce4d4f1da51c3ec259909de9a91a72ad85588090b.

| Mesure dev, partiel | hybrid | hybrid_camembert | Évolution en points |
| --- | ---: | ---: | ---: |
| Rappel PERSON | 82/83 = 98,80 % | 82/83 = 98,80 % | +0,00 |
| Précision PERSON | 82/91 = 90,11 % | 82/91 = 90,11 % | +0,00 |
| Rappel ORGANIZATION | 13/17 = 76,47 % | 17/17 = 100,00 % | +23,53 |
| Précision ORGANIZATION | 13/26 = 50,00 % | 17/29 = 58,62 % | +8,62 |
| Rappel PERSON et ORGANIZATION réunis, micro | 95/100 = 95,00 % | 99/100 = 99,00 % | +4,00 |
| Précision PERSON et ORGANIZATION réunis, micro | 95/117 = 81,20 % | 99/120 = 82,50 % | +1,30 |
| Rappel global micro | 186/192 = 96,88 % | 190/192 = 98,96 % | +2,08 |
| Précision globale micro | 186/208 = 89,42 % | 190/211 = 90,05 % | +0,62 |
| F2 global micro | 95,29 % | 97,04 % | +1,75 |
| Fuite de caractères | 220/4012 = 5,48 % | 46/4012 = 1,15 % | -4,34 |

- Contrôle en exact : rappel PERSON 81/83 = 97,59 % dans les deux configurations ; ORGANIZATION 7/17 = 41,18 % puis 17/17 = 100,00 %. Précision globale exacte 85,58 % puis 89,10 %. Le gain ne repose donc pas seulement sur un recouvrement partiel des sociétés.
- Ressources : `PY scripts/measure_memory.py`, CPU, même processus, modèles conservés entre les deux lignes. hybrid : chargement 4,077 s, RSS chargée 711,9 Mio, détection démo 0,135 s, RSS finale 716,6 Mio, 17 détections. hybrid_camembert : chargement additionnel 0,710 s, RSS chargée 1164,4 Mio, détection 0,477 s, RSS finale 1203,9 Mio, 18 détections. Surcoût résident final : 487,3 Mio ; détection environ 3,53 fois plus lente. Ces RSS sont des instantanés après opération, pas des pics ; les durées excluent le démarrage de Python et les imports initiaux.
- Choix : à la demande de recommandation de l'humain, retenir le rappel micro des deux types réunis comme critère explicite : +4,00 points de rappel et +1,30 point de précision, donc seuil de +2 points atteint et aucune perte supérieure à 5 points. Verdict : CamemBERT admissible comme option de l'appli locale, désactivée par défaut, jamais dans le cloud. L'interface reste inchangée dans cette session, conformément au périmètre ; sa proposition à l'utilisateur relève d'une session autorisant cette modification. Le gain porte sur ORGANIZATION, aucun gain PERSON n'est démontré. Un seuil de +2 points par type serait impossible pour PERSON, déjà à 98,80 % ; sous cette autre lecture, le verdict serait rapport seulement. Cette interprétation du critère est explicitée après la mesure et ne doit pas être présentée comme préenregistrée.
- Limites : torch 2.14.1+cpu, transformers 5.21.0 et sentencepiece 0.2.2, modèle Jean-Baptiste/camembert-ner en cache uniquement ; HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1 et local_files_only=True. Chargement partagé, inférence CPU, aucune dépendance ajoutée à requirements.txt, aucun déploiement cloud. Les morceaux sont limités à 512 jetons, jetons spéciaux compris ; une phrase trop longue peut imposer une coupure dans une mention et réduire le rappel. Le branchement paresseux déjà présent dans pipeline.py est réutilisé sans modification.

## D-S33-1 Étape Restore : noms de fichiers, table importée, résultat périmé
- Choix : les fichiers téléchargés se nomment huisclos-<8 premiers caractères de l'empreinte SHA-256 du texte pseudonymisé>.<nature>.<extension> (pseudonymized, restored, mapping.json), jamais d'après le nom du document source. Un fichier JSON téléversé remplace la table du document pour la restauration ; s'il est illisible, une erreur claire s'affiche et la table du document reste utilisée. Un résultat de restauration n'est montré que si la réponse collée et la table sont celles du clic sur Restore (empreinte conservée dans restore_signature). Le téléverseur de table dépend du compteur upload_nonce, donc la remise à zéro oublie la table sensible.
- Raison : le nom d'un fichier source peut contenir le nom d'un client, et le texte pseudonymisé part chez un tiers ; l'empreinte relie quand même le texte, sa table et la restauration. Montrer un ancien résultat à côté d'une réponse modifiée ou d'une autre table serait trompeur.
- Limite connue : st.code retire les espaces et sauts de ligne de début et de fin à l'affichage et à la copie ; les téléchargements gardent le texte complet. Sans pseudonymisation dans la session, l'étape ne s'ouvre pas depuis l'interface (aucun bouton ne mène à Restore) : l'import d'une table enregistrée y fonctionne, mais son point d'entrée reste à ajouter à l'étape Import.
- Recontrôle du 27 octobre 2026 à 21:44 (Paris), base 7aed779 : comparaison dev relancée avec les mêmes configurations, sorties dans le dossier temporaire huisclos-s44-recheck-7567d82ea8f74cfbaf855a774a91dd9f ; seuil 0,30, empreinte dev et tous les chiffres du tableau reproduits. Nouvelle mesure séquentielle CPU : hybrid, chargement 4,115 s, RSS chargée 712,1 Mio, détection 0,125 s, RSS finale 716,9 Mio ; hybrid_camembert, chargement additionnel 0,698 s, RSS chargée 1164,6 Mio, détection 0,433 s, RSS finale 1203,5 Mio. Surcoût final 486,6 Mio, durée de détection multipliée par 3,46 ; verdict et limites inchangés. Aucun recalcul de l'évaluation test ni remplacement des résultats G4.

## D-S35-1 SIREN à clé invalide accompagné d'un libellé
- Contexte : un SIREN mal recopié (clé de Luhn fausse) restait en clair, alors que le texte l'annonçait comme SIREN.
- Choix : neuf chiffres, groupés 3-3-3 ou non, précédés dans les 25 caractères d'un libellé "SIREN" (y compris "n° SIREN") ou "RCS", sont signalés comme SIREN avec la source pattern et le score 0,40, comme un NIR, un IBAN ou un SIRET à clé fausse (D-07). Sans ce libellé et sans clé valide, aucune détection : un montant ou une quantité de neuf chiffres reste visible. Le contexte large ("immatriculée", "registre du commerce") ne suffit pas pour une clé fausse.
- Raison : principe 3, une faute de frappe ne rend pas le numéro moins identifiant ; le libellé proche limite les faux positifs. Le score reste sous celui du checksum (1,00 ou 0,70) et au-dessus du seuil de D-13 (0,30).

## D-S35-2 Règle d'extension des sociétés
- Contexte : diagnostic dev (results/errors_dev.csv de G4) : noms de sociétés coupés à gauche, fragmentés, ou absents quand aucun reconnaisseur ne les voyait ; "M. Prénom NOM" scindé en PERSON et ORGANIZATION.
- Choix : nouvelle étape detection/organization_bounds.py après merge. Une société qui finit par une forme juridique de text_utils s'étend vers la gauche, une société qui commence par une forme juridique vers la droite, sur les mots à majuscule et les liaisons (de, des, du, d', la, le, les, et, &). Arrêt sur ponctuation, saut de ligne, chiffre, mot en minuscule hors liaison, civilité, libellé (société, employeur, expéditeur, destinataire), mot grammatical à majuscule ("Contre", "Chez"), autre forme juridique, juridiction ou texte exclu de plusieurs mots, ou au bout de 6 mots. Aucune liaison en tête ni en fin. Les noms contenus sont absorbés ; un identifiant, une adresse, un ajout manuel ou un nom qui déborde bloquent l'extension. Une forme juridique libre précédée ou suivie de mots à majuscule crée une société (source heuristic, score 0,70, comme les autres heuristiques de nom de D-07), seulement si les heuristiques sont activées. Deux sociétés séparées par une seule liaison sont réunies, sauf si la forme juridique sépare deux sociétés complètes ("A SARL et B SAS"). Une civilité suivie de un à trois mots à majuscule donne un seul PERSON (score au moins 0,80) qui remplace les fragments de personne ou de société contenus, sauf si le nom est suivi d'une forme juridique. À la propagation, une forme courte comprise dans une occurrence de la forme longue est élargie à celle-ci. Les intitulés de lettre (Veuillez, Lettre, Courriel, Téléphone, Section, Audience, Copie, Lecture) sont exclus seulement en tête de ligne.
- Raison : règles générales, sans liste de noms tirée du corpus ; D-09 respectée (libellés et civilités hors du span, forme juridique dedans). Mesure dev, hybrid : fuite de 5,48 % à 0,85 %, rappel ORGANIZATION de 76,47 % à 100 %, précision micro de 0,894 à 0,965.
- Limite connue : un mot à majuscule en tête de ligne devant le nom ("Contrat Durand SARL") est absorbé ; un nom de plus de 6 mots est tronqué à gauche ; une forme juridique écrite en minuscules n'est pas reconnue.

## D-S35-3 Seconde mesure du jeu test (G4bis)
- Contexte : G4 a mesuré le jeu test une fois (hybrid, seuil 0,30 : rappel 95,70 %, précision 94,68 %, fuite 12,02 %) ; S35 modifie la détection d'après le seul diagnostic dev.
- Choix : une seconde mesure du jeu test est prévue en G4bis, une seule fois, après S35 ; aucune règle n'a été ajustée d'après le jeu test, qui n'a été ni ouvert ni évalué en S35. Les résultats G4 restent cités dans l'historique (docs/PROGRESS.md, tag gate-4) et ne sont pas présentés comme ceux de la version finale.
- Raison : la séparation dev et test de D-12 reste intacte ; la seconde mesure est motivée par des erreurs observées sur dev uniquement et sera rapportée à côté de la première, sans la remplacer.

## D-G4bisfix-1 Clarification et gel du contrôle de surajustement
- Contexte : le prompt G4bis-fix remplace explicitement « aucune chaîne ajoutée ne figure dans le corpus » par l'absence de noms propres, identifiants ou formulations spécifiques recopiés du corpus pour orienter une règle ou construire un test. Un recouvrement lexical générique ne suffit pas à établir un surajustement.
- Méthode : classification figée avant toute nouvelle comparaison au corpus, à partir du seul diff S35 et du rôle des valeurs. Même extraction que G4bis : constantes Python non blanches touchant les lignes ajoutées et ligne d'exclusion ajoutée, hors commentaires, 11 fichiers et 175 valeurs distinctes. Les 31 valeurs déjà littérales dans src/ ou tests/ avant S35 sont distinguées des 144 nouvelles ; cette antériorité est établie dans git, sans consulter le corpus.
- Exclusions génériques : 18 valeurs grammaticales ou de libellé (liaisons, mots d'arrêt, société/employeur/expéditeur/destinataire, intitulés de lettre, SIREN/RCS et leur contexte) ; 14 valeurs techniques (syntaxe de regex, ponctuation, noms de groupes, états internes et jeton attendu) ; 5 valeurs de compte ou d'énumération (comptes d'interface 15 et 21, suites de nombres en toutes lettres testant la limite d'extension) ; 3 noms communs isolés d'activité ou de parenté (Comptoir, Verrerie, Fils). Ces mots n'identifient pas une société à eux seuls. Les expressions composites qui contiennent un nom restent candidates. Les formes sociales et civilités sont des catégories communes ; les règles les importent des constantes existantes, sans nouvelle liste de sociétés.
- Candidats : les 104 autres valeurs nouvelles sont conservées par prudence, y compris les formulations complètes et les docstrings. Quinze fragments supplémentaires définis sur le diff couvrent dix racines de noms fictifs, un nom composé, l'adresse complète et trois graphies d'identifiants. Aucune exclusion n'est construite à partir de correspondances test. Manifeste hors dépôt `%TEMP%/huisclos-g4bisfix-classification.json`, avec catégories, valeurs et positions dans S35 ; SHA-256 cea199d5c73acca662009b5833ccb89708894566e96df5012d90e07025f5bfc3, contrôlé par le script avant lecture des splits.
- Vérification : `%TEMP%/huisclos-g4bisfix-compare.py`, SHA-256 dcf40bd59a6b596a5210975b59060f8e13449d38bfcbdcdb256fa035d6b3c70d, lit les textes annotés par script seulement et n'affiche que des comptes. Pour chacun des deux groupes de candidats et chacun des splits dev et test : zéro correspondance en sous-chaîne exacte, zéro sans distinction de casse, zéro dans les spans annotés sans distinction de casse. Aucun appel à detect(), aucune métrique, aucune évaluation et aucun affichage de contenu du corpus.
- Portée : les comptes bruts historiques de G4bis restent conservés ; ils mélangent valeurs techniques, mots communs, libellés et candidats spécifiques et ne démontrent donc pas une copie spécifique. La revue manuelle confirme que les branches exécutables utilisent des règles de casse, de bornes, de contexte, de forme juridique et de chevauchement, sans nom de société fixé ni exception individuelle. L'audit ne relève aucune trace de surajustement dans le périmètre S35 ; il ne prétend pas reconstituer toutes les commandes historiques. D-13 et D-S35-1 à D-S35-3 restent inchangées ; les résultats enregistrés sont conservés sans nouvelle mesure.
