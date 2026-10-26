package com.mohamedrejeb.calf.ui.utils

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class PremultipliedRgbaTest {
    @Test fun primaryColorsHaveAnExplicitByteOrder() {
        assertContentEquals(
            listOf(255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255),
            premultipliedRgbaBytes(intArrayOf(0xffff0000.toInt(), 0xff00ff00.toInt(), 0xff0000ff.toInt())).map { it.toInt() and 255 },
        )
    }

    @Test fun transparentAndTranslucentPixelsArePremultipliedWithRounding() {
        assertContentEquals(
            listOf(0, 0, 0, 0, 128, 0, 0, 128, 64, 32, 16, 128),
            premultipliedRgbaBytes(intArrayOf(0x00ffffff, 0x80ff0000.toInt(), 0x80804020.toInt())).map { it.toInt() and 255 },
        )
        assertTrue(premultipliedRgbaBytes(intArrayOf()).isEmpty())
    }

    @Test fun rasterDimensionsRejectEmptyAndOverflowedAllocations() {
        assertTrue(validRasterSize(1, 1))
        assertTrue(validRasterSize(192, 192))
        assertFalse(validRasterSize(0, 10))
        assertFalse(validRasterSize(-1, 10))
        assertFalse(validRasterSize(Int.MAX_VALUE, 2))
        assertFalse(validRasterSize(Int.MAX_VALUE, Int.MAX_VALUE))
    }
}
