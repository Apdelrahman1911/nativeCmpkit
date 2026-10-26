// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
@file:OptIn(ExperimentalTime::class, ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.datepicker

import com.mohamedrejeb.calf.ui.utils.datetime.KotlinxDatetimeCalendarModel
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.datetime.DateTimeUnit
import kotlinx.datetime.LocalDate
import kotlinx.datetime.TimeZone
import kotlinx.datetime.atStartOfDayIn
import kotlinx.datetime.number
import kotlinx.datetime.plus
import platform.Foundation.NSCalendar
import platform.Foundation.NSCalendarIdentifierGregorian
import platform.Foundation.NSDate
import platform.Foundation.NSDateComponents
import platform.Foundation.NSDayCalendarUnit
import platform.Foundation.NSEraCalendarUnit
import platform.Foundation.NSMonthCalendarUnit
import platform.Foundation.NSYearCalendarUnit
import platform.Foundation.NSTimeZone
import platform.Foundation.localTimeZone
import platform.Foundation.dateWithTimeIntervalSince1970
import kotlin.time.ExperimentalTime

private val calendarModel = KotlinxDatetimeCalendarModel()

private const val MILLIS_PER_SECOND = 1000.0

/** Public timestamps are Gregorian UTC days, regardless of the user's preferred calendar. */
internal fun gregorianCalendar(timeZone: NSTimeZone = NSTimeZone.localTimeZone): NSCalendar =
    NSCalendar(calendarIdentifier = NSCalendarIdentifierGregorian).apply { this.timeZone = timeZone }

internal fun utcMonthStartMillis(utcTimeMillis: Long): Long {
    val date = utcDayToLocalDate(utcTimeMillis)
    return LocalDate(date.year, date.month, 1).atStartOfDayIn(TimeZone.UTC).toEpochMilliseconds()
}

/** The calendar day of a UTC day timestamp, as a plain date. */
internal fun utcDayToLocalDate(utcTimeMillis: Long): LocalDate {
    val canonicalDate = calendarModel.getCanonicalDate(utcTimeMillis)
    return LocalDate(
        year = canonicalDate.year,
        month = canonicalDate.month,
        day = canonicalDate.dayOfMonth,
    )
}

/** Start of the same calendar day in the device time zone. */
internal fun localStartOfDay(utcTimeMillis: Long): NSDate {
    val startMillis = utcDayToLocalDate(utcTimeMillis)
        .atStartOfDayIn(TimeZone.currentSystemDefault())
        .toEpochMilliseconds()
    return NSDate.dateWithTimeIntervalSince1970(startMillis / MILLIS_PER_SECOND)
}

/** Last millisecond of the same calendar day in the device time zone. */
internal fun localEndOfDay(utcTimeMillis: Long): NSDate {
    val nextDayStartMillis = utcDayToLocalDate(utcTimeMillis)
        .plus(1, DateTimeUnit.DAY)
        .atStartOfDayIn(TimeZone.currentSystemDefault())
        .toEpochMilliseconds()
    return NSDate.dateWithTimeIntervalSince1970((nextDayStartMillis - 1) / MILLIS_PER_SECOND)
}

/** The UTC start of the calendar day this date falls on in the device time zone. */
internal fun NSDate.toUtcDayMillis(calendar: NSCalendar = gregorianCalendar()): Long {
    val components = calendar.components(
        NSEraCalendarUnit or NSYearCalendarUnit or NSMonthCalendarUnit or NSDayCalendarUnit,
        this,
    )
    return components.toUtcDayMillis()
}

/** The UTC start of the day described by year, month and day components. */
internal fun NSDateComponents.toUtcDayMillis(): Long =
    LocalDate(year = if (era == 0L) 1 - year.toInt() else year.toInt(), month = month.toInt(), day = day.toInt())
        .atStartOfDayIn(TimeZone.UTC)
        .toEpochMilliseconds()

/** Year, month and day components for a UTC day timestamp. */
internal fun utcDayToDateComponents(utcTimeMillis: Long): NSDateComponents {
    val date = utcDayToLocalDate(utcTimeMillis)
    return NSDateComponents().apply {
        calendar = gregorianCalendar()
        timeZone = NSTimeZone.localTimeZone
        era = if (date.year <= 0) 0 else 1
        year = if (date.year <= 0) 1L - date.year else date.year.toLong()
        month = date.month.number.toLong()
        day = date.day.toLong()
    }
}
