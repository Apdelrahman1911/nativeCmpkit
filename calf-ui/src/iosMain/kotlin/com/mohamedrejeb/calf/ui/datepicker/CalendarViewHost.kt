// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.ui.graphics.Color
import com.mohamedrejeb.calf.ui.utils.applyTheme
import com.mohamedrejeb.calf.ui.utils.isDark
import com.mohamedrejeb.calf.ui.utils.toUIColor
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCSignatureOverride
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.minus
import kotlinx.datetime.number
import kotlinx.datetime.plus
import platform.CoreGraphics.CGRectMake
import platform.Foundation.NSDate
import platform.Foundation.NSDateComponents
import platform.Foundation.NSDateInterval
import platform.Foundation.NSTimeZone
import platform.Foundation.distantFuture
import platform.Foundation.distantPast
import platform.Foundation.localTimeZone
import platform.UIKit.UICalendarView
import platform.UIKit.UICalendarViewDecoration
import platform.UIKit.UICalendarViewDelegateProtocol
import platform.darwin.NSObject

private const val MAX_SUPPORTED_YEAR = 9999L
private const val MAX_MONTH = 12L

/** A Gregorian `UICalendarView` (iOS 16+) using the device locale and time zone. */
internal class CalendarViewHost {

    var onVisibleMonthChanged: (Long) -> Unit = {}
    private var lastVisibleMonth: Long? = null
    private var requestedEnabled = true
    private var emptyBounds = false
    private var suppressVisibleMonthReporting = false

    // The delegate notification was added in iOS 16.2. Layout observation covers 16.0/16.1
    // without a permanent frame loop, and also updates range highlights while scrolling.
    val calendarView: UICalendarView = object : UICalendarView(frame = CGRectMake(0.0, 0.0, 0.0, 0.0)) {
        override fun layoutSubviews() {
            super.layoutSubviews()
            reportVisibleMonth()
        }
    }.apply {
        calendar = gregorianCalendar()
        locale = getCalendarLocalDefault()
        timeZone = NSTimeZone.localTimeZone
    }

    /** Draws no decorations, but lets [refresh] ask the calendar to rebuild its day cells. */
    private val decorationDelegate = object : NSObject(), UICalendarViewDelegateProtocol {
        @ObjCSignatureOverride
        override fun calendarView(
            calendarView: UICalendarView,
            decorationForDateComponents: NSDateComponents,
        ): UICalendarViewDecoration? = null

        @ObjCSignatureOverride
        override fun calendarView(
            calendarView: UICalendarView,
            didChangeVisibleDateComponentsFrom: NSDateComponents,
        ) {
            reportVisibleMonth()
        }
    }

    init {
        calendarView.delegate = decorationDelegate
    }

    fun showMonth(utcTimeMillis: Long, animated: Boolean) {
        if (lastVisibleMonth == utcMonthStartMillis(utcTimeMillis)) return
        calendarView.setVisibleDateComponents(utcDayToDateComponents(utcTimeMillis), animated = animated)
    }

    private fun reportVisibleMonth() {
        if (suppressVisibleMonthReporting) return
        val visible = calendarView.visibleDateComponents
        if (visible.year !in 1..MAX_SUPPORTED_YEAR || visible.month !in 1..MAX_MONTH) return
        val month = utcYearStartMillis(visible.year) // used only to create a valid first-of-month below
        val components = utcDayToDateComponents(month).apply { this.month = visible.month }
        val value = components.toUtcDayMillis()
        if (lastVisibleMonth == value) return
        lastVisibleMonth = value
        onVisibleMonthChanged(value)
    }

    /** UIKit may scroll to a programmatic selection; that is not owner month navigation. */
    fun preservingVisibleMonth(change: () -> Unit) {
        val visible = calendarView.visibleDateComponents
        val wasSuppressed = suppressVisibleMonthReporting
        suppressVisibleMonthReporting = true
        try {
            change()
        } finally {
            // Restore the actual month, not lastVisibleMonth, which is only an
            // observer deduplication value and can precede a UIKit layout pass.
            calendarView.setVisibleDateComponents(visible, animated = false)
            suppressVisibleMonthReporting = wasSuppressed
        }
    }

    fun applyDateBounds(minDateMillis: Long?, maxDateMillis: Long?) {
        emptyBounds = DateBounds(minDateMillis, maxDateMillis).isEmpty
        calendarView.userInteractionEnabled = requestedEnabled && !emptyBounds
        if (emptyBounds) return // Keep the last safe native interval; rules reject every day.
        val start = minDateMillis?.let(::localStartOfDay) ?: NSDate.distantPast
        val end = maxDateMillis?.let(::localEndOfDay) ?: NSDate.distantFuture
        calendarView.availableDateRange = NSDateInterval(startDate = start, endDate = end)
    }

    /**
     * Rebuilds the days around the visible month, so bounds and rule changes show right away
     * instead of on the next scroll or tap.
     */
    fun refresh() {
        val days = daysAroundVisibleMonth()
        if (days.isNotEmpty()) {
            calendarView.reloadDecorationsForDateComponents(days, animated = false)
        }
        calendarView.setNeedsLayout()
        calendarView.layoutIfNeeded()
    }

    fun applyColors(containerColor: Color, dayContentColor: Color, selectedDayContainerColor: Color) {
        calendarView.applyTheme(dark = !isDark(dayContentColor))
        calendarView.tintColor = selectedDayContainerColor.toUIColor()
        calendarView.backgroundColor = containerColor.toUIColor()
    }

    fun setEnabled(enabled: Boolean) {
        requestedEnabled = enabled
        calendarView.userInteractionEnabled = enabled && !emptyBounds
    }

    /** Every day of the visible month and its two neighbours, which may be partly on screen. */
    fun daysAroundVisibleMonth(): List<NSDateComponents> {
        val visible = calendarView.visibleDateComponents
        val year = visible.year
        val month = visible.month
        if (year !in 1..MAX_SUPPORTED_YEAR || month !in 1..MAX_MONTH) return emptyList()

        val firstOfMonth = LocalDate(year.toInt(), month.toInt(), 1)
        val start = firstOfMonth.minus(1, DateTimeUnit.MONTH)
        val end = firstOfMonth.plus(2, DateTimeUnit.MONTH)
        return generateSequence(start) { it.plus(1, DateTimeUnit.DAY) }
            .takeWhile { it < end }
            .map { date ->
                NSDateComponents().apply {
                    calendar = gregorianCalendar()
                    era = 1
                    this.year = date.year.toLong()
                    this.month = date.month.number.toLong()
                    this.day = date.day.toLong()
                }
            }
            .toList()
    }
}
