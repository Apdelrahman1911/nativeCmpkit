# [Medium][UI-045] Applying a native view theme also mutates its parent view style

<!-- nativecmpkit-item:audit:UI-045 -->
## Classification
- **Finding:** UI-045
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ThemeUtils.kt:11-26,40-46`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/utils/ThemeUtils.kt#L11-L26) — `UIView.applyTheme / UIViewController.applyTheme / isDark`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt:77-80`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt#L77-L80) — `applyColors`

## Root cause
UIView.applyTheme sets overrideUserInterfaceStyle on both the target view and its superview. Individual control color synchronization can therefore alter a shared parent style; the light/dark heuristic also ignores alpha and uses a simple RGB weighted threshold.

## Impact and preconditions
Sibling/native-host appearance can be affected by configuring a single picker, especially with mixed per-component themes or nested controller hosts. Actual propagation depends on UIKit hierarchy and overrides and was not runtime-tested.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- UIView.applyTheme writes superview?.overrideUserInterfaceStyle as well as this.overrideUserInterfaceStyle.

## Recommended solution
Limit theme mutation to owned views/controllers unless parent ownership is explicit. Derive theme from an explicit state/policy where possible; test whether a parent override is truly needed for a specific control before retaining it.

## Risks and compatibility
Some UIKit controls may use parent presentation surfaces, so removing the superview assignment blindly can regress popovers. This is scoped as a risk requiring ownership tests, not a confirmed global theme corruption.

## Required tests / acceptance criteria
- Two native controls with opposite themes in one parent; update/remove each independently.
- Mixed Compose/native sheets/popovers and transparent day-content colors.
- System theme change and explicit caller overrides remain isolated.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
