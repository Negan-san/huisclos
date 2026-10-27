# Corpus generation prompt, batch 1

Verbatim prompt used to generate doc_01 to doc_06 (dev split).

```text
Tu es juriste en droit social et en droit des affaires français. Tu rédiges des documents entièrement fictifs qui serviront à tester un outil de pseudonymisation. Aucune personne, société, adresse ou affaire réelle : invente tout, et évite les noms de personnalités ou d'entreprises connues.

Pour chaque document demandé, produis un bloc de code séparé, exactement dans ce format :
---
id: doc_XX
doc_type: <type>
split: <dev, test ou demo>
title: <titre court>
---
<texte du document>

Règles d'annotation, à appliquer dans le texte :
1. Entoure chaque donnée identifiante par [[valeur|TYPE]], avec TYPE parmi PERSON, ORGANIZATION, ADDRESS, EMAIL, PHONE, IBAN, NIR, SIREN, SIRET, BIRTH_DATE, CASE_NUMBER, CUSTOM.
2. Laisse hors de l'annotation la civilité et les libellés : M. [[Karim BENALI|PERSON]] ; née le [[14 mars 1987|BIRTH_DATE]] ; RG n° [[24/01873|CASE_NUMBER]] ; SIRET [[{{SIRET#1}}|SIRET]].
3. N'invente jamais de numéro à clé de contrôle : écris un marqueur que notre script remplacera par une valeur valide et fictive : {{NIR}}, {{NIR_2A}} (personne née en Corse), {{NIR_BADKEY}} (NIR mal recopié), {{IBAN}}, {{IBAN_BADKEY}}, {{SIREN#1}} et {{SIRET#1}} (même chiffre pour une même société, #2 pour une deuxième), {{SIREN_BADKEY}}, {{PHONE_MOBILE}}, {{PHONE_FIXE}}. Annote ces marqueurs comme toute valeur. Le marqueur {{DIGITS9}} sert de piège (numéro de commande, montant) : ne l'annote jamais.
4. Annote chaque occurrence, y compris les formes courtes : [[Jean DUPONT|PERSON]], puis M. [[Dupont|PERSON]], puis [[DUPONT|PERSON]].
5. N'annote jamais : juridictions (Conseil de prud'hommes de Nanterre, Cour d'appel de Versailles), institutions publiques (URSSAF, France Travail, inspection du travail), textes et articles de loi, dates autres que de naissance, montants, références de jurisprudence publiée (Cass. soc., 12 mars 2020, n° 18-12.345).
6. Une adresse s'annote en une seule fois, du numéro de voie à la ville, saut de ligne compris.
7. Adresses e-mail en example.com ou example.org uniquement.
8. Un identifiant interne qu'aucun format standard ne reconnaît (matricule de salarié, numéro de badge) s'annote CUSTOM.

Contenu attendu pour chaque document : 250 à 500 mots ; 12 à 30 annotations ; au moins une personne citée sous deux formes ou plus ; au moins deux pièges parmi : homonymes (deux DUPONT différents), prénom qui est aussi un mot courant (Rose, Pierre, Claire, Constant), nom de famille qui est aussi un mot courant (Petit, Blanc, Lebrun), société dont le nom contient un nom de personne (Boulangerie Martin SARL), personne désignée par son seul nom, nom tout en majuscules, adresse sur deux lignes, numéro à clé fausse, juridiction et article de loi à laisser en clair, date d'audience à laisser en clair.

Ton et forme : style juridique français réaliste, formules d'usage, références de textes exactes ; aucun espace réservé du type [Nom].

Génère maintenant les documents suivants : doc_01 à doc_06, split dev : doc_01 lettre de licenciement pour faute grave ; doc_02 convocation à entretien préalable ; doc_03 conclusions prud'homales du salarié ; doc_04 mise en demeure pour loyers impayés ; doc_05 courriel client à avocat ; doc_06 extrait de bail d'habitation.
```

## Follow-up prompt

```text
1. Relis-les rapidement avec la checklist de l'annexe A5.
2. Enregistre-le en UTF-8 sous `corpus/source/doc_XX.md`.
3. Copie le prompt utilisé dans `docs/prompts/corpus_lot_1.md`.
```
