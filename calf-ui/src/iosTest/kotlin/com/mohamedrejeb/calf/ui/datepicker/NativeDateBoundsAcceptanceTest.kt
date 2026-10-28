@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class,
    androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DisplayMode
import androidx.compose.ui.uikit.LocalUIViewController
import androidx.compose.runtime.saveable.SaverScope
import com.mohamedrejeb.calf.ui.internal.datePickers
import com.mohamedrejeb.calf.ui.internal.requireOwnedApplicationWindow
import com.mohamedrejeb.calf.ui.internal.runApplicationUiTest
import com.mohamedrejeb.calf.ui.internal.sameNativeObject
import com.mohamedrejeb.calf.ui.internal.waitForNative
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSThread
import platform.Foundation.timeIntervalSince1970
import platform.UIKit.*
import kotlin.test.*

/** Real attached UIKit intervals, month intent and public Compose restoration, not stand-ins. */
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
                initialMaterialDisplayMode = DisplayMode.Picker,
                initialUIKitDisplayMode = if (kind == "wheels") UIKitDisplayMode.Wheels else UIKitDisplayMode.Picker,
                selectableDates = empty)
            val range = AdaptiveDateRangePickerState(initialSelectedStartDateMillis = MAR_15_2026,
                initialSelectedEndDateMillis = MAR_16_2026, initialDisplayedMonthMillis = MAR_1_2026,
                yearRange = 2026..2026, initialMaterialDisplayMode = DisplayMode.Picker,
                selectableDates = empty)
            lateinit var parent: UIViewController
            setContent {
                parent = LocalUIViewController.current
                if (kind == "range") AdaptiveDateRangePicker(range) else AdaptiveDatePicker(state)
            }
            // setContent is asynchronous; a committed real root initializes parent.
            waitForIdle()
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

    @Test fun publicInlineCalendarKeepsSelectionIndependentFromActualMonthNavigation() = runApplicationUiTest {
        val state = dateIntentState()
        lateinit var parent: UIViewController
        setContent {
            parent = LocalUIViewController.current
            AdaptiveDatePicker(state)
        }
        waitForIdle()
        waitForNative { parent.view.calendars().singleOrNull()?.window != null }
        runOnIdle {
            val calendar = parent.view.calendars().single()
            assertEquals(4L, calendar.visibleDateComponents.month)
            assertEquals(3L, (calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate?.month)
            calendar.setVisibleDateComponents(utcDayToDateComponents(APR_1_2026).apply { month = 5 }, animated = false)
            // Programmatic navigation need not invalidate layout or notify UIKit's
            // delegate. Exercise the real layout-observation path deliberately.
            calendar.setNeedsLayout()
            calendar.layoutIfNeeded()
            assertEquals(5L, calendar.visibleDateComponents.month, "Actual native month navigation must succeed")
        }
        val may = utcMonthStartMillis(APR_1_2026 + 32 * MILLIS_PER_DAY)
        awaitMain("public inline state observes the actual May calendar layout") { state.displayedMonthMillis == may }
        runOnIdle { state.selectedDateMillis = MAR_16_2026 }
        waitForIdle()
        runOnIdle {
            val calendar = parent.view.calendars().single()
            assertEquals(5L, calendar.visibleDateComponents.month)
            assertEquals(MAR_16_2026, (calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate?.toUtcDayMillis())
            assertEquals(may, state.displayedMonthMillis)
            state.selectedDateMillis = null
        }
        waitForIdle()
        runOnIdle {
            val calendar = parent.view.calendars().single()
            assertNull((calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate)
            assertEquals(5L, calendar.visibleDateComponents.month)
            assertEquals(may, state.displayedMonthMillis)
        }
    }

    @Test fun nativeMonthNavigationSurvivesRealRootDisposalAndSaverRestoration() {
        val saver = AdaptiveDatePickerState.Saver()
        var saved: Any? = null
        val may = utcMonthStartMillis(APR_1_2026 + 32 * MILLIS_PER_DAY)
        runApplicationUiTest {
            val state = dateIntentState()
            lateinit var parent: UIViewController
            setContent {
                parent = LocalUIViewController.current
                AdaptiveDatePicker(state)
            }
            waitForIdle()
            waitForNative { parent.view.calendars().singleOrNull()?.window != null }
            runOnIdle {
                val calendar = parent.view.calendars().single()
                calendar.setVisibleDateComponents(utcDayToDateComponents(may), animated = false)
                calendar.setNeedsLayout()
                calendar.layoutIfNeeded()
                assertEquals(5L, calendar.visibleDateComponents.month)
            }
            awaitMain("native May layout is recorded before saving the disposed root") { state.displayedMonthMillis == may }
            runOnIdle { saved = requireNotNull(with(saver) { SaverScope { true }.save(state) }) }
        } // The real Compose root/native view is disposed and the owned UIWindow restored.
        val restored = requireNotNull(saver.restore(requireNotNull(saved)))
        assertEquals(MAR_15_2026, restored.selectedDateMillis)
        assertEquals(may, restored.displayedMonthMillis)
        @Suppress("UNCHECKED_CAST")
        val legacy = requireNotNull(saver.restore((requireNotNull(saved) as List<Any?>).take(5)))
        assertEquals(MAR_15_2026, legacy.selectedDateMillis)
        assertEquals(MAR_1_2026, legacy.displayedMonthMillis)
        runApplicationUiTest {
            lateinit var parent: UIViewController
            setContent {
                parent = LocalUIViewController.current
                AdaptiveDatePicker(restored)
            }
            waitForIdle()
            waitForNative { parent.view.calendars().singleOrNull()?.window != null }
            runOnIdle {
                val calendar = parent.view.calendars().single()
                assertEquals(5L, calendar.visibleDateComponents.month)
                assertEquals(MAR_15_2026,
                    (calendar.selectionBehavior as UICalendarSelectionSingleDate).selectedDate?.toUtcDayMillis())
                assertEquals(may, restored.displayedMonthMillis)
            }
        }
    }

    @Test fun publicWheelsAndCompactKeepIndependentMonthIntentDuringNativeEditsAndClear() {
        for (compact in listOf(false, true)) runApplicationUiTest {
            val state = dateIntentState(UIKitDisplayMode.Wheels)
            lateinit var parent: UIViewController
            setContent {
                parent = LocalUIViewController.current
                if (compact) AdaptiveCompactDatePicker(state) else AdaptiveDatePicker(state)
            }
            waitForIdle()
            waitForNative { parent.view.datePickers().singleOrNull()?.window != null }
            runOnIdle {
                val picker = parent.view.datePickers().single()
                assertEquals(if (compact) UIDatePickerStyle.UIDatePickerStyleCompact else UIDatePickerStyle.UIDatePickerStyleWheels,
                    picker.preferredDatePickerStyle)
                // UIDatePicker has one shown date, not an independently navigable calendar month.
                assertEquals(MAR_15_2026, picker.date.toUtcDayMillis())
                assertEquals(APR_1_2026, state.displayedMonthMillis)
                picker.setDate(localStartOfDay(MAR_16_2026), animated = false)
                picker.sendActionsForControlEvents(UIControlEventValueChanged)
                assertEquals(MAR_16_2026, state.selectedDateMillis)
                assertEquals(APR_1_2026, state.displayedMonthMillis)
                state.selectedDateMillis = null
            }
            waitForIdle()
            runOnIdle {
                assertNull(state.selectedDateMillis)
                assertEquals(APR_1_2026, state.displayedMonthMillis)
                assertEquals(MAR_16_2026, parent.view.datePickers().single().date.toUtcDayMillis(),
                    "A native shown date does not silently create a non-null owner selection")
            }
        }
    }
}

private fun dateIntentState(mode: UIKitDisplayMode = UIKitDisplayMode.Picker) = AdaptiveDatePickerState(
    initialSelectedDateMillis = MAR_15_2026, initialDisplayedMonthMillis = APR_1_2026,
    yearRange = 2020..2030, initialMaterialDisplayMode = DisplayMode.Picker, initialUIKitDisplayMode = mode,
)

private fun attached(root: UIView, view: UIView, checks: () -> Unit) {
    assertTrue(NSThread.isMainThread)
    view.setFrame(CGRectMake(0.0, 0.0, 320.0, 320.0))
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
