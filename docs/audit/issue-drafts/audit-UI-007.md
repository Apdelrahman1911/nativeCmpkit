# [Medium][UI-007] Native range highlighting eagerly allocates every day of a selected range on the UI path

<!-- nativecmpkit-item:audit:UI-007 -->
## Classification
- **Finding:** UI-007
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** L
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateRangeSelection.kt:22-25`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateRangeSelection.kt#L22-L25) — `DateRangeSelection.days`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarRangePickerBackend.kt:74-91`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarRangePickerBackend.kt#L74-L91) — `onTap / render / setSelectedRange`

## Root cause
Rendering expands the entire start/end interval into a List<Long>, filters it, allocates NSDateComponents for every retained day and sends the whole list to UICalendarSelectionMultiDate synchronously.

## Impact and preconditions
Work and allocation are O(number of selected days), not O(visible cells). The default1900-2100 year range can span over73000 dates; custom ranges can be larger. Long-range selection risks main-thread stalls and native memory pressure.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- days() uses generateSequence(...).takeWhile(...).toList().
- render performs a further filter, map and native setSelectedDates during a native tap callback.

## Recommended solution
Measure first, then cap supported span or virtualize/decorate visible range cells with a documented native strategy. At minimum bound work before allocating and avoid repeated full conversion for identical selections.

## Risks and compatibility
No timing, OOM or memory-leak claim was verified. UIKit multi-selection semantics may require a different range renderer, so evaluate after the audit rather than imposing an untested rewrite.

## Required tests / acceptance criteria
- Instrument one-day, one-year and full default-range selection on old and current iPhones.
- Benchmark allocation/time while changing range endpoints and rules.
- Verify disabled gaps and displayed highlights after rule updates.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/544
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
