# Corpus lot 4: difficult development documents

Session S14, 28 October 2026. Eight entirely fictional sources, written directly
in UTF-8 with LF endings. No test or challenge source was inspected. This lot is
development material and cannot establish performance on unseen documents.

Authoring instructions: follow MASTER_PLAN appendix A5, 250 to 500 words and
12 to 30 annotations per document. Annotate every identifying occurrence using
`[[value|TYPE]]`; keep titles and labels outside spans, attached legal forms
inside company spans, and complete addresses in one span. Use generated markers
for checksum identifiers, `{{DIGITS9}}` for unannotated accounting traps, and only
example.com or example.org for email. Telephone numbers have no checksum; the
explicit fictional formats complement generated numbers in the earlier lots.
Leave courts, institutions, articles, hearing dates, amounts and published case
references visible. Review names, repeated forms, headers and annotation bounds.

| Source | Document | Main difficulties |
| --- | --- | --- |
| doc_19 | Commissioner's report | particles, surname first, title, apostrophe, complex overseas address, passport, fiscal number, registration |
| doc_20 | Email thread with signatures | lowercase name, surname first, compound name, masked email, employee, member, client, identity card, police, old registration |
| doc_21 | Judicial judgment | initials, particles, birth date, venelle, parquet, unpublished appeal, passport, fiscal number |
| doc_22 | Insurance declaration | van der, common surnames, both vehicle formats, overseas and postal addresses, client, member, identity card |
| doc_23 | CSE meeting | MM., Dr, Pr, compound names, particles, apostrophe, employee and staff identifiers, compact phone |
| doc_24 | Power of attorney | surname first, initials, particles, common surname, passport, identity card, contract, CS, Cedex |
| doc_25 | Company services agreement | personal names inside company names, signature forms, client, police, contract, member, passport, masked email |
| doc_26 | PDF extraction | line breaks in people and addresses, line-end hyphenation, lowercase repeated forms, employee, fiscal number |

Every document also contains a field label followed by a colon, an accounting
`{{DIGITS9}}` trap, an amount and a legal article. Dates of birth use slash,
dot and written-month formats. RG, Portalis, parquet and unpublished appeal
numbers each occur in at least two documents. Each internal identifier family
occurs at least twice. BP, CS, Cedex, bis, ter, residence, building, apartment,
lieu-dit and overseas postal codes occur in at least two addresses where applicable;
the overseas range 971 to 976 is represented. No detection rule or unit-test
value may be copied from these fictional names or identifiers.

The authoring and rule work share one session, as requested. This is an explicit
methodological limit; challenge is authored independently after the rule freeze.
