# S71 : prompt prêt à copier

```text
[HuisClos] Session S71 : rapport de méthode et architecture, lancement immédiat
Piste A, dossier huisclos, branche dev. Claude Code ou Codex, modèle disponible.
La vidéo est confiée à un camarade : elle ne bloque pas cette session.

0. Lis AGENTS.md en entier, vérifie git status. Si l'arbre est propre,
   git merge lane-b --no-edit ; conflit : arrête et signale-le, sans le résoudre.
   Ne lance ni pilote post_g7.py ni autre fiche de session.
1. Lis les trois premières entrées de docs/PROGRESS.md, docs/DECISIONS.md,
   README.md, docs/USER_GUIDE.md, docs/LOCAL_MODELS.md,
   docs/POST_G7_PROTOCOL.md, results/summary.md,
   results/challenge_comparison.md, results/gate8/report.md,
   results/gate8-recheck/report.md si présent, results/gate8-resume/report.md,
   results/recette8/report.md et docs/PROMPTS.md.
   Si docs/RESEARCH.md existe, lis-le ; sinon constate son absence sans bloquer.
   Lis seulement les docstrings de module de src/huisclos/**/*.py, les schémas
   de src/huisclos/models.py et les signatures publiques utiles du pipeline,
   de la pseudonymisation, du contrôle sortant et des lecteurs/exporteurs.
   Tu peux lire app/i18n/method*.py pour les références déjà affichées.
   Lis results/fix3-recheck/guarded_pytest.py pour les contrôles autorisés.
2. Présente un plan de dix lignes au plus et rédige sans attendre.

Fichiers autorisés en écriture : docs/METHOD_REPORT.md, docs/ARCHITECTURE.md,
docs/PROGRESS.md, docs/PROMPTS.md ; docs/DECISIONS.md seulement si une décision
documentaire nouvelle est nécessaire. Aucun code, résultat, corpus, README,
masterplan, document vidéo ou fichier de dépendances à modifier.

Crée METHOD_REPORT.md en anglais, 2 500 à 3 500 mots, douze sections :
1. Problem and users : besoin, avocats et juristes, extension RH présentée
   comme hypothèse, aucun chiffre de marché inventé.
2. Legal and ethical framework : références exactes déjà étayées dans les
   documents lus ; secret professionnel, RGPD, distinction pseudonymisation/
   anonymisation, table sensible. Lie les sources primaires disponibles.
   Ne présente pas une URL comme une vérification juridique récente.
   Sans RESEARCH.md probant, omets CNB 2026, statut final des lignes directrices
   CEPD et interprétation CJUE non vérifiés ; explicite la recherche manquante.
3. Market and alternatives : comparaison qualitative annoncée comme telle ;
   concurrents nommés ou chiffres seulement si leurs sources sont disponibles.
4. Solution and pipeline : Mermaid et choix justifiés avec décisions exactes.
5. Evaluation : sépare dev, test historique, challenge et C3 FR/EN ; tailles,
   types inclus/exclus, exact/partiel, F2, seuil, couverture complète, fuite,
   surmasquage, bootstrap et limites. Conserve le registre G4, G4bis, G7, G8,
   l'échec challenge, le diagnostic FIX2 et la reprise unique G8R2.
   N'exécute aucune mesure pour compléter une cellule manquante.
6. Course concepts applied : coût asymétrique, humain dans la boucle,
   hybride, transfert et mesure, chacun relié à une fonction visible.
7. Beyond the course : modèles facultatifs, fenêtres, projection Unicode,
   regroupement, restauration tolérante, mémoire, contrôle des deux segments,
   autorisation révoquée après modification, bootstrap apparié.
8. Limits and ethics : omissions, contexte, qualité PDF/DOCX, absence d'OCR,
   biais synthétiques, faux positifs, table, responsabilité et limites EN.
9. Value if widely used : hypothèses qualitatives, coût de revue et étude de
   temps encore nécessaire ; ni gain de productivité ni conformité garantis.
10. Reproducibility : commandes locales Windows/macOS tirées du guide,
    dépendances/modèles facultatifs préparés hors application. Sépare tests
    ordinaires et évaluation réservée, qui exige une gate et son autorisation.
    Une commande d'évaluation documentée n'est pas à exécuter dans S71.
11. Use of AI tools : usages constatés seulement et renvoi à PROMPTS.md.
    Vidéo externe entièrement produite avec IA et voix synthétique : prévue,
    outils et résultat final à créditer après réception, pas déjà réalisée.
12. References : fichiers et sources primaires effectivement disponibles.

Règles de preuve prioritaires : D-G8R2-1 et D-R8-1.
- G8R2 : code 930c414, huit documents FR du challenge déjà connu, avant revue ;
  Standard 157/190 entités entièrement couvertes, 325/3600 caractères exposés ;
  Enhanced 170/190 et 218/3600 ; précision partielle 0,803922/0,801802 ;
  surmasquage 366/379 caractères. Vérifie les valeurs dans le rapport source.
- Gain de couverture non significatif : IC apparié touche zéro. Ne confonds
  pas avec la réduction de fuite dont l'intervalle exclut zéro sur ce lot.
- G8 test/C3 mesure e3d13bd : historique, pas validation du code courant.
- Standard EN expérimental avec réserves fortes ; Enhanced EN expérimental
  et non recommandé. Aucun GO bilingue complet, aucune garantie zéro fuite.
- Une alerte ne masque rien ; cloud de démonstration et traitement local
  sont distincts ; limites de continuité D-FIX3-2 conservées.

Crée ARCHITECTURE.md en anglais, 1 500 à 2 000 mots, pour un non-informaticien :
trajet d'une phrase fictive inventée, Mermaid, frontières local/cloud/LLM,
table séparée, familles de modules avec chemins, entrées et sorties,
paramètres document/UI/jetons indépendants, profils et repli explicite,
états périmés, gestion d'erreurs et où modifier quoi après le gel.
Regroupe les modules proches pour respecter le budget de mots sans omettre
les étapes. Glossaire : NER, regex, clé, Luhn, modulo 97, jeton, pseudonymisation,
anonymisation, précision, rappel, F1/F2, fuite, couverture complète, surmasquage,
seuil, transfert, hybride, revue, Streamlit, Presidio, spaCy et bootstrap.

Contraintes : aucun réseau, aucune installation, aucune lecture/empreinte de
test, challenge, blind_post_g7 ou de leurs sources. Ne modifie pas les tests
pour une rédaction seule. Contrôle ponctuel hors dépôt : mots par document,
douze sections, chemins/liens locaux, provenance de chaque tableau.
Sous Windows : PYTHONUTF8=1, PY=.venv/Scripts/python.exe.
Lance PY results/fix3-recheck/guarded_pytest.py -q tests : suite existante,
roundtrip limité à dev par la garde conservée, zéro accès réservé attendu.
Puis PY -m ruff check ., PY -m ruff format --check .,
PY scripts/check_style.py et git diff --check. N'ouvre aucun lanceur de gate.
Si une dépendance manque ou une erreur préexistante est hors périmètre,
consigne-la sans installer ni corriger l'application ; ne prétends pas vert.
Mets à jour PROGRESS en tête et PROMPTS (référence à ce fichier, relances
exactes, limites de preuve et vidéo encore externe). Commit unique :
"S71 : rapport de méthode et architecture". Aucun push ni tag.
Termine en cinq lignes au plus : fait, tests, reste, risques, suite S72.
```
