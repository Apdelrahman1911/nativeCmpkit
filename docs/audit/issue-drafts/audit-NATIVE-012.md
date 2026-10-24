# [Medium][NATIVE-012] Desktop and iOS getCookies do not implement full request-URL cookie matching

<!-- nativecmpkit-item:audit:NATIVE-012 -->
## Classification
- **Finding:** NATIVE-012
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt:42-57`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.desktop.kt#L42-L57) — `getCookies`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt:75-103`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/CookieManager.ios.kt#L75-L103) — `getCookies domain-only filtering`

## Root cause
Desktop returns CookieStore.get(uri), which does not apply request-path matching performed by CookieManager.get. iOS fetches all cookies and filters only on host/domain suffix, ignoring path and secure scheme, and cannot express host-only scope in the public Cookie model.

## Impact and preconditions
Returned cookies may not be applicable to the requested URL. Callers copying results into request headers can leak a path-restricted token or, on iOS, a Secure cookie into a non-HTTPS request. This API does not itself send the cookie or alter WebKit request filtering.

## Supporting evidence
- Actual Desktop CookieManager standalone probe returned a cookie restricted to /private for https://audit.invalid/public/.
- iOS filter at86-92 uses only host/domain; no scheme/path predicates occur.

## Recommended solution
Specify whether the method lists storage metadata or cookies applicable to a request. If request matching is intended, implement RFC6265 host-only/domain/path/secure/expiry rules or use the native request-cookie API; otherwise rename/add a scoped method and document restrictions.

## Risks and compatibility
Desktop path mismatch was executed; iOS matching was source-reviewed only. Native browser cookie enforcement itself is not shown to be broken. Cookie path is not a general same-origin security boundary, but callers still must not forward inappropriate credentials.

## Required tests / acceptance criteria
- Domain exact/subdomain/host-only, /private versus /public, /foo versus /foobar paths.
- Secure cookie queried over HTTP versus HTTPS and expiry boundary.
- Compare returned set with actual native HTTP request headers, including duplicate names on different paths.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/425
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
