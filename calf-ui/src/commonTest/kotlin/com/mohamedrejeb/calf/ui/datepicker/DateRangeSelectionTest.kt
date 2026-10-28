// Modified for NativeCmpKit (2026-10-28): DEX-compatible test names, assertions unchanged.
package com.mohamedrejeb.calf.ui.datepicker

import kotlin.test.Test
import kotlin.test.assertEquals

class DateRangeSelectionTest {

    @Test
    fun firstTapStartsANewRange() {
        assertEquals(
            DateRangeSelection(start = MAR_14_2026, end = null),
            DateRangeSelection(start = null, end = null).afterTap(MAR_14_2026),
        )
    }

    @Test
    fun tappingAfterTheStartCompletesTheRange() {
        assertEquals(
            DateRangeSelection(start = MAR_14_2026, end = MAR_16_2026),
            DateRangeSelection(start = MAR_14_2026, end = null).afterTap(MAR_16_2026),
        )
    }

    @Test
    fun tappingTheStartDayAgainMakesASingleDayRange() {
        assertEquals(
            DateRangeSelection(start = MAR_14_2026, end = MAR_14_2026),
            DateRangeSelection(start = MAR_14_2026, end = null).afterTap(MAR_14_2026),
        )
    }

    @Test
    fun tappingBeforeTheStartMovesTheStart() {
        assertEquals(
            DateRangeSelection(start = MAR_13_2026, end = null),
            DateRangeSelection(start = MAR_14_2026, end = null).afterTap(MAR_13_2026),
        )
    }

    @Test
    fun tappingWhileARangeIsCompleteStartsOver() {
        assertEquals(
            DateRangeSelection(start = MAR_1_2026, end = null),
            DateRangeSelection(start = MAR_14_2026, end = MAR_16_2026).afterTap(MAR_1_2026),
        )
    }

    @Test
    fun daysInRangeListsEveryDayStartFromStartToEndInclusive() {
        assertEquals(
            listOf(MAR_13_2026, MAR_14_2026, MAR_15_2026, MAR_16_2026),
            DateRangeSelection(start = MAR_13_2026, end = MAR_16_2026).days(),
        )
        assertEquals(listOf(MAR_14_2026), DateRangeSelection(start = MAR_14_2026, end = null).days())
        assertEquals(emptyList(), DateRangeSelection(start = null, end = null).days())
    }
}
