# [Medium][PERM-001] Android silently treats an unregistered Permission as granted

<!-- nativecmpkit-item:audit:PERM-001 -->
## Classification
- **Finding:** PERM-001
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt:101-111`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/PermissionsUtil.android.kt#L101-L111) — `toAndroidPermission/isAlwaysGranted`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt:86-99,118-126`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.android.kt#L86-L99) — `launchPermissionRequest/getPermissionStatus`
- [`calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt:24-38`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/androidMain/kotlin/com/mohamedrejeb/calf/permissions/AndroidPermissionRegistry.kt#L24-L38) — `register/getMapping/findByAndroidString`

## Root cause
No mapping and a deliberately out-of-SDK-range mapping both become the empty string. The state interprets either as Granted and calls onPermissionResult(true). The public open Permission class permits custom permissions without an Android registration.

## Impact and preconditions
Missing custom integration is indistinguishable from real authorization and differs from the explicit missing-delegate error on iOS. Consumers may attempt protected operations and fail at the OS boundary. This is not an OS permission bypass.

## Supporting evidence
- Exact toAndroidPermission logic returned empty for Permission("Unregistered") in the isolated JVM harness. Source then returns Granted for empty.
- iOS PermissionDelegateRegistry.getDelegate throws for missing registration.
- Upstream #191 explicitly confirms RemoteNotification was intentionally iOS-specific.

## Recommended solution
Distinguish Registered, NotApplicable, and Unknown mapping results; fail clearly for Unknown, preserve explicitly documented no-op permissions, and validate custom names/ranges. Define main-thread registration or synchronize/freeze the registry.

## Risks and compatibility
Existing callers may rely on custom unknown permissions being no-ops. RemoteNotification on Android is intentionally iOS-only and documented as Granted; do not silently redefine that compatibility contract as part of this fix. Concurrent registry mutation is a risk, not an observed exploit.

## Required tests / acceptance criteria
- Custom unknown permission on Android/iOS gives a consistent diagnostic.
- Out-of-range mappings remain explicit not-applicable, including Notification below33.
- Custom registration/name collision and concurrent registration/lookup tests.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/191
- https://github.com/MohamedRejeb/Calf/commit/7d382c69ba93e218a210239ed9dfc99a34660be0
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
