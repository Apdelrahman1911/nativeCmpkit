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
    private val datePickerDelegate = object : NSObject() {
        @ObjCAction
        fun onTimeChanged(sender: UIDatePicker) {
            val components = (sender.calendar ?: NSCalendar.currentCalendar).components(
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
        val calendar = datePicker.calendar ?: NSCalendar.currentCalendar
        val components = calendar.components(NSCalendarUnitYear or NSCalendarUnitMonth or
            NSCalendarUnitDay or NSCalendarUnitHour or NSCalendarUnitMinute, datePicker.date)
        if (components.hour == hour.toLong() && components.minute == minute.toLong()) return
        components.hour = hour.toLong()
        components.minute = minute.toLong()
        calendar.dateFromComponents(components)?.let { datePicker.setDate(it, animated = false) }
    }
}
