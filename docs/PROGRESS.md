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

### 2026-10-27 14:45 | S11 | Corpus fictif H1, lot 1 | Codex
- Fait : relecture des six documents dev selon A5 ; sources doc_01 à doc_06 enregistrées en UTF-8 sans BOM ; prompt initial et suivi copiés dans docs/prompts/corpus_lot_1.md.
- Tests : contrôles ciblés sur les six sources OK (299 à 353 mots, 16 à 18 annotations, en-têtes, spans, marqueurs, formes courtes, pièges, domaines réservés) ; copie du prompt comparée au modèle A5 ; ruff check et ruff format --check OK.
- Reste à faire : validation humaine A5 ; construction du corpus lorsque scripts/build_corpus.py sera disponible.
- Décisions : aucune.
- Risques ou blocages : pytest exécuté sans tests collectés ; scripts/check_style.py absent du dépôt initial, contrôle officiel impossible ; aucune installation ni utilisation du réseau.
- Prochaine session : validation humaine du lot 1, puis préparation du lot 2 dev.

### 2026-10-27 14:40 | H0 | Amorçage du dépôt | Humain
- Fait : dépôt public créé, fichiers de démarrage versés (AGENTS.md, CLAUDE.md, docs/), branches main et dev, worktree huisclos-b sur lane-b.
- Tests : aucun, pas encore de code.
- Reste à faire : S01.
- Décisions : D-01 à D-18 (master plan).
- Risques ou blocages : aucun.
- Prochaine session : S01, socle du dépôt (Claude Code, Sonnet 5.5 High).
