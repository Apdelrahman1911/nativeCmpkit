# [High][UI-018] Sheet operation cancellation and disposal can leave native presentation and retained owners behind

<!-- nativecmpkit-item:audit:UI-018 -->
## Classification
- **Finding:** UI-018
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt:46-54,61-99`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/SheetState.ios.kt#L46-L54) — `iosSheetManager / deferredUntilShown / deferredUntilHidden`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt:92-127,133-149`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt#L92-L127) — `show / hide`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt:104-105,132-145`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/AdaptiveBottomSheet.ios.kt#L104-L105) — `manager attachment / DisposableEffect`

## Root cause
show/hide return false during animation instead of queueing/awaiting the desired transition. Deferred objects are reset only after a successful await, so cancellation can reuse an already completed deferred. Disposal makes a single hide attempt, immediately forces state Hidden, and never clears the state-to-manager reference; the effect is keyed by Unit rather than its owners.

## Impact and preconditions
Rapid navigation/removal can leave a native sheet displayed after Compose considers it hidden. Later operations may complete before their animations. Hoisted state can retain the presenting controller, sheet controller, content and composition-local context after disposal. Public suspend methods also lack UI-thread confinement.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- deferredUntilShown/Hidden are fields reset after await with no finally.
- hide returns false when !isPresented||isAnimating.
- onDispose ignores hide result and does not set iosSheetManager=null.

## Recommended solution
Use per-operation completion tokens and a serialized, cancellation-safe presentation state machine confined to Main. Ensure disposal records a terminal cleanup request even during animation, detaches only its own manager reference, and releases content/controller ownership when safe.

## Risks and compatibility
Lost hide and stale-deferred paths are source-confirmed. Persistent heap growth and background-thread crashes are risks, not profiled/reproduced facts. Preserve content-local propagation for nested native widgets.

## Required tests / acceptance criteria
- show then hide before show completes; dispose during either animation.
- Cancel a show/hide waiter, complete native animation, then repeat the operation; await duration must be correct.
- Concurrent callers, owner/state/controller replacement, off-main call policy, weak-reference/heap checks after disposal.

## Dependencies
- UI-016
- UI-017

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/37
- https://github.com/MohamedRejeb/Calf/issues/75
- https://github.com/MohamedRejeb/Calf/issues/77
- https://github.com/MohamedRejeb/Calf/issues/408
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
