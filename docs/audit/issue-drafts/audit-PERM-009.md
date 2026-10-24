# [High][PERM-009] iOS BackgroundLocation cannot upgrade an existing WhenInUse grant to Always

<!-- nativecmpkit-item:audit:PERM-009 -->
## Classification
- **Finding:** PERM-009
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/background-location`, `calf-permissions/core`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt:25-50`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/background-location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/BackgroundLocationPermissionHelper.kt#L25-L50) — `launchPermissionRequest/getPermissionStatus`
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt:20-29`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt#L20-L29) — `handleLaunchPermissionRequest`

## Root cause
AuthorizedWhenInUse falls through to Denied(shouldShowRationale=true). The shared handler interprets that as permanently denied and immediately invokes false; requestAlwaysAuthorization is only reached for NotDetermined.

## Impact and preconditions
The normal staged foreground-to-background authorization upgrade is blocked by library logic, independently of OS dialog scheduling. Existing foreground grants can never request Always through this helper.

## Supporting evidence
- The actual baseline BackgroundLocationPermissionHelper compiled against a controlled CoreLocation adapter returned false and made zero requestAlwaysAuthorization calls for AuthorizedWhenInUse.
- This is a deterministic Kotlin control-flow reproduction, not an iOS runtime test.

## Recommended solution
Model authorizedWhenInUse as eligible for upgrade (not denied/restricted); invoke requestAlwaysAuthorization through a dedicated background state machine with the required usage keys and documented iOS staged/provisional semantics.

## Risks and compatibility
Changing the generic rationale convention for every permission would reintroduce historical iOS denial bugs. Fix the background state transition specifically and keep owner-visible disclosure before background access.

## Required tests / acceptance criteria
- WhenInUse -> Always upgrade, NotDetermined -> staged authorization, denied/restricted, Allow Once, deferred Always dialog.
- Test exact callback count and app resume after a settings upgrade.

## Dependencies
- PERM-007

## Historical context
- https://github.com/MohamedRejeb/Calf/commit/292f66f41c63bdb2da1fbebc232758797fa1d626
- https://github.com/MohamedRejeb/Calf/pull/421
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
