# [Medium][UI-030] Liquid Glass switch can visually diverge from its controlled checked value

<!-- nativecmpkit-item:audit:UI-030 -->
## Classification
- **Finding:** UI-030
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt:87-139,150-178`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt#L87-L139) — `fraction / DampedDragAnimation callbacks / LaunchedEffect`

## Root cause
The switch updates an internal fraction before optionally invoking onCheckedChange. Synchronization back to checked runs only in LaunchedEffect(checked). If the callback is null or the owner rejects the change and keeps checked unchanged, that effect does not restart; the independent fraction remains toggled.

## Impact and preconditions
A nominally read-only switch can animate to a different value, or a vetoed change looks accepted while semantics still report the original checked state. Only the thumb is clickable by the custom gesture path; tapping the empty track does nothing.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- onDragStopped writes fraction.value before currentOnCheckedChange?.invoke.
- LaunchedEffect is keyed only by checked; an unchanged value does not trigger reconciliation.

## Recommended solution
Treat checked as the authoritative state, distinguish preview from committed value and reconcile after every gesture, including rejected/null-callback cases. Attach toggle behavior to the full control with explicit read-only/disabled semantics.

## Risks and compatibility
Preserve smooth drag preview without silently making the control internally stateful. UI automation on iOS is required to prove final animation/semantics consistency.

## Required tests / acceptance criteria
- onCheckedChange=null, callback accepts, callback rejects, delayed owner update.
- Tap thumb and either end of track, drag across threshold then back, external checked update mid-gesture.
- Disabled gestures leave both visual and semantic state unchanged.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
