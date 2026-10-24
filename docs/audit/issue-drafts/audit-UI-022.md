# [Medium][UI-022] Clearing native navigation-bar items leaves the previous tabs visible

<!-- nativecmpkit-item:audit:UI-022 -->
## Classification
- **Finding:** UI-022
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt:40-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt#L40-L60) — `TabBarManager.setItems`

## Root cause
setItems returns immediately for an empty items list, without clearing tabBar.items or selectedItem.

## Impact and preconditions
Conditional navigation items removed from app state remain visible and can retain obsolete actions/selection until the entire manager is destroyed.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- if(items.isEmpty()) return precedes construction and assignment of native items.

## Recommended solution
Treat empty input as an explicit clear operation, reset selection safely, and define out-of-range selectedIndex behavior.

## Risks and compatibility
Native selectedItem/delegate behavior after clearing needs a small UIKit test; do not preserve obsolete tabs as a fallback for empty data.

## Required tests / acceptance criteria
- Populate two tabs, update to empty, then repopulate; assert native items and callbacks.
- Selection index out of bounds and item reorder.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
