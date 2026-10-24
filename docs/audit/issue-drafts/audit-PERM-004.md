# [High][PERM-004] Android location requests do not orchestrate fine/coarse and foreground/background prerequisites

<!-- nativecmpkit-item:audit:PERM-004 -->
## Classification
- **Finding:** PERM-004
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`, `calf-permissions/location`, `calf-permissions/background-location`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:90-99`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt#L90-L99) — `launchPermissionRequest`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt:130-138`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.android.kt#L130-L138) — `launchMultiplePermissionRequest`
- [`calf-permissions/location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/LocationPermissions.android.kt:5-21`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/LocationPermissions.android.kt#L5-L21) — `registerFineLocationPermission/registerCoarseLocationPermission`
- [`calf-permissions/background-location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/BackgroundLocationPermissions.android.kt:5-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/background-location/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/BackgroundLocationPermissions.android.kt#L5-L12) — `registerBackgroundLocationPermission`
- [`docs/permissions.md:113-120,291-329`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/docs/permissions.md#L113-L120) — `location examples`

## Root cause
A logical permission maps to exactly one string; FineLocation alone requests only ACCESS_FINE_LOCATION. Bulk dispatch sends all strings together without separating background location from foreground permissions or checking prerequisites.

## Impact and preconditions
Android12+ requires requesting FINE together with COARSE for precise access; requesting fine alone may be ignored. Android11+ foreground and background location cannot be requested together; background requires an already-granted foreground path and settings-oriented UX. Common single-fine/sample bulk patterns do not implement these rules.

## Supporting evidence
- Source sends one native string for FineLocation and an unpartitioned array for all bulk permissions.
- Android platform guidance: https://developer.android.com/develop/sensors-and-location/location/permissions/runtime and /background.

## Recommended solution
Add a tested location request strategy (fine+coarse in one foreground step, then a separate background step with target-SDK-appropriate education/settings); or explicitly reject/document unsupported combinations until that API exists. Preserve approximate grants rather than treating coarse-only as total failure.

## Risks and compatibility
OS and target-SDK dependent; precise dialog/device behavior was not executed in this Linux audit. Never silently escalate a coarse-only request to precise/background access.

## Required tests / acceptance criteria
- API23,29,30,31,33+ with both current and legacy targetSdk: fine alone, coarse alone, fine+coarse, foreground+background.
- Accept approximate, deny precise, deny background and return from Settings.
- Verify manifest omissions and location services disabled are distinguished.

## Dependencies
- PERM-003

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/281
- https://github.com/MohamedRejeb/Calf/pull/298
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
