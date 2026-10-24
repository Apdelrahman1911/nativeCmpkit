# [Medium][NATIVE-004] Web state-driven URL loading does not clear existing iframe srcdoc

<!-- nativecmpkit-item:audit:NATIVE-004 -->
## Classification
- **Finding:** NATIVE-004
- **Priority:** Medium
- **Evidence status:** `confirmed-test` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-webview`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt:50-59,220-226`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-webview/src/webMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.web.kt#L50-L59) — `state.content collector versus navigation LoadUrl`

## Root cause
WebContent.Data sets iframe.srcdoc. A later WebContent.Url only sets src; HTML iframe srcdoc takes precedence over src until the attribute is removed. The navigator LoadUrl branch already removes srcdoc but the state branch does not.

## Impact and preconditions
Switching from inline HTML to a URL through state/content recomposition leaves old HTML displayed and can expose stale authenticated or sensitive content despite the host believing a new URL was loaded.

## Supporting evidence
- Real Chrome153 probe stateUrlLeavesSrcdoc=true; navigatorUrlClearsSrcdoc=true.

## Recommended solution
Use one shared content loader for navigator and state paths and remove srcdoc before assigning src for every URL transition.

## Risks and compatibility
Chrome DOM reproduction mirrors exact source operations rather than compiling Compose Web; verify JS and Wasm integration after correction. Preserve inline HTML reload semantics.

## Required tests / acceptance criteria
- Data→Url→Data transitions via direct state assignment and remembered-state updates.
- Navigator and state loaders produce the same iframe attributes and page.
- Cross-origin destination with CSP/X-Frame-Options failure does not leave old content falsely reported as new.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/pull/429
- https://github.com/MohamedRejeb/Calf/pull/431
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/NATIVE.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/NATIVE.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
