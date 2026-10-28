# Reserved bilingual blind corpus after G7

This directory is reserved for authoring session C3 and gate scripts, including
G8. Coding agents must not open its sources or JSONL files, inspect its errors,
or tune detection against it. Its existence is not evidence of detection quality.
The older development, test and challenge sets remain separate and unchanged.

## Frozen annotation conventions

Version: `post_g7_fr_en_1.0`. Frozen on 28 October 2026 before source authoring,
after pilot confirmation of A4 commit
`dc5b04146c9217bdd09da5064091e0cf638f5b37`.

- Each language has eight independent fictional matters: two consultations,
  two correspondence documents, two instruments/drafts and two summaries.
  Six have 250-450 words; two have 800-1,200 words. Words are nonempty
  whitespace-separated units of the final plain text, including table cells.
- Sources use the four-field header and `[[value|TYPE]]` syntax documented in
  `corpus/README.md`. The generated schema has the existing six fields; its split
  is `challenge`. Language, provenance and hashes are in the manifest.
- Annotate every sensitive occurrence, including initials, shortened surnames,
  signatures, headings and table cells. Keep titles and labels outside spans.
  Persons and private organisations are sensitive; include an attached legal
  form in an organisation span. Public institutions, courts, legislation,
  public geographical context and legal citations remain unannotated.
- An address is one span, from its street number or explicit delivery component
  through its last explicit postal component, including postcode, country and
  line breaks when present. A city alone used as public context is not an address.
- EMAIL and PHONE cover the whole contact value, including a country prefix or
  explicit extension. Email addresses use example.com or example.org only.
  BIRTH_DATE covers dates explicitly identified as birth dates; ordinary event,
  contract, hearing and payment dates are not sensitive by this convention.
- IBAN, NIR, SIREN and SIRET retain the French meanings even in English prose.
  Synthetic keys are calculated locally from this dataset's namespace and document
  ID. CASE_NUMBER covers private case references; labels such as RG, case ref or
  dossier remain outside. CUSTOM covers explicitly labelled internal identifiers.
- The twelve permitted labels are PERSON, ORGANIZATION, ADDRESS, EMAIL, PHONE,
  IBAN, NIR, SIREN, SIRET, BIRTH_DATE, CASE_NUMBER and CUSTOM. No new foreign
  identifier label is introduced. LOCATION is outside these corpus conventions,
  as in the existing source contract; no LOCATION performance can be inferred.
- No nested, empty or overlapping spans are permitted. Offsets count Python
  Unicode characters, not bytes; each entity text equals its exact source slice.
  Annotation markers are removed without normalising body whitespace.
- Public references, amounts, article numbers and ordinary dates are deliberate
  unannotated context. No real client material, previous corpus values, detector
  feedback, separate annotation LLM or performance measurement informs this lot.

## Construction and reservation

From the lane-b worktree, using the project interpreter as PY:

```text
PY scripts/build_blind_post_g7.py --self-test
PY scripts/build_blind_post_g7.py
PY scripts/build_blind_post_g7.py --check
```

The builder reads only the sixteen explicitly named new sources. It never imports
project detection code, evaluates a model, reads an older split or writes outside
this directory. `--check` compares deterministic outputs without writing;
`--self-test` uses tiny in-memory examples, never the reserved lot. Diagnostics
report counts or error categories, never corpus text or spans. The convention
file's SHA-256 is recorded with each language file's separate SHA-256, source
hashes, genres, counts, word lengths and A4 provenance in `manifest.json`.

Both final JSONL files are reserved challenge material. Old builders use their
own source directories; these nested sources must never be added to those scans.
After C3 freezes the lot, its author must not become an implementer using its
contents. Gates may read it programmatically under their explicit authorisation.
The JSONL and manifest are deterministic UTF-8 with LF line endings.

## Boundary appendix and limitations

An English document can concern French parties and French identifiers. Language
does not establish nationality or jurisdiction. English postal addresses include
the final postal component actually written, rather than stopping at the city.
A private reference is CASE_NUMBER, whereas a labelled staff or asset identifier
is CUSTOM. No SSN, UK national insurance, passport or foreign company-number
coverage is claimed. Invalid identifier samples and isolated locations are not
exhaustively represented. Standalone legal forms are ordinary prose unless
attached to a private organisation's name. A family name alone still identifies
the person when context establishes that reference.

Every matter has separate invented identities and contacts. This reduces obvious
dependencies; it does not prove statistical independence. One author and one
model family create shared stylistic and annotation dependencies. The editorial
second pass checks omissions and boundaries but cannot prove exhaustiveness.
Synthetic valid checksums do not prove that a number is unassigned in reality;
no registry or remote service is consulted. These are fictional examples only.
Pseudonymisation is not anonymisation; human review remains necessary.

The sources and generated files use CC BY 4.0, attributed to the HuisClos project.
