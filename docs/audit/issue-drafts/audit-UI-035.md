# [Medium][UI-035] Several iOS adaptive visual and interaction parameters are accepted but unused

<!-- nativecmpkit-item:audit:UI-035 -->
## Classification
- **Finding:** UI-035
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveButton.ios.kt:15-56`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveButton.ios.kt#L15-L56) — `AdaptiveButton`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveIconButton.ios.kt:16-55`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/AdaptiveIconButton.ios.kt#L16-L55) — `AdaptiveIconButton`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:65-83,256-258`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L65-L83) — `LiquidGlassSlider colors / interactionSource`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/AdaptiveSwitch.ios.kt:10-39`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/AdaptiveSwitch.ios.kt#L10-L39) — `AdaptiveSwitch`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt:69-81,229-235`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt#L69-L81) — `LiquidGlassSwitch thumbContent / interactionSource`

## Root cause
AdaptiveButton does not forward shape/contentPadding. The older icon-button branch ignores supplied colors and the Liquid branch ignores container colors. Liquid slider ignores its colors and interactionSource; Liquid switch ignores thumbContent/interactionSource and most color fields, while the adaptive26+ branch drops caller SwitchColors altogether.

## Impact and preconditions
Public customization and externally observed interactions silently stop working on iOS or after an OS26 branch change. Brand colors/disabled contrast and custom thumb content can differ from the requested API, undermining accessibility and predictable reuse.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Liquid slider derives hardcoded accent/track colors and paints a white thumb instead of using the colors argument.
- Liquid switch receives thumbContent and interactionSource but never references them in its UI body.

## Recommended solution
Create an explicit parameter support matrix, forward or faithfully translate supported values, and mark intentionally platform-only inputs clearly. Remove unusable experimental configuration only with a compatibility plan, not through silent omission.

## Risks and compatibility
Some Material-specific appearance differences are intentionally adaptive and not defects by themselves. Prioritize unused platform-neutral arguments and exposed Liquid-specific parameters; do not promise pixel-identical native and Material design.

## Required tests / acceptance criteria
- Distinctive custom colors/shape/padding/thumb content on both iOS branches.
- Pressed/released/drag interactions observed through supplied MutableInteractionSource.
- Disabled contrast, dark mode and large text snapshots.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
