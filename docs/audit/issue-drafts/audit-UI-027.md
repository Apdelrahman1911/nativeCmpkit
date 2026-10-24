# [High][UI-027] Liquid Glass slider retains stale enabled, range, geometry and direction inside drag callbacks

<!-- nativecmpkit-item:audit:UI-027 -->
## Classification
- **Finding:** UI-027
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:95-176`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L95-L176) — `dampedDragAnimation / track pointerInput`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt:20-29,66-83`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt#L20-L29) — `DampedDragAnimation.modifier`

## Root cause
DampedDragAnimation is remembered only by animationScope and stores callbacks capturing the initial enabled, valueRange, trackWidth, thumbWidthPx and isLtr. The track pointerInput is keyed only by enabled. didDrag is set after motion but never reset for a new gesture; drag-stop callbacks are not enabled-guarded.

## Impact and preconditions
A slider initially enabled can continue sending thumb-drag changes after it is disabled; initially disabled can stay inert after enabling. Resizing, range replacement or RTL changes can yield wrong values. A later tap can reuse previous drag state.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- remember(animationScope) wraps callbacks using enabled/range/width/direction.
- Only onValueChange and onValueChangeFinished use rememberUpdatedState.
- didDrag has no reset assignment after its initial remember(false).

## Recommended solution
Separate stable gesture machinery from latest parameters via updated-state holders or complete keys; recreate range-bound animation state safely when range changes. Reset gesture-local flags on every start/cancel and consistently gate interactions/completion while disabled.

## Risks and compatibility
This confirms stale capture paths, not an executed iOS input test. Recreating state indiscriminately can interrupt active gestures; define transition/cancellation behavior explicitly.

## Required tests / acceptance criteria
- enabled true-to-false and false-to-true after first composition, during drag and while idle.
- Resize, density, RTL and valueRange changes without changing enabled.
- Drag then tap, callback replacement, disabled finish/cancel events.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/517
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
