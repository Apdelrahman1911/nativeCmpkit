# [Low][Upstream #259] Demonstration of AdaptiveCircularProgressIndicator in AdaptiveAlertDialog

<!-- nativecmpkit-item:upstream-topic:5098a291f843be33ed16 -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/259 (#259, issue)
- **Original author:** `lemkoleg`
- **Original ID:** `2861084678`; node ID `I_kwDOKDql7s6qiLAG`
- **Original creation / update:** `2025-02-18T17:11:00Z` / `2025-02-18T17:11:00Z`
- **Original state at observation:** `open`
- **Priority:** Low
- **Assessment:** `separate_improvement` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
Common alert exposes materialText/materialContent slots but iOS uses native UIAlertController descriptors and text. The requested adaptive busy/progress-dialog example is not available as a uniform arbitrary native Compose content slot.

- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt:65-122`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.kt#L65-L122) — `AdaptiveAlertDialog and AdaptiveBasicAlertDialog`

## Recommended next step
Design/document an explicit busy-dialog example with cancel/accessibility semantics and a deliberate iOS presentation strategy; avoid silently inserting unsupported Material content into UIKit.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `adaptive-busy-dialog-example`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
