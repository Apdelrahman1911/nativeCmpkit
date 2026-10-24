# [High][UI-021] Native bars live outside the Compose layout/transition hierarchy

<!-- nativecmpkit-item:audit:UI-021 -->
## Classification
- **Finding:** UI-021
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt:126-137,185-202`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt#L126-L137) — `DisposableEffect / placeholder Box`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt:120-134,186-203`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt#L120-L134) — `DisposableEffect / placeholder Box`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt:25-85`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveScaffold.ios.kt#L25-L85) — `AdaptiveScaffold`

## Root cause
UINavigationBar/UITabBar are inserted directly into the root UIViewController.view and constrained there; Compose receives a size/padding placeholder rather than a UIKitView tied to the composable bounds. The bar facade also drops the supplied modifier for its placeholder.

## Impact and preconditions
Compose clipping, visibility, route animation and input modifiers do not govern the native bar as callers expect. Outgoing/incoming routes can overlap bars or reveal the destination bar early during back gestures, matching open upstream#530.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Root addSubview/Auto Layout ownership is independent of the Compose placeholder node.
- Open#530 describes bar persistence during outgoing transitions; proposed native-controller integration was not implemented.

## Recommended solution
First specify ownership across routes and document current overlay behavior. Add transition tests and coordinate native attachment/visibility with the owner lifecycle. Evaluate UIKitView or per-screen controller integration only after this audit, not as an unreviewed architectural rewrite.

## Risks and compatibility
Some root-overlay placement may be intentional for native appearance. Upstream transition symptoms are preserved as reported evidence; exact behavior depends on host navigation and iOS.

## Required tests / acceptance criteria
- Push/pop animations and cancelled/completed interactive back gestures.
- Two screens with different/no bars, clipping/alpha/modifier changes, nested scaffolds.
- Native scroll-edge behavior, keyboard, safe areas and accessibility traversal order.

## Dependencies
- UI-020

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/530
- https://github.com/MohamedRejeb/Calf/issues/132
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
