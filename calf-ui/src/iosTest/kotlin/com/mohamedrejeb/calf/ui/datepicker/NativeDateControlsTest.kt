@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import platform.Foundation.*
import platform.UIKit.*
import kotlin.test.*

class NativeDateControlsTest {
    @Test fun gregorianRoundTripsAcrossExtremeOffsetsAndPreEpochDates() = runNativeUiTest {
        for (offset in listOf(-12 * 3600L, 0L, 14 * 3600L)) {
            val calendar = gregorianCalendar(NSTimeZone.timeZoneForSecondsFromGMT(offset))
            assertEquals(NSCalendarIdentifierGregorian, calendar.calendarIdentifier)
            for (day in listOf(-MILLIS_PER_DAY, FEB_29_2000, MAR_15_2026)) {
                val components = utcDayToDateComponents(day).apply { this.calendar = calendar; timeZone = calendar.timeZone }
                val date = requireNotNull(calendar.dateFromComponents(components))
                assertEquals(day, date.toUtcDayMillis(calendar))
            }
        }
    }

    @Test fun uidatePickerEmptyBoundsDisableAndRecoverWithoutOverridingExplicitDisable() = runNativeUiTest {
        val backend = UIDatePickerBackend(MAR_15_2026, UIDatePickerStyle.UIDatePickerStyleWheels, {}, { it })
        val picker = backend.view as UIDatePicker
        assertEquals(NSCalendarIdentifierGregorian, picker.calendar?.calendarIdentifier)
        backend.applyDateBounds(MAR_16_2026, MAR_15_2026)
        backend.setEnabled(true)
        assertFalse(picker.enabled)
        backend.applyDateBounds(MAR_1_2026, MAR_31_2026)
        assertTrue(picker.enabled)
        assertTrue(requireNotNull(picker.minimumDate).timeIntervalSince1970 <= requireNotNull(picker.maximumDate).timeIntervalSince1970)
        backend.setEnabled(false)
        backend.applyDateBounds(null, null)
        assertFalse(picker.enabled)
    }

    @Test fun calendarEmptyBoundsKeepASafeIntervalAndRecover() = runNativeUiTest {
        val host = CalendarViewHost()
        host.applyDateBounds(MAR_1_2026, MAR_31_2026)
        val safeInterval = host.calendarView.availableDateRange
        host.applyDateBounds(MAR_16_2026, MAR_15_2026)
        assertFalse(host.calendarView.userInteractionEnabled)
        assertEquals(safeInterval, host.calendarView.availableDateRange)
        host.applyDateBounds(MAR_1_2026, MAR_31_2026)
        assertTrue(host.calendarView.userInteractionEnabled)
    }

    @Test fun selectedAndDisplayedMonthAreIndependent() = runNativeUiTest {
        val backend = CalendarDatePickerBackend(MAR_15_2026, APR_1_2026, {}, {}, { true })
        val calendar = backend.view as UICalendarView
        assertEquals(4L, calendar.visibleDateComponents.month)
        assertEquals(3L, (calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate?.month)
        backend.setSelectedDate(MAR_16_2026)
        assertEquals(4L, calendar.visibleDateComponents.month)
    }

    @Test fun fullYearRangeHighlightsOnlyVisibleMonthsAndReevaluatesRules() = runNativeUiTest {
        var allowed = true
        val backend = CalendarRangePickerBackend(
            DateRangeSelection(utcYearStartMillis(1900), utcYearStartMillis(2100)),
            MAR_1_2026, {}, {}, { allowed },
        )
        val calendar = backend.view as UICalendarView
        val selection = calendar.selectionBehavior as UICalendarSelectionMultiDate
        assertTrue(selection.selectedDates.size in 1..93)
        allowed = false
        backend.updateSelectableDates()
        assertTrue(selection.selectedDates.isEmpty())
        allowed = true
        backend.setDisplayedMonth(APR_1_2026)
        calendar.layoutIfNeeded()
        backend.updateSelectableDates()
        assertTrue(selection.selectedDates.size in 1..93)
    }
}
