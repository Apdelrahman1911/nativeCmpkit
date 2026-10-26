package com.mohamedrejeb.calf.ui.slider

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class SliderValueDomainTest {
    @Test fun negativeAccessibilityTargetSnapsToNearestStep() {
        assertEquals(-0.5f, SliderValueDomain(-1f..1f, 3).snap(-0.7f))
    }

    @Test fun allNegativeRangesAndTiesUseTheSameRule() {
        val domain = SliderValueDomain(-10f..-2f, 3)
        assertEquals(-8f, domain.snap(-8.8f))
        assertEquals(-6f, domain.snap(-7f))
        assertEquals(-10f, domain.snap(-100f))
        assertEquals(-2f, domain.snap(100f))
    }

    @Test fun continuousAndDiscreteEndpointsStayInRange() {
        for (steps in listOf(0, 1, 3, Int.MAX_VALUE)) {
            val domain = SliderValueDomain(-1f..1f, steps)
            assertEquals(-1f, domain.snap(-10f))
            assertEquals(1f, domain.snap(10f))
            for (value in -100..100) assertTrue(domain.snap(value / 100f) in -1f..1f)
        }
        assertEquals(-0.7f, SliderValueDomain(-1f..1f, 0).snap(-0.7f))
    }

    @Test fun zeroRangeAndZeroWidthNeverProduceNonFiniteValues() {
        val constant = SliderValueDomain(2f..2f, 3)
        assertEquals(0f, constant.fraction(9f))
        assertEquals(2f, constant.valueAt(0.5f))
        assertEquals(2f, constant.offsetValue(0f, 0, 40, false))
        assertEquals(2f, constant.keyboardValue(2f, 1))
        assertEquals(0f, SliderValueDomain(0f..1f, 0).offsetValue(10f, 20, 40, true))
    }

    @Test fun finiteExtremeEndpointsDoNotOverflowTheSpan() {
        val domain = SliderValueDomain(-Float.MAX_VALUE..Float.MAX_VALUE, 0)
        assertEquals(0.5f, domain.fraction(0f))
        assertEquals(0f, domain.valueAt(0.5f))
        assertTrue(domain.keyboardValue(0f, 1).isFinite())
    }

    @Test fun invalidDomainsAndValuesFailBeforeLayout() {
        for (range in listOf(1f..0f, Float.NaN..1f, 0f..Float.POSITIVE_INFINITY)) {
            assertFailsWith<IllegalArgumentException> { SliderValueDomain(range, 0) }
        }
        assertFailsWith<IllegalArgumentException> { SliderValueDomain(0f..1f, -1) }
        val domain = SliderValueDomain(0f..1f, 0)
        for (value in listOf(Float.NaN, Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY)) {
            assertFailsWith<IllegalArgumentException> { domain.coerce(value) }
        }
        assertEquals(0f, domain.fraction(-2f))
        assertEquals(1f, domain.fraction(2f))
    }

    @Test fun pointerGeometryUsesTheCurrentWidthThumbAndDirection() {
        val domain = SliderValueDomain(-1f..1f, 3)
        assertEquals(-1f, domain.offsetValue(20f, 240, 40, false))
        assertEquals(1f, domain.offsetValue(20f, 240, 40, true))
        assertEquals(0f, domain.offsetValue(120f, 240, 40, true))
        assertEquals(-0.5f, domain.offsetValue(120f, 440, 40, false))
    }

    @Test fun denseTickRenderingDoesNotAllocatePerStep() {
        assertEquals(5, sliderTickFractions(3).size)
        assertTrue(sliderTickFractions(Int.MAX_VALUE).isEmpty())
    }
}
