# [Low][UI-039] Internal expandable FAB loses expanded items on model updates and is not ready for public exposure

<!-- nativecmpkit-item:audit:UI-039 -->
## Classification
- **Finding:** UI-039
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/ExpandableFABManager.kt:93-142,203-250,255-290`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/ExpandableFABManager.kt#L93-L142) — `updateItems / setExpanded / layoutButtons / animateExpansion`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.ios.kt:45-120`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.ios.kt#L45-L120) — `AdaptiveExpandableFAB / LiquidGlassExpandableFAB`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.kt:34-45`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/fab/AdaptiveExpandableFAB.kt#L34-L45) — `AdaptiveExpandableFAB`

## Root cause
updateItems rebuilds option buttons at alpha0/scale0.3, while setExpanded returns early if the expanded Boolean has not changed. An already-expanded menu therefore does not reapply its visible state after an item update. The native experiment also assumes fixed right/bottom offsets and an always-expanded-size container.

## Impact and preconditions
Dynamic item updates can make an expanded menu disappear. Transparent-container hit interception, RTL/safe-area placement and image-only accessibility are additional native risks. APIs are internal, limiting current external exposure.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- createItemButton/updateItems initialize alpha/transform before setExpanded sees an unchanged value.
- Container placement uses a hardcoded80pt tab-bar offset; title is logged rather than rendered.

## Recommended solution
Keep the API internal; reapply the actual expansion layout after rebuild and complete hit-test, layout-direction, safe-area and accessibility tests before exposure. Replace content-bearing NSLog calls with intentional development diagnostics or remove them.

## Risks and compatibility
Do not present this unfinished native prototype as a supported public feature or a security vulnerability. The disappearing-item path is source-confirmed; transparent hit interception needs UIKit execution.

## Required tests / acceptance criteria
- Update items/main item while expanded and collapsed, including empty lists.
- Touches through collapsed empty area, RTL, rotation, tab bar presence and varying safe areas.
- Accessible labels/actions and no item titles in production logs.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
