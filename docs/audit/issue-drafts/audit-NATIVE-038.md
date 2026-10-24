# [Medium][NATIVE-038] Android enables multiple WebView windows but supplies no window-creation handler

<!-- nativecmpkit-item:audit:NATIVE-038 -->
## Classification
- **Finding:** NATIVE-038
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:99-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L99-L103) — `AndroidSettings.supportMultipleWindows default`
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:104-106,233-239,309-328`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L104-L106) — `settings and AccompanistWebChromeClient`

## Root cause
supportMultipleWindows defaults true and is applied to Android WebSettings, but the installed WebChromeClient implements only title, icon and progress callbacks. It never overrides onCreateWindow; Android defaults reject creation. The public common WebView API also does not accept a custom chrome client.

## Impact and preconditions
Pages using target=_blank or window.open can request a new window that is never displayed, even with javaScriptCanOpenWindowsAutomatically=true. Browser/payment/login flows depending on popup navigation can silently fail.

## Supporting evidence
- AccompanistWebChromeClient overrides only onReceivedTitle, onReceivedIcon, onProgressChanged.
- AndroidSettings defaults supportMultipleWindows=true; native applySettings calls setSupportMultipleWindows.

## Recommended solution
Choose and document a safe popup policy: reject explicitly, load allowed same-view requests, or expose/manage child windows with a trusted host callback. Do not enable multiple-window support without a handler and do not automatically open untrusted external schemes.

## Risks and compatibility
Source confirms the missing handler/configuration mismatch; exact Android link fallback behavior is WebView/version/content-dependent and needs device reproduction. Creating windows adds origin, lifecycle and phishing concerns; policy must be explicit.

## Required tests / acceptance criteria
- target=_blank link and user-initiated/scripted window.open with JavaScript/settings combinations.
- Accepted and denied popup origins/schemes yield documented outcomes.
- Child window closure, back navigation and dispose release all resources.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
