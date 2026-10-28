# FIX3R independent recheck

Verdict: **NO-GO for FIX3**. The token substitution correction is verified, but FIX3R-01
violates the required Review error contract: a previous pseudonymization result survives
a failed retry. A challenge measurement by a separate gate session is **not authorized**
by this recheck. No reserved measurement was performed.

## 1. Frozen reference and scope

The initial working tree was clean on lane-b at
`ae5dfe97ed8236bfa7a00aac4daefbd8074ccd7b`. `git merge dev --no-edit` fast-forwarded
without conflict to the required `bbfc6c12f069808c05b678faafc3024514c6ae77`.

[scope.json](scope.json) verifies the exact nine-file list from
`git diff ae5dfe9..bbfc6c1 --name-only`: tokens.py, workflow_review.py, review_step.py,
test_tokens.py, test_fix2.py, test_case_memory.py and the three session documents.
No other path changed in FIX3.

The check used a separate temporary Git index, applied the archived FIX2 patch to the
base index, then amended exactly one docstring line in memory. The following are Git blob
identifiers, computed from bytes, rather than a visual comparison:

| State of tokens.py | Blob |
| --- | --- |
| Base ae5dfe9 | `48df79d5dc19bed0549a3688e161ae2edc7d44a0` |
| Base plus unmodified FIX2 patch | `ea94c160dced2c6b001cd1e2fd0f3ae98f15f00f` |
| Predicted patch plus docstring amendment | `a2d698a980c21481c454e543759cca9d6e6b00d1` |
| Actual FIX3 | `a2d698a980c21481c454e543759cca9d6e6b00d1` |

The two final identifiers match. The index directory was removed automatically.

## 2. Required controls

| Control | Result | Evidence |
| --- | --- | --- |
| Complete pytest collection | 1720 passed, zero xfail | [pytest.log](pytest.log) |
| Ruff check | Exit 0 | [ruff-check.log](ruff-check.log) |
| Ruff format --check | Exit 0 | [ruff-format.log](ruff-format.log) |
| check_style.py | Zero errors, 15 existing length warnings | [style.log](style.log) |
| Git diff whitespace | Exit 0, including staged files | [diff-check.log](diff-check.log), [staged-diff-check.log](staged-diff-check.log) |

Scope qualification: ordinary pytest would read the reserved test split through
`tests/test_roundtrip_corpus.py::roundtrip_inputs`. The session explicitly forbids that
execution. [guarded_pytest.py](guarded_pytest.py) keeps every collected test and assertion,
but restricts that fixture's input list to dev. It also refuses opening other corpus paths,
except english_dev and the eight explicitly documented dev sources used by editorial
tests. The final run refused zero opens. Thus 1720 is a full test count with a reduced
data scope for the corpus roundtrip, not an unrestricted replay of FIX3's corpus reads.

The first guarded run refused eight dev-source reads because the guard was too broad:
1712 passed and eight policy failures, retained in [pytest-initial.log](pytest-initial.log).
Reading the editorial test established that doc_19 through doc_26 are dev-only; only these
eight paths were added to the allowlist. No reserved file was opened to make this change.
The final run reports the existing Torch deprecation and pytest-cache permission warnings.
The first staged whitespace check rejected Windows carriage returns in captured logs.
Raw captures are retained as .log.raw; normalize_logs.py converts readable copies to
UTF-8/LF and removes trailing whitespace. The failed staged check is retained separately.

## 3. Six red/green regressions

An external temporary worktree at bbfc6c1 was created with a sparse checkout excluding
the entire corpus directory. Only its tokens.py was replaced with the ae5dfe9 blob.
The following six tests failed; replacing that file with the bbfc6c1 blob made all six pass:

- Three parameterized text/file-name cases in test_fix2.
- The real Review-to-Restore file-name workflow in test_fix2.
- Position-based assignment of two tokens to one spelling in test_tokens.
- Loss of case-memory token continuity in test_case_memory.

Evidence: [six-before.log](six-before.log), [six-after.log](six-after.log),
[regressions.json](regressions.json). The old run exited 1 with six failures; the corrected
run exited 0 with six passes. The worktree was removed in a finally block, its absolute
target was verified before removal, and its absence from disk and the worktree registry
was checked. The pre-existing G7 reference worktree was left intact.

## 4. New Standard FR/EN reproductions

[pipeline_probes.py](pipeline_probes.py) contains new fictional identities and company
names, different from FIX2, FIX2R and FIX3. Each language uses the real Standard profile,
spaCy, the detection pipeline, grouping, Presidio, mapping serialization and restoration.
DNS and network connections are blocked during these probes.

All **20 required cases pass** in [pipeline.json](pipeline.json): seven cases in each
language, plus three controls without any file name in each language.

| Case, repeated in FR and EN | Expected occurrences | Required checks |
| --- | --- | --- |
| Name in prose and a file name | 3 | No original value, exact restoration, separate file token |
| Defined acronym in a file name | 3 | No original value, exact restoration, separate file token |
| Same name in two file names | 2 | No original value, exact restoration, distinct file token |
| Name only in a file name | 1 | No original value, exact restoration |
| Adjacent EMAIL mentions separated by one space | 2 | Separate occurrences, exact restoration |
| English token style | 3 | English label for each actual entity type |
| Case table loaded through read_table_file, known= | 3 | Original prose token reused |
| Person control, no file name | 2 | No original value, exact restoration |
| Organization/alias control, no file name | 2 | No original value, exact restoration |
| Email control, no file name | 1 | No original value, exact restoration |

For each row, occurrence count equals the explicit fixture expectation and detection
count; every recorded original and output token is checked against its detection and
output slice. Every permutation of the supplied detections is replayed with a fixed
timestamp: **68 input orders** across the 20 required cases produce identical complete
results, including the mapping. Token labels follow the detected type; an English
file-name occurrence can be classified as an organization without exposing its value.

Two additional exploratory numeric-suffix fixtures are retained. EN has three detections;
FR has four instead of the initial expectation of three. Its count assertion is red, while
all original-value, restoration, alignment and 24-order determinism checks pass. This is
additional masking, not a demonstrated FIX3 substitution regression. Detection was not
adjusted. The script reports this failure rather than silently changing its expectation.

Initial probe outputs are preserved in pipeline-initial.json, pipeline-second.json and
memory-initial.json. Initial extra assertions incorrectly assumed a PERSON label for
every English file-name occurrence and one merged group for every known-table case.
Those assumptions are not the application contract: the final required checks verify the
actual type's English label and reuse of the known prose token. NER can include a file
extension or classify a file fragment differently; no exact-spelling collision is claimed
for these broad automatic spans. The six regressions and controlled memory cases isolate
the exact-spelling collision independently.

## 5. Presidio invariants and G8 diagnostic

The fake engine in pipeline_probes.py uses monkeypatch on tokens._engine. One response
omits an item; another substitutes a wrong item token. Both raise RuntimeError, and both
verify merge_entities_with_spaces=False. The unchanged code also checks the output slice
against the expected token. [invariants.json](invariants.json) records only the error class
and actual code locations: tokens.py:_substitute:171 and :176.

This also establishes that the G8 location diagnostic resolves the current function.
The obsolete _token_tables:140 example in scripts/gate8_measure.py is **non-blocking**:
it is a docstring example, while code_location reads the traceback and validates its
actual path, function and line. The file was not modified.

## 6. D-FIX3-2: acceptable continuity limit

[memory.json](memory.json) confirms the effect independently for FR and EN, using new
controlled automatic detections to isolate grouping from NER span/type variation. This
is explicitly a substitution/memory probe, separate from the real Standard matrix.

Two entries share a surname spelling after one prose/file document. A subsequent full
name alone keeps its old token. A surname alone receives a new token because two entries
match. Two people with the same surname and different given names keep distinct tokens,
including when a file name carries the shared surname. The merged table restores a
response mixing the original person's token, the new surname token and the second
person's token in tolerant mode, with the expected canonical forms and no unknown token.
Exact restoration and absence of the original surname also pass.

Acceptance is reasonable for this limited behavior: continuity is lost conservatively,
not replaced with a guessed identity. The table and human review remain necessary.
These tests do not establish identity resolution for two people with identical complete
names. The optional schema/origin redesign described in D-FIX3-2 remains outside scope.

## 7. D-FIX3-3 and blocking finding FIX3R-01

Four fresh AppTest cases pass: RuntimeError and ValueError, each in FR and EN, with the
document language matched to the UI language. RuntimeError displays exactly
review.error.substitution; ValueError keeps review.error.pseudonymize. Review remains
open, no result is stored, no uncaught exception appears, and the fictional exception
mention is absent from error/info/warning/success messages, captured logs, stdout and
stderr. The legitimate source preview is not treated as an error message.

**FIX3R-01: a failed retry retains the previous pseudo_result (FR and EN).**

Reproduction uses only normal navigation before injection:

1. Import a new fictional document and run real Standard detection.
2. Click Pseudonymize successfully; the app reaches Restore with a valid result.
3. Click restore_back_review without editing any detection.
4. Force tokens._substitute to raise RuntimeError containing a fictional surname.
5. Click review_pseudonymize again.

The expected error is displayed safely and Review remains open, but pseudo_result still
equals the result from step 2. This violates the requested condition that no
pseudonymization result remain in session and weakens the message that nothing was
produced. No leak or external send is demonstrated. The failing branches in
review_step._pseudonymize return without clearing existing results; go_to only changes
the step. [ui.json](ui.json) records previous_result_retained=true for both retry cases.
No production correction was made. A future authorized correction must invalidate the
previous result on this error path and add regression coverage for the retry workflow.

## 8. G8 worker and handover

The actual separate G8 worker succeeds on a new fictional prose/file fixture in FR and
EN: one document, three detections and three substitutions per process; network blocked
and final check available. Only counts and booleans are exported in
[worker.json](worker.json); no document, mapping, position or worker payload is archived.

Run the local harness with the prescribed Python interpreter:
`PY results/fix3-recheck/check_controls.py scope`, then `regressions` or `checks`.
`PY results/fix3-recheck/recheck_fix3.py <pipeline|memory|invariants|ui|worker>` regenerates
the probe JSON; pipeline and ui exit 1 for the retained findings. summarize.py consolidates
the final staged audit into [summary.json](summary.json).

D-FIX3R-1 records NO-GO. A separate challenge gate is not authorized until FIX3R-01 is
corrected and independently rechecked. The global NO-GO and the existing Enhanced EN
recommendation restriction remain. No test, challenge, C3 or all evaluation, reserved
file opening or hashing, detection tuning, package installation, tag, push or R8 occurred.
Only results/fix3-recheck and the three authorized documents were changed in this session.
