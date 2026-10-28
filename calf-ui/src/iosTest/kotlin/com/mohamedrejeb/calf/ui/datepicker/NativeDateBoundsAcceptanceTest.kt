@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.ui.internal.datePickers
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.UIKit.*
import kotlin.test.*

/** Real attached UIKit intervals and public Compose synchronization, not picker stand-ins. */
class NativeDateBoundsAcceptanceTest {
    @Test fun everyUidatePickerStyleHandlesEmptyIntradayExtremeAndNullBounds() = runApplicationUiTest {
        setContent {}
        runOnIdle {
            val root = requireNotNull(requireOwnedApplicationWindow().rootViewController).view
            for (style in listOf(UIDatePickerStyle.UIDatePickerStyleInline,
                UIDatePickerStyle.UIDatePickerStyleCompact, UIDatePickerStyle.UIDatePickerStyleWheels)) {
                val backend = UIDatePickerBackend(MAR_15_2026, style, {}, { it })
                val picker = backend.view as UIDatePicker
                attached(root, picker) {
                    assertEquals(style, picker.preferredDatePickerStyle)
                    backend.applyDateBounds(MAR_16_2026, MAR_15_2026)
                    assertFalse(picker.enabled, "Reversed days disable $style")
                    assertNull(picker.minimumDate)
                    assertNull(picker.maximumDate)
                    backend.setEnabled(true)
                    assertFalse(picker.enabled)

                    // Reversed timestamps in the SAME UTC day are not an empty day set.
                    backend.applyDateBounds(MAR_15_2026 + NOON_OFFSET_MILLIS, MAR_15_2026 + 1)
                    assertTrue(picker.enabled)
                    assertEquals(MAR_15_2026, requireNotNull(picker.minimumDate).toUtcDayMillis())
                    assertEquals(MAR_15_2026, requireNotNull(picker.maximumDate).toUtcDayMillis())
                    assertTrue(requireNotNull(picker.minimumDate).timeIntervalSince1970 <=
                        requireNotNull(picker.maximumDate).timeIntervalSince1970)

                    val first = utcYearStartMillis(1900)
                    val last = utcYearStartMillis(2101) - MILLIS_PER_DAY
                    backend.applyDateBounds(first, last)
                    assertTrue(picker.enabled)
                    assertEquals(first, requireNotNull(picker.minimumDate).toUtcDayMillis())
                    assertEquals(last, requireNotNull(picker.maximumDate).toUtcDayMillis())
                    backend.applyDateBounds(first, null)
                    assertNull(picker.maximumDate)
                    backend.applyDateBounds(null, last)
                    assertNull(picker.minimumDate)
                    backend.applyDateBounds(null, null)
                    assertNull(picker.minimumDate)
                    assertNull(picker.maximumDate)
                    assertTrue(picker.enabled)

                    backend.setEnabled(false)
                    backend.applyDateBounds(MAR_16_2026, MAR_15_2026)
                    backend.applyDateBounds(first, last)
                    assertFalse(picker.enabled, "Bounds recovery must retain explicit disabled state")
                }
            }
        }
    }

    @Test fun singleAndRangeCalendarsPreserveSafeIntervalsAndRecoverAtYearEndpoints() = runApplicationUiTest {
        setContent {}
        runOnIdle {
            val root = requireNotNull(requireOwnedApplicationWindow().rootViewController).view
            val single = CalendarDatePickerBackend(MAR_15_2026, MAR_1_2026, {}, {}, { true })
            var rangeBounds = DateBounds()
            val range = CalendarRangePickerBackend(DateRangeSelection(MAR_15_2026, MAR_16_2026),
                MAR_1_2026, {}, {}, { rangeBounds.isSelectableDate(it) })
            val applyRange: (Long?, Long?) -> Unit = { min, max ->
                rangeBounds = DateBounds(min, max)
                range.applyDateBounds(min, max)
            }
            for ((view, apply) in listOf(single.view to single::applyDateBounds,
                range.view to applyRange)) {
                val calendar = view as UICalendarView
                attached(root, calendar) {
                    apply(MAR_1_2026, MAR_31_2026)
                    val safe = calendar.availableDateRange
                    apply(MAR_16_2026, MAR_15_2026)
                    assertFalse(calendar.userInteractionEnabled)
                    assertEquals(safe, calendar.availableDateRange, "Never install a reversed native interval")
                    apply(MAR_15_2026 + NOON_OFFSET_MILLIS, MAR_15_2026 + 1)
                    assertTrue(calendar.userInteractionEnabled)
                    assertEquals(MAR_15_2026, calendar.availableDateRange.startDate.toUtcDayMillis())
                    assertEquals(MAR_15_2026, calendar.availableDateRange.endDate.toUtcDayMillis())

                    val first = utcYearStartMillis(1900)
                    val last = utcYearStartMillis(2101) - MILLIS_PER_DAY
                    apply(first, last)
                    assertEquals(first, calendar.availableDateRange.startDate.toUtcDayMillis())
                    assertEquals(last, calendar.availableDateRange.endDate.toUtcDayMillis())
                    for ((min, max) in listOf(first to null, null to last, null to null)) {
                        apply(min, max)
                        assertTrue(calendar.userInteractionEnabled)
                        assertTrue(calendar.availableDateRange.duration > 0.0)
                    }
                }
            }
            val calendar = single.view as UICalendarView
            single.setEnabled(false)
            single.applyDateBounds(MAR_16_2026, MAR_15_2026)
            single.applyDateBounds(MAR_1_2026, MAR_31_2026)
            assertFalse(calendar.userInteractionEnabled)
            single.setEnabled(true)
            assertTrue(calendar.userInteractionEnabled)
        }
    }

    @Test fun publicDateAndRangeControlsApplyChangingDisjointAndSameDayRules() {
        val empty = DateBounds(maxDateMillis = MAR_31_2026) and DateBounds(minDateMillis = APR_1_2026)
        val sameDay = DateBounds(MAR_15_2026 + NOON_OFFSET_MILLIS, MAR_15_2026 + 1)
        assertTrue(requireNotNull(empty.dateBoundsOrNull()).isEmpty)
        assertFalse(sameDay.isEmpty)
        assertTrue(sameDay.isSelectableDate(MAR_15_2026))
        for (kind in listOf("inline", "wheels", "range")) runApplicationUiTest {
            val state = AdaptiveDatePickerState(initialSelectedDateMillis = MAR_15_2026,
                initialDisplayedMonthMillis = MAR_1_2026, yearRange = 2026..2026,
                initialUIKitDisplayMode = if (kind == "wheels") UIKitDisplayMode.Input else UIKitDisplayMode.Picker,
                selectableDates = empty)
            val range = AdaptiveDateRangePickerState(initialSelectedStartDateMillis = MAR_15_2026,
                initialSelectedEndDateMillis = MAR_16_2026, initialDisplayedMonthMillis = MAR_1_2026,
                yearRange = 2026..2026, initialMaterialDisplayMode = androidx.compose.material3.DisplayMode.Picker,
                selectableDates = empty)
            lateinit var parent: UIViewController
            setContent {
                parent = LocalUIViewController.current
                if (kind == "range") AdaptiveDateRangePicker(range) else AdaptiveDatePicker(state)
            }
            waitForNative {
                val view = if (kind == "wheels") parent.view.datePickers().singleOrNull()
                    else parent.view.calendars().singleOrNull()
                view != null && sameNativeObject(view.window, parent.view.window) &&
                    if (view is UIDatePicker) !view.enabled else !view.userInteractionEnabled
            }
            runOnIdle {
                if (kind == "range") range.selectableDates = sameDay else state.selectableDates = sameDay
            }
            waitForNative {
                if (kind == "wheels") {
                    val picker = parent.view.datePickers().single()
                    picker.enabled && picker.minimumDate?.toUtcDayMillis() == MAR_15_2026 &&
                        picker.maximumDate?.toUtcDayMillis() == MAR_15_2026
                } else {
                    val calendar = parent.view.calendars().single()
                    calendar.userInteractionEnabled && calendar.availableDateRange.startDate.toUtcDayMillis() == MAR_15_2026 &&
                        calendar.availableDateRange.endDate.toUtcDayMillis() == MAR_15_2026
                }
            }
            runOnIdle {
                if (kind == "range") range.selectableDates = empty else state.selectableDates = empty
            }
            waitForNative {
                if (kind == "wheels") !parent.view.datePickers().single().enabled
                else !parent.view.calendars().single().userInteractionEnabled
            }
            runOnIdle {
                if (kind == "range") range.selectableDates = DateBounds() else state.selectableDates = DateBounds()
            }
            waitForNative {
                if (kind == "wheels") parent.view.datePickers().single().enabled
                else parent.view.calendars().single().userInteractionEnabled
            }
        }
    }
}

private fun attached(root: UIView, view: UIView, checks: () -> Unit) {
    assertTrue(NSThread.isMainThread)
    view.frame = CGRectMake(0.0, 0.0, 320.0, 320.0)
    root.addSubview(view)
    try {
        view.layoutIfNeeded()
        assertNotNull(root.window)
        assertTrue(sameNativeObject(view.window, root.window))
        checks()
    } finally {
        view.removeFromSuperview()
        assertNull(view.window)
    }
}

private fun UIView.calendars(): List<UICalendarView> =
    if (this is UICalendarView) listOf(this) else subviews.filterIsInstance<UIView>().flatMap { it.calendars() }
