# [High][PERM-018] Android LocationTracker never updates its public location states

<!-- nativecmpkit-item:audit:PERM-018 -->
## Classification
- **Finding:** PERM-018
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:37-39,58-108,124-148`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt#L37-L39) — `onLocationResult/locationState/extendedLocationState`

## Root cause
onLocationResult constructs data and sends it to two private conflated channels. Neither channel is consumed/exposed, and the two MutableState fields are only initialized, never assigned after construction.

## Impact and preconditions
Even when the OS delivers real fixes, public locationState stays (0,0) and extended state remains all-zero with timestamp0. Tracking wastes work without producing a usable result; initial coordinates also masquerade as a real location.

## Supporting evidence
- Search of all geo source finds channel sends but no receives and no _locationState.value/_extendedLocationState.value assignments.
- The Android file is unchanged since commit2492c2a (2023-12-02); historical #26/#40 are not evidence of a complete implementation.

## Recommended solution
Route validated updates into public observable state (prefer a single coherent source for simple/extended views), represent no-fix explicitly, remove unused channels or implement a lifecycle-owned consumer, and add regression tests before publishing geo.

## Risks and compatibility
The module has no publication plugin and appears to be a prototype. Changing non-null State types requires an additive state/result API or compatibility bridge; do not advertise ready geolocation until verified.

## Required tests / acceptance criteria
- Inject one and multiple Android LocationResult values and assert both observable states update consistently.
- No-fix/null lastLocation, stop/dispose, no duplicate emissions, initial unavailable state and recomposition observation.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/26
- https://github.com/MohamedRejeb/Calf/pull/40
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
