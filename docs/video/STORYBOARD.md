# HuisClos AI production storyboard

Master duration: **4:45**. English synthetic narration: **620 words**; use `SCRIPT.md` verbatim.
Narration continues over adjacent shots; the quoted phrases below are sync cues, not extra speech.
Each row has one visible action or a single held view. All times are master-edit timecodes.

## AI production setup

- Reconstruct verified views of the public app at `https://huisclos.streamlit.app` with fictional data only, Standard,
  English interface, French document and default French token labels. Use the local logo
  `app/assets/logo.svg` in the title and end cards; do not modify or regenerate it.
- The public warning must remain legible in every app shot. Its exact text is
  **Public demo: use fictitious data only. To process real client files, install HuisClos on your computer (see the user guide).**
  Preserve the warning strip above the magnified content in Review and Restore close-ups.
  Keep a **Fictional demo** caption on cards and ChatGPT footage as well.
- Prepare the French sample with **Load sample case**. Append `Code de retrait : qx-74-zp.`
  in the input only. The original sample file stays unchanged. Rehearse the manual addition:
  S14 proposed this unmarked value, but S61 does not verify current detector behaviour.
  If it is already marked, prepare a different invented, visibly unmarked value and update
  the take's input and manual-add clips together. Never stage a false miss.
- Prepare a separate public-app browser session for shot 36: **Document language** = **English**,
  **Detection profile** = **Standard**; paste only
  `Client: Mr Pierre VERNOLAC. Email: pierre.vernolac@example.org.`
  This is a translated fragment of the fictional sample, not an evaluation corpus.
  Keep French token labels to make the separate settings visible. No Enhanced model is used online.
- Validate the full review and message check before rendering. If verified states have additional
  alerts, animate each decision as a separate insert in shot 21's time slot. Retiming must
  use block 4's 12.14 seconds of holds, preserve all seven boundaries and keep the master at 4:45.
  Label inserts `21a_check_decision.mp4`, `21b_check_decision.mp4`, one decision per clip.
  Never substitute a ready-state frame for unresolved alerts. Follow the masking/edit/decision
  rules in `SCRIPT.md`; the exact acknowledgement is **I reviewed this mention in its context: keep it in clear**.
- Generate one original English synthetic voice, readable animated app views and English captions.
  Keep **AI-generated reconstruction. Fictional data.** visible throughout the workflow.
  Generate no account details, keys, notifications or unrelated browser tabs.
- Plans 23-25 illustrate transfer and a prepared token-preserving answer, labelled
  **Illustrative AI answer**. Use that same answer for Restore; never claim a live request.
  Validate states against the app or trusted reference captures. If real AI-operated capture
  is used instead, adapt the narration and use the mode B evidence rules in `MASTER_PLAN.md`.

## Shot table

In mode A, each action below is an AI-generated animation of a verified state, not a live click.
ChatGPT views are labelled illustrations. Only alternative mode B can show real captures.
Use `MASTER_PLAN.md` for production steps, tools and evidence requirements.

| Shot | Start | End | Image | Exact action | On-screen text | Narration sync cue | Sound |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 01 | 0:00 | 0:08 | App: prepared fictional sample | Hold on the dismissal note; no input action. | Fictional demo; deadline scenario | "A lawyer has a deadline." | Synthetic voice; quiet room tone. |
| 02 | 0:08 | 0:20 | App: sample detail | Pan once across the client paragraph; leave public warning in frame. | Name / Home address / Social security number (NIR) | "Can we ask an AI tool for help while limiting what we disclose?" | Voice continues; no identifier read aloud. |
| 03 | 0:20 | 0:33 | Legal card | Reveal the secrecy references as one card. | Law of 31 December 1971, art. 66-5; Penal Code, art. 226-13 | "French professional secrecy covers the case file." | Voice only. |
| 04 | 0:33 | 0:50 | Legal card | Replace the secrecy card with the GDPR card. | GDPR art. 4(5), recital 26; Personal data; Separate mapping table | "The result remains personal data." | Voice, then short reading hold. |
| 05 | 0:50 | 1:01 | Title card | Reveal the existing logo, name and tagline together. | HuisClos; Use generative AI on client files without breaching professional secrecy. | "HuisClos, pronounced wee-kloh, means a hearing behind closed doors." | Synthetic voice; pronounce wee-kloh. |
| 06 | 1:01 | 1:05 | App: Import home header | Cut to the matching closed-door logo and header; no click. | Import; public warning | "keep client identities inside the room while preparing a text for AI." | Voice continues. |
| 07 | 1:05 | 1:09 | App: Import | Click **Load sample case**. | Fictitious sample notice | "I choose Load sample case." | Voice; subdued click. |
| 08 | 1:09 | 1:19 | App: settings and input | Hold on the already open sidebar; do not alter settings. | Language: English; Document language: French; Detection profile: Standard; Token style: French labels [PERSONNE_1] | "This public demo processes text on its server, so real files belong in a local installation." | Voice continues through the settings sentence. |
| 09 | 1:19 | 1:23 | App: input | Append `Code de retrait : qx-74-zp.` in **Text to process**. | Invented collection code | "I append an invented collection code, then detect sensitive data." | Voice; quiet typing. |
| 10 | 1:23 | 1:26 | App: Import to Review | Click **Detect sensitive data**; retain the real loading indicator. | Detecting sensitive data. The first run loads the language model. | Continuation of shot 09. | Voice; subdued click. |
| 11 | 1:26 | 1:33 | App: Review close-up | Scroll through **Highlighted text** and **Entities** once, after completing the full review in the take. | Review; colour and type labels; Read unmarked passages too | "I read the whole document, including unmarked passages." | Voice; brief reading hold. |
| 12 | 1:33 | 1:40 | App: Review close-up | Uncheck **Mask** for `Atelier Martin des Nivelles SARL`. | REJECTED; Fictional teaching decision; Real employer details may identify a client | "For this fictional example, I uncheck the employer." | Voice includes the disclosure-risk sentence. |
| 13 | 1:40 | 1:43 | App: manual addition | Enter `qx-74-zp` in **Value to mask**. | Add a value the detection missed | "Next, I add the collection code" | Voice; quiet typing. |
| 14 | 1:43 | 1:45 | App: manual addition | Select **Other identifier** under **Type of this value**. | Other identifier | "as Other identifier" | Voice continues. |
| 15 | 1:45 | 1:48 | App: manual addition | Click **Add and mask everywhere**. | Added occurrence confirmation; OTHER label | "and choose Add and mask everywhere." | Voice; subdued click. |
| 16 | 1:48 | 1:52 | App: Review to Restore | Click **Pseudonymize**. | Replacing the masked values with tokens. | "Pseudonymize replaces accepted values with consistent labels." | Voice; subdued click. |
| 17 | 1:52 | 1:56 | App: outgoing message | Hold on repeated person tokens and the newly masked code; keep the fictional employer visible. | Consistent labels within this document | "The same person keeps the same token within this document." | Voice; short visual hold. |
| 18 | 1:56 | 2:03 | App: Restore instruction | Enter the full deliberately identifying instruction from `SCRIPT.md` in **Your instruction (sent after the text, checked with it)**. | Instruction deliberately includes fictional Pierre VERNOLAC | "I deliberately put the fictional client's name in the instruction." | Voice; quiet typing. |
| 19 | 2:03 | 2:07 | App: Final check close-up | Hold on the real instruction alert; do not dismiss it. | Final check; Location: your instruction. | "The final check flags it." | Voice; no alert sound added. |
| 20 | 2:07 | 2:13 | App: instruction | Replace the entire instruction with the clean version from `SCRIPT.md`. | Summarize the dispute in three short English sentences. Keep every bracketed token exactly as written; do not change, translate or invent tokens. | "I remove it and read the complete message again." | Voice; quiet typing. |
| 21 | 2:13 | 2:19 | App: refreshed Final check and message | Wait for the new check, then hold on its actual resolved status and both message segments. | Actual resolved check status; Check document AND instruction | "Edits require a new check before copying. An alert protects nothing until someone acts." | Voice; reading hold. |
| 22 | 2:19 | 2:22 | App: checked message | Click the enabled copy control at the message's top right, as directed by **Use the copy button at the top right of the message.** | Copy only the checked message | "We illustrate copying the checked message into ChatGPT, without a live request." | Voice; subdued click. |
| 23 | 2:22 | 2:27 | ChatGPT | Paste the checked message unchanged into the composer. | Fictional demo; No mapping table | "The prepared summary preserves each bracketed token unchanged." | Voice; no message sound. |
| 24 | 2:27 | 2:29 | ChatGPT | Animate the checked message as an illustrative request; send nothing in mode A. | Optional Mistral connector: off by default | "The optional Mistral connector stays off by default." | Voice; no connector action. |
| 25 | 2:29 | 2:33 | Illustrative AI answer view | Animate copying the labelled prepared answer; retain unchanged tokens. | Illustrative AI answer; no live request | Transition into "I bring an illustrative answer back" | Synthetic voice or brief room tone during the scene transition. |
| 26 | 2:33 | 2:37 | App: Restore close-up | Illustrate pasting the prepared answer into **Answer from the AI tool**. | Restore the AI answer | "I bring an illustrative answer back and choose Restore." | Voice; quiet paste. |
| 27 | 2:37 | 2:41 | App: Restore close-up | Click **Restore**. | Restored text | "The table replaces tokens with their values." | Voice; subdued click. |
| 28 | 2:41 | 2:46 | App: restored answer close-up | Read and scroll the restored answer once. | Highlighted; type labels beside restored values | "I read the restored answer and export it." | Voice; reading hold. |
| 29 | 2:46 | 2:49 | App: export | Click **Restored text (.docx)**. | Restored answer | Continuation of shot 28. | Voice; subdued click. |
| 30 | 2:49 | 3:00 | App: mapping warning | Hold beside **Mapping table (.mapping.json)**; do not open or copy the table. | Sensitive file: it links tokens to real identities. Keep it on this computer. Never send it to an AI tool. | "That table links tokens to identities. Never send it to an AI tool. A saved case table helps reuse tokens across documents; continuity still needs checking." | Synthetic voice. |
| 31 | 3:00 | 3:07 | Pipeline diagram | Reveal the hybrid detection stage and its plain-language explanations together. | Built-in arithmetic checks; Expected text formats; Context rules; Model trained to label names | "Detection combines check digits, text patterns, name clues and pretrained entity recognition: a model that labels names." | Voice; no effects. |
| 32 | 3:07 | 3:12 | Pipeline diagram | Reveal the local-processing boundary and separate table branch. | No-network test: local processing; Review -> tokens -> final check -> AI answer -> restore; Table stays separate | "A network blocking test checks local processing. Consistent tokens preserve references." | Voice. |
| 33 | 3:12 | 3:28 | Method card | Reveal the threshold and blind-challenge explanation as one held card. | Threshold = cutoff; F2 favours fewer misses; Challenge written blind after freeze; G8R2 reuses that known set | "We chose the threshold, the cutoff for accepting proposed detections, using F two" | Voice continues through the blind-challenge sentence. |
| 34 | 3:28 | 3:37 | Results card | Reveal the G8R2 French table from `SCRIPT.md`, with the two coverage cells highlighted by outlines and text. | Standard 157/190, 325/3600 leaked; Enhanced 170/190, 218/3600 leaked; Local FR option; Coverage gain not statistically significant | "Its French results are on screen. The coverage gain is not statistically significant. French Enhanced is a local option." | Voice; no counting sound. |
| 35 | 3:37 | 3:39 | Historical code card | Replace the French table with the historical-code card. | G8: historical results, e3d13bd; Not a new validation of current code | "G8 results describe historical code." | Voice continues over the cut. |
| 36 | 3:39 | 3:45 | App: prepared English session | Hold on the separate Standard English document view; no second workflow or Enhanced switch. | Document language: English; Standard EN: experimental, strong reservations; Enhanced EN: experimental, not recommended | "English Standard remains experimental with strong reservations; English Enhanced is experimental and not recommended." | Synthetic voice. |
| 37 | 3:45 | 3:58 | Qualitative comparison card | Reveal the proposed preparation workflow beside manual replacement, with no time or accuracy scale. | Qualitative proposal; Manual replacements / Reviewed consistent tokens | "The value case is qualitative. If this review became routine, legal teams could prepare AI requests without rebuilding every replacement by hand." | Voice. |
| 38 | 3:58 | 4:09 | Value card | Reveal the review cost and responsibility caption. | Benefit to test: consistency; Cost: human review | "The tradeoff is time spent reviewing detections, context and the final answer." | Voice continues through the wider-use proposal. |
| 39 | 4:09 | 4:20 | Evidence card | Reveal the evidence needed, without logos or named competitors. | Evidence needed: time study; sourced product comparison; independent assessment | "Testing time savings and comparing competing products would require separate evidence." | Voice continues through "Its usefulness needs independent assessment." |
| 40 | 4:20 | 4:33 | Limits card | Reveal the context and validation limits together. | Context may identify; Pseudonymization is not anonymization; No zero-leakage guarantee; Measured French scope; No complete bilingual validation | "Context can still identify someone." | Synthetic voice; steady pace. |
| 41 | 4:33 | 4:45 | End card | Reveal and hold the existing logo, responsibilities and both addresses through the final frame. | Human review required; Public demo: fictitious data only; Real files: local installation; App: https://huisclos.streamlit.app; Code: https://github.com/Negan-san/huisclos | "Review every detection and the final answer. The human remains responsible. Try the public demo with fictional data, or inspect the code at the addresses on screen." | Voice ends cleanly; room tone to 4:45. |

## Sources and continuity

Exact application labels come from `app/i18n/common.py`, `workflow_import.py`, `workflow_review.py`,
`workflow_check.py` and `workflow_restore.py`. They reflect the working tree read for S61.
Sidebar values may be under separate setting groups; shot 08 is a prepared view, not a sequence
of undisclosed setting changes. Copy controls in HuisClos and ChatGPT are icon controls;
the HuisClos instruction above is the exact localized guidance, not an invented button label.
ChatGPT submission uses the keyboard, so no unverified ChatGPT button label is prescribed.

Legal-card references come from `app/i18n/method.py`, `method.legal.secrecy` and `method.legal.gdpr`.
The door and keyhole explanation comes from D-FIX5-1 and the S61 brief. The data and invented employer
are from the permitted first 40 lines of `data/samples/demo_case_fr.txt`; the collection-code idea
comes from the S14 progress entry. Never open a reserved corpus to prepare a take.

Results in shot 34 are the saved G8R2 figures, code `930c414`, from `README.md` and
`results/gate8-resume/report.md`. Keep **8 fictional documents; known challenge; before human review**
and **Coverage gain not statistically significant** legible. If displaying the full table, retain
partial precision 0.8039/0.8018 and extra masking 366/379 as separate columns, not accuracy claims.
The coverage interval touches zero; the leakage-reduction interval excludes it. The small fictional
set cannot establish zero leakage. G8 on `e3d13bd` is historical; show no current bilingual GO.

`docs/RESEARCH.md` is absent. Shots 37-39 are explicitly qualitative proposals; omit market numbers,
named competitors, CNB-guide claims and claims of measured productivity or superiority.
All cuts preserve the same French sample, review decisions, final checked message and labelled illustrative answer.
Unknown or altered tokens must be reviewed if they appear; retain the app's actual warning.
Do not present any restored AI answer as legal advice ready to send to a client.

## Render list in edit order

These are planned render filenames, not existing deliverables. Generate the voice separately as
`voice_en_synthetic.wav`. Cards and diagrams can be exported with the same clip names for assembly.

| Order | Planned file | Content |
| ---: | --- | --- |
| 01 | `01_hook_file.mp4` | Fictional deadline and dismissal note. |
| 02 | `02_hook_identifiers.mp4` | Name, NIR and address detail. |
| 03 | `03_secrecy_rules.mp4` | French secrecy references. |
| 04 | `04_gdpr_rules.mp4` | Personal data and separate table. |
| 05 | `05_title_logo.mp4` | Existing logo, name and exact tagline. |
| 06 | `06_import_header.mp4` | Matching application header. |
| 07 | `07_load_sample.mp4` | Load sample case. |
| 08 | `08_settings_scope.mp4` | Public hosting and separate settings. |
| 09 | `09_append_code.mp4` | Append invented collection code. |
| 10 | `10_detect.mp4` | Detection action and real loading state. |
| 11 | `11_review_read.mp4` | Review zoom and full reading. |
| 12 | `12_review_reject.mp4` | Uncheck invented employer. |
| 13 | `13_manual_value.mp4` | Type the unmarked value. |
| 14 | `14_manual_type.mp4` | Select Other identifier. |
| 15 | `15_manual_add.mp4` | Add and mask everywhere. |
| 16 | `16_pseudonymize.mp4` | Create tokens. |
| 17 | `17_consistent_tokens.mp4` | Consistent references. |
| 18 | `18_instruction_name.mp4` | Deliberate fictional identifier in instruction. |
| 19 | `19_instruction_alert.mp4` | Actual final-check alert. |
| 20 | `20_instruction_correct.mp4` | Replace with the clean instruction. |
| 21 | `21_message_check.mp4` | Actual refreshed status and complete message. |
| 22 | `22_copy_message.mp4` | Copy checked message. |
| 23 | `23_chatgpt_paste.mp4` | Animate the unchanged checked message in the illustrated composer. |
| 24 | `24_chatgpt_submit.mp4` | Animate an illustrative request; no live submission in mode A. |
| 25 | `25_chatgpt_answer.mp4` | Animate the labelled illustrative answer; no live request claimed. |
| 26 | `26_restore_paste.mp4` | Animate the same prepared answer in HuisClos. |
| 27 | `27_restore_click.mp4` | Restore. |
| 28 | `28_restore_review.mp4` | Read restored values and type labels. |
| 29 | `29_export_docx.mp4` | Download restored text. |
| 30 | `30_mapping_warning.mp4` | Sensitive table and case-continuity caveat. |
| 31 | `31_hybrid_pipeline.mp4` | Hybrid inputs in plain language. |
| 32 | `32_local_boundary.mp4` | No-network test and separate table. |
| 33 | `33_threshold_challenge.mp4` | F2 choice and blind-challenge history. |
| 34 | `34_g8r2_french_results.mp4` | Saved G8R2 French table and limits. |
| 35 | `35_g8_historical.mp4` | Historical e3d13bd label. |
| 36 | `36_english_experimental.mp4` | Brief English Standard view and reservations. |
| 37 | `37_qualitative_value.mp4` | Proposed preparation benefit. |
| 38 | `38_review_cost.mp4` | Human review cost and responsibility. |
| 39 | `39_evidence_needed.mp4` | Productivity and competition evidence still needed. |
| 40 | `40_limits.mp4` | Context and validation limits. |
| 41 | `41_end_addresses.mp4` | Logo, app and repository addresses. |

The sample and its appended line are filming inputs only. Keep any downloaded `.mapping.json`
outside the repository and out of ChatGPT. Do not film a real client file or create extra input files
in this documentation-only session. The optional English fragment is prepared in its separate session.

## Final edit checks

Confirm that the public warning survives every crop, Review and Restore are readable, every visible
decision has its own clip, the corrected instruction is the one illustrated as the outgoing message, and the labelled illustrative answer is the
one restored. Keep captions within the frame, source footers legible and the end addresses on screen
for the last 12 seconds. The voice and action holds in `SCRIPT.md` total 4:45. Check actual export
runtime, TTS timing and human editorial review before submission; no finished video or rehearsal is claimed by S61.

## Rubric coverage

| Criterion | Points | Supporting shots | What the viewer can assess |
| --- | ---: | --- | --- |
| Clarity | 10 | 01-08, 11-21, 27-36, 40-41 | Problem, legal limits, name, settings, visible human decisions, restoration and measured scope. |
| Concision | 5 | 07-30, 34-39 | One French Standard workflow, one brief English view, one current results card, qualitative value case. |
| Delivery | 5 | 01-41, especially 05, 12, 21, 30, 40 | Synthetic English voice, wee-kloh pronunciation, short sentences and deliberate pauses. |
| Production quality | 5 | 05-06, 11-15, 18-21, 26-30, 34, 41 | Existing branding, readable Review/Restore zooms, stable audio, visible warning, explicit reconstruction disclosure and legible addresses. |
| Duration | 5 | 01-41 | Seven blocks from 0:00 to 4:45, checked after the actual export; allowed 4:30-5:30. |
