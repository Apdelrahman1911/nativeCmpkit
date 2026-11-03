# Shared Worker memory / independent XCTest startup recovery — 433–436

## Actual originals, reviewed once before edits

- [41567513880](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41567513880):
  **FAILED, native2 /1pass /1fail, XML1, Gradle1, 1398.63s** at `510f2531c109`.
  Accept/exclude `repeatedDisposalDuringBothNativeAnimationsLeavesNoWaiterOrCapturedContent`:
  all four alternating real show/hide disposal/GC cycles pass. Public composition
  disposal still fails its original captured-owner weak check after three Main GC
  passes. Prior disposal/detachment/native disappearance/callback checks pass;
  reopen tail is unreached. Real Main/Worker completion, native transport and all
  four owned-app cleanup witnesses pass independently. **#31 remains open**;
  remaining retention chain/persistent heap growth are unproven.
- [41567531261](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41567531261):
  **FAILED before library launch, ZERO library methods/XML/input, Gradle1,
  1491.28s** at the same revision. Independent Swift `build-for-testing` passes
  **0 /52.483s**, copied inputs and runner identity hold. Failure is
  `runner-readiness`; original exit-vs-timeout/startup cause is unknown. There is
  no post-launch runtime/binary witness or application protocol. All eight owning
  input/app cleanup witnesses pass. ZERO library methods does **not** establish
  ZERO independent XCTest runner code execution. No iPad dispatch against this
  known failed startup. The honest pre-launch review never invents XML/launch.

Both originals hold all **1,246 actual input maps** against the frozen own-Git
blobs. ZIPs/logs were acquired once and remain private; exact member hashes,
original receipts and selected JSON/XML are retained here. No raw private Xcode
logs/configuration/authentication, apps/packages or screenshots are uploaded.

## Coordinated test/tooling patch

- Worker `onApplicationMain` now owns an explicit autorelease pool around its
  Objective-C synchronous dispatch bridge. Main inline execution, exact Result/
  Throwable identity, native window/lifecycle predicates and every original
  lifecycle body remain unchanged. The Worker-vs-Main capture origin is a
  plausible harness-retention hypothesis, **not a confirmed old failure chain**.
- Two NEW library-level controls isolate a plain root capture (no sheet) and
  exact Main value/throwable propagation. `ios-modal-worker-memory-recovery`
  selects only those two plus the failed public sheet method; accepted repeated
  disposal and presenter/state-replacement methods are excluded.
- XCTest setup/transport now provides bounded fixed-phase/typed OS-code
  observations and independent actual process-exit/deadline operands. Scheme
  credentials use `EnvironmentVariables`, preserving Xcode's separate testing
  paths; both environment fields are documented, so the old failure cause is
  **not inferred** from this change. Existing credentials and foreign AUT launch
  configuration are refused before mutation.
- `ios-xctest-startup` compiles/runs the exact shared Swift UI runner/server/
  owning cleanup independently, with no Kotlin/Gradle/Java/Rust setup, installed
  AUT, fabricated signed hashes, library input, library XML or package. It can
  establish only startup/completion. Its first poll requests finish with zero
  operations and never certifies library `verified=true`. One fixed actual
  simulator is restored only if this job originally booted it.
- Six exact **23-fragment** owning inverses preserve historical pins. The terminal
  AWT helper, production sources, dependencies and public APIs remain unchanged.

## Important local checks — not native acceptance

- NEW10 +affected5 **15/15 once**, unittest0.313s/wrapper0.567079s, **1,252 held**.
  No accepted local population replayed. One additional NEW SHA1 control **1/1**
  corrects a self-reviewed pre-dispatch SHA1-vs-SHA256 startup validator defect;
  no startup/native execution had occurred. Its first defect record is retained.
- Fresh exact four-source iOS test KLIB **Gradle0 /36.771s**, JDK17/Gradle9.7.1,
  production UP-TO-DATE, all1,252 inputs held. Native-disabled/cross-compile
  warnings remain in the original log. **ZERO Apple link/Swift/XCTest/native**
  locally. Later route/control-only SHA1 edits do not change compiler inputs.
- Actionlint0, four passive source plans and exact old alert-source bindings pass.
  These are not executed native/control populations or readiness certification.

## Next verification / issue boundaries

Freeze/push development only; freshly reconcile maximum two combined hosted-heavy
reservations INCLUDING queued. Request missing memory3 and independent startup
only. After startup is accepted, request genuine seven-case iPhone input, then
missing iPad7 after capacity frees. Review original criteria once and close every
complete sibling immediately; **none newly complete at this preparation**.
#28/#30/#31/#125/#126 stay open. Reuse accepted native/source/compiler evidence
only within its stated unchanged applicable scope, never as a fresh result.

98closed/74open/172;22implemented/41partial/96verified/five unresolved. SOLO,
serial local/8GiB reserve/read-only Actions/all/no mandatory SHA pinning. All
publishing/Pages/main/history/legal/security/consumer/API–ABI/readiness gates
remain; no packages/releases/deployment publication.
