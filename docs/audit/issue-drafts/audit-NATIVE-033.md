# [Medium][NATIVE-033] Public mobile launch/evaluation operations lack an explicit main-thread contract or enforcement

<!-- nativecmpkit-item:audit:NATIVE-033 -->
## Classification
- **Finding:** NATIVE-033
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-camera-picker`, `calf-share`, `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt:32-36,92-95`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-camera-picker/src/iosMain/kotlin/com.mohamedrejeb.calf/camerapicker/CameraPickerLauncher.ios.kt#L32-L36) — `camera construction/presentation`
- [`calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt:49-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt#L49-L100) — `presentShareSheet`
- [`calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt:20-30`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/androidMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.android.kt#L20-L30) — `context.startActivity`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt:35-65,75-83,110-123`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt#L35-L65) — `WKHTTPCookieStore access`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:184-195`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L184-L195) — `settings/JavaScript calls`

## Root cause
Only iOS camera presentation is dispatched to main; it still constructs/configures UIImagePickerController before dispatch. iOS sharing and WebView settings/evaluation/cookie-store access run on the caller coroutine/thread. Public launch functions and suspend cookie API do not document/enforce UI affinity.

## Impact and preconditions
Calls from background application coroutines can violate UIKit/WebKit expectations, produce warnings/failures or missing completion. Most normal Compose click handlers are already on UI, so this is conditional rather than a failure of ordinary usage.

## Supporting evidence
- Camera comment says Always present controller on main, but UIImagePickerController is constructed earlier outside dispatch.
- Share presentShareSheet calls UIActivityViewController creation/present directly without any dispatch or caller check.

## Recommended solution
Document required affinity and marshal the entire native UI operation to the proper main dispatcher where safe. For suspend APIs, use withContext(Main) around thread-confined native calls; avoid dispatching just the final present call while constructing UI off-thread.

## Risks and compatibility
No mobile thread sanitizer/device run was available. Confirm each underlying native API requirement individually; do not claim all Foundation or all cookie processing must execute on main. Ensure result callbacks have a stable documented dispatcher.

## Required tests / acceptance criteria
- Call supported public APIs from Dispatchers.Default/IO and main; observe deterministic safe dispatch/result.
- UIKit Main Thread Checker and Kotlin/Native concurrency tests.
- Cancellation before dispatch, after presentation and before callback cannot orphan work.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/326
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
