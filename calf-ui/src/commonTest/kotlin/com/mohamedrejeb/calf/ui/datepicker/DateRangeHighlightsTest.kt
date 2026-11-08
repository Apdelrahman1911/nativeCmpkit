package com.mohamedrejeb.calf.ui.datepicker

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class DateRangeHighlightsTest {

    @Test
    fun `missing start never consults the rule`() {
        for (selection in listOf(DateRangeSelection(null, null), DateRangeSelection(null, MAR_16_2026))) {
            assertEquals(
                emptyList(),
                selection.highlightedDaysIn(MAR_13_2026, MAR_16_2026) {
                    error("An empty selection must not consult the rule")
                },
            )
        }
    }

    @Test
    fun `unfinished range highlights only its start day`() {
        val inspected = mutableListOf<Long>()
        val selection = DateRangeSelection(MAR_14_2026 + NOON_OFFSET_MILLIS, null)

        val highlights = selection.highlightedDaysIn(MAR_13_2026, MAR_16_2026) { day ->
            inspected.add(day)
            true
        }

        assertEquals(listOf(MAR_14_2026), highlights)
        assertEquals(listOf(MAR_14_2026), inspected)
        assertEquals(MAR_14_2026 + NOON_OFFSET_MILLIS, selection.start)
        assertEquals(null, selection.end)
    }

    @Test
    fun `complete range includes both endpoints without expanding to the window`() {
        val selection = DateRangeSelection(MAR_14_2026, MAR_16_2026 + NOON_OFFSET_MILLIS)

        assertEquals(
            listOf(MAR_14_2026, MAR_15_2026, MAR_16_2026),
            selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026) { true },
        )
        assertEquals(MAR_16_2026 + NOON_OFFSET_MILLIS, selection.end)
    }

    @Test
    fun `one day one year and default sized ranges stay within the same month window budget`() {
        val windowStart = utcDay(20485)
        val windowEnd = utcDay(20573)
        val cases = listOf(
            DateRangeSelection(MAR_14_2026, MAR_14_2026) to 1,
            DateRangeSelection(utcDay(20454), utcDay(20818)) to 89,
            DateRangeSelection(utcDay(-25567), utcDay(47846)) to 89,
        )

        for ((selection, expectedCount) in cases) {
            var ruleCalls = 0
            val highlights = selection.highlightedDaysIn(windowStart, windowEnd) { day ->
                ruleCalls += 1
                assertTrue(ruleCalls <= 89)
                assertTrue(day in windowStart..windowEnd)
                true
            }

            assertEquals(expectedCount, ruleCalls)
            assertEquals(expectedCount, highlights.size)
            if (expectedCount == 89) {
                assertEquals(windowStart, highlights.first())
                assertEquals(windowEnd, highlights.last())
            }
        }
    }

    @Test
    fun `extreme selection endpoints are clipped before enumeration`() {
        val selection = DateRangeSelection(Long.MIN_VALUE, Long.MAX_VALUE)
        val inspected = mutableListOf<Long>()

        val highlights = selection.highlightedDaysIn(utcDay(-1), utcDay(1)) { day ->
            assertTrue(inspected.size < 3)
            inspected.add(day)
            true
        }

        assertEquals(listOf(utcDay(-1), utcDay(0), utcDay(1)), highlights)
        assertEquals(highlights, inspected)
        assertEquals(Long.MIN_VALUE, selection.start)
        assertEquals(Long.MAX_VALUE, selection.end)
    }

    @Test
    fun `disjoint selections do not enumerate or consult the rule`() {
        val selections = listOf(
            DateRangeSelection(JAN_1_2025, FEB_28_2026),
            DateRangeSelection(APR_1_2026, APR_1_2026),
            DateRangeSelection(JAN_1_2025, null),
        )

        for (selection in selections) {
            assertEquals(
                emptyList(),
                selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026) {
                    error("A disjoint selection must not consult the rule")
                },
            )
        }
    }

    @Test
    fun `disabled interior days leave a gap between highlighted endpoints`() {
        val selection = DateRangeSelection(MAR_13_2026, MAR_16_2026)
        val inspected = mutableListOf<Long>()

        val highlights = selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026) { day ->
            inspected.add(day)
            day != MAR_14_2026 && day != MAR_15_2026
        }

        assertEquals(listOf(MAR_13_2026, MAR_16_2026), highlights)
        assertEquals(listOf(MAR_13_2026, MAR_14_2026, MAR_15_2026, MAR_16_2026), inspected)
    }

    @Test
    fun `rule changes remove and restore highlights without changing endpoints`() {
        val selection = DateRangeSelection(MAR_13_2026, MAR_16_2026)
        val disabled = mutableSetOf<Long>()
        var ruleCalls = 0
        val rule: (Long) -> Boolean = { day ->
            ruleCalls += 1
            day !in disabled
        }
        val allDays = listOf(MAR_13_2026, MAR_14_2026, MAR_15_2026, MAR_16_2026)

        assertEquals(allDays, selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026, rule))
        disabled.addAll(listOf(MAR_14_2026, MAR_15_2026))
        assertEquals(
            listOf(MAR_13_2026, MAR_16_2026),
            selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026, rule),
        )
        disabled.addAll(allDays)
        assertEquals(emptyList(), selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026, rule))
        disabled.clear()
        assertEquals(allDays, selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026, rule))

        assertEquals(16, ruleCalls)
        assertEquals(DateRangeSelection(MAR_13_2026, MAR_16_2026), selection)
    }

    @Test
    fun `moving and revisiting the window keeps full endpoints and reads the current rule`() {
        val selection = DateRangeSelection(JAN_1_2025, APR_1_2026)

        assertEquals(
            listOf(MAR_14_2026, MAR_15_2026, MAR_16_2026),
            selection.highlightedDaysIn(MAR_14_2026, MAR_16_2026) { true },
        )
        assertEquals(
            listOf(JAN_1_2025),
            selection.highlightedDaysIn(JAN_1_2025, JAN_1_2025) { true },
        )
        assertEquals(
            listOf(MAR_14_2026, MAR_16_2026),
            selection.highlightedDaysIn(MAR_14_2026, MAR_16_2026) { it != MAR_15_2026 },
        )
        assertEquals(DateRangeSelection(JAN_1_2025, APR_1_2026), selection)
    }

    @Test
    fun `bounds and a disabled gap filter highlights without truncating the range`() {
        val selection = DateRangeSelection(JAN_1_2025, APR_1_2026)
        val highlights = selection.highlightedDaysIn(MAR_1_2026, MAR_31_2026) { day ->
            isDayWithinBounds(
                day,
                minDateMillis = MAR_13_2026 + NOON_OFFSET_MILLIS,
                maxDateMillis = MAR_16_2026 + NOON_OFFSET_MILLIS,
            ) && day != MAR_14_2026 && day != MAR_15_2026
        }

        assertEquals(listOf(MAR_13_2026, MAR_16_2026), highlights)
        assertEquals(DateRangeSelection(JAN_1_2025, APR_1_2026), selection)
    }

    @Test
    fun `pre epoch partial days use floor division`() {
        val selection = DateRangeSelection(utcDay(-2) + NOON_OFFSET_MILLIS, -1L)

        assertEquals(
            listOf(utcDay(-2), utcDay(-1)),
            selection.highlightedDaysIn(utcDay(-3), utcDay(1)) { true },
        )
    }

    @Test
    fun `reversed selection never consults the rule`() {
        assertEquals(
            emptyList(),
            DateRangeSelection(MAR_16_2026, MAR_13_2026)
                .highlightedDaysIn(MAR_1_2026, MAR_31_2026) {
                    error("A reversed selection must not consult the rule")
                },
        )
    }

    @Test
    fun `maximum window is accepted and a larger window is refused before rule evaluation`() {
        val selection = DateRangeSelection(utcDay(0), utcDay(100))
        var ruleCalls = 0
        val highlights = selection.highlightedDaysIn(utcDay(0), utcDay(92)) {
            ruleCalls += 1
            true
        }

        assertEquals(93, highlights.size)
        assertEquals(93, ruleCalls)
        assertEquals(utcDay(0), highlights.first())
        assertEquals(utcDay(92), highlights.last())
        assertFailsWith<IllegalArgumentException> {
            selection.highlightedDaysIn(utcDay(0), utcDay(93)) {
                error("An oversized window must be rejected before consulting the rule")
            }
        }
    }

    @Test
    fun `reversed window is refused before rule evaluation`() {
        assertFailsWith<IllegalArgumentException> {
            DateRangeSelection(MAR_1_2026, MAR_31_2026)
                .highlightedDaysIn(MAR_16_2026, MAR_13_2026) {
                    error("A reversed window must be rejected before consulting the rule")
                }
        }
    }

    @Test
    fun `non canonical window endpoints are refused before rule evaluation`() {
        val selection = DateRangeSelection(MAR_1_2026, MAR_31_2026)
        val windows = listOf(
            MAR_13_2026 + NOON_OFFSET_MILLIS to MAR_16_2026,
            MAR_13_2026 to MAR_16_2026 + NOON_OFFSET_MILLIS,
        )

        for ((windowStart, windowEnd) in windows) {
            assertFailsWith<IllegalArgumentException> {
                selection.highlightedDaysIn(windowStart, windowEnd) {
                    error("Non canonical windows must be rejected before consulting the rule")
                }
            }
        }
    }

    @Test
    fun `native range refresh requires the public month callback`() {
        for (version in listOf("15.7.9", "16", "16.0", "16.1.2", "invalid")) {
            assertEquals(false, supportsNativeRangeHighlighting(version), version)
        }
        for (version in listOf("16.2", "16.10", "17", "18.5", "26.0.1")) {
            assertEquals(true, supportsNativeRangeHighlighting(version), version)
        }
    }

}
