# HuisClos evaluation corpus

This fictional French legal corpus measures entity detection before local
pseudonymisation. Pseudonymisation is not anonymisation. Human review remains
necessary before sending text to a language model. Sources are authored separately
from detection rules; character positions are computed by the builder.

The collection contains 20 development documents, 6 held-out test documents
and one demonstration document. Agents must never inspect test sources or
`test.jsonl`, or tune detection using their contents. Only evaluation and corpus
construction scripts may read them.

The `challenge` split is reserved for gates in the same way as `test`. Its
`chl_*.md` sources are authored independently after S14 freezes detection rules.
Coding agents must not inspect those sources or `challenge.jsonl`, export their
errors, or tune detection against them. Corpus authoring session C2 and gate
evaluation scripts are the permitted consumers.

Development sources doc_01 to doc_12 form lots 1 and 2; doc_19 to doc_26 form
the difficult lot 4 (commissioner's report, email thread, judgment, insurance
declaration, CSE meeting, power of attorney, services agreement and PDF extraction).
Its authoring instructions and coverage are recorded in
`docs/prompts/corpus_lot_4.md`. Evaluate this lot separately from earlier material
when comparing changes. It is development material, including its difficult cases.

## Source format

Store one UTF-8 document in `corpus/source/<id>.md`:

```text
---
id: doc_01
doc_type: lettre_licenciement
split: dev
title: Fictional dismissal letter
---
Madame [[Alice BRUME|PERSON]] habite [[17 rue des Lanternes
75012 Paris|ADDRESS]]. SIREN : [[{{SIREN#1}}|SIREN]].
```

All four header fields are required, nonempty and unique. Splits are `dev`, `test`,
`challenge` or `demo`. Each document ID must be unique across all sources. Header values are
plain text, without YAML quoting. The body starts immediately after the closing
header line; its whitespace is preserved. Annotations cannot nest or overlap.
Use `[[value|TYPE]]` with exactly one separator and a nonempty value. Values may
span multiple lines. Supported types are PERSON, ORGANIZATION, ADDRESS, EMAIL,
PHONE, IBAN, NIR, SIREN, SIRET, BIRTH_DATE, CASE_NUMBER and CUSTOM.

Keep titles and labels outside spans: `Madame [[Alice BRUME|PERSON]]`,
`née le [[12/03/1980|BIRTH_DATE]]`, `RG n° [[26/12345|CASE_NUMBER]]`.
Include an attached company legal form in its span. Annotate an entire address
in one span, from street number to city, including line breaks. Annotate every
occurrence, including shortened personal names. Never annotate courts,
jurisdictions or institutions. Keep deliberate nonsensitive traps unannotated.

## Generated placeholders

| Marker | Replacement |
| --- | --- |
| `{{NIR}}` | NIR with a valid key |
| `{{NIR_2A}}` | Valid Corsican NIR with department 2A |
| `{{NIR_BADKEY}}` | NIR with an invalid key |
| `{{IBAN}}` | French IBAN with a valid key |
| `{{IBAN_BADKEY}}` | French IBAN with an invalid key |
| `{{SIREN#k}}` | Valid SIREN for positive integer k |
| `{{SIRET#k}}` | Valid SIRET beginning with the same document's SIREN k |
| `{{SIREN_BADKEY}}` | SIREN with an invalid key |
| `{{PHONE_MOBILE}}` | French mobile telephone number |
| `{{PHONE_FIXE}}` | French landline telephone number |
| `{{DIGITS9}}` | Nine compact digits with an invalid SIREN key, outside annotations |

Repeated markers share one value within a document. Numbered companies are local
to that document and work in either order. Values use `random.Random` seeded by
`zlib.crc32` of the UTF-8 document ID, then the `synthetic_ids.format_*` functions
(except the compact DIGITS9 trap). Markers are replaced before spans are computed.
The builder checks keys with the production checksum functions.

## Commands and output

Use the project's Python interpreter as `PY`, with `PYTHONUTF8=1` on Windows.
In the Windows lane-b worktree, `PY` is `../huisclos/.venv/Scripts/python.exe`.
No network or package installation is required.

```text
PY scripts/build_corpus.py --check
PY scripts/build_corpus.py --check tests/fixtures/corpus_source_example.md
PY scripts/build_corpus.py
PY scripts/build_corpus.py --export-demo
PY -m pytest -q tests/test_corpus.py
```

`--check` validates without writing anything. Building writes `corpus/dev.jsonl`,
`corpus/test.jsonl` and `corpus/stats.md`. `--export-demo` additionally writes the
single demo document to `data/samples/demo_case_fr.txt`, without annotations.
Optional `--source-dir`, `--output-dir` and `--demo-path` allow isolated builds.
Explicit source paths override `--source-dir`.

If challenge sources exist, the builder also writes `corpus/challenge.jsonl`
and includes their counts in the statistics. It creates no challenge file when
there are no challenge sources. Gate command `PY scripts/run_evaluation.py
--split challenge` requires an existing `threshold.json` in its output folder,
uses that saved development threshold without a sweep, and preserves existing
development and test result rows. No challenge error file is exported. `all`
retains its existing meaning, development followed by test only. The reserved
loader in `evaluation.run` validates challenge through an isolated adapter;
the common `load_split` API remains limited to development and test.

JSONL documents are sorted by ID, with fields `id`, `doc_type`, `split`, `title`,
`text`, `entities`. Each entity has `start`, `end`, `type`, `text`. Positions count
Python Unicode characters, with start included and end excluded. Each entity's
text must equal the corresponding document slice; overlaps are rejected.
Outputs use UTF-8 and LF line endings and are byte-identical on repeated builds.
Errors identify the source file and line. `load_corpus(path)` loads and validates
JSONL; `load_split("dev")` and `load_split("test")` load repository splits.

## Fictional data and licence

All documents, people and case details are fictional. Randomly generated
identifiers can accidentally coincide with numbers assigned in real life;
no connection with any real person or organisation is intended. A valid checksum
does not establish that an identifier exists or is assigned.

The corpus sources and generated corpus are licensed under Creative Commons
Attribution 4.0 International (CC BY 4.0). Attribute the HuisClos project and
indicate changes when sharing adapted versions.
