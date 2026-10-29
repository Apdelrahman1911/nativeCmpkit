<!-- nativecmpkit-upstream-sync:674932206:34 -->
<!-- source-fingerprint:07db64e27168bf9370097a6be4a2c877f5521818606d5e43acd68ddef037a155 -->
## Current upstream context: Calf #34

Original: [Camera issue in webview iOS](https://github.com/MohamedRejeb/Calf/issues/34) — [ssvaghasiya](https://github.com/ssvaghasiya); created `2023-10-09T12:28:12Z`, updated `2025-03-10T22:02:35Z`; upstream state **open**.
Original IDs: `1932958429` / `I_kwDOKDql7s5zNprd`. Original labels: None.

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant as an unverified reproduction target; the original report does not establish a current root cause.

The 2023 report concerns camera presentation inside WKWebView, not calf-camera-picker. No current device reproduction or exact causal line is available. WKWebView still has delegate/presentation integration, so archive the report rather than treating it as resolved or confirmed.

**Next step:** Reproduce web-page camera capture/cancel on current iOS hardware and iPad with a minimal page; record whether host/navigation or permission delegates dismiss the view.

Primary tracking: #168. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:54-141`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L54-L141) — `WebView iOS creation and lifecycle`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:197-249`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L197-L249) — `WK navigation callbacks`

### Original issue description (verbatim Markdown)
````markdown
When i open camera and close camera in webview webview close automatically

example video:
https://github.com/MohamedRejeb/Calf/assets/49331161/729e7d71-5681-4697-81b1-d62fcc38592f


````

### Original public discussion (1 comments)

**[the-best-is-best](https://github.com/the-best-is-best)** — created `2025-03-10T22:02:34Z`, updated `2025-03-10T22:02:34Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/34#issuecomment-2711946671); IDs `2711946671` / `IC_kwDOKDql7s6hpQWv`.
````markdown
Camera not work in simulator 
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/34/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/34/comments.json)
- [Full public timeline: 2 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/34/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-10-24T16:25:11Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/34)); [[Medium][Upstream #34] Camera issue in webview iOS](https://github.com/Apdelrahman1911/nativeCmpkit/issues/168).
