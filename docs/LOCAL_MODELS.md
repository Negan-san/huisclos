# Local models and study environments

This page records the local models and Python environments prepared in session A1 (28 October
2026) for the bilingual work after gate G7. Since session A3, the application uses only the
existing CamemBERT model, through the Enhanced profile described below; the other models are not
used by the application. The deployed configuration and `requirements*.txt` are unchanged. Model files and environments live
outside the repository, in `pilotage/post_g7_assets/` next to the project folder, and are never
committed.

## Manifest

`post_g7_assets/manifest.json` is the single source for later sessions. It holds:

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

## Environments

| Key | Purpose | Stack | Status |
| --- | --- | --- | --- |
| `baseline_python` | G7 reference; A2, A3 and general B3 checks, full test suite | exact G7 freeze (Transformers 5.21.0, Hub 2.3.0, torch 2.14.1+cpu, spaCy 3.8.18) plus `en_core_web_sm` 3.8.0 | available |
| `candidate_python` | explicit B3 experiments, then A4 checks if a migration is accepted | baseline with Transformers 5.16.1, Hub 1.9.2, GLiNER 0.2.29; httpx2 and httpcore2 (Hub 2.x only) removed | available |

The baseline differs from the shared venv by one declared addition, `en_core_web_sm` 3.8.0
(official wheel, MIT, SHA-256
`1932429db727d4bff3deed6b34cfc05df17794f4a52eeb26cf8928f7c1a0fb85`), which G7 never used. Both environments were
built from lock files with exact pins, without `--no-deps`, and pass `pip check`. The full test
suite passes under the shared venv and under the baseline (1285 tests). Under the candidate, the
CamemBERT, window and merge tests pass; torch warns that `torch.jit.script` is deprecated.

GLiNER 0.2.29 requires `transformers<5.17`, and Transformers 5.16.x requires
`huggingface-hub>=1.5,<2`: the candidate therefore pins the latest 1.x Hub. No migration is
applied to the project; only A4 may change the shared venv.

## Models

| Model | Revision | Licence | Weights | Role |
| --- | --- | --- | --- | --- |
| Jean-Baptiste/camembert-ner | `ef35fe77` | MIT | safetensors | current French reference (D-06) |
| Anonym-IA/V2-camembert-ner-pii-french | `b39848cc` | MIT | safetensors | French PII candidate, `CamembertForTokenClassification` |
| urchade/gliner_multi_pii-v1 | `1fcf13e8` | Apache-2.0 | `pytorch_model.bin` only | French and English PII candidate |
| microsoft/mdeberta-v3-base | `a0484667` | MIT | none copied | GLiNER backbone: config and tokenizer only |
| spaCy `en_core_web_sm` | 3.8.0 | MIT | wheel | English rule and NER base |

GLiNER publishes no safetensors file. Its weights are loaded by GLiNER with
`torch.load(..., weights_only=True)`, which refuses arbitrary Python objects. The scores on the
model cards are not HuisClos results; B3 measures each model and useful combinations on the
project corpus.

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

## Use in the application (session A3)

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
profile has no CamemBERT equivalent until session A4 integrates a multilingual model; the French
CamemBERT is never used for an English document.
