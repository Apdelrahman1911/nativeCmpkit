# [Medium][PERM-019] Non-Android geolocation trackers only print messages and report fabricated zero coordinates

<!-- nativecmpkit-item:audit:PERM-019 -->
## Classification
- **Finding:** PERM-019
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-geo`
- **Estimated complexity:** XL
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-geo/src/iosMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:7-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/iosMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt#L7-L40) — `LocationTracker`
- [`calf-geo/src/desktopMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt:7-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/desktopMain/kotlin/com/mohamedrejeb/calf/geo/LocationTracker.kt#L7-L40) — `LocationTracker`
- [`calf-geo/src/jsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.js.kt:7-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/jsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.js.kt#L7-L40) — `LocationTracker`
- [`calf-geo/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.wasmJs.kt:7-40`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.wasmJs.kt#L7-L40) — `LocationTracker`
- [`calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt:6-14`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-geo/src/commonMain/kotlin/com.mohamedrejeb.calf/geo/LocationTracker.kt#L6-L14) — `expect LocationTracker`

## Root cause
All four actual implementations have println-only start/stop and constant all-zero states. The common expect class declares no constructor/factory for shared-code creation or binding.

## Impact and preconditions
Compilation is not platform support: no CoreLocation, navigator.geolocation or desktop provider runs, and consumers cannot distinguish unsupported/no-fix from a position at0,0. Shared initialization is also incomplete.

## Supporting evidence
- All four files were read in full and are equivalent except file/source-set path; startTracking/stopTracking contain only println.
- No geo publication plugin is applied in baseline build.gradle.kts.

## Recommended solution
Mark geo experimental/unavailable, provide a common lifecycle/factory and explicit unavailable result, then implement target backends in planned increments or remove unsupported target claims until complete.

## Risks and compatibility
Do not add a fake always-success default to satisfy a multiplatform type. A portable desktop location source may not exist; Unsupported can be the correct result.

## Required tests / acceptance criteria
- Compile a common-code usage sample; verify supported/unsupported outcome on every target.
- iOS usage keys/denial/accuracy, browser secure contexts/watch cancellation, desktop provider absence.

## Dependencies
- PERM-018

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/26
- https://github.com/MohamedRejeb/Calf/pull/40
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
