# [Medium][PERM-016] PermissionStatus loses partial capability, precision and requestability distinctions

<!-- nativecmpkit-item:audit:PERM-016 -->
## Classification
- **Finding:** PERM-016
- **Priority:** Medium
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`, `calf-permissions/gallery`, `calf-permissions/contacts`, `calf-permissions/location`, `calf-permissions/notifications`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.kt:9-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/commonMain/kotlin/com.mohamedrejeb.calf/permissions/PermissionsUtil.kt#L9-L20) — `PermissionStatus`
- [`calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt:39-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/location/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocationPermissionHelper.kt#L39-L57) — `getPermissionStatus`
- [`calf-permissions/gallery/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/GalleryPermissionHelper.kt:17-18,25-44`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/gallery/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/GalleryPermissionHelper.kt#L17-L18) — `legacy Photos authorization`
- [`calf-permissions/contacts/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/ContactPermissionHelper.kt:25-35`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/contacts/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/ContactPermissionHelper.kt#L25-L35) — `getPermissionStatus`
- [`calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt:41-55`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt#L41-L55) — `authorization mapping`

## Root cause
Two status variants collapse not-determined, restricted, permanently denied, limited and unsupported states. Fine/Coarse share a location helper that never checks accuracyAuthorization; contacts limited falls into denial; Photos uses legacy APIs that may report limited access as Authorized; provisional notifications count as Granted without delivery capability detail.

## Impact and preconditions
A granted FineLocation does not prove precise location on iOS, a limited contacts grant is unusable through the abstraction, and callers cannot distinguish partial gallery access or provisional alerts. Android shouldShowRationale=false means both first-use and permanent denial, while iOS true often means settings-only.

## Supporting evidence
- No partial/unsupported/requestability state exists. Native status switches expose the listed collapsing behavior.
- Historical #154/#229/#258/#284 show repeated confusion around the Boolean rationale convention.

## Recommended solution
Add a capability/result model alongside the compatibility Boolean API: requestability/denial reason, limited scope, iOS accuracy level and notification delivery modes. Use modern access-level APIs with availability guards. Document old Granted as a coarse permission signal, never full resource access.

## Risks and compatibility
A new sealed variant can break exhaustive when expressions; prefer additive API or a deliberate major migration. Photos limited behavior differs between legacy and modern query APIs, so do not assert legacy query currently denies every limited grant.

## Required tests / acceptance criteria
- iOS reduced/full accuracy and temporary full accuracy, limited/full contacts, selected/all photos, provisional/ephemeral notifications.
- Android14 selected media, approximate location, first deny/second deny/never asked and unsupported targets.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/154
- https://github.com/MohamedRejeb/Calf/issues/175
- https://github.com/MohamedRejeb/Calf/issues/229
- https://github.com/MohamedRejeb/Calf/issues/258
- https://github.com/MohamedRejeb/Calf/issues/284
- https://github.com/MohamedRejeb/Calf/issues/177
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
