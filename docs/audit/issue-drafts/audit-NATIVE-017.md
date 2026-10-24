# [Medium][NATIVE-017] iOS inline-media configuration is changed only after WKWebView construction

<!-- nativecmpkit-item:audit:NATIVE-017 -->
## Classification
- **Finding:** NATIVE-017
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:111-124,251-258`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L111-L124) — `WKWebView factory and applySettings`
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:149-155`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L149-L155) — `IosSettings.allowsInlineMediaPlayback`

## Root cause
The factory constructs WKWebView() with default configuration, then sets configuration.allowsInlineMediaPlayback. Apple’s configuration property returns a copy and changing that configuration does not affect the existing web view. Dynamic changes repeat the same ineffective scalar assignment.

## Impact and preconditions
The common default/setting can report inline playback enabled while iPhone behavior remains the native default. Consumers cannot reliably opt into inline playback using the exposed API.

## Supporting evidence
- Apple WKWebView.configuration documentation retrieved2026-10-24: returns a copy; changes do not affect the web view configuration.
- The code uses WKWebView() then configuration.allowsInlineMediaPlayback; no prepared configuration initializer exists.

## Recommended solution
Create WKWebViewConfiguration before native view initialization and pass it to WKWebView(frame, configuration). Clearly separate creation-only options from mutable preferences; recreate deliberately or reject unsupported runtime changes.

## Risks and compatibility
No iOS playback run was possible. Evidence concerns the scalar configuration field, not an assumption that every nested preferences property is copied or that all JavaScript toggles fail.

## Required tests / acceptance criteria
- iPhone video with playsinline under true/false initial settings.
- Changing creation-only configuration after mount has explicitly tested documented behavior.
- Ensure initialization order does not regress onCreated, navigation delegate or default website data store.

## Dependencies
- None identified.

## Historical context
- https://developer.apple.com/documentation/webkit/wkwebview/configuration
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
