# FIX2 : investigation ciblée après le NO-GO de G8R

Session manuelle Claude Code du 28 octobre 2026, piste A (dev), base G8R
`84bb7f0a5faaaf494a170c385c3c677777a4c41d` fusionnée en avance rapide.
Aucune publication, aucun tag ni push ; aucun GO global ; R8 reste bloqué.

## Verdict

| Point | État FIX2 |
| --- | --- |
| A. Échec du challenge historique | Cause établie : défaut de substitution FIX2-01. Correctif proposé et vérifié hors dépôt, **non appliqué** : le fichier en cause est hors du périmètre autorisé. |
| A. Fiabilité du harnais | Corrigé : un worker en échec cite désormais son lieu validé (fichier, fonction, ligne), sans message. |
| B. Enhanced EN | Aucun défaut général établi. Profil conservé, expérimental et non recommandé ; statut visible dans l'interface. |
| Global | NO-GO maintenu. Une session de correction autorisée sur `src/huisclos/pseudonymize/` reste nécessaire avant tout recontrôle du challenge. |

## A. Échec du challenge historique

### Faits établis

1. Le CLI de mesure G8 a terminé avec le code 2. Dans `scripts/evaluate_robustness.py`,
   `main` renvoie 2 pour toute `RuntimeError`, `ValueError` ou `OSError` de `measure`.
   Avant FIX, une exception du worker le faisait sortir en code 1, que `run_separate`
   convertissait en `RuntimeError`. Le code 2 désigne donc un échec quelconque du worker
   ou du parent, sans le situer.
2. Une sonde de 40 structures fictives ([probe_fixtures.py](probe_fixtures.py)) a parcouru
   les stades réels du worker G8 pour les deux profils FR. Seule la structure « sigle défini
   puis repris dans un nom de fichier » échoue, en substitution, dans
   `src/huisclos/pseudonymize/tokens.py:_token_tables:140`.
3. Reproduction minimale, sans modèle et avec des détections fournies à la main :
   `M. Lucien FALVERAC conteste. M. FALVERAC signe. Pièce : conclusions_FALVERAC.pdf.`
   Même échec en anglais (`statement_FALVERICK.pdf`) et avec un sigle (`contrat_BL_2024.pdf`).
4. L'unique tentative diagnostique autorisée sur le challenge historique situe l'échec
   **au même lieu**, pour les deux profils : stade `pseudonymization`, `RuntimeError`,
   `src/huisclos/pseudonymize/tokens.py`, `_token_tables`, ligne 140
   ([diagnostic_challenge.json](diagnostic_challenge.json)). Aucun autre lieu n'apparaît ;
   aucun profil n'atteint la construction du rapport.

### Cause

`group_mentions` (`src/huisclos/pseudonymize/grouping.py`) place volontairement un nom
repéré dans un nom de fichier dans un groupe distinct (D-AF-A2-7). Or `_token_tables`
indexe les jetons par type et par **texte exact** de la mention : son docstring suppose que
deux mentions de même type et de même texte appartiennent au même groupe. Depuis A2, cet
invariant est faux dès que la même écriture figure dans le texte courant et dans un nom de
fichier. `_token_tables` lève alors `RuntimeError("mention rattachée à deux groupes")`.

Dans le code de regroupement, c'est le seul chemin qui mène à deux groupes de même type
pour une même écriture : les formes du texte courant sont indexées par clé normalisée, et
une même écriture donne toujours la même clé. Ce raisonnement explique l'échec
challenge ; la tentative diagnostique en confirme le lieu, pas le document concerné.

- G7 mesurait le challenge avec le regroupement d'avant A2 : il n'échouait pas.
- C3 FR, test et dev passent : la structure n'y provoque pas de collision.
- G8-01 (panne du contrôle final) n'est **pas** la cause : l'échec survient avant le
  contrôle final, à la substitution. G8-01 reste un défaut réel, déjà corrigé par FIX.

### Conséquences hors harnais

- Interface : `review_step._pseudonymize` n'attrape que `ValueError`. Avec un tel document,
  Pseudonymize s'arrête sur une exception brute, affichée localement, dont le message cite
  la mention. Rien n'est envoyé. Test AppTest xfail strict
  `test_review_pseudonymizes_a_name_repeated_in_a_file_name`.
- Toutes les langues et tous les profils sont touchés : le défaut est dans la substitution
  commune, pas dans un détecteur.

### Correction

Le périmètre FIX2 autorise `src/huisclos/detection/` et `config.py`, mais pas
`src/huisclos/pseudonymize/` ni `app/steps/`. Aucune correction honnête n'est possible
dans les fichiers autorisés : la détection est correcte, retirer ces détections réduirait
la protection, et le harnais ne doit pas masquer un défaut du produit. Le correctif est
donc **proposé, pas appliqué** :

- [proposed_fix2_01.patch](proposed_fix2_01.patch), sur `tokens.py` seulement : le jeton
  est retrouvé par la **position** de la mention (`_owners`), avec une clé Presidio par
  groupe (`replace`), au lieu d'une table indexée par le texte. Le jeton distinct du nom
  de fichier (D-AF-A2-7) est conservé ; les contrôles d'appariement de D-S21-1 restent.
- Variante écartée : rattacher la mention du nom de fichier au groupe de même écriture
  dans `grouping.py`. Elle change D-AF-A2-7 et porterait ce fichier à 422 lignes, au-delà
  des 400 autorisées.
- Vérification dans deux worktrees temporaires détachés de HEAD, hors dépôt, supprimés
  ensuite : sans les marqueurs xfail, les 4 tests FIX2-01 passent ; la suite complète
  passe (1713 tests, [proposed_patch_full_pytest.log](proposed_patch_full_pytest.log)), puis
  94 tests ciblés avec le test d'interface ajouté ensuite.
- Dans le dépôt, les 4 tests restent `xfail(strict=True)` : 3 sur `pseudonymize` (FR, EN,
  sigle, `raises=RuntimeError`) et 1 sur le parcours d'interface. Rouges avec `--runxfail`.

À traiter par une session autorisée : appliquer le patch, retirer les quatre xfail, et
décider si `review_step._pseudonymize` doit aussi attraper une erreur de substitution par
un message clair (fichier `app/steps/`, hors périmètre FIX2).

### Harnais : diagnostic situé

`scripts/gate8_measure.py` : la réponse d'échec du worker (code 3) ajoute `path`,
`function` et `line` du dernier cadre du code mesuré (`src/huisclos/`) ou du harnais
(`scripts/`). Le message, les variables locales et la sortie d'erreur ne sont jamais lus.
Le parent ne cite ce lieu que si chemin, fonction et ligne sont tous conformes ; sinon il
garde seulement le stade et la classe. Un prochain échec réservé sera donc situé dès le
premier essai, sans tentative supplémentaire. Le comportement en cas de succès et le
contrôle final indisponible (FIX) sont inchangés.

## B. Enhanced EN

### Examiné

| Hypothèse | Méthode | Résultat |
| --- | --- | --- |
| Labels et conversion de types | Lecture de `pii_labels.py`, `gliner.py` | Six labels vers six types existants ; labels inconnus ignorés. Conforme. |
| Scores, textes et offsets | Lecture de `gliner.analyze` | Offset, score ou texte incohérent : arrêt explicite. Conforme. |
| Fenêtres et troncature | Lecture de `windows.py`, `validate_window` | Fenêtre 256, prompt complet encodé sans troncature (D-AF-A4-7). Conforme. |
| Plusieurs labels par span, spans imbriqués | Code installé GLiNER 0.2.29 (`decoding/utils.py`) puis sonde dev | `multi_label=True` et `flat_ner=False` les autorisent, et la règle 5b départage par type, pas par score. Mais **0** span à plusieurs labels et **0** paire imbriquée sur 112 résultats dev, et sur des fixtures fictives conçues pour. Hypothèse non retenue. |
| Exclusions, fusion, propagation | Lecture de `pipeline.detect`, `merge`, `conflicts` | Les candidats GLiNER suivent le chemin commun : projection, rognage, exclusions, union de même type (5a), arbitrage (5b), propagation. Aucun contournement. |
| Effet sur les protections existantes | Sonde dev par source | L'union 5a garde la source au meilleur score : 100 vrais positifs passent à `ner_gliner`, contre 58 à `pattern` en Standard. Les bornes ne font que s'élargir ; aucune protection perdue sur dev. |

### Mesures dev (code inchangé, distinctes des mesures réservées G8)

[en_dev_probe.json](en_dev_probe.json), `corpus/english_dev/dev.jsonl`, 8 documents,
seuil 0,30, GLiNER 0,70, appariement partiel micro :

| Profil | VP | FP | Précision partielle | FP par catégorie |
| --- | ---: | ---: | ---: | --- |
| Standard (`hybrid`) | 122 | 9 | 0,931298 | 6 type faux spaCy ORG, 2 sans référence spaCy ORG, 1 sans référence spaCy PERSON |
| Enhanced (`hybrid_gliner`) | 124 | 9 | 0,932331 | identiques à Standard, aucun FP propre à GLiNER |

Ces valeurs reproduisent exactement A4 (validation_v3). Elles ne disent rien de la
généralisation : Enhanced EN passait déjà ce critère sur ce dev avant G8, puis a perdu
0,134862 de précision sur C3 (0,834862 vers 0,7000, mesure G8 réutilisée par G8R).

### Conclusion

Aucun correctif général défendable n'est établi par le code et le dev : le dev ne
reproduit pas la perte, et l'hypothèse structurelle examinée est réfutée. Aucun seuil,
label, paramètre GLiNER, liste ou exception n'est modifié ; aucune calibration n'est
lancée ; aucune donnée de C3, test ou challenge n'a servi.

- Enhanced EN reste disponible en installation locale, **expérimental et non recommandé**.
  Choisi pour un document anglais, il affiche maintenant un avertissement visible
  (`sidebar.profile.status.en`), sans bascule silencieuse vers Standard.
- Standard reste le profil recommandé ; la revue humaine de chaque détection reste exigée.
- Ce changement de texte n'est pas une amélioration mesurée de la détection.
- Hypothèses ouvertes, non testables sans nouveau lot : faux positifs GLiNER sur des
  formes absentes du dev (institutions publiques, rôles génériques), puis amplifiés par la
  propagation. Une nouvelle revendication EN exige un lot indépendant rédigé après un
  nouveau gel, dans une autre session.

## Registre des essais FIX2

| N° | Essai | Corpus | Résultat |
| --- | --- | --- | --- |
| 1 | Sonde de 30 structures fictives, 2 profils FR | fictif | 60/60 sans erreur |
| 2 | Même sonde avec 10 structures alias et noms de fichiers | fictif | 2 échecs (`alias_in_file`, les deux profils), substitution, `tokens.py:_token_tables:140` |
| 3 | Reproductions minimales FR, EN, détections manuelles | fictif | 3 échecs au même lieu |
| 4 | Répétition du diagnostic, 3 documents dont 1 piège | fictif, split dev | lieu exact retrouvé, rapport non atteint |
| 5 | Répétition du diagnostic, 2 documents sans piège | fictif, split dev | deux profils complets, rapport construit en mémoire |
| 6 | Refus du challenge par le mode répétition | challenge, refusé avant lecture | `ValueError` attendu |
| 7 | **Tentative diagnostique unique du challenge historique** | challenge, mode gate | échec situé, deux profils, même lieu |
| 8 | Analyse des FP dev EN, puis sonde archivée | english_dev | voir mesures dev |
| 9 | Observation multi-labels GLiNER | english_dev et 4 fixtures | 0 multi-label, 0 imbriqué |
| 10 | Correctif proposé, suite complète | worktree temporaire | 1713 réussis |
| 11 | Correctif proposé, tests ciblés et test d'interface | worktree temporaire | 94 réussis |
| 12 | Sonde fixtures archivée ([probe_fixtures.json](probe_fixtures.json)) | fictif | résultat de l'essai 2, rejoué |

Tentative 7 : enregistrée avant lancement dans
[diagnostic_registration.json](diagnostic_registration.json) (17:35:20 UTC) : SHA de
référence G8R, arbres métier identiques, hashes du harnais diagnostique, de
`gate8_measure.py` et de `evaluate_robustness.py`, corpus `c47502d6...`, plan
`747c3721...`, seuils 0,30 et 0,10, environnement, numéro 3 des exécutions du challenge
historique dans le projet (G7 complet, G8 en échec, FIX2 diagnostique). Reçu
[diagnostic_attempt.json](diagnostic_attempt.json) écrit avant le lancement ; résultat à
17:36:40 UTC. Processus séparé par profil, `-I`, réseau refusé dans le worker et le
parent, sortie d'erreur jetée, réponse revalidée champ par champ. Export limité au stade,
à la classe, au chemin, à la fonction et à la ligne. Aucun texte, valeur, identifiant,
position, compte de documents, annotation, message, variable ni métrique. Réutilisation
diagnostique d'un corpus connu, pas une validation aveugle. Pas de relance ; le challenge
n'est pas remesuré avec le code modifié.

Le harnais diagnostique utilise `gate8_measure.final_alerts`, inchangé depuis G8, et le
code métier de G8R. `gate8_measure.py` a été modifié après la tentative ; son hash
enregistré (`bbbfd93a...`) décrit la version FIX utilisée par la tentative.

## Contrôles de clôture

| Essai | Résultat | Suite |
| --- | --- | --- |
| pytest complet 1 ([log](closure-pytest-attempt1.log)) | 2 échecs : deux tests anciens attendaient les textes « until G8 » | assertions alignées sur les nouveaux statuts |
| pytest complet 2 ([log](closure-pytest-attempt2.log)) | 1712 réussis, 4 xfail stricts | |
| ruff check 1 ([log](closure-ruff_check-attempt1.log)) | 6 lignes trop longues dans app/i18n après conversion des accents en échappements | chaînes recoupées, contenu identique |
| ruff check, ruff format --check, check_style, git diff --check | conformes ; style : 0 erreur, 15 avertissements de longueur connus | |
| pytest complet 3, arbre final ([log](closure-pytest.log)) | 1712 réussis, 4 xfail stricts, avertissement torch connu | |

Le pipeline de détection n'a pas changé : les parcours AppTest FR/EN, payload exact,
révocations, offsets, restauration et sondes hors ligne de la suite complète restent verts.

## Fichiers modifiés et comportement

| Fichier | Changement |
| --- | --- |
| `scripts/gate8_measure.py` | `code_location`, `location_detail` : lieu validé dans l'échec du worker |
| `tests/test_gate8.py` | deux assertions du contrat d'échec étendues aux trois nouveaux champs |
| `tests/test_detection_profiles.py` | deux assertions alignées sur les statuts post-G8 |
| `tests/test_fix2.py` | nouveau : 4 xfail stricts FIX2-01, contrats du lieu, diagnostic, statut UI |
| `app/sidebar.py` | avertissement Enhanced EN visible ; légende Enhanced FR mise à jour |
| `app/i18n/common.py`, `app/i18n/method.py` | statuts post-G8 en anglais et en français |
| `README.md`, `docs/USER_GUIDE.md`, `docs/LOCAL_MODELS.md` | cause du challenge et statut EN |
| `docs/POST_G7_PROTOCOL.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/PROMPTS.md` | journaux FIX2 |
| `results/fix2/` | sondes, diagnostic, registres, patch proposé, ce rapport |

Aucun détecteur, seuil, label, modèle, corpus, requirement, environnement, rapport G8/G8R
ni reçu historique n'est modifié. Aucun paquet installé ; aucun accès réseau ajouté.

## Statut par langue et profil

| Langue et profil | Statut |
| --- | --- |
| FR Standard | Gains G8 conservés ; challenge historique bloqué par FIX2-01, commun à tous les profils |
| FR Enhanced | Expérimental ; même blocage FIX2-01 |
| EN Standard | Expérimental avec réserves fortes (22/100 entités exposées avant revue en G8) ; FIX2-01 le concerne aussi |
| EN Enhanced | Expérimental, non recommandé, avertissement visible ; aucun correctif de précision établi |

## Soumission au contrôle indépendant

- SHA : le commit `FIX2 : corrections ciblées après recontrôle bilingue` sur dev, enfant
  direct de `84bb7f0`.
- Paramètres à figer, inchangés depuis A4 et G8 : plans `plan_fr.json`, `plan_en.json`,
  `plan_historical_fr.json` de results/gate8 ; seuil 0,30 en FR et en EN ; GLiNER 0,70 ;
  contrôle final 0,10 ; marges 0,02 en précision et 0,01 en surmasquage ; bootstrap
  2000 tirages, graine 45 ; OMP/MKL à 2 threads, hors ligne, `HUISCLOS_MODELS_DIR` sur
  `pilotage/post_g7_assets`.
- Un recontrôle sur ce SHA peut vérifier le diagnostic, le harnais, le statut UI et le
  patch proposé. Il ne doit **pas** remesurer le challenge : FIX2-01 n'étant pas corrigé
  dans le dépôt, l'échec se reproduirait à l'identique.

## Points restant bloquants

1. FIX2-01 non corrigé dans le dépôt : appliquer le patch proposé dans une session
   autorisée sur `src/huisclos/pseudonymize/tokens.py`, et traiter le message d'erreur de
   `app/steps/review_step.py`.
2. Après correction, la mesure réservée du challenge historique reste à faire dans une
   session indépendante expressément autorisée. Ce sera la quatrième exécution de ce corpus,
   déjà connu : elle ne vaudra pas validation aveugle fraîche.
3. Enhanced EN : aucune revendication possible sans nouveau lot indépendant, rédigé après
   un nouveau gel.
4. Les corpus restent petits, fictifs, d'un auteur ou d'une famille de modèle ; aucun score
   ne garantit l'anonymat ni l'absence de fuite.
