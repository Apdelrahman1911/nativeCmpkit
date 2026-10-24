# [Medium][NATIVE-007] Non-Android saveable WebView state restores metadata but no content

<!-- nativecmpkit-item:audit:NATIVE-007 -->
## Classification
- **Finding:** NATIVE-007
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:319-331`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L319-L331) — `rememberSaveableWebViewState`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:251-268`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L251-L268) — `WebStateSaver`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:388-405`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L388-L405) — `WebStateSaver`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:232-250`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L232-L250) — `WebStateSaver`

## Root cause
Desktop, iOS and Web savers store title and lastLoadedUrl but restore WebContent.NavigatorOnly. No native history or pending load is restored, and no platform factory consumes lastLoadedUrl to initiate a load. NavigatorOnly is explicitly a no-op.

## Impact and preconditions
After restoration the visible native/browser view is blank while metadata still describes the former page. Saved history/scroll/form state are not portable despite the common saveable helper.

## Supporting evidence
- All three non-Android restorers construct WebViewState(WebContent.NavigatorOnly) and only assign metadata.

## Recommended solution
Define an honest per-platform persistence contract. Restore at least a safe requested URL with an explicit reload policy where native history is unavailable; document lost POST/form/history/scroll state and protect sensitive URL serialization. Keep full Android Bundle restore separate.

## Risks and compatibility
The current common comment mentions activity recreation; non-Android full session restore is not promised in detail. A change that automatically reloads URLs could repeat side effects or leak secrets, so expose/document the policy.

## Required tests / acceptance criteria
- Save/restore URL, HTML, navigator-only, redirect and null URL states on each target.
- Check restored content actually loads and title/history do not falsely describe a blank view.
- Ensure form submissions and one-time URLs are not automatically repeated without intended semantics.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
