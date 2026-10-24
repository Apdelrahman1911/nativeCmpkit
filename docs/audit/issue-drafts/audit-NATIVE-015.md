# [Medium][NATIVE-015] JavaScript evaluation has inconsistent failure, result and thread semantics

<!-- nativecmpkit-item:audit:NATIVE-015 -->
## Classification
- **Finding:** NATIVE-015
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:375-378`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L375-L378) — `evaluateJavascript`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:188-195`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L188-L195) — `evaluateJavascript`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:204-208`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L204-L208) — `evaluateJavascript`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:152-159`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L152-L159) — `evaluateJavascript`

## Root cause
Android/iOS call native APIs on the caller thread and silently omit callback when no view exists. Desktop queues to FX but does not catch executeScript exceptions. iOS sends localized error text through the same String channel as success. Android returns native JSON-encoded values while other targets use toString; Web catches errors as null.

## Impact and preconditions
Portable client code cannot reliably distinguish null, error text, quoted string and successful string, and may wait forever for callbacks or cause UI-thread violations/uncaught FX exceptions. A callback throwing inside the Web try block can itself trigger a second callback(null).

## Supporting evidence
- Source methods differ in both dispatch and error handling; no common result normalization exists.
- The Android JavascriptInterface annotation does not itself register a JS bridge; no addJavascriptInterface call exists in the module.

## Recommended solution
Add a typed result/error API with documented serialization and exactly-once callback/suspend semantics; route native execution to the correct UI dispatcher, handle absent/disposed views and script errors explicitly. Preserve the old function as a documented compatibility adapter.

## Risks and compatibility
Do not expose a universal unsafe bridge to untrusted pages while adding functionality. Existing consumers may depend on Android JSON encoding; changes need additive compatibility treatment.

## Required tests / acceptance criteria
- Evaluate string, number, object, null, undefined and throwing scripts on all targets.
- Call before attach, after dispose, off main thread and after callback substitution.
- Callback exceptions are not misreported as script failures or delivered twice.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/2
- https://github.com/MohamedRejeb/Calf/pull/16
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
