# [High][UI-029] Liquid Glass slider and switch lack actionable accessibility and keyboard semantics

<!-- nativecmpkit-item:audit:UI-029 -->
## Classification
- **Finding:** UI-029
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt:65-264`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/LiquidGlassSlider.kt#L65-L264) — `LiquidGlassSlider`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt:145-178,234-235`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toggle/LiquidGlassSwitch.kt#L145-L178) — `LiquidGlassSwitch semantics / gesture target`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt:662-704`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/slider/CupertinoSlider.kt#L662-L704) — `cupertinoSliderSemantics`

## Root cause
The Liquid slider is constructed from Box/pointerInput without range/progress/setProgress/focusable semantics. The Liquid switch sets role/toggleableState/stateDescription but no semantic click/toggle action and only attaches pointer gestures to its40x24dp thumb. It hardcodes English On/Off labels.

## Impact and preconditions
VoiceOver, Switch Control and keyboard users cannot reliably operate these controls through standard semantic actions. This is an accessibility regression from the pre26 Cupertino slider/switch and Material branches, which expose interaction semantics.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- LiquidGlassSlider has no semantics or progressSemantics/focusable call.
- Switch semantics block only assigns role, toggleableState, English stateDescription and disabled.
- CupertinoSlider already uses setProgress/progressSemantics, illustrating the regression.

## Recommended solution
Use foundation toggleable/appropriate slider semantics or equivalent complete actions on the full accessible control, with localized state, disabled/read-only rules, focus and minimum touch targets. Ensure visuals follow the same controlled state as accessibility.

## Risks and compatibility
Missing semantic actions are source-confirmed. Actual iOS assistive-technology traversal and UIKit interop defaults are not tested; do not infer that all native widgets lack accessibility.

## Required tests / acceptance criteria
- VoiceOver adjust slider/double-tap switch, Switch Control and hardware keyboard on iOS26+.
- Semantics tests for disabled/read-only, min/max/current/steps, localized labels and callback counts.
- Full-track and minimum44pt target checks at large text sizes.

## Dependencies
- UI-030

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
