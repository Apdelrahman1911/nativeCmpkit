# [Low][UI-011] Native time picker ignores the public is24Hour preference

<!-- nativecmpkit-item:audit:UI-011 -->
## Classification
- **Finding:** UI-011
- **Priority:** Low
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** S
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt:15-20,39-58`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/TimePickerManager.kt#L15-L20) — `TimePickerManager`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt:41-50`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/timepicker/AdaptiveTimePicker.ios.kt#L41-L50) — `AdaptiveTimePicker`

## Root cause
is24Hour is passed to the manager but never used; the UIDatePicker locale is simply the current device locale.

## Impact and preconditions
A caller requesting24-hour or12-hour display gets the device preference instead, unlike Material. Persisted is24Hour state does not control presentation.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- The constructor receives is24Hour:Boolean but its body never references it.

## Recommended solution
Either implement a supported locale/format policy honoring the parameter or clearly document it as Material-only with an explicit native policy. Avoid brittle locale overrides that break localized digits/calendars.

## Risks and compatibility
Whether the API should override the system preference is a product decision; the unused parameter is source-confirmed, no native screenshot comparison was performed.

## Required tests / acceptance criteria
- 12-hour and24-hour system settings with is24Hour true/false and multiple locales.
- Accessibility time readout and SavedState restoration.

## Dependencies
- None identified.

## Historical context
- None identified.
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
