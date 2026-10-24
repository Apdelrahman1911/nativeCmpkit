# [Medium][NAV-006] AdaptiveNavHost retains stale graph closures and does not initialize a replacement controller

<!-- nativecmpkit-item:audit:NAV-006 -->
## Classification
- **Finding:** NAV-006
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt:13-31`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt#L13-L31) — `AdaptiveNavHost remember/LaunchedEffect`

## Root cause
The graph builder is remembered without keys, and initialization is a LaunchedEffect(Unit). Recomposition with another controller, startDestination or builder does not rebuild graph closures or rerun start-route setup.

## Impact and preconditions
Replacing an empty controller at the same composition location can render no destination indefinitely; remembered destination lambdas can still capture the previous controller or stale state. Callers cannot infer the graph lifetime contract from the signature.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Keyless remember at line23 closes over the initial builder.
- LaunchedEffect(Unit) at line29 runs on host entry, not on controller replacement.

## Recommended solution
Choose and document static versus dynamic graph ownership. Key controller initialization correctly; use stable graph specifications and updated callback/state capture or intentional graph keys. Add replacement tests before exposing navigation as supported.

## Risks and compatibility
Blindly keying on an unstable builder lambda may rebuild the graph on every recomposition and lose state. Changing startDestination must not unexpectedly reset an existing stack.

## Required tests / acceptance criteria
- Replace a controller at one composition site and verify initialization and callback routing.
- Recompose after an outer callback/state changes and confirm graph content sees intended values.
- Change startDestination with an empty and nonempty stack under an explicit policy.

## Dependencies
- NAV-001
- NAV-002

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
