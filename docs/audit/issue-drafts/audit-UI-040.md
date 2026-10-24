# [High][UI-040] calf-ui test coverage omits all native managers and most interactive control families

<!-- nativecmpkit-item:audit:UI-040 -->
## Classification
- **Finding:** UI-040
- **Priority:** High
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsTest.kt:12-110`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBoundsTest.kt#L12-L110) — `DateBoundsTest`
- [`calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerStateMaterialTest.kt:22-172`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerStateMaterialTest.kt#L22-L172) — `AdaptiveDatePickerStateMaterialTest`
- [`calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickableMaterialTest.kt:19-153`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/gesture/AdaptiveClickableMaterialTest.kt#L19-L153) — `AdaptiveClickableMaterialTest`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt:24-219`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt#L24-L219) — `AlertDialogManager`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt:29-167`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt#L29-L167) — `BottomSheetManager`

## Root cause
The baseline has32 common algorithm/action tests and37 desktop Material tests, concentrated on dates, dialog button construction/rendering and adaptiveClickable. There are no calf-ui iosTest/Android instrumentation test sources, and no tests for time pickers, native modals/bars/menus, images, sliders, switches or animation ownership.

## Impact and preconditions
Native lifecycle, accessibility, interop and dynamic-state defects have no executable regression protection. Passing common/desktop tests alone cannot substantiate iOS support or general UI correctness.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Baseline inventory contains5 commonTest files(4 test classes) and6 desktopTest files(5 test classes), with69 @Test annotations total.
- No other calf-ui test source sets contain tracked tests.

## Recommended solution
Add a prioritized native/Compose test program using the per-finding cases and docs/testing/ui.md. Start with lifecycle/callback correctness, controlled-state/accessibility contracts and date calendar boundaries; keep source probes separate from real target tests.

## Risks and compatibility
Test inventory counts are not passing-test counts. Apple devices/toolchains are unavailable in this Linux audit; CI additions must not enable publication and must use feasible resource budgets.

## Required tests / acceptance criteria
- iOS simulator and iPad device suites for native modal lifecycle and callbacks.
- Compose control semantics/pointer cancellation/state replacement tests.
- Cross-platform contract tests plus visual/performance baselines; recorded command/result evidence.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
