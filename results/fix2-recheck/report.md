# FIX2R : recontrôle indépendant de FIX2

Session Claude Code du 28 octobre 2026, piste B (lane-b), SHA figé FIX2
`a29532c` fusionné en avance rapide sans conflit (dérogation explicite à la branche
mouvante). Aucune exécution sur test, challenge, C3 ou all ; aucun réglage, aucun paquet,
aucun tag, push ni R8. Toutes les valeurs utilisées sont fictives et écrites pour FIX2R.

## Verdict

| Point | Verdict |
| --- | --- |
| 1. Reproductions FIX2-01 et xfail stricts | Conforme. **Cause établie : oui.** |
| 2. Harnais diagnostique | Conforme : registre antérieur au reçu, empreintes égales aux blobs, export sans contenu. |
| 3. Correctif proposé | **Patch recevable : oui, sous trois conditions** (voir point 3). |
| 4. Lieu du worker et statut Enhanced EN | Conforme ; deux limites mineures, non bloquantes. |
| 5. Périmètre de FIX2 | Conforme : aucun corpus, seuil, modèle, rapport G8/G8R, src/ ni requirement modifié. |
| Global | FIX2 confirmé. NO-GO maintenu tant que FIX2-01 n'est pas corrigé dans le dépôt. |

## 1. Reproductions et xfail stricts

Faits :

- `pytest tests/test_fix2.py` : 13 réussis, 4 xfail stricts (3 cas `pseudonymize` FR, EN,
  sigle avec `raises=RuntimeError`, 1 parcours Review AppTest).
- Avec `--runxfail` : les 4 échouent, `RuntimeError: mention rattachée à deux groupes`,
  `src/huisclos/pseudonymize/tokens.py:140`, appelé depuis `_substitute:164`.
- Reproductions indépendantes ([recheck_fix2.py](recheck_fix2.py),
  [recheck_fix2.json](recheck_fix2.json)), autres valeurs et autres formes de fichier :

| Cas | Détections | Résultat |
| --- | --- | --- |
| R1 FR, « Mme VARNESSE » et `attestation_VARNESSE.docx` | manuelles | échec `tokens.py:_token_tables:140` |
| R2 EN, nom en tête de fichier `KORVELL_witness.pdf` | manuelles | même lieu |
| R3 sigle défini puis repris dans `devis-QI-2025.pdf` (tirets) | manuelles | même lieu |
| P-fr, P-en, pipeline Standard réel (`hybrid`, spaCy local) | produites par `detect` | même lieu, FR et EN |
| T1 témoin : écritures différentes (nom complet, fichier) | manuelles | réussi, aucune fuite, restauration exacte |
| T2 témoin : mention du fichier ajoutée à la main (`manual`) | manuelles | réussi, un seul jeton (exception de D-AF-A2-7) |
| T3 témoin : même nom dans deux noms de fichier seulement | manuelles | réussi, un seul jeton |

Lecture du code (`grouping.py`) : `_forms_by_type` réunit les mentions de même type et de
même clé normalisée en une seule forme ; `_group_persons` place chaque forme dans un seul
groupe ; `_link_aliases` déplace des formes entières. Le seul chemin qui donne deux groupes
de même type pour une même écriture est donc la séparation entre texte courant et nom de
fichier (`in_files`, D-AF-A2-7). La ligne 140 est l'unique `raise` de `_token_tables`. Le
harnais diagnostique continue après un document en échec et déduplique les lieux : le seul
lieu exporté signifie que **chaque** document en échec du challenge a échoué à ce `raise`.

Limite : le diagnostic confirme le lieu et le mécanisme, pas le document ni la forme
exacte concernés ; un défaut situé après la substitution dans ces documents reste
invisible tant que FIX2-01 n'est pas corrigé.

**Cause établie : oui.** FIX2-01 explique l'échec du challenge historique pour les deux
profils FR ; G8-01 n'en est pas la cause.

## 2. Harnais diagnostique `diagnose_challenge.py`

Relu en entier, non relancé.

- Ordre : `diagnostic_registration.json` à 17:35:20 UTC, reçu `diagnostic_attempt.json` à
  17:35:27, résultat à 17:36:40. `run_reserved` revérifie les empreintes du harnais, du
  corpus et du plan **avant** d'écrire le reçu. `save` ouvre en mode `x` : un reçu existant
  rend toute relance impossible sans effacement visible.
- Empreintes enregistrées contre blobs indexés (SHA-256 des octets bruts, `git show`) :

| Fichier | Empreinte enregistrée | Blob | Égalité |
| --- | --- | --- | --- |
| `results/fix2/diagnose_challenge.py` | `dbe770ec...` | a29532c, `-text` | oui, disque identique |
| `scripts/gate8_measure.py` | `bbbfd93a...` | 37f98f1 (FIX) et 84bb7f0 (G8R) | oui ; la version a29532c (`045965d6...`) est postérieure, comme FIX2 le déclare |
| `scripts/evaluate_robustness.py` | `8aec0a09...` | 84bb7f0 et a29532c | oui, inchangé |

- `register` refuse un code métier différent de 84bb7f0 (`git diff --quiet` sur src, app,
  data, .streamlit, streamlit_app.py, requirements.txt) ; a29532c ne touche aucun de ces
  arbres métier hors app/ i18n et sidebar, modifiés **après** la tentative.
- Export : `valid_site` exige exactement les cinq clés stade, classe, fichier, fonction,
  ligne, chacune conforme à une forme fermée ; une réponse non conforme est remplacée par
  un lieu `unvalidated`. Les prédictions du worker restent en mémoire pour la construction
  du rapport, jamais écrites. Le JSON exporte en plus le nom du préréglage, le code de
  sortie du worker, un booléen et l'état `not_reached` : vocabulaire fermé, sans contenu.
- Écart mineur : `valid_site` accepte la ligne 0, `location_detail` du harnais G8 la refuse.
  Sans effet sur la tentative (ligne 140).

## 3. Correctif proposé `proposed_fix2_01.patch`

Appliqué dans un worktree détaché de a29532c, hors dépôt (dossier temporaire de session),
avec `git apply --check` puis `git apply` sans erreur ; les deux décorateurs xfail retirés
(4 tests) ; worktree supprimé ensuite.

- Suite complète sur l'arbre patché : **1716 réussis**, 0 échec, 0 xfail, en 147 s
  ([patched_full_pytest.log](patched_full_pytest.log)) ; 1716 = 1712 de FIX2 + les 4
  anciens xfail. Ruff check et format conformes sur le patch ; tokens.py passe de 241 à
  232 lignes.
- Propriétés vérifiées en plus, valeurs fictives : R1 rend
  `Mme [PERSONNE_1] ... Mme [PERSONNE_1] produit attestation_[PERSONNE_2].docx` ;
  restauration exacte et restauration de jetons altérés (casse, crochets ôtés) ; sortie et
  table identiques octet pour octet à created_at imposé ; mentions accolées de même groupe
  et de groupes voisins non réunies (4 occurrences pour 4 détections). Sorties dans
  [patched_properties.txt](patched_properties.txt).

Jugement contre les décisions :

- **D-AF-A2-7** : respecté. Le regroupement n'est pas modifié ; la mention du nom de fichier
  garde son groupe et son jeton propres, sauf ajout manuel ou table du dossier. La variante
  écartée par FIX2 (rattacher dans `grouping.py`) aurait changé cette décision.
- **D-S21-1** : garanties conservées, mécanisme modifié. Restent : presidio pour la
  substitution (D-04), `merge_entities_with_spaces=False`, appariement des éléments triés
  aux détections triées, contrôle du nombre et du jeton de chaque mention. Change : un
  opérateur `replace` par groupe (clé `G<group_id>`, unique par `enumerate`, conservée par
  `_merge_same_token`) au lieu d'un opérateur `custom` par type lisant une table texte vers
  jeton. La raison donnée par D-S21-1 (« même type et même texte, même jeton ») est fausse
  depuis A2 : c'est précisément FIX2-01. Le patch doit donc s'accompagner d'une décision
  qui amende D-S21-1.
- **D-S24-2 (mémoire de dossier)**, effet non signalé par FIX2 : après un document où la
  même écriture a deux jetons, la table du dossier contient deux entrées de variante
  commune (« VARNESSE »). Dans le document suivant, un groupe qui contient cette écriture
  trouve deux candidats et `match_entry` rend None : « Mme VARNESSE ... Mme Odile VARNESSE »
  reçoit `[PERSONNE_3]` au lieu de `[PERSONNE_1]`. Témoin : avec une table propre, la
  continuité est conservée et la mention du fichier rejoint `[PERSONNE_1]`. Effet prudent
  (aucune fuite, aucune confusion de personnes), mais perte de continuité du jeton.

**Patch recevable : oui**, sous trois conditions pour la session de correction :
(a) décision qui amende D-S21-1 ; (b) test qui fixe l'effet sur la mémoire de dossier et
choix consigné (accepter, ou exclure de la comparaison les entrées issues d'un seul nom de
fichier) ; (c) `review_step._pseudonymize` doit traiter une erreur de substitution par un
message clair sans citer la mention (défense en profondeur, même après correction).

## 4. Lieu du worker G8 et statut Enhanced EN

`gate8_measure.code_location`, cadres réels ou fabriqués par `compile` :

| Cas | Lieu exporté |
| --- | --- |
| Erreur FIX2-01 réelle | `src/huisclos/pseudonymize/tokens.py`, `_token_tables`, 140 ; la valeur n'y figure pas |
| Erreur de bibliothèque seule | aucun |
| Cadre hors dépôt et hors code mesuré (`results/fix2-recheck`) | aucun |
| Fichier avec espace (`src/huisclos/Lucien FALVERAC.py`) | aucun |
| Dernier cadre `<lambda>` dans `src/huisclos` | aucun (arrêt, pas de repli sur le cadre précédent) |
| Chemin quelconque contenant `/src/huisclos/` | accepté, suffixe seul (voulu pour un checkout séparé) |

`failure_detail` sur 20 sorties falsifiées : chemin absolu, `..`, `tests/`, `results/`,
chemin de plus de 120 caractères, ligne 0, flottante, nulle ou booléenne, fonction absente
donnent stade et classe seuls ; stade inconnu, `final_check` ou classe avec espace donnent
une chaîne vide ; une clé `message` en plus n'est jamais recopiée ; seule la dernière ligne
non vide est lue, et une dernière ligne non JSON annule tout le détail.

Limites mineures, non bloquantes :

1. La validation du parent est syntaxique : une valeur en forme d'identifiant
   (`FALVERAC`) passe comme fonction, nom de fichier ou classe d'erreur. C'était déjà vrai
   de la classe d'erreur depuis FIX. Le worker ne produit ces champs qu'à partir des noms
   réels du code ; aucune valeur de document n'y parvient sans code généré depuis le
   document, ce que le projet ne fait pas.
2. Une erreur dont le dernier cadre du code mesuré est une `<lambda>` ou un `<genexpr>`
   n'est pas située ; seuls stade et classe restent.

Statut Enhanced (AppTest, interfaces FR et EN, strict i18n) : document anglais et Enhanced,
un seul avertissement égal à `sidebar.profile.status.en` dans la langue d'interface, profil
conservé ; document français et Enhanced, légende `sidebar.profile.status.fr`, aucun
avertissement ; document anglais et Standard, aucun avertissement. Aucune exception.

## 5. Périmètre de FIX2

`git diff 84bb7f0 a29532c` : arbres `src`, `corpus`, `data`, `results/gate8`,
`results/gate8-recheck` identiques (mêmes identifiants d'arbre). Aucun changement dans
requirements, `.streamlit`, `pilotage`, ni fichier de configuration. Fichiers modifiés :
README, app/i18n (common, method), app/sidebar.py, docs, scripts/gate8_measure.py, tests
(test_fix2 nouveau, deux assertions de test_gate8 et test_detection_profiles), results/fix2.
Le seuil par défaut (results/threshold.json) et les plans de results/gate8 sont inchangés. Le contrôle du corpus a été fait par
identifiant d'arbre Git, sans ouvrir ni hacher aucun fichier réservé.

Écart mineur : dans `test_gate8.py`, l'égalité exacte de la réponse d'échec devient une
vérification champ par champ ; le second test garde l'ensemble exact des clés. Pas de
perte de garantie.

## Registre FIX2R

| N° | Essai | Corpus | Résultat |
| --- | --- | --- | --- |
| 1 | `tests/test_fix2.py`, puis `--runxfail` | fictif | 13 réussis et 4 xfail ; puis 4 échecs au lieu attendu |
| 2 | Reproductions et témoins, script de session | fictif | 3 échecs manuels et 2 en pipeline réel au même lieu ; 3 témoins réussis |
| 3 | Empreintes enregistrées contre blobs | aucun | égalité pour les trois fichiers |
| 4 | Patch dans un worktree temporaire, suite complète | fictif et dev de la suite | 1716 réussis, worktree supprimé |
| 5 | Propriétés du patch, mémoire de dossier et témoin | fictif | voir point 3 |
| 6 | `recheck_fix2.py` (lieux, sorties falsifiées, AppTest) | fictif | [recheck_fix2.json](recheck_fix2.json) |
| 7 | Contrôles de clôture ([pytest](closure-pytest.log), [ruff check](closure-ruff_check.log), [format](closure-ruff_format.log), [style](closure-style.log), [diff](closure-diff.log)) | aucun | 1712 réussis et 4 xfail stricts ; Ruff conforme ; style 0 erreur, 15 avertissements connus ; diff --check vide |

Aucune mesure réservée, aucun seuil ni modèle touché, aucun rapport G8, G8R ou FIX2 réécrit.
