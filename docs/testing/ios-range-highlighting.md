# Bounded iOS range highlighting

Issue #122 / UI-007, source preparation dated 2026-11-08. No compiler, link,
common-test, UIKit-test, simulator, device, allocation or timing result exists
for this patch. The original issue remains open.

## Runtime changes prepared

`CalendarRangePickerBackend` keeps complete selection endpoints and intersects
those endpoints with the visible month and its two neighbours before enumerating
selected days. The projection admits at most 93 canonical UTC days. Filtering
and native component allocation depend on that window rather than the length of
the selected range. `DateRangeSelection.days()` is no longer used by the backend.

The host forwards the public visible-month delegate callback. The backend queues
one main-queue refresh after the native delegate returns, coalescing pending
requests and reading the latest selection, viewport, bounds and rule. Equal day
lists avoid redundant native selection writes. Native selection writes suppress
synthetic owner taps; a genuine tap invalidates that cache, including deselecting
the only highlighted day when the desired highlight stays unchanged. Rule and
bounds updates rebuild highlights even when the endpoints remain identical.

Both Compose disposal and `UIKitView.onRelease` call idempotent cleanup. Cleanup
removes the native selection behavior and calendar delegate and prevents any
already-queued refresh from writing. No polling, display link, gesture target,
notification observer or continuing offscreen task is installed. A queued block
can retain the backend until that main-queue turn, but cannot reactivate it.
State replacement restarts bounds, selection, layout and color synchronization.

The host's adjacent-month list is clamped to AD 1–9999. This change does not import
the independent #27 date/calendar conversion patch. The current user-calendar
conversion limitation is still a separate gate; no non-Gregorian or BC UIKit
correctness is claimed here.

## iOS 16.0–16.1 compatibility

The native range renderer now starts at iOS 16.2. Earlier versions use the
existing Material range picker, retaining the public state, selectable-day
rules, bounds, title/headline, formatter and mode-toggle inputs. This changes
presentation on 16.0 and 16.1; it must be checked on those operating systems.
Single-date picker availability is unchanged.

Apple's official symbol metadata reports iOS/iPadOS 16.2 for
`calendarView(_:didChangeVisibleDateComponentsFrom:)`:

- https://developer.apple.com/documentation/uikit/uicalendarviewdelegate/calendarview(_:didchangevisibledatecomponentsfrom:)
- https://developer.apple.com/tutorials/data/documentation/uikit/uicalendarviewdelegate/calendarview(_:didchangevisibledatecomponentsfrom:).json

The legacy path deliberately uses the existing range component because no
public complete visible-month transition stream was established on 16.0–16.1.
Decoration demand, undocumented KVO, private descendant scroll views and window
attachment are insufficient substitutes for that stream and its lifecycle.

## Prepared tests: sixteen common and six controlled UIKit methods

`DateRangeHighlightsTest` contains sixteen methods. Fifteen cover the projection:
missing/unfinished/completed selections; one-day/year/1900–2100 ranges with equal
viewport work; extreme endpoints; disjoint/reversed ranges; disabled gaps and
rule replacement; moving/revisiting windows; bounds; pre-epoch partial days; the
93-day limit; and malformed windows. Counting/failing predicates check that
clipping happens before enumeration. The sixteenth checks the 16.2 availability
boundary, later major versions and an invalid version string.

`NativeRangeHighlightTest` prepares six controlled UIKit methods: a full range
produces exactly the 89 days of February–April 2026 after a manually delivered
month callback; rules and bounds remove/restore native highlights with unchanged
endpoints; deselecting the only highlighted day restores it and emits one owner
callback; and disposal invalidates a queued refresh and clears native delegates.
The tests inject a queue and explicitly dispatch to main when needed. They inject
a Gregorian calendar before backend initialization to isolate this issue from #27.
They also coalesce endpoint/rule/bounds replacement before one drain and assert
the complete selection values delivered to the owner for selection/deselection.
They do not present a calendar,
produce a real swipe, exercise Compose replacement or establish callback timing
on any real operating system. All twenty-two methods remain unexecuted.

## Native qualification: twelve scenario groups

Use actual iOS 16.0/16.1 for the Material fallback, a 16.2+ native calendar, and
both an older supported physical iPhone and a current physical iPhone. Record
model, OS, Xcode/SDK, build configuration, revision, locale, calendar, time zone
and year range. A mocked version boundary does not prove older-OS compatibility.

| Group | Exercise | Required evidence |
|---|---|---|
| N1 | One-day, one-year and full actual default-range selection | Instruments allocations and CPU/wall time; rule calls, component count, native selection size and retained count. Native projection must remain bounded by the viewport. |
| N2 | Endpoint changes near/far from the viewport | Complete endpoints retained; current window highlighted after programmatic scrolling; peak/transient allocations and refresh timings. |
| N3 | Forward/back scrolling through leap February and year boundaries | Eligible visible days highlighted; disabled days excluded; no growing accumulation. |
| N4 | Fast fling, month/year jump and cached-month revisit | No stale/missing highlights after settling, including jumps beyond both neighbours. |
| N5 | Replace rules: interior gap, all denied, restore | Highlights update without tap/scroll; retain allocation/time measurements. A stable rule object's internal mutation still needs an owner update signal. |
| N6 | Change bounds within/beyond the viewport | Inclusive bounds honoured, complete endpoints retained, moved viewport refreshed. |
| N7 | Tap start/same/earlier/later/interior day | Existing range state machine and one owner callback per genuine selection/deselection tap. |
| N8 | Refresh during native selection/layout callbacks | No recursive native writes, synthetic owner tap or unchanged refresh loop. Retain callback traces. |
| N9 | Dispose/replace state with refresh queued | No old-view write or stale owner callback; delegates and owner released. |
| N10 | Retained hidden/covered host; navigation; background/foreground | No continuing sampling; current highlights on re-entry. Validate Compose and UIKit release ordering. |
| N11 | VoiceOver, heading controls and programmatic navigation | Native callback coverage on 16.2+; complete functional fallback on 16.0/16.1. |
| N12 | Rapid rule/endpoint/bounds updates while scrolling/reusing | Latest inputs win; no lost refresh or retained-owner growth. |

Measure original and candidate under equivalent workloads. Retain warm-up,
sample count, median/tail time, peak/retained allocations and frame interruptions.
The helper's operation bound cannot substitute for measured UIKit performance.

## Remaining acceptance

Compile/link the production and test source sets, execute and retain the exact
16 common / 6 UIKit testcase identities, then complete the native matrix. Local
compiler admission requires 8 GiB available disk and 6 GiB available memory; no
local compiler/test execution was admitted during this source preparation.

All three original criteria remain unproven: instrument one-day/year/full range
on old/current iPhones; benchmark allocation/time during endpoint and rule changes;
and verify disabled gaps and displayed highlights after rule updates. No #122
closure, consumer/API–ABI, native or release acceptance follows from this patch.
