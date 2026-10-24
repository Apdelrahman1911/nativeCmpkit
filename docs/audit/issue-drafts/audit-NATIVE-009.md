# [Medium][NATIVE-009] iOS captureBackPresses=false is overridden by settings and URL loads

<!-- nativecmpkit-item:audit:NATIVE-009 -->
## Classification
- **Finding:** NATIVE-009
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt:83-92,111-124,251-258`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/iosMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.ios.kt#L83-L92) — `URL load, factory and applySettings`
- [`calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt:140-146`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebSettings.kt#L140-L146) — `IosSettings.allowsBackForwardNavigationGestures`

## Root cause
Factory first assigns allowsBackForwardNavigationGestures=captureBackPresses, then applySettings assigns the independent setting whose default is true. Every state-driven URL load also unconditionally sets the property true.

## Impact and preconditions
Disabling captureBackPresses cannot reliably disable swipe navigation; setting the iOS flag false is undone by subsequent URL content changes. Applications with sensitive/special back navigation may unexpectedly leave a page.

## Supporting evidence
- Default true settings overwrite captureBackPresses at factory time; line91 forces true again.

## Recommended solution
Define precedence (for example captureBackPresses AND the iOS option), apply it from a single update path, and remove the unconditional URL-load assignment. Observe captureBackPresses changes on recomposition.

## Risks and compatibility
Fixing precedence changes behavior for consumers accidentally relying on the override; document the intended combined contract.

## Required tests / acceptance criteria
- All combinations of captureBackPresses and iOS setting at creation, mutation, URL load and recomposition.
- Swipe-back/forward test on real iPhone/iPad confirms false actually disables gestures.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/428
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
