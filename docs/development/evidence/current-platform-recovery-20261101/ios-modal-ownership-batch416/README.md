# Shared iOS modal ownership patch — 2026-11-03

Related issues: **#28, #30, #31, #125, #126**. One production patch, one focused
native selection, one results review; close all fully verified issues together.
No issue is closed by this preparation.

## Root causes and changes

- `SheetState.ios.kt`: a mutex held across suspended native operations prevented
  hide from withdrawing a show queued behind another modal. Retain Main confinement
  and the current confirmation/skip policy, but serialize intent updates rather
  than the entire animation.
- `BottomSheetManager.kt`: remove unadmitted shows from the actual ownership queue;
  cancel their show waiters and complete hidden waiters. Alternating show/hide/show
  or hide/show/hide cancels only the superseded **unstarted** middle transition;
  admitted animation callers still await their native completion.
- `AlertDialogManager.kt`: queued dismiss/rebuild/disposal withdraws the stale
  controller without dismissing the actual blocking owner's modal. User dismissal
  notification remains separate from cleanup.
- `NativePresentationState.kt`: precise queued cancellation invalidates the old
  generation only after the driver proves real queue removal. It cannot stand in
  for an admitted UIKit animation or interactive dismissal.

Public signatures/packages, dependencies, licensing and attribution are unchanged.
An unstarted superseded sheet request now throws `CancellationException`, rather
than waiting forever or reporting a presentation that never occurred.

## Important verification

See [local-verification.json](local-verification.json) and the original XML/logs.

- Fresh common state tests: **4/4**, no failures/skips; Gradle0 /59.02s.
- Fresh iOS production/test KLIB recovery: **exit0 /56.01s**, 1,226 inputs held.
  The initial new-test missing `kotlinx.coroutines.IO` import failure remains
  preserved (exit1 /51.01s). Later tooling-only changes do not require recompilation.
- Four current routing/history controls qualify; retain the first new plan-control
  keyword error and its failed-method-only correction. Actionlint1.7.12 and both
  finite real source plans pass after retained PATH/CLI operational refusals.
- Seven sources/13 exact reversible fragments allow old offline fixture readers
  to retain their original pins. Actual native selection uses current sources,
  not this projection; passive old alert/TLS source admission qualifies.
- **Nine genuine UIKit application tests prepared; zero executed locally.**
  Profiles `ios-modal-ownership-batch` and `ios-modal-ownership-ipad` each select
  only those nine new methods on one real host. Accepted legacy tests are excluded.

## Remaining acceptance

### First CI tooling failure repaired together

[41551470920](https://github.com/Apdelrahman1911/nativeCmpkit/actions/runs/41551470920)
at `d961cab9` failed **before** platform selection: 2,470 CI fixture methods,
10 failure records across four methods. Three historical readers compared newer
raw modal sources against older stage pins or expected the older refusal stage.
All four failed methods now pass together (**4/4 /0.855s**); original pins,
other method bodies, live workflow permissions and native tests are unchanged.
See [the once-acquired originals and review](ci-tooling-recovery/review.json).
Zero library Gradle/native/XML; reuse the accepted local compiler/common results.

Native queued/concurrent/cancellation/GC outcomes await the immutable hosted run.
The four original #28 accessibility-activation failures remain failed: this patch
does not diagnose their observation/input problem. Inside/outside touches, actual
detent dragging, complete parent replacement and iPad adaptation are separate
original requirements, not inferred from compilation or controlled callbacks.

Current **98 closed /74 open /172 total**. Solo execution, serial local heavy
builds/8GiB reserve and maximum two combined hosted-heavy reservations including
queued work remain. Development branch only; no package/release/deploy/Pages/main
publication or security/readiness waiver.
