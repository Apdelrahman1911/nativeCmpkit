# [Medium][NATIVE-005] WebView request state is not reset consistently on Desktop, iOS and Web

<!-- nativecmpkit-item:audit:NATIVE-005 -->
## Classification
- **Finding:** NATIVE-005
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt:60-90`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt#L60-L90) — `loadWorker state listener`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:208-247,345-383`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L208-L247) — `WKNavigationDelegate and KVO`
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-65,76-95,183-228`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50-L65) — `content/navigation loaders and iframe listeners`

## Root cause
Desktop RUNNING does not clear errorsForCurrentRequest. iOS clears errors only at didCommitNavigation, so consecutive provisional failures accumulate old errors. Web never sets Loading when changing src/srcdoc and never clears prior errors/title; its cross-origin load handler cannot read URL/title and leaves old values. Web navigation capability flags are unconditionally false.

## Impact and preconditions
A successful retry can retain an old error, a new request can appear Finished, and cross-origin content may display a previous page title/URL. Consumers deriving loading/error/security UI from common state receive inconsistent or stale signals.

## Supporting evidence
- Android onPageStarted resets errors/title, providing the existing comparison behavior.
- Desktop writes errors only on FAILED; iOS reset is didCommit only; Web event source has no Loading assignment anywhere.

## Recommended solution
Centralize begin-request state reset and terminal-state handling; separate requested URL from observable final URL; explicitly represent unknown cross-origin title/history. Clear errors at provisional request start on iOS and RUNNING on Desktop. Do not infer iframe load success from the load event alone.

## Risks and compatibility
Browser deliberately hides many iframe errors and cross-origin metadata; do not promise reliable progress/final URL or bypass same-origin policy. History capability may need an explicit unsupported state rather than invented booleans.

## Required tests / acceptance criteria
- Fail→success, fail→fail, reload, stop and redirects on every target.
- Browser same-origin→cross-origin→inline transitions; blocked framing and offline destination.
- iOS provisional DNS/TLS failure before commit resets the previous request errors.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/426
- https://github.com/MohamedRejeb/Calf/pull/466
- https://github.com/MohamedRejeb/Calf/issues/39
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
