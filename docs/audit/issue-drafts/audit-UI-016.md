# [Medium][UI-016] iOS sheet programmatic transitions bypass confirmValueChange and skipHiddenState

<!-- nativecmpkit-item:audit:UI-016 -->
## Classification
- **Finding:** UI-016
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt:25-36,61-99`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt#L25-L36) — `AdaptiveSheetState.show / hide`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt:154-164`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt#L154-L164) — `BottomSheetControllerDelegate`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt:30-43,67-98`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt#L30-L43) — `AdaptiveBottomSheet`

## Root cause
confirmValueChange is consulted only by presentationControllerShouldDismiss for interactive dismissal. show/hide do not call it; skipHiddenState is checked only against the initial value and not retained. ModalBottomSheetProperties is accepted by the iOS facade but not applied.

## Impact and preconditions
A sheet can close programmatically despite a veto used to protect an unfinished form, or enter Hidden despite skipHiddenState. Modal dismissal-property expectations differ silently from Material.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- SheetState.show/hide call manager directly; the only confirmValueChange invocation is in the interactive native delegate.

## Recommended solution
Define a single transition-policy gate for all user/programmatic transitions and honor skip flags. Explicitly map supported ModalBottomSheetProperties or document unsupported platform-only behavior.

## Risks and compatibility
Forcing a cleanup dismissal on disposal must remain possible without triggering business callbacks; policy and resource release should be distinct. Positional/velocity thresholds are Material-specific and need not be emulated blindly.

## Required tests / acceptance criteria
- Veto Hidden/Expanded independently for show/hide/drag/outside dismissal.
- skipHiddenState=true with permitted initial state; confirm no forbidden transition.
- Dismissal properties and disposal cleanup policy on iPhone/iPad.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/116
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
