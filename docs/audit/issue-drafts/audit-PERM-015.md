# [Medium][PERM-015] iOS RemoteNotification skips APNs registration when notification authorization already exists

<!-- nativecmpkit-item:audit:PERM-015 -->
## Classification
- **Finding:** PERM-015
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/notifications`, `calf-permissions/core`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/RemoteNotificationPermissionHelper.kt:22-42,46-64`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/RemoteNotificationPermissionHelper.kt#L22-L42) — `launchPermissionRequest/getPermissionStatus`
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt:20-29`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/PermissionHelper.kt#L20-L29) — `handleLaunchPermissionRequest`

## Root cause
registerForRemoteNotifications is inside only the fresh requestAuthorization success closure. The shared handler short-circuits Granted (including provisional/ephemeral) with true, so it never registers on later launches or when local notifications authorized first.

## Impact and preconditions
The helper-added APNs registration side effect is missing for already-authorized users; apps depending on it may not obtain refreshed tokens. A Boolean permission grant is also not APNs token/registration success.

## Supporting evidence
- Commit4644603/#523 added registration only inside requestAuthorization success.
- Isolated original shared-handler test confirms Granted bypasses the native launch closure.

## Recommended solution
If APNs registration remains part of this API contract, call it on main after any eligible authorized result, including the short-circuit path; explicitly separate permission from registration/token state. Document aps-environment entitlement, app delegate token/error handling and background mode only when needed.

## Risks and compatibility
Some apps already register independently, so avoid duplicate callback/token assumptions. No entitlement/token delivery was tested, and a permission callback must not promise successful APNs connectivity.

## Required tests / acceptance criteria
- Fresh permission, already authorized at launch, local then remote, provisional/ephemeral, denied; assert registration call count/main thread.
- Valid/missing APNs entitlement and native registration success/failure callbacks on device.

## Dependencies
- PERM-007

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/523
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
