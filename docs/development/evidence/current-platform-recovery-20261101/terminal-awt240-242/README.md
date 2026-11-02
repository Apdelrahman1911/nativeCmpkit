# Share terminal lifecycle and bounded desktop ownership — 240–243

**Unpublished, dirty development snapshot** based on8a2b307e. The
[solo lead review243](REPORT.json) records31 passive source/results checks and
1201 held final inputs in [the shared map](INPUTS.json); it is not a separate
agent review or security attestation. No issue is closed by this batch.

## Causes and owning corrections

- `ShareLauncher.ios.kt::IosShareOwner.Request.complete/release`: the old activity
  callback directly released controller/scopes before any owned dismissal barrier.
  The first terminal input now waits for actual presentation/dismissal completions.
  Owner disposal suppresses pending delivery; duplicates cannot replace it.
  Cleanup/owner invalidation precede callback/reentry. Whole callback state access
  and mapping run on main. Error→Failed, true→Completed, false→Dismissed and public
  signatures remain; **callback timing intentionally changes** to follow cleanup.
  Positive scope starts, recipient access and packaged API/ABI are unproved.
- `IosSharePresentationOwnershipTest.kt::publicRememberedShare…`: the
  [Share227 original](../share227-original238-239/README.md) supplied two true inputs
  only after programmatic dismissal had produced a false terminal. Ignoring those
  stale inputs was correct. The fixture now supplies its controlled **first** true
  input while presented and requires production's genuine UIKit dismissal before
  delivery. Original Main/Default/IO/current-callback/reentry/disposal expectations
  remain, strengthened with phase/native-absence assertions. No recipient success
  is inferred. Four new `ShareTerminalBarrierScenarios.kt` controlled Request cases
  execute **inside that one method**, not four additional JUnit executions. They
  cover both barriers/deduplication, pending-result suppression, release-before-
  reentry and a throwing callback; their barriers are explicitly controlled.
- `BoundedDesktopAwtWindow.kt` replaces fixture `invokeAndWait` with owned queued
  work. Creation waits30s/disposal10s; cancellation before entry allocates nothing;
  late constructor return disposes its exact window without configuring/showing
  it. Reentrant dispatch cannot release during initialization. Handles remain
  owned during disposal and after failure; a once-only attempt is not successful
  cleanup. Failed Stop's FX observer removal also has a10s cancellable wait.
  These bounds **cannot preempt blocked native calls**. Original Stop actions/six
  predicates/10s acceptance and redirect body remain unchanged. [Actual237](../windows-awt237/README.md)
  preserves scheduler/real-thread results and first-map custody limitations.

## Source composition and important results

The new inert projection admits14 explicitly listed tracked-source changes through
39 finite inverse fragments, whole hashes and exact forward round-trips. Historical
guards reconstruct their previous bytes **only for source checks**; native/library
tests never execute reconstructed code. Camera updates touch current shared
metadata only, not BEFORE47/original controls or the unknown admission cause.
The planner pins the AWT helper with selected Stop/redirect fixtures. Windows still
selects failed Stop1/one XML; Share selects failed public1, not its accepted12.
No workflow, dependency or public API-signature change belongs to this batch.

- [Source241](source-results241.json): first26 loader entries yield **24 actual
  passes**, including NEW8, plus two pre-execution AttributeErrors from incorrect
  lead class selectors. No test failed; unittest0.736s/wrapper1.168819s. Only the
  [corrected two](selector-recovery241.json) then pass2/2,0.083s/0.285364s.
  **26 cumulative unique controls, not a fresh full26 green suite**.1201 inputs
  hold across both; accepted24 were not replayed. [Original selection](initial-source-selection241.json)
  preserves both mistakes.
- [Compiler240](compiler-results240-242.json): fresh production/test Share KLIB
  succeeds, Gradle0/31.01s/1198 held. A subsequent readiness-predicate strengthening
  and owning source guards require the final compiler242.
- [Final242](compiler-results240-242.json): fresh test KLIB Gradle0/28.01s/1201 held;
  production UP-TO-DATE. Existing `IosShareRequestTest.kt:97` unused-expression
  warning remains. **ZERO Apple link/native executions locally.**
- Windows first NEW8 and later NEW9 pass in separate XMLs. First immediate-after
  map was not captured before two-file refinement: no current full-nine/native
  acceptance or first-map before/after equality is claimed.

## Missing acceptance

Freeze/push development only, then request genuine Windows Stop1 and Share public1.
Max2 combined hosted-heavy reservations includes queued work. Preserve failures;
acquire each terminal original once. #64/#81/#88/#48/#100 remain open until their
own criteria pass. Continue solo/serial local/8GiB. No packages/releases/deployments/
Pages, `main` integration, consumer/ABI/security/legal/readiness certification.
