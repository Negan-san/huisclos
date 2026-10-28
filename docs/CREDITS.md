# Credits and local provenance

This inventory was compiled offline in S72 after integrating S71, commit `fa518d2`.
It credits recorded use, and identifies missing evidence separately from planned work.
The project code is MIT, copyright 2026 HuisClos contributors: [LICENSE](../LICENSE).
That licence does not replace package, model or training-data licences.

## Direct software dependencies

The declarations below come from the four requirement files linked in each section.
Installed versions were read with `importlib.metadata` from
`../huisclos/.venv/Lib/site-packages/`, using Python 3.12.10.
`M(name)` means the installed distribution's `<name>-<version>.dist-info/METADATA`;
hyphens in distribution names can be underscores in the directory name.
`L(name)` means the licence file named in that distribution's metadata or RECORD.
The source column identifies the local evidence, not an online licence check.
Every installed direct version matches its declaration; there is no version substitution.
`pip-licenses` 5.5.5 is already installed, but this inventory uses metadata directly.

### Core application

Declarations: [requirements.txt](../requirements.txt). Included requirement files retain their own categories.

| Distribution | Declared version | Installed version | Licence | URL | Role | Local source |
| --- | --- | --- | --- | --- | --- | --- |
| streamlit | 1.66.1 | 1.66.1 (matches) | Apache-2.0 | [upstream](https://github.com/streamlit/streamlit) | Local review interface | M(streamlit): License-Expression |
| presidio-analyzer | 2.2.366 | 2.2.366 (matches) | MIT | [upstream](https://github.com/data-privacy-stack/presidio) | Recognizer registry and detection orchestration | M(presidio-analyzer): License-Expression |
| presidio-anonymizer | 2.2.366 | 2.2.366 (matches) | MIT | [upstream](https://github.com/data-privacy-stack/presidio) | Token substitution | M(presidio-anonymizer): License-Expression |
| spacy | 3.8.18 | 3.8.18 (matches) | MIT | [upstream](https://github.com/explosion/spaCy) | Language pipeline and NER runtime | M(spacy): License; L(spacy): licenses/LICENSE |
| python-docx | 1.2.0 | 1.2.0 (matches) | MIT | [upstream](https://github.com/python-openxml/python-docx) | DOCX reading and export | M(python-docx): License; L(python-docx): licenses/LICENSE |
| pypdf | 6.21.3 | 6.21.3 (matches) | BSD-3-Clause | [upstream](https://github.com/py-pdf/pypdf) | Native PDF text reading | M(pypdf): License-Expression; Project-URL Source |
| pandas | 3.1.0 | 3.1.0 (matches) | BSD-3-Clause | [upstream](https://github.com/pandas-dev/pandas) | Evaluation and interface tables | M(pandas): License-Expression |
| requests | 2.34.2 | 2.34.2 (matches) | Apache-2.0 | [upstream](https://github.com/psf/requests) | Optional explicit Mistral HTTP transport | M(requests): License; L(requests): licenses/LICENSE and NOTICE |
| fr_core_news_md | 3.8.0 (wheel URL) | 3.8.0 (matches) | LGPL-LR | [upstream](https://github.com/explosion/spacy-models/releases/tag/fr_core_news_md-3.8.0) | French model package; artifact licence below | M(fr_core_news_md): License; LICENSE and LICENSES_SOURCES |
| en_core_web_sm | 3.8.0 (wheel URL) | 3.8.0 (matches) | MIT | [upstream](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0) | English model package; artifact licence below | M(en_core_web_sm): License; LICENSE and LICENSES_SOURCES |

### Development and verification

Declarations: [requirements-dev.txt](../requirements-dev.txt). Included requirement files retain their own categories.

| Distribution | Declared version | Installed version | Licence | URL | Role | Local source |
| --- | --- | --- | --- | --- | --- | --- |
| pytest | 9.1.1 | 9.1.1 (matches) | MIT | [upstream](https://github.com/pytest-dev/pytest) | Automated tests | M(pytest): License-Expression |
| ruff | 0.17.3 | 0.17.3 (matches) | MIT | [upstream](https://github.com/astral-sh/ruff) | Lint and formatting checks | M(ruff): License-Expression |
| python-stdnum | 2.2 | 2.2 (matches) | LGPL-2.1-or-later | [upstream](https://github.com/arthurdejong/python-stdnum/) | Checksum validation oracles in tests | M(python-stdnum): METADATA description grants version 2.1 or later; licenses/COPYING is version 2.1; classifier says LGPLv2+ |
| fpdf2 | 2.8.9 | 2.8.9 (matches) | LGPL-3.0-only | [upstream](https://github.com/py-pdf/fpdf2) | Synthetic PDF test fixtures | M(fpdf2): License-Expression |
| psutil | 7.2.2 | 7.2.2 (matches) | BSD-3-Clause | [upstream](https://github.com/giampaolo/psutil) | Local memory measurements | M(psutil): License; L(psutil): LICENSE |
| pip-licenses | 5.5.5 | 5.5.5 (matches) | MIT | [upstream](https://github.com/raimon49/pip-licenses) | Available licence inventory utility | M(pip-licenses): License-Expression |

### Heavy options

Declarations: [requirements-transformers.txt](../requirements-transformers.txt). Included requirement files retain their own categories.

| Distribution | Declared version | Installed version | Licence | URL | Role | Local source |
| --- | --- | --- | --- | --- | --- | --- |
| torch | 2.14.1+cpu | 2.14.1+cpu (matches) | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT | [upstream](https://github.com/pytorch/pytorch) | Optional CPU tensor and model runtime | M(torch): License-Expression |
| transformers | 5.16.1 | 5.16.1 (matches) | Apache-2.0 | [upstream](https://github.com/huggingface/transformers) | Optional pretrained model runtime | M(transformers): License; licenses/LICENSE, Apache 2.0 text |
| huggingface-hub | 1.9.2 | 1.9.2 (matches) | Apache-2.0 | [upstream](https://github.com/huggingface/huggingface_hub) | Optional model preparation and local resolution | M(huggingface-hub): License; licenses/LICENSE |
| tokenizers | 0.23.3 | 0.23.3 (matches) | Apache Software License; exact version not verified locally | [upstream](https://github.com/huggingface/tokenizers) | Optional tokenization and offset support | M(tokenizers): Classifier only; no local licence text or versioned expression found; check upstream LICENSE linked in M(tokenizers) |
| sentencepiece | 0.2.2 | 0.2.2 (matches) | Apache-2.0 | [upstream](https://github.com/google/sentencepiece) | Optional subword vocabulary support | M(sentencepiece): License-Expression |

### English heavy option

Declarations: [requirements-enhanced.txt](../requirements-enhanced.txt). Included requirement files retain their own categories.

| Distribution | Declared version | Installed version | Licence | URL | Role | Local source |
| --- | --- | --- | --- | --- | --- | --- |
| gliner | 0.2.29 | 0.2.29 (matches) | Apache-2.0 | [upstream](https://github.com/urchade/GLiNER) | Optional English neural recognizer runtime | M(gliner): License; licenses/LICENSE |


Python itself is the interpreter, not a pip requirement. The recorded environment is
Python 3.12.10; its separate distribution licence is not verified locally in S72.

### Complete optional environment lock

[requirements-enhanced-lock.txt](../requirements-enhanced-lock.txt) records 109 pins for
the A4 Windows CPU environment. It includes the 22 direct distributions above and 87 other
distributions, including transitive libraries and installation tools. It is not a list of
109 libraries imported directly by HuisClos, and is not a macOS validation.
The local metadata inventory found all 109 installed at the declared versions.
The other 87 licences are not individually credited or cleared here: not verified locally;
consult their installed `METADATA`, `License-Expression`, `License-File` and bundled notices
before redistributing that complete environment. Preserve notices supplied by the wheels.
The separate toolkit requirements select installation options; they do not change this
distinction between direct declarations and the complete lock. See [LOCAL_MODELS.md](LOCAL_MODELS.md).

## Pretrained models

The library code licences appear above. The following licences are the model publishers'
recorded declarations for model artifacts, not licences for every training example.
Standard is the default. Enhanced is optional and local; English Enhanced remains
experimental and not recommended. See [LOCAL_MODELS.md](LOCAL_MODELS.md) and D-G8R2-1
in [DECISIONS.md](DECISIONS.md).

| Model and repository | Version or immutable revision | Artifact licence evidence | Recorded role |
| --- | --- | --- | --- |
| [Explosion fr_core_news_md](https://github.com/explosion/spacy-models/releases/tag/fr_core_news_md-3.8.0) | 3.8.0, declared and installed | LGPL-LR, Lesser General Public License for Linguistic Resources; installed `fr_core_news_md/meta.json`, distribution `LICENSE` and `LICENSES_SOURCES` | French Standard NER; also used in French Enhanced |
| [Explosion en_core_web_sm](https://github.com/explosion/spacy-models/releases/tag/en_core_web_sm-3.8.0) | 3.8.0, declared and installed | MIT; installed `en_core_web_sm/meta.json`, distribution `LICENSE` and `LICENSES_SOURCES` | English Standard NER; also used in English Enhanced |
| [Jean-Baptiste/camembert-ner](https://huggingface.co/Jean-Baptiste/camembert-ner) | `ef35fe7767c1dad71f5c853838cdd80d0b3441ed` | MIT recorded in the A1 local manifest and LOCAL_MODELS.md; separate weight licence text not verified locally: the pinned local `models/camembert_ner/README.md` is absent | Retained French Enhanced backend, safetensors weights |
| [urchade/gliner_multi_pii-v1](https://huggingface.co/urchade/gliner_multi_pii-v1) | `1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d` | Apache-2.0 declared by the pinned local model card and A1 manifest | Optional English Enhanced backend, published PyTorch binary weights; also studied in French |
| [microsoft/mdeberta-v3-base](https://huggingface.co/microsoft/mdeberta-v3-base) | `a0484667b22365f84929a935b5e50a51f71f159d` | MIT declared by the pinned local model card and A1 manifest | GLiNER backbone configuration and tokenizer; no separate backbone weights copied |
| [Anonym-IA/V2-camembert-ner-pii-french](https://huggingface.co/Anonym-IA/V2-camembert-ner-pii-french) | `b39848ccac582505a33dc859084f49a27bcd1402` | MIT declared by the pinned local model card and A1 manifest | A1-A4 study candidate, rejected at integration; no embedded application backend |

Neural provenance sources are outside the repository under
`../pilotage/post_g7_assets/manifest.json` and `models/<folder>/README.md`.
The inspected folders were only `camembert_ner`, `gliner_multi_pii_v1`,
`mdeberta_v3_base` and `anonym_ia_v2`. S72 read metadata and the available cards,
without loading weights or browsing document caches. The spaCy release versions identify
the wheels; `spacy_git_version=5010fcbd3` in both meta files identifies spaCy's recorded
build source, not a new model-weight revision.

### External training data and resources

HuisClos's evaluation documents are fictional, but its pretrained models depend on external
data. Model and library licences must not be presented as licences for those data.
The following statements report local publisher metadata; S72 did not fetch datasets.

| Model or resource | External source credited locally | Licence or remaining evidence gap |
| --- | --- | --- |
| French spaCy | [UD French Sequoia v2.8](https://github.com/UniversalDependencies/UD_French-Sequoia), Candito, Seddah, Perrier and Guillaume | LGPL-LR in `meta.json` and `LICENSES_SOURCES` |
| French spaCy | [WikiNER](https://figshare.com/articles/Learning_multilingual_named_entity_recognition_from_Wikipedia/5462500), Nothman, Ringland, Radford, Murphy and Curran | CC BY 4.0 in the same local sources |
| French spaCy | [spaCy lookups data](https://github.com/explosion/spacy-lookups-data), Explosion | MIT in the same local sources |
| French spaCy | Explosion fastText vectors, trained on OSCAR Common Crawl and Wikipedia | CC0 recorded for the vectors in `meta.json`; underlying text rights are not separately verified locally |
| English spaCy | [OntoNotes 5](https://catalog.ldc.upenn.edu/LDC2013T19), Weischedel and coauthors | `commercial (licensed by Explosion)` in `meta.json` and `LICENSES_SOURCES`; the MIT model licence does not grant access to the dataset |
| English spaCy | [ClearNLP conversion reference](https://github.com/clir/clearnlp-guidelines/blob/master/md/components/dependency_conversion.md), Emory University | Local metadata says citation only, no code packaged with the model |
| English spaCy | [WordNet 3.0](https://wordnet.princeton.edu/), Princeton University | WordNet 3.0 License, text included in `LICENSES_SOURCES` |
| Retained CamemBERT | Training lineage not independently established from an available pinned card | not verified locally; obtain `camembert_ner/README.md` for the pinned revision and the referenced data notices |
| GLiNER PII | Fine-tuning of `urchade/gliner_multi-v2.1` on `urchade/synthetic-pii-ner-mistral-v1`, named in the local card | Dataset and intermediate model licences not verified locally; their own pinned cards and notices are needed |
| mDeBERTa | CC100 multilingual pretraining data, named in the local card | Data licence and complete upstream lineage not verified locally; check the CC100 data notice separately |
| Anonym-IA candidate | Local card names `almanach/camembert-base`, synthetic French legal examples and `TypicaAI/pii-masking-60k_fr` | Training-data licences not verified locally; model MIT declaration does not resolve them. Card training and score claims are publisher statements, not HuisClos measurements |

The GLiNER name of a synthetic dataset is evidence of upstream model training, not evidence
that HuisClos used a Mistral generation service. The Anonym-IA card's placeholder GitHub URL
is not credited as a verified project repository; the model repository above is identified.

## Project corpus, authorship and review

[corpus/README.md](../corpus/README.md), section "Fictional data and licence", explicitly
licenses the corpus sources and generated corpus under **CC BY 4.0**. Attribute the
HuisClos project and indicate changes. This establishes the attribution locally;
the code's MIT notice alone would not establish it.

The corpora were created for the course, using invented legal matters and deterministic
synthetic identifier placeholders. Valid checksums do not establish that an identifier is
unassigned in real life. The corpus is not a collection of client files.

| Material | Recorded tool and review evidence |
| --- | --- |
| Initial French development batch | S11/H1, Codex, model not exposed; saved initial and follow-up instructions in `docs/prompts/corpus_lot_1.md`; editorial reread reported in PROGRESS.md |
| French batches 2 and 3 and demonstration | C1, Codex, model unknown; authoring instructions in `docs/prompts/corpus_lot_2.md` and `corpus_lot_3.md`; reread and builder validation recorded |
| Difficult French development batch | S14, Codex, model unknown; `docs/prompts/corpus_lot_4.md`; authorship shared with rule development, so not independent validation |
| Historical French challenge | C2, Claude Code, Opus 5.5; provenance already recorded in PROGRESS.md and path `docs/prompts/corpus_lot_5.md`; reserved authoring prompt not opened in S72 |
| English development material | AF-B2; tool and model unknown in the integrated fragment; editorial completeness remains limited, as corpus/README.md records |
| Post-G7 blind FR/EN material | C3, Codex, model unknown; existing provenance and editorial second reading recorded in PROGRESS.md and D-C3-3; path `docs/prompts/corpus_post_g7_blind.md`, not opened in S72 |

S72 did not read or fingerprint reserved corpus texts or annotations. Authoring agents'
editorial rereads and automated span checks are not evidence that an independent human
validated every annotation. Single-author and model-family correlations remain limitations.
[CONTRIBUTIONS.md](CONTRIBUTIONS.md) names Graciano Nascimento for project framing and the
master plan. Other individual human contributions should be credited only when documented.

## AI tools used during the project

| Tool and model | Recorded role and evidence |
| --- | --- |
| Claude at claude.ai, Opus 5.5 | Master planning, planning row in [PROMPTS.md](PROMPTS.md) and `docs/prompts/00_master_prompt.md` |
| Claude Code, Opus 5.5, Sonnet 5.5 and Haiku 5.5 | Implementation, correction, acceptance and documentation sessions identified individually in PROGRESS.md and PROMPTS.md; S71 is Claude Code, Opus 5.5 |
| Codex, GPT-6 where explicitly recorded; otherwise model unknown | Implementation, independent reviews, corpus authoring, planning and documentation. S61, TK1 and PLAN71 explicitly record GPT-6. The planning suggestion GPT 6.1 Sol High is not evidence that every Codex session used that model |
| Codex, exact model unknown in S72 | Offline attribution and prompt-log consolidation after observing the committed S71 handoff; this session's prompt names only the available model |
| ChatGPT and Mistral as destination services | Available or planned workflow destinations, not attested external production runs in S61/S71/S72. Tests use simulated responses or transport; the mapping table is never a permitted payload |

The [prompt log](PROMPTS.md) retains exact follow-ups where available and distinguishes
missing originals from reconstructed summaries. Human prompt submission, decisions and
code-review responsibilities are documented in AGENTS.md and D-PIL-1; this is not a claim
of a signed human audit of every output.

## External video: production pending

The video is entrusted to a classmate, with AI production and synthetic voice planned.
S61 already produced the script and storyboard; PLAN71 adapted the plan to a disclosed
synthetic reconstruction. Those are completed documentation tasks, not a rendered video.
The production tool, voice model, producer's name and actual generation prompts have not
been supplied. Canva, Clipchamp, ElevenLabs and other recommended tools must not be credited
as used without that evidence. PLAN71's official web readings were planning research only.

A separate video credits annex will accompany the delivered video: actual tools and model
versions, assets and rights, voice attribution, submitted prompts and production dates.
Future prompts in [video/MASTER_PLAN.md](video/MASTER_PLAN.md) are planned, not submitted.
No render, synthetic voice file, free quota or export entitlement is guaranteed by S72.
S72 can finish before that delivery; the course submission still requires the video.

## Legal and market references

Use S71's [METHOD_REPORT.md](METHOD_REPORT.md), sections 2, 3 and 12, for the references
actually retained: GDPR Regulation (EU) 2016/679, Law no. 71-1130 article 66-5 and Penal
Code article 226-13, with official publication links. S71 and S72 did not consult those
sites. Reuse licences for the linked publications are **not verified locally**; check the
publication notices at the EUR-Lex and Legifrance links in the report.

`docs/RESEARCH.md` and root `RESEARCH.md` are absent. No research report, market statistics,
competitor study or final status of recent legal guidance is credited as completed.
The application Method page's historical CNB reference remains unverified in the repository,
as S71 records; it is not a new verified source for these credits. Research and video
production evidence remain separate from local software and model metadata.
