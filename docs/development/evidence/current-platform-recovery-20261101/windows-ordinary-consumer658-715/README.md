# Ordinary Windows consumer — exact source adoption

This isolated related patch adds a proper Maven consumer of the production
WebView/JavaFX artifacts and a manual Windows verification route. It does not use
the sample applications or rerun the previously accepted private Windows Stop
case. Public package/API identities, minimum permissions and publishing gates
are unchanged.

## Changes and review

- Sixteen exact source files / 244,940 bytes: one existing workflow derivative
  and fifteen additions. Existing `0644` is preserved; additions are `0644`.
- Raw JUnit report bytes are exclusively retained and bound to graph/verifier
  input bytes and closed-file identities; report substitution is refused.
- Independent final source/results review: [`review705/FINAL16-SPARSE-WORKTREE-SOURCE-ADOPTION-ACCEPTANCE705.json`](review705/FINAL16-SPARSE-WORKTREE-SOURCE-ADOPTION-ACCEPTANCE705.json),
  SHA-256 `7e6fb477ccb2eff1c0d5329513457454d3abfda4346df69ac09608ea3641e4c3`.
- Actual lead prewrite/adoption: [`lead715/ACTUAL-SOURCE-ADOPTION715.json`](lead715/ACTUAL-SOURCE-ADOPTION715.json).
  The separate ROOT producer/Camera/Android source cohort was not changed.

## Test chronology — no accepted replay

Original FIRST10 was nine passes/one failure. The failed formatter case and one
changed workflow case subsequently passed 2/2. Original report-custody3 remains
one pass/one error/one failure. Only its two failed controls passed after the
structural correction: **2/2 once**, 0.046s suite / 0.165125s wrapper; all 61
finite inputs and seventeen named absences held. Passing graph-coupling controls,
other unchanged source controls, Actionlint and private Windows Stop evidence
are reused within their unchanged scope, not fresh executions.

## Limits and next gate

This is **source-only acceptance**: zero compiler, staged artifact, Windows
native or ordinary consumer executions. The sparse worktree's absent local
prerequisite files do not certify a full checkout. Issue #64 and consumer,
dependency verification, source/legal, API/ABI, memory/process-lifecycle,
security and release requirements remain open.

After applicable compiler preparation and the complete successful ROOT
producer/same-HEAD Camera/Android cohort, dispatch only the exact manual
`windows-ordinary-consumer1` route with branch/head/input readback and at most
two combined hosted reservations, including queued work. Inspect fresh original
reports and consumer behavior before any issue closure. No publishing, release,
deployment, Pages, main or history mutation is authorized by this patch.

`ARCHIVE-MANIFEST.json` and `SHA256SUMS` retain 170 byte-identical original,
successor, donor and reviewer/adoption records. Historical failures and mode/path
refusals are preserved; archival observations are not instructions to execute
their embedded commands.
