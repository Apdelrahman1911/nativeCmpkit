# [Medium][UI-004] Empty or reversed date-bound intersections reach native interval APIs without a defined policy

<!-- nativecmpkit-item:audit:UI-004 -->
## Classification
- **Finding:** UI-004
- **Priority:** Medium
- **Evidence status:** `risk` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBounds.kt:17-25,59-63`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/commonMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateBounds.kt#L17-L25) — `DateBounds / intersect`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt:58-61`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt#L58-L61) — `applyDateBounds`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/UIDatePickerBackend.kt:71-73`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/UIDatePickerBackend.kt#L71-L73) — `applyDateBounds`

## Root cause
DateBounds allows min greater than max, and intersecting two individually valid but disjoint bounds produces that state. Native adapters pass both endpoints directly to NSDateInterval or UIDatePicker min/max rather than representing an empty allowed set.

## Impact and preconditions
An empty business rule can become an invalid UIKit interval, unexpected clamping, or a platform exception. Actual UIKit failure mode is unverified; empty intersections are legitimate inputs and must not be confused with a generic malformed caller.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- intersect chooses max(min) and min(max) with no empty-state check.
- CalendarViewHost constructs NSDateInterval(startDate=start,endDate=end) without comparing endpoints.

## Recommended solution
Represent/recognize empty effective bounds explicitly. Disable selection with safe native bounds or expose a documented validation error; handle direct reversed bounds and disjoint and-compositions consistently. Do not prohibit useful empty intersections without an API policy.

## Risks and compatibility
Pure rule evaluation currently correctly rejects every date for a disjoint interval. A fix must preserve that semantics and not accidentally expand an empty range to all dates.

## Required tests / acceptance criteria
- Direct reversed min/max; same UTC day with reversed intraday endpoints; disjoint and rules.
- Native inline/compact/wheels/range application and subsequent nonempty recovery.
- Extreme supported dates and null endpoints.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/541
- https://github.com/MohamedRejeb/Calf/issues/544
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
