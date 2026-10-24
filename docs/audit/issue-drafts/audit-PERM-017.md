# [Medium][PERM-017] Desktop, JS and Wasm permissions are nonfunctional stubs with silent callbacks

<!-- nativecmpkit-item:audit:PERM-017 -->
## Classification
- **Finding:** PERM-017
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-permissions/core`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.desktop.kt:22-28,44-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutablePermissionState.desktop.kt#L22-L28) — `rememberMutablePermissionState/MutablePermissionStateImpl`
- [`calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.js.kt:22-28,43-52`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/jsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.js.kt#L22-L28) — `MutablePermissionStateImpl`
- [`calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.wasmJs.kt:22-28,43-52`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/wasmJsMain/kotlin/com.mohamedrejeb.calf/permissions/MutablePermissionState.wasmJs.kt#L22-L28) — `MutablePermissionStateImpl`
- [`calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.desktop.kt:69-71`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-permissions/core/src/desktopMain/kotlin/com/mohamedrejeb/calf/permissions/MutableMultiplePermissionsState.desktop.kt#L69-L71) — `launchMultiplePermissionRequest`

## Root cause
Nonmobile factories discard callbacks; all states start Denied(false), and request, refresh and settings methods are empty. All nonmobile feature registration actuals are Unit. Multiple launch is also empty.

## Impact and preconditions
Shared UI compiles but can be permanently blocked by a denied permission gate even where the OS/browser operation is possible; callback consumers wait indefinitely. Existing docs correctly describe permissions as Android/iOS, so this is a capability gap rather than proof that advertised browser dialogs regressed.

## Supporting evidence
- Read all desktop/js/wasm state implementations and all feature registration actuals; no native/browser service call exists.
- Upstream #31 has a 2024 comment identifying desktop perpetual-denial behavior; the closed issue is not proof of completion.

## Recommended solution
Explicitly surface Unsupported/NotRequired and complete requests deterministically. Implement browser permission/service-specific requests only for supported capabilities, respecting user gestures/secure contexts; define desktop OS-specific policy instead of blindly granting everything.

## Risks and compatibility
Global desktop Granted would be wrong for macOS TCC and sandbox permissions. Browser APIs differ substantially and cannot emulate every mobile permission.

## Required tests / acceptance criteria
- Desktop/macOS sandbox behavior; browser camera/microphone/location/notifications with unavailable API, insecure context and denial.
- Every stub path completes once with a documented unsupported result rather than silently doing nothing.

## Dependencies
- PERM-016

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/31
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/PERM.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/PERM.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
