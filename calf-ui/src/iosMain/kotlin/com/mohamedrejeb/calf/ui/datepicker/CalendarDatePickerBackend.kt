// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCSignatureOverride
import platform.Foundation.NSDateComponents
import platform.UIKit.UICalendarSelectionSingleDate
import platform.UIKit.UICalendarSelectionSingleDateDelegateProtocol
import platform.UIKit.UIColor
import platform.UIKit.UIView
import platform.darwin.NSObject

/**
 * Inline calendar backed by `UICalendarView` (iOS 16+). Days rejected by [isDaySelectable]
 * are greyed out and cannot be tapped, matching the Material picker.
 */
internal class CalendarDatePickerBackend(
    initialSelectedDateMillis: Long?,
    initialDisplayedMonthMillis: Long,
    onDisplayedMonthChanged: (Long) -> Unit,
    private val onSelectionChanged: (utcTimeMillis: Long?) -> Unit,
    private val isDaySelectable: (utcTimeMillis: Long) -> Boolean,
) : IosDatePickerBackend {

    private val host = CalendarViewHost()

    private val selectionDelegate = object : NSObject(), UICalendarSelectionSingleDateDelegateProtocol {
        @ObjCSignatureOverride
        override fun dateSelection(
            selection: UICalendarSelectionSingleDate,
            didSelectDate: NSDateComponents?,
        ) {
            onSelectionChanged(didSelectDate?.toUtcDayMillis())
        }

        @ObjCSignatureOverride
        override fun dateSelection(
            selection: UICalendarSelectionSingleDate,
            canSelectDate: NSDateComponents?,
        ): Boolean {
            val day = canSelectDate?.toUtcDayMillis() ?: return true
            return isDaySelectable(day)
        }
    }

    private val selection = UICalendarSelectionSingleDate(delegate = selectionDelegate)

    override val view: UIView
        get() = host.calendarView

    init {
        host.calendarView.selectionBehavior = selection
        initialSelectedDateMillis?.let { millis ->
            selection.setSelectedDate(utcDayToDateComponents(millis), animated = false)
        }
        host.onVisibleMonthChanged = onDisplayedMonthChanged
        host.showMonth(initialDisplayedMonthMillis, animated = false)
        host.calendarView.sizeToFit()
    }

    override fun setSelectedDate(utcTimeMillis: Long?) {
        val current = selection.selectedDate?.toUtcDayMillis()
        if (current == utcTimeMillis) return

        host.preservingVisibleMonth {
            // An animated selection can scroll later, after month restoration.
            // Programmatic owner synchronization must not navigate its month.
            selection.setSelectedDate(utcTimeMillis?.let(::utcDayToDateComponents), animated = false)
        }
    }

    override fun setDisplayedMonth(utcTimeMillis: Long) {
        host.showMonth(utcTimeMillis, animated = false)
    }

    override fun applyDateBounds(minDateMillis: Long?, maxDateMillis: Long?) {
        host.applyDateBounds(minDateMillis, maxDateMillis)
    }

    override fun updateSelectableDates() {
        selection.updateSelectableDates()
        host.refresh()
    }

    override fun setEnabled(enabled: Boolean) {
        host.setEnabled(enabled)
    }

    override fun applyColors(containerColor: UIColor, selectedDayContainerColor: UIColor) {
        host.calendarView.tintColor = selectedDayContainerColor
        host.calendarView.backgroundColor = containerColor
    }
}
