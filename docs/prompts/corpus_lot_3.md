# C1 : corpus fictif, lot 3 et démonstration

Session de rédaction sans réseau, piste B. L'exception C1 d'AGENTS.md autorise
la rédaction des sources test sans modification du code. Après cette session,
ces sources et leur sortie JSONL restent réservées aux scripts d'évaluation.

## Consignes de rédaction

Tu es juriste en droit social et en droit des affaires français. Tu rédiges des
documents entièrement fictifs pour tester un outil de pseudonymisation. Invente
les personnes, sociétés, adresses et affaires, sans reprendre de personnalité,
d'entreprise connue ni de dossier réel.

Écris directement chaque fichier en UTF-8 et LF, sans bloc de code. L'en-tête
délimité par deux lignes `---` contient exactement les champs `id`, `doc_type`,
`split`, `title`, un par ligne. Le corps suit la fermeture de cet en-tête.

1. Annote toute donnée identifiante par `[[valeur|TYPE]]` avec PERSON,
   ORGANIZATION, ADDRESS, EMAIL, PHONE, IBAN, NIR, SIREN, SIRET, BIRTH_DATE,
   CASE_NUMBER ou CUSTOM. Répète l'annotation à chaque occurrence.
2. Civilités et libellés restent hors des spans, notamment M., née le, RG n°,
   SIRET et matricule n°. Inclus une forme juridique accolée à la société.
3. N'invente jamais de numéro à clé de contrôle. Les marqueurs autorisés sont
   `{{NIR}}`, `{{NIR_2A}}` pour une naissance corse, `{{NIR_BADKEY}}`,
   `{{IBAN}}`, `{{IBAN_BADKEY}}`, `{{SIREN#1}}`, `{{SIRET#1}}`,
   `{{SIREN_BADKEY}}`, `{{PHONE_MOBILE}}` et `{{PHONE_FIXE}}`.
   Annote ces marqueurs. Les indices SIREN/SIRET identiques désignent la même
   société ; #2 désigne la deuxième. BADKEY représente une clé mal recopiée.
   Le marqueur piège `{{DIGITS9}}`, numéro de commande ou montant, reste hors
   annotation.
4. Annote les formes courtes, les noms seuls et les noms en majuscules, même
   lorsqu'une forme longue a déjà été annotée.
5. Ne masque pas les juridictions, institutions publiques, références légales,
   montants, références de jurisprudence publiée ou dates hors naissance.
   Conseil de prud'hommes de Nanterre, Cour d'appel de Versailles, URSSAF,
   France Travail et inspection du travail restent en clair.
6. Une adresse constitue un seul span du numéro à la ville, saut de ligne
   compris. Les courriels utilisent uniquement example.com ou example.org.
7. Un identifiant interne sans format standard, tel un badge ou matricule,
   relève de CUSTOM.

Chaque document comprend 250 à 500 mots, 12 à 30 annotations, une personne
présentée sous deux formes au moins et au moins deux pièges. Choix possibles :
homonymes, prénoms Rose, Pierre, Claire ou Constant, noms Petit, Blanc ou Lebrun,
société contenant un nom de personne, nom seul, majuscules, adresse multiligne,
clé fausse, juridiction et article en clair, date d'audience. Style juridique
français réaliste et sobre, références exactes, aucun espace réservé comme [Nom].

## Liste du lot

| Fichier | Split | Document |
| --- | --- | --- |
| corpus/source/doc_13.md | test | Licenciement pour motif économique |
| corpus/source/doc_14.md | test | Conclusions prud'homales de l'employeur |
| corpus/source/doc_15.md | test | Courriel client |
| corpus/source/doc_16.md | test | Extrait de bail commercial |
| corpus/source/doc_17.md | test | Compte rendu d'entretien RH |
| corpus/source/doc_18.md | test | Procès-verbal d'assemblée de SARL |
| corpus/source/demo_01.md | demo | Note de dossier, doc_type note_dossier |

## Exigences de la démonstration

Rédiger environ 300 mots sous la forme d'une note d'avocat préparant la
contestation d'un licenciement pour faute grave. Citer le client sous trois
formes : prénom et NOM, civilité et nom, nom seul. Inclure sa naissance,
`{{NIR}}`, adresse sur deux lignes, `{{PHONE_MOBILE}}`, courriel et matricule
n° 4471-B, avec la valeur du matricule annotée CUSTOM et son libellé en clair.
Inclure l'employeur avec sa forme juridique, `{{SIREN#1}}`, `{{SIRET#1}}`, son
gérant nommé et un collègue témoin nommé. Mentionner le RG devant le Conseil de
prud'hommes de Nanterre, l'article L. 1232-6 du Code du travail et la date de
l'entretien préalable en clair. Ajouter `{{IBAN}}` pour une éventuelle indemnité.

## Relecture et construction

Relire toutes les occurrences et limites d'annotation, les en-têtes, marqueurs,
volumes et pièges. Lancer `PY scripts/build_corpus.py --check`, corriger dans la
limite de trois cycles et signaler tout retrait. Construire par
`PY scripts/build_corpus.py`, puis `PY scripts/build_corpus.py --export-demo`.
Vérifier dans corpus/stats.md les comptes 12 dev, 6 test, 1 demo. Exécuter pytest,
ruff et le contrôle de style, mettre à jour PROGRESS et PROMPTS, puis créer le
commit C1. Aucun extrait test ne figure dans le compte rendu ; aucun code de
src/, app/, scripts/ ou tests/ n'est modifié.
