# [Low][Upstream #343] Support native file preview

<!-- nativecmpkit-item:upstream-topic:7a9f2e0f6e37e239b233 -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/343 (#343, issue)
- **Original author:** `MohamedRejeb`
- **Original ID:** `3246327607`; node ID `I_kwDOKDql7s7Bfwc3`
- **Original creation / update:** `2025-07-20T12:41:26Z` / `2025-07-20T12:41:26Z`
- **Original state at observation:** `open`
- **Priority:** Low
- **Assessment:** `separate_improvement` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
No dedicated native file-preview API/module exists. Desktop share opening a file is not a portable preview abstraction or iOS Quick Look implementation.

- [`settings.gradle.kts:28-60`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/settings.gradle.kts#L28-L60) — `included modules`
- [`calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt:1-59`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-share/src/commonMain/kotlin/com/mohamedrejeb/calf/share/ShareContent.kt#L1-L59) — `share content API, not preview`

## Recommended next step
Record native preview as an opt-in future module: define unsupported/cancel/error behavior, file-access lifetime and platform viewer capabilities before selecting dependencies.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `native-file-preview`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
