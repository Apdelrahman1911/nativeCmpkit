package com.mohamedrejeb.calf.ui.cupertino

import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.drawscope.CanvasDrawScope
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class CupertinoActivityIndicatorDrawingTest {
    @Test fun transparentCallerColorPaintsNoPixels() {
        val pixels = draw(Color.Red.copy(alpha = 0f)).toPixelMap()
        for (y in 0 until pixels.height) for (x in 0 until pixels.width) assertEquals(0f, pixels[x, y].alpha)
    }

    @Test fun halfAlphaIsAnOpacityBoundAcrossTheWholeAnimationCycle() {
        for (frame in 0 until 8) {
            val pixels = draw(Color.Red.copy(alpha = .5f), frame.toFloat()).toPixelMap()
            var maximum = 0f
            for (y in 0 until pixels.height) for (x in 0 until pixels.width) maximum = maxOf(maximum, pixels[x, y].alpha)
            assertTrue(maximum in .49f..(.5f + 1f / 255f), "frame=$frame max alpha=$maximum")
        }
    }

    @Test fun firstInactiveSpokeIsNotPaintedTwice() {
        val pixels = draw(Color.Red).toPixelMap()
        assertEquals(pixels[40, 13].alpha, pixels[67, 40].alpha, absoluteTolerance = 1f / 255f)
        assertTrue(pixels[67, 40].alpha in .09f.. .11f)
    }

    private fun draw(color: Color, angle: Float = 0f): ImageBitmap {
        val bitmap = ImageBitmap(80, 80)
        CanvasDrawScope().draw(Density(1f), LayoutDirection.Ltr, Canvas(bitmap), Size(80f, 80f)) {
            drawCupertinoActivityIndicator(color, angle)
        }
        return bitmap
    }
}
