# [Medium][UI-023] iOS toolbar does not implement its documented Material fallback

<!-- nativecmpkit-item:audit:UI-023 -->
## Classification
- **Finding:** UI-023
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.kt:10-38`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.kt#L10-L38) — `AdaptiveToolbar contract`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.ios.kt:24-62`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/AdaptiveToolbar.ios.kt#L24-L62) — `AdaptiveToolbar`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/ToolbarManager.kt:35-48`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/toolbar/ToolbarManager.kt#L35-L48) — `attachTo`

## Root cause
The iOS actual returns immediately for empty iosItems; otherwise it always creates a native UIToolbar, with no iOS26 availability branch or invocation of Material content. expanded, modifier, leadingContent, trailingContent and content are ignored.

## Impact and preconditions
A portable toolbar using only the documented composable content is invisible on iOS, including older versions that promise Material fallback. Native placement is fixed to the root safe-area bottom and supplies no Compose inset/size.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The only early condition is if(iosItems.isEmpty()) return; no OS-version check or Material actual invocation exists.

## Recommended solution
Implement the documented availability/content fallback and clarify which arguments apply to the native branch. Coordinate native placement with scaffold ownership to avoid overlap; preserve internal FAB fallback as a reference, not a wholesale rewrite.

## Risks and compatibility
UIToolbar itself exists beforeiOS26, so this is a contract/behavior problem, not an unsupported-class crash claim.

## Required tests / acceptance criteria
- Pre26/26+ with empty and populated iosItems, expanded changes and content counters.
- Modifiers/insets, simultaneous bottom bar, keyboard and orientation.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
