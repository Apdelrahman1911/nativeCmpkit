# [High][NATIVE-002] Android and Desktop WebViews retain live native views after composition disposal

<!-- nativecmpkit-item:audit:NATIVE-002 -->
## Classification
- **Finding:** NATIVE-002
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:194-215,405-408`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L194-L215) — `AndroidView.factory/onRelease and WebViewState.webView`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:52-108,211-212`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L52-L108) — `DisposableEffect/onDispose and WebViewState.webView`

## Root cause
Android onRelease only calls the user callback; it neither stops/destroys the WebView nor clears state.webView/clients. Desktop onDispose only calls the user callback; it leaves scene, engine load, listeners and state.webView connected, with implicit FX exit disabled.

## Impact and preconditions
When callers retain WebViewState, it retains the Android Activity/view or the entire Desktop WebView/scene and callbacks after the UI is removed. Loading, audio/timers and native resources may outlive the screen; old views can be observed during remount.

## Supporting evidence
- Android line209 stores state.webView; line213 is the sole onRelease action.
- Desktop line101 stores state.webView and lines60-98 register strong closures; lines105-107 do not undo either.

## Recommended solution
Define ownership and teardown ordering: save state first, cancel load, detach clients/listeners, remove scene/native references, destroy Android WebView after removal, and clear state.webView if it still denotes that instance. Put cleanup in finally so a throwing user onDispose cannot skip it. Manage FX runtime lifetime independently rather than exiting per view.

## Risks and compatibility
Missing teardown and retained references are source-confirmed; actual retained heap size, active playback and host process shutdown depend on engine/application behavior. Do not invoke private JavaFX dispose APIs without support analysis.

## Required tests / acceptance criteria
- Retain state, mount/unmount repeatedly and verify Activity/native view collectability with weak references/profilers.
- Verify teardown cancels a slow request and media and does not clear a replacement instance.
- Test onDispose throwing, delayed Platform.runLater initialization, process-state save and multiwindow operation.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/203
- https://github.com/MohamedRejeb/Calf/pull/426
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
