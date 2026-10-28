# Protocole de mesure après G7 (B1)

Ce protocole fixe, avant toute validation aveugle, ce qui sera mesuré, comment, contre quoi et dans quel ordre. Il s'applique aux documents français et anglais. Il complète D-12, D-13, D-S45-1 et D-G7-1 sans les modifier : les métriques et résultats historiques restent intégralement valables et comparables.

## 1. Métriques

### 1.1 Métriques historiques, inchangées

- Appariement exact ou partiel, un à un, de même type ; le rappel partiel accepte tout recouvrement positif de même type. Une étiquette erronée ne devient jamais un vrai positif.
- `exposed_entities` désigne une entité entièrement découverte. La fuite historique (`leak_rate`) compte les caractères de référence non couverts par une prédiction d'un des onze types évalués.
- Onze types évalués ; LOCATION et CUSTOM exclus. Seuil 0,30 pour les mesures FR de G7.
- Les résultats de G7 ne sont ni recalculés ni remplacés. Aucun intervalle historique n'est reconstruit depuis des agrégats ; une métrique nouvelle absente d'un ancien rapport est notée non disponible.

### 1.2 Couverture complète (nouvelle)

Calcul pur de `src/huisclos/evaluation/coverage.py`. Les caractères masqués sont l'union des substitutions effectives, quel que soit le type prédit : un masquage LOCATION ou une mauvaise étiquette protège les caractères, sans créer de vrai positif historique.

| Mesure | Définition |
| --- | --- |
| entities_fully_covered | références dont tous les caractères sont masqués ; un seul caractère visible l'empêche |
| entities_partially_exposed | références dont une partie seulement reste visible (prénom masqué, nom visible) |
| entities_fully_exposed | références sans aucun caractère masqué |
| entities_with_any_exposure | somme des deux précédentes |
| full_coverage_rate | entités entièrement couvertes / entités de référence |
| leaked_characters et leaked_character_rate | caractères de référence visibles, puis rapportés aux caractères de référence |
| documents_with_any_exposure | documents avec au moins un caractère de référence visible |
| non_sensitive_characters_masked et non_sensitive_masked_rate | caractères masqués hors de toute annotation, puis rapportés aux caractères hors annotation (surmasquage) |

- Dénominateurs : les onze types historiques forment le périmètre de comparaison (`evaluated`). CUSTOM et LOCATION forment un périmètre séparé (`custom_location`), publié à part. Les caractères non sensibles sont ceux hors de toute annotation, quel que soit son type. Aucun périmètre ne change selon le profil mesuré.
- Ratio sans dénominateur : `null` dans le JSON, `n/a` dans la synthèse, pour "not applicable". Ce n'est jamais une garantie de fuite nulle.
- Les ratios d'un ensemble de documents se recalculent sur la somme des comptes, jamais par moyenne de ratios.

## 2. Stades mesurés

1. `detection` : propositions de `detect()`, une seule détection par document et par profil.
2. `pseudonymization` : pseudonymisation automatique de toutes les propositions ; les passages réellement remplacés sont replacés dans le texte d'origine.
3. `final_check` : alertes du contrôle final sur le texte pseudonymisé, au seuil courant moins 0,20, comme dans l'interface. Une alerte ne masque rien : la fuite de ce stade est celle du stade 2. Les alertes sont reliées aux caractères sensibles visibles (`exposed_entities_alerted`) et aux autres passages (`alerts_elsewhere`).

Aucun stade ne simule un humain qui connaîtrait les annotations : pas d'acceptation sélective, pas de "Mask everywhere" automatique.

## 3. Pilote

Commande, avec l'interpréteur du projet (PY) :

```
PY scripts/evaluate_robustness.py --corpus <jsonl> --dataset-id <id> --plan <plan.json> --out <dossier neuf> [--mode dev|gate]
```

- `--corpus`, `--dataset-id`, `--plan` et `--out` sont obligatoires ; aucun split n'est choisi par défaut. Le dossier de sortie ne doit pas contenir de rapport : une mesure n'en écrase jamais une autre.
- Plan figé (JSON) : `document_language` (fr ou en), `profiles` (nom vers `preset`, `threshold`, et pour une référence `checkout` et `python`), `comparisons` (paires `[candidat, référence]`). Toute clé inconnue, langue absente, seuil hors [0, 1] ou paire invalide est refusée. Le SHA-256 du plan, le plan entier, le SHA-256 du corpus, le commit de mesure et, par profil, le commit et la propreté du code mesuré, la configuration entière, les versions, le modèle spaCy et sa version, le nom et la révision locale de CamemBERT, les seuils et le seuil du contrôle final sont enregistrés.
- Mode `dev` (par défaut) : refuse avant lecture `test.jsonl`, `challenge.jsonl`, tout chemin qui traverse `blind_post_g7` et tout fichier identique sur le disque aux vrais corpus réservés, après résolution des chemins relatifs, liens et casse ; refuse ensuite un fichier dont les documents portent un split réservé. Les expositions détaillées sont écrites dans `coverage_exposures_dev.csv`.
- Mode `gate` : réservé aux gates autorisées. Chaque profil tourne dans un processus séparé ; les textes passent par un tube ; aucun texte, valeur, position ou identifiant de document n'est écrit ni affiché ; la sortie d'erreur d'un processus en échec n'est pas recopiée.
- Référence d'un autre commit : `checkout` désigne un worktree détaché hors dépôt et `python` son interpréteur de référence. Le processus séparé importe le code de ce checkout et ne renvoie que positions et types ; la mesure nouvelle s'applique à ces prédictions sans changer leur code ni refaire de détection. Un code sans contrôle final est publié `available: false`.
- Sorties : `robustness.json` et `robustness.md`, rapport séparé de `results.json`. Ses sections `metrics_by_type`, `bootstrap_method`, `bootstrap_intervals` et `selected_threshold` (si tous les profils partagent le seuil) suivent le schéma de `results.json` ; la clé `config` y porte le nom du profil.

## 4. Incertitude

- Bootstrap par document, 2 000 tirages, `random.Random(45)`, percentiles 2,5 et 97,5 interpolés (D-S45-1). Les mêmes tirages servent à tous les profils d'un rapport : `draw_indices` reproduit exactement la suite de `bootstrap_intervals`, et les intervalles historiques du pilote sont identiques à ceux de `run_evaluation.py` (vérifié bit à bit sur dev contre G7).
- Couverture : un tirage sans dénominateur est écarté et compté (`undefined_draws`), jamais remplacé par zéro.
- Différences appariées : candidat moins référence, tirage par tirage, sur les mêmes documents, pour précision et rappel partiels (stade 1) et pour les trois ratios de couverture (stades 1 et 2). Une différence n'est dite significative au niveau de 95 % que si son intervalle apparié exclut zéro (`excludes_zero`). Aucune conclusion de significativité depuis les seuls intervalles marginaux, ni entre rapports distincts.
- Ces intervalles restent conditionnels au corpus, à ses auteurs et au seuil figé.

## 5. Comparateurs

Chaque résultat nomme son comparateur. Comparaisons prévues, dans une même langue et sur les mêmes documents :

| Candidat | Référence | Usage |
| --- | --- | --- |
| Standard actuel | G7 `hybrid`, seuil 0,30 | correction FR du profil par défaut |
| Enhanced actuel | G7 `hybrid_camembert`, seuil 0,30 | correction FR du profil renforcé |
| Enhanced actuel | Standard actuel | recommander ou non l'option, FR et EN séparément |
| nouveau backend (A3/A4) | meilleur profil déjà retenu, sans ce backend | apport marginal ; jamais seulement contre le plus faible de G7 |

- Référence G7 : worktree détaché du commit 422a2cd (code de détection identique à b86a977), hors dépôt, avec l'environnement de référence G7 préservé ; profil `hybrid` ou `hybrid_camembert` au seuil 0,30.
- Le code de G7 ne fournit aucun profil anglais : une demande EN contre G7 échoue clairement. Cette absence est publiée ; aucun chiffre G7 ne valide l'anglais.

## 6. Critère de recommandation

Critère d'ingénierie, pas un seuil juridique, calculé par le pilote (`engineering_criteria`) sur les estimations ponctuelles, après pseudonymisation, contre le comparateur nommé :

1. fuite (`leaked_character_rate`) strictement plus faible ;
2. couverture complète (`full_coverage_rate`) strictement plus élevée ;
3. précision partielle micro au moins égale à celle de la référence moins deux points ;
4. surmasquage (`non_sensitive_masked_rate`) au plus égal à celui de la référence plus un point.

Une égalité de fuite ou de couverture ne suffit pas : sans gain mesuré, l'option plus lourde n'est pas recommandée. Masquer tout le texte annulerait la fuite mais ferait échouer la condition 4 ; ce n'est jamais une solution. Les différences appariées et leurs intervalles accompagnent chaque recommandation.

## 7. Séquence et gel

1. Réglages : profils, seuils, langue, modèles et marges viennent du dev et de fixtures nouvelles seulement. Le challenge C2 a servi à choisir une stratégie : il n'en est plus une validation fraîche.
2. Seuils par langue : FR, règle D-13 sur le dev FR. EN, même règle sur le dev EN de B2 : un plan dev peut déclarer un profil par seuil candidat (0,30 à 0,95 par pas de 0,05), puis retenir le F2 partiel micro maximal, le plus bas à égalité. Aucun seuil EN n'est déduit d'un résultat FR.
3. Gel avant toute mesure réservée : plans JSON finaux (profils, seuils, langue, modèles, comparateurs, marges, métriques) et leurs SHA-256 consignés par G8 avant le premier chiffre aveugle.
4. Mesure dev en mode dev, puis vérification que les seuils mesurés égalent ceux des plans ; tout écart arrête la gate avant la mesure réservée.
5. Ne pas utiliser `run_evaluation.py --split all` lorsqu'une vérification intermédiaire des seuils est exigée : cette commande choisit le seuil sur dev puis enchaîne immédiatement test. Utiliser `--split dev`, vérifier, puis `--split test`, puis `--split challenge`.
6. Nouveau lot C3 FR/EN rédigé à l'aveugle après le gel A4, dans `corpus/blind_post_g7/`. Mesure unique par document, profil et code, en mode gate, avec les plans gelés. Aucun nouveau choix de seuil ni correction après un chiffre aveugle.
7. Résultats, seuils et intervalles séparés par langue. Aucune moyenne bilingue ne doit cacher une régression anglaise.

## 8. Contrat de langue du document (A2)

- `DetectionConfig.document_language` vaut `fr` ou `en`, défaut `fr`. Il est indépendant de la langue de l'interface et du style des jetons (`TokenStyle.language`).
- Le pilote fixe ce champ depuis le plan avec `dataclasses.replace`. Tant que le champ n'existe pas, une demande `en` échoue avec un message clair au lieu de simuler un support anglais avec le moteur français ; une demande `fr` est mesurée et marquée `document_language_field: false`.
- La langue d'un jeu est portée par le plan, pas par les enregistrements JSONL : `load_corpus` refuse aujourd'hui toute clé inconnue.

## 9. Limites

- Corpus fictifs, petits, écrits par peu d'auteurs ; les intervalles n'en mesurent pas le biais.
- La couverture compte des caractères : elle ne juge pas une ré-identification par le contexte (fonction unique, lieu rare). Un passage sensible non annoté compte comme surmasquage.
- CUSTOM reste hors de la comparaison principale : son périmètre séparé est publié, sans critère.
- Les alertes du contrôle final aident l'humain ; elles ne réduisent aucune fuite tant qu'il ne masque pas.

## 10. Point de départ dev (B1)

Mesure B1 du 28 octobre 2026 en mode dev, hors dépôt : `corpus/dev.jsonl`, 20 documents, 311 entités évaluées, seuil 0,30, code de détection de G7.

| Profil | Précision | Rappel | Couverture complète | Fuite | Surmasquage | Alertes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Standard (`hybrid`) | 0.9904 | 1.0000 | 311/311 | 0 caractère | 7 caractères (0.0002) | 0 |
| Enhanced (`hybrid_camembert`) | 0.9904 | 1.0000 | 311/311 | 0 caractère | 7 caractères (0.0002) | 2, hors références |

- Métriques et intervalles historiques identiques bit à bit à G7 dev ; profil Standard rejoué en processus séparé identique (différences appariées nulles).
- Périmètre séparé : 50 annotations CUSTOM, 46 entièrement couvertes, 4 entièrement exposées (48 caractères).
- Critère Enhanced contre Standard non rempli : aucun gain mesurable sur ce dev déjà saturé. Ce n'est pas une conclusion sur des documents nouveaux.
