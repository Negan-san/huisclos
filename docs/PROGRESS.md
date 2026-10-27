# Journal de passage de relais

Une entrée par session, la plus récente en tête de la section Entrées. Cinq à huit lignes, sans paraphrase du code.

## Modèle d'entrée

### AAAA-MM-JJ HH:MM | S00 | Titre de la session | Agent, modèle
- Fait :
- Tests : commande et résultat (exemple : "pytest : 42 passed ; ruff : OK ; check_style : OK")
- Reste à faire :
- Décisions : renvoi D-xx, ou "aucune"
- Risques ou blocages :
- Prochaine session :

## Entrées

### 2026-10-27 15:36 | S12 | NER française, heuristiques de personnes, exclusions | Claude Code, Sonnet 5.5
- Fait : detection/ner.py (moteur spaCy fr, reconnaisseur marqué ner_spacy, refus de charger un modèle absent), detection/person_heuristics.py (civilité 0,80 ; Prénom NOM et NOM Prénom 0,70 ; gardes : mots de début de phrase, acronymes, chiffres romains), detection/exclusions.py et data/exclusions_fr.txt (cinq sections, X = nom de lieu, entrées re:, spans fusionnés, is_excluded limité à PERSON, ORGANIZATION, LOCATION).
- Tests : pytest : 87 passed (dont test_ner, test_person_heuristics, test_exclusions, un test NER sous no_network) ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement.
- Reste à faire : brancher les trois modules dans le pipeline (fusion, propagation) ; enrichir la liste de mots courants et [mots] d'après les erreurs mesurées sur dev ; "Jean DUPONT SARL" garde l'acronyme dans le span.
- Décisions : D-S12-1 (score NER 0,85 confirmé dans le code installé ; D-07 mis à jour).
- Risques ou blocages : Presidio télécharge le modèle spaCy s'il manque, d'où le garde-fou de build_nlp_engine ; les nouveaux fichiers ont été vérifiés sans toucher à patterns.py ni à checksums.py ; aucun fichier du split test lu.
- Prochaine session : suite du plan (fusion et propagation), selon docs/MASTER_PLAN.md.
### 2026-10-27 15:38 | S11 | Validateurs et reconnaisseurs à motifs | Codex
- Fait : dev synchronisé sans conflit ; signatures Presidio lues dans le code installé ; validateurs purs, générateurs déterministes et neuf reconnaisseurs français créés dans le périmètre autorisé.
- Tests : pytest : 191 passed ; 500 valeurs valides et 500 à clé fausse par type comparées à python-stdnum, compactes et groupées ; 500 NIR par département corse et 500 SIRET La Poste ; spans, contexte de 40 caractères, scores D-07 et métadonnées vérifiés ; exécution sans réseau testée.
- Contrôles : ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement ; aucun import de tldextract dans src/.
- Reste à faire : intégration des reconnaisseurs dans le pipeline de détection par les sessions suivantes ; aucun changement à models.py, aux paquets __init__.py, à app/ ni aux modules de la piste A.
- Décisions : aucune ; application de D-03, D-07, D-09 et D-11. Les oracles demandés sont tous disponibles ; leurs contraintes supplémentaires ne remplacent pas le contrat des validateurs.
- Risques ou blocages : dossier temporaire Windows standard inaccessible ; pytest -q passe avec TEMP et TMP dirigés vers .pytest_cache/s11-temp ; aucune installation, aucun appel réseau ni lecture du split test.
- Prochaine session : suivre la sortie du script de pilotage S11 après le commit.

### 2026-10-27 15:35 | R0 | Recette de la gate G0 | Claude Code, Haiku 5.5
- Fait : dev fusionné avec lane-b sans conflit ; verdict G0 lu : GO. Étape 1 installation à neuf (venv Python 3.12 temporaire, requirements.txt) : OK, 138 s, dossier supprimé. Étape 2 lancement headless sur le port 8599 : OK, HTTP 200 après 20 s, /_stcore/health 200, aucune erreur dans la sortie, processus arrêté et port libéré. Étape 3 AppTest : OK, titre HuisClos, accroche, sous-titres 1. Import, 2. Review, 3. Restore et mention RGPD (art. 4(5), considérant 26) affichés.
- Tests : pytest : 31 passed ; ruff check : OK ; ruff format --check : OK ; check_style : 0 erreur, 0 avertissement.
- Reste à faire : centraliser les textes de la page d'accueil dans app/i18n/ ; ajouter au README la distinction pseudonymisation/anonymisation (repris de G0).
- Décisions : aucune.
- Risques ou blocages : au démarrage Streamlit affiche une "External URL", donc il interroge sans doute un service d'IP publique ; à vérifier avant le test réseau du pipeline (principe 1 d'AGENTS.md).
- Prochaine session : suite du plan après la gate G0 ; tag gate-0 posé sur main si le push réussit.

### 2026-10-27 15:13 | G0 | Contrôle du socle : GO | Codex
- Fait : conflits PROGRESS/PROMPTS résolus sur demande en conservant les entrées des deux pistes ; diff complet S01 (0b86362) relu ; dépendances, configuration, exclusions Git, attributs union et contrat models.py conformes.
- Corrections : C5 reconnaît aussi print avec espaces ; C5/C6 appliqués aux fichiers Python externes fournis par --paths ; caractères interdits écrits en échappements dans le script et ses tests ; docstring Detection rectifiée sans changement du contrat ; tests des noms de types et scores non finis renforcés.
- Tests : pytest : 31 passed ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement ; fichier fautif temporaire hors dépôt : sortie 1, C1 et C5, puis dossier supprimé ; Python 3.12 et versions installées vérifiés sans réseau.
- Reste à faire et repli : centraliser les textes dans app/i18n/ (hors périmètre), ajouter au README la distinction pseudonymisation/anonymisation ; conserver jusque-là la mention légale présente dans l'interface ; créer le test réseau du pipeline quand il sera implémenté.
- Décisions : D-G0-1 ; verdict GO selon les critères de G0, sans changement d'architecture ni du contrat de models.py.
- Risques ou blocages : pytest standard a rencontré un refus d'accès au dossier temporaire Windows existant ; contourné avec --basetemp .pytest_cache/g0-final ; aucune installation, aucun appel réseau, aucune lecture du split test.
- Prochaine session : recette R0 par la piste A ; la fusion reprend dev à 62e3362, son état au démarrage ; le nouveau commit de pilotage 7a69f7c sera conservé lors de la synchronisation suivante ; aucun tag ni push dans G0.

### 2026-10-27 15:10 | PIL | Délégation des tâches humaines aux agents | Claude Code, Opus 5.5
- Fait : AGENTS.md sections 7, 11 et 12 : synchronisation par les agents (étape 0), sessions de recette R<N> qui fusionnent, taguent et poussent après une gate GO, session C1 qui rédige les lots 2 et 3 du corpus.
- Tests : check_style vert sur AGENTS.md (128 lignes).
- Décisions : D-PIL-1.
- Risques ou blocages : le commit fdd4f3a de lane-b, libellé "S11", contient en réalité le lot 1 du corpus ; S11 reste à faire.
- Prochaine session : G0 (Codex, huisclos-b).

### 2026-10-27 14:45 | S11 | Corpus fictif H1, lot 1 | Codex
- Fait : relecture des six documents dev selon A5 ; sources doc_01 à doc_06 enregistrées en UTF-8 sans BOM ; prompt initial et suivi copiés dans docs/prompts/corpus_lot_1.md.
- Tests : contrôles ciblés sur les six sources OK (299 à 353 mots, 16 à 18 annotations, en-têtes, spans, marqueurs, formes courtes, pièges, domaines réservés) ; copie du prompt comparée au modèle A5 ; ruff check et ruff format --check OK.
- Reste à faire : validation humaine A5 ; construction du corpus lorsque scripts/build_corpus.py sera disponible.
- Décisions : aucune.
- Risques ou blocages : pytest exécuté sans tests collectés ; scripts/check_style.py absent du dépôt initial, contrôle officiel impossible ; aucune installation ni utilisation du réseau.
- Prochaine session : validation humaine du lot 1, puis préparation du lot 2 dev.

### 2026-10-27 14:34 | S01 | Socle du dépôt et garde-fous | Claude Code, Sonnet 5.5
- Fait : requirements (épinglés), pyproject, .gitignore, .gitattributes, .streamlit/config.toml, LICENSE, README, models.py (contrat respecté), paquets vides, streamlit_app.py et style.css, scripts/check_style.py (règles C1 à C7) et banned_phrases.txt, tests.
- Tests : pytest : 28 passed ; ruff check : OK ; ruff format --check : OK ; check_style : OK (0 erreur) ; spacy validate : fr_core_news_md compatible.
- Reste à faire : app/i18n/ (textes centralisés, règle du paragraphe 9 d'AGENTS.md) non créé car hors liste de S01 ; les textes de la page d'accueil sont des constantes de streamlit_app.py.
- Décisions : D-05 complétée, D-S01-1 à D-S01-3.
- Risques ou blocages : aucun ; pip install a réussi sans modification des versions.
- Prochaine session : S02, selon docs/MASTER_PLAN.md.

### 2026-10-27 14:40 | H0 | Amorçage du dépôt | Humain
- Fait : dépôt privé créé (choix de l'humain), fichiers de démarrage versés (AGENTS.md, CLAUDE.md, docs/), branches main et dev, worktree huisclos-b sur lane-b.
- Tests : aucun, pas encore de code.
- Reste à faire : S01.
- Décisions : D-01 à D-18 (master plan).
- Risques ou blocages : aucun.
- Prochaine session : S01, socle du dépôt (Claude Code, Sonnet 5.5 High).
