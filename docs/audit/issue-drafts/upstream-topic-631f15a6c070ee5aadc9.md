# [Low][Upstream #72] Zoom in/out in browser

<!-- nativecmpkit-item:upstream-topic:631f15a6c070ee5aadc9 -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/72 (#72, issue)
- **Original author:** `rcd27`
- **Original ID:** `2166082242`; node ID `I_kwDOKDql7s6BG8rC`
- **Original creation / update:** `2024-03-04T06:59:09Z` / `2024-03-04T07:28:53Z`
- **Original state at observation:** `open`
- **Priority:** Low
- **Assessment:** `needs_reproduction` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
Browser zoom/focus mismatch was reported against the 2024 rendering stack. The baseline sample now enters ComposeViewport and no exact current library-level coordinate bug is demonstrated by the report. The maintainer asked whether this was Desktop in comment1975890950; the actual host remains ambiguous in the archived exchange.

- [`sample/web-js/src/jsMain/kotlin/Main.kt:1-20`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/web-js/src/jsMain/kotlin/Main.kt#L1-L20) — `ComposeViewport sample entrypoint`
- [`sample/web-wasm/src/wasmJsMain/kotlin/Main.kt:1-17`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/sample/web-wasm/src/wasmJsMain/kotlin/Main.kt#L1-L17) — `ComposeViewport Wasm sample entrypoint`

## Recommended next step
Add current JS/Wasm zoom/devicePixelRatio/pointer/keyboard smoke reproduction on Chromium, Firefox and Safari; route to Compose/Skiko if library-independent. First confirm whether the original reporter meant browser or desktop WebView zoom.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `web-zoom-focus-reproduction`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
