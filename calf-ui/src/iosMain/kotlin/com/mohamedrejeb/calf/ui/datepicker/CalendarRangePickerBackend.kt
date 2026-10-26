// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.graphics.Color
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCSignatureOverride
import platform.Foundation.NSDateComponents
import platform.UIKit.UICalendarSelectionMultiDate
import platform.UIKit.UICalendarSelectionMultiDateDelegateProtocol
import platform.UIKit.UIView
import platform.darwin.NSObject

/**
 * Range calendar backed by `UICalendarView` (iOS 16+) with multi-date selection. Taps are
 * folded into a [DateRangeSelection], and every day of the range is highlighted. Days rejected
 * by [isDaySelectable] are greyed out.
 */
internal class CalendarRangePickerBackend(
    initialSelection: DateRangeSelection,
    initialDisplayedMonthMillis: Long,
    onDisplayedMonthChanged: (Long) -> Unit,
    private val onSelectionChanged: (selection: DateRangeSelection) -> Unit,
    private val isDaySelectable: (utcTimeMillis: Long) -> Boolean,
) {
    private val host = CalendarViewHost()

    private var selection = initialSelection

    private val selectionDelegate = object : NSObject(), UICalendarSelectionMultiDateDelegateProtocol {
        @ObjCSignatureOverride
        override fun multiDateSelection(
            selection: UICalendarSelectionMultiDate,
            didSelectDate: NSDateComponents,
        ) {
            onTap(didSelectDate.toUtcDayMillis())
        }

        @ObjCSignatureOverride
        override fun multiDateSelection(
            selection: UICalendarSelectionMultiDate,
            didDeselectDate: NSDateComponents,
        ) {
            onTap(didDeselectDate.toUtcDayMillis())
        }

        @ObjCSignatureOverride
        override fun multiDateSelection(
            selection: UICalendarSelectionMultiDate,
            canSelectDate: NSDateComponents,
        ): Boolean = isDaySelectable(canSelectDate.toUtcDayMillis())

        @ObjCSignatureOverride
        override fun multiDateSelection(
            selection: UICalendarSelectionMultiDate,
            canDeselectDate: NSDateComponents,
        ): Boolean = true
    }

    private val multiSelection = UICalendarSelectionMultiDate(delegate = selectionDelegate)

    val view: UIView
        get() = host.calendarView

    /** Width divided by height of the calendar, or 0 when it has no intrinsic size yet. */
    val aspectRatio: Float

    init {
        host.calendarView.selectionBehavior = multiSelection
        host.onVisibleMonthChanged = {
            render(animated = false)
            onDisplayedMonthChanged(it)
        }
        host.showMonth(initialDisplayedMonthMillis, animated = false)
        render(animated = false)
        host.calendarView.sizeToFit()
        aspectRatio = host.calendarView.aspectRatioOrZero()
    }

    private fun onTap(utcTimeMillis: Long) {
        selection = selection.afterTap(utcTimeMillis)
        render(animated = true)
        onSelectionChanged(selection)
    }

    private fun render(animated: Boolean) {
        // At most three months (~92 days), independent of the selected range's length.
        val highlightedDays = host.daysAroundVisibleMonth().filter {
            val day = it.toUtcDayMillis()
            selection.contains(day) && isDaySelectable(day)
        }
        multiSelection.setSelectedDates(highlightedDays, animated = animated)
    }

    fun setSelectedRange(newSelection: DateRangeSelection) {
        if (newSelection == selection) return
        selection = newSelection
        render(animated = true)
    }

    fun setDisplayedMonth(utcTimeMillis: Long) = host.showMonth(utcTimeMillis, animated = false)

    fun applyDateBounds(minDateMillis: Long?, maxDateMillis: Long?) {
        host.applyDateBounds(minDateMillis, maxDateMillis)
        updateSelectableDates()
    }

    fun updateSelectableDates() {
        multiSelection.updateSelectableDates()
        render(animated = false)
        host.refresh()
    }

    fun applyColors(containerColor: Color, dayContentColor: Color, selectedDayContainerColor: Color) {
        host.applyColors(containerColor, dayContentColor, selectedDayContainerColor)
    }
}
