package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.toPixelMap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.graphics.vector.rememberVectorPainter
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.captureToImage
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.v2.runComposeUiTest
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

@OptIn(ExperimentalTestApi::class)
class ImageRasterizationTest {
    @Test fun nestedGroupsClipsPaintsEvenOddAndTrimMatchComposeVectorPainter() = compareWithCompose(
        detailedVector(), LayoutDirection.Ltr, 3f,
    )

    @Test fun tintAndRtlAutoMirrorMatchComposeVectorPainterAtTwoTimesDensity() = compareWithCompose(
        detailedVector(tint = Color(0xBB22CC44), autoMirror = true), LayoutDirection.Rtl, 2f,
    )

    @Test fun invalidSizesAndViewportDoNotAllocateARaster() {
        val vector = detailedVector()
        assertNull(vector.rasterize(0, 10))
        assertNull(vector.rasterize(-1, 10))
        assertNull(vector.rasterize(Int.MAX_VALUE, 10))
        assertNull(vector.rasterize(10, 10, Float.NaN))
        assertNull(vector.rasterize(10, 10, -1f))
        val invalid = ImageVector.Builder(defaultWidth = 1.dp, defaultHeight = 1.dp, viewportWidth = 0f, viewportHeight = 1f).build()
        assertNull(invalid.rasterize(10, 10))
    }

    @Test fun transparentVectorRetainsTransparentPixels() {
        val empty = ImageVector.Builder(defaultWidth = 24.dp, defaultHeight = 16.dp, viewportWidth = 24f, viewportHeight = 16f).build()
        val bitmap = assertNotNull(empty.rasterize(48, 32))
        val map = bitmap.toPixelMap()
        for (y in 0 until map.height) for (x in 0 until map.width) assertEquals(0f, map[x, y].alpha)
    }

    private fun compareWithCompose(vector: ImageVector, direction: LayoutDirection, density: Float) = runComposeUiTest {
        val width = (24 * density).toInt()
        val height = (16 * density).toInt()
        val raster = assertNotNull(vector.rasterize(width, height, density, direction))
        setContent {
            CompositionLocalProvider(LocalDensity provides Density(1f), LocalLayoutDirection provides direction) {
                Box(Modifier.size(width.dp, height.dp).background(Color.White).testTag("reference")) {
                    Image(rememberVectorPainter(vector), null, Modifier.size(width.dp, height.dp))
                }
            }
        }
        val expected = onNodeWithTag("reference").captureToImage().toPixelMap()
        val actual = raster.toPixelMap()
        assertEquals(width, expected.width)
        assertEquals(height, expected.height)
        var differing = 0
        for (y in 0 until height) for (x in 0 until width) {
            val a = actual[x, y]
            val e = expected[x, y]
            // Composite over the same opaque white used by the real reference control.
            val channels = listOf(a.red * a.alpha + 1f - a.alpha, a.green * a.alpha + 1f - a.alpha, a.blue * a.alpha + 1f - a.alpha)
            val target = listOf(e.red, e.green, e.blue)
            if (channels.indices.any { abs(channels[it] - target[it]) > 3f / 255f }) differing++
        }
        assertTrue(differing <= width * height / 100, "$differing pixels differ from Compose VectorPainter")
    }

    private fun detailedVector(tint: Color = Color.Unspecified, autoMirror: Boolean = false): ImageVector =
        ImageVector.Builder("native bridge regression", 24.dp, 16.dp, 24f, 16f, tintColor = tint, autoMirror = autoMirror).apply {
            addPath(PathParser().parsePathString("M0,0 H9 V6 H0 Z M2,2 H7 V4 H2 Z").toNodes(),
                pathFillType = PathFillType.EvenOdd, fill = SolidColor(Color.Red), fillAlpha = .7f)
            addGroup(translationX = 13f, translationY = 4f, rotate = 30f, pivotX = 2f, pivotY = 2f, scaleX = .8f, scaleY = 1.3f)
            addPath(PathParser().parsePathString("M0,0 H6 V6 H0 Z").toNodes(), fill = SolidColor(Color.Blue),
                stroke = SolidColor(Color.Yellow), strokeLineWidth = .5f, strokeAlpha = .6f)
            addGroup(translationX = 1f, translationY = 1f, clipPathData = PathParser().parsePathString("M0,0 H3 V3 H0 Z").toNodes())
            addPath(PathParser().parsePathString("M-1,-1 H5 V5 H-1 Z").toNodes(),
                fill = Brush.horizontalGradient(listOf(Color.Cyan, Color.Magenta), endX = 5f))
            clearGroup()
            clearGroup()
            addPath(PathParser().parsePathString("M1,12 H21").toNodes(), stroke = SolidColor(Color.Green),
                strokeLineWidth = 2f, strokeLineCap = StrokeCap.Round, trimPathStart = .2f, trimPathEnd = .8f, trimPathOffset = .1f)
        }.build()
}
