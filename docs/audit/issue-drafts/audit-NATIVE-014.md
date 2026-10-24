# [Medium][NATIVE-014] Desktop cookie expiry is recalculated from read time and drifts into the future

<!-- nativecmpkit-item:audit:NATIVE-014 -->
## Classification
- **Finding:** NATIVE-014
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:30-37,50-54`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L30-L37) — `setCookie/getCookies expiresDate mapping`

## Root cause
HttpCookie.maxAge is a lifetime measured from creation, not remaining time. getCookies converts it to epoch expiry using current time on every read rather than preserving the creation timestamp/original expiry.

## Impact and preconditions
Repeated reads report later and later expiration while the Java cookie store still expires at the original time. Code persisting or copying those returned cookies can extend sessions unintentionally and show misleading session lifetime.

## Supporting evidence
- Actual Desktop CookieManager probe reported +1201ms expiry drift after ~1.2s without rewriting the cookie.

## Recommended solution
Preserve an absolute expiry in controlled metadata or use a backend exposing creation/expiry; otherwise explicitly mark expiry unavailable rather than inventing it. Keep session/maxAge=0 distinctions.

## Risks and compatibility
The store itself still expires cookies; this finding concerns exposed metadata and downstream copying. Avoid relying on inaccessible JDK internals to read creation time.

## Required tests / acceptance criteria
- Set a cookie with a known future expiry; reads separated in time remain at the same absolute expiry.
- Roundtrip returned cookie to another store without increasing lifetime.
- Session, already-expired, near-second-boundary and overflow-sized timestamps.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/425
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
