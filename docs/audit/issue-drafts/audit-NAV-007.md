# [Medium][NAV-007] Unknown routes and duplicate graph registrations silently render blank or select the first definition

<!-- nativecmpkit-item:audit:NAV-007 -->
## Classification
- **Finding:** NAV-007
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt:20-25`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt#L20-L25) — `navigate`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavGraphBuilder.kt:5-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavGraphBuilder.kt#L5-L20) — `addDestination/composable`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt:39-46`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt#L39-L46) — `route lookup`

## Root cause
The controller accepts any string; graph addition never enforces uniqueness; host dispatch uses find and nullable lets without an error branch.

## Impact and preconditions
Route typos or restoring a removed route leave a blank host. Duplicate registrations silently prefer the first definition, concealing graph construction errors.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- backStack.add accepts the input unchanged.
- destinations += destination at graph line12; destinations.find at host line41 is first-match only.

## Recommended solution
Validate graph uniqueness, define unknown-route behavior and restoration migrations, and provide a visible/fail-fast diagnostic appropriate to debug versus production. Keep registration/entry lookup consistent with the chosen controller architecture.

## Risks and compatibility
A controller can be used before a host attaches; validation must not accidentally prohibit legitimate graph initialization or typed-route migrations.

## Required tests / acceptance criteria
- Duplicate route registration produces a deterministic diagnostic.
- Navigate/start/restore with an unknown route has explicit behavior and no silent blank screen.
- Restore a route removed by an app upgrade using the documented fallback.

## Dependencies
- NAV-001

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
