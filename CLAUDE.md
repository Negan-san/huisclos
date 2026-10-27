@AGENTS.md

# Consignes propres à Claude Code

- Applique le protocole de session d'AGENTS.md (section 7) sans exception.
- Quota limité : pas de sous-agents, pas d'exploration large du dépôt, pas de recherche web sauf demande du prompt. Lis seulement les fichiers listés.
- Gros fichiers : lis une plage de lignes ; jamais corpus/*.jsonl ni data/ en entier.
- Sous Windows, ton shell est Git Bash : utilise les chemins de la section 6 d'AGENTS.md (.venv/Scripts/python.exe).
- Pour vérifier l'interface, préfère les tests AppTest. Si tu lances streamlit, fais-le en mode headless et arrête le processus avant la fin de la session.
- Annonce dans ton plan toute commande longue (installation, évaluation complète) avant de la lancer.
- En fin de session : compte rendu de 5 lignes, puis arrêt. N'enchaîne jamais sur la session suivante.
