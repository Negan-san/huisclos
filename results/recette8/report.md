# R8 : recette et publication du périmètre validé après G8R2

Session R8 du 28 octobre 2026, piste A, Claude Code (Opus 5.5), branche dev.

## 1. Référence contrôlée

- Arbre initial propre ; HEAD initial `930c414dd7ae1e7128b292bfa7bac1e45f27b1e9` (FIX4).
- Fusion `git merge a838b05091485240c8b7d51d35fe9268daa17a27 --no-edit` en avance rapide,
  sans conflit ; HEAD après fusion égal à `a838b05` (G8R2).
- Code contrôlé : celui de `a838b05`. Le commit R8 ne change que README.md,
  docs/USER_GUIDE.md, docs/PROGRESS.md, PROMPTS.md, DECISIONS.md et ce dossier ; aucune
  logique, interface, modèle, seuil, dépendance ou corpus.
- Interpréteur : `.venv/Scripts/python.exe`, Python 3.12.10, Streamlit 1.66.1.

## 2. Contrôles automatiques hors ligne

Environnement : PYTHONUTF8=1, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1,
HF_HUB_DISABLE_TELEMETRY=1, OMP_NUM_THREADS=2, MKL_NUM_THREADS=2,
TOKENIZERS_PARALLELISM=false ; HUISCLOS_MODELS_DIR retiré de l'environnement global.

| Commande | Résultat | Journal |
| --- | --- | --- |
| `PY results/fix3-recheck/guarded_pytest.py -q tests results/gate8-resume/test_recheck.py results/gate8-resume/test_launch_safety.py` | 1749 passed, 265,02 s, zéro ouverture réservée refusée, code 0 | pytest.log |
| `PY -m ruff check .` | All checks passed, code 0 | ruff-check.log |
| `PY -m ruff format --check .` | 307 fichiers conformes, code 0 | ruff-format.log |
| `PY scripts/check_style.py` | 0 erreur, 15 avertissements de longueur préexistants, code 0 | style.log |
| `git diff --check` | aucun écart, code 0 | diff-check.log |
| `git diff --cached --check` | contrôlé avant le commit, aucun écart | compte rendu de session |

Avertissements déjà acceptés, consignés sans devenir bloquants : FutureWarning
`torch.jit.script`, avertissements Streamlit "missing ScriptRunContext" propres à AppTest,
quinze longueurs de fichiers au-delà de 300 lignes.

Aucun corpus réservé lu, haché, reconstruit ou remesuré ; aucun CLI d'évaluation, aucun
lanceur G8/G8R2. La fixture roundtrip reste limitée à dev par la garde FIX3R.

## 3. Recette locale FR/EN (AppTest)

Script : `results/recette8/test_recette.py`, lancé sous la même garde :
`PY results/fix3-recheck/guarded_pytest.py -q -p no:cacheprovider --tb=short results/recette8/test_recette.py`.
Résultat : 7 passed, 39,95 s, zéro ouverture réservée refusée (recette-apptest.log).
Résumé chiffré sans texte de document : apptest-summary.json ; textes des pages : pages-text.json.

Données : quatre documents fictifs nouveaux écrits pour R8, dont chaque nom de personne
figure aussi dans un nom de fichier (cas FIX2-01). Réseau : connexions refusées hors boucle
locale ; transport Mistral remplacé par un envoi simulé ; clé fictive. Aucun appel à un LLM.

| Cas | UI | Document | Profil | Sources observées | Résultat |
| --- | --- | --- | --- | --- | --- |
| 1 | EN | FR | Standard | heuristic, ner_spacy, pattern, propagation | conforme, second document conforme |
| 2 | FR | EN | Standard | ner_spacy, pattern, propagation | conforme, second document conforme |
| 3 | FR | FR | Enhanced | ner_camembert, pattern, propagation | conforme |
| 4 | EN | EN | Enhanced | ner_gliner, propagation | conforme, avertissement EN visible |

Vérifié dans chaque cas :

- Import, langue du document distincte de l'interface, détection sans exception.
- Review : ajout manuel réel (code d'accès fictif), société laissée en clair par décision
  de l'humain et bien laissée en clair après pseudonymisation.
- Pseudonymisation : noms, courriel et ajout manuel absents du texte ; la collision
  texte/nom de fichier ne bloque plus.
- Contrôle du document et de la consigne : consigne propre prête à l'envoi ; nom fictif
  planté dans la consigne signalé, envoi désactivé, autorisation révoquée ; consigne
  corrigée, nouveau contrôle, nouvelle confirmation sur une autre empreinte.
- Révocation : la modification de la politique du contrôle retire l'autorisation.
- Envoi simulé : un seul envoi, contenu égal au texte pseudonymisé plus la consigne
  corrigée, sans aucune valeur réelle ; autorisation consommée après l'envoi.
- Restore : réponse simulée restaurée, jeton inconnu `[PERSONNE_99]` signalé ; texte
  pseudonymisé restauré en mode exact, égal au document d'origine.
- Second document (cas 1 et 2) : "Start a new document", table de dossier importée à
  Import, jeton de la personne déjà connue inchangé (`[PERSONNE_2]`), nouvelle personne
  sur un numéro inutilisé (`[PERSONNE_4]`, `[PERSONNE_3]` étant l'entrée issue du nom de
  fichier, limite D-FIX3-2 respectée : aucune stabilité promise pour le nom seul).
- Pages Method et Evaluation en interface EN et FR, sans exception.

Observations, sans erreur de logique ni exception Streamlit :

- En anglais, le contrôle de la consigne signale le mot "Summarise" en tête de phrase
  (fausse alerte de prudence, aucun masquage). L'humain la tranche par la case prévue ;
  la recette l'a fait explicitement. Conforme à la priorité au rappel.
- "Start a new document" vide toute la session, langue d'interface comprise (retour à
  l'anglais) : comportement documenté ("erases the current session"), l'utilisateur
  choisit de nouveau ses langues.
- Le style de jetons par défaut reste français pour un document anglais, comme documenté.

## 4. Cohérence documentaire

- README et guide actualisés : collision corrigée, FIX4 recontrôlé et FIX3R-01 clos,
  reprise unique du challenge réussie, quatre critères français remplis, réserves
  anglaises explicites. Résultats G8 test/C3 présentés comme historiques (code e3d13bd),
  G8R2 comme mesure distincte du challenge déjà connu, comparaison G7 descriptive.
  Aucune significativité du gain de couverture (IC [0 ; 0,1667]). Revue humaine complète,
  pseudonymisation différente de l'anonymisation, aucune garantie de fuite nulle.
- Page Method : "Both Enhanced profiles remain experimental" et verdict G8 NO-GO pour
  l'anglais : réserve plus prudente que D-G8R2-1 pour Enhanced FR, recevable.
- Page Evaluation : tableaux G7 explicitement historiques. Une phrase reste obsolète,
  "bilingual blind validation is pending G8" : elle ne revendique aucune validation et
  reste prudente ; correction de texte d'interface hors périmètre de R8, à confier à une
  session autorisée.
- LOCAL_MODELS.md (profils renforcés dits expérimentaux, réserve plus prudente) et
  DEPLOYMENT.md (déploiement depuis main, bannière de démonstration) lus, sans
  contradiction bloquante.

## 5. Verdict limité au périmètre autorisé

GO de la recette locale pour la publication limitée à D-G8R2-1 : correctif FIX4 ;
fonctionnement technique FR/EN sur fixtures et données fictives ; périmètre FR mesuré,
Standard par défaut et Enhanced FR en option locale. Standard EN reste expérimental avec
réserves fortes ; Enhanced EN reste expérimental et non recommandé. Aucune validation
bilingue complète, aucune garantie d'absence de fuite, revue humaine complète requise.
Les anciens verdicts et reçus restent inchangés.

## 6. Réserves et vérification publique

- Corpus petits et fictifs, challenge déjà connu, auteurs corrélés ; 33 entités Standard et
  20 Enhanced au moins partiellement exposées avant revue sur le challenge.
- Continuité des jetons limitée (D-FIX3-2) ; phrase obsolète de la page Evaluation.
- La recette AppTest n'utilise pas de navigateur ; la vérification visuelle reste humaine.
- Publication (`git fetch . dev:main`, tag `gate-8`, push) et vérification de la démo
  publique : effectuées après ce commit ; leur résultat figure dans le compte rendu de
  session et dans des preuves hors dépôt, sans second commit. Tant que ce compte rendu ne
  dit pas le contraire, la version en ligne n'est pas considérée comme vérifiée.
