# [Low][UI-041] Liquid button eagerly builds an unused highlight shader and lacks a measured effects budget

<!-- nativecmpkit-item:audit:UI-041 -->
## Classification
- **Finding:** UI-041
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt:70-74,83-155`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/button/LiquidGlassButton.kt#L70-L74) — `LiquidGlassButton`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt:22-24,43-95`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/InteractiveHighlight.kt#L22-L24) — `isRuntimeShaderSupported / InteractiveHighlight`

## Root cause
InteractiveHighlight eagerly constructs RuntimeShader, but LiquidGlassButton consumes only its gestureModifier/state and never its drawing modifier. The shader-support predicate is hardcoded true. Backdrop blur/lens/shadow effects and modifier shader creation have no performance or reduced-motion/transparency checks in this module.

## Impact and preconditions
Buttons can pay setup cost for a shader not drawn; dense lists and animated glass controls risk avoidable CPU/GPU work. Exact compilation/allocation/frame cost is unmeasured, not a demonstrated frame-rate regression.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- No calf-ui consumer applies InteractiveHighlight.modifier; the only consumer applies gestureModifier.
- RuntimeShader is created in the helper constructor, and isRuntimeShaderSupported() always returns true.

## Recommended solution
Remove unused shader construction or make it lazy behind an actual capability/usage path; profile representative lists and reuse native/graphics resources deliberately. Add an accessibility reduced-effects policy where appropriate.

## Risks and compatibility
Do not drop attribution when consolidating imported helpers. Skia/backdrop backend capability must be checked against pinned dependency versions rather than Android-specific assumptions.

## Required tests / acceptance criteria
- Trace construction/allocation with100 buttons and no highlight drawing modifier.
- Frame time/GPU overdraw on supported older and current Apple hardware.
- Reduced motion/transparency, dark mode, scrolling backgrounds and fallback backdrop behavior.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
