# [High][UI-002] Native date conversion treats user-calendar components as Gregorian dates

<!-- nativecmpkit-item:audit:UI-002 -->
## Classification
- **Finding:** UI-002
- **Priority:** High
- **Evidence status:** `confirmed-source` (source/test evidence is not automatically a demonstrated exploit)
- **Affected modules:** `calf-ui`
- **Estimated complexity:** M
- **Reviewed upstream baseline:** `af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6`; original commit preserved in this repository.

## Exact code / symbols
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateConversions.kt:53-75`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/DateConversions.kt#L53-L75) — `NSDate.toUtcDayMillis / NSDateComponents.toUtcDayMillis / utcDayToDateComponents`
- [`calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt:35-38,88-106`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6/calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/CalendarViewHost.kt#L35-L38) — `calendarView / daysAroundVisibleMonth`

## Root cause
UICalendarView and NSDate extraction use NSCalendar.currentCalendar, whereas component year/month/day values are read into or generated from Gregorian kotlinx.datetime.LocalDate without calendar/era conversion.

## Impact and preconditions
Non-Gregorian device calendars can select the wrong year/day or receive nonsensical visible-month data. Buddhist year offsets, Japanese era numbering and leap-month calendars are not interchangeable with Gregorian components; month13 cannot be represented by LocalDate.

## Supporting evidence
- All cited source locations refer to immutable upstream baseline af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6.
- currentCalendar.components(year|month|day) feeds LocalDate(year,month,day) directly.
- calendarView.calendar is explicitly currentCalendar, but outgoing NSDateComponents have Gregorian numbers and no calendar/era.

## Recommended solution
Choose and document the calendar contract. Either configure all UIKit/calendar extraction as Gregorian with the device locale/timezone, or convert through absolute NSDate instants using the originating calendar and era. Use the same policy for visible-month refresh, bounds, callbacks and range highlights.

## Risks and compatibility
This is a source-confirmed incompatible conversion; examples describe mathematical/calendar consequences, not executed iOS outcomes. Retain local-day/DST semantics while fixing calendar identity.

## Required tests / acceptance criteria
- iPhone/iPad Gregorian, Buddhist, Japanese and Hebrew device calendars.
- Roundtrip selection, displayed month, min/max and range across era/leap-month boundaries.
- Time zones UTC, UTC-12, UTC+14 and DST-transition days.

## Dependencies
- None identified.

## Historical context
- https://github.com/MohamedRejeb/Calf/issues/172
- https://github.com/MohamedRejeb/Calf/issues/541
- https://github.com/MohamedRejeb/Calf/issues/544
Original upstream records (authors, IDs, timestamps, comments, reviews and public revisions) are archived in [`docs/migration/upstream-metadata/`](https://github.com/Apdelrahman1911/nativeCmpkit/tree/main/docs/migration/upstream-metadata). Links above are attribution; this issue is newly created for the independent project, not an impersonated original.

## Persistent technical record
[`docs/audit/findings/UI.json`](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/findings/UI.json) · [Audit](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/audit/README.md) · [Roadmap](https://github.com/Apdelrahman1911/nativeCmpkit/blob/main/docs/roadmap/README.md)
