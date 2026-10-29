<!-- nativecmpkit-upstream-sync:674932206:548 -->
<!-- source-fingerprint:d70b24bc40cb2e3f4e1a30b5b02454374f87bbe6a0d272a356c1d8d3b4446f1a -->
## Current upstream context: Calf #548

Original: [[Bug]:  AdaptiveTopBar (iOS): content top padding goes stale after device rotation](https://github.com/MohamedRejeb/Calf/issues/548) — [EEseka](https://github.com/EEseka); created `2026-09-14T18:37:32Z`, updated `2026-09-20T16:43:13Z`; upstream state **open**.
Original IDs: `5453160699` / `I_kwDOKDql7s8AAAABRQig-w`. Original labels: `bug` (#d73a4a; Something isn't working).

This comment preserves attributed public upstream material. It does not impersonate the original author, replace this issue's technical body, or transplant GitHub authorship/timestamps.

### Reconciled disposition
Still relevant; tracked by the existing nativeCmpkit finding rather than a duplicate issue.

Source corroborates the report: native top-bar measurement uses LaunchedEffect(Unit), stops after stable frames, and has no rotation/window-size restart. Initial safe-area and cached heights are remembered, so later orientation changes can leave padding stale.

**Next step:** Link UI geometry finding and test portrait↔landscape, split view, safe-area changes and prefersLargeTitles transitions; observe view geometry rather than a one-shot warmup loop.

Primary tracking: #32. Related existing tickets: none additional.
**Lifecycle:** keep the existing nativeCmpkit issue state and unrelated labels/content unchanged. Do not close a broader remaining bug because an old upstream symptom is source-addressed.

### Current-source assessment locations
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt:104-174`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/navigation/AdaptiveTopBar.ios.kt#L104-L174) — `initialSafeAreaTop and finite measurement effect`

### Original issue description (verbatim Markdown)
````markdown
### Steps to Reproduce

Calf 0.14.0 (also 0.13.0), Compose Multiplatform 1.12.0, iOS.

1. Build a screen with `AdaptiveScaffold` and an `AdaptiveTopBar` as its `topBar`.
2. Launch the app with the device in portrait and open that screen.
3. Rotate the device to landscape while staying on the screen.

Reverse case: open the screen in landscape, then rotate to portrait.

### Expected Behavior

The scaffold's top content padding updates to the new native navigation bar height and safe-area inset
after rotation, so the content sits directly below the bar in both orientations.

### Actual Behavior

The top padding keeps the value measured in the orientation the screen was opened in:

- Portrait → landscape: content keeps the portrait padding, leaving a large gap below the status bar.
- Landscape → portrait: the padding is too small, so content sits under the navigation bar.

Leaving the screen and coming back fixes it, because `AdaptiveTopBar` re-enters composition and measures again.

Cause: in `navigation/AdaptiveTopBar.ios.kt`, the height is measured in a `LaunchedEffect(Unit)` loop that
`break`s once `navBarHeightConsistencyCounter > 6` and is never restarted, so a rotation is never picked up.

Workaround: wrapping `AdaptiveTopBar` in `key(LocalWindowInfo.current.containerSize) { ... }` forces a
re-measure on rotation. A fix could restart the measurement when the view's size changes.

### Module

calf-ui

### Specify Other Module (if you selected "other" above)

_No response_

### Platform

iOS

### Library Version

latest
````

### Original public discussion (1 comments)

**[MohamedRejeb](https://github.com/MohamedRejeb)** — created `2026-09-20T16:43:13Z`, updated `2026-09-20T16:43:13Z`; [original comment](https://github.com/MohamedRejeb/Calf/issues/548#issuecomment-5751165501); IDs `5751165501` / `IC_kwDOKDql7s8AAAABVsvSPQ`.
````markdown
Hello
Thanks for reporting this issue, will check it.
````

### Relevant history and immutable evidence
- [Fresh original issue record](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/548/detail.json)
- [Full original comments](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/548/comments.json)
- [Full public timeline: 3 entries](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/source/issues/548/timeline.json)
- [Verified snapshot receipt](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/receipt.json) and [SHA256SUMS](https://github.com/Apdelrahman1911/nativeCmpkit/blob/__UPSTREAM_SYNC_ARCHIVE_COMMIT__/docs/migration/upstream-updates/20261029T012644Z/SHA256SUMS)
- Earlier original edit diffs, release/PR history and available attachment copies remain in `docs/migration/upstream-metadata/`; that frozen archive was not rewritten.
- `2026-09-14T18:37:34Z`: `labeled` by [EEseka](https://github.com/EEseka) ([event](https://api.github.com/repos/MohamedRejeb/Calf/issues/events/31122315134)); label `bug`.
- `2026-10-24T16:16:19Z`: `cross-referenced` by [Apdelrahman1911](https://github.com/Apdelrahman1911) ([event](https://github.com/MohamedRejeb/Calf/issues/548)); [[High][UI-020] Native bar measurement permanently stops after several stable frames](https://github.com/Apdelrahman1911/nativeCmpkit/issues/32).
