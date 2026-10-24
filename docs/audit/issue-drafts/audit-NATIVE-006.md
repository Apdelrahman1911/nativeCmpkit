# [Medium][NATIVE-006] Web WebView never invokes onDispose and retains iframe/listener references

<!-- nativecmpkit-item:audit:NATIVE-006 -->
## Classification
- **Finding:** NATIVE-006
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:35-42,69-106,162-166`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L35-L42) — `WebView lifecycle and WebViewState.iframe`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.web.kt:7-12`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebElementView.web.kt#L7-L12) — `CalfWebElementView signature`

## Root cause
The public onDispose parameter is never used. The wrapper exposes only factory/update, with no release callback/effect that clears state.iframe or unregisters its load/error listeners.

## Impact and preconditions
Caller cleanup is skipped on JS/Wasm and retained WebViewState keeps a detached DOM node plus captured state/navigator closures. A remount can briefly operate on an old node; lifecycle behavior differs from every native implementation.

## Supporting evidence
- No occurrence of onDispose in the function body after its declaration.
- factory assigns state.iframe at97 and no branch clears it.

## Recommended solution
Add a disposal path using the supported Compose Web interop lifecycle or an explicit DisposableEffect bound to the node. Remove listeners, stop/detach as appropriate, clear only the matching node and deliver onDispose once.

## Risks and compatibility
Compose WebElementView removes its own rendered element; this finding does not claim the DOM remains mounted. The retained state reference and missing user callback are the library defects.

## Required tests / acceptance criteria
- Mount/unmount with a callback counter; verify exactly one onDispose.
- Retained state no longer references the old iframe after removal.
- Queued load/error events after disposal do not update a replacement view.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/429
- https://github.com/MohamedRejeb/Calf/pull/431
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
