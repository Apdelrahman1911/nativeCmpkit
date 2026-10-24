# [Medium][NATIVE-037] Replacing WebViewState or native lifecycle callbacks at the same composable identity is not safely rebound

<!-- nativecmpkit-item:audit:NATIVE-037 -->
## Classification
- **Finding:** NATIVE-037
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:151-162,190-215`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L151-L162) — `state reference, client rebind and AndroidView factory`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:50-108,110-141`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L50-L108) — `Unit-keyed DisposableEffect and factory captures`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:63-80,111-135`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L63-L80) — `state reference and UIKitView factory`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:43-50,69-105`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L43-L50) — `state reference and iframe factory listeners`

## Root cause
Native view creation occurs once in interop factories/effects; effects read the native reference from the currently supplied state, but a replacement WebViewState starts with null. Factories do not rerun or transfer the native view when state changes. Several listeners/onCreated/onDispose lambdas capture the original state/navigator/callback because effects are Unit-keyed or factories are one-shot.

## Impact and preconditions
Passing a new state object to an existing WebView composition can leave the rendered old view attached while new content/navigation/evaluation has no native target. Desktop/iOS/Web listeners can keep updating the old state or navigator; callback substitution is not consistently observed.

## Supporting evidence
- Android updates client.state on each composition but assigns state.webView only in factory; Desktop initialization effect is keyed Unit.
- iOS factory installs navigationDelegate=state once; browser event listeners close over initial state/navigator.

## Recommended solution
Either explicitly key the native view lifecycle on its state owner, with proper disposal, or implement safe rebinding/update callbacks and rememberUpdatedState for callbacks. Document one-state-per-native-view ownership and behavior of navigator replacement.

## Risks and compatibility
The normal rememberWebViewState helper retains one state, so ordinary URL recomposition is not this failure. This is a source-traced edge case requiring Compose interop tests, not a claim every recomposition breaks WebView.

## Required tests / acceptance criteria
- At a stable composition location replace stateA with stateB and verify content, native identity, observed state and disposal semantics.
- Replace navigator and callback lambdas without recreating the screen; only current owners receive updates.
- Rapid replacement during queued FX initialization/navigation does not resurrect stale state.

## Dependencies
- NATIVE-002
- NATIVE-006

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
