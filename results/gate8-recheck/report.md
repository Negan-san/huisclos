# G8R : recontrôle indépendant des corrections

Verdict global : NO-GO. G8-01 est corrigé ; le challenge historique reste indisponible
et Enhanced EN dépasse toujours la marge de perte de précision préenregistrée.
Aucune publication, aucun tag ni push. Le parcours s'arrête après G8R selon le pilote.

## Référence et choix enregistré avant exécution

FIX `37f98f15bd82ac2edf4c4d6ebe03d2ec0c58cb10` est la nouvelle référence du gel.
Le diff depuis G8 `1ecb063` porte sur le harnais, ses tests et les journaux/protocole.
Les arbres métier `src`, `app`, `data` et `.streamlit` sont identiques au HEAD mesuré
`e3d13bd`. Aucun détecteur, seuil, modèle, configuration ou dépendance modifié.

D-G8R-1 consigne avant les contrôles le choix de réutiliser les mesures G8.
G8R n'ajoute aucune série de détection sur C3, test ou challenge, aucun balayage dev
ni nouveau choix de seuil. C3 est un holdout déjà mesuré ; ce recontrôle ne constitue
pas une nouvelle validation aveugle. Les métriques décrivent le code mesuré en G8,
dont les arbres métier sont identiques à FIX, et ne sont pas des mesures du harnais FIX.

## Registre des mesures réservées

| Série | Essais G8 | État conservé | Essais G8R |
| --- | --- | --- | --- |
| C3 FR | 1 | Rapport G8 réutilisé | 0 |
| C3 EN | 1 | Rapport G8 réutilisé | 0 |
| Test historique FR | 1, quatrième mesure du projet | Rapport G8 réutilisé | 0 |
| Challenge historique FR | 1 | Échec code 2, sans rapport ni prédictions récupérables | 0 |

Les reçus et les trois séries terminées restent dans [gate8](../gate8/report.md).
L'essai challenge échoué n'est ni effacé, ni remplacé, ni relancé.
Les tests et sondes techniques utilisent uniquement des valeurs fictives connues.

## Recontrôle des points ouverts

| Point | Preuve indépendante | État G8R |
| --- | --- | --- |
| G8-01, perte des sorties si le contrôle final échoue | Huit régressions nouvelles ; comparaison exacte de tous les spans et substitutions sur quatre documents, panne au premier, deuxième ou dernier ; aucune reprise du contrôle après panne | Corrigé |
| Diagnostic du worker | Injections aux quatre stades load, detection, pseudonymization et metadata ; code 3, stade et classe seuls ; panne finale seule : code 0, contrôle indisponible | Vérifié sur fixtures |
| Indisponibilité honnête | Alertes de tout le profil à null après panne ; rapport reconstruit indisponible ; aucune absence d'alerte fabriquée ; message de l'exception absent du payload | Vérifié |
| Challenge historique | Reçu d'échec préservé, aucune prédiction récupérable ni rapport ; aucune nouvelle mesure autorisée en l'absence de changement de détection | Ouvert, NO-GO |
| Enhanced EN | Recalcul pur de la différence à partir des agrégats G8 : 0,8348623853 vers 0,7000000000, perte 0,1348623853 supérieure à 0,02 | NO-GO de recommandation |

Le nouveau diagnostic n'établit pas la cause de l'ancien échec challenge.
Aucun lien causal avec G8-01 n'est démontré. Les gains de protection EN ne permettent
pas de modifier après coup la marge de précision ou les seuils.

## Contrôles techniques

Les 205 tests ciblés couvrent le harnais, les quatre parcours croisant langue UI et
langue du document, les modèles absents, le mode public, le payload exact, la révocation
à chaque changement, la confirmation à usage unique et la mémoire de dossier.
Ils couvrent aussi la projection Unicode, les répétitions et offsets exacts, le refus
des résultats GLiNER incohérents et des prompts tronqués, et les fenêtres bornées.
Les journaux et codes de la suite complète sont dans [full-checks.json](full-checks.json).
La suite complète compte 1699 tests réussis en 143,90 secondes. Deux avertissements :
torch.jit.script déprécié, déjà connu, et cache pytest non inscriptible sans effet sur les
résultats. Quatre lignes trop longues du nouveau script de synthèse ont été corrigées ;
Ruff check/format, style (zéro erreur, quinze longueurs connues) et diff sont ensuite
contrôlés dans [final-checks.json](final-checks.json). Aucun nouveau test ni code métier
n'a changé après la suite complète.

Les quatre sondes [offline.json](offline.json) exécutent Enhanced FR/EN dans des
processus neufs, caches vides, sockets et DNS bloqués avant import métier. Deux documents
par langue gardent leurs jetons, restaurent exactement leur texte et une réponse mêlée ;
les écritures sont interdites pendant le traitement. Retirer un auxiliaire de chaque
paquet provoque le refus attendu, sans repli. Aucun cache modèle n'est créé.

[integrity.json](integrity.json) vérifie vingt fichiers de modèles, les freezes
installés et pip check des environnements actuel et G7, ainsi que 79 artefacts G8.
Le premier contrôle brut a refusé summarize.py, converti en CRLF par le checkout
Windows : l'essai est conservé dans integrity-attempt1.json. La vérification corrigée
compare son hash Git nettoyé et conserve son hash brut ; tous les artefacts hors Python
sont également vérifiés octet pour octet. Aucun fichier G8 n'a été réécrit.

Le premier index des preuves G8R utilisait un hash Git filtré différent du blob brut
effectivement indexé pour les rapports. Le contrôle a échoué mais la commande shell
a poursuivi jusqu'au commit. Les SHA-256 des rapports sont restés identiques aux blobs.
L'ancien index est conservé dans artifact-index-attempt1.json et le contrôle refusé
dans index-verification-attempt1.json. L'index final décrit les blobs réellement indexés
et leurs SHA-256, séparés des octets du disque. Le seul commit est amendé avant finish.

## Verdict par langue et profil

| Langue et profil | Couverture complète G8 | Fuite de caractères G8 | Verdict G8R |
| --- | --- | --- | --- |
| FR Standard | 95/105 | 139/2042 | Gains observés conservés ; validation challenge ouverte |
| FR Enhanced | 96/105 | 130/2042 | Critère ponctuel conservé ; validation challenge ouverte |
| EN Standard | 78/100 | 235/2285 | Parcours fonctionnel, expérimental avec réserves fortes |
| EN Enhanced | 88/100 | 115/2285 | NO-GO de recommandation, marge de précision refusée |

Le test historique conserve 93/93 entités évaluées couvertes et 0/1889 caractères
exposés pour les deux profils ; CUSTOM et LOCATION restent hors de ce périmètre.
Les gains et leurs intervalles sont ceux de G8, sans nouvelle estimation d'incertitude.
Les petits corpus fictifs, l'auteur unique et la corrélation de style restent des limites.

Repli : Standard, revue humaine complète, ajouts manuels et contrôle des deux segments.
Une absence d'alerte ne garantit ni anonymat ni fuite nulle. Aucune boucle automatique
de correction et mesure n'est ouverte après ce recontrôle.
