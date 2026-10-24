# [Medium][NATIVE-016] Common WebContent options are silently ignored on several targets

<!-- nativecmpkit-item:audit:NATIVE-016 -->
## Classification
- **Finding:** NATIVE-016
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:46-58,165-176,264-267`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L46-L58) — `WebContent, navigation payloads and header documentation`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:120-132,240-243`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L120-L132) — `load/loadContent`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:94-100,272-289`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L94-L100) — `HTML data loaders`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-59,220-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50-L59) — `iframe loads`

## Root cause
Desktop drops additionalHttpHeaders, baseUrl, encoding and historyUrl. Web drops URL headers and HTML base/mime/encoding/history entirely. iOS state-driven HTML only calls loadHTMLString, while navigator HTML with a base URL encodes bytes as UTF8 regardless of the requested encoding label. Common documentation claims headers apply to all subsequent requests although mobile code only sets them on the requested load.

## Impact and preconditions
Authentication/header-dependent pages or relative HTML resources can fail silently; iOS non-UTF8 labels can mismatch UTF8 data. Applications cannot infer parity from the common signatures. Automatic forwarding of credential headers would itself need an origin policy.

## Supporting evidence
- Desktop engine.load receives only content.url/event.url. Web assigns only src/srcdoc.
- iOS navigator line275 always dataUsingEncoding(NSUTF8StringEncoding), but line282 uses caller event.encoding.

## Recommended solution
Document and expose capability restrictions; validate/reject unsupported options rather than implying support. Share consistent state/navigator loaders. If implementing headers/base URLs, do not leak authorization across origins; encode bytes consistently with the declared encoding.

## Risks and compatibility
Browser cannot attach arbitrary headers to iframe navigation; a proxy/fetch workaround changes origin, cookies, CSP and security and is not a routine fix. Do not promise full web/native parity.

## Required tests / acceptance criteria
- Authenticated URL with custom header, redirect to same/different origin and subsequent links/subresources.
- Inline relative URLs with baseUrl and non-ASCII data under supported encodings.
- State versus navigator content produce the same semantics per platform.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/428
- https://github.com/MohamedRejeb/Calf/pull/429
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
