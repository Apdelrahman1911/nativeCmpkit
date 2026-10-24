# [Low][NATIVE-036] Desktop customUserAgent cannot be reset to its documented default using null

<!-- nativecmpkit-item:audit:NATIVE-036 -->
## Classification
- **Finding:** NATIVE-036
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:162-169`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L162-L169) — `DesktopSettings.customUserAgent`
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:215-221`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L215-L221) — `WebView.applySettings`

## Root cause
The nullable setting documents null as the default user agent, but applySettings only assigns engine.userAgent inside customUserAgent?.let. After a custom value is installed, assigning null notifies settings but never restores the original value.

## Impact and preconditions
A state reused across pages/accounts continues advertising an obsolete custom user agent despite its public setting being null. Host-specific authentication/content negotiation behavior can persist unexpectedly.

## Supporting evidence
- DesktopSettings documentation says If null, the default user agent is used; native setter has no else branch.

## Recommended solution
Capture the engine default user agent at creation or use a supported reset strategy and assign that value when the public setting becomes null. Document initial versus runtime semantics.

## Risks and compatibility
This is a source-confirmed missing reset, not a measured JavaFX integration behavior. Changing null behavior is a corrective API change but can affect applications accidentally relying on stale headers.

## Required tests / acceptance criteria
- Set custom A, change to B, reset null and inspect actual request User-Agent/default engine value.
- Multiple WebView instances preserve their individual defaults.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
