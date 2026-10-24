# [High][UI-001] iOS date state and native calendars do not enforce the documented UTC-day/year-range contract

<!-- nativecmpkit-item:audit:UI-001 -->
## Classification
- **Finding:** UI-001
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.ios.kt:35-53,61-72`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePickerState.ios.kt#L35-L53) — `AdaptiveDatePickerState.selectedDateMillis`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt:84-100,123-129`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt#L84-L100) — `rememberDatePickerManager / SyncNativeDatePicker`
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/SelectableDays.kt:138-160`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/SelectableDays.kt#L138-L160) — `isDaySelectable / snapSelectionToSelectable`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.ios.kt:50-62,79-82`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDateRangePicker.ios.kt#L50-L62) — `AdaptiveDateRangePicker`

## Root cause
Only the initial iOS single-date value is canonicalized; subsequent assignments are an unvalidated mutableState property. yearRange is stored but is neither validated by the iOS state constructor/setter nor intersected with native bounds or selection predicates. Native single/range callbacks likewise call only isSelectableDate, not isSelectableYear or the state yearRange.

## Impact and preconditions
A public property documented as UTC start-of-day can hold arbitrary intraday values and out-of-range years. Native calendars can offer years that Material-backed state rejects, creating divergent behavior and potentially a callback exception or native/local selection disagreement.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The iOS constructor advertises IllegalArgumentException at lines30-31 but has no corresponding require.
- selectedDateMillis uses mutableStateOf(canonical initial value) without a custom setter.
- Native applyDateBounds receives only state.dateBounds; both isDaySelectable helpers consult only isSelectableDate, ignoring isSelectableYear and yearRange.

## Recommended solution
Centralize canonicalization and year-range validation for constructor/setters and intersect the effective native selectable range with yearRange. Define programmatic selection versus SelectableDates behavior separately; do not silently add business-rule validation to the Material-compatible setter without an API decision.

## Risks and compatibility
Changing accepted values can affect callers relying on permissive iOS behavior. Native range rejection behavior and exception propagation require Apple execution; the contract/implementation mismatch is source-confirmed, not an observed UIKit crash.

## Required tests / acceptance criteria
- Shared constructor/setter tests for null, intraday UTC, pre-epoch and out-of-range year values.
- iOS inline/wheels/compact/range selection at both year endpoints and outside them.
- Rule changes that would snap outside yearRange; align both actual implementations.
- A rule with isSelectableYear=false but isSelectableDate=true must have an explicit consistent native/Material policy.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/172
- https://github.com/MohamedRejeb/Calf/issues/328
- https://github.com/MohamedRejeb/Calf/issues/541
- https://github.com/MohamedRejeb/Calf/issues/544
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
