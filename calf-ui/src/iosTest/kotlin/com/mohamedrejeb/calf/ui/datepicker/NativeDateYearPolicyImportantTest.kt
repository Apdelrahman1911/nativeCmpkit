@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.internal.NativeApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.datePickers
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.UIKit.*
import kotlin.test.*

/**
 * PRIVATE, UNCOMPILED proposal. Every native control belongs to the genuine
 * library test app. UIDatePicker value events and retained calendar delegate
 * calls are deliberately controlled; they are not native taps/XCUI/OS gestures.
 * Calendar outside days exercise the actual canSelectDate rejection boundary,
 * never illegal setSelectedDate calls or fabricated native callback outcomes.
 */
class NativeDateYearPolicyImportantTest {
    @Test fun publicInlineCalendarSelectsBothYearEndpointsAndRejectsAdjacentYears() = runApplicationUiTest {
        val state = importantYearState()
        val calendar = mountImportantSingleCalendar(state)
        runOnIdle {
            val selection = calendar.selectionBehavior as UICalendarSelectionSingleDate
            val delegate = requireNotNull(selection.delegate)
            for (day in listOf(IMPORTANT_YEAR_FIRST, IMPORTANT_YEAR_LAST)) {
                val components = utcDayToDateComponents(day)
                assertTrue(delegate.dateSelection(selection, canSelectDate = components))
                calendar.setVisibleDateComponents(components, animated = false)
                selection.setSelectedDate(components, animated = false)
                val actual = requireNotNull(selection.selectedDate)
                assertEquals(day, actual.toUtcDayMillis())
                delegate.dateSelection(selection, didSelectDate = actual)
                assertEquals(day, state.selectedDateMillis)
            }
            for (outside in listOf(IMPORTANT_YEAR_FIRST - MILLIS_PER_DAY, IMPORTANT_YEAR_LAST + MILLIS_PER_DAY)) {
                val priorOwner = state.selectedDateMillis
                val priorNative = selection.selectedDate?.toUtcDayMillis()
                assertFalse(delegate.dateSelection(selection, canSelectDate = utcDayToDateComponents(outside)))
                assertEquals(priorOwner, state.selectedDateMillis)
                assertEquals(priorNative, selection.selectedDate?.toUtcDayMillis())
            }
        }
    }

    @Test fun publicWheelsSelectBothYearEndpointsAndRejectAdjacentYears() = runApplicationUiTest {
        exerciseImportantUidateEndpoints(compact = false)
    }

    @Test fun publicCompactSelectsBothYearEndpointsAndRejectsAdjacentYears() = runApplicationUiTest {
        exerciseImportantUidateEndpoints(compact = true)
    }

    @Test fun publicRangeCalendarSelectsBothYearEndpointsAndRejectsAdjacentYears() = runApplicationUiTest {
        val state = importantRangeState()
        val calendar = mountImportantRangeCalendar(state)
        runOnIdle {
            val selection = calendar.selectionBehavior as UICalendarSelectionMultiDate
            val delegate = requireNotNull(selection.delegate)
            for (day in listOf(IMPORTANT_YEAR_FIRST, IMPORTANT_YEAR_LAST)) {
                val components = utcDayToDateComponents(day)
                assertTrue(delegate.multiDateSelection(selection, canSelectDate = components))
                calendar.setVisibleDateComponents(components, animated = false)
                selection.setSelectedDates(listOf(components), animated = false)
                val actual = selection.selectedDates.filterIsInstance<platform.Foundation.NSDateComponents>().single()
                assertEquals(day, actual.toUtcDayMillis())
                delegate.multiDateSelection(selection, didSelectDate = actual)
            }
            assertEquals(IMPORTANT_YEAR_FIRST, state.selectedStartDateMillis)
            assertEquals(IMPORTANT_YEAR_LAST, state.selectedEndDateMillis)
            for (outside in listOf(IMPORTANT_YEAR_FIRST - MILLIS_PER_DAY, IMPORTANT_YEAR_LAST + MILLIS_PER_DAY)) {
                val prior = state.selectedStartDateMillis to state.selectedEndDateMillis
                assertFalse(delegate.multiDateSelection(selection, canSelectDate = utcDayToDateComponents(outside)))
                assertEquals(prior, state.selectedStartDateMillis to state.selectedEndDateMillis)
            }
            // Keep the accepted bounded-highlight policy, not full-year enumeration.
            assertTrue(selection.selectedDates.size <= 93)
            assertTrue(selection.selectedDates.filterIsInstance<platform.Foundation.NSDateComponents>()
                .all { utcYearOf(it.toUtcDayMillis()) == 2026 })
        }
    }

    @Test fun publicRuleChangesNeverSnapBeyondYearRange() = runApplicationUiTest {
        val state = importantYearState()
        val calendar = mountImportantSingleCalendar(state)
        runOnIdle { assertImportantYearSnapPolicy(state) }
        waitForNative {
            (calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate?.toUtcDayMillis() ==
                state.selectedDateMillis
        }
        runOnIdle {
            assertEquals(2026, utcYearOf(requireNotNull(state.selectedDateMillis)))
            assertTrue(state.isSelectionSelectable)
            assertEquals(IMPORTANT_YEAR_FIRST, calendar.availableDateRange.startDate.toUtcDayMillis())
            assertEquals(IMPORTANT_YEAR_LAST, calendar.availableDateRange.endDate.toUtcDayMillis())
        }
    }

    @Test fun publicNativeYearPredicateRejectsDateTrueUserPicksAndRecovers() {
        for (kind in listOf("inline", "wheels", "compact")) runApplicationUiTest {
            val state = importantYearState(mode = if (kind == "inline") UIKitDisplayMode.Picker else UIKitDisplayMode.Wheels)
            val calendar = if (kind == "inline") mountImportantSingleCalendar(state) else null
            val picker = if (kind != "inline") mountImportantUidatePicker(state, compact = kind == "compact") else null
            runOnIdle { state.selectableDates = RejectEveryYearAllowEveryDate }
            waitForIdle()
            runOnIdle {
                assertFalse(state.selectableDates.isSelectableYear(2026))
                assertTrue(state.selectableDates.isSelectableDate(MAR_16_2026))
                assertEquals(MAR_15_2026, state.selectedDateMillis)
                assertFalse(state.isSelectionSelectable)
                if (calendar != null) {
                    val selection = calendar.selectionBehavior as UICalendarSelectionSingleDate
                    assertFalse(requireNotNull(selection.delegate)
                        .dateSelection(selection, canSelectDate = utcDayToDateComponents(MAR_16_2026)))
                } else {
                    val native = requireNotNull(picker)
                    native.setDate(localStartOfDay(MAR_16_2026), animated = false)
                    assertEquals(MAR_16_2026, native.date.toUtcDayMillis())
                    native.sendActionsForControlEvents(UIControlEventValueChanged)
                    // Important owning regression: current yearRange-only final
                    // resolver predicate instead accepts this rejected raw pick.
                    assertEquals(MAR_15_2026, state.selectedDateMillis)
                }
            }
            if (picker != null) waitForNative { picker.date.toUtcDayMillis() == MAR_15_2026 }
            runOnIdle { state.selectableDates = DatePickerDefaults.AllDates }
            waitForIdle()
            runOnIdle {
                if (calendar != null) {
                    val selection = calendar.selectionBehavior as UICalendarSelectionSingleDate
                    val delegate = requireNotNull(selection.delegate)
                    val components = utcDayToDateComponents(MAR_16_2026)
                    assertTrue(delegate.dateSelection(selection, canSelectDate = components))
                    selection.setSelectedDate(components, animated = false)
                    delegate.dateSelection(selection, didSelectDate = requireNotNull(selection.selectedDate))
                } else {
                    val native = requireNotNull(picker)
                    native.setDate(localStartOfDay(MAR_16_2026), animated = false)
                    native.sendActionsForControlEvents(UIControlEventValueChanged)
                }
                assertEquals(MAR_16_2026, state.selectedDateMillis)
                assertTrue(state.isSelectionSelectable)
            }
        }
        runApplicationUiTest {
            val state = importantRangeState()
            val calendar = mountImportantRangeCalendar(state)
            runOnIdle { state.selectableDates = RejectEveryYearAllowEveryDate }
            waitForIdle()
            runOnIdle {
                val selection = calendar.selectionBehavior as UICalendarSelectionMultiDate
                assertFalse(requireNotNull(selection.delegate)
                    .multiDateSelection(selection, canSelectDate = utcDayToDateComponents(MAR_16_2026)))
                assertEquals(MAR_15_2026, state.selectedStartDateMillis)
                assertEquals(MAR_16_2026, state.selectedEndDateMillis)
                assertTrue(selection.selectedDates.isEmpty())
            }
            runOnIdle { state.selectableDates = DatePickerDefaults.AllDates }
            waitForIdle()
            runOnIdle {
                val selection = calendar.selectionBehavior as UICalendarSelectionMultiDate
                val delegate = requireNotNull(selection.delegate)
                val components = utcDayToDateComponents(IMPORTANT_MAR_17_2026)
                assertTrue(delegate.multiDateSelection(selection, canSelectDate = components))
                selection.setSelectedDates(listOf(components), animated = false)
                delegate.multiDateSelection(selection, didSelectDate = components)
                assertEquals(IMPORTANT_MAR_17_2026, state.selectedStartDateMillis)
                assertNull(state.selectedEndDateMillis)
            }
        }
    }
}

private fun importantRangeState() = AdaptiveDateRangePickerState(
    initialSelectedStartDateMillis = MAR_15_2026,
    initialSelectedEndDateMillis = MAR_16_2026,
    initialDisplayedMonthMillis = MAR_1_2026,
    yearRange = 2026..2026,
    initialMaterialDisplayMode = DisplayMode.Picker,
)

private fun UIView.importantCalendars(): List<UICalendarView> =
    if (this is UICalendarView) listOf(this)
    else subviews.filterIsInstance<UIView>().flatMap { it.importantCalendars() }

private fun NativeApplicationUiTest.mountImportantSingleCalendar(state: AdaptiveDatePickerState): UICalendarView {
    var parent: UIViewController? = null
    setContent { parent = LocalUIViewController.current; AdaptiveDatePicker(state) }
    return awaitImportantCalendar { parent }
}

private fun NativeApplicationUiTest.mountImportantRangeCalendar(state: AdaptiveDateRangePickerState): UICalendarView {
    var parent: UIViewController? = null
    setContent { parent = LocalUIViewController.current; AdaptiveDateRangePicker(state) }
    return awaitImportantCalendar { parent }
}

private fun NativeApplicationUiTest.awaitImportantCalendar(parent: () -> UIViewController?): UICalendarView {
    waitForNative {
        val calendar = parent()?.view?.importantCalendars()?.singleOrNull() ?: return@waitForNative false
        sameNativeObject(calendar.window, requireOwnedApplicationWindow()) &&
            calendar.availableDateRange.startDate.toUtcDayMillis() == IMPORTANT_YEAR_FIRST &&
            calendar.availableDateRange.endDate.toUtcDayMillis() == IMPORTANT_YEAR_LAST
    }
    return runOnIdle { requireNotNull(parent()).view.importantCalendars().single() }
}

private fun NativeApplicationUiTest.mountImportantUidatePicker(
    state: AdaptiveDatePickerState,
    compact: Boolean,
): UIDatePicker {
    var parent: UIViewController? = null
    setContent {
        parent = LocalUIViewController.current
        if (compact) AdaptiveCompactDatePicker(state) else AdaptiveDatePicker(state)
    }
    waitForNative {
        val picker = parent?.view?.datePickers()?.singleOrNull() ?: return@waitForNative false
        sameNativeObject(picker.window, requireOwnedApplicationWindow()) &&
            picker.minimumDate?.toUtcDayMillis() == IMPORTANT_YEAR_FIRST &&
            picker.maximumDate?.toUtcDayMillis() == IMPORTANT_YEAR_LAST
    }
    return runOnIdle {
        requireNotNull(parent).view.datePickers().single().also {
            assertEquals(if (compact) UIDatePickerStyle.UIDatePickerStyleCompact else UIDatePickerStyle.UIDatePickerStyleWheels,
                it.preferredDatePickerStyle)
        }
    }
}

private fun NativeApplicationUiTest.exerciseImportantUidateEndpoints(compact: Boolean) {
    val state = importantYearState(mode = UIKitDisplayMode.Wheels)
    val picker = mountImportantUidatePicker(state, compact)
    for ((endpoint, outside) in listOf(
        IMPORTANT_YEAR_FIRST to IMPORTANT_YEAR_FIRST - MILLIS_PER_DAY,
        IMPORTANT_YEAR_LAST to IMPORTANT_YEAR_LAST + MILLIS_PER_DAY,
    )) {
        runOnIdle {
            picker.setDate(localStartOfDay(endpoint), animated = false)
            assertEquals(endpoint, picker.date.toUtcDayMillis())
            picker.sendActionsForControlEvents(UIControlEventValueChanged)
            assertEquals(endpoint, state.selectedDateMillis)
            picker.setDate(localStartOfDay(outside), animated = false)
            val rawNativeDay = picker.date.toUtcDayMillis()
            // Actual UIKit may clamp or retain this endpoint before delivery.
            // Neither branch is guessed to have occurred from a green result.
            assertTrue(rawNativeDay == outside || rawNativeDay == endpoint)
            picker.sendActionsForControlEvents(UIControlEventValueChanged)
            assertEquals(endpoint, state.selectedDateMillis)
        }
        waitForNative { picker.date.toUtcDayMillis() == endpoint }
    }
}
