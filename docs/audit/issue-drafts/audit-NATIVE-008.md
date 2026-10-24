# [Medium][NATIVE-008] Replay-one navigation flow replays transient back/forward/stop commands on reattachment

<!-- nativecmpkit-item:audit:NATIVE-008 -->
## Classification
- **Finding:** NATIVE-008
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt:159-179,227-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt#L159-L179) — `NavigationEvent and navigationEvents`
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:157-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L157-L160) — `navigation collector`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:112-115`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L112-L115) — `navigation collector`

## Root cause
All navigation commands share MutableSharedFlow(replay=1). A new collector receives the last command even after it was already consumed by an old native view; no acknowledgement/reset distinguishes retained content from one-shot actions.

## Impact and preconditions
Recreating/rebinding a WebView can repeat Back, Forward, Reload or StopLoading unexpectedly. With NATIVE-001, a retained StopLoading can restart the feedback loop. Sharing a navigator across views broadcasts commands to both without an ownership contract.

## Supporting evidence
- Exact common Navigator compiled in standalone probe; first() subscriptions observed Back twice after one navigateBack call.

## Recommended solution
Separate persistent desired content from one-shot commands, or add an explicit owner/acknowledgement strategy. Choose and document what happens to commands sent before attachment rather than replacing replay=1 blindly.

## Risks and compatibility
Changing to replay=0 without buffering breaks pre-attachment loadUrl/loadHtml calls, including saveable-state patterns. Preserve these intentionally with tests.

## Required tests / acceptance criteria
- Consume Back then replace collector; second collector must not repeat it.
- A load sent before first attachment is processed exactly once.
- Two WebViews with one navigator are either rejected/documented or have deliberate broadcast behavior.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
