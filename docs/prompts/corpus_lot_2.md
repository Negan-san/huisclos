# C1 : corpus fictif, lot 2

Session de rédaction sans réseau, piste B. Ces consignes sont conservées pour
documenter la génération du corpus, indépendamment des règles de détection.

## Consignes de rédaction

Tu es juriste en droit social et en droit des affaires français. Tu rédiges des
documents entièrement fictifs destinés à tester un outil de pseudonymisation.
Aucune personne, société, adresse ou affaire réelle : invente tout et évite les
noms de personnalités ou d'entreprises connues. Aucun exemple issu d'un dossier
réel ne doit être utilisé.

Écris chaque document directement dans son fichier UTF-8, avec fins de ligne LF,
sans bloc de code. L'en-tête commence par `---`, puis comporte une ligne pour
chacun des champs `id`, `doc_type`, `split`, `title`, et se termine par `---`.
Le corps suit immédiatement. Le titre est court ; le split est `dev` pour ce lot.

1. Entoure chaque donnée identifiante par `[[valeur|TYPE]]`. Types autorisés :
   PERSON, ORGANIZATION, ADDRESS, EMAIL, PHONE, IBAN, NIR, SIREN, SIRET,
   BIRTH_DATE, CASE_NUMBER, CUSTOM.
2. Laisse hors du span les civilités et libellés : M., née le, RG n°, SIRET.
   Inclus la forme juridique accolée dans le span d'une société.
3. N'invente aucun numéro à clé de contrôle. Utilise les marqueurs `{{NIR}}`,
   `{{NIR_2A}}`, `{{NIR_BADKEY}}`, `{{IBAN}}`, `{{IBAN_BADKEY}}`,
   `{{SIREN#1}}`, `{{SIRET#1}}`, `{{SIREN_BADKEY}}`, `{{PHONE_MOBILE}}`
   ou `{{PHONE_FIXE}}`, et annote-les selon leur type. Un même indice relie
   SIREN et SIRET d'une société ; utilise #2 pour une deuxième société.
   `{{NIR_2A}}` concerne une personne née en Corse ; BADKEY signale une clé
   erronée. Le piège `{{DIGITS9}}` reste toujours hors annotation : il représente
   un numéro de commande ou un montant, jamais un identifiant à détecter.
4. Annote chaque occurrence, y compris prénom et NOM, nom après civilité,
   nom seul et forme entièrement en majuscules.
5. N'annote jamais les juridictions, institutions publiques, textes et articles
   de loi, dates autres que de naissance, montants ou jurisprudences publiées.
   Conseil de prud'hommes de Nanterre, Cour d'appel de Versailles, URSSAF,
   France Travail et inspection du travail restent en clair.
6. Annote une adresse en un seul span, du numéro à la ville, y compris un
   éventuel saut de ligne. Utilise uniquement example.com ou example.org pour
   les adresses électroniques.
7. Annote CUSTOM les identifiants internes sans format standard, comme un
   matricule de salarié ou un numéro de badge.

Chaque document comprend 250 à 500 mots et 12 à 30 annotations. Une personne
apparaît sous au moins deux formes. Prévoir au moins deux pièges : homonymes,
prénom courant comme Rose, Pierre, Claire ou Constant, nom comme Petit ou Blanc,
société contenant un nom de personne, nom seul, majuscules, adresse sur deux
lignes, clé fausse, juridiction et article de loi en clair, date d'audience.
Le style juridique français reste professionnel et sobre, avec des références
exactes et sans espace réservé comme [Nom].

## Liste du lot

| Fichier | Split | Document |
| --- | --- | --- |
| corpus/source/doc_07.md | dev | Procès-verbal d'assemblée de SAS |
| corpus/source/doc_08.md | dev | Attestation de témoin |
| corpus/source/doc_09.md | dev | Extrait de contrat de travail |
| corpus/source/doc_10.md | dev | Requête au conseil de prud'hommes |
| corpus/source/doc_11.md | dev | Courriel RH sur une rupture conventionnelle |
| corpus/source/doc_12.md | dev | Mise en demeure pour facture impayée entre sociétés |

## Relecture et construction

Vérifier toutes les occurrences, les limites des spans, les domaines réservés,
les marqueurs, les deux pièges, les volumes et les quatre champs d'en-tête.
Ne corriger les sources du lot 1 que pour un balisage signalé par `--check`.
Exécuter `PY scripts/build_corpus.py --check`, avec trois cycles de correction
au plus ; retirer et signaler une source irrécupérable. Après rédaction du lot 3
et de la démo, construire les sorties puis exporter la démo. Les comptes attendus
sont 12 dev, 6 test et 1 demo. Aucun code ni test n'est modifié pendant C1.
