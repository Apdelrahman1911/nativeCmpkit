// Modified for NativeCmpKit (2026-10-28): DEX-compatible test names, assertions unchanged.
package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

@OptIn(ExperimentalMaterial3Api::class)
class DateBoundsTest {

    @Test
    fun everyDayIsWithinBoundsWhenNoBoundsAreSet() {
        assertTrue(isDayWithinBounds(MAR_15_2026 + NOON_OFFSET_MILLIS, minDateMillis = null, maxDateMillis = null))
    }

    @Test
    fun daysBeforeTheMinimumAreRejectedAndTheMinimumDayItselfIsAccepted() {
        assertFalse(isDayWithinBounds(FEB_28_2026, minDateMillis = MAR_1_2026, maxDateMillis = null))
        assertTrue(isDayWithinBounds(MAR_1_2026, minDateMillis = MAR_1_2026, maxDateMillis = null))
    }

    @Test
    fun daysAfterTheMaximumAreRejectedAndTheMaximumDayItselfIsAccepted() {
        assertTrue(isDayWithinBounds(MAR_31_2026, minDateMillis = null, maxDateMillis = MAR_31_2026))
        assertFalse(isDayWithinBounds(APR_1_2026, minDateMillis = null, maxDateMillis = MAR_31_2026))
    }

    @Test
    fun boundsAreComparedAtDayGranularity() {
        assertTrue(isDayWithinBounds(MAR_1_2026, minDateMillis = MAR_1_2026 + NOON_OFFSET_MILLIS, maxDateMillis = null))
        assertTrue(isDayWithinBounds(MAR_31_2026 + NOON_OFFSET_MILLIS, minDateMillis = null, maxDateMillis = MAR_31_2026))
    }

    @Test
    fun yearsOutsideTheBoundsAreRejected() {
        assertFalse(isYearWithinBounds(2025, minDateMillis = MAR_1_2026, maxDateMillis = MAR_31_2026))
        assertTrue(isYearWithinBounds(2026, minDateMillis = MAR_1_2026, maxDateMillis = MAR_31_2026))
        assertFalse(isYearWithinBounds(2027, minDateMillis = MAR_1_2026, maxDateMillis = MAR_31_2026))
        assertTrue(isYearWithinBounds(1999, minDateMillis = null, maxDateMillis = null))
    }

    @Test
    fun utcYearIsDerivedFromEpochMillisAcrossYearAndLeapBoundaries() {
        assertEquals(1970, utcYearOf(0))
        assertEquals(1969, utcYearOf(-1))
        assertEquals(2000, utcYearOf(FEB_29_2000))
        assertEquals(2024, utcYearOf(JAN_1_2025 - 1))
        assertEquals(2025, utcYearOf(JAN_1_2025))
        assertEquals(2026, utcYearOf(MAR_1_2026))
    }

    @Test
    fun clampingKeepsADayInsideTheBoundsUnchanged() {
        assertEquals(MAR_15_2026, clampDayIntoBounds(MAR_15_2026, minDateMillis = MAR_1_2026, maxDateMillis = MAR_31_2026))
    }

    @Test
    fun clampingMovesADayBeforeTheMinimumToTheStartOfTheMinimumDay() {
        assertEquals(MAR_1_2026, clampDayIntoBounds(FEB_28_2026, minDateMillis = MAR_1_2026 + NOON_OFFSET_MILLIS, maxDateMillis = null))
    }

    @Test
    fun clampingMovesADayAfterTheMaximumToTheStartOfTheMaximumDay() {
        assertEquals(MAR_31_2026, clampDayIntoBounds(APR_1_2026, minDateMillis = null, maxDateMillis = MAR_31_2026 + NOON_OFFSET_MILLIS))
    }

    @Test
    fun nearestSelectableDayIsTheStartOfTheDayItselfWhenItIsSelectable() {
        assertEquals(
            MAR_15_2026,
            nearestSelectableDay(MAR_15_2026 + NOON_OFFSET_MILLIS, null, null, DatePickerDefaults.AllDates),
        )
    }

    @Test
    fun nearestSelectableDaySkipsTheDaysTheRuleRejects() {
        assertEquals(MAR_13_2026, nearestSelectableDay(MAR_14_2026, null, null, WeekdaysOnly))
        assertEquals(MAR_16_2026, nearestSelectableDay(MAR_15_2026, null, null, WeekdaysOnly))
    }

    @Test
    fun nearestSelectableDayStaysInsideTheBounds() {
        assertEquals(MAR_31_2026, nearestSelectableDay(APR_1_2026, null, MAR_31_2026, DatePickerDefaults.AllDates))
        assertEquals(MAR_1_2026, nearestSelectableDay(FEB_28_2026, MAR_1_2026, null, DatePickerDefaults.AllDates))
    }

    @Test
    fun nearestSelectableDayIsNullWhenNothingIsSelectableWithinTheSearchWindow() {
        assertNull(nearestSelectableDay(MAR_15_2026, null, null, NoDates, maxDistanceDays = 3))
    }

    @Test
    fun aPickedDayIsKeptWhenTheBoundsAndTheRuleAcceptIt() {
        assertEquals(MAR_13_2026, resolvePickedDay(MAR_13_2026, DateBounds(MAR_1_2026, MAR_31_2026), WeekdaysOnly))
    }

    @Test
    fun aRejectedPickResolvesToTheNearestSelectableDay() {
        assertEquals(MAR_13_2026, resolvePickedDay(MAR_14_2026, DateBounds(), WeekdaysOnly))
        assertEquals(MAR_31_2026, resolvePickedDay(APR_1_2026, DateBounds(maxDateMillis = MAR_31_2026), DatePickerDefaults.AllDates))
    }

    @Test
    fun aRejectedPickIsKeptWhenNothingSelectableIsWithinReach() {
        assertEquals(MAR_14_2026, resolvePickedDay(MAR_14_2026, DateBounds(), NoDates))
    }
}
