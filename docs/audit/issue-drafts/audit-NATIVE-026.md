# [Medium][NATIVE-026] Web clipboard fallback reports success before its promise resolves

<!-- nativecmpkit-item:audit:NATIVE-026 -->
## Classification
- **Finding:** NATIVE-026
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-share`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt:58-93`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/webMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.web.kt#L58-L93) — `shareText/shareUrl clipboard fallback`
- [`calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt:35-37`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/jsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.js.kt#L35-L37) — `copyToClipboard`
- [`calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt:80-81,126-128`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/wasmJsMain/kotlin/com/mohamedrejeb/calf/share/WebShareApi.wasmJs.kt#L80-L81) — `jsCopyToClipboard`

## Root cause
copyToClipboard discards navigator.clipboard.writeText Promise and returns Unit. The caller immediately reports Success in a synchronous try/catch; asynchronous permission/insecure-context rejections bypass that catch and have no rejection handler.

## Impact and preconditions
Unsupported native sharing can falsely report a successful copy while nothing reaches the clipboard and an unhandled rejection is emitted. The user loses a fallback action without useful feedback.

## Supporting evidence
- Standalone Node result outcomes=[Success], unhandledRejection=true for a rejected writeText promise.

## Recommended solution
Return/await clipboard completion via callback/promise/suspend interop and map rejection to a real unavailable/failure outcome. Check secure context/API support and preserve user activation requirements.

## Risks and compatibility
The Node proof uses the exact Wasm JS body with a mocked rejection, not real clipboard permission UI. Browser integration must test both JS/Wasm and real activation. Never read unrelated clipboard contents in tests.

## Required tests / acceptance criteria
- Rejected NotAllowedError promise produces no Success and no unhandled rejection.
- Resolved promise produces one Success only after completion.
- Missing clipboard API, insecure context, denied permission and direct user gesture.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/508
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
