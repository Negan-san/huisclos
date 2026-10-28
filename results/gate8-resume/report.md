# G8R2 : recontrôle de FIX4 et reprise unique du challenge

Code mesuré : `930c414dd7ae1e7128b292bfa7bac1e45f27b1e9`. FIX3R-01 clos, **GO du correctif FIX4**.

Périmètre FR : **GO du correctif et des critères français mesurés**.
Standard reste le défaut ; Enhanced est recommandé comme option locale française dans ce périmètre.

Fonctionnement technique FR/EN : GO sur fixtures fictives hors ligne. Enhanced EN
reste expérimental et non recommandé. Aucune validation bilingue sans réserve.

## Périmètre et prérequis

Arbre initial propre sur lane-b ; SHA dev enregistré puis fusionné en avance rapide,
HEAD égal au SHA prévu. Diff depuis 4b8a686 : état, tests et documentation seulement.
tokens.py, détection, modèles, configurations, corpus et dépendances inchangés.

Huit AppTest indépendants : UI/document FR et EN, RuntimeError/ValueError, premier
échec et retour réel Restore vers Review. Tous les résultats, bases, réponses, tables
importées à Restore, contrôles, avis et autorisations précédents sont invalidés.
Décisions, ajout manuel, table de dossier, consigne et réglages sont conservés.
Chaque panne est suivie d'un succès et d'une restauration exacte ; aucune mention
de la panne n'apparaît dans les messages ou journaux. Quatre vrais workers séparés
passent sur un nom présent dans le texte et un nom de fichier : Standard/Enhanced,
FR/EN. Douze fichiers de modèles retenus et versions conformes au manifeste A4.

La suite complète sous garde FIX3R compte 1749 réussites, sans xfail, en 267,41 secondes.
Elle inclut ces sondes et les sept tests du lanceur ;
roundtrip limité à dev, zéro ouverture réservée refusée. Ruff check/format, style et
diff conformes. Les journaux preflight et final portent les commandes et résultats.
Le premier précontrôle (preflight) a étendu à tort HUISCLOS_MODELS_DIR aux tests du
cache : deux assertions sur le chemin échouent, 1747 tests passent. Le lanceur seul a été corrigé
pour limiter cette variable aux sondes worker. Les deux témoins passent ensuite, puis
la suite complète est reprise dans preflight2, avant tout accès au challenge.

Preuves FIX3R réutilisées : vingt cas Standard requis, six régressions avant/après,
invariants Presidio et mémoire contrôlée. Pas de nouvelle exploration générale.
Limites recevables conservées : D-FIX3-2, docstring _token_tables obsolète,
surmasquage FR numérique isolé sans fuite, longueurs et avertissements connus.

## Registre et méthode

Quatrième exécution historique, diagnostics compris : G7 complète, G8 en échec,
FIX2 diagnostique, puis G8R2. Registre et reçu créés exclusivement avant lancement ;
un second essai est refusé avant tout accès réservé. Plan historique FR inchangé :
hybrid et hybrid_camembert, seuil 0,30 ; contrôle 0,10, bootstrap apparié 2000 tirages,
graine 45, marges précision 0,02 et surmasquage 0,01. Une seule exécution par profil ;
les mêmes prédictions alimentent métriques et intervalles. Aucun autre CLI de mesure.

Seuls les scripts de mesure/provenance lisent et hachent le challenge ; son hash reste historique.
Aucune lecture manuelle ; test et C3 ni ouverts, ni hachés, ni remesurés. Archives
antérieures préservées. Aucune sortie brute du worker conservée. Ce challenge déjà
connu ne constitue pas une nouvelle validation aveugle.

## Challenge FR courant

| Profil | Couverts | Fuite caractères | Précision partielle | Surmasquage caractères |
| --- | ---: | ---: | ---: | ---: |
| enhanced | 170/190 | 218/3600 | 0.801802 | 379 |
| standard | 157/190 | 325/3600 | 0.803922 | 366 |

Critères Enhanced contre Standard (plan figé) :

- lower_leakage : True.
- higher_full_coverage : True.
- precision_within_margin : True.
- over_masking_within_margin : True.
- met : True.

Différences appariées, candidat Enhanced moins référence Standard :

| Stade | Mesure | Différence | IC95 | Exclut zéro |
| --- | --- | ---: | --- | --- |
| detection | precision | -0.002120 | [-0.021053 ; 0.018175] | False |
| detection | recall | 0.073684 | [0.010753 ; 0.166667] | True |
| detection | full_coverage_rate | 0.068421 | [0.000000 ; 0.166667] | False |
| detection | leaked_character_rate | -0.029722 | [-0.061759 ; -0.006485] | True |
| detection | non_sensitive_masked_rate | 0.000836 | [0.000000 ; 0.001773] | False |
| pseudonymization | full_coverage_rate | 0.068421 | [0.000000 ; 0.166667] | False |
| pseudonymization | leaked_character_rate | -0.029722 | [-0.061759 ; -0.006485] | True |
| pseudonymization | non_sensitive_masked_rate | 0.000836 | [0.000000 ; 0.001773] | False |

Les intervalles marginaux, métriques exactes/partielles, CUSTOM/LOCATION, alertes
et coûts par processus figurent dans [le rapport complet](challenge/robustness.md).
Les alertes ne masquent rien. Aucun seuil n'est rechoisi.
Le contrôle final est disponible pour les deux profils ; huit appels principaux de détection par profil.
L'intervalle apparié de fuite exclut zéro ; celui de couverture complète touche zéro.
Le GO repose sur les estimations ponctuelles préenregistrées, sans déclarer le gain de couverture
statistiquement significatif. Avant revue humaine, 33 entités Standard et 20 Enhanced restent
au moins partiellement exposées sur ce challenge fictif.

L'état Git de mesure est consigné dans registration.json : seuls les nouveaux artefacts de gate
sont non suivis, le code mesuré correspond au SHA annoncé. Les empreintes des scripts et du plan
réellement employés sont enregistrées avant lancement.

## Comparaison historique, sans nouvelle mesure G7

| Profil | Précision G7 vers courant | Rappel G7 vers courant | Fuite G7 vers courant |
| --- | --- | --- | --- |
| standard | 0.792079 vers 0.803922 | 0.842105 vers 0.863158 | 462 vers 325 |
| enhanced | 0.795455 vers 0.801802 | 0.921053 vers 0.936842 | 349 vers 218 |

Même empreinte de corpus. G7 n'a pas enregistré couverture complète et surmasquage :
ces valeurs et les intervalles appariés G7/courant restent indisponibles. Aucune
reconstruction depuis les agrégats et aucune significativité entre rapports distincts.

## Résultats G8 réutilisés comme histoire

Code historique e3d13bd, aucun de ces chiffres n'est une nouvelle validation de FIX4.
Sur C3 FR, Standard 95/105 couverts et 139/2042 caractères exposés ; Enhanced 96/105
et 130/2042. Les trois critères comparatifs FR de G8 restent historiquement remplis.
Test historique G8 : 93/93 couverts et 0/1889 exposés pour les deux profils.
C3 EN : Standard 78/100 et 235/2285, Enhanced 88/100 et 115/2285. Précision partielle
0,834862 vers 0,700000 : perte 0,134862, supérieure à 0,02. Enhanced EN conserve donc
son NO-GO de recommandation ; Standard EN reste expérimental avec réserves fortes.

Standard reste le repli, avec revue humaine complète et ajouts manuels. La
pseudonymisation n'est pas une anonymisation et les résultats ne garantissent pas
une absence de fuite sur tout document. Corpus fictifs petits, auteurs corrélés,
challenge déjà connu et continuité des jetons limitée restent des réserves explicites.
Aucun code applicatif corrigé pendant cette gate, aucun paquet installé, tag, push ou R8.

Le premier diff indexé a signalé cinq lignes à espaces finaux dans le journal pytest du
précontrôle en échec. Copie originale exacte conservée en .log.raw ; version texte normalisée
et empreintes avant/après enregistrées dans log-normalization.json. Aucune donnée de mesure
ni archive antérieure modifiée par cette normalisation.
