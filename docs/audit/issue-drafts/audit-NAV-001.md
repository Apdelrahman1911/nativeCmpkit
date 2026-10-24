# [High][NAV-001] Adaptive navigation silently discards per-navigation arguments

<!-- nativecmpkit-item:audit:NAV-001 -->
## Classification
- **Finding:** NAV-001
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-navigation`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt:16-25`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHostController.kt#L16-L25) — `AdaptiveNavHostController.navigate/backStack`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt:39-44`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/AdaptiveNavHost.kt#L39-L44) — `AdaptiveNavHost destination dispatch`
- [`calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavDestination.kt:5-9`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-navigation/src/commonMain/kotlin/com.mohamedrejeb.calf/navigation/NavDestination.kt#L5-L9) — `NavDestination.arguments`

## Root cause
navigate(route, arguments) appends only the route String. No entry or argument payload is stored; the host passes the graph destination's static Map<String, NavArgument> definition to content instead of a navigation entry's values.

## Impact and preconditions
Callers cannot send different argument values to two visits of the same route. The API accepts input that is never observed; saved/restored stacks likewise carry no arguments. The module is currently unpublished, which limits consumer exposure but not the defect.

## Supporting evidence
- All source locations refer to immutable baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Controller line24 uses only backStack.add(route).
- Host line43 calls destination.content(destination.arguments); there is no lookup of the navigate arguments parameter.
- No route interpolation/deep-link argument parser is wired into AdaptiveNavHost.

## Recommended solution
Before stabilizing or publishing navigation, define a typed entry/payload contract distinct from argument schema; validate and merge defaults at navigation, expose resolved values to content, and implement a save/restore policy. Preserve or deprecate the current overload explicitly rather than silently dropping inputs.

## Risks and compatibility
Changing public types and saver format affects callers and restoration; do not hide the change in the identity migration. Never persist secrets or arbitrary unserializable objects by default.

## Required tests / acceptance criteria
- Navigate to one route with two distinct payloads; each visit receives its own values.
- Validate missing, nullable, wrong-type and defaulted arguments.
- Round-trip entry IDs and arguments through the saver; reject unsupported values predictably.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NAV.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NAV.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
