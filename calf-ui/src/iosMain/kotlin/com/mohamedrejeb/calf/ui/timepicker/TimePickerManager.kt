// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.timepicker

import androidx.compose.runtime.mutableStateOf
import com.mohamedrejeb.calf.core.InternalCalfApi
import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.ObjCAction
import kotlinx.cinterop.useContents
import platform.Foundation.*
import platform.UIKit.*
import platform.darwin.NSObject
import platform.objc.sel_registerName

@OptIn(ExperimentalForeignApi::class)
class TimePickerManager internal constructor(
    private val datePicker: UIDatePicker,
    initialMinute: Int,
    initialHour: Int,
    @Suppress("UNUSED_PARAMETER") is24Hour: Boolean,
    private val onHourChanged: (hour: Int) -> Unit,
    private val onMinuteChanged: (minute: Int) -> Unit,
) {
    private var disposed = false

    private val datePickerDelegate = object : NSObject() {
        @ObjCAction
        fun onTimeChanged(sender: UIDatePicker) {
            requireMain()
            if (disposed) return
            val components = effectiveCalendar(sender).components(
                NSCalendarUnitHour or NSCalendarUnitMinute,
                sender.date
            )

            onHourChanged(components.hour.toInt())
            onMinuteChanged(components.minute.toInt())
        }
    }

    val datePickerWidth = mutableStateOf(0f)
    val datePickerHeight = mutableStateOf(0f)

    init {
        requireMain()
        val calendar = NSCalendar.currentCalendar
        val dateComponents = calendar.components(
            NSCalendarUnitYear or NSCalendarUnitMonth or NSCalendarUnitDay,
            NSDate(),
        ).apply {
            minute = initialMinute.toLong()
            hour = initialHour.toLong()
        }

        val date = calendar.dateFromComponents(dateComponents) ?: NSDate()

        datePicker.apply {
            this.date = date
            this.calendar = calendar
            locale = NSLocale.currentLocale
            datePickerMode = UIDatePickerMode.UIDatePickerModeTime
            preferredDatePickerStyle = UIDatePickerStyle.UIDatePickerStyleWheels

            // Add target using NSObject delegate
            addTarget(
                target = datePickerDelegate,
                action = sel_registerName("onTimeChanged:"),
                forControlEvents = UIControlEventValueChanged
            )
        }

        datePicker.sizeToFit()

        datePicker.frame.useContents {
            datePickerWidth.value = this.size.width.toFloat()
            datePickerHeight.value = this.size.height.toFloat()
        }
    }

    internal fun setTime(hour: Int, minute: Int) {
        requireMain()
        if (disposed) return
        val calendar = effectiveCalendar(datePicker)
        val components = calendar.components(NSCalendarUnitYear or NSCalendarUnitMonth or
            NSCalendarUnitDay or NSCalendarUnitHour or NSCalendarUnitMinute, datePicker.date)
        if (components.hour == hour.toLong() && components.minute == minute.toLong()) return
        components.hour = hour.toLong()
        components.minute = minute.toLong()
        calendar.dateFromComponents(components)?.let { datePicker.setDate(it, animated = false) }
    }

    /** UIKit's explicit picker zone takes precedence over the calendar's snapshot. */
    private fun effectiveCalendar(picker: UIDatePicker): NSCalendar =
        ((picker.calendar ?: NSCalendar.currentCalendar).copyWithZone(null) as NSCalendar).apply {
            timeZone = picker.timeZone ?: NSTimeZone.localTimeZone
        }

    /** Detach only our action; a retained obsolete control must not edit hoisted state. */
    internal fun dispose() {
        requireMain()
        if (disposed) return
        disposed = true
        datePicker.removeTarget(datePickerDelegate, sel_registerName("onTimeChanged:"), UIControlEventValueChanged)
    }

    private fun requireMain() = check(NSThread.isMainThread) { "UIKit time picker operations must run on Main" }
}
