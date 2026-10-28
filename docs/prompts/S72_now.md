# S72 : prompt prêt à copier

```text
[HuisClos] Session S72 : crédits et journal des prompts, lancement immédiat
Piste B, dossier huisclos-b, branche lane-b. Codex, modèle disponible.
À lancer après le commit S71 pour intégrer ses documents et éviter les
écritures simultanées dans les journaux. Aucune attente de la vidéo.

0. Lis AGENTS.md en entier et vérifie git status. Si l'arbre est propre,
   git merge dev --no-edit ; conflit : arrête et signale-le sans le résoudre.
   Ne lance ni pilote ni autre session.
1. Lis les trois entrées récentes de docs/PROGRESS.md puis les titres et les
   lignes utiles à la provenance de toutes les autres entrées ; lis
   docs/DECISIONS.md, docs/PROMPTS.md, docs/CONTRIBUTIONS.md,
   requirements.txt, requirements-dev.txt, requirements-transformers.txt,
   requirements-enhanced.txt et requirements-enhanced-lock.txt si présents,
   LICENSE, corpus/README.md, docs/LOCAL_MODELS.md, docs/POST_G7_PROTOCOL.md,
   README.md et les sections IA/références des documents S71 si présents.
   Consulte docs/MASTER_PLAN.md et docs/prompts/ pour retrouver les prompts,
   sauf le contenu des prompts de rédaction des lots réservés C3/challenge.
   Leur chemin et la provenance déjà journalisée suffisent.
   Lis les métadonnées installées des dépendances directes, les meta.json des
   modèles fr_core_news_md et en_core_web_sm, et les seules fiches locales
   des modèles CamemBERT/GLiNER/Anonym-IA explicitement étudiés en A1-A4.
   Ne parcours ni caches de documents ni secrets, et ne charge pas les poids.
   RESEARCH.md : si absent, le signaler, sans créer de source imaginaire.
   Lis results/fix3-recheck/guarded_pytest.py pour les contrôles.
2. Présente un plan de dix lignes au plus, puis rédige sans attendre.

Écriture autorisée : docs/CREDITS.md, docs/PROMPTS.md, docs/PROGRESS.md ;
docs/DECISIONS.md seulement si décision documentaire nouvelle nécessaire.
Aucun autre fichier à modifier. Aucun réseau, paquet à installer, pilote,
mesure, lecture ou empreinte de corpus réservé, push ou tag.

Crée CREDITS.md en anglais :
- Dépendances directes : nom, version déclarée, version installée si
  différente, licence exacte, URL, rôle et source locale du relevé.
  Distingue socle, développement, options lourdes et verrou transitif.
  pip-licenses seulement s'il existe déjà ; sinon importlib.metadata,
  License-Expression, License, fichiers de licence et Project-URL.
  Ne suppose ni sa présence ni que toutes les licences sont MIT.
- Modèles : les deux spaCy 3.8.0, CamemBERT retenu FR, GLiNER option EN,
  dépôts, révisions et licences réellement attestés ; Anonym-IA comme
  candidat étudié et écarté, sans le présenter comme backend embarqué.
  Distingue licence du code, des poids et des données d'entraînement.
- Données : corpus fictifs créés pour le cours, usages documentés des outils
  IA et relecture. Pas de lecture des textes ni des annotations réservés.
  N'invente aucune licence du corpus : si l'attribution CC BY 4.0 n'est pas
  établie par un fichier, écris "licence not documented" et consigne le point.
  Les modèles préentraînés utilisent des données externes : ne prétends pas
  que le projet n'a aucune dépendance envers des données externes.
- Outils IA : outil/modèle, rôle, preuve dans les journaux ; modèles absents
  de l'historique marqués inconnus, pas déduits du plan initial.
- Vidéo : production externe confiée à un camarade, voix synthétique,
  statut prévu/en cours ; ni Canva, Clipchamp, ElevenLabs ni autre outil
  recommandé à créditer comme utilisé sans preuve remise par le camarade.
  Signale la future annexe de crédits vidéo séparée ; S72 peut être terminée
  sans cette vidéo. Distingue les lectures web de planification des usages
  de production. Aucun rendu vidéo ni quota gratuit garanti.
- Sources juridiques et marché : renvois aux références S71 et à RESEARCH
  seulement s'il existe. Licence introuvable : "not verified locally",
  avec le fichier ou la fiche à vérifier, sans fabriquer de conclusion.

Consolide PROMPTS.md en anglais sans écraser les lignes historiques :
- En-tête "How AI tools were used", six lignes au plus.
- Une entrée par occurrence de session du journal : date, ID, outil/modèle,
  référence au prompt versionné et résultat réel. Ne fusionne pas deux
  corrections qui partagent un ID. N'ajoute pas S73 ou une gate non exécutée.
- Ajoute S71 si réalisé et conserve S61 comme travail déjà effectué.
- Pour chaque manque : "reconstructed from PROGRESS.md". Ce résumé n'est
  pas un verbatim : indique "original prompt unavailable" si introuvable.
  Une fiche révisée aujourd'hui n'est pas l'original historique de S61.
- Conserve les relances exactes disponibles. Ne reconstitue pas une citation
  à partir d'un résumé et ne recopie aucune donnée réservée.
- "Other AI tools" : corpus, recherche et vidéo, avec statut et preuves.
  Prompts vidéo futurs : planifiés, pas soumis ; les traces de production
  seront remises séparément avec le fichier vidéo.
- Contrôle hors dépôt : chaque entrée de PROGRESS a une correspondance
  dans PROMPTS, chaque dépendance directe est créditée ou explicitement
  signalée comme licence non vérifiée ; noms, versions et liens cohérents.

Sous Windows : PYTHONUTF8=1 ; PY=../huisclos/.venv/Scripts/python.exe.
Lance PY results/fix3-recheck/guarded_pytest.py -q tests, puis
PY -m ruff check ., PY -m ruff format --check .,
PY scripts/check_style.py, git diff --check. Ne lance aucune évaluation.
Pas de tests nouveaux qui recopient les tableaux ; vérifications ponctuelles
de complétude hors dépôt. Si un paquet manque, documente sans installation.
Mets à jour PROGRESS en tête et ajoute la ligne S72 dans PROMPTS, avec la
référence à ce fichier et les relances exactes. Commit unique :
"S72 : crédits et journal des prompts". Aucun push ni tag.
Compte rendu en cinq lignes au plus : fait, tests, reste, risques, suite.
```
