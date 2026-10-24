# [Medium][PERM-022] Android geo data treats missing accuracy/speed/bearing/altitude as real zero measurements

<!-- nativecmpkit-item:audit:PERM-022 -->
## Classification
- **Finding:** PERM-022
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:61-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/androidMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt#L61-L103) — `onLocationResult`
- [`calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/ExtendedLocation.kt:3-8`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/ExtendedLocation.kt#L3-L8) — `ExtendedLocation`
- [`calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Location.kt:9-11`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/Location.kt#L9-L11) — `Location`

## Root cause
Accuracy nullability is chosen only by SDK>=26; hasSpeedAccuracy/hasBearingAccuracy/hasVerticalAccuracy are never consulted. hasAccuracy, hasSpeed, hasBearing and hasAltitude are also ignored; Android getter defaults can become false physical measurements.

## Impact and preconditions
Consumers can interpret absent metadata as0 error/perfect accuracy, stationary speed, north bearing or sea-level altitude. This becomes externally visible once PERM-018 wires state delivery.

## Supporting evidence
- API-level guards exist for three new getters, but no has* method appears anywhere in onLocationResult.

## Recommended solution
Check every native has* flag; preserve absence in a versioned/additive measurement model, distinguish course/bearing from device heading, and document timestamp, units and stale-fix policy.

## Risks and compatibility
Making currently non-null values nullable can break callers. Avoid simply substituting NaN without a documented contract; keep API26 guards for newer getters.

## Required tests / acceptance criteria
- Construct Android Locations with each metadata flag independently absent/present on API23/26+.
- True zero vs missing value, coarse/stale/mock fixes, negative altitude, unit and epoch checks.

## Dependencies
- PERM-018

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/40
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
