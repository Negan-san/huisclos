# Corpus, lot 5 : jeu challenge rédigé à l'aveugle (C2)

Ce fichier décrit comment le jeu challenge a été écrit. Il ne contient volontairement aucune valeur des documents : les agents de code peuvent lire ce dossier, alors que les sources `chl_*.md` et `corpus/challenge.jsonl` leur restent fermées (AGENTS.md, section 11).

## Conditions de rédaction

- Session C2, 28 octobre 2026, Claude Code (Opus 5.5), piste A, après le gel des règles de détection de S14.
- Fichiers lus : AGENTS.md, les deux dernières entrées de docs/PROGRESS.md, corpus/README.md, corpus/source/doc_01.md (format) et l'annexe A5 de docs/MASTER_PLAN.md.
- Fichiers non lus : src/, tests/, results/, les sources doc_07 à doc_26 et les décisions D-S14. L'auteur ne connaît donc ni les nouvelles règles ni les documents dev difficiles qui les ont guidées.
- Aucun code modifié : le builder acceptait déjà le split challenge.

## Commande de la session (extrait du prompt)

Huit documents de types absents du corpus actuel : chl_01 assignation devant le tribunal judiciaire ; chl_02 échange de SMS retranscrit dans une attestation ; chl_03 extrait de rapport d'expertise après un accident, sans détail médical ; chl_04 compte rendu d'enquête interne pour harcèlement ; chl_05 mise en demeure adressée par un assureur ; chl_06 fiche de renseignements client d'un cabinet, sous forme de formulaire à champs ; chl_07 courriel transféré avec historique et signatures ; chl_08 texte extrait d'un PDF scanné de qualité moyenne, avec coupures et espaces manquants.

Chaque difficulté doit apparaître au moins deux fois sur le lot, sans jamais être signalée dans le texte. Les règles d'annotation et la relecture suivent l'annexe A5.

## Volume

| Document | Mots | Annotations |
| --- | --- | --- |
| chl_01 | 491 | 24 |
| chl_02 | 395 | 28 |
| chl_03 | 423 | 24 |
| chl_04 | 401 | 27 |
| chl_05 | 335 | 22 |
| chl_06 | 319 | 29 |
| chl_07 | 324 | 30 |
| chl_08 | 275 | 19 |

Total : 203 entités. Chaque document contient au moins une personne citée sous plusieurs formes.

## Couverture des difficultés imposées

| Difficulté | Documents |
| --- | --- |
| Personnes nommées dans un ordre inhabituel (nom avant prénom, avec ou sans virgule) | 01, 02, 03, 04, 05, 06, 07 |
| Prénoms composés | 01, 02, 03, 04, 06, 07, 08 |
| Particules | 01, 02, 03, 05, 06, 08 |
| Initiales | 01, 02, 03, 04, 05, 06, 07, 08 |
| Noms qui sont aussi des mots courants | 01, 02, 03, 04, 05, 06, 07, 08 |
| Noms en minuscules ou en majuscules | 01, 02, 03, 04, 05, 06, 07, 08 |
| Libellés de champ en tête de ligne | 02, 03, 04, 05, 06, 07 |
| Identifiants internes libellés (CUSTOM) | 02, 03, 04, 05, 06, 07, 08 |
| Numéros de procédure variés (RG, Portalis, minute, prud'hommes, parquet) | 01, 02, 03, 04, 07, 08 |
| Adresses complexes (bis, ter, BP, CS, Cedex, lieu-dit, résidence, outre-mer) | 01, 02, 03, 05, 06, 07, 08 |
| Téléphones de formats variés (compact, points, international, poste) | 02, 03, 04, 07, 08 |
| Courriels de formats variés (majuscules, signe plus, chevrons, forme [at]) | 02, 05, 06, 07 |
| Dates de naissance de formats variés (lettres, points, tirets, ISO, mois abrégé, espace manquante) | 01, 02, 05, 06, 08 |
| Coupures de ligne au milieu d'une entité | 03, 07, 08 |
| Pièges A5 laissés en clair (juridictions, articles, dates d'audience, montants) | tous |
| Piège {{DIGITS9}} | 01, 05, 07, 08 |

## Difficultés ajoutées

1. Noms de personnes dans des noms de fichiers (documents 02, 03, 04, 07). Les pièces jointes et les pièces versées portent souvent le nom du client ou d'un salarié, collé à d'autres mots par des tirets bas. Seul le nom est annoté, à l'intérieur du nom de fichier. Un outil qui découpe le texte en mots sur les espaces ne le voit pas.
2. Diminutifs et surnoms (documents 02, 04, 07). Dans les SMS, les messageries internes et les courriels entre collègues, une personne est désignée par un diminutif, un surnom ou son seul prénom. Ces formes identifient la personne dans le contexte du dossier et sont annotées PERSON, même quand elles ne ressemblent à aucune forme déjà citée.
3. Sigle repris après la raison sociale (documents 04, 05, 06). Une organisation est citée une fois sous son nom complet, puis par un sigle, ou par une partie seulement de sa dénomination, sans forme juridique. Chaque reprise est annotée ORGANIZATION.

## Conventions retenues

- La particule fait partie du nom et entre dans le span ; la civilité reste dehors, même collée au nom sans espace (texte de scan).
- Les initiales entrent dans le span avec le nom qu'elles accompagnent.
- Une raison sociale qui contient un nom de personne est annotée une seule fois en ORGANIZATION ; le même nom employé seul pour la personne est annoté PERSON.
- Pour un téléphone suivi d'un numéro de poste, seul le numéro est annoté ; le poste reste en clair.
- Les lieux de naissance et les villes citées seules restent en clair (LOCATION n'est pas un type du corpus).
- Les témoins désignés par un numéro dans un compte rendu restent en clair : ce numéro est déjà une pseudonymisation.
- Les numéros à clé de contrôle passent tous par un marqueur. Pour varier les formats de téléphone, certains numéros sont écrits à la main dans les tranches que l'ARCEP réserve aux œuvres de fiction ; ils n'ont pas de clé de contrôle.
- Les identifiants de pièces d'identité, de contrats d'assurance, de sinistres, de signalements, de prêts et les références de dossier sont annotés CUSTOM, avec leur libellé laissé en clair.

## Relecture A5

Relecture faite pour chaque source : chaque valeur annotée à chacune de ses occurrences, vérifié aussi par un script qui cherche les valeurs annotées restées en clair ailleurs dans le texte ; aucune civilité ni aucun libellé dans une annotation ; aucun nom de personne ou de société connue ; aucun numéro à clé écrit à la main ; en-tête complet. `PY scripts/build_corpus.py --check` a validé le lot au premier cycle.
