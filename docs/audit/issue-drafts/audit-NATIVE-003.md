# [Medium][NATIVE-003] Android and iOS onCreated run before the advertised native WebView reference exists

<!-- nativecmpkit-item:audit:NATIVE-003 -->
## Classification
- **Finding:** NATIVE-003
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt:47-48,194-209`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt#L47-L48) — `WebView factory/onCreated`
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:48-49,111-125`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L48-L49) — `UIKitView.factory`

## Root cause
Both mobile factories call the public zero-argument onCreated callback before assigning state.webView. Documentation explicitly directs callers to that property inside onCreated. Android additionally applies settings and replaces clients after the callback.

## Impact and preconditions
First creation callbacks see null and silently fail to customize the native view; remount can expose a stale old Android view. Cross-platform configuration code works on Desktop/Web but not the advertised mobile hook.

## Supporting evidence
- Android invokes onCreated at197 then assigns state.webView at209.
- iOS invokes onCreated at114 then assigns state.webView at123.

## Recommended solution
Assign the native instance before invoking the public callback and document settings/client ordering. Prefer an additive platform-typed customization hook if native callbacks must remain internally owned.

## Risks and compatibility
Reordering may alter applications relying on current settings precedence; lock down behavior rather than simply moving callbacks past every configuration write.

## Required tests / acceptance criteria
- Assert native reference identity inside onCreated on all targets.
- Configure a native setting and verify whether common settings intentionally override it.
- Retain state across remount and verify callback never observes the previous instance.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/428
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
