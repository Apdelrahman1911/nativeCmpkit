# [Medium][UI-025] Native dropdown reports dismissal immediately after opening and cannot follow expanded=false

<!-- nativecmpkit-item:audit:UI-025 -->
## Classification
- **Finding:** UI-025
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.ios.kt:94-153`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dropdown/AdaptiveDropDown.ios.kt#L94-L153) — `AdaptiveDropDown effects / hidden UIButton`

## Root cause
The expanded=true effect triggers the UIButton menu then immediately invokes onDismissRequest. There is no expanded=false branch to dismiss an open menu or delegate reporting actual native menu dismissal.

## Impact and preconditions
The public controlled expanded state becomes false while a native menu is still visible, and caller-driven closing does not close it. Callback timing differs from Material and can desynchronize owner navigation or focus.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- onDismissRequest() is called directly after performPrimaryAction/private fallback, with no wait for dismissal.
- The effect has no else branch.

## Recommended solution
Define native menu presentation ownership and observe real display/dismiss events through supported UIKit APIs. Either implement controlled expanded state or expose/document a distinct trigger-based API instead of simulating dismissal.

## Risks and compatibility
UIKit UIButton menu presentation is not a drop-in controlled Popup; supported native options may constrain the fix. The hidden button is rooted outside Compose, so nested-controller coordinates should be tested too.

## Required tests / acceptance criteria
- Open, dismiss by outside tap, select item, set expanded=false programmatically, reopen immediately.
- Callback ordering/cardinality and trigger inside moved/nested controller.

## Dependencies
- UI-024

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
