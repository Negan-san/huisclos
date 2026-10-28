# G8 : résultats agrégés et provenance

Verdict global : NO-GO. Enhanced EN échoue à la marge de précision préenregistrée.
Le challenge historique n'a pas de rapport exploitable ; son essai n'est pas répété.
Les contrôles techniques et les gains FR mesurés sont conservés ; EN reste expérimental.
G8-01 : panne injectée, prédictions perdues, xfail strict ; cause challenge inconnue.
Détails et replis : docs/DECISIONS.md, D-G8-1.

Mesure indépendante du 28 octobre 2026, code métier gelé A4 dc5b041, HEAD de mesure e3d13bd.
Plans et harnais enregistrés avant tout chiffre réservé dans registration.json.
Les fichiers G7 sont conservés intégralement dans g7_archive, sans nouvelle mesure de leurs anciens splits.

Une détection principale par document/profil/code, toutes les propositions substituées automatiquement.
Les prédictions en mémoire alimentent métriques exactes/partielles, F2, couverture, fuite et intervalles.
Les relectures du contrôle final sont mesurées séparément ; les alertes ne masquent rien.
Bootstrap par document, 2000 tirages, graine 45 ; mêmes tirages pour les différences appariées.
Aucun humain connaissant le gold n'est simulé. Aucun seuil n'est rechoisi après mesure aveugle.

G7 ne propose pas de véritable profil anglais : aucune référence EN G7 n'est publiée.
Les onze types historiques et le périmètre CUSTOM/LOCATION sont séparés. Aucun LOCATION dans C3.
Les intervalles de précision/rappel/F2 sont ceux du mode partiel ; les métriques exactes sont ponctuelles.

## Lot neuf FR

8 documents ; corpus SHA-256 : `df179266f4866128c5b4aaa770559d4ebedfd06c5a0cf47a9f6490ab51d89d6f`.

| Profil | P exacte | R exact | P partielle [IC95] | R partiel [IC95] | F2 [IC95] |
| --- | --- | --- | --- | --- | --- |
| enhanced | 0.8725 | 0.8476 | 0.8824 [0.8370, 0.9494] | 0.8571 [0.8316, 0.8833] | 0.8621 [0.8404, 0.8886] |
| g7_enhanced | 0.8627 | 0.8381 | 0.8824 [0.8370, 0.9494] | 0.8571 [0.8316, 0.8833] | 0.8621 [0.8404, 0.8886] |
| g7_standard | 0.8725 | 0.8476 | 0.8922 [0.8473, 0.9500] | 0.8667 [0.8367, 0.8915] | 0.8716 [0.8469, 0.8954] |
| standard | 0.8824 | 0.8571 | 0.8922 [0.8473, 0.9500] | 0.8667 [0.8367, 0.8915] | 0.8716 [0.8469, 0.8954] |

| Profil | Couverts | Couverture [IC95] | Caractères exposés | Fuite [IC95] | Entités partielles/entières exposées | Documents exposés | Surmasquage caractères | Taux [IC95] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | 96/105 | 0.9143 [0.8837, 0.9350] | 130/2042 | 0.0637 [0.0414, 0.1020] | 2/7 | 8 | 27/20518 | 0.0013 [0.0000, 0.0021] |
| g7_enhanced | 95/105 | 0.9048 [0.8764, 0.9268] | 162/2042 | 0.0793 [0.0506, 0.1131] | 3/7 | 8 | 27/20518 | 0.0013 [0.0000, 0.0021] |
| g7_standard | 94/105 | 0.8952 [0.8609, 0.9259] | 171/2042 | 0.0837 [0.0506, 0.1225] | 4/7 | 8 | 27/20518 | 0.0013 [0.0000, 0.0021] |
| standard | 95/105 | 0.9048 [0.8764, 0.9268] | 139/2042 | 0.0681 [0.0480, 0.1030] | 3/7 | 8 | 27/20518 | 0.0013 [0.0000, 0.0021] |

CUSTOM/LOCATION, hors comparaison principale :

| Profil | Couverts | Caractères exposés | Entités partielles exposées | Entités entièrement exposées |
| --- | --- | --- | --- | --- |
| enhanced | 2/7 | 53 | 1 | 4 |
| g7_enhanced | 2/7 | 53 | 1 | 4 |
| g7_standard | 2/7 | 53 | 1 | 4 |
| standard | 2/7 | 53 | 1 | 4 |

Alertes finales sans masquage :

| Profil | Alertes | Sur références visibles | Ailleurs | Entités exposées alertées |
| --- | --- | --- | --- | --- |
| enhanced | 2 | 0 | 2 | 0/9 |
| g7_enhanced | 2 | 0 | 2 | 0/10 |
| g7_standard | 3 | 1 | 2 | 1/11 |
| standard | 3 | 1 | 2 | 1/10 |

Coûts par processus neuf, CPU, OMP/MKL demandés à deux threads, RSS échantillonné toutes les 20 ms.
Les imports métier sont inclus au chargement ; démarrage de Python et imports du harnais exclus.

| Profil | Chargement s | Inférence s | Substitution s | Contrôle s | Pic RSS Mio | Appels principaux |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | 12.78 | 8.06 | 0.01 | 14.32 | 1165.1 | 8 |
| g7_enhanced | 13.55 | 7.98 | 0.01 | 6.97 | 1253.2 | 8 |
| g7_standard | 12.14 | 1.12 | 0.01 | 1.02 | 737.5 | 8 |
| standard | 12.14 | 1.17 | 0.01 | 1.95 | 739.7 | 8 |

[Rapport complet](blind_fr/robustness.md), [JSON](blind_fr/robustness.json).

## Lot neuf EN

8 documents ; corpus SHA-256 : `e3fd4886a2499563f6710cf1cfe57a3f27b3302be1e576e06ac67a4ddede5aea`.

| Profil | P exacte | R exact | P partielle [IC95] | R partiel [IC95] | F2 [IC95] |
| --- | --- | --- | --- | --- | --- |
| enhanced | 0.6462 | 0.8400 | 0.7000 [0.6460, 0.7708] | 0.9100 [0.8750, 0.9457] | 0.8585 [0.8268, 0.8929] |
| standard | 0.6881 | 0.7500 | 0.8349 [0.7641, 0.9032] | 0.9100 [0.8518, 0.9496] | 0.8939 [0.8410, 0.9375] |

| Profil | Couverts | Couverture [IC95] | Caractères exposés | Fuite [IC95] | Entités partielles/entières exposées | Documents exposés | Surmasquage caractères | Taux [IC95] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | 88/100 | 0.8800 [0.8384, 0.9271] | 115/2285 | 0.0503 [0.0266, 0.0680] | 7/5 | 7 | 252/20880 | 0.0121 [0.0078, 0.0166] |
| standard | 78/100 | 0.7800 [0.7241, 0.8367] | 235/2285 | 0.1028 [0.0687, 0.1355] | 16/6 | 8 | 93/20880 | 0.0045 [0.0020, 0.0075] |

CUSTOM/LOCATION, hors comparaison principale :

| Profil | Couverts | Caractères exposés | Entités partielles exposées | Entités entièrement exposées |
| --- | --- | --- | --- | --- |
| enhanced | 2/8 | 60 | 2 | 4 |
| standard | 2/8 | 60 | 2 | 4 |

Alertes finales sans masquage :

| Profil | Alertes | Sur références visibles | Ailleurs | Entités exposées alertées |
| --- | --- | --- | --- | --- |
| enhanced | 43 | 4 | 39 | 4/12 |
| standard | 28 | 1 | 27 | 1/22 |

Coûts par processus neuf, CPU, OMP/MKL demandés à deux threads, RSS échantillonné toutes les 20 ms.
Les imports métier sont inclus au chargement ; démarrage de Python et imports du harnais exclus.

| Profil | Chargement s | Inférence s | Substitution s | Contrôle s | Pic RSS Mio | Appels principaux |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | 14.59 | 21.28 | 0.01 | 38.99 | 2823.3 | 8 |
| standard | 9.16 | 1.05 | 0.01 | 2.05 | 420.2 | 8 |

[Rapport complet](blind_en/robustness.md), [JSON](blind_en/robustness.json).

## Test historique FR, quatrième mesure

6 documents ; corpus SHA-256 : `12a7852e765d98c10be74025e684c15280ccb47615017529ee320370faa4cd4d`.

| Profil | P exacte | R exact | P partielle [IC95] | R partiel [IC95] | F2 [IC95] |
| --- | --- | --- | --- | --- | --- |
| enhanced | 0.9684 | 0.9892 | 0.9789 [0.9560, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.9957 [0.9909, 1.0000] |
| standard | 0.9789 | 1.0000 | 0.9789 [0.9560, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.9957 [0.9909, 1.0000] |

| Profil | Couverts | Couverture [IC95] | Caractères exposés | Fuite [IC95] | Entités partielles/entières exposées | Documents exposés | Surmasquage caractères | Taux [IC95] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enhanced | 93/93 | 1.0000 [1.0000, 1.0000] | 0/1889 | 0.0000 [0.0000, 0.0000] | 0/0 | 0 | 25/11645 | 0.0021 [0.0004, 0.0041] |
| standard | 93/93 | 1.0000 [1.0000, 1.0000] | 0/1889 | 0.0000 [0.0000, 0.0000] | 0/0 | 0 | 20/11645 | 0.0017 [0.0000, 0.0037] |

CUSTOM/LOCATION, hors comparaison principale :

| Profil | Couverts | Caractères exposés | Entités partielles exposées | Entités entièrement exposées |
| --- | --- | --- | --- | --- |
| enhanced | 2/6 | 40 | 0 | 4 |
| standard | 2/6 | 40 | 0 | 4 |

Alertes finales sans masquage :

| Profil | Alertes | Sur références visibles | Ailleurs | Entités exposées alertées |
| --- | --- | --- | --- | --- |
| enhanced | 1 | 0 | 1 | 0/0 |
| standard | 0 | 0 | 0 | 0/0 |

Coûts par processus neuf, CPU, OMP/MKL demandés à deux threads, RSS échantillonné toutes les 20 ms.
Les imports métier sont inclus au chargement ; démarrage de Python et imports du harnais exclus.

| Profil | Chargement s | Inférence s | Substitution s | Contrôle s | Pic RSS Mio | Appels principaux |
| --- | --- | --- | --- | --- | --- | --- |
| enhanced | 12.79 | 5.32 | 0.01 | 8.96 | 1139.3 | 6 |
| standard | 12.01 | 0.93 | 0.01 | 1.13 | 738.5 | 6 |

[Rapport complet](test/robustness.md), [JSON](test/robustness.json).

## Challenge historique FR, série G8 unique

Non disponible : essai unique en échec (code 2).
Aucun rapport courant exploitable ; aucune nouvelle détection autorisée.
Agrégats G7 archivés ; aucun chiffre courant ni intervalle inventé.

## Comparaison historique

[Test](historical_comparison/test_comparison.md). Challenge courant non disponible : essai en échec.
Seuls Standard et Enhanced sont remesurés, comme préenregistré ; les ablations G7 restent archivées.
Aucun intervalle apparié n'est inventé entre les séries historiques. Les métriques nouvelles absentes de G7 sont non disponibles.

## Contrôles et limites

1680 tests passent avant la mesure réservée ; modèles et environnements inchangés, pip check conforme.
C3 suit A4 sans modification de logique ; seize sources et les plans ont des empreintes vérifiées.
Les parcours UI FR/EN et documents FR/EN, payload exact, révocations et absence de table envoyée sont testés.
Le repli de langue hors session est limité à AppTest pour tester Review en français ; le code de production reste intact.
Les sondes Enhanced FR/EN passent en processus neufs, caches vides, réseau et écritures des documents bloqués.
L'audit des littéraux conserve sa classification préalable et ses comptes bruts ; des recouvrements génériques ne prouvent pas une copie spécifique.
Les corpus sont petits, fictifs et liés au style d'un seul auteur/famille de modèle. Aucun score ne garantit anonymat ou fuite nulle.
Les coûts sont indicatifs sur cette machine. Les détails de versions et de poids sont dans provenance.json et les métadonnées de chaque profil.
