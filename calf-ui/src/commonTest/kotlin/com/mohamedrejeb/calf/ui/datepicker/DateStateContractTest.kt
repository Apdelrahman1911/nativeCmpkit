package com.mohamedrejeb.calf.ui.datepicker

import androidx.compose.material3.DatePickerDefaults
import androidx.compose.material3.DisplayMode
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SelectableDates
import androidx.compose.runtime.saveable.SaverScope
import kotlin.test.*

@OptIn(ExperimentalMaterial3Api::class)
class DateStateContractTest {
    private fun state(selected: Long? = MAR_15_2026, month: Long? = MAR_1_2026, years: IntRange = 1900..2100) =
        AdaptiveDatePickerState(selected, month, years, DisplayMode.Picker, UIKitDisplayMode.Picker)

    @Test fun setterCanonicalizesUtcDayIncludingBeforeEpoch() {
        val state = state()
        state.selectedDateMillis = MAR_15_2026 + NOON_OFFSET_MILLIS
        assertEquals(MAR_15_2026, state.selectedDateMillis)
        state.selectedDateMillis = -1L
        assertEquals(-MILLIS_PER_DAY, state.selectedDateMillis)
        state.selectedDateMillis = null
        assertNull(state.selectedDateMillis)
    }

    @Test fun constructorAndSetterRejectOutOfRangeYears() {
        assertFailsWith<IllegalArgumentException> { state(years = 2027..2028) }
        assertFailsWith<IllegalArgumentException> { state(selected = null, month = null, years = 2027..2026) }
        val state = state(years = 2026..2026)
        assertFailsWith<IllegalArgumentException> { state.selectedDateMillis = -1L }
        assertFailsWith<IllegalArgumentException> { state.displayedMonthMillis = -1L }
        assertEquals(MAR_15_2026, state.selectedDateMillis)
    }

    @Test fun programmaticSelectionDoesNotApplyBusinessRules() {
        val state = state()
        state.selectableDates = NoDates
        state.selectedDateMillis = MAR_16_2026
        assertEquals(MAR_16_2026, state.selectedDateMillis)
        assertFalse(state.isSelectionSelectable)
    }

    @Test fun nativeBoundsIntersectYearRangeAndBusinessBounds() {
        val state = state(years = 2026..2026)
        state.selectableDates = DateBounds(minDateMillis = MAR_1_2026)
        assertEquals(MAR_1_2026, state.dateBounds.minDateMillis)
        assertEquals(utcYearStartMillis(2027) - MILLIS_PER_DAY, state.dateBounds.maxDateMillis)
        assertFalse(state.isDaySelectable(utcYearStartMillis(2027)))
    }

    @Test fun yearPredicateParticipatesInSelectionAndSnapping() {
        val state = state(years = 2026..2026)
        state.selectableDates = object : SelectableDates {
            override fun isSelectableYear(year: Int) = false
        }
        assertFalse(state.isSelectionSelectable)
        assertNull(nearestSelectableDay(MAR_15_2026, null, null, state.selectableDates))
        assertEquals(MAR_15_2026, state.selectedDateMillis)
    }

    @Test fun emptyBoundsAndSameDayIntradayEndpointsAreDistinct() {
        val empty = DateBounds(MAR_16_2026, MAR_15_2026)
        assertTrue(empty.isEmpty)
        assertFalse(empty.isSelectableYear(2026))
        assertNull(nearestSelectableDay(MAR_15_2026, empty.minDateMillis, empty.maxDateMillis, DatePickerDefaults.AllDates))
        assertFalse(DateBounds(MAR_15_2026 + NOON_OFFSET_MILLIS, MAR_15_2026).isEmpty)
        assertTrue(DateBounds(MAR_16_2026).intersect(DateBounds(maxDateMillis = MAR_15_2026)).isEmpty)
    }

    @Test fun saverRetainsDifferentDisplayedMonthAndAcceptsLegacyLists() {
        val state = state()
        state.displayedMonthMillis = APR_1_2026
        val saver = AdaptiveDatePickerState.Saver()
        val saved = requireNotNull(with(saver) { SaverScope { true }.save(state) })
        val restored = requireNotNull(saver.restore(saved))
        assertEquals(MAR_15_2026, restored.selectedDateMillis)
        assertEquals(APR_1_2026, restored.displayedMonthMillis)
        val legacy = requireNotNull(saver.restore(listOf<Any?>(MAR_15_2026, 2020, 2030, 0, 0)))
        assertEquals(MAR_1_2026, legacy.displayedMonthMillis)
    }

    @Test fun yearStartAlgorithmHandlesLeapCenturiesAndNegativeEpoch() {
        assertEquals(0L, utcYearStartMillis(1970))
        for (year in listOf(1L, 1600, 1900, 1969, 2000, 2026, 2100, 9999)) {
            val millis = utcYearStartMillis(year)
            assertEquals(year.toInt(), utcYearOf(millis))
            assertEquals((year - 1).toInt(), utcYearOf(millis - 1))
        }
    }

    @Test fun rangeMembershipDoesNotEnumerateTheRange() {
        val selection = DateRangeSelection(utcYearStartMillis(1900), utcYearStartMillis(2100))
        assertTrue(selection.contains(MAR_15_2026))
        assertFalse(selection.contains(utcYearStartMillis(2101)))
        assertTrue(DateRangeSelection(MAR_15_2026, null).contains(MAR_15_2026 + 1))
        assertFalse(DateRangeSelection(null, null).contains(MAR_15_2026))
    }
}
