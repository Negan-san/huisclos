# AI prompts log

This file records every prompt given to an AI tool while building HuisClos, as the assignment requires ("show us where and how you used such tools by reporting the prompts used").

- Planning prompt, verbatim: docs/prompts/00_master_prompt.md, sent to Claude (claude.ai, Opus 5.5) on 27 October 2026.
- Session prompts, verbatim: docs/MASTER_PLAN.md, one card per session (S01 to S73, gates G0 to GF).
- Follow-up prompts given during a session, and prompts given to other tools (ChatGPT for the corpus and the research, video tools), are copied verbatim in the table below or saved in docs/prompts/.

| Date and time (Paris) | Session | Tool and model | Prompt reference | Follow-up prompts (verbatim) or notes |
| --- | --- | --- | --- | --- |
| 2026-10-27 11:28 | Plan | Claude (claude.ai), Opus 5.5 | docs/prompts/00_master_prompt.md | Produced docs/MASTER_PLAN.md |
| 2026-10-27 14:45 | S11 / H1 batch 1 | Codex (model not exposed) | docs/prompts/corpus_lot_1.md | Generation prompt and follow-up copied verbatim; six fictional dev sources reviewed against A5 and saved as UTF-8. |
| 2026-10-27 14:34 | S01 | Claude Code, Sonnet 5.5 High | docs/MASTER_PLAN.md, card S01 | No follow-up prompt. |
| 2026-10-27 15:10 | PIL | Claude Code, Opus 5.5 | Demande de l'humain : déléguer la piste humaine | AGENTS.md sections 7, 11, 12 amendées. |
| 2026-10-27 15:13 | G0 | Codex (model not exposed) | docs/MASTER_PLAN.md, card G0; session request "[HuisClos] Gate 0 : contrôle du socle" | Follow-up (verbatim): "Resouds les conflits et relance le controle". Conflicts resolved with both histories retained; independent foundation review and offline checks completed. |
| 2026-10-27 15:35 | R0 | Claude Code, Haiku 5.5 | Session request "[HuisClos] Recette R0 : recette de la gate G0, fusion et tag" | No follow-up prompt. Merge of lane-b, fresh install, headless launch, AppTest and gate checks run by the agent. |
| 2026-10-27 15:36 | S12 | Claude Code, Sonnet 5.5 High | Session request "[HuisClos] Session S12 : NER française, heuristiques de personnes, exclusions" | No follow-up prompt. |
| 2026-10-27 15:38 | S11 | Codex | Session request "[HuisClos] Session S11 : validateurs et reconnaisseurs à motifs"; docs/MASTER_PLAN.md, card S11 | No follow-up prompt. Implemented local validators, deterministic synthetic generators and French Presidio recognizers; checked installed APIs, stdnum oracles, exact spans, confidence scores and offline execution. |
| 2026-10-27 15:54 | S13 | Claude Code, Opus 5.5 High | Session request "[HuisClos] Session S13 : fusion des détections, propagation, pipeline" | No follow-up prompt. Merged lane-b, built config, text utilities, merge rules 1 to 8, propagation, Presidio pipeline, detection CLI and the mini_case fixture with tests. |
