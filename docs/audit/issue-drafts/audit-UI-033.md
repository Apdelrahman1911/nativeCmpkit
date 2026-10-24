# [Medium][UI-033] Cupertino slider accessibility snapping fails for negative target values

<!-- nativecmpkit-item:audit:UI-033 -->
## Classification
- **Finding:** UI-033
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt:662-704`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt#L662-L704) — `Modifier.cupertinoSliderSemantics`

## Root cause
The discrete setProgress search initializes distance to newValue instead of a nonnegative distance/infinity. When the coerced target is negative, every abs(step-originalValue)<=distance comparison fails and the unsnapped target is emitted.

## Impact and preconditions
Accessibility adjustments can violate the discrete steps domain for negative ranges even though pointer/tick snapping uses different logic. For-1..1 with three interior steps, a requested-0.7 remains-0.7 rather than snapping to-0.5.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- distance:Float=newValue at line678 is compared against abs(step-originalValue) at685.
- Executed the exact extracted cupertinoSliderSemantics helper with a capture-only Modifier/semantics stub: range-1..1,steps3,target-0.7 emits-0.7; positive0.7 control snaps to0.5. No Compose runtime/VoiceOver was loaded. See docs/testing/ui-source-probes.py and evidence/ui-source-probes.txt.

## Recommended solution
Initialize minimum distance to positive infinity or use a shared nearest-tick helper, with deterministic ties. Align semantic, tap and drag snapping behavior.

## Risks and compatibility
The arithmetic defect is independent of UIKit. The harness may extract this exact helper with Compose semantics stubs; such a probe is not a real accessibility integration test.

## Required tests / acceptance criteria
- Semantic setProgress on-1..1,steps3,target-0.7 expects-0.5.
- All-negative range, zero/positive ranges, ties/endpoints and callback completion.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
