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

### 2026-10-27 16:27 | G1-fix | Correction ciblée après la gate 1 | Claude Code, Opus 5.5
- Fait : dev avancée sur lane-b (avance rapide, commit G1). Les cinq xfail retirés, échecs constatés puis corrigés. merge.py : toutes les parties libres d'une détection rognée sont gardées (M1) ; filtre des types après la requalification (M2) ; voie suivie d'un code postal réunie à 0,70 (M3) ; un nom qui franchit la borne d'un passage exclu en perd la partie exclue et garde le reste (M4). propagation.py : une occurrence qui franchit la borne d'un passage exclu est ignorée, la forme courte reste cherchée (P1).
- Tests : pytest : 381 passed, 0 xfail (deux tests ajoutés : exclusion contenue dans un nom, propagation d'une société avec "SARL") ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 1 avertissement (merge.py, 349 lignes, sous le maximum de 400). detect_cli hybrid sur mini_case : 16/16.
- Reste à faire : rejouer la gate G1 ; mesurer sur dev l'effet des restes de noms laissés par la soustraction des exclusions.
- Décisions : D-G1fix-1 (complète D-S13-1). test_merge.test_rule3 modifié : il attendait "Nanterre, Paul Martin" entier à travers la juridiction, soit le défaut M4.
- Risques ou blocages : une exclusion entièrement contenue dans un nom ne le coupe pas ("SARL", "Cabinet"), sinon la forme juridique sortirait du span (D-09) ; un nom NER qui contiendrait toute une juridiction la masquerait encore (non observé). Aucun fichier du split test lu ; models.py inchangé.
- Prochaine session : suivre la sortie du script de pilotage G1.

### 2026-10-27 16:16 | G1 | Contrôle du moteur de détection : NO-GO | Codex
- Fait : dev fusionnée dans lane-b sans conflit ; arbre initial propre ; revue de S11 à S13, des règles, signatures Presidio installées et tests ; aucun changement au contrat models.py ni au code de merge.py et propagation.py ; aucune installation ni lecture du split test.
- Corrections : patterns.py reconnaît les espaces U+00A0 et U+202F sans décaler les spans ; person_heuristics.py accepte U+202F et consomme les suites en capitales une seule fois ; pipeline.py normalise ces blancs à longueur constante pour spaCy et refuse les sources toutes désactivées avant le repli Presidio. Six fichiers de tests renforcés.
- Tests : deux cycles de correction ; pytest : 374 passed, 5 xfailed en 10,39 s avec --basetemp .pytest_cache/g1-cycle2 ; ruff check, ruff format --check et check_style : OK (0 erreur, 0 avertissement). Pytest standard bloqué par les permissions du dossier temporaire Windows ; les cinq défauts ouverts donnent bien 5 failed avec --runxfail. Assertions directes et helpers relus, aucune assertion vide ou tautologique constatée.
- Scénarios : CLI hybrid 16/16, patterns_only 11/16, ner_only 8/16 ; hybride 16/16 aussi avec chaque espace insécable et apostrophes typographiques ; textes exacts et aucun chevauchement. Après chargement de 3,71 s : 10 000 caractères en 0,389 à 0,393 s ; 50 000 en 1,930 à 2,009 s (trois passages). Suite en capitales de 50 001 caractères : 9,01 s avant, 0,006 s après ; ligne de 5 000 caractères sans espace et longue suite à initiales majuscules : OK. Corse 2A/2B, exception La Poste et IBAN suivi de mots en capitales : OK ; fusion indépendante de l'ordre vérifiée par les tests existants.
- Ouverts : G1-M1, test_merge.test_all_sensitive_parts_survive_an_inner_identifier (une partie sensible perdue) ; G1-M2, test_merge.test_requalified_organization_respects_disabled_types (type désactivé renvoyé) ; G1-M3, test_merge.test_joined_full_address_gets_d07_score (0,55 au lieu de 0,70) ; G1-M4, test_pipeline.test_court_is_not_masked_when_a_name_crosses_its_end (NER débordant dans une juridiction) ; G1-P1, test_propagation.test_propagation_does_not_partially_overlap_an_exclusion (propagation partiellement exclue). Tous marqués xfail strict.
- Risques et replis : M1, revue manuelle et ajout des morceaux perdus avant tout envoi, puis conserver toutes les parties libres ; M2, garder les types activés par défaut, puis filtrer après requalification ; M3, conserver le seuil 0,40, puis recalculer le score des adresses réunies ; M4, corriger manuellement les bornes, puis soustraire les exclusions sans perdre les noms adjacents ; P1, désactiver la propagation, puis empêcher tout chevauchement avec une exclusion. L'essai du registre vide initial a révélé des tentatives réseau de tldextract, bloquées par l'environnement ; le cas est maintenant refusé et testé sous no_network, comme les trois presets. Aucun import direct de tldextract dans src/, aucun reconnaisseur prédéfini ou anglais dans leurs registres.
- Décisions et suite : aucune nouvelle décision ; D-07 et D-11 appliquées. Verdict NO-GO : le cas adverse M4 viole le critère de juridiction jamais détectée, malgré mini_case conforme ; les défauts M1 et P1 restent aussi ouverts. Corriger les cinq tests stricts dans une session dédiée, retirer leurs xfail après validation et rejouer G1 ; ni tag ni push. Exécuter le pilotage G1 --nogo après le commit.

### 2026-10-27 15:58 | C1 | Corpus fictif, lots 2 et 3, cas de démonstration | Codex
- Fait : lane-b déjà synchronisée avec dev ; treize sources fictives rédigées en UTF-8/LF, relues et accompagnées des consignes et listes des lots 2 et 3 ; aucune correction nécessaire aux six sources existantes.
- Construction : --check valide les 19 sources au premier cycle ; JSONL et statistiques construits, démo exportée ; répartition confirmée : 12 dev (205 entités), 6 test (99 entités), 1 demo (18 entités).
- Tests : pytest : 290 passed avec --basetemp .pytest_cache/c1-full ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement ; nouvelles sources : 296 à 337 mots, 14 à 19 annotations, UTF-8/LF, marqueurs et domaines réservés vérifiés.
- Reste à faire : revue humaine du corpus ; aucune source retirée et aucun fichier de src/, app/, scripts/ ou tests/ modifié.
- Décisions : aucune ; application de l'exception de rédaction C1 pour le split test, sans adaptation des règles de détection.
- Risques ou blocages : aucun blocage ; aucun réseau ni installation ; les clés valides sont synthétiques et ne prouvent pas l'absence de coïncidence avec un numéro attribué ; le split test redevient réservé aux scripts après C1.
- Prochaine session : exécuter le pilotage C1 après le commit et suivre sa sortie.

### 2026-10-27 15:46 | S41 | Format, construction et validation du corpus | Codex
- Fait : piste B synchronisée avec dev en avance rapide, sans conflit ; format source documenté en anglais ; chargeur JSONL typé et constructeur Markdown déterministe créés avec validation des spans, marqueurs, clés et identifiants uniques.
- Tests : pytest : 290 passed, dont 43 tests corpus ; fixture et six sources présentes validées par build_corpus.py --check ; déterminisme octet par octet, adresse multiligne, liens SIREN/SIRET, clés fausses, diagnostics fichier:ligne et export demo testés.
- Contrôles : ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement ; tests exécutés avec --basetemp .pytest_cache/s41-full pour contourner les permissions du dossier temporaire Windows.
- Reste à faire : compléter les sources jusqu'aux 12 dev, 6 test et 1 demo prévus ; construire les sorties JSONL et exporter la démo quand les sources seront complètes. Aucune sortie générée ajoutée au dépôt pendant S41.
- Décisions : aucune ; application de D-12. Les options de chemins permettent la validation isolée de la fixture et les constructions temporaires.
- Risques ou blocages : aucun appel réseau ni installation ; aucun contenu du split test consulté par l'agent ; les marqueurs répétés partagent une valeur dans chaque document et DIGITS9 reste hors annotation.
- Prochaine session : suivre le script de pilotage S41 ; les sources existantes restent inchangées.
### 2026-10-27 15:54 | S13 | Fusion des détections, propagation, pipeline | Claude Code, Opus 5.5
- Fait : dev synchronisé avec lane-b sans conflit. config.py (DetectionConfig, 5 PRESETS, seuil lu dans results/threshold.json sinon 0,40), text_utils.py (fold, civilités, formes juridiques), detection/merge.py (règles 1 à 8, ordre d'arrivée sans effet), detection/propagation.py (variantes, recherche sans accents, majuscule obligatoire), detection/pipeline.py (analyseurs Presidio en cache, registre fr), scripts/detect_cli.py, fixture mini_case (216 mots, 16 spans attendus, NIR et SIRET de synthetic_ids avec la graine 18).
- Tests : pytest : 308 passed (test_merge, test_propagation, test_pipeline, test_no_network ajoutés) ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 0 avertissement. detect_cli sur mini_case : 16 détections sur 16 attendues, détection en 0,09 s après un chargement de 3,8 s.
- Reste à faire : mesurer sur dev les effets de la propagation d'un nom de famille seul (homonymes, mots en tête de phrase) ; module detection/camembert.py attendu par pipeline (build_camembert_recognizers).
- Décisions : D-S13-1 à D-S13-4.
- Risques ou blocages : patterns_only et ner_only passent aussi par spaCy (Presidio l'exige), ce qui les rend plus lents sans changer leurs résultats ; patterns_only ne trouve aucune société sans forme juridique ni NER (constaté sur mini_case). Aucun fichier du split test lu.
- Prochaine session : suivre la sortie du script de pilotage S13.

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
