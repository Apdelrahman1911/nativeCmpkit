# [High][NATIVE-001] Desktop stopLoading re-enqueues itself instead of cancelling WebEngine loading

<!-- nativecmpkit-item:audit:NATIVE-001 -->
## Classification
- **Finding:** NATIVE-001
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:225-248`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L225-L248) — `WebViewNavigator.handleNavigationEvents / StopLoading`
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:248-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L248-L249) — `WebViewNavigator.stopLoading`

## Root cause
Inside with(webView.engine), unqualified stopLoading() has no matching WebEngine member and resolves to the enclosing WebViewNavigator.stopLoading(). That emits another StopLoading event, which queues another Platform.runLater callback.

## Impact and preconditions
One stop request produces an unbounded coroutine/FX event feedback loop while the collector lives, consumes CPU, and does not stop the network/page load. Replayed commands can restart it after attachment.

## Supporting evidence
- docs/testing/native-features-probes/results-baseline.json: STOP_FEEDBACK steps=100 queued=1 nativeCancels=0.
- Dependency evidence identifies JavaFX19 WebEngine private stop(), reached by loadWorker.cancel(), not a public stopLoading API.
- git log -S stopLoading() traces the call back to the initial separate webview artifact; later FX-thread fixes retained it.

## Recommended solution
Call webView.engine.loadWorker.cancel() explicitly on the FX thread. Use explicit native receivers for each branch and ensure stop produces no new navigation event.

## Risks and compatibility
Probe replaces the FX engine and queue, not a running JavaFX GUI; the exact handler and navigator bodies were compiled. Public JavaFX19 source confirms absence of stopLoading. Do not describe this as a passed Desktop integration test.

## Required tests / acceptance criteria
- Assert a single stop request calls the native worker cancel once and emits no further commands.
- Run slow-page loading, stop, detach/reattach, and repeated-stop cases in an actual JavaFX/Compose window.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/203
- https://github.com/MohamedRejeb/Calf/pull/428
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
