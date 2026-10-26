// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(BetaInteropApi::class, ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCAction
import kotlinx.datetime.TimeZone
import kotlinx.datetime.toNSTimeZone
import platform.Foundation.NSDate
import platform.UIKit.UIColor
import platform.UIKit.UIControlEventValueChanged
import platform.UIKit.UIDatePicker
import platform.UIKit.UIDatePickerMode
import platform.UIKit.UIDatePickerStyle
import platform.UIKit.UIView
import platform.darwin.NSObject
import platform.objc.sel_registerName

/**
 * Picker backed by `UIDatePicker`: the wheels and compact styles, and the inline fallback below
 * iOS 16. `UIDatePicker` can only enforce a minimum and a maximum date, so a picked day the
 * rule rejects is replaced by [resolveSelection] and the control moves to that day.
 */
internal class UIDatePickerBackend(
    initialSelectedDateMillis: Long?,
    style: UIDatePickerStyle,
    private val onSelectionChanged: (utcTimeMillis: Long?) -> Unit,
    private val resolveSelection: (pickedUtcTimeMillis: Long) -> Long?,
) : IosDatePickerBackend {

    private val datePicker = UIDatePicker()
    private var requestedEnabled = true
    private var emptyBounds = false

    private val valueChangedTarget = object : NSObject() {
        @Suppress("unused")
        @ObjCAction
        fun onDateChanged(sender: UIDatePicker) {
            val picked = sender.date.toUtcDayMillis()
            val resolved = resolveSelection(picked)
            if (resolved != null && resolved != picked) {
                sender.setDate(localStartOfDay(resolved), animated = true)
            }
            onSelectionChanged(resolved)
        }
    }

    override val view: UIView
        get() = datePicker

    init {
        datePicker.setDate(initialSelectedDateMillis?.let(::localStartOfDay) ?: NSDate(), animated = false)
        datePicker.locale = getCalendarLocalDefault()
        datePicker.calendar = gregorianCalendar()
        datePicker.timeZone = TimeZone.currentSystemDefault().toNSTimeZone()
        datePicker.datePickerMode = UIDatePickerMode.UIDatePickerModeDate
        datePicker.preferredDatePickerStyle = style
        datePicker.sizeToFit()
        datePicker.addTarget(
            target = valueChangedTarget,
            action = sel_registerName("onDateChanged:"),
            forControlEvents = UIControlEventValueChanged,
        )
    }

    override fun setSelectedDate(utcTimeMillis: Long?) {
        // The wheels always show a date, so a cleared selection leaves them where they are.
        val target = utcTimeMillis ?: return
        if (datePicker.date.toUtcDayMillis() == target) return
        datePicker.setDate(localStartOfDay(target), animated = true)
    }

    override fun applyDateBounds(minDateMillis: Long?, maxDateMillis: Long?) {
        emptyBounds = DateBounds(minDateMillis, maxDateMillis).isEmpty
        // Clear the old pair first: switching from a disjoint range must not temporarily
        // leave minimumDate greater than maximumDate, even for nonempty new bounds.
        datePicker.minimumDate = null
        datePicker.maximumDate = null
        if (!emptyBounds) {
            datePicker.maximumDate = maxDateMillis?.let(::localEndOfDay)
            datePicker.minimumDate = minDateMillis?.let(::localStartOfDay)
        }
        datePicker.enabled = requestedEnabled && !emptyBounds
    }

    override fun updateSelectableDates() {
        // UIDatePicker cannot grey out individual days; rejected picks are resolved on change.
    }

    override fun setEnabled(enabled: Boolean) {
        requestedEnabled = enabled
        datePicker.enabled = enabled && !emptyBounds
    }

    override fun applyColors(containerColor: UIColor, selectedDayContainerColor: UIColor) {
        datePicker.tintColor = selectedDayContainerColor
        datePicker.backgroundColor = containerColor
    }
}
