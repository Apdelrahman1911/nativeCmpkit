# [Medium][UI-032] Liquid Glass slider arithmetic does not guard zero-length or invalid numeric ranges

<!-- nativecmpkit-item:audit:UI-032 -->
## Classification
- **Finding:** UI-032
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt:43-59,95-102,134-140`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/DampedDragAnimation.kt#L43-L59) — `valueAnimation / progress / release / updateVelocity`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:95-108,140-149,188-203`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L95-L108) — `LiquidGlassSlider geometry`

## Root cause
progress and normalized velocity divide by end-start without a zero-span guard; initialValue is not coerced before Animatable construction. Track calculations also divide by available width and assume finite bounded dimensions.

## Impact and preconditions
A valid degenerate range such as0f..0f yields0/0=NaN and feeds layout rounding/translation; invalid/reversed/nonfinite ranges and unbounded/zero width can propagate invalid geometry or throw. Exact renderer failure mode has not been run on iOS.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- progress=(value-start)/(end-start); updateVelocity divides by the same span.
- The width of the active-track layout is computed from progress.fastRoundToInt with no finite check.

## Recommended solution
Specify numeric input policy and handle equal endpoints as a fixed value without division. Validate finite ordered ranges, coerce initial/external values consistently, and guard zero/unbounded layout width before producing sizes or callbacks.

## Risks and compatibility
Material/Cupertino behavior for degenerate ranges should guide compatibility. Do not classify caller-supplied NaN as a remote security issue.

## Required tests / acceptance criteria
- 0..0, negative range, reversed range, NaN/infinite value/endpoints and out-of-range initial values.
- Zero-width, very narrow and unbounded horizontal constraints, RTL, range change mid-animation.
- No NaN/Infinity reaches layout or velocity state.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
