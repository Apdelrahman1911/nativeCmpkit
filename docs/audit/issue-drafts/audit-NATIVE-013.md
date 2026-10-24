# [High][NATIVE-013] Desktop CookieManager overwrites JavaFX and application-global cookie handlers

<!-- nativecmpkit-item:audit:NATIVE-013 -->
## Classification
- **Finding:** NATIVE-013
- **Priority:** High
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:13-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L13-L20) — `cookieManager getter`

## Root cause
Any default CookieHandler not deriving from java.net.CookieManager is replaced by a new empty java.net.CookieManager. JavaFX19 WebPage normally installs com.sun.webkit.network.CookieManager, which extends CookieHandler directly, so even a first read can replace the active WebKit cookie store. Application custom handlers are likewise replaced.

## Impact and preconditions
Cookie operations can discard access to existing login cookies and change networking behavior for every component using the process-global handler. JavaFX uses special javascript/javascripts schemes for document.cookie filtering, so substituting an unrelated handler also requires semantic compatibility review.

## Supporting evidence
- Standalone actual CookieManager probe COOKIE_HANDLER_REPLACED true.
- JavaFX19 WebPage.java141-146 installs com.sun.webkit.network.CookieManager; that class extends CookieHandler, not java.net.CookieManager.

## Recommended solution
Do not mutate global state during a getter. Establish explicit cookie-store ownership at toolkit initialization, preserve/adapt compatible handlers, or expose a deliberate application-supplied backend. Handle JavaFX’s store and concurrent access without silently replacing it.

## Risks and compatibility
A custom-handler replacement was executed against the actual Kotlin cookie class. JavaFX default installation/type were verified in the exact 19 source archive; loss of a real logged-in JavaFX session remains a required GUI integration test. No private com.sun API adoption without maintenance assessment.

## Required tests / acceptance criteria
- Login in a real WebEngine, call getCookies, then ensure session and handler identity remain valid.
- Install a custom CookieHandler before creation and verify library does not overwrite it.
- Two managers accessed concurrently and secure/HttpOnly document.cookie behavior under the chosen backend.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/425
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
