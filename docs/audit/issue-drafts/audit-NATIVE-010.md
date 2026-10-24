# [High][NATIVE-010] Enabling Web JavaScript removes all iframe isolation for inline HTML

<!-- nativecmpkit-item:audit:NATIVE-010 -->
## Classification
- **Finding:** NATIVE-010
- **Priority:** High
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:57-58,169-176,225-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L57-L58) — `HTML content and iframe.applySettings`

## Root cause
javaScriptEnabled=true removes the sandbox attribute entirely. srcdoc then inherits the host origin; scripts in supplied inline HTML can access the parent DOM, same-origin storage and host-page capabilities. There is no separate sandbox/origin policy in the common API.

## Impact and preconditions
If an application renders untrusted HTML with JavaScript enabled, content that would be isolated inside a native WebView instead obtains the browser host application origin. A browser probe changed the host DOM using only child script; exploitation requires attacker-controlled HTML and the explicit JS opt-in.

## Supporting evidence
- Real Chrome153 probe unsandboxedSrcdocCanModifyHost=true using a local harmless parent attribute change.
- Disabled mode sets sandbox without allow-scripts; enabled mode removes every sandbox restriction.

## Recommended solution
Expose a distinct sandbox/trusted-content policy with safe defaults; for untrusted HTML use an opaque-origin sandbox allowing only needed capabilities and a validated postMessage bridge. Warn that enabling scripts is not merely toggling execution in an isolated native container.

## Risks and compatibility
This is not an unconditional XSS or sandbox bypass: default JavaScript is false, normal cross-origin pages still have same-origin restrictions, and browser CSP may constrain effects. allow-scripts plus allow-same-origin for same-origin/srcdoc content is not robust isolation.

## Required tests / acceptance criteria
- Untrusted inline script cannot read/mutate parent DOM or storage under isolated mode.
- Trusted mode preserves deliberate integration and is explicitly opted into.
- Test popups/forms/top navigation, nested frames, postMessage origin validation and CSP.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/431
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
