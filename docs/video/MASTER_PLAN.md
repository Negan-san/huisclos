# HuisClos : plan autonome de production vidéo par IA

Révision du 28 octobre 2026. Responsable : le camarade chargé de la vidéo.
Ce plan remplace les anciennes tâches S61/S6A/H6/G6 du masterplan applicatif.
S61 est déjà réalisée : ses textes sont la base, pas une session à relancer.
La production vidéo ne bloque ni S71 ni S72. Aucun développement applicatif
ni installation dans le dépôt HuisClos n'est demandé ici.

## 1. Résultat à livrer

Vidéo en anglais, cible 4:45, fenêtre de la consigne 4:30 à 5:30.
Livrables : `huisclos_demo_1080p.mp4`, `huisclos_demo_en.srt`, copie 720p,
sources de montage, journal des prompts, crédits des médias et outils,
fiche de contrôle final et lien de téléchargement testé.
Format visé : 1920 x 1080, 16:9, MP4 H.264 avec audio AAC, 30 images/s.
Le camarade pilote les outils, choisit les propositions et contrôle l'export.
Les images animées, la narration et les sous-titres sont produits avec IA.
Aucune voix humaine à enregistrer, aucun acteur à filmer.

Deux modes sont distingués explicitement :

| Mode | Fabrication | Présentation honnête |
| --- | --- | --- |
| A, entièrement synthétique, mode de référence | Un agent produit une reconstitution animée déterministe à partir d'états vérifiés et des libellés exacts ; voix TTS, cartons et montage produits avec IA | Mention permanente sur la démo : **AI-generated reconstruction. Fictional data.** Réponse préparée marquée **Illustrative AI answer**. Aucune prétention de session en direct |
| B, preuve complémentaire si un agent peut piloter le navigateur | L'IA exécute le vrai parcours et capture les états réels, génère voix et montage | **AI-operated app demonstration. Fictional data.** Échange LLM réel seulement s'il a effectivement eu lieu ; attente coupée signalée |

Le mode A répond à la demande de démo entièrement générée. Le mode B produit
la vidéo avec IA mais inclut des captures, ce qui ne signifie pas que chaque
pixel est synthétique. Ne bascule pas entre ces modes sans adapter les mentions.
Une reconstitution explique un usage ; elle ne remplace pas une preuve de test.
Si le cours exige une capture réelle, joindre la preuve du mode B ou déclarer
la limite : ne jamais faire passer A pour une exécution filmée.

## 2. Dossier à transmettre au camarade

Transmettre des copies en lecture seule :

- `docs/video/SCRIPT.md` et `STORYBOARD.md`, adaptés depuis S61 ;
- ce plan, `README.md`, `docs/USER_GUIDE.md`, `app/assets/logo.svg` ;
- `results/gate8-resume/report.md` pour les chiffres et leur portée ;
- captures publiques de référence ou états préparés à partir du cas fictif,
  contrôlés contre le guide et l'application ; aucun corpus réservé ;
- adresses : https://huisclos.streamlit.app et
  https://github.com/Negan-san/huisclos.

Créer un dossier de production séparé du dépôt : `huisclos-video-production/`,
avec `01_brief`, `02_reference`, `03_voice`, `04_visuals`, `05_edit`, `06_export`.
Ne transmettre ni `.env`, clé, table `.mapping.json`, compte personnel,
historique de navigateur, document client ou texte des corpus réservés.
Le scénario et ses identités sont fictifs ; leur transcription dans un service
de production externe est une action distincte du fonctionnement local de l'app.

## 3. Outils : chaîne gratuite prioritaire

Sources officielles consultées le 28 octobre 2026 ; quotas et droits effectifs
à confirmer sur le compte du camarade par un export test avant le montage.
Les recommandations ne prouvent pas que ces services ont déjà été utilisés.

| Besoin | Choix | Condition et repli |
| --- | --- | --- |
| Scénario, montage déterministe et cartons | Assistant IA déjà accessible au camarade ; demander un projet vidéo autonome ou des animations HTML/SVG exportables | Ne pas acheter un nouvel abonnement pour la rédaction. Code généré par IA possible hors dépôt ; si aucun moteur de rendu n'est disponible, importer des images fixes générées et les animer dans l'éditeur |
| Voix anglaise et montage | Clipchamp, compte personnel gratuit | [Voix TTS](https://clipchamp.com/en/features/ai-voice-over-generator/) et [export 1080p gratuit](https://support.microsoft.com/en-us/clipchamp/what-format-is-my-video-exported-in). Éviter les éléments Premium ; tester l'export, pas seulement l'aperçu. Clipchamp assemble les médias, il ne génère pas à lui seul une interface applicative fidèle depuis un prompt |
| Variante de voix | ElevenLabs Free, facultatif | [10 000 crédits mensuels annoncés](https://elevenlabs.io/pricing), consommation dépendante du modèle et des reprises. [Conditions de publication](https://help.elevenlabs.io/hc/en-us/articles/13313564601361-Can-I-publish-the-content-I-generate-on-the-platform) : usage gratuit non commercial, attribution requise dans le titre avec elevenlabs.io ou 11.ai. Vérifier la destination de publication ; si incompatible ou quota épuisé, revenir au TTS Clipchamp |
| Images d'ambiance, facultatives | Canva Magic Media, offre gratuite | [Usages gratuits limités](https://www.canva.com/video-editor/ai/) ; [clips Magic Media de quatre secondes](https://www.canva.com/help/using-magic-media/). Pas de quota chiffré promis. Deux ou trois inserts sans texte au plus, jamais une fausse interface ni des chiffres générés dans l'image |
| Sous-titres | IA de Clipchamp | [Transcription, correction et SRT](https://support.microsoft.com/en-us/clipchamp/how-to-use-autocaptions-in-clipchamp). Le son est traité par Azure ; n'y mettre que la narration fictive. Si indisponible, faire générer un SRT puis recaler chaque entrée sur le son réel |
| Avatar | Aucun dans la version de base | La voix synthétique suffit. Un avatar original reste facultatif, après un essai exporté de 10 secondes ; aucune imitation de camarade ni abonnement requis pour finir |

Budget cible : 0 EUR de dépense supplémentaire. Si un compte ou un quota
ne permet pas l'export, changer d'outil ou simplifier les plans, sans multiplier
les comptes pour contourner les limites. Aucun prix promotionnel tenu pour acquis.
Ne pas rendre la livraison dépendante de 285 secondes de text-to-video :
les plans de l'interface et des résultats sont générés de façon déterministe.

## 4. Adaptation de S61 et montage

Conserver les sept blocs, les 41 plans et les résultats sourcés de S61.
Les durées de voix calculées à 140 mots/minute sont indicatives : la vraie
durée du TTS détermine le calage. La cible 4:45 inclut générique et mentions.

| Temps | Plans S61 | Traitement IA |
| --- | --- | --- |
| 0:00-0:20 | 01-02 | Dossier fictif illustré, champs sensibles avec libellés lisibles, voix synthétique |
| 0:20-0:50 | 03-04 | Cartons juridiques déterministes reprenant seulement les références déjà sourcées |
| 0:50-1:05 | 05-06 | Logo existant, explication du nom, transition vers Import |
| 1:05-3:00 | 07-30 | Reconstitution animée vérifiée du parcours Import, Review, Restore ; mentions mode A visibles ; contrôle de la consigne, ajout manuel, réponse illustrative et restauration |
| 3:00-3:45 | 31-36 | Pipeline et chiffres exacts, code mesuré, petite vue EN et réserves explicites |
| 3:45-4:20 | 37-39 | Bénéfice proposé, coût de revue, absence d'étude de productivité ou de comparaison indépendante |
| 4:20-4:45 | 40-41 | Limites, responsabilité, adresses et crédit IA discret dans le carton final |

Pour une version entièrement synthétique, reconstruire les contrôles UI à partir
de références vérifiées, avec texte vectoriel dans le montage. Ne pas demander
à un générateur vidéo probabiliste d'écrire les boutons, jetons ou tableaux.
Le projet généré doit avoir un fichier de données unique pour texte, jetons,
réponse illustrative et restauration. Un changement de scène doit garder
les mêmes valeurs et décisions. Aucune détection manquante inventée : le code
`qx-74-zp` doit être vérifié comme non marqué avant d'en faire un exemple.
À défaut de vérification, annoncer l'ajout manuel comme une fonction illustrée,
sans affirmer que la version courante a raté cet identifiant.

Conserver les alertes réelles connues et ne générer aucun état prêt à envoyer
tant que le scénario ne montre pas leur résolution. Ne jamais afficher de table
de correspondance dans l'interface ChatGPT, même pour rendre le montage plus clair.
En mode A, la réponse est écrite pour l'illustration, annoncée comme telle,
avec les jetons exacts issus du message vérifié. Sa restauration doit correspondre
à la fonction réelle sur cet exemple, pas à un remplacement approximatif inventé.

## 5. Étapes et points d'arrêt

Temps indicatifs à partir de la prise en charge, indépendants des sessions code.
Paris : version contrôlable jeudi 29 octobre à 14:00, finale à 16:00,
remise au responsable du dépôt avant 17:00 ; dépôt cible 21:00, marge 21:59.
Si le travail commence tard, supprimer les inserts et l'avatar, garder tout le parcours.

| Étape | Budget | Sortie et condition pour continuer |
| --- | --- | --- |
| V0, essai freemium | 20 min | 10 secondes exportées avec voix, texte UI et sous-titre ; coût nul, droits et filigrane constatés |
| V1, adaptation finale | 30 min | Script TTS nettoyé et liste des 41 plans ; toutes les mentions synthétiques explicites |
| V2, validation de la démo | 45 min | État initial, détections, décisions, message, réponse et restauration cohérents ; provenance conservée |
| V3, voix | 40 min | Sept fichiers audio nommés `01_hook` à `07_close`, même voix et accent ; durées mesurées |
| V4, images et animations | 90 min | 41 plans générés depuis le scénario validé, résultats et logo fidèles ; contrôle à chaque groupe de plans |
| V5, montage et sous-titres | 70 min | MP4 brouillon et SRT, voix calée, lecture intégrale, corrections ciblées |
| V6, contrôle et remise | 45 min | Export 1080p, copie 720p, crédit, journal et lien testé ; verdict sur chaque critère |

Environ 5 h 40 avec marge jusqu'à 6 h 30. Au premier blocage de génération
d'ambiance, utiliser des cartons animés générés par code. Au blocage d'avatar,
le retirer. Au blocage TTS, utiliser Clipchamp. Ne jamais couper revue,
contrôle de la consigne, restauration, avertissement table ou limites.

## 6. Prompts opérationnels pour le camarade

Donner uniquement les pièces nécessaires à chaque outil. Ces prompts sont
préparés ; ils ne sont pas encore déclarés comme exécutés dans les crédits.

### V1 : direction et adaptation

```text
Tu réalises la vidéo HuisClos, en anglais, entièrement générée avec IA,
voix comprise. Je te fournis SCRIPT.md, STORYBOARD.md, ce plan et les preuves
publiques fictives. Conserve les sept blocs et les 41 plans, cible 4:45,
fenêtre 4:30-5:30. Ne modifie pas le produit. Mode A : reconstitution animée,
mention permanente "AI-generated reconstruction. Fictional data." ; réponse
marquée "Illustrative AI answer". Aucun tournage humain, voix TTS originale.
Rends : script spoken-only, sept budgets de durée, tableau de production
par plan et liste des fichiers. Aucun chiffre ou résultat nouveau, aucune
conformité ou fuite nulle promise. Une affirmation sans preuve est retirée
ou explicitement présentée comme hypothèse. Signale toute incohérence
entre scénario, libellés, jetons et résultat avant de créer les médias.
```

### V2/V4 : génération déterministe de la démo

```text
À partir du storyboard et des états fictifs vérifiés joints, génère un projet
vidéo autonome hors du dépôt HuisClos, avec les commandes de rendu et les
dépendances exactes. Utilise un moteur déjà disponible ; n'invente pas qu'un
rendu a réussi. Produis des animations déterministes, texte vectoriel lisible,
16:9, 1920x1080, 30 fps. Palette #1F3A5F, #0E7490, blanc ; logo fourni intact.
Pas de CDN, médias distants, données réelles ou table envoyée au LLM.
Un seul fichier de données porte états, valeurs, jetons, réponse illustrative
et restauration. Respecte les 41 plans, avec zooms Review/Restore et mentions
de reconstitution. Les boutons reprennent les références sans libellé inventé.
Les plans 23-25 illustrent le transfert du message vérifié et une réponse
préparée, sans prétendre à une requête en direct. Les chiffres 157/190,
170/190, 325/3600, 218/3600 ont leur provenance G8R2 et leurs limites visibles.
Rends d'abord 10 secondes exportables, puis les plans séparés avec durées,
une image de contrôle par état et un manifeste des sources. Tout état non
vérifié est un point à résoudre, pas une permission d'inventer un succès.
```

### V3 : consigne de voix

```text
English narration, calm and clear, suitable for a university legal technology
demo. One consistent original synthetic voice; no voice cloning. Aim around
140 words per minute, with short pauses between actions. Pronounce HuisClos
"wee-kloh", GDPR as letters and F2 as "F two". Read only the supplied spoken
text. Do not read citations, headings, tables, timestamps or production cues.
Do not add music or words. Generate each of the seven blocks separately.
```

Cette consigne est à appliquer aux réglages du TTS ; coller seulement le texte
à lire dans le champ de synthèse. Tester d'abord la prononciation du nom.
Pour éviter que la voix dise une annotation source, nettoyer toutes les
annotations `[source: ...]` avant synthèse, en conservant les références à part.

### V5/V6 : contrôle du montage

```text
Contrôle le MP4 fourni, son SRT, le script et les preuves G8R2 joints.
Si tu ne peux pas lire le fichier vidéo ou mesurer sa durée, indique-le :
ne déduis pas la durée réelle de la seule dernière ligne du SRT.
Rends un tableau critère/preuve/écart/correction : durée, continuité,
lisibilité des jetons et boutons, synchronisation, erreurs de sous-titrage,
mentions synthétiques, données fictives, distinction local/cloud, table
jamais transmise, revue humaine, portée FR et réserves EN, chiffres exacts,
sources, logo, nom, valeur qualitative, adresses, crédits et droits d'export.
Compare les jetons du message, de la réponse illustrative et de la restauration.
Donne les timecodes des corrections. Verdict prêt seulement si les écarts
bloquants sont résolus ; aucune supposition de succès à partir du storyboard.
```

## 7. Contrôle et remise au projet

- Clarté, 10 points : problème, nom, parcours et responsabilité compréhensibles.
- Concision, 5 : une seule démo FR et brève vue EN, aucun plan sans fonction.
- Délivrance, 5 : voix synthétique intelligible, prononciations et pauses relues.
- Production, 5 : UI lisible, pas de texte déformé, audio stable, SRT synchronisé.
- Durée, 5 : fichier réellement lu, durée mesurée dans la fenêtre de la consigne.

Contrôler aussi : absence de données réelles, liens utilisables, droits des médias,
absence de filigrane gênant sur l'export test et export final, aucun chiffre
inventé, mode A annoncé, aucun GO bilingue complet ni couverture significative
affirmée. Pas de concurrents nommés ou guide CNB non sourcé : S61 les a omis.

Le journal vidéo indique date, outil/modèle, offre, prompt exact, fichier généré,
durée, retouches, licence/attribution et responsable. Le générique inclut
**AI-generated visuals and synthetic narration. Human editorial review.**
Ajouter toute attribution imposée par l'outil, notamment au titre si ElevenLabs
Free est retenu. Ne pas promettre une gratuité universelle sur la base de ce plan.

Le camarade remet le paquet hors dépôt au responsable. Celui-ci reporte ensuite
le lien final et les usages IA réellement attestés dans le dossier de dépôt,
avec un complément documentaire dédié. S71/S72 restent terminables auparavant.
Ce fichier prépare la production ; aucun MP4, voix, compte ou publication
n'a été créé pendant cette session de planification.
