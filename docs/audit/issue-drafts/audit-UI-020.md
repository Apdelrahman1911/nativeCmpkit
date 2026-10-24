# [High][UI-020] Native bar measurement permanently stops after several stable frames

<!-- nativecmpkit-item:audit:UI-020 -->
## Classification
- **Finding:** UI-020
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt:144-175`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt#L144-L175) — `native-height LaunchedEffect`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt:141-176`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveNavigationBar.ios.kt#L141-L176) — `native-height LaunchedEffect`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/IosBarHeightCache.kt:17-59`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/IosBarHeightCache.kt#L17-L59) — `IosBarHeightCache`

## Root cause
Frame-based height observation exits once more than six consecutive measurements are equal. No layout/trait/safe-area observation restarts it for rotation or later changes; the last height is also cached globally rather than per window/trait context.

## Impact and preconditions
Scaffold padding/placeholder height can remain sized for a previous orientation, safe area or large-title state, causing visible gaps/overlap. Upstream#548 reports a matching rotation reproduction.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Both measurement loops break after stableMeasurements>6.
- No event restarts the same effect for a later view-frame change.

## Recommended solution
Replace one-shot stabilization with lifecycle-scoped native layout/safe-area/trait callbacks, or another inexpensive persistent observation. Cache by relevant window/traits or use only estimates until real layout is available.

## Risks and compatibility
The stale-observation mechanism is source-confirmed and upstream-reported, not locally reproduced on an iOS device. Do not add a permanent busy frame loop without profiling.

## Required tests / acceptance criteria
- Rotate repeatedly after several seconds of stable layout.
- Dynamic Type, large-title toggle, split view, safe-area changes and multiple windows.
- Tab/top bar insertion/removal and cached-height cold start.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/548
- https://github.com/MohamedRejeb/Calf/issues/476
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
