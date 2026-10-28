package com.mohamedrejeb.calf.ui.cupertino

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.drawscope.CanvasDrawScope
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import kotlin.math.abs
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

    @OptIn(ExperimentalTestApi::class)
    @Test fun publicIndicatorPreservesSemanticsOpacityAndEightFramesAcrossItsActualCycle() = runComposeUiTest {
        var tint by mutableStateOf(Color.Red.copy(alpha = .5f))
        mainClock.autoAdvance = false
        setContent {
            CompositionLocalProvider(LocalDensity provides Density(1f)) {
                Box(Modifier.size(80.dp).background(Color.White)) {
                    CupertinoActivityIndicator(tint, Modifier.size(80.dp).testTag("spinner"))
                }
            }
        }
        val indicator = onNodeWithTag("spinner")
        val progress = SemanticsMatcher.expectValue(
            SemanticsProperties.ProgressBarRangeInfo, ProgressBarRangeInfo.Indeterminate,
        )
        indicator.assert(progress)
        // Initialize the real infinite transition, then sample safely between
        // its 125ms boundaries. Capture never advances the controlled clock.
        mainClock.advanceTimeByFrame()
        mainClock.advanceTimeByFrame()
        mainClock.advanceTimeBy(64, ignoreFrameDuration = true)
        var first: ImageBitmap? = null
        for (frame in 0..8) {
            if (frame != 0) mainClock.advanceTimeBy(125, ignoreFrameDuration = true)
            val actual = indicator.captureToImage()
            assertEquals(80, actual.width)
            assertEquals(80, actual.height)
            val expected = drawOnWhite(tint, (frame % 8).toFloat())
            assertSamePixels(expected, actual, "animation frame=$frame")
            if (frame == 0) first = actual
            if (frame == 8) assertSamePixels(first!!, actual, "one-second restart")
            indicator.assert(progress)
        }
        // A changed caller color reaches the actual public composable; no
        // remembered opaque paint remains after a transparent update.
        runOnIdle { tint = Color.Red.copy(alpha = 0f) }
        mainClock.advanceTimeByFrame()
        assertSamePixels(drawOnWhite(tint, 0f), indicator.captureToImage(), "transparent update")
        indicator.assert(progress)
    }

    private fun drawOnWhite(color: Color, angle: Float): ImageBitmap {
        val bitmap = ImageBitmap(80, 80)
        CanvasDrawScope().draw(Density(1f), LayoutDirection.Ltr, Canvas(bitmap), Size(80f, 80f)) {
            drawRect(Color.White)
            drawCupertinoActivityIndicator(color, angle)
        }
        return bitmap
    }

    private fun assertSamePixels(expected: ImageBitmap, actual: ImageBitmap, label: String) {
        val a = actual.toPixelMap()
        val e = expected.toPixelMap()
        assertEquals(e.width, a.width)
        assertEquals(e.height, a.height)
        var differing = 0
        for (y in 0 until a.height) for (x in 0 until a.width) {
            val left = a[x, y]
            val right = e[x, y]
            if (abs(left.red - right.red) > 2f / 255f || abs(left.green - right.green) > 2f / 255f ||
                abs(left.blue - right.blue) > 2f / 255f || abs(left.alpha - right.alpha) > 2f / 255f) differing++
        }
        assertEquals(0, differing, "$label: public pixels must match all eight production spokes")
    }

    private fun draw(color: Color, angle: Float = 0f): ImageBitmap {
        val bitmap = ImageBitmap(80, 80)
        CanvasDrawScope().draw(Density(1f), LayoutDirection.Ltr, Canvas(bitmap), Size(80f, 80f)) {
            drawCupertinoActivityIndicator(color, angle)
        }
        return bitmap
    }
}
