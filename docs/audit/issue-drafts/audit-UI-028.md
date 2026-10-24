# [Medium][UI-028] AdaptiveSlider drops discrete steps on the iOS26 Liquid Glass branch

<!-- nativecmpkit-item:audit:UI-028 -->
## Classification
- **Finding:** UI-028
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSlider.ios.kt:10-42`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/AdaptiveSlider.ios.kt#L10-L42) — `AdaptiveSlider`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:65-74,140-175`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L65-L74) — `LiquidGlassSlider`

## Root cause
AdaptiveSlider forwards steps only to CupertinoSlider. LiquidGlassSlider has no steps parameter or tick snapping, so the iOS26 branch is always continuous.

## Impact and preconditions
The same public call selects arbitrary values after an OS upgrade even when a discrete domain was requested. Negative steps are also not validated by that branch.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- LiquidGlassSlider call omits steps because its signature has none; CupertinoSlider call supplies it.

## Recommended solution
Implement discrete snapping consistently for drag, tap and accessibility actions, including endpoints and completion, or use a tested compatible renderer until discrete support exists.

## Risks and compatibility
Keep the public steps convention (number of interior steps), avoid changing existing continuous behavior, and share validation with numeric-domain fixes.

## Required tests / acceptance criteria
- steps0,1,3 and invalid negative; drag/tap/accessibility values on pre26 and26+.
- Nonzero/negative ranges, RTL and endpoint rounding.

## Dependencies
- UI-029
- UI-032

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
