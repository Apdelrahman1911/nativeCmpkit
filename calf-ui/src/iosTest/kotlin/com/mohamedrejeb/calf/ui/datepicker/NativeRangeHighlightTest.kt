@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import platform.Foundation.*
import platform.UIKit.*
import platform.darwin.dispatch_get_main_queue
import platform.darwin.dispatch_sync
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Controlled UIKit inputs and a queued dispatcher; no presentation or scrolling acceptance. */
class NativeRangeHighlightTest {
    @Test
    fun fullRangeUsesOnlyTheCurrentMonthAndItsNeighbours() = onMain {
        Fixture().use { fixture ->
            fixture.showMarch()
            val days = fixture.selectedDays()
            // February, March and April 2026: 28 + 31 + 30 days.
            assertEquals(89, days.size)
            assertEquals(utcDay(20485), days.first()) // 2026-02-01
            assertEquals(utcDay(20573), days.last()) // 2026-04-30
            assertEquals(0, fixture.ownerCalls)
        }
    }

    @Test
    fun replacingRulesAndBoundsRebuildsHighlightsWithUnchangedEndpoints() = onMain {
        Fixture().use { fixture ->
            fixture.showMarch()
            val disabled = utcDay(20526) // 2026-03-14
            fixture.rejectedDay = disabled
            fixture.backend.updateSelectableDates()
            fixture.drain()
            assertTrue(disabled !in fixture.selectedDays())
            fixture.rejectedDay = null
            fixture.backend.updateSelectableDates()
            fixture.drain()
            assertTrue(disabled in fixture.selectedDays())
            fixture.backend.applyDateBounds(utcDay(20525), utcDay(20528))
            fixture.drain()
            assertEquals((20525L..20528L).map(::utcDay), fixture.selectedDays())
            assertEquals(0, fixture.ownerCalls)
        }
    }

    @Test
    fun nativeDeselectionRestoresTheOnlyDayAndNotifiesTheOwnerOnce() = onMain {
        val day = utcDay(20526)
        Fixture(DateRangeSelection(day, day)).use { fixture ->
            fixture.showMarch()
            fixture.multiSelection.setSelectedDates(emptyList<NSDateComponents>(), animated = false)
            fixture.multiSelection.delegate!!.multiDateSelection(
                fixture.multiSelection,
                didDeselectDate = utcDayToDateComponents(day),
            )
            fixture.drain()
            assertEquals(listOf(day), fixture.selectedDays())
            assertEquals(1, fixture.ownerCalls)
        }
    }

    @Test
    fun disposalInvalidatesAQueuedRefreshAndClearsTheNativeDelegates() = onMain {
        Fixture().use { fixture ->
            fixture.showMarch()
            fixture.backend.updateSelectableDates()
            assertEquals(1, fixture.queued.size)
            val before = fixture.totalRuleCalls
            fixture.backend.dispose()
            fixture.drain()
            assertEquals(before, fixture.totalRuleCalls)
            assertEquals(null, fixture.calendar.delegate)
            assertEquals(null, fixture.calendar.selectionBehavior)
            fixture.backend.dispose() // Compose and UIKitView may both release the owner.
            assertEquals(0, fixture.ownerCalls)
        }
    }

    private class Fixture(
        selection: DateRangeSelection = DateRangeSelection(utcDay(0), utcDay(84005)),
    ) : AutoCloseable {
        val queued = mutableListOf<() -> Unit>()
        var rejectedDay: Long? = null
        var totalRuleCalls = 0
        var ownerCalls = 0
        val backend = CalendarRangePickerBackend(
            initialSelection = selection,
            onSelectionChanged = { ownerCalls++ },
            isDaySelectable = {
                totalRuleCalls++
                it != rejectedDay
            },
            enqueueRefresh = { queued.add(it) },
        )
        val calendar = backend.view as UICalendarView
        val multiSelection = calendar.selectionBehavior as UICalendarSelectionMultiDate

        fun showMarch() {
            // Isolate range refresh from the separately reviewed user-calendar conversion issue.
            calendar.calendar = NSCalendar(NSCalendarIdentifierGregorian)
            val previous = calendar.visibleDateComponents
            calendar.setVisibleDateComponents(NSDateComponents().apply {
                year = 2026
                month = 3
                day = 1
            }, animated = false)
            // Deliver the public callback explicitly; this is not a real scrolling test.
            calendar.delegate!!.calendarView(
                calendar,
                didChangeVisibleDateComponentsFrom = previous,
            )
            drain()
        }

        fun selectedDays(): List<Long> = multiSelection.selectedDates
            .map { (it as NSDateComponents).toUtcDayMillis() }
            .sorted()

        fun drain() {
            var iterations = 0
            while (queued.isNotEmpty()) {
                check(++iterations <= 10) { "Native refresh did not settle" }
                queued.removeAt(0).invoke()
            }
        }

        override fun close() {
            backend.dispose()
            drain()
        }
    }

    private fun onMain(block: () -> Unit) {
        if (NSThread.isMainThread) {
            block()
        } else {
            var result: Result<Unit>? = null
            dispatch_sync(dispatch_get_main_queue()) { result = runCatching(block) }
            checkNotNull(result).getOrThrow()
        }
    }
}
