# [Medium][UI-010] Remembered native time picker keeps writing to the original state after replacement

<!-- nativecmpkit-item:audit:UI-010 -->
## Classification
- **Finding:** UI-010
- **Priority:** Medium
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt:36-52,58-93`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt#L36-L52) — `AdaptiveTimePicker`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt:15-36`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt#L15-L36) — `TimePickerManager / onTimeChanged`

## Root cause
UIDatePicker and TimePickerManager are remembered without state identity. The manager callbacks close over the state from first composition, and no effect synchronizes a replacement state into the native picker.

## Impact and preconditions
Hoisting/replacing AdaptiveTimePickerState can leave the visible time stale and native edits updating an obsolete state instead of the current screen model.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- remember { UIDatePicker() } and remember { TimePickerManager(... onHourChanged={state.hourState...}) } have no keys.

## Recommended solution
Recreate the manager/view under key(state), or forward latest-state callbacks and explicitly synchronize all supported state changes. Key theme/direction effects to the newly created manager if using recreation.

## Risks and compatibility
The public hour/minute fields are read-only on iOS, so this finding concerns state replacement, not a nonexistent public setter. Preserve strong target ownership.

## Required tests / acceptance criteria
- Replace stateA with different hour/minute stateB; native edits must only changeB.
- Controller replacement, timezone/locale change, and recompose with identical state.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
