# [Medium][UI-026] Material dropdown silently drops most public popup and styling parameters

<!-- nativecmpkit-item:audit:UI-026 -->
## Classification
- **Finding:** UI-026
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.kt:39-56`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.kt#L39-L56) — `AdaptiveDropDown`
- [`calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.material.kt:19-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.material.kt#L19-L40) — `AdaptiveDropDown`

## Root cause
The Material actual accepts offset, scrollState, properties, shape, containerColor, tonalElevation, shadowElevation and border but forwards only expanded, onDismissRequest, modifier and materialContent to DropdownMenu.

## Impact and preconditions
Caller positioning, scrolling, popup focus/dismiss policy and appearance are ignored on Android/Desktop/Web. This is not merely an iOS-only styling limitation.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Only four named arguments are supplied in the DropdownMenu call at lines35-40.

## Recommended solution
Forward every supported parameter to DropdownMenu and add contract tests for behavior as well as visuals. Correct the documentation that suggests iosItems are automatically rendered in Material; the current actual requires and uses materialContent.

## Risks and compatibility
Some PopupProperties are target-specific; test platform behavior rather than assuming every field has an effect everywhere. No exploit or screenshot protection failure was reproduced.

## Required tests / acceptance criteria
- Nondefault offset/scrollState, dismissOnBackPress/dismissOnClickOutside/focusability where supported.
- Custom shape/colors/elevations/border and long scrollable contents.
- Android/Desktop/browser regression matrix.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
