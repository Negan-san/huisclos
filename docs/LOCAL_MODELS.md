# Local models and study environments

This page records the local models and Python environments prepared in session A1 (28 October
2026), and the A4 integration after gate G7. Standard supports French and English. Enhanced
retains CamemBERT for French and adds GLiNER for English, locally and optionally. These post-G7
profiles remain experimental until bilingual gate G8. Historical A1/A3 records below are preserved;
the current installation, migration and measurements are in the A4 section. Model files and environments live
outside the repository, in `pilotage/post_g7_assets/` next to the project folder, and are never
committed.

## Manifest

`post_g7_assets/manifest.json` records the A1 environments and pinned model files. The A4
`retained-runtime-final.json` and integration report at the end of this page record the
retained runtime; the historical A1 files are preserved. The A1 manifest holds:

- `baseline_python` and `candidate_python`: the two interpreters, each with a status
  (`available` or `unavailable`) and a note;
- `environments`: Python version, key package versions, `pip check` result and a full freeze file
  with its SHA-256, for the shared project venv (read only), the baseline and the candidate;
- `models`: repository, immutable revision, licence, local path, and for every file its size,
  SHA-256 and the published hash it was checked against (LFS SHA-256 for weights, git blob SHA-1
  for small files);
- `checks`: offline loading results per interpreter, including the missing-file check.

Regenerate or extend it with `PY scripts/prepare_local_models.py` and one of four actions:
`fetch` (download pinned files, network used for downloads only), `export` (copy the CamemBERT
snapshot from the local Hugging Face cache), `envs` (record interpreters) and `verify` (load each
model in a fresh process).

## Historical environments (A1, before A4 migration)

| Key | Purpose | Stack | Status |
| --- | --- | --- | --- |
| `baseline_python` | G7 reference; A2, A3 and general B3 checks, full test suite | exact G7 freeze (Transformers 5.21.0, Hub 2.3.0, torch 2.14.1+cpu, spaCy 3.8.18) plus `en_core_web_sm` 3.8.0 | available |
| `candidate_python` | explicit B3 experiments, then A4 checks if a migration is accepted | baseline with Transformers 5.16.1, Hub 1.9.2, GLiNER 0.2.29; httpx2 and httpcore2 (Hub 2.x only) removed | available |

At A1, the baseline differed from the shared venv by one declared addition, `en_core_web_sm` 3.8.0
(official wheel, MIT, SHA-256
`1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85`), which G7 never used. Both environments were
built from lock files with exact pins, without `--no-deps`, and passed `pip check`. At A1 the
full suite passed under the shared venv and baseline (1285 tests); the candidate passed the
CamemBERT, window and merge tests. Torch warned that `torch.jit.script` is deprecated.

GLiNER 0.2.29 requires `transformers<5.17`, and Transformers 5.16.x requires
`huggingface-hub>=1.5,<2`: the candidate therefore pins Hub 1.9.2. No migration was
applied to the project at A1; A4 later migrated the shared venv as recorded below.

## Model inventory and licences

The table includes study candidates. In the retained application, CamemBERT is the French
Enhanced backend and GLiNER is the English Enhanced backend; Anonym-IA was not adopted.
The Standard French model `fr_core_news_md` 3.8.0 is LGPL-LR; the English model below is MIT.
Licences are recorded from the pinned local model manifest and installed metadata, not from
the application's own MIT licence. No paid inference service is used for these local models;
the measured costs below are CPU time and resident memory, not a cloud price estimate.

| Model | Revision | Licence | Weights | Role |
| --- | --- | --- | --- | --- |
| Jean-Baptiste/camembert-ner | `ef35fe77` | MIT | safetensors | retained French Enhanced backend (D-06) |
| Anonym-IA/V2-camembert-ner-pii-french | `b39848cc` | MIT | safetensors | French PII candidate, `CamembertForTokenClassification` |
| urchade/gliner_multi_pii-v1 | `1fcf13e8` | Apache-2.0 | `pytorch_model.bin` only | retained English Enhanced backend; French study candidate rejected |
| microsoft/mdeberta-v3-base | `a0484667` | MIT | none copied | GLiNER backbone: config and tokenizer only |
| spaCy `en_core_web_sm` | 3.8.0 | MIT | wheel | English rule and NER base |

Full immutable revisions of retained neural models:

| Repository | Revision |
| --- | --- |
| Jean-Baptiste/camembert-ner | `ef35fe7767c1dad71f5c853838cdd80d0b3441ed` |
| urchade/gliner_multi_pii-v1 | `1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d` |
| microsoft/mdeberta-v3-base, configuration and tokenizer | `a0484667b22365f84929a935b5e50a51f71f159d` |

GLiNER publishes no safetensors file. Its weights are loaded by GLiNER with
`torch.load(..., weights_only=True)`, which refuses arbitrary Python objects. The scores on the
model cards are not HuisClos results; B3 compared candidates and A4 measured the integrated
profiles on development data only.

Anonym-IA V2 uses its own label set (for example `NOM_PERSONNE`, `PRENOM_PERSONNE`,
`NOM_SOCIETE`, `NOM_VOIE`, `VILLE`, `NUM_DOSSIER`). On the check sentence it labels first and last
name as two separate entities: a mapping to HuisClos types is needed before any comparison.

## Offline loading

`verify` starts a new process per model with `HF_HOME` and `HF_HUB_CACHE` pointing to an empty
temporary folder, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` and socket connections refused.
Token classification models load with `local_files_only=True` and `trust_remote_code=False`.
GLiNER exposes no `trust_remote_code` option; for its DeBERTa backbone it builds the Transformers
class `DebertaV2Model` directly, and no model folder contains Python code.

GLiNER reads its backbone name from `gliner_config.json` and offers no override at load time. The
probe therefore builds a temporary runtime folder: a hard link to the official weights and a copy
of the configuration whose only change is `model_name`, set to the local mdeberta folder. The
official files are never modified.

A missing auxiliary file must fail clearly. A1 found that Transformers 5.21 silently builds a
CamemBERT tokenizer of 6 tokens when `sentencepiece.bpe.model` is missing; the model then runs
on unreadable input and finds nothing. `detection.camembert.check_vocabulary` now refuses a
tokenizer smaller than the model vocabulary, and the probe applies the same rule. Results: a
missing `sentencepiece.bpe.model` (CamemBERT), `config.json` (Anonym-IA) or backbone `spm.model`
(GLiNER) each stops the load with an error.

## Using an interpreter

Read the path from the manifest, then call it explicitly, for example:

```
PYTHONUTF8=1 "<baseline_python>" -m pytest -q
PYTHONUTF8=1 "<candidate_python>" <B3 experiment script>
```

Model folders are under `post_g7_assets/models/<name>`. A model missing from the manifest or
marked `unavailable` must be reported as such, never replaced by a download at run time.

## Historical application configuration (session A3)

The sidebar offers two detection profiles, independent of the interface language and of the token
style:

| Profile | Document languages | Sources | Where |
| --- | --- | --- | --- |
| Standard | French, English | rules, spaCy (`fr_core_news_md` or `en_core_web_sm`), propagation | everywhere |
| Enhanced local detection | French only | Standard plus CamemBERT | local installation only |

Enhanced loads CamemBERT on the first detection that asks for it, behind a progress indicator,
and keeps only the engine in the process cache, never a text or a mapping table. Before any
loading, `detection.pipeline.check_camembert_snapshot` checks the local Hugging Face cache
without network access: `config.json`, `sentencepiece.bpe.model` and `model.safetensors` must
exist for revision `ef35fe7767c1dad71f5c853838cdd80d0b3441ed` (the A1 revision, declared in
`huisclos.config.CAMEMBERT_REVISION`), and the `main` reference of the cache must point to that
same revision. A missing package, a missing file or another revision stops the detection with a
clear message; nothing is downloaded and the application never switches to another profile on its
own. With `HUISCLOS_PUBLIC_DEMO=true`, Enhanced is refused even if an older session value asks
for it.

The identity of the models (document language, spaCy model and installed version, CamemBERT
repository and revision) is part of the detection fingerprint: changing the profile, the document
language or the installed model makes the earlier review and final check stale. The English
profile had no Enhanced equivalent in A3. A4 adds GLiNER, as described below; the French
CamemBERT is never used for an English document.

## Historical A4 preflight, before installation permission

The Codex preflight on 28 October 2026 verified all 20 recorded model files, package origins
inside each respective venv, unchanged installed freezes and successful `pip check` in all three
environments. Evidence is outside the repository in
`benchmarks/A4/preflight-codex-20261028T135415Z.json`. The A1 freeze hashes describe UTF-8 text
normalised to LF; Windows files use CRLF, so their byte hashes differ. Both hashes are recorded
in the preflight; the historical manifest and freezes were preserved. Future records made by
`describe_environment` hash the bytes read back from the written file, with LF and CRLF
regression tests, so their hashes can be checked directly against the file.

`en_core_web_sm` was absent from the shared project venv. A4 requires its installation even
if no new neural backend is selected. The session prompt forbids Codex package installation and
assigns dependency migration decisions to Claude. Integration and the final profile choice remain
pending; no package, model, environment or requirement was changed by this preflight. A4 is not
frozen at that point. The user then explicitly authorised Codex to perform the tasks assigned to
Claude, including installation and architecture choices. The continuation below supersedes this
temporary block.

## A4 retained profiles and migration

| Document | Standard, default | Enhanced, optional local profile |
| --- | --- | --- |
| French | rules, checksums, fr_core_news_md 3.8.0, propagation | Standard plus existing CamemBERT, revision ef35fe77 |
| English | rules, checksums, en_core_web_sm 3.8.0, propagation | Standard plus GLiNER multi PII v1, revision 1fcf13e8, cutoff 0.70 |

No Anonym-IA runtime backend is retained. The French development set is saturated: Anonym-IA,
GLiNER and their union provide no coverage gain against Standard or existing CamemBERT. The
existing French option is kept as required by A4, without a new recommendation from this dev.
GLiNER is retained only as an optional English reinforcement; Standard remains the default in
both languages. No heavy profile is allowed in the public demo.

The shared venv now matches the A1 candidate exactly: Transformers 5.16.1, huggingface-hub 1.9.2,
GLiNER 0.2.29, torch 2.14.1+cpu, tokenizers 0.23.3, sentencepiece 0.2.2, spaCy 3.8.18 and both spaCy
models 3.8.0. Only the English model was added to the light requirements. Torch, Transformers
and GLiNER remain optional. The two obsolete Hub 2.x packages, httpx2/httpcore2, were removed;
all other package versions match the baseline plus English. No constraint was bypassed.

Before migration, the independent G7 checkout at 422a2cd passed 1229 tests under baseline_python;
the candidate passed the integrated suite. `pip check`, the normal resolver dry runs and the
shared installation all passed. The complete portable lock is `requirements-enhanced-lock.txt`
(Python 3.12.10, Windows CPU); its SHA-256 is
`f14dc46242cb69f46764df772b32eea3a8a021dbb839ae9fd0bd284249dd35dc`.
The shared freeze, normalised LF, is
`65204dcb4cd892eca279356d9e858660f52c8c8ebc85a7e8730e852e023bbce7`, identical to the A1 candidate
text freeze. Full evidence is in `post_g7_assets/benchmarks/A4/migration.json` and the adjacent
resolver, install and test logs. The historical A1 manifest, locks and snapshots were preserved.

### Local installation

For Standard, install `requirements.txt` (or `requirements-dev.txt` for development) as in
the [user guide](USER_GUIDE.md). Standard needs neither the model package below nor Torch,
Transformers or GLiNER. For the local heavy option, use the full lock in a separate venv.
`PY` below means the explicit path to that environment's Python, not a command to paste as-is:

```
PY -m pip install -r requirements-enhanced-lock.txt
PY -m pip check
```

Alternatively, install the CPU torch wheel from the index stated in requirements-transformers.txt,
then `PY -m pip install -r requirements-enhanced.txt`. The full lock is the reproducible reference;
do not install with `--no-deps`. Preserve the light environment when creating an enhanced one.

Prepare a package outside the repository, before starting the application:

```
PY scripts/prepare_local_models.py fetch --assets <folder> --models camembert_ner gliner_multi_pii_v1 mdeberta_v3_base
```

Set `HUISCLOS_MODELS_DIR` to that folder. For the current development machine, it is
`C:/Users/nasci/Documents/Coding Project/Assignment/pilotage/post_g7_assets`.
The folder must contain `manifest.json` and the model subfolders written by the preparation tool.
Download requests contain model identifiers only, never a document or a mapping table.
Anonym-IA is unnecessary for the retained runtime profiles.

For example, after preparing your own package outside the repository, start the optional
profile from PowerShell with that package path (replace both paths with yours):

```powershell
$env:PYTHONUTF8 = "1"
$env:HUISCLOS_MODELS_DIR = "C:/HuisClosModels"
C:/HuisClosEnhanced/Scripts/python.exe -m streamlit run streamlit_app.py --server.address localhost
```

The complete lock was validated on Python 3.12.10, Windows CPU. The normal Standard commands
also cover macOS; the heavy lock has not been validated on macOS. Preparation may use a
network connection to fetch public packages and model files; application processing does not.

GLiNER checks the two repository identities and immutable revisions, all five required files
and their pinned SHA-256 before loading. The backbone vocabulary, capacity and span width are
also checked. The encoder keeps its native 512-token limit; the 256-token text window does not
reduce that limit. Every prepared label prompt plus text is encoded without truncation and
checked against 512 before prediction. It uses CPU, six fixed labels (person, organization, address, email, phone number,
date of birth), 256-subtoken windows including specials and a 64-subtoken overlap. No generic
date or city is requested. It produces its own `ner_gliner` source before canonical projection
and the common merge; invalid offsets, scores or span text stop processing. No document is
truncated and no component is silently promoted into a complete address.

CamemBERT also accepts the explicit package, with its five file hashes checked, and loads the
immutable revision explicitly. Without HUISCLOS_MODELS_DIR it keeps the historical Hugging Face
cache behaviour. An explicitly incomplete package fails, without falling back to that cache.
GLiNER uses the explicit package or `<home>/.cache/huisclos`, never a remote model identifier.

The GLiNER runtime folder contains a temporary local copy of its configuration pointing to the
local backbone and a link (or copy) of the official weights; it is removed after loading. Official
snapshots are unchanged. The only persistent cache holds engines. Model files, revisions,
package versions and the backend cutoff enter the fingerprints and archived registration.
Missing files or incompatible versions stop detection visibly, without download or profile fallback.

### Integrated development comparison and limitations

Two independent repetitions per profile, CPU, same thresholds, source hashes and paired B1
bootstrap (2000 draws, seed 45). Reports are outside the repository in
`benchmarks/A4/validation_v3/integrated_{fr,en}_{1,2}/`; the replayed full candidate matrix is in
`benchmarks/A4/matrix_v2/`. G7 outputs and historical metrics were not overwritten.

| Dev | Profile | Fully covered | Leaked characters | Non-sensitive masked |
| --- | --- | ---: | ---: | ---: |
| FR, 20 documents | Standard, Enhanced and G7 comparators | 311/311 | 0/6701 | 7/34777 |
| EN, 8 documents | Standard | 124/136 | 105/2553 | 48/12864 |
| EN, 8 documents | Enhanced GLiNER | 126/136 | 63/2553 | 48/12864 |

English point estimates meet the predeclared engineering criterion. Partial precision changes
from 0.9313 to 0.9323; full coverage gains 0.014706 [0; 0.032473], leakage changes by -0.016451
[-0.037632; 0] and over-masking by 0 [0; 0]. All three paired intervals include
zero: no significance or generalisation claim is made. The B3-01 phone correction accounts for
one additional covered entity and one less leaked character in each English profile versus B3.

Final check does not mask anything. On this dev it raises no English Standard alert despite
12 exposed entities. English Enhanced raises 29 alerts, one on a visible reference and 28
elsewhere, with 10 entities still exposed. This is a substantial review burden, not an independent
validation. GLiNER keeps its validated 0.70 cutoff in final check; only the main detection
threshold drops from 0.30 to 0.10. French Enhanced raises two alerts outside references.

GLiNER needs roughly 2.8 GiB resident memory in the local probes; this is far above Standard EN.
The short two-document CPU probe, including imports, models and restoration, took about
16 seconds with two torch threads. These measurements are observations, not latency guarantees.
`PY scripts/measure_memory.py --enhanced --language en` compares the retained local profiles;
its RSS readings are snapshots, not sampled peaks. B3 contains independent full-lot cost records.

For context only, the historical Standard French S51 probe reached 732.2 MiB RSS including
Streamlit imports; the earlier S44 sequential comparison recorded 716.6 MiB for Standard and
1203.9 MiB for French Enhanced, with detection taking 0.135 s and 0.477 s respectively.
These used the older neural stack and a short demonstration document. They are not new A4
measurements and cannot be compared directly with the English two-document probe.

Both production backends passed fresh-process tests with empty HF caches, sockets/DNS blocked,
two stable-token documents, JSON reloading and a mixed restored reply. Removing CamemBERT's
vocabulary or GLiNER's backbone vocabulary fails before inference; caches stay empty. Candidate
and shared evidence is in `package-{candidate,shared}-final.json` and the adjacent logs.

The GLiNER import emits the installed torch.jit.script deprecation warning. Transformers also
emits a generic Mistral-regex warning for the local DeBERTa tokenizer: inspection of its installed
code shows that a config without transformers_version triggers that branch even for DeBERTa.
No Mistral regex patch was applied to this SentencePiece model. The warning is preserved in logs;
offset validity and actual development outputs were tested rather than inferred from that message.

The small fictional dev sets do not validate new documents. Long English private-reference
wordings outside the bounded rules remain a known coverage limit. Human review is required.
Only G8 may measure reserved corpora and decide the bilingual validation after the A4 freeze.

### Reproducible fallback

Standard needs neither Torch, Transformers nor GLiNER; selecting it is an explicit user action.
The autonomous A1 baseline and its full lock remain under `post_g7_assets/envs/`, with the original
G7 model snapshots and the independent checkout `reference_g7` at 422a2cd. Run that checkout with
baseline_python to reproduce G7; it does not import shared-venv packages.
To rebuild the reference, create a separate Python 3.12.10 venv and resolve the preserved
`baseline_lock.txt` with the CPU torch index and the archived English wheel, then run pip check
and the G7 suite. Restoring the old neural stack in an environment requires removing optional
GLiNER before installing the baseline lock, since its Transformers constraint is incompatible.
Keep the validated enhanced venv and its lock when using a separate baseline; no worker or
service is needed for either profile.

### Truncation correction before the final freeze

A4 found that setting the shared GLiNER tokenizer limit to 256 also truncated its internal
label prompt plus text. A new synthetic 242-word case reproduces 261 encoded tokens being cut
to 256. The final backend A4.2 separates the 256-token text windows from the native 512-token
encoder and checks the complete prepared input. Regression tests cover both limits and refusal
of an overflowing prompt.

The earlier A4 matrix and validation_v2 reports, and the GLiNER prototype observations in B3,
are historical experiments with that limitation; they are not the evidence for adoption.
The corrected full matrix is matrix_v2 and the real integrated comparisons are validation_v3.
Their two repetitions agree and their source hashes are registered. No label, threshold or
reserved-corpus result was used to compensate for the fix. The final profiles still use 0.30
and GLiNER 0.70, selected on dev only. The original reports are preserved.

The final provenance report is benchmarks/A4/integration-summary.json, SHA-256
`8f2bcf99aac29f0d6904b7806168bab564c948ea862244fc0214bb383e67f5ff`. It includes actual
model identities, revisions, dependency versions, source hashes and the unchanged B1 metrics.
The retained runtime manifest is retained-runtime-final.json, SHA-256
`3e3e8fefcbe59f057e199f558dd1a634d6ebf2c103f35b9df524ee21ae5c5416`.
