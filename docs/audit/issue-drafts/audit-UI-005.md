# [Low][UI-005] Single-date state loses displayed-month intent on iOS and save/restore

<!-- nativecmpkit-item:audit:UI-005 -->
## Classification
- **Finding:** UI-005
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.ios.kt:35-40,96-115`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.ios.kt#L35-L40) — `AdaptiveDatePickerState / Saver`
- [`calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.material.kt:120-139`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/materialMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.material.kt#L120-L139) — `Saver`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt:84-100`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt#L84-L100) — `rememberDatePickerManager`

## Root cause
Single-date Savers persist selection/years/modes but not the displayed month and restore it from selection. The iOS native manager never receives initialDisplayedMonthMillis at all.

## Impact and preconditions
A picker intentionally opened on a month different from its selection ignores that request on iOS; Material month navigation is lost on state restoration. Null selection can restore the current month instead of the user position.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- Both Savers restore initialDisplayedMonthMillis=value[0], which is selectedDateMillis.
- DatePickerManager constructor is given only the selected date, presentation and callbacks.

## Recommended solution
Define displayed-month state explicitly, forward initial display intent to the backend and include restorable month state in a version-compatible Saver. Preserve support for the historical five-element saved list.

## Risks and compatibility
Do not claim identical native and Material calendar navigation APIs already exist; adding observation of native displayed month needs platform tests and may need an additive API.

## Required tests / acceptance criteria
- Selected month differs from displayed month, with/without a selection.
- Save/restore after month navigation; legacy five-element input.
- Native compact/wheels/inline appropriate behavior.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/541
- https://github.com/MohamedRejeb/Calf/issues/543
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
