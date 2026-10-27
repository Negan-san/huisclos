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
| NER spaCy (score fixe attribué par Presidio, à confirmer dans le code installé) | 0,85 |
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
