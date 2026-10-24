# [Medium][NATIVE-011] Browser CookieManager silently misrepresents URL, expiry, HttpOnly and deletion support

<!-- nativecmpkit-item:audit:NATIVE-011 -->
## Classification
- **Finding:** NATIVE-011
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt:12-45`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.web.kt#L12-L45) — `setCookie/getCookies/removeAllCookies`
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt:10-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/Cookie.kt#L10-L22) — `Cookie contract`

## Root cause
Web setters append numeric epoch milliseconds directly as expires, whereas cookies require an HTTP date. URL parameters are ignored in favor of host document.cookie. JavaScript cannot set HttpOnly; the implementation appends that attribute anyway. Deletion always uses path=/ and has no original domain/path.

## Impact and preconditions
An already-expired cookie can become a session cookie, requested HttpOnly writes can be rejected, cross-origin URL queries return host cookies, and logout-style removeAllCookies leaves non-root-path/domain/HttpOnly cookies. Callers receive Unit/normal lists rather than capability/error information.

## Supporting evidence
- Chrome153: invalidExpiresRetainsExpiredCookie=true; httpOnlyAttemptRejected=true; rootOnlyDeletionLeavesPathCookie=true.
- Both url parameters are unused. Common CookieManager documentation still says Web is no-op, while source actively writes host cookies.

## Recommended solution
Format expiry as UTC HTTP date or valid Max-Age; reject unsupported foreign-origin/HttpOnly operations explicitly; scope browser cookie APIs to the actual document context; document that complete domain/path/HttpOnly clearing requires server cooperation and/or tracked cookie identities.

## Risks and compatibility
Chrome rejected the entire HttpOnly assignment; do not claim it created an insecure non-HttpOnly cookie. Browsers may vary. Reading HttpOnly cookies via JavaScript is intentionally impossible and must not be bypassed.

## Required tests / acceptance criteria
- Past/future expiry and session cookies in Chromium/Firefox/WebKit.
- Verify HttpOnly requests surface unsupported status rather than silent success.
- URL mismatch, path-specific/domain cookies and server-set HttpOnly logout cases.
- Cookie names/values containing delimiters are validated rather than changing attributes.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/425
- https://github.com/MohamedRejeb/Calf/pull/429
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
