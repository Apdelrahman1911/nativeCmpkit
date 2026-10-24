# [Medium][UI-017] iOS sheet state never tracks partial detents or interactive dismissal and uses reversed detent order

<!-- nativecmpkit-item:audit:UI-017 -->
## Classification
- **Finding:** UI-017
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt:39-44,61-99`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt#L39-L44) — `iosCurrentValue / iosTargetValue / show / hide`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt:53-60,100-109,154-164`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt#L53-L60) — `presentationControllerDelegate / show`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt:67-77`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt#L67-L77) — `sheetManager onDismiss`

## Root cause
The native detent list is large then medium rather than ascending order. State.show always records Expanded, there is no selectedDetentIdentifier change observer, and interactive dismissal changes only manager.isPresented/onDismissRequest, not the shared state.

## Impact and preconditions
currentValue/targetValue/isVisible can disagree with the native sheet. Code awaiting show cannot rely on the documented partial-if-available result; detent ordering may impair UIKit behavior.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- No assignment to PartiallyExpanded or native selected-detent observer exists.
- onDismiss closure only invokes onDismissRequestState; show completion sets Expanded unconditionally.
- Historicalecf81868aa95c2d336b56a52785a630272a3e4c9 introduced the current large/medium ordering.

## Recommended solution
Supply detents in ascending order, set the intended initial detent and observe native detent changes. Route presentation/dismissal delegate events through one state synchronizer before notifying callers.

## Risks and compatibility
Native visual outcome of reversed order is not tested. Caller removal currently masks stale isVisible through disposal; test both removal and retaining the composable after dismissal.

## Required tests / acceptance criteria
- Show with and without partial detent; drag medium-to-large and back while observing state.
- Interactive dismissal without removing composition must set Hidden.
- Save/restore all supported SheetValue values and iPad adaptation.

## Dependencies
- UI-016

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
