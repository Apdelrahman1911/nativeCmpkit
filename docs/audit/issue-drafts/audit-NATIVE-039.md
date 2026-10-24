# [Low][NATIVE-039] WebView settings changes and error accumulation perform avoidable full updates

<!-- nativecmpkit-item:audit:NATIVE-039 -->
## Classification
- **Finding:** NATIVE-039
- **Priority:** Low
- **Evidence status:** `improvement` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:6-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L6-L169) — `all property setters`
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:221-245,292-296`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L221-L245) — `full applySettings and error snapshots`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:187-221`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L187-L221) — `applySetting/runLater`

## Root cause
Every setter invokes a full native settings reapply even when assigning the same value; Desktop queues one FX task per setter and each task reads the whole live settings object. Android records each resource error by copying the entire accumulated list with toList().

## Impact and preconditions
Configuration batches cause redundant native/JNI/FX work; many failed resources allocate quadratically many error-list elements over a request. No benchmark demonstrates a user-visible slowdown yet, so this is an optimization candidate rather than a release-blocking defect.

## Supporting evidence
- All setters call onSettingsChanged unconditionally. Android onReceivedError calls mutableErrorsForCurrentRequest.toList after each addition.

## Recommended solution
Skip equal-value notifications, batch/transaction settings changes or apply field deltas on the correct UI thread, and choose a bounded/batched immutable error reporting strategy that preserves diagnostics. Measure before and after.

## Risks and compatibility
Coalescing updates may alter observable timing; mutable collections must not leak through supposedly immutable UI state. Bounded diagnostics need an explicit truncation/count indicator rather than silently discarding errors.

## Required tests / acceptance criteria
- Assign identical settings repeatedly and apply a multi-setting batch; assert bounded native/FX calls.
- Thousands of resource failures: benchmark allocation/time and preserve required error metadata.
- Concurrent/UI-thread application still sees a coherent settings snapshot.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
