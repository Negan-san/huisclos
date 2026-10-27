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

### 2026-10-27 19:45 | R2 | Recette de la gate G2 | Claude Code, Sonnet 5.5
- Fait : lane-b fusionnée dans dev (avance rapide, sans conflit). Verdict G2 : GO (recontrôle de 19:33). Recette sur textes fictifs dans un dossier temporaire hors dépôt, supprimé ensuite.
- Étape 1 : OK. Texte de cinq lignes, roundtrip_cli.py code 0, mode exact, 13 remplacements ; aucun nom, adresse, e-mail, téléphone, SIREN, numéro de dossier ni IBAN visible dans la sortie pseudonymisée.
- Étape 2 : OK. Réponse altérée (crochets retirés, minuscules, PERSONNE_9 inventé) avec --llm : mode tolérant, 7 formes altérées restaurées, valeurs correctes, 1 forme inconnue signalée (PERSONNE_9, position 257).
- Étape 3 : KO. lettre.docx (python-docx, en-tête de cabinet) et lettre.pdf (fpdf2) : roundtrip_cli.py échoue avec UnicodeDecodeError, car le script ne lit que du texte UTF-8 (read_text). Diagnostic hors script avec io.readers.read_document : DOCX et PDF lus (377 caractères chacun, en-tête inclus), aucune valeur identifiante visible, aller-retour exact. Le moteur est sain ; la CLI ne prend pas en charge DOCX ni PDF.
- Tests : pytest 677 passed ; ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants (merge.py, grouping.py).
- Constats mineurs : le mot Objet est masqué comme société (gêne, pas une fuite) ; un en-tête de cabinet est masqué comme personne ou adresse, ce qui est le comportement voulu.
- Verdict de recette : non conforme à l'étape 3 telle qu'écrite. Aucun fast-forward de main, aucun tag gate-2, aucun push.
- Reste à faire : faire lire DOCX et PDF à scripts/roundtrip_cli.py via read_document (une session à planifier), ou valider par l'humain que le diagnostic io.readers suffit pour poser gate-2.

### 2026-10-27 19:33 | G2 recontrôle | Pseudonymisation, restauration et fichiers validés | Codex
- Fait : dev fusionnée en avance rapide sans conflit, arbre propre au départ. Revue des modules et tests autorisés ; G2-R1 à G2-R4 vérifiés, aucun nouveau défaut de logique constaté. Aucun module métier corrigé ; ajout d'un test des 24 permutations de quatre mentions, avec nom seul et initiale avant leurs deux candidats, jetons distincts et positions stables.
- Tests : contrôle initial, 676 passed ; contrôle final, 677 passed, aucun xfail ni test ignoré. Ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants. Cache pytest final hors dépôt après un avertissement de droits au premier passage.
- Scénarios : les deux CLI sortent avec le code 0, 16 remplacements exacts ; réponse LLM, 8 restaurations dont 6 formes altérées et seul PERSONNE_9 inconnu. Aller-retour exact à 100 % sur 18 documents (12 dev, 6 test), également depuis le JSON relu ; altérations aléatoires restaurées. Corpus lu seulement par les scripts et tests, sans affichage de contenu.
- Fichiers : DOCX et PDF fabriqués à la volée puis restaurés depuis le JSON ; corps, tableaux, cellules fusionnées et six variantes d'en-têtes et pieds couverts. Neuf codes d'erreur de lecture testés ; JSON relu sans perte ; accès texte explicites en UTF-8, accès binaires sans encodage.
- Reste à faire et repli : aucun blocage de gate. Conserver les tables positionnées actuelles ; une ancienne table sans positions ne distingue pas les jetons littéraux et ne protège pas contre une liste externe complète mais décalée (limite D-G2fix-2).
- Décisions : aucune. Risques : limites documentées du mode tolérant (forme canonique), du PDF sans OCR et de la mise en page non conservée ; aucune donnée réelle, aucun réseau, aucune installation, aucun tag ni push.
- Verdict et suite : GO ; lancer le pilotage G2 --go après le compte rendu, puis suivre ses prompts.

### 2026-10-27 19:28 | G2-fix | Positions persistées prioritaires en mode exact (G2-R4) | Claude Code, Opus 5.5
- Fait : lane-b fusionnée en avance rapide. Trois xfails G2-R4 retirés, trois échecs constatés, puis succès. Cause : restore acceptait une liste externe dont l'inventaire (jeton, original) correspondait, sans relier chaque original à sa position. Correction : quand la table porte des positions, elles font foi et la liste externe est ignorée ; la liste ne sert plus qu'aux anciennes tables sans positions. Aucun changement de models.py.
- Tests : pytest : 676 passed, aucun xfail ; ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants.
- Reste à faire : rejouer la gate 2.
- Décisions : D-G2fix-2.
- Risques ou blocages : test_inconsistent_occurrences_fall_back_to_tolerant, hors des points ouverts, contredisait la correction (table positionnée, liste décalée : mode exact désormais) ; renommé en test_inconsistent_occurrences_never_give_a_wrong_text, avec un cas positionné (exact) et un cas ancien JSON (tolérant). Une ancienne table sans positions reste exposée à une liste complète mais décalée.
- Prochaine session : suivre la sortie du pilotage G2.

### 2026-10-27 19:22 | G2 recontrôle | Positions des occurrences et contrôle des fichiers | Codex
- Fait : dev intégrée en avance rapide sans conflit ; arbre propre au départ. Relecture des modules et tests autorisés, sans ouvrir le corpus. G2-R1, G2-R2 et G2-R3 corrigés auparavant et vérifiés. Aucun module métier corrigé dans ce recontrôle ; trois tests xfail stricts ajoutés pour G2-R4.
- Tests : contrôle initial, 672 passed ; contrôle final, 672 passed et 3 xfailed stricts, aucun test ignoré. Ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants. Les trois nouveaux cas échouent aussi avec --runxfail, sur des valeurs fictives seulement.
- Scénarios : deux CLI de code 0, 16 remplacements exacts, puis 8 restaurations dont 6 formes altérées et seul PERSONNE_9 inconnu. Aller-retour exact sur les 18 documents du corpus, JSON relu inclus ; altérations aléatoires restaurées. DOCX et PDF fabriqués à la volée et restaurés depuis le JSON ; neuf codes d'erreur de lecture testés, tableaux et variantes d'en-tête couverts. Accès texte explicites en UTF-8 ; accès binaires sans encodage.
- Reste à faire : G2-R4, restore compare l'inventaire (jeton, original) des occurrences fournies à celui de la table, mais pas leur association aux positions persistées. Déplacer une occurrence sur un jeton littéral restaure le mauvais emplacement ; permuter les positions de Jean DUPONT et Dupont renvoie Dupont et Jean DUPONT, toujours en mode exact. Deux tests pour le littéral avant ou après, un test pour les variantes permutées.
- Décisions : aucune ; le défaut de logique de reidentify.py reste documenté sans correction, conformément au prompt de gate. Un seul cycle de mise en forme des tests, aucun changement hors périmètre.
- Risques ou blocages : verdict NO-GO : une liste complète mais décalée peut encore produire un faux mode exact. Repli : appeler restore avec la nouvelle table JSON positionnée et sans fournir de liste d'occurrences externe ; conserver les anciennes limites des JSON sans positions. Aucun réseau ni installation ; aucune donnée réelle, aucun tag ni push.
- Prochaine session : corriger G2-R4, retirer ses trois xfails après constat de leurs échecs puis succès, et rejouer G2 ; suivre la sortie du pilotage G2 --nogo.

### 2026-10-27 19:20 | S31 | Charte, squelette de l'interface, étape Import | Claude Code, Sonnet 5.5
- Fait : lane-b déjà intégrée (avance rapide, 619 tests verts avant travail). Navigation st.navigation à trois pages (Pseudonymize, Evaluation, Method & limits), état (state.py), charte (ui_common.py, style.css, ENTITY_STYLES), barre latérale avec remise à zéro confirmée, étape Import complète (collage, fichier, cas d'exemple, détection avec empreinte, un message par code d'erreur), squelettes Review et Restore, page Method avec schéma graphviz, i18n EN avec t(). demo_case_fr.txt régénéré par build_corpus.py : aucun changement.
- Tests : pytest : 672 passed (36 tests d'interface dans test_app_smoke.py) ; ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants. Import vers Review sur l'exemple : 4,2 s au premier appel (chargement de spaCy), 0,2 s ensuite.
- Reste à faire : écrans Review (S32) et Restore (S33), page Evaluation (S43), chaînes FR ; vérification visuelle dans un vrai navigateur (CSS non vu hors AppTest).
- Décisions : D-S31-1, D-S31-2.
- Risques ou blocages : le test ancien test_home_page_renders de tests/test_smoke.py (hors liste) a dû être retiré, la page d'accueil minimale n'existant plus. Une session G2 a modifié src/ et tests/ dans le même dossier en parallèle ; un git stash/pop de ma part a brièvement retiré ces modifications (restaurées à l'identique, aucune n'est dans mon commit). Référence au guide du CNB (mars 2026) reprise du prompt, non vérifiée.
- Prochaine session : suivre la sortie du script de pilotage S31.

### 2026-10-27 19:14 | G2-fix | Positions JSON et restauration complète | Codex
- Fait : dev synchronisée avec lane-b sans conflit. Cinq xfails retirés, leurs cinq échecs constatés avant correction, puis succès. G2-R1 : positions conservées dans les occurrences JSON ; G2-R2 : sociétés sans crochets reconnues seulement avec tiret bas ou tiret ; G2-R3 : inventaire des occurrences comparé à la table avant le mode exact, repli sur la table si incomplet. Aucun changement de models.py.
- Tests : ciblés, 115 passed ; copie temporaire du dernier commit avec les seuls changements G2, pytest -q : 640 passed, aucun xfail ; ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants. Dernier pytest du dossier partagé : 673 passed. Lecture des anciens JSON sans positions, positions invalides, collisions littérales, variantes, listes vides, partielles et avec doublons vérifiées.
- Reste à faire : rejouer la gate 2 indépendamment ; les travaux d'interface présents en parallèle restent hors périmètre.
- Décisions : D-G2fix-1 ; extension compatible du JSON version 1 et refus des formes de société ambiguës séparées par une simple espace.
- Risques ou blocages : dans le dossier partagé, premier contrôle global à 639 passed et 1 échec du test d'accueil, puis 673 passed après évolution parallèle de l'interface ; dernier Ruff partagé : 5 erreurs et 4 fichiers non formatés hors périmètre, laissés intacts. Copie G2 isolée entièrement verte. Les anciens JSON sans positions ne permettent toujours pas de distinguer une collision littérale. Aucun réseau, aucune installation, aucun contenu du split test ouvert par l'agent.
- Prochaine session : suivre le pilotage G2 et relancer le contrôle croisé ; aucun tag ni push.

### 2026-10-27 20:05 | G2 | Contrôle de la pseudonymisation et des fichiers | Codex
- Fait : dev fusionnée sans conflit ; arbre propre au début du contrôle. Revue indépendante des regroupements, jetons, occurrences, JSON, restauration et entrées-sorties. Correction simple en un cycle : la fixture LLM référençait une date de naissance absente de mini_case ; elle utilise maintenant une adresse disponible, avec un test du scénario réel. Aucun module métier modifié.
- Tests : contrôle initial, 619 passed ; contrôle final, 622 passed et 5 xfailed stricts, aucun test ignoré. Ruff check et format : OK ; check_style : 0 erreur, 2 avertissements existants. Aller-retour exact sur les 18 documents du corpus, également depuis le JSON relu ; scénarios CLI : code 0, 16 remplacements exacts, puis 8 restaurations dont 6 formes altérées et seul PERSONNE_9 inconnu. DOCX et PDF fabriqués puis lus, pseudonymisés et restaurés depuis le JSON : OK ; neuf codes d'erreur de lecture testés, en-têtes et tableaux inclus. Cache pytest redirigé hors dépôt après un avertissement de droits initial.
- Reste à faire : G2-R1, le JSON ne conserve pas les positions et transforme un jeton littéral du texte source en identité (2 xfails) ; G2-R2, la phrase ordinaire LA SOCIETE A SIGNE LE CONTRAT. devient LA Valmont SARL SIGNE LE CONTRAT. (1 xfail) ; G2-R3, une liste d'occurrences vide ou partielle laisse des jetons tout en annonçant le mode exact (2 xfails). Les cinq échecs ont aussi été confirmés avec --runxfail sur les seuls cas fictifs concernés.
- Décisions : aucune ; conformément au prompt de gate, les défauts de logique de reidentify.py sont documentés par des tests, sans correction dans cette session. Les variantes de date de naissance restent couvertes séparément après la correction de la fixture.
- Risques ou blocages : verdict NO-GO malgré les contrôles automatiques sans échec inattendu : la restauration sans perte depuis le JSON et la conservation des phrases ordinaires ne sont pas garanties. Repli : conserver les occurrences positionnées complètes dans la session, refuser les collisions avec un jeton littéral et faire valider les formes sans crochets ; ne pas transmettre une liste partielle. Aucun réseau, aucune installation, aucun contenu du corpus ouvert par l'agent.
- Prochaine session : corriger G2-R1, G2-R2 et G2-R3, retirer leurs xfails une fois les régressions corrigées, puis rejouer G2. Aucun tag ni push ; suivre la sortie du script de pilotage G2 --nogo.

### 2026-10-27 18:55 | S42 | Métriques, configurations et choix du seuil | Codex
- Fait : dev fusionnée sans conflit ; métriques exactes et partielles par type, micro et macro, appariement unique par recouvrement décroissant, fuite par union des caractères et entités exposées. Comparaison des quatre configurations locales, balayage hybride de 0,30 à 0,95 et six sorties dans results/ ; seuil retenu 0,30 selon D-13. Erreurs exactes exportées pour dev seulement.
- Tests : pytest -q : 550 passed, dont 19 nouveaux tests sans modèle sous no_network ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 2 avertissements existants (merge.py et grouping.py). Évaluation dev complète en 32,3 s ; seconde exécution : les trois CSV identiques octet pour octet. Les branches test et all sont vérifiées uniquement sur des fichiers fictifs temporaires, avec detect simulé.
- Reste à faire : évaluation du véritable split test à la gate 4 ; configuration CamemBERT à reprendre après implémentation de son reconnaisseur local en S44.
- Décisions : aucune ; application de D-07, D-12 et D-13. Les conventions d'appariement, de macro sur onze types et de divisions nulles sont explicitées dans results/summary.md ; les empreintes concernent seulement les splits évalués.
- Risques ou blocages : aucun blocage ; hybride sur dev, partiel micro : précision 0,8942, rappel 0,9688, F2 0,9529, fuite 0,0548 et 5 entités entièrement exposées. transformers est installé mais huisclos.detection.camembert est absent : ligne omise et note dans les rapports. Aucun réseau, aucune installation, aucune règle de détection modifiée, aucune lecture du vrai split test.
- Prochaine session : suivre la sortie du script de pilotage S42 ; conserver le test pour la gate 4 et relire les erreurs dev lors d'une session autorisant les règles.
### 2026-10-27 18:59 | S22 | Réidentification tolérante et test aller-retour | Claude Code, Opus 5.5
- Fait : lane-b fusionnée (lecture et export S23, sans conflit). reidentify.py : restore et RestoreResult (text, mode, replaced, altered, unknown, missing), find_token_forms. Mode exact par les occurrences positionnées, ou par les occurrences de la table si chaque jeton apparaît le nombre de fois attendu ; sinon mode tolérant (libellés FR et EN sans casse ni accents, séparateurs tiret bas, tiret bas échappé, espace, tiret ; paires de crochets échappées ou non ; bornes de fin ; forme sans crochets acceptée seulement en majuscules ou avec un tiret bas). scripts/roundtrip_cli.py, fixture llm_response_altered.txt.
- Tests : pytest : 600 passed (69 nouveaux, dont 20 textes faits main en mode exact et l'aller-retour sur les 18 documents dev et test : exact à 100 %, puis tolérant après 288 altérations aléatoires à graine fixe, unknown vide) ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 2 avertissements existants (merge.py, grouping.py).
- Reste à faire : brancher restore sur l'étape Restore de l'interface (chargement de la table, affichage de altered et unknown).
- Décisions : D-S22-1.
- Risques ou blocages : le mode tolérant restaure la forme canonique, pas l'écriture exacte de chaque mention ; une forme sans crochets en majuscules ("PERSONNE 1") dans une réponse est restaurée même si le LLM l'employait comme mot ordinaire. Aucun défaut constaté dans tokens.py ni mapping.py.
- Prochaine session : suivre la sortie du script de pilotage S22.

### 2026-10-27 18:40 | S23 | Lecture et export des documents | Codex
- Fait : dev fusionnée en avance rapide sans conflit ; API installées de python-docx, pypdf et fpdf2 consultées. Lecture locale TXT (UTF-8, BOM, repli cp1252 signalé), DOCX (corps, tableaux, cellules fusionnées, variantes des en-têtes et pieds de page sans répétition) et PDF natif ; normalisation NFC et LF, espaces insécables conservés, limites et neuf codes d'erreur. Exports TXT sans BOM et DOCX avec titre, lignes conservées et métadonnées personnelles vidées.
- Tests : pytest -q : 449 passed, dont 40 nouveaux tests sous no_network ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 1 avertissement existant (merge.py, 361 lignes). Premier passage : erreurs de préparation dues aux identifiants de paramètres trop longs et au cache temporaire inaccessible ; identifiants raccourcis, TEMP/TMP et cache pytest redirigés vers des dossiers accessibles hors dépôt.
- Reste à faire : raccorder ces fonctions aux étapes Import et Restore de l'interface.
- Décisions : aucune ; application de D-15 et D-16, avertissement cp1252 fourni sous forme de code pour traduction par l'interface.
- Risques ou blocages : aucun blocage ; PDF sans texte exploitable et PDF chiffrés refusés, sans OCR ; la mise en page source n'est pas conservée. Aucune installation, aucun appel réseau ni lecture du split test.
- Prochaine session : suivre la sortie du script de pilotage S23 ; commit limité aux deux modules, à leurs tests et aux deux journaux.
### 2026-10-27 18:44 | S21 | Regroupement des mentions, jetons stables, table de correspondance | Claude Code, Opus 5.5
- Fait : lane-b déjà intégrée (rien à fusionner). models.py complété (TokenStyle, EntityGroup, Occurrence, PseudonymizationResult). grouping.py : clés normalisées par type, règles PERSON (mêmes mots, initiale, nom seul, prénom seul), ambiguous_with en cas de doute. tokens.py : numérotation par type et par première apparition, lettres pour les sociétés, substitution par presidio-anonymizer (opérateur custom), avertissement sur les chaînes en forme de jeton. mapping.py : schéma JSON version 1, to_json, from_json validé, MappingError.
- Tests : pytest : 491 passed (82 nouveaux) ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 2 avertissements (merge.py 361 lignes, grouping.py 352 lignes, sous le maximum de 400).
- Reste à faire : pseudonymize.reidentify (modes exact et tolérant de D-10) ; branchement sur l'étape Review de l'interface.
- Décisions : D-S21-1.
- Risques ou blocages : created_at rend la table différente d'une exécution à l'autre ; le déterminisme octet pour octet suppose un created_at imposé (paramètre prévu). Un nom seul partagé par deux personnes reçoit son propre jeton : la revue humaine doit trancher. Les réponses du LLM qui écrivent un jeton altéré relèvent de la restauration.
- Prochaine session : suivre la sortie du script de pilotage S21.

### 2026-10-27 17:50 | R1 | Recette de la gate G1 | Claude Code, Sonnet 5.5
- Fait : dev fusionné avec lane-b (avance rapide, sans conflit) ; verdict G1 lu : GO. Étape 1 (detect_cli sur mini_case_fr.txt, config hybrid) : OK, 16 détections ; les quatre formes de Dupont (Jean DUPONT, Dupont, DUPONT, Marie DUPONT, soit cinq occurrences) sont masquées ; la juridiction (Conseil de prud'hommes de Nanterre), l'article L. 1232-6 et le mot "petit" restent en clair ; chargement 3,9 s, détection 0,09 s. Étape 2 (paragraphe fictif de six lignes, hors dépôt, supprimé ensuite) : OK, aucune fuite de nom, 15 détections (11 PERSON, 1 ORGANIZATION, 1 ADDRESS, 2 PHONE). Constat sans fuite : "Valmont" seul est typé PERSON (propagation et NER) au lieu d'ORGANIZATION, donc jeton [PERSONNE_n] au lieu de [SOCIETE_x] ; "Lyon" seul dans une phrase reste en clair car LOCATION est désactivé par défaut.
- Tests : pytest : 409 passed ; ruff check : OK ; ruff format --check : OK ; check_style : 0 erreur, 1 avertissement existant (merge.py, 361 lignes).
- Reste à faire : requalifier la propagation d'une forme courte de société ; étape 3 de la recette (installation de torch, transformers et du modèle camembert-ner pour S44) exécutée après le tag, résultat dans le compte rendu de session ; aucun fichier requirements modifié.
- Décisions : aucune.
- Risques ou blocages : le typage de la forme courte d'une société en PERSON est sans effet sur le secret mais fausse le libellé du jeton.
- Prochaine session : suite du plan après la gate G1 ; tag gate-1 posé sur main si le push réussit.

### 2026-10-27 17:25 | G1 | Recontrôle après les corrections ciblées : GO | Codex
- Fait : arbre initial propre ; dev fusionnée en avance rapide sans conflit (ba1d69c) ; règles, décisions, entrées S11 à S13, moteur, tests correspondants et signatures Presidio installées relus. Les onze cas de régression des deux contrôles précédents sont corrigés et leurs tests passent. Contrat models.py, merge.py et propagation.py inchangés pendant ce contrôle.
- Corrections : exclusions.py accepte aussi "d'X" et les apostrophes typographiques pour les modèles "de X", ainsi que SAINT, SAINTE, ST et STE devant un lieu ; data/exclusions_fr.txt exclut les articles et lois sans dépendre de leur casse. Deux cycles, chacun avec échecs de régression constatés avant correction : 12 puis 5 cas. test_exclusions.py et test_pipeline.py renforcés ; 22 cas supplémentaires au total, dont SIREN et SIRET préservés par les exclusions.
- Tests : pytest standard initial : 333 passed, 54 erreurs de permissions du dossier temporaire Windows ; avec --basetemp local : 387 passed avant correction. Validation finale par pytest -q avec TEMP et TMP dans .pytest_cache/g1-third-temp : 409 passed, 0 xfail, 10,50 s. Ruff check, ruff format --check et git diff --check : OK ; check_style : 0 erreur, 1 avertissement existant (merge.py, 361 lignes, sous le maximum de 400). Helpers d'assertion et contextes pytest.raises relus ; aucune assertion vide ou tautologique relevée.
- Scénarios : CLI hybrid 16/16 spans exacts, patterns_only 11/16, ner_only 8/16 ; hybrid reste à 16/16 avec U+00A0, U+202F et apostrophes typographiques. Aucun chevauchement, Detection.text exact, juridiction et article préservés sur mini_case et les régressions adverses. Chargement à froid : 3,68 s ; après chargement, trois passages de 10 000 caractères : 0,365 à 0,373 s ; 50 000 caractères répétés depuis mini_case : 1,897 à 2,014 s.
- Revue : tous les reconnaisseurs locaux sur une ligne de 5 000 caractères sans espace : 0,002 s ; initiales majuscules : 0,002 s ; 50 001 caractères en capitales : 0,023 s ; voie longue : 0,002 s. Corse 2A/2B, exception La Poste, IBAN suivi de capitales, scores D-07, ordre d'arrivée à la fusion, mots courants en minuscules et identifiants à clé : OK. Exemples corrigés : un nom fictif Angers ne se propage plus dans "Cour d'appel d'Angers" ; "ARTICLE L. 1232-6 DU CODE DU TRAVAIL" et "TRIBUNAL JUDICIAIRE DE SAINT DENIS" restent lisibles.
- Réseau et périmètre : chargement à froid, CLI, variantes et mesures exécutés avec connect, create_connection et getaddrinfo bloqués ; tests test_no_network verts. Registres limités aux reconnaisseurs français HuisClos, aucun import direct de tldextract dans detection, aucune installation ni lecture du split test. Seuls les quatre fichiers de correction et ces deux journaux sont modifiés.
- Ouverts, risques et suite : aucun défaut bloquant restant, aucun test xfail ; mesurer ensuite sur dev les effets des exclusions et de la propagation, avec revue humaine des détections. Les limites déjà documentées en D-G1fix-2 subsistent pour les références d'un seul mot incluses dans un nom. Aucune nouvelle décision. Verdict GO ; commit "G1 : contrôle du moteur de détection", puis pilotage G1 --go ; ni tag ni push.

### 2026-10-27 16:46 | G1-fix | Correction ciblée après la gate 1 rejouée | Claude Code, Opus 5.5
- Fait : dev avancée sur lane-b (avance rapide, commit G1 rejoué). Les six xfail stricts retirés, six échecs constatés puis corrigés. exclusions.py : is_legal_reference (passage de plusieurs mots) ; "Saint", "Sainte", "St", "Ste" suivi d'un espace relié à un seul nom de lieu (E1). merge.py : cutting_spans ajoute aux passages franchissant une borne les références juridiques contenues ; les restes eux-mêmes exclus sont écartés (M5). propagation.py : une occurrence qui contient une référence juridique est ignorée (P2).
- Tests : pytest : 387 passed, 0 xfail (avec --basetemp .pytest_cache/g1fix2) ; ruff check et ruff format --check : OK ; check_style : 0 erreur, 1 avertissement (merge.py, 361 lignes, sous le maximum de 400). detect_cli hybrid sur mini_case : 16 détections, comme avant. "La société Tribunal judiciaire de Nanterre SARL." : aucune détection ; "Tribunal judiciaire de Saint Denis, Paul Martin" : seul Paul Martin.
- Reste à faire : rejouer la gate G1 ; mesurer sur dev l'effet de la soustraction des références contenues.
- Décisions : D-G1fix-2 (complète D-G1fix-1).
- Risques ou blocages : une référence d'un seul mot (URSSAF, RGPD) contenue dans un nom reste masquée ; "Saint" suivi d'un prénom peut l'absorber, le nom restant signalé par soustraction. Aucun fichier du split test lu ; models.py inchangé.
- Prochaine session : suivre la sortie du script de pilotage G1.

### 2026-10-27 16:36 | G1 | Recontrôle après G1-fix : NO-GO | Codex
- Fait : arbre initial propre ; dev fusionnée en avance rapide, sans conflit (4a2f8da) ; règles, entrées S11 à S13, G1-fix, moteur, signatures Presidio installées et tests correspondants relus. Les cinq défauts du premier G1 sont corrigés et leurs tests passent. Aucun code métier modifié pendant ce recontrôle.
- Tests : pytest standard : 327 passed, 54 erreurs de permissions dans le dossier temporaire Windows ; avec --basetemp .pytest_cache/g1-recheck-initial : 381 passed. Validation finale avec un dossier temporaire local : 381 passed, 6 xfailed ; les six nouveaux cas échouent avec --runxfail. Ruff check, ruff format --check, git diff --check : OK ; check_style : 0 erreur, 1 avertissement existant (merge.py, 343 lignes). Assertions, helpers et contextes pytest.raises relus ; le test d'identité de load_exclusions vérifie réellement son cache.
- Scénarios : CLI et comparaison des spans attendus : hybrid 16/16, patterns_only 11/16, ner_only 8/16 ; aucun chevauchement, textes exacts, juridiction et article de mini_case préservés, y compris avec U+00A0, U+202F et apostrophes typographiques. Chargement : 3,92 s ; trois passages après chargement : 10 000 caractères en 0,393 à 0,415 s, 50 000 en 2,099 à 2,153 s. Tous les reconnaisseurs locaux : ligne sans espace de 5 000 caractères en 0,003 s ; initiales majuscules en 0,003 s ; 50 001 caractères en capitales en 0,025 s ; voie longue en 0,003 s.
- Revue : Corse 2A/2B, SIRET La Poste, IBAN valide ou à clé fausse suivi de mots en capitales, scores D-07, ordre d'arrivée à la fusion, mots courants en minuscules, identifiants à clé préservés par les exclusions : OK. Registres limités aux reconnaisseurs français HuisClos ; aucun import direct de tldextract dans detection ; tests et mesures exécutés avec sockets bloquées, y compris chargement à froid. Aucune installation ni lecture du split test.
- Ouverts : G1-M5, test_merge.test_enclosed_legal_reference_is_not_masked (deux cas), confirmé avec spaCy par test_pipeline.test_court_is_not_masked_when_fully_inside_a_ner_name : une juridiction ou un article entièrement inclus dans un nom est masqué ; exemple observé : "La société Tribunal judiciaire de Nanterre SARL.". G1-P2, test_propagation.test_propagation_skips_an_enclosed_legal_reference (deux cas) : le même défaut autorise l'ajout d'une occurrence englobant l'exclusion. Ces défauts de logique restent en xfail strict, sans modification de merge.py ni propagation.py.
- Autre limite et replis : G1-E1, test_exclusions.test_court_with_an_unhyphenated_compound_place_is_fully_excluded (xfail strict) : "Tribunal judiciaire de Saint Denis" exclut seulement jusqu'à "Saint", puis spaCy signale "Denis". M5 : revoir les bornes à la main avant tout envoi, puis distinguer les références juridiques des formes juridiques internes (SARL) pour soustraire les premières. P2 : désactiver la propagation jusqu'à la correction. E1 : revue manuelle des juridictions à lieu composé ; prévoir des variantes explicites sans absorber un nom adjacent. Une simple extension aux mots à majuscule menacerait le rappel des personnes.
- Décisions et suite : aucune nouvelle décision ; D-G1fix-1 explique la limite des exclusions internes, mais le critère de gate "juridiction et article jamais détectés" reste violé. Verdict NO-GO ; quatre fichiers de tests renforcés, PROGRESS et PROMPTS mis à jour ; corriger les trois points ouverts, retirer les six xfail après validation et rejouer G1. Commit G1, puis pilotage G1 --nogo ; ni tag ni push.

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
