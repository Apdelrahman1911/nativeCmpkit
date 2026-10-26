// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SelectableDates

internal const val MILLIS_PER_DAY = 86_400_000L

/** How far, in days on each side, a snapped selection may move to find a selectable day. */
internal const val DEFAULT_SNAP_SEARCH_DAYS = 366

/** Canonicalize programmatic selections, independently of the caller's business rules. */
internal fun canonicalDateInYearRange(value: Long?, yearRange: IntRange): Long? {
    require(!yearRange.isEmpty()) { "yearRange must not be empty" }
    if (value == null) return null
    require(utcYearOf(value) in yearRange) { "The date must be within yearRange: $yearRange" }
    val epochDay = value.floorDiv(MILLIS_PER_DAY)
    require(epochDay >= Long.MIN_VALUE / MILLIS_PER_DAY) { "UTC start of day is not representable" }
    return epochDay * MILLIS_PER_DAY
}

/** Start of January 1 in the proleptic Gregorian calendar (inverse of [utcYearOf]). */
internal fun utcYearStartMillis(year: Long): Long {
    val marchYear = year - 1
    val era = marchYear.floorDiv(400)
    val yearOfEra = marchYear - era * 400
    val dayOfEra = yearOfEra * 365 + yearOfEra / 4 - yearOfEra / 100 + 306
    val day = era * 146097 + dayOfEra - 719468
    require(day in (Long.MIN_VALUE / MILLIS_PER_DAY)..(Long.MAX_VALUE / MILLIS_PER_DAY)) {
        "yearRange exceeds representable UTC milliseconds"
    }
    return day * MILLIS_PER_DAY
}

internal fun IntRange.dateBounds(): DateBounds {
    require(!isEmpty()) { "yearRange must not be empty" }
    return DateBounds(utcYearStartMillis(first.toLong()), utcYearStartMillis(last.toLong() + 1) - MILLIS_PER_DAY)
}

private const val DAYS_FROM_CIVIL_EPOCH_TO_UNIX_EPOCH = 719_468L
private const val DAYS_PER_ERA = 146_097L
private const val YEARS_PER_ERA = 400L

/**
 * Returns true when the UTC day containing [utcTimeMillis] lies within the inclusive
 * [minDateMillis]..[maxDateMillis] range.
 *
 * Bounds are compared at day granularity, so any timestamp inside the min or max day keeps
 * that whole day selectable. A null bound is open on that side.
 */
internal fun isDayWithinBounds(
    utcTimeMillis: Long,
    minDateMillis: Long?,
    maxDateMillis: Long?,
): Boolean {
    val day = utcTimeMillis.floorDiv(MILLIS_PER_DAY)
    val afterMin = minDateMillis == null || day >= minDateMillis.floorDiv(MILLIS_PER_DAY)
    val beforeMax = maxDateMillis == null || day <= maxDateMillis.floorDiv(MILLIS_PER_DAY)
    return afterMin && beforeMax
}

/**
 * Returns true when [year] contains at least one day of the inclusive
 * [minDateMillis]..[maxDateMillis] range. A null bound is open on that side.
 */
internal fun isYearWithinBounds(
    year: Int,
    minDateMillis: Long?,
    maxDateMillis: Long?,
): Boolean {
    val afterMin = minDateMillis == null || year >= utcYearOf(minDateMillis)
    val beforeMax = maxDateMillis == null || year <= utcYearOf(maxDateMillis)
    return afterMin && beforeMax
}

/**
 * Moves the UTC day containing [utcTimeMillis] into the inclusive bounds.
 *
 * Returns [utcTimeMillis] unchanged when it is already inside, otherwise the _start_ of the
 * minimum or maximum day in UTC, whichever is nearer. A null bound is open on that side.
 */
internal fun clampDayIntoBounds(
    utcTimeMillis: Long,
    minDateMillis: Long?,
    maxDateMillis: Long?,
): Long {
    val day = utcTimeMillis.floorDiv(MILLIS_PER_DAY)
    val minDay = minDateMillis?.floorDiv(MILLIS_PER_DAY)
    val maxDay = maxDateMillis?.floorDiv(MILLIS_PER_DAY)
    return when {
        minDay != null && day < minDay -> minDay * MILLIS_PER_DAY
        maxDay != null && day > maxDay -> maxDay * MILLIS_PER_DAY
        else -> utcTimeMillis
    }
}

/**
 * Proleptic Gregorian year of a UTC timestamp, computed without a calendar dependency
 * using the days-to-civil algorithm from Howard Hinnant's date algorithms.
 */
internal fun utcYearOf(utcTimeMillis: Long): Int {
    val days = utcTimeMillis.floorDiv(MILLIS_PER_DAY)
    val shifted = days + DAYS_FROM_CIVIL_EPOCH_TO_UNIX_EPOCH
    val era = shifted.floorDiv(DAYS_PER_ERA)
    val dayOfEra = shifted - era * DAYS_PER_ERA
    val yearOfEra = (dayOfEra - dayOfEra / 1460 + dayOfEra / 36524 - dayOfEra / 146096) / 365
    val dayOfYear = dayOfEra - (365 * yearOfEra + yearOfEra / 4 - yearOfEra / 100)
    val monthIndex = (5 * dayOfYear + 2) / 153 // 0 is March, 11 is February
    val marchBasedYear = yearOfEra + era * YEARS_PER_ERA
    return (if (monthIndex >= 10) marchBasedYear + 1 else marchBasedYear).toInt()
}

/**
 * Finds the selectable day nearest to [utcTimeMillis] and returns its _start_ in UTC.
 *
 * The day is first clamped into the bounds, then the search walks outwards one day at a
 * time, later days first, until [selectableDates] accepts one. Returns null when no day within
 * [maxDistanceDays] on either side is selectable.
 */
@OptIn(ExperimentalMaterial3Api::class)
internal fun nearestSelectableDay(
    utcTimeMillis: Long,
    minDateMillis: Long?,
    maxDateMillis: Long?,
    selectableDates: SelectableDates,
    maxDistanceDays: Int = DEFAULT_SNAP_SEARCH_DAYS,
): Long? {
    if (DateBounds(minDateMillis, maxDateMillis).isEmpty) return null
    fun isSelectable(day: Long): Boolean {
        if (day !in (Long.MIN_VALUE / MILLIS_PER_DAY)..(Long.MAX_VALUE / MILLIS_PER_DAY)) return false
        val dayStart = day * MILLIS_PER_DAY
        return isDayWithinBounds(dayStart, minDateMillis, maxDateMillis) &&
            selectableDates.isSelectableYear(utcYearOf(dayStart)) &&
            selectableDates.isSelectableDate(dayStart)
    }

    val startDay = clampDayIntoBounds(utcTimeMillis, minDateMillis, maxDateMillis)
        .floorDiv(MILLIS_PER_DAY)
    if (isSelectable(startDay)) return startDay * MILLIS_PER_DAY

    for (distance in 1..maxDistanceDays) {
        val later = startDay + distance
        if (isSelectable(later)) return later * MILLIS_PER_DAY
        val earlier = startDay - distance
        if (isSelectable(earlier)) return earlier * MILLIS_PER_DAY
    }
    return null
}

/**
 * The day a native picker should end up on after the user picked [pickedUtcTimeMillis]: the
 * pick itself when [bounds] and [selectableDates] accept it, otherwise the nearest selectable
 * day, or the pick unchanged when none is within reach.
 */
@OptIn(ExperimentalMaterial3Api::class)
internal fun resolvePickedDay(
    pickedUtcTimeMillis: Long,
    bounds: DateBounds,
    selectableDates: SelectableDates,
): Long {
    val accepted = isDayWithinBounds(pickedUtcTimeMillis, bounds.minDateMillis, bounds.maxDateMillis) &&
        selectableDates.isSelectableYear(utcYearOf(pickedUtcTimeMillis)) &&
        selectableDates.isSelectableDate(pickedUtcTimeMillis)
    if (accepted) return pickedUtcTimeMillis
    return nearestSelectableDay(pickedUtcTimeMillis, bounds.minDateMillis, bounds.maxDateMillis, selectableDates)
        ?: pickedUtcTimeMillis
}

/** True when the rule accepts the day containing [utcTimeMillis]. */
@OptIn(ExperimentalMaterial3Api::class)
internal fun AdaptiveDatePickerState.isDaySelectable(utcTimeMillis: Long): Boolean =
    utcYearOf(utcTimeMillis) in yearRange &&
        selectableDates.isSelectableYear(utcYearOf(utcTimeMillis)) &&
        selectableDates.isSelectableDate(utcTimeMillis)

/**
 * Whether a non-null selection satisfies both the year range and current date/year rules.
 * Programmatic assignment intentionally does not enforce business rules. A rule-change snap
 * can also retain an invalid selection when the bounded search finds no acceptable day.
 */
@OptIn(ExperimentalMaterial3Api::class)
val AdaptiveDatePickerState.isSelectionSelectable: Boolean
    get() = selectedDateMillis?.let(::isDaySelectable) ?: false

/** The bounds the rule enforces natively; open on both sides for rules without bounds. */
@OptIn(ExperimentalMaterial3Api::class)
internal val AdaptiveDatePickerState.dateBounds: DateBounds
    get() = yearRange.dateBounds().intersect(selectableDates.dateBoundsOrNull() ?: DateBounds())

/**
 * Moves an existing selection to the nearest selectable day when the rule no longer accepts
 * it, so every platform behaves the same way. The selection is left untouched when no
 * selectable day exists within [DEFAULT_SNAP_SEARCH_DAYS].
 */
@OptIn(ExperimentalMaterial3Api::class)
internal fun AdaptiveDatePickerState.snapSelectionToSelectable() {
    val selected = selectedDateMillis ?: return
    if (isDaySelectable(selected)) return
    val bounds = dateBounds
    val snapped = nearestSelectableDay(selected, bounds.minDateMillis, bounds.maxDateMillis, selectableDates)
        ?: return
    if (snapped != selected) {
        selectedDateMillis = snapped
    }
}
