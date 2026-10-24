# [Low][Upstream #471] Feature request: iOS-native styling customization for AdaptiveNavigationBar and AdaptiveTopBar

<!-- nativecmpkit-item:upstream-topic:80b18aaaa4c8a57bea15 -->
## Imported actionable historical item
- **Original:** https://github.com/MohamedRejeb/Calf/issues/471 (#471, issue)
- **Original author:** `antoniokranjcina`
- **Original ID:** `4126530434`; node ID `I_kwDOKDql7s719duC`
- **Original creation / update:** `2026-03-24T09:43:20Z` / `2026-04-03T16:58:23Z`
- **Original state at observation:** `open`
- **Priority:** Low
- **Assessment:** `separate_improvement` — not a newly confirmed bug unless separately demonstrated.

This is a newly created nativeCmpkit issue. GitHub author/timestamp/number metadata cannot be transplanted faithfully. The original full text, comments, timelines and public revisions remain in the independent [raw archive](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata).

## Current-source assessment / evidence
PR499 implements selected tint, pre-iOS26 unselected tint and title color only. Maintainer comment4184266309 leaves iOS26 unselected tint and title font/typography unchecked. Baseline configuration has no title typography field and explicitly documents the Liquid Glass unselected-color limitation.

- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt:6-22`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitNavigationBarConfiguration.kt#L6-L22) — `UIKitNavigationBarConfiguration`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt:6-24`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/navigation/UIKitTabBarConfiguration.kt#L6-L24) — `UIKitTabBarConfiguration`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt:64-87`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/TabBarManager.kt#L64-L87) — `updateConfiguration`

## Recommended next step
Preserve only the remaining styling requirements; design optional typography/font-resource mapping and iOS26 appearance support without changing unspecified native defaults.

## Risks and required verification
Do not treat the historical report as a current reproduction, or an implemented permission as a complete data API. Define explicit platform capability, unsupported/error/cancel behavior and compatibility before implementing. Add a minimal current-baseline reproduction or a scoped acceptance test matrix; record runtime/OS/browser versions and classify confirmed behavior separately from assumptions. No major rewrite or release is authorized by this issue.

## Deduplication / rationale
Stable topic key: `ios-native-bar-styling-remainder`. Disposition and code references are preserved in [upstream-actionable-decisions.json](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/migration/upstream-actionable-decisions.json). Already implemented requests and requests covered by audit findings are not blindly recreated.
