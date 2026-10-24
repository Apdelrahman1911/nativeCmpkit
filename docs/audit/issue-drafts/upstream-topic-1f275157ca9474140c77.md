# [Medium][Upstream #34] Camera issue in webview iOS

<!-- nativecmpkit-item:upstream-topic:1f275157ca9474140c77 -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/34 (#34, issue)
- **Original author:** `ssvaghasiya`
- **Original ID:** `1932958429`; node ID `I_kwDOKDql7s5zNprd`
- **Original creation / update:** `2023-10-09T12:28:12Z` / `2025-03-10T22:02:35Z`
- **Original state at observation:** `open`
- **Priority:** Medium
- **Assessment:** `needs_reproduction` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
The 2023 report concerns camera presentation inside WKWebView, not calf-camera-picker. No current device reproduction or exact causal line is available. WKWebView still has delegate/presentation integration, so archive the report rather than treating it as resolved or confirmed.

- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:54-141`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L54-L141) — `WebView iOS creation and lifecycle`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:197-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L197-L249) — `WK navigation callbacks`

## Recommended next step
Reproduce web-page camera capture/cancel on current iOS hardware and iPad with a minimal page; record whether host/navigation or permission delegates dismiss the view.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `ios-webview-camera-dismissal`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
