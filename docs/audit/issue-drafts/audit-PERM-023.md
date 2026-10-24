# [Low][PERM-023] Specify and test the numerical domain and undefined-bearing policy of LatLng

<!-- nativecmpkit-item:audit:PERM-023 -->
## Classification
- **Finding:** PERM-023
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LatLng.kt:11-34,44-79`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LatLng.kt#L11-L34) — `LatLng/distanceTo/getAngleTo`

## Root cause
Coordinates accept nonfinite/out-of-range values, the haversine intermediate is not explicitly clamped, and bearing of coincident/antipodal points has no undefined policy. Distance is spherical kilometers while Location accuracy uses meters; rounding defaults to10 degrees.

## Impact and preconditions
Invalid input propagates NaN or misleading coordinates and callers can misuse distance/bearing units/meaning. A numerical domain violation from valid antipodes was NOT reproduced in5,000,000 seeded JVM cases; this is contract hardening, not a confirmed valid-input NaN bug.

## Supporting evidence
- Actual LatLng passed zero-distance, quarter-equator, north/east bearing and dateline tests on JVM;5,000,000 seeded antipodal trials found no NaN.

## Recommended solution
Document valid ranges, unit distinctions, spherical model error and undefined bearings; add validated/normalized factories and finite/domain checks as compatible additions, consider clamping the haversine intermediate, and benchmark before changing math.

## Risks and compatibility
Constructor validation/normalization changes existing data-class behavior and equality. Do not claim geodesic-grade WGS84 accuracy from the6371km spherical approximation.

## Required tests / acceptance criteria
- Identical/cardinal/dateline/poles/antipodes, very close points, nonfinite/out-of-range data.
- Properties symmetry/distance bounds, rounded0..350 vs unrounded[0,360), precision across JVM/JS/Wasm/Native.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
