package com.mohamedrejeb.calf.sample.utils

import kotlin.test.Test
import kotlin.test.assertFailsWith

class SampleImageBoundsTest {
    @Test
    fun acceptsPositiveBoundedDimensions() {
        validateSampleImageDimensions(1, 1)
        validateSampleImageDimensions(4000, 2000)
        validateSampleImageDimensions(4096, 1)
    }

    @Test
    fun rejectsInvalidOversizedOrOverflowProneDimensionsBeforeAllocation() {
        listOf(0 to 1, 1 to 0, -1 to 1, 4097 to 1, 4000 to 2001,
            Int.MAX_VALUE to Int.MAX_VALUE, Int.MIN_VALUE to 1).forEach { (width, height) ->
            assertFailsWith<IllegalArgumentException> { validateSampleImageDimensions(width, height) }
        }
    }
}
