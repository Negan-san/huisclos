# AGENTS.md : HuisClos

Source unique de vérité pour tous les agents (Claude Code, Codex). À lire en entier avant toute tâche.
En cas de conflit, ce fichier prime sur tout autre document du dépôt, sauf consigne explicite du prompt de session.

## 1. Objectif

HuisClos est une application Streamlit qui pseudonymise localement des documents juridiques français avant leur envoi à un LLM, puis restaure les vraies valeurs dans la réponse.
Accroche : "Use generative AI on client files without breaching professional secrecy."
Devoir de groupe noté (cours Advanced AI Algorithms). Gel des fonctionnalités : mercredi 28 octobre 2026, 23h59. Dépôt : jeudi 29 octobre 2026 (Paris).

## 2. Principes non négociables

1. Traitement local : aucun appel réseau à l'exécution, sauf action explicite de l'utilisateur (connecteur Mistral, désactivé par défaut). Pas de police web, pas de CDN, télémétrie Streamlit coupée. Le test tests/test_no_network.py le vérifie.
2. Aucune donnée réelle : tests, corpus et démo sont fictifs. Ne jamais coller une donnée réelle dans un outil d'IA.
3. Priorité au rappel : un nom oublié est une violation du secret, un mot masqué en trop n'est qu'une gêne. L'humain valide chaque détection.
4. Pseudonymisation n'est pas anonymisation (RGPD, art. 4(5) et considérant 26) : l'interface et la documentation le disent.
5. La table de correspondance est sensible : jamais envoyée au LLM, jamais commitée (sauf fixtures fictives de tests).

## 3. Pipeline

1. Texte -> io.readers -> détection : detection.patterns, detection.person_heuristics, detection.ner (option detection.camembert).
2. -> detection.exclusions -> detection.merge -> detection.propagation -> revue humaine (app/).
3. -> pseudonymize.grouping -> pseudonymize.tokens -> texte pseudonymisé et table de correspondance.
4. Réponse du LLM + table -> pseudonymize.reidentify -> texte restauré -> io.writers.
5. evaluation.* mesure le pipeline sur corpus/dev.jsonl puis, une seule fois par gate, sur corpus/test.jsonl.

## 4. Arborescence

- streamlit_app.py : point d'entrée ; ajoute src/ au chemin d'import.
- app/ : interface (state.py, sidebar.py, ui_common.py, components/, steps/, pages/, i18n/, assets/style.css).
- src/huisclos/ : code métier (models.py, config.py, text_utils.py, detection/, pseudonymize/, io/, evaluation/, llm/).
- data/ : exclusions_fr.txt, samples/demo_case_fr.txt.
- corpus/ : source/*.md (sources annotées), dev.jsonl, test.jsonl. results/ : sorties de l'évaluation.
- scripts/ : check_style.py, banned_phrases.txt, build_corpus.py, run_evaluation.py, detect_cli.py, roundtrip_cli.py, measure_memory.py.
- tests/ : un fichier test_<module>.py par module, fixtures/, conftest.py (fixture no_network).
- docs/ : PROGRESS.md, DECISIONS.md, PROMPTS.md, CONTRIBUTIONS.md, puis livrables en anglais.

## 5. Types d'entités, jetons et spans

- Types (src/huisclos/models.py) : PERSON, ORGANIZATION, ADDRESS, EMAIL, PHONE, IBAN, NIR, SIREN, SIRET, BIRTH_DATE, CASE_NUMBER, LOCATION (désactivé par défaut), CUSTOM.
- Sources : checksum, pattern, heuristic, ner_spacy, ner_camembert, propagation, manual. Chaque RecognizerResult porte recognition_metadata["huisclos_source"] = valeur de Source.
- Jetons FR par défaut : [PERSONNE_1], [SOCIETE_A], [ADRESSE_1], [EMAIL_1], [TELEPHONE_1], [IBAN_1], [NIR_1], [SIREN_1], [SIRET_1], [DATE_NAISSANCE_1], [DOSSIER_1], [LIEU_1], [AUTRE_1].
- Jetons EN en option : PERSON, COMPANY, ADDRESS, EMAIL, PHONE, IBAN, NIR, SIREN, SIRET, BIRTH_DATE, CASE, PLACE, OTHER.
- Spans : civilités et libellés ("né le", "RG n°", "SIRET") hors du span ; forme juridique accolée dans le span d'une société ; une adresse = un span du numéro à la ville ; aucun chevauchement après fusion ; Detection.text == texte[start:end].
- Barème de confiance et seuil : docs/DECISIONS.md, D-07 et D-13.

## 6. Commandes

Appeler l'interpréteur par son chemin, noté PY ci-dessous :
- dossier huisclos : PY = .venv/Scripts/python.exe (Windows) ou .venv/bin/python (macOS) ;
- worktree huisclos-b : PY = ../huisclos/.venv/Scripts/python.exe (Windows) ou ../huisclos/.venv/bin/python (macOS).

- Installer : PY -m pip install -r requirements-dev.txt
- Tests : PY -m pytest -q
- Lint : PY -m ruff check . puis PY -m ruff format --check .
- Style : PY scripts/check_style.py
- Appli : PY -m streamlit run streamlit_app.py
- Détection en ligne de commande : PY scripts/detect_cli.py <fichier> --config hybrid
- Corpus : PY scripts/build_corpus.py
- Évaluation : PY scripts/run_evaluation.py --split dev
- Sous Windows, définir PYTHONUTF8=1 dans l'environnement.

Codex travaille sans réseau : aucune installation de paquet. Si un paquet manque, l'écrire dans le compte rendu et contourner sans lui ou s'arrêter sur ce point.

## 7. Protocole de session (obligatoire)

1. Lire AGENTS.md, les 3 dernières entrées de docs/PROGRESS.md, docs/DECISIONS.md, puis uniquement les fichiers listés dans le prompt.
2. Présenter un plan de 10 lignes au plus, puis implémenter sans attendre de validation, sauf ambiguïté bloquante.
3. Écrire ou mettre à jour les tests ; lancer pytest, ruff check, ruff format --check et scripts/check_style.py ; corriger jusqu'au vert.
4. Mettre à jour docs/PROGRESS.md (nouvelle entrée en tête de la section Entrées), docs/PROMPTS.md (une ligne), docs/DECISIONS.md si une décision est prise (identifiant D-<session>-<n>, en fin de fichier).
5. Un commit par session, message en français : "S11 : <résumé>". Fusion, tag et push seulement dans les cas de la section 12.
6. Finir par un compte rendu de 5 lignes au plus : fait, tests, reste à faire, risques, suite.

Contexte presque plein : s'arrêter proprement, consigner l'état dans docs/PROGRESS.md, committer "S11 (partiel) : <état>".

## 8. Règles de code

- Python 3.12, annotations de type partout, identifiants en anglais explicites.
- Commentaires et docstrings en français, phrases simples et complètes, compréhensibles par un étudiant en droit ou en gestion.
- Chaque module commence par une docstring de 3 à 6 lignes : rôle, entrées, sorties, place dans le pipeline.
- Chaque fonction a une docstring : rôle, paramètres, valeur retournée, exemple quand c'est utile.
- Commenter le pourquoi (choix technique, règle juridique, limite connue), jamais la paraphrase du code.
- Fonctions courtes ; fichiers de 300 lignes environ, 400 au maximum.
- Caractères typographiques dans le code : écrire les échappements ("\u2019", "\u00ab", "\u00a0"), jamais le caractère littéral.
- Toujours encoding="utf-8" pour lire ou écrire un fichier.
- Pas de print dans src/ ni app/, pas de TODO ni FIXME, pas de code commenté ni de code mort.
- Avant d'utiliser une API de bibliothèque (Presidio, Streamlit, pypdf, python-docx), lire sa signature dans le code installé, pas de mémoire.
- Tests : pytest, cas valides, invalides et pièges ; aucun accès réseau ; modèle spaCy chargé une fois par session de test (fixture de portée session).

## 9. Règles d'interface

- Textes en anglais, centralisés dans app/i18n/ (une clé par texte ; EN obligatoire, FR en option).
- Parcours en trois étapes visibles : Import, Review, Restore.
- Esthétique sobre de legaltech : palette retenue, police système lisible, hiérarchie claire, espacements constants, aucun dégradé ni décor gratuit, CSS minimal dans app/assets/style.css.
- Chaque entité surlignée porte une couleur ET un libellé texte ; jamais d'information portée par la seule couleur ; contrastes suffisants.
- Tout texte de l'utilisateur injecté en HTML passe par html.escape.
- États vides et messages d'erreur en langage clair ; indicateur de chargement pour toute opération de plus d'une seconde.
- Tests d'interface avec streamlit.testing.v1.AppTest, sans navigateur.

## 10. Interdits (code, interface, documentation)

- Emojis, tiret cadratin, points de suspension typographiques ; guillemets typographiques dans le code ; bannières décoratives.
- Formules creuses et superlatifs marketing (liste dans scripts/banned_phrases.txt).
- TODO orphelins, code mort, print de débogage.
- scripts/check_style.py vérifie ces interdits dans src/, app/, docs/ et README.md ; il fait partie de chaque gate.

## 11. Données et confidentialité

- Ne jamais lire en entier corpus/*.jsonl ni data/ : lire une plage de lignes ou passer par un script.
- corpus/test.jsonl et les sources du split test sont réservés à l'évaluation : ne pas les ouvrir, ne pas ajuster une règle d'après leur contenu ; seuls les scripts les lisent. Seule exception : la session de rédaction du corpus (C1), qui ne touche à aucun code.
- *.mapping.json, .streamlit/secrets.toml et .env sont ignorés par git.

## 12. Git

- Branches : main (déployée ; reçoit dev après une gate GO), dev (piste A, dossier huisclos), lane-b (piste B, worktree huisclos-b).
- Un commit par session. L'humain colle les prompts et relit le code ; les agents font le reste, dans ces seules limites :
  - étape 0 de chaque session, synchronisation : piste A, `git merge lane-b --no-edit` ; piste B, `git merge dev --no-edit` ; en cas de conflit, s'arrêter et le signaler ;
  - session de recette R<N> après une gate GO, sans quitter dev : `git fetch . dev:main` (avance rapide seulement), `git tag gate-N main`, `git push origin main dev --tags` ;
  - jamais de push --force, de rebase de branche partagée, ni de suppression de branche ou de tag.
- Ne modifier que les fichiers listés par le prompt ; tout autre besoin va dans le compte rendu.

## 13. Définition de "terminé"

- Critères d'acceptation du prompt remplis et vérifiés.
- pytest, ruff check, ruff format --check et scripts/check_style.py verts.
- docs/PROGRESS.md et docs/PROMPTS.md à jour ; commit fait.
- Aucune donnée réelle, aucun appel réseau ajouté, aucun fichier hors périmètre modifié.
