# [High][UI-031] Cancelled pointer gestures can commit a Liquid Glass switch toggle

<!-- nativecmpkit-item:audit:UI-031 -->
## Classification
- **Finding:** UI-031
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt:66-82`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt#L66-L82) — `modifier onDragEnd / onDragCancel`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DragGestureInspector.kt:21-38,52-58`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DragGestureInspector.kt#L21-L38) — `inspectDragGestures / drag`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt:103-123`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt#L103-L123) — `onDragStopped`

## Root cause
DampedDragAnimation routes both drag end and cancellation through the same committing onDragStopped callback. The inspector begins immediately on down, without touch slop, and cancels when another recognizer consumes a change; the switch toggles even when didDrag is false.

## Impact and preconditions
A parent scroll recognizer winning the gesture or another pointer cancellation can change application state although the user did not complete a switch activation. Sliders also emit finish/commit callbacks on cancellation.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- onDragCancel calls onDragStopped exactly as onDragEnd does.
- inspectDragGestures calls onDrag with Offset.Zero on first down and returns cancellation when change.isConsumed.

## Recommended solution
Separate cancel from commit in the gesture contract, restore authoritative state on cancellation and arbitrate slop/consumption with standard gesture facilities. Ensure cancellation does not invoke business callbacks.

## Risks and compatibility
The callback-routing defect is source-confirmed; exact nested-scroll/pointer event reproduction requires Compose iOS. Avoid altering normal tap behavior while adding slop handling.

## Required tests / acceptance criteria
- Start on thumb then scroll vertically so parent consumes; no toggle callback.
- Pointer removed/cancelled, second pointer handoff, composable disposal and disabled transition mid-gesture.
- Successful tap/drag each commits exactly once.

## Dependencies
- UI-030

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
