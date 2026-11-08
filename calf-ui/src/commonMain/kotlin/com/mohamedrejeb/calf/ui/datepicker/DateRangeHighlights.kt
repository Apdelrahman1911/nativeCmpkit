package com.mohamedrejeb.calf.ui.datepicker

private const val MAX_HIGHLIGHT_WINDOW_DAYS = 93L

internal fun DateRangeSelection.highlightedDaysIn(
    windowStartMillis: Long,
    windowEndMillis: Long,
    isDaySelectable: (Long) -> Boolean,
): List<Long> {
    require(windowStartMillis % MILLIS_PER_DAY == 0L)
    require(windowEndMillis % MILLIS_PER_DAY == 0L)

    val windowStartDay = windowStartMillis / MILLIS_PER_DAY
    val windowEndDay = windowEndMillis / MILLIS_PER_DAY
    require(windowEndDay - windowStartDay in 0L until MAX_HIGHLIGHT_WINDOW_DAYS)

    val selectedStartDay = start?.floorDiv(MILLIS_PER_DAY) ?: return emptyList()
    val selectedEndDay = end?.floorDiv(MILLIS_PER_DAY) ?: selectedStartDay
    val firstDay = maxOf(selectedStartDay, windowStartDay)
    val lastDay = minOf(selectedEndDay, windowEndDay)

    return buildList {
        for (day in firstDay..lastDay) {
            val utcTimeMillis = day * MILLIS_PER_DAY
            if (isDaySelectable(utcTimeMillis)) add(utcTimeMillis)
        }
    }
}

/** The native range renderer needs the visible-month callback introduced in iOS 16.2. */
internal fun supportsNativeRangeHighlighting(systemVersion: String): Boolean {
    val version = systemVersion.split('.')
    val major = version.firstOrNull()?.toIntOrNull() ?: return false
    val minor = version.getOrNull(1)?.toIntOrNull() ?: 0
    return major > 16 || (major == 16 && minor >= 2)
}
