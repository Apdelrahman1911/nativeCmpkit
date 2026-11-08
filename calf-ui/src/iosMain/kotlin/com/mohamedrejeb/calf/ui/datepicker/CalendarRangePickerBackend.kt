@file:OptIn(ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.graphics.Color
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCSignatureOverride
import platform.Foundation.NSDateComponents
import platform.UIKit.UICalendarSelectionMultiDate
import platform.UIKit.UICalendarSelectionMultiDateDelegateProtocol
import platform.UIKit.UICalendarView
import platform.UIKit.UIView
import platform.darwin.NSObject
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue

/**
 * Range calendar backed by `UICalendarView` (iOS 16+) with multi-date selection. Taps are
 * folded into a [DateRangeSelection]. Only the visible month and its neighbours are submitted
 * to UIKit, while the public selection retains its complete endpoints. Requires iOS 16.2+
 * for the public visible-month delegate callback. Days rejected by [isDaySelectable] are greyed out.
 */
internal class CalendarRangePickerBackend(
    initialSelection: DateRangeSelection,
    private val onSelectionChanged: (selection: DateRangeSelection) -> Unit,
    private val isDaySelectable: (utcTimeMillis: Long) -> Boolean,
    private val enqueueRefresh: (() -> Unit) -> Unit = { work ->
        dispatch_async(dispatch_get_main_queue()) { work() }
    },
    configureCalendar: (UICalendarView) -> Unit = {},
) {
    private var disposed = false
    private var rendering = false
    private var refreshQueued = false
    private var renderedDays: List<Long>? = null
    private var selection = initialSelection
    private val host = CalendarViewHost(onVisibleMonthChanged = ::requestRender).also {
        // Apply controlled calendar configuration before initial navigation or selection writes.
        configureCalendar(it.calendarView)
    }

    private var minDateMillis: Long? = null
    private var maxDateMillis: Long? = null

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
        selection.start?.let { host.showMonth(it, animated = false) }
        render(animated = false)
        host.calendarView.sizeToFit()
        aspectRatio = host.calendarView.aspectRatioOrZero()
    }

    private fun onTap(utcTimeMillis: Long) {
        // UIKit selection writes must never turn into a second owner tap.
        if (disposed || rendering) return
        selection = selection.afterTap(utcTimeMillis)
        // A native deselection may leave the desired days unchanged (for example,
        // tapping the only highlighted day), so force its selection to be restored.
        renderedDays = null
        requestRender()
        onSelectionChanged(selection)
    }

    private fun requestRender() {
        if (disposed || refreshQueued) return
        refreshQueued = true
        // Leave the native delegate stack before changing its selection. The one queued
        // closure reads current inputs, so scrolling/rule changes coalesce without a timer.
        enqueueRefresh {
            refreshQueued = false
            if (!disposed) render(animated = false)
        }
    }

    private fun render(animated: Boolean) {
        if (disposed) return
        val window = host.daysAroundVisibleMonth()
        val highlightedDays = if (window.isEmpty()) emptyList() else {
            selection.highlightedDaysIn(
                windowStartMillis = window.first().toUtcDayMillis(),
                windowEndMillis = window.last().toUtcDayMillis(),
            ) { day ->
                isDayWithinBounds(day, minDateMillis, maxDateMillis) && isDaySelectable(day)
            }
        }
        if (highlightedDays == renderedDays) return
        rendering = true
        try {
            multiSelection.setSelectedDates(highlightedDays.map(::utcDayToDateComponents), animated)
            renderedDays = highlightedDays
        } finally {
            rendering = false
        }
    }

    fun setSelectedRange(newSelection: DateRangeSelection) {
        if (disposed || newSelection == selection) return
        selection = newSelection
        newSelection.start?.let { host.showMonth(it, animated = true) }
        requestRender()
    }

    fun applyDateBounds(minDateMillis: Long?, maxDateMillis: Long?) {
        if (disposed) return
        this.minDateMillis = minDateMillis
        this.maxDateMillis = maxDateMillis
        host.applyDateBounds(minDateMillis, maxDateMillis)
        updateSelectableDates()
    }

    fun updateSelectableDates() {
        if (disposed) return
        multiSelection.updateSelectableDates()
        host.refresh()
        requestRender()
    }

    fun dispose() {
        if (disposed) return
        disposed = true
        renderedDays = null
        host.calendarView.selectionBehavior = null
        host.dispose()
    }

    fun applyColors(containerColor: Color, dayContentColor: Color, selectedDayContainerColor: Color) {
        host.applyColors(containerColor, dayContentColor, selectedDayContainerColor)
    }
}
