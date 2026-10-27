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

### 2026-10-27 15:10 | PIL | Délégation des tâches humaines aux agents | Claude Code, Opus 5.5
- Fait : AGENTS.md sections 7, 11 et 12 : synchronisation par les agents (étape 0), sessions de recette R<N> qui fusionnent, taguent et poussent après une gate GO, session C1 qui rédige les lots 2 et 3 du corpus.
- Tests : check_style vert sur AGENTS.md (128 lignes).
- Décisions : D-PIL-1.
- Risques ou blocages : le commit fdd4f3a de lane-b, libellé "S11", contient en réalité le lot 1 du corpus ; S11 reste à faire.
- Prochaine session : G0 (Codex, huisclos-b).

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
