# HuisClos demonstration script

Target runtime: **4:45 (285 seconds)**. Spoken budget: **618 words**, **4:24.86 of speech**
at 140 words per minute, plus **20.14 seconds of reading/action holds**.
Seven blocks include narration and short reading or action holds; their allocated durations total 4:45.
Record an English human voice. Pronounce HuisClos **wee-kloh**. Read only the blockquotes.
Sources in square brackets, headings, tables and production cues are silent.

| Block | Timeline | Allocated duration | Spoken words | Speech at 140 wpm | Reading/action hold |
| --- | --- | ---: | ---: | ---: | ---: |
| 1. Hook | 0:00-0:20 | 20 s | 43 | 18.43 s | 1.57 s |
| 2. Problem and rules | 0:20-0:50 | 30 s | 66 | 28.29 s | 1.71 s |
| 3. Name and promise | 0:50-1:05 | 15 s | 32 | 13.71 s | 1.29 s |
| 4. Live demo | 1:05-3:00 | 115 s | 238 | 102.00 s | 13.00 s |
| 5. Under the hood | 3:00-3:45 | 45 s | 103 | 44.14 s | 0.86 s |
| 6. Value and competition | 3:45-4:20 | 35 s | 81 | 34.71 s | 0.29 s |
| 7. Limits and close | 4:20-4:45 | 25 s | 55 | 23.57 s | 1.43 s |
| Total | 0:00-4:45 | 285 s | 618 | 264.86 s | 20.14 s |

Timing convention: count whitespace-separated spoken words after removing source annotations.
Hyphenated words count once. Say numbers as written in the narration; numeric result tables are visual only.
Speech time is words multiplied by 60/140; the remaining time in each block is a planned hold.
Displayed values are rounded; totals use the unrounded values.
Rehearse against the allocated block boundaries, then export exactly 4:45; the permitted window is 4:30-5:30.

## 1. Hook | 0:00-0:20

> A lawyer has a deadline. The dismissal file names the client, gives a home address, and includes a French social security number, the NIR. [source: data/samples/demo_case_fr.txt, opening paragraphs; deadline is the fictional framing of this demonstration.]
> Can we ask an AI tool for help while limiting what we disclose? This demonstration uses entirely fictional data. [source: README.md, introduction and Confidentiality.]

Silent cue: introduce the fictional dismissal file; show the name, NIR and address with text labels.
Keep the public demo warning visible. Do not read the identifiers aloud.

## 2. Problem and rules | 0:20-0:50

> French professional secrecy covers the case file. The nineteen seventy one law and the Penal Code set the legal duties and penalties shown here. [source: app/i18n/method.py, method.legal.secrecy.]
> Under the GDPR, pseudonymization replaces identifying values, while keeping the information needed to restore them separately. The result remains personal data. It still needs protection. The mapping table must stay separate. Replacing a name does not remove every clue about the person. [source: app/i18n/method.py, method.legal.gdpr; README.md, Confidentiality and Limits.]

Silent legal card: **Law of 31 December 1971, art. 66-5; Penal Code, art. 226-13;
GDPR, art. 4(5) and recital 26**. Use these references as displayed in `app/i18n/method.py`.
`docs/RESEARCH.md` is absent. Omit the March 2026 CNB guide, market statistics and named competitors.
No external legal research or independent legal verification was performed in this writing session.

## 3. Name and promise | 0:50-1:05

> HuisClos, pronounced wee-kloh, means a hearing behind closed doors. The closed door and keyhole in our logo express the promise: keep client identities inside the room while preparing a text for AI. [source: S61 session brief, Name and promise; docs/DECISIONS.md, D-FIX5-1; README.md, How it works.]

Silent title card: use the existing `app/assets/logo.svg`, **HuisClos**, and the exact tagline,
**Use generative AI on client files without breaching professional secrecy.**
Return to the matching Import header. The tagline is an aim, qualified by the limits in blocks 4 and 7.

## 4. Live demo | 1:05-3:00

> I choose Load sample case. This public demo processes text on its server, so real files belong in a local installation. We use Standard, with a French document. Interface language, document language and token labels are separate settings. [source: app/i18n/workflow_import.py, import.sample.button and import.privacy.demo; README.md, Confidentiality and What HuisClos does.]
> I append an invented collection code, then detect sensitive data. In Review, coloured labels show each proposed value and its type. I read the whole document, including unmarked passages. [source: docs/PROGRESS.md, S14 demonstration note; app/i18n/workflow_review.py, review.intro and review.tag.*.]
> For this fictional example, I uncheck the employer. Keeping a real employer visible could identify the client. Next, I add the collection code as Other identifier and choose Add and mask everywhere. [source: data/samples/demo_case_fr.txt, employer; app/i18n/workflow_review.py, review.column.mask.help and review.manual.*; README.md, Limits.]
> Pseudonymize replaces accepted values with consistent labels. The same person keeps the same token within this document. [source: README.md, What HuisClos does and How it works.]
> I check the document together with my instruction. I deliberately put the fictional client's name in the instruction. The final check flags it. I remove it and read the complete message again. Edits require a new check before copying. An alert protects nothing until someone acts. [source: results/recette8/report.md, local acceptance checks; app/i18n/workflow_check.py, check.intro and check.found.]
> Only the checked message goes into ChatGPT by copy and paste. I request a short summary with unchanged tokens. The optional Mistral connector stays off by default. [source: README.md, Confidentiality; app/i18n/workflow_restore.py, restore.send.instruction.en; S61 session brief, Live demo.]
> I bring the answer back and choose Restore. The table replaces tokens with their values. I read the restored answer and export it. [source: app/i18n/workflow_restore.py, restore.answer.* and restore.download.*.]
> That table links tokens to identities. Never send it to an AI tool. A saved case table helps reuse tokens across documents; continuity still needs checking. [source: README.md, What HuisClos does, Confidentiality and Limits.]

Silent preparation and actions:

- Use `https://huisclos.streamlit.app`, English UI, French document, Standard, default French token labels.
  Keep the public demo warning visible, including in zooms. Never select Enhanced on this demo.
- Load the sample, then append `Code de retrait : qx-74-zp.` in **Text to process**, in memory only.
  S14 proposed this fictional value for a manual addition. Confirm during rehearsal that it remains
  unmarked in the version being filmed; no fresh detector run was made for S61.
  If already marked, stop that take and prepare another visibly unmarked fictional addition;
  do not present an existing detection as a miss. Leave the sample file unchanged.
- Review every entity and unmarked passage. Uncheck **Mask** only for the invented
  `Atelier Martin des Nivelles SARL`. This is a teaching decision, with its disclosure risk stated aloud.
  Add `qx-74-zp` through **Value to mask**, **Type of this value** = **Other identifier**,
  then **Add and mask everywhere**. Click **Pseudonymize**.
- Under **Your instruction (sent after the text, checked with it)**, enter:
  `Summarize the dispute involving Pierre VERNOLAC in three short English sentences.
  Keep every bracketed token exactly as written; do not change, translate or invent tokens.`
  Show the instruction alert. Replace the entire instruction with:
  `Summarize the dispute in three short English sentences.
  Keep every bracketed token exactly as written; do not change, translate or invent tokens.`
  Wait for the refreshed check. Read both message segments. Resolve every remaining alert
  by masking a private value, editing the instruction, or making an explicit contextual decision
  using **I reviewed this mention in its context: keep it in clear**. Never send an unresolved alert.
- Copy only the enabled, checked message with its top-right copy control. Paste it unchanged
  into ChatGPT. Never paste the source text, a mapping table or additional identifiers.
  No Mistral key, consent or send action is used. Capture an actual fictional exchange during filming;
  S61 itself sends no request. Cut waiting time with a visible **Waiting time shortened** caption.
- Paste the actual answer into **Answer from the AI tool**, click **Restore**, read the result,
  then click **Restored text (.docx)**. Show the sensitive-file warning beside
  **Mapping table (.mapping.json)** without opening or exposing that table.
- Mention case reuse over the table warning; a second French document is outside this timed take.
  Token continuity has the file-name/name limitation recorded in `README.md`, Limits.

## 5. Under the hood | 3:00-3:45

> Detection combines check digits, text patterns, name clues and pretrained entity recognition: a model that labels names. A network blocking test checks local processing. Consistent tokens preserve references. [source: README.md, How it works; AGENTS.md, sections 2 and 3.]
> We chose the threshold, the cutoff for accepting proposed detections, using F two, a score favouring fewer missed identifiers over fewer false alarms. Challenge documents were written blind after the rules froze; G8R2 reused that known set. [source: app/i18n/evaluation.py, evaluation.choice; results/summary.md; results/gate8-resume/report.md, Registre et méthode.]
> Its French results are on screen. The coverage gain is not statistically significant. French Enhanced is a local option. G8 results describe historical code. [source: README.md, G8R2 and Historical G8 blind results.]
> English Standard remains experimental with strong reservations; English Enhanced is experimental and not recommended. [source: docs/DECISIONS.md, D-G8R2-1 and D-R8-1.]

Silent diagram: **Check digits + patterns + name clues + pretrained name model -> review ->
consistent tokens -> final message check -> AI answer -> restore**. The table stays separate.
Explain check digits visually as an identifier's built-in arithmetic check, patterns as expected text
formats, name clues as context rules, and the pretrained model as software trained to label names.
The no-network test concerns local application processing; the public demo uses a hosting server,
and the deliberate ChatGPT exchange uses the network.

Show this card, rather than the application's historical Evaluation table:

**G8R2 French challenge: 8 fictional documents, already known; measured code 930c414. Before human review.**

| Profile | Fully covered entities | Leaked characters | Partial precision | Non-sensitive characters masked |
| --- | ---: | ---: | ---: | ---: |
| Standard, default | 157/190 | 325/3600 | 0.8039 | 366 |
| Enhanced, local French option | 170/190 | 218/3600 | 0.8018 | 379 |

Source: `README.md`, G8R2; `results/gate8-resume/report.md`, Challenge FR courant.
Fully covered means no annotated character of that entity remains visible; leaked characters
are annotated characters left visible. Partial precision measures overlap-based detection correctness;
non-sensitive characters masked measure extra masking. These are different measures.
Footer: **Small fictional set. Coverage gain not statistically significant: paired interval [0; 0.1667].
Leakage reduction interval excludes zero: [-0.0618; -0.0065]. Alerts alone mask nothing.**
No universal accuracy, no significant coverage claim, and no new blind status for G8R2.

During the historical-code sentence, show **G8: historical results, e3d13bd; not a new validation of current code**.
Finish with a separate, prepared Standard English view using only the translated fictional sample fragment:
`Client: Mr Pierre VERNOLAC. Email: pierre.vernolac@example.org.`
Keep **Document language: English**, the English experimental warning overlay and the public demo warning visible.
Do not run or show Enhanced English as a recommended demonstration.

## 6. Value and competition | 3:45-4:20

> The value case is qualitative. If this review became routine, legal teams could prepare AI requests without rebuilding every replacement by hand. Consistent tokens could make a file easier to follow across drafts. [source: qualitative proposal based on README.md, What HuisClos does; no productivity measurement.]
> The tradeoff is time spent reviewing detections, context and the final answer. Wider use could make careful preparation more consistent, while leaving responsibility with the professional. [source: qualitative proposal based on README.md, How it works and Limits.]
> Testing time savings and comparing competing products would require separate evidence. That work remains to be done. Its usefulness needs independent assessment. [source: S61 evidence boundary; docs/RESEARCH.md is absent.]

Silent card: **Proposed benefit: consistent preparation. Cost: human review.
Evidence needed: time study and sourced product comparison.**
Show manual preparation beside the HuisClos workflow as a conceptual comparison.
Do not imply a measured speed improvement, market estimate, compliance certification or superiority.
ChatGPT is the destination of this demonstration, not a benchmarked competitor.

## 7. Limits and close | 4:20-4:45

> Context can still identify someone. Pseudonymization is not anonymization, and no score guarantees zero leakage. French support is validated only within the measured scope; bilingual validation is incomplete. [source: README.md, Current status, Confidentiality and Limits; docs/DECISIONS.md, D-G8R2-1.]
> Review every detection and the final answer. The human remains responsible. Try the public demo with fictional data, or inspect the code at the addresses on screen. [source: README.md, introduction, How it works, Confidentiality and Limits; S61 session brief, closing addresses.]

Silent end card, held through 4:45:

- **HuisClos** and the existing logo.
- **Human review required. Pseudonymization is not anonymization.**
- **Public demo: fictitious data only. Real client files: local installation.**
- **App: https://huisclos.streamlit.app**
- **Code: https://github.com/Negan-san/huisclos**

No filming, external AI request, reserved-corpus access, evaluation or pilot was performed for S61.
