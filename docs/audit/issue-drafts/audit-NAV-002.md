# [High][NAV-002] Route-keyed saved state aliases duplicate back-stack entries and incompletely fixes #542

<!-- nativecmpkit-item:audit:NAV-002 -->
## Classification
- **Finding:** NAV-002
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt:16-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt#L16-L24) — `backStack/navigate`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt:34-44`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt#L34-L44) — `SaveableStateProvider`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt:50-64`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt#L50-L64) — `ForgetPoppedDestinations`
- [`calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt:23-71`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/desktopTest/kotlin/com/mohamedrejeb/calf/navigation/AdaptiveNavHostStateTest.kt#L23-L71) — `existing distinct-route restoration tests`

## Root cause
The stack permits duplicate strings, but the state provider key is currentDestination (route) and popped-state cleanup compares sets of routes. There is no unique navigation-entry identity.

## Impact and preconditions
A -> B -> A reuses the first A's saveable state; A -> A can keep the same composition. Popping one occurrence while another remains cannot discard only the popped entry's state. A pop/re-push between observed compositions is also invisible to route-set cleanup.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Provider key at line42 is the route string; cleanup at line56 drops multiplicity via toSet().
- The two baseline tests exercise home/detail with distinct routes only.
- Archived #542 commit1554f1b7758e634faf93cd4e851046b94b3fb954 introduced route-keyed retention; no duplicate-entry test is present.

## Recommended solution
Give each stack entry a stable unique ID, key state and cleanup by that ID, persist it with the entry, and prune state for removed entries. Retain the positive distinct-route behavior introduced by #542.

## Risks and compatibility
Saver compatibility and lifecycle expectations must be specified. A route-key optimization is not equivalent to Jetpack Navigation's per-entry owners. Compose/device reproduction remains required; this finding is based on the explicit identity algorithm.

## Required tests / acceptance criteria
- A -> B -> A has two independent counters and popping restores the original A.
- Consecutive A -> A produces fresh local/saveable entry state.
- Pop and immediately push the same route before an idle frame; the new entry is fresh.
- Restore a stack containing duplicate routes and pop each independently.
- Retain both existing #542 tests.

## Dependencies
- NAV-001

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/542
- https://github.com/MohamedRejeb/Calf/commit/1554f1b7758e634faf93cd4e851046b94b3fb954
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
