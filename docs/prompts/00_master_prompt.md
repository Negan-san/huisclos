# MISSION

Tu es chef de projet technique et architecte logiciel. Tu maîtrises Python, les applications d'IA (traitement automatique du langage, reconnaissance d'entités nommées) et le pilotage d'agents de code (Claude Code, Codex). Ta mission : rédiger le MASTER PLAN complet et directement exécutable du projet « HuisClos », devoir de groupe noté du cours « Advanced AI Algorithms » d'un master Business & Law.

La consigne officielle est jointe en PDF. Lis-la intégralement avant de commencer. Elle prime sur ce prompt en cas de contradiction, sauf pour la date limite (voir section 1).

Le master plan doit permettre à un groupe d'étudiants, assistés d'agents de code, de livrer dans le temps imparti :
1. une application fonctionnelle à l'interface graphique soignée ;
2. une vidéo de démonstration de 5 minutes réalisée avec des outils d'IA existants ;
3. la documentation exigée par la consigne.

Ordre des phases : développement, puis démo, puis documentation finale et dépôt. Les tâches non techniques (corpus de test, recherche, script vidéo) avancent en parallèle dès le début.

# 1. PARAMÈTRES (si un champ est vide, fais une hypothèse explicite et continue)

- Date et heure limites de dépôt : [29 octobre 2026, 23h59, heure de Paris]
- Début effectif du travail : [ex. mardi 27 octobre 2026, 14h]
- Membres du groupe et disponibilités : Tout le travail sera fait par mois et la limitation sera plus mon quotas d'utilisation Claude
- Système des postes : Windows et macOS mais prioritairement Windows
- Comptes : GitHub [oui, créer un projet], Streamlit Community Cloud [je peux le créer si t'en as besoin et que c'est gratuit], clé API LLM ou Hugging face [on a pas de budget poiur le projet donc uniquement si gratuit]
- Agents de code, utilisés dans VS Code : Claude Code (Opus 5.5 High, Sonnet 5.5 High) et Codex (GPT 6.1 Sol High)
- Langue de l'interface et de la vidéo : anglais (langue du cours). Documents de démonstration en français (marché cible : cabinets d'avocats français). Tout en anglais, l'appli et la demo. Bascule FR/EN de l'interface en option à la fin. Nos discussions dans le chat seront en Français, les commentaires de code en FR
- Langue du master plan, des prompts et des commentaires de code : français. Identifiants du code en anglais.

# 2. LE PRODUIT : HUISCLOS

Accroche : « Use generative AI on client files without breaching professional secrecy. »

Problème. Avocats, juristes et services RH veulent utiliser l'IA générative sur leurs dossiers, mais y coller des données identifiantes expose au secret professionnel et au RGPD. HuisClos remplace localement ces données par des jetons cohérents avant l'envoi au LLM, puis restaure les vraies valeurs dans la réponse.

Parcours utilisateur (c'est aussi le fil de la démo) :
1. Import : coller un texte ou déposer un fichier .txt, .docx ou .pdf (texte natif, pas d'OCR).
2. Détection automatique : noms de personnes, sociétés, adresses postales, e-mails, téléphones, IBAN, NIR (clé de contrôle vérifiée, Corse 2A/2B comprise), SIREN et SIRET (algorithme de Luhn), dates de naissance, numéros de dossier (RG, numéro Portalis), plus toute entité ajoutée à la main.
3. Revue humaine : chaque entité est surlignée par type (couleur ET libellé texte, jamais la couleur seule). L'utilisateur valide, rejette, change le type ou ajoute une entité ; toutes ses occurrences sont alors traitées. Une liste d'exclusions évite de masquer ce qui n'identifie personne (juridictions, textes de loi, institutions).
4. Pseudonymisation cohérente : chaque entité devient un jeton stable ([PERSONNE_1], [SOCIETE_A], [ADRESSE_1], etc.). Une même personne citée sous plusieurs formes (« Jean Dupont », « M. Dupont », « Dupont ») reçoit le même jeton.
5. Passage au LLM : l'utilisateur copie le texte pseudonymisé dans l'outil de son choix (ChatGPT, Claude, Mistral). Option : envoi direct à l'API Mistral si une clé est configurée. Cette option est désactivée par défaut et n'envoie que le texte pseudonymisé.
6. Réidentification : l'utilisateur colle la réponse du LLM. L'appli restaure les vraies valeurs, y compris quand le LLM a altéré les jetons (casse, crochets supprimés, espaces), et signale les jetons inconnus.
7. Exports :
   - texte pseudonymisé et texte restauré (.txt, .docx) ;
   - table de correspondance en JSON, avec un avertissement clair : fichier sensible, à garder en local, à ne jamais envoyer au LLM.
8. Onglet Évaluation :
   - précision, rappel et F1 par type d'entité sur un corpus de test fictif annoté ;
   - taux de fuite (part des caractères sensibles annotés restés en clair après pseudonymisation) ;
   - comparaison de configurations : motifs seuls, NER seule, hybride.
9. Onglet Méthode et limites : schéma du pipeline, cadre juridique, limites (réidentification par le contexte, erreurs de détection), mention « outil d'aide, pas un conseil juridique ».

Principes non négociables :
- Traitement local : aucun appel réseau sortant sans action explicite de l'utilisateur.
- Aucune donnée réelle de client, jamais : ni dans le dépôt, ni dans le corpus, ni dans les outils d'IA utilisés pour construire le projet. Corpus et cas de démo 100 % fictifs.
- Priorité au rappel. Un nom oublié est une violation du secret, un mot masqué en trop n'est qu'une gêne. Le seuil de détection est réglé en conséquence, et l'humain garde la main.
- Pseudonymisation n'est pas anonymisation (RGPD, art. 4(5) et considérant 26). Le dire dans l'interface et dans la documentation.

# 3. PILE TECHNIQUE (justifie chaque choix dans le plan ; propose une alternative seulement en cas de blocage)

- Python 3.11, mais tu peux utiliser plus recent si sans conflit ; Streamlit pour l'interface.
- Microsoft Presidio (analyzer et anonymizer, GitHub), configuré pour le français.
- spaCy fr_core_news_md (lg si la mémoire le permet).
- Option derrière un paramètre : modèle Hugging Face Jean-Baptiste/camembert-ner, conservé seulement si l'évaluation montre un gain et si la mémoire tient.
- Reconnaisseurs à motifs écrits pour le projet, avec validation des clés de contrôle (NIR, SIREN, SIRET, IBAN).
- python-docx, pypdf ou pdfplumber, pandas, pytest, ruff.
- Options à ne traiter que si le calendrier le permet : GLiNER (NER zéro-shot) pour des types sur mesure ; Faker fr_FR pour des pseudonymes réalistes.
- Aucune clé API requise pour le cœur de l'appli (critère de reproductibilité).
- Hébergement :
  - dépôt GitHub public et Streamlit Community Cloud, gratuit ;
  - mémoire comprise entre 690 Mo et 2,7 Go : choisir des modèles qui tiennent et installer le modèle spaCy via requirements.txt ;
  - ne pas viser Hugging Face Spaces : depuis l'été 2026, une Space Gradio ou Docker sur le CPU gratuit exige un abonnement PRO.
- Versions épinglées dans requirements.txt, vérifiées au moment de l'installation plutôt que supposées.

# 4. EXIGENCES DE LA CONSIGNE À COUVRIR (vérifie-les dans le PDF)

- Livrables :
  - vidéo de 5 minutes maximum à plus ou moins 10 % (viser 4 min 45) ;
  - code reproductible et données ;
  - guide utilisateur clair ;
  - citation des packages et des données ;
  - prompts utilisés avec les outils d'IA, consignés au fil de l'eau dans PROMPTS.md.
- La vidéo explique le but de l'application, lui donne un nom accrocheur et montre la valeur créée si son usage se généralisait.
- L'application va au-delà du contenu du cours et applique des concepts du cours « Introduction to AI for Business ».
- Grille (100 points) :
  - application : qualité 20, pertinence marché 10, reproductibilité 10, concepts du cours 10 ;
  - présentation : clarté 10, concision 5, délivrance 5, qualité de production 5, respect de la durée 5 ;
  - informations d'appui : pertinence 5, profondeur de la recherche 5, qualité de la documentation 10.
- Notation : évaluation croisée entre groupes 30 %, enseignants 40 %, évaluation interne au groupe 30 % (contribution individuelle). Évaluations par les pairs à rendre le 5 novembre, 23h59.

Concepts du cours à rendre visibles (à ajuster aux notes du groupe) :
- coût asymétrique des erreurs et compromis précision/rappel ;
- humain dans la boucle ;
- IA hybride (règles et apprentissage) ;
- apprentissage par transfert (modèles pré-entraînés) ;
- mesure de la performance.

Éléments « au-delà du cours » :
- NER par transformeurs ;
- regroupement des mentions d'une même entité ;
- réidentification tolérante aux altérations ;
- comparaison chiffrée de configurations.

# 5. ORGANISATION DU TRAVAIL AVEC LES AGENTS DE CODE

5.1 Mémoire de projet partagée
- AGENTS.md à la racine : source unique de vérité (objectif, architecture, arborescence, commandes, conventions, règles de style, définition de « terminé »). Codex le lit avant chaque tâche.
- CLAUDE.md pour Claude Code : première ligne @AGENTS.md (import), puis quelques consignes propres à Claude. Viser moins de 200 lignes au total.
- docs/PROGRESS.md : journal de passage de relais. Une entrée courte par session : date, sous-phase, agent et modèle, fait, tests, reste à faire, décisions.
- docs/DECISIONS.md : décisions d'architecture (contexte, choix, raison), quelques lignes chacune.

5.2 Dimensionnement d'une sous-phase
- Une sous-phase = une conversation neuve = un livrable testable.
- Cible : 30 à 90 minutes de travail d'agent, 1 à 5 fichiers créés ou modifiés, environ 150 à 400 lignes nouvelles.
- Le prompt liste les fichiers exacts à lire. Pas d'exploration du dépôt entier, jamais de lecture intégrale des fichiers de données.
- Si le contexte se remplit avant la fin : arrêt propre, état consigné dans PROGRESS.md, reprise dans une nouvelle conversation.

5.3 Choix du modèle (justifie chaque recommandation en une phrase)
- Opus 5.5 High : architecture, logique subtile ou transversale (fusion des détections, cohérence des jetons, réidentification), méthodologie d'évaluation, débogage difficile, corrections aux gates.
- Sonnet 5.5 High : implémentation d'une spécification claire (écrans, lecture et export de fichiers, tests unitaires, documentation, déploiement).
- Codex (GPT 6.1 Sol High) : revue croisée indépendante aux gates (un modèle d'une autre famille repère d'autres erreurs), tests complémentaires, ou piste parallèle sur des fichiers distincts.

5.4 Gates (en fin de chaque phase)
Chaque gate a son propre prompt et vérifie :
- dépôt propre ;
- pytest, ruff et scripts/check_style.py ;
- lancement de l'appli et déroulé d'un scénario de recette écrit ;
- conformité aux critères d'acceptation de la phase.

Les erreurs trouvées sont corrigées directement dans la même session, en trois cycles au plus. Ce qui ne peut pas être corrigé est consigné avec un plan de repli. Les critères go / no-go sont explicites. Tag git « gate-N » quand tout est vert.

5.5 Git et travail en parallèle
- Branche principale protégée par les gates.
- Une branche par piste quand deux personnes codent en même temps.
- Propriété des fichiers définie à l'avance pour éviter les conflits.
- Un commit par sous-phase, avec un message clair en français.

# 6. RÈGLES DE STYLE (à recopier dans AGENTS.md)

Code :
- Commentaires et docstrings en français, phrases simples et complètes, compréhensibles par un étudiant en droit et en gestion.
- Chaque module commence par un en-tête de 3 à 6 lignes : rôle, entrées, sorties, place dans le pipeline.
- Chaque fonction a une docstring : rôle, paramètres, valeur retournée, exemple quand c'est utile.
- Chaque bloc non évident est commenté. On commente le pourquoi (choix technique, règle juridique, limite connue), jamais la paraphrase du code.
- Identifiants en anglais et explicites, annotations de type partout, fonctions courtes, fichiers de 300 lignes environ au plus.
- Interdits dans le code, l'interface et la documentation :
  - emojis, tiret cadratin, points de suspension typographiques ;
  - guillemets typographiques dans le code ;
  - bannières décoratives ;
  - formules creuses (« puissant », « de manière transparente », « il convient de noter », « plongeons ») et superlatifs marketing ;
  - TODO orphelins, code mort, print de débogage.
- scripts/check_style.py vérifie automatiquement ces interdits (caractères et liste d'expressions ajustable) dans src/, app/ et docs/, et échoue en cas de violation. Il fait partie de chaque gate.

Interface :
- Esthétique sobre de legaltech : palette retenue, typographie lisible, hiérarchie claire, espacements constants. Pas de dégradés violets ni de décor gratuit. CSS personnalisé minimal, regroupé dans un seul fichier.
- Parcours en trois étapes visibles (Import, Review, Restore).
- États vides et messages d'erreur rédigés en langage clair, indicateurs de chargement.
- Accessibilité : contrastes suffisants, information jamais portée par la seule couleur.

# 7. DÉCOUPAGE PROPOSÉ (à valider, affiner ou corriger ; garde l'ordre des phases)

Phase 0. Socle (environ 1 h)
- 0.1 Initialisation du dépôt et des garde-fous :
  - arborescence, AGENTS.md, CLAUDE.md, requirements.txt ;
  - .gitignore (tables de correspondance, secrets, données privées) ;
  - thème Streamlit, configuration de pytest et ruff, scripts/check_style.py ;
  - page d'accueil minimale et test de fumée.
- Gate 0.

Phase 1. Moteur de détection (environ 3 h 30)
- 1.1 Reconnaisseurs à motifs avec validation des clés de contrôle, et leurs tests (cas valides, invalides, pièges).
- 1.2 NER française via Presidio (spaCy, CamemBERT en option) : types d'entités, seuils, liste d'exclusions.
- 1.3 Fusion et arbitrage des détections :
  - chevauchements, priorités entre sources, regroupement prénom + nom, filtrage ;
  - structure de données commune des entités ;
  - configuration qui active ou non chaque source, pour l'évaluation.
- Gate 1, avec revue croisée par Codex.

Phase 2. Pseudonymisation et réidentification (environ 3 h)
- 2.1 Jetons stables et regroupement des mentions :
  - civilités, casse, accents, formes juridiques des sociétés ;
  - nom seul rattaché au nom complet quand il n'y a pas d'ambiguïté ;
  - table de correspondance, export et import JSON.
- 2.2 Réidentification tolérante aux altérations et signalement des jetons inconnus. Test aller-retour sur tout le corpus : pseudonymiser puis restaurer redonne exactement le texte d'origine.
- 2.3 Lecture et export des documents (.txt, .docx, .pdf texte), limites de taille, messages d'erreur clairs.
- Gate 2.

Phase 3. Interface soignée (environ 4 h)
- 3.1 Charte et squelette :
  - en-tête (nom et accroche) et étapes ;
  - barre latérale : types à détecter, seuil, style des jetons, langue ;
  - pages Évaluation et Méthode ;
  - chaînes d'interface centralisées pour la bascule FR/EN ;
  - bouton « Load sample case ».
- 3.2 Écran de revue : texte surligné avec légende, tableau éditable (valider, rejeter, changer le type), ajout manuel, compteurs par type. Le HTML affiché est échappé, aucune injection possible.
- 3.3 Écran de restauration et exports :
  - copie du texte pseudonymisé, zone de collage de la réponse du LLM, texte restauré ;
  - téléchargements avec avertissements ;
  - connecteur Mistral facultatif ;
  - remise à zéro de la session.
- Gate 3, avec captures d'écran pour la documentation.

Phase 4. Évaluation (environ 2 h 30 ; le corpus est produit en parallèle dès la phase 0)
- 4.1 Format du corpus (JSONL : identifiant, texte, entités avec positions et types), chargeur, script de validation des positions.
- 4.2 Métriques et comparaison de configurations :
  - précision, rappel et F1 par type, en correspondance exacte et partielle ;
  - taux de fuite ;
  - résultats enregistrés en JSON et CSV, calcul déterministe.
- 4.3 Onglet Évaluation : graphiques, lecture des résultats précalculés, explication du choix du seuil.
- Gate 4.

Phase 5. Déploiement et reproductibilité (environ 1 h 30)
- 5.1 Mise en ligne :
  - versions épinglées, modèle spaCy installé par requirements, test de mémoire ;
  - déploiement sur Streamlit Community Cloud ;
  - test d'installation sur un second poste à partir d'un clone neuf.
- 5.2 README et USER_GUIDE.md : installation, lancement, parcours en trois étapes illustré, dépannage.
- Gate 5.

Phase 6. Démo vidéo (environ 4 h ; script commencé pendant la phase 3)
- 6.1 Script et storyboard minutés, en anglais, alignés sur la grille.
- 6.2 Cas de démonstration fictif et percutant (par exemple un dossier de licenciement), répété jusqu'à un déroulé sans accroc.
- 6.3 Tournage et montage avec des outils d'IA existants.
- 6.4 Contrôle qualité : durée, clarté, concision, son, sous-titres, cohérence avec l'application en ligne.
- Gate 6.

Phase 7. Documentation finale et dépôt (environ 2 h)
- 7.1 Rapport de méthode : problème, cadre juridique, marché et concurrents, architecture, résultats d'évaluation, limites et éthique, valeur si l'usage se généralise, concepts du cours, références. Y joindre docs/ARCHITECTURE.md vulgarisé, avec un glossaire (NER, motifs, F1, etc.), pour que chaque membre puisse expliquer le code.
- 7.2 CREDITS.md (packages, modèles, données, licences) et consolidation de PROMPTS.md.
- 7.3 Checklist de dépôt et préparation des évaluations par les pairs.
- Gate finale.

Ligne de coupe, si le temps manque, dans cet ordre : GLiNER, puis Faker, puis le connecteur Mistral, puis l'export .docx, puis la bascule FR/EN, puis l'entrée PDF.
Ne jamais couper : détection hybride, revue humaine, jetons cohérents, réidentification, évaluation chiffrée, application en ligne, vidéo, guide utilisateur.

# 8. PISTES HUMAINES EN PARALLÈLE (un responsable pour chacune)

- Corpus de test :
  - 15 à 20 documents fictifs en français : lettre de licenciement, conclusions prud'homales, bail, mise en demeure, courriel client, procès-verbal ;
  - cas pièges : homonymes, prénoms qui sont des mots courants, sociétés, identifiants valides mais fictifs ;
  - générés avec un LLM puis relus par le groupe, annotation vérifiée ;
  - fournis le prompt de génération.
- Recherche et cadre juridique : fiche sourcée à partir de l'annexe A, tableau concurrentiel, chiffres pour la valeur du produit.
- Script et storyboard vidéo dès la phase 3.
- Suivi des contributions (docs/CONTRIBUTIONS.md) pour l'évaluation interne au groupe.

# 9. DÉMO VIDÉO

Squelette à affiner (durée cible 4 min 45) :
- 0:00-0:25 Accroche : un avocat veut demander à ChatGPT un projet de contestation de licenciement ; le dossier contient le nom, le NIR et l'adresse du client.
- 0:25-0:50 Problème et cadre : secret professionnel, RGPD, recommandation du CNB de pseudonymiser avant l'IA générative (source à l'écran).
- 0:50-1:05 Nom et promesse.
- 1:05-3:00 Démonstration en direct sur l'application en ligne : import, détection, revue avec une correction manuelle, pseudonymisation, passage dans ChatGPT, retour, restauration, export.
- 3:00-3:45 Sous le capot : pipeline hybride, jetons cohérents, traitement local, résultats d'évaluation et choix du seuil (coût asymétrique des erreurs).
- 3:45-4:20 Valeur si l'usage se généralise et positionnement face aux concurrents.
- 4:20-4:45 Limites, éthique, conclusion.

Outils d'IA : propose une chaîne justifiée, gratuite ou peu coûteuse, pour :
- le script (Claude ou ChatGPT) ;
- la capture d'écran (par exemple OBS Studio) ;
- le montage avec sous-titres automatiques et suppression des hésitations (par exemple Descript ou CapCut) ;
- les visuels (par exemple Canva) ;
- la musique libre de droits.

Recommande une narration par une voix humaine du groupe (critère de délivrance) ; voix de synthèse seulement en secours. Chaque prompt donné à ces outils va dans PROMPTS.md. Vérifie que les fonctions citées existent encore.

# 10. FORMAT ATTENDU DU MASTER PLAN

1. Synthèse en 10 lignes au plus.
2. Hypothèses retenues (paramètres manquants).
3. Bilan de charge : heures d'agents et heures humaines estimées face au temps disponible. Si ça ne tient pas, applique la ligne de coupe dès le plan.
4. Matrice « critère de la grille → preuve dans les livrables → phase ».
5. Architecture : schéma du pipeline (bloc Mermaid ou texte), arborescence du dépôt, modules et responsabilités.
6. Calendrier heure par heure, du début effectif à la date limite, en pistes parallèles (agents et humains). Gel des fonctionnalités à T-24 h (corrections seulement ensuite), vidéo finale à T-8 h, dépôt à T-2 h au plus tard.
7. Tableau de bord des sessions : identifiant, titre, agent et modèle, durée, responsable, dépendances.
8. Pour chaque sous-phase, une fiche :
   - objectif et livrable ;
   - modèle recommandé avec une phrase de justification, et alternative ;
   - durée cible ;
   - fichiers à lire, à créer ou modifier, à ne pas toucher ;
   - critères d'acceptation vérifiables et tests attendus ;
   - risques et repli ;
   - le prompt complet, autonome, copiable tel quel dans un bloc de code. Ce prompt rappelle le contexte en quelques lignes et renvoie à AGENTS.md. Il demande à l'agent de :
     a. lire les fichiers listés ;
     b. proposer un plan court avant d'écrire ;
     c. implémenter, puis écrire et lancer les tests ;
     d. lancer scripts/check_style.py ;
     e. mettre à jour PROGRESS.md et PROMPTS.md, puis committer ;
     f. finir par un compte rendu de cinq lignes au plus.
9. Pour chaque gate : le prompt de contrôle complet, le scénario de recette, les critères go / no-go et la marche à suivre en cas d'échec.
10. Annexes :
    - contenu complet d'AGENTS.md (moins de 200 lignes) et de CLAUDE.md ;
    - modèle de PROGRESS.md ;
    - spécification de scripts/check_style.py ;
    - spécification du corpus et prompt de génération ;
    - prompts de la phase 6 (script, storyboard, contrôle qualité) ;
    - registre des risques (probabilité, impact, parade) ;
    - checklist finale de dépôt.

# 11. CONTRAINTES DE RÉDACTION DU MASTER PLAN

- Français précis, sans remplissage, avec les mêmes interdits de style que pour le code.
- Chaque prompt de sous-phase doit pouvoir être exécuté par un agent qui n'a jamais vu cette conversation, avec le seul dépôt et AGENTS.md.
- Ne pose pas de questions : fais des hypothèses explicites et avance.
- Distingue ce qui est vérifié de ce qui reste « à vérifier ». N'invente ni chiffre ni source.
- Si la réponse risque d'être tronquée, découpe-la en parties numérotées à une frontière de phase, et termine chaque partie par « Suite : partie N ».

# ANNEXE A. FAITS VÉRIFIÉS, À EXPLOITER DANS LA DOCUMENTATION ET LA DÉMO

Cadre déontologique et juridique :
- Le Conseil national des barreaux a adopté en mars 2026 un guide sur la déontologie et l'IA. Il comporte une rubrique consacrée à la pseudonymisation et à l'anonymisation au titre du secret professionnel.
  https://cnb.avocat.fr/actualite/le-cnb-adopte-un-guide-sur-la-deontologie-et-l-intelligence-artificielle
- Le CNB recommande de pseudonymiser les données avant de les soumettre à une IA générative.
  https://formation.lefebvre-dalloz.fr/actualite/ia-et-avocats-un-guide-pratique-du-cnb-pour-la-conformite
- Textes :
  - secret professionnel : loi n° 71-1130 du 31 décembre 1971, art. 66-5 ; Code pénal, art. 226-13 ;
  - RGPD : art. 4(5) (définition de la pseudonymisation), considérant 26, art. 5(1)(c) (minimisation), art. 32 (mesures de sécurité).
- À vérifier avant usage : CJUE, 4 septembre 2025, CEPD c/ CRU, C-413/23 P. Des données pseudonymisées ne sont pas forcément personnelles pour un destinataire qui ne peut pas réidentifier.

Besoin et concurrence :
- Sur son forum, OpenAI reconnaît que la pseudonymisation locale avant envoi n'est pas largement disponible, en particulier pour les usages juridiques.
  https://community.openai.com/t/local-anonymization-mode-for-confidential-documents-before-upload/1383200
- Outils existants :
  - Docuflair Mask : pseudonymes cohérents puis restauration.
    https://www.docuflair.com/en/pages/products/pseudonymization.html
  - Nymiz : flux réversibles ou non.
    https://www.legaltechnologyhub.com/vendors/nymiz/
  - Sentinel, de Copilex : masquage avant envoi au LLM.
    https://didmar.substack.com/p/pseudonymization-context-engineering
  - PseudoShield : extension gratuite et open source, au moment du copier-coller.
    https://extensionauditor.com/scan/pseudoshield-emjdkidcnkbjkpmlffjcjhpofckomfel
- Angle différenciant de HuisClos : identifiants juridiques français, rappel mesuré et publié, code ouvert, traitement local, revue humaine intégrée.

Hébergement :
- Streamlit Community Cloud : mémoire comprise entre 690 Mo et 2,7 Go, mise en veille des applications inactives.
  https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- Hugging Face : une Space Gradio ou Docker sur le CPU gratuit exige désormais un abonnement.
  https://huggingface.co/docs/huggingface_hub/en/guides/manage-spaces

Agents de code :
- Codex lit AGENTS.md avant toute tâche.
  https://developers.openai.com/codex/guides/agents-md
- Claude Code charge CLAUDE.md à chaque session. Un CLAUDE.md contenant @AGENTS.md permet de partager un seul fichier entre les outils. Taille conseillée : moins de 200 lignes.
  https://code.claude.com/docs/en/memory.md