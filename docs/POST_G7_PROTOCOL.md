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
- Mise en oeuvre A2 (D-AF-A2-1) : le champ existe ; `replace(config, document_language="en")` charge en_core_web_sm 3.8.0, enregistré par le pilote comme modèle spaCy du profil (`document_language_field: true`). Le code de G7 et celui du départ de A2 refusent toujours l'anglais : aucune référence anglaise antérieure n'existe. CamemBERT est refusé pour un document anglais. Les préréglages gardent leurs noms et leur langue française par défaut.

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

## 11. Mesure avant/après A2

Mesure AF-A2 du 28 octobre 2026 en mode dev, hors dépôt, baseline_python, seuil 0,30. Référence "avant" : worktree détaché au SHA de départ ccc8b81 (A1 et B1), en processus séparé ; "après" : arbre de travail du commit A2. Les fixtures viennent de tests/fixtures/post_g7/, annotées avant les règles, converties en JSONL par le parseur du corpus.

| Jeu | Profil | Précision partielle | Rappel partiel | Rappel exact | Couverture complète | Fuite | Surmasquage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dev FR, 20 documents | Standard avant | 0.9904 | 1.0000 | 311/311 | 311/311 | 0 caractère | 7 caractères |
| dev FR, 20 documents | Standard après | 0.9904 | 1.0000 | 311/311 | 311/311 | 0 caractère | 7 caractères |
| fixtures FR, 3 documents | Standard avant | 0.8421 | 0.8571 | 40/56 | 43/56 | 234/1128 | 94 caractères (0.0642) |
| fixtures FR, 3 documents | Standard après | 0.9825 | 1.0000 | 56/56 | 56/56 | 0/1128 | 17 caractères (0.0116) |
| fixtures EN, 2 documents | Standard après | 0.9394 | 0.9394 | 30/33 | 31/33 | 17/615 | 5 caractères (0.0049) |

- Enhanced égale Standard sur chaque ligne française, avant comme après ; le dev FR reste saturé (différences appariées nulles).
- Fuite par type, fixtures FR avant : adresses 149, personnes 37, procédure 30, naissance 18 caractères ; après : zéro pour chaque type.
- Différences appariées sur les fixtures FR (après moins avant) : couverture complète +0,2321 [0,1111 ; 0,4286], fuite -0,2074 [-0,3529 ; -0,1729], intervalles qui excluent zéro ; précision +0,1404 et rappel +0,1429, intervalles qui touchent zéro. Critère d'ingénierie rempli pour Standard et Enhanced. Trois documents écrits dans la même session que les règles : ce n'est pas une mesure de généralisation.
- Anglais : aucune référence antérieure. Restent une signature sans civilité manquée par en_core_web_sm (16 caractères), la parenthèse d'un indicatif rognée par la fusion (1 caractère) et une personne lue comme société, masquée. Ces chiffres ne valident pas le support anglais : le dev EN de B2 puis C3 en décideront.

## 12. Gel A4 avant C3

Cette section fixe la configuration finale après intégration réelle, sans changer les métriques,
les marges ni les résultats historiques. Aucune mesure réservée n'a été effectuée en A4.
Les profils après G7 restent expérimentaux avant le verdict bilingue de G8.

| Langue du document | Standard | Enhanced local | Seuil principal | Seuil propre au renfort |
| --- | --- | --- | ---: | ---: |
| fr | règles, checksums, fr_core_news_md 3.8.0, propagation | Standard + CamemBERT existant | 0,30 | probabilités CamemBERT soumises au seuil principal |
| en | règles, checksums, en_core_web_sm 3.8.0, propagation | Standard + GLiNER multi PII v1 | 0,30 | GLiNER 0,70 |

- Standard reste le défaut ; Enhanced est facultatif, local seulement, refusé en démonstration publique. Aucun modèle français ne sert à valider l'anglais.
- Anonym-IA et l'union Anonym-IA/GLiNER ne sont pas retenus en FR : aucune réduction de fuite ni hausse de couverture sur dev contre Standard ou CamemBERT. Conformément à A4, le CamemBERT existant est conservé sans lui attribuer de nouveau gain sur ce dev saturé. Pas de troisième modèle.
- GLiNER EN est retenu comme option : sur le pipeline intégré, couverture 124/136 vers 126/136, fuite 105/2553 vers 63/2553, surmasquage 48 vers 48 caractères ; précision partielle 0,9313 vers 0,9323. Le critère ponctuel B1 est rempli ; les intervalles appariés incluent zéro. Le coût et les 28 alertes hors références au contrôle final sont publiés dans LOCAL_MODELS.md, sans les compter comme des protections.
- Le seuil EN 0,30 est confirmé par le balayage dev B3 rejoué sur le code intégré, F2 partiel maximal puis minimum à égalité. Le seuil GLiNER 0,70 est confirmé par sa grille 0,30/0,50/0,70 ; aucun choix après un résultat aveugle ne sera permis.
- Labels GLiNER figés : `person`, `organization`, `address`, `email`, `phone number`, `date of birth`, vers les six types existants. Pas de ville seule ni de date ordinaire. Source `ner_gliner`, positions absolues validées, projection canonique puis fusion et propagation communes ; aucun champ de la table JSON n'est changé.
- Fenêtres : CamemBERT 512 jetons avec spéciaux ; GLiNER 256 avec spéciaux, capacité interne 384 mots et largeur 12 mots ; recouvrement 64 pour les deux. Refus de troncature. Les composants d'adresse Anonym-IA ne sont pas intégrés et ne fondent aucune revendication de couverture.
- Contrôle final : seuil principal abaissé à 0,10, GLiNER maintenu à 0,70. Toute modification de ces paramètres, des versions, du profil ou des fichiers invalide les résultats et autorisations de l'interface. Une alerte ne masque rien.

Pile locale validée : Python 3.12.10, Transformers 5.16.1, huggingface-hub 1.9.2, GLiNER 0.2.29,
torch 2.14.1+cpu, tokenizers 0.23.3, sentencepiece 0.2.2, spaCy 3.8.18, Presidio analyzer et
anonymizer 2.2.366. Les deux modèles spaCy sont en 3.8.0. Le verrou complet et les instructions
de repli figurent dans requirements-enhanced-lock.txt et LOCAL_MODELS.md ; les paquets lourds
restent hors de requirements.txt. Les snapshots et la référence G7 A1 sont préservés.

Révisions immuables :

| Modèle | Révision |
| --- | --- |
| Jean-Baptiste/camembert-ner | ef35fe7767c1dad71f5c853838cdd80d0b3441ed |
| urchade/gliner_multi_pii-v1 | 1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d |
| microsoft/mdeberta-v3-base, configuration et tokenizer seulement | a0484667b22365f84929a935b5e50a51f71f159d |

Plans finaux hors dépôt, dans `pilotage/post_g7_assets/benchmarks/A4/`, en UTF-8 LF :

- `frozen_fr.json`, SHA-256 `7fd554ae608eb5e3231a9663ee7fe8f6b3303bfe42adb5e4559d2bc43ffbb453` ; Standard actuel contre G7 hybrid, Enhanced actuel contre G7 hybrid_camembert, puis Enhanced contre Standard. Référence autonome : checkout 422a2cd et baseline_python A1, seuil 0,30.
- `frozen_en.json`, SHA-256 `ce2af6dec9f395b7c26ad5e924ba5b4762451d939a2aa749197585301708fdd1` ; Enhanced (`hybrid_gliner`) contre Standard (`hybrid`), langue en. Aucune référence anglaise G7 inventée.
- `retained-runtime-final.json` consigne les labels, seuils, versions, révisions et empreintes de tous les fichiers des modèles retenus, l'identité du paquet et le verrou. Il complète les plans B1 sans leur ajouter de clé non admise.
- Le préenregistrement des comparaisons intégrées est `validation_v3/integrated_registration.json`, SHA-256 `074f1f89277cb9e945a64cc6172aae2de780522b82ef7507d97bfc0a968b317f`. Les deux répétitions réelles FR et EN sont identiques pour métriques, couverture, contrôle et intervalles. Les plans finaux ont les mêmes paramètres que ces plans de mesure ; seules les fins de ligne sont normalisées LF.
- La grille dev rejouée est archivée dans `matrix/`, plan SHA-256 `ca3e3482f78d80475d0e17e991f62d19c9176943f3d013d9b2982c70e9329d1b`. Les adaptateurs expérimentaux Anonym-IA/GLiNER servent à cette grille, pas au runtime. Les rapports intégrés utilisent les vrais backends de production, sans injection de candidats ni simulation de revue.

Le critère G8 reste celui de la section 6 : fuite strictement plus faible, couverture entière
strictement plus élevée, précision partielle au moins référence moins 0,02 et surmasquage au plus
référence plus 0,01. Bootstrap apparié de 2000 tirages, graine 45 ; publication séparée FR/EN,
CUSTOM/LOCATION à part, pas de moyenne bilingue ni de significativité déduite d'intervalles
marginaux. Le coût du contrôle final est publié séparément.

G8 devra vérifier les empreintes et l'égalité des seuils avant la première mesure réservée, puis
mesurer les profils prévus, sans les profils FR GLiNER expérimentaux rejetés. La langue du document
est fixée par le plan, indépendamment de l'interface. Déclarer HUISCLOS_MODELS_DIR comme décrit
dans LOCAL_MODELS.md avant les mesures Enhanced ; un paquet absent interrompt la mesure.
Les rapports B1 restent compatibles avec les champs historiques de results.json.

Pour reproduire les mesures CPU, fixer OMP_NUM_THREADS=2, MKL_NUM_THREADS=2 et
TOKENIZERS_PARALLELISM=false avant le lancement de Python ; les sondes confirment deux threads
Torch. Le runtime reste hors ligne (HF_HUB_OFFLINE=1 et TRANSFORMERS_OFFLINE=1). Ces paramètres
et le paquet explicite sont conservés pour G8, sans nouveau réglage après un résultat aveugle.

Le commit final A4 et son empreinte de logique seront enregistrés par `post_g7.py finish A4`.
C3 rédigera ensuite le nouveau lot FR/EN à l'aveugle, sans lire la logique ni les résultats ; seul
G8 mesurera les corpus réservés. Aucune logique ne doit changer pendant A5/C3 et aucun seuil,
label, modèle, comparateur ou marge ne doit être rechoisi après un résultat aveugle.

Le runtime final A4.2 distingue la fenêtre GLiNER de 256 jetons de son encodeur natif de
512 jetons et vérifie le prompt entier avant inférence. Les premiers essais avec une limite
interne de 256 sont conservés mais remplacés par validation_v3 et matrix_v2. La preuve
fictive de troncature et son correctif figurent dans truncation-proof.json. Le manifeste
retained-runtime-final.json porte le SHA-256
`3e3e8fefcbe59f057e199f558dd1a634d6ebf2c103f35b9df524ee21ae5c5416` ; le rapport de
provenance integration-summary.json porte
`8f2bcf99aac29f0d6904b7806168bab564c948ea862244fc0214bb383e67f5ff`.

## 13. Constat G8 du 28 octobre 2026

Le protocole et les seuils ci-dessus restent figés. G8 conclut NO-GO global : Enhanced EN
réduit les fuites mais dépasse la perte de précision autorisée ; la série challenge
historique échoue sans rapport exploitable et n'est pas relancée. Les contrôles techniques
et les gains FR mesurés sont conservés, sans annoncer une validation bilingue complète.

Le quatrième test historique est mesuré une fois, après vérification du dev : 93/93 entités
couvertes et zéro caractère exposé dans les onze types, dans les deux profils actuels.
Les deux lots aveugles neufs sont mesurés une fois par profil/code ; leurs langues restent
séparées. Aucun G7 anglais n'est inventé. Les alertes ne réduisent aucune fuite.

Le harnais G8 complète B1 avec le contrôle réel du contexte source et les coûts par
processus ; les prédictions servent à toutes les métriques avant d'être oubliées. Les
mesures dev du harnais utilisent le mode gate sur le seul split dev pour isoler les
profils et supprimer les détails. Le CLI --split dev et la grille EN sont vérifiés avant
registration.json et avant tout chiffre réservé. Pour les splits historiques, run_gate.py
exige --split test puis --split challenge et dérive les rapports compatibles depuis les
mêmes prédictions : aucun deuxième passage par le CLI historique, aucun --split all.

G8-01 reproduit sur une panne injectée la perte des prédictions quand le contrôle final
échoue ; xfail strict, sans lien établi avec l'échec challenge. La cause et la sous-étape
de cet échec réservé restent inconnues, sans journal sensible conservé. Aucune nouvelle
détection réservée n'est autorisée par ce constat ; un relais explicite devra en fixer
les limites. [D-G8-1](DECISIONS.md#d-g8-1-gate-bilingue-et-protection-complete) et
[rapport complet](../results/gate8/report.md) conservent méthodes, intervalles et replis.

Correctif AF-FIX, après G8 et sans nouvelle mesure : une panne du contrôle final garde les
prédictions principales et rend ce contrôle indisponible pour tout le profil ; un worker en
échec cite seulement son stade et la classe d'erreur. Critères, seuils, plans et rapports
G8 restent inchangés ; les chiffres G8 décrivent le code mesuré, pas ce correctif.
[D-FIX-1](DECISIONS.md#d-fix-1-contrôle-final-indisponible-et-diagnostic-du-worker-g8).
