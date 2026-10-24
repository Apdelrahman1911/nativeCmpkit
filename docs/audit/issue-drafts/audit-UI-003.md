# [Medium][UI-003] Replacing iOS date state can skip initialization effects for the new native picker

<!-- nativecmpkit-item:audit:UI-003 -->
## Classification
- **Finding:** UI-003
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt:58-65,84-101,119-145`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt#L58-L65) — `rememberDatePickerManager / SyncNativeDatePicker`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.ios.kt:50-65,75-102`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.ios.kt#L50-L65) — `AdaptiveDateRangePicker`

## Root cause
Managers/backends are correctly remembered by state identity and UIKitView is keyed by manager, but synchronization effects are outside that key and depend only on individual values. A new state with equal rules/colors/selection/direction/enabled does not restart those effects for the new view.

## Impact and preconditions
A replaced native picker may retain default appearance/direction/bounds/enabled behavior even though the API parameters are unchanged. Compact disabled state is especially relevant when a fresh native manager is created.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- remember(state) and key(manager) exist, but LaunchedEffect(layoutDirection), LaunchedEffect(state.selectableDates) and color/enabled effects omit manager.

## Recommended solution
Key every native synchronization effect by its manager/backend as well as the relevant data, or place creation and synchronization inside a manager-keyed composition group. Include presentation in the manager key if it can vary independently.

## Risks and compatibility
Avoid recreating managers on every recomposition or reintroducing stale-state callbacks. Initial selection is supplied to the constructor, so not every property is missing in every replacement.

## Required tests / acceptance criteria
- Replace state A with state B that has equal selected date/rule/colors and inspect native min/max, tint, RTL and enabled state.
- Repeat for compact disabled fields and range picker.
- Recompose without identity changes and assert no redundant view recreation.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/541
- https://github.com/MohamedRejeb/Calf/issues/543
- https://github.com/MohamedRejeb/Calf/issues/544
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
