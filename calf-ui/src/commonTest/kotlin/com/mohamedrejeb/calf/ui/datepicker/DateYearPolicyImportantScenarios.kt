package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SelectableDates
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Private proposal: shared assertions, zero generated tests or production APIs. */
internal val IMPORTANT_YEAR_FIRST = utcYearStartMillis(2026)
internal val IMPORTANT_YEAR_LAST = utcYearStartMillis(2027) - MILLIS_PER_DAY
internal val IMPORTANT_MAR_17_2026 = MAR_16_2026 + MILLIS_PER_DAY

@OptIn(ExperimentalMaterial3Api::class)
internal fun importantYearState(
    selected: Long = MAR_15_2026,
    mode: UIKitDisplayMode = UIKitDisplayMode.Picker,
) = AdaptiveDatePickerState(
    initialSelectedDateMillis = selected,
    initialDisplayedMonthMillis = MAR_1_2026,
    yearRange = 2026..2026,
    initialMaterialDisplayMode = DisplayMode.Picker,
    initialUIKitDisplayMode = mode,
    selectableDates = DatePickerDefaults.AllDates,
)

@OptIn(ExperimentalMaterial3Api::class)
internal object RejectEveryYearAllowEveryDate : SelectableDates {
    override fun isSelectableYear(year: Int) = false
    override fun isSelectableDate(utcTimeMillis: Long) = true
}

/** Both actual state implementations execute these same newly added assertions. */
@OptIn(ExperimentalMaterial3Api::class)
internal fun assertImportantYearSnapPolicy(state: AdaptiveDatePickerState) {
    assertEquals(2026..2026, state.yearRange)
    for ((seed, outside, inside) in listOf(
        Triple(IMPORTANT_YEAR_FIRST, IMPORTANT_YEAR_FIRST - MILLIS_PER_DAY, IMPORTANT_YEAR_FIRST + 2 * MILLIS_PER_DAY),
        Triple(IMPORTANT_YEAR_LAST, IMPORTANT_YEAR_LAST + MILLIS_PER_DAY, IMPORTANT_YEAR_LAST - 2 * MILLIS_PER_DAY),
    )) {
        state.selectableDates = DatePickerDefaults.AllDates
        state.selectedDateMillis = seed
        state.selectableDates = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long) = utcTimeMillis == outside
        }
        // No selectable in-range result: retain an explicitly invalid in-range
        // owner selection, never throw from an attempted out-of-year snap.
        assertEquals(seed, state.selectedDateMillis)
        assertFalse(state.isSelectionSelectable)
        assertFalse(state.isDaySelectable(outside))

        state.selectableDates = DateBounds(outside, outside)
        assertTrue(state.dateBounds.isEmpty)
        assertEquals(seed, state.selectedDateMillis)

        state.selectableDates = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long) =
                utcTimeMillis == outside || utcTimeMillis == inside
        }
        // The outside day is closer, but only the in-range alternative may win.
        assertEquals(inside, state.selectedDateMillis)
        assertTrue(state.isSelectionSelectable)
        assertEquals(2026, utcYearOf(requireNotNull(state.selectedDateMillis)))
    }
    state.selectableDates = DatePickerDefaults.AllDates
}
