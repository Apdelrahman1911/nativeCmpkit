# [Medium][PERM-007] iOS result callbacks are not main-thread/disposal safe and run before status refresh

<!-- nativecmpkit-item:audit:PERM-007 -->
## Classification
- **Finding:** PERM-007
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`, `calf-permissions/camera`, `calf-permissions/microphone`, `calf-permissions/contacts`, `calf-permissions/calendar`, `calf-permissions/notifications`, `calf-permissions/gallery`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt:77-83,106-110`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.ios.kt#L77-L83) — `launchPermissionRequest/refreshPermissionStatus`
- [`calf-permissions/camera/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/AVCameraPermissionHelper.kt:18-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/camera/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/AVCameraPermissionHelper.kt#L18-L24) — `launchPermissionRequest`
- [`calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt:22-32`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/notifications/src/iosMain/kotlin/com.mohamedrejeb.calf/permissions/helper/LocalNotificationPermissionHelper.kt#L22-L32) — `authorization callback`

## Root cause
Native completion callbacks directly invoke the application onPermissionResult, then refresh status. Only status assignment is launched on Dispatchers.Main. The composition scope does not own or cancel native callbacks and there is no disposed/request-generation guard.

## Impact and preconditions
UI/navigation callbacks can run on native completion queues, observe the old denied state despite result=true, and execute after the composable was disposed. Callback exceptions also prevent the subsequent refresh.

## Supporting evidence
- AVCaptureDevice, PHPhotoLibrary, CNContactStore, EventKit and UNUserNotificationCenter callbacks are forwarded directly; only refresh assignment uses Dispatchers.Main.
- Past #150 concerned snapshot threading, and #177/#179 discussed callback shape; a Boolean callback was retained for compatibility.

## Recommended solution
Marshal callback and status application onto the active main scope, refresh/apply a coherent result before notifying, and add request IDs/disposal cancellation or suppression. Define exactly-once completion/error semantics and ensure cleanup in finally.

## Risks and compatibility
Do not assume all Apple completion handlers are delivered on main. Queue/lifecycle integration is unverified on-device; source confirms the absence of dispatch and callback-before-refresh order, not a demonstrated UI crash.

## Required tests / acceptance criteria
- Deliver a helper result from a background queue and assert callback main thread and matching status.
- Dispose while native prompt remains active; no stale UI callback/state publication.
- Throw from user callback and verify cleanup/status recovery; race two asynchronous status queries.

## Dependencies
- PERM-005

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/150
- https://github.com/MohamedRejeb/Calf/issues/177
- https://github.com/MohamedRejeb/Calf/pull/179
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
