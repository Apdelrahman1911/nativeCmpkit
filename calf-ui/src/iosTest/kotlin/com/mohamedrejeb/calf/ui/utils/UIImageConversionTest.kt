@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Paint
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
import com.mohamedrejeb.calf.ui.internal.runNativeUiTest
import com.mohamedrejeb.calf.ui.uikit.UIKitImage
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.UByteVar
import kotlinx.cinterop.convert
import kotlinx.cinterop.get
import kotlinx.cinterop.reinterpret
import kotlinx.cinterop.useContents
import platform.CoreGraphics.CGBitmapContextCreate
import platform.CoreGraphics.CGBitmapContextGetData
import platform.CoreGraphics.CGBlendMode
import platform.CoreGraphics.CGColorSpaceCreateWithName
import platform.CoreGraphics.CGColorSpaceRef
import platform.CoreGraphics.CGColorSpaceRelease
import platform.CoreGraphics.CGContextDrawImage
import platform.CoreGraphics.CGContextFillRect
import platform.CoreGraphics.CGContextRef
import platform.CoreGraphics.CGContextRelease
import platform.CoreGraphics.CGContextSetBlendMode
import platform.CoreGraphics.CGContextSetRGBFillColor
import platform.CoreGraphics.CGImageAlphaInfo
import platform.CoreGraphics.CGImageGetHeight
import platform.CoreGraphics.CGImageGetWidth
import platform.CoreGraphics.CGImageRef
import platform.CoreGraphics.CGRectMake
import platform.CoreGraphics.kCGBitmapByteOrder32Big
import platform.CoreGraphics.kCGColorSpaceSRGB
import platform.UIKit.UIImage
import kotlin.experimental.ExperimentalNativeApi
import kotlin.math.abs
import kotlin.native.runtime.GC
import kotlin.native.runtime.NativeRuntimeApi
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Real Skia -> CoreGraphics -> UIImage conversions, including ownership/failure injection. */
@OptIn(ExperimentalTestApi::class)
class UIImageConversionTest {
    @Test fun primaryTransparentAndHalfAlphaPixelsHaveExplicitRgbaChannels() = runNativeUiTest {
        listOf(
            Color.Red to listOf(255, 0, 0, 255),
            Color.Green to listOf(0, 255, 0, 255),
            Color.Blue to listOf(0, 0, 255, 255),
            Color.Transparent to listOf(0, 0, 0, 0),
            Color.Red.copy(alpha = .5f) to listOf(128, 0, 0, 128),
        ).forEach { (color, expected) ->
            val image = assertNotNull(solidBitmap(color).toUIImage())
            assertChannels(expected, image.drawRgba(), tolerance = 1)
        }
    }

    @Test fun halfAlphaCompositesCorrectlyOverBlackAndWhite() = runNativeUiTest {
        val image = assertNotNull(solidBitmap(Color.Red.copy(alpha = .5f)).toUIImage())
        assertChannels(listOf(128, 0, 0, 255), image.drawRgba(Color.Black), tolerance = 1)
        assertChannels(listOf(255, 127, 127, 255), image.drawRgba(Color.White), tolerance = 1)
    }

    @Test fun imageScaleAndDensityRetainLogicalDimensions() = runNativeUiTest {
        val vector = detailedVector()
        for (density in listOf(2f, 3f)) {
            val image = assertNotNull(UIKitImage.Vector(vector, 24.dp, 16.dp).toUIImage(density))
            assertEquals(density.toDouble(), image.scale)
            assertEquals(24.0, image.size.useContents { width })
            assertEquals(16.0, image.size.useContents { height })
            assertEquals((24 * density).toULong(), CGImageGetWidth(image.CGImage))
            assertEquals((16 * density).toULong(), CGImageGetHeight(image.CGImage))
        }
    }

    @Test fun nativeVectorPixelsMatchTheRealComposePainter() = compareVectorWithCompose(
        detailedVector(), LayoutDirection.Ltr, 3f,
    )

    @Test fun nativeVectorTintAndRtlMatchTheRealComposePainter() = compareVectorWithCompose(
        detailedVector(tint = Color(0xBB22CC44), autoMirror = true), LayoutDirection.Rtl, 2f,
    )

    @Test fun invalidScaleAndDimensionsStopBeforeNativeAllocation() = runNativeUiTest {
        val bitmap = solidBitmap(Color.Red)
        for (scale in listOf(0.0, -1.0, Double.NaN, Double.POSITIVE_INFINITY)) {
            val bridge = CountingBridge()
            assertNull(bitmap.toUIImage(scale, bridge))
            assertEquals(0, bridge.colorSpaceAttempts)
        }
        val vector = detailedVector()
        for (size in listOf(0.dp, (-1).dp, Float.NaN.dp, Float.POSITIVE_INFINITY.dp, Float.MAX_VALUE.dp)) {
            assertNull(UIKitImage.Vector(vector, size, 16.dp).toUIImage(3f))
        }
        assertNull(UIKitImage.Vector(vector).toUIImage(0f))
        assertNull(UIKitImage.Vector(vector).toUIImage(Float.NaN))
    }

    @Test fun eachAllocationFailureReleasesAllEarlierNativeObjects() = runNativeUiTest {
        val bitmap = solidBitmap(Color.Cyan, width = 17, height = 9)
        Failure.entries.filter { it != Failure.None && it != Failure.ImageException }.forEach { failure ->
            val bridge = CountingBridge(failure)
            assertNull(bitmap.toUIImage(1.0, bridge), "failure=$failure")
            bridge.assertBalanced()
            assertEquals(1, bridge.colorSpaceAttempts)
            if (failure != Failure.ColorSpace) assertEquals(1, bridge.colorSpacesCreated)
            if (failure >= Failure.Data) assertEquals(1, bridge.contextsCreated)
            if (failure >= Failure.Image) assertEquals(1, bridge.imagesCreated)
        }
    }

    @Test fun exceptionAfterSnapshotStillReleasesImageContextAndColorSpace() = runNativeUiTest {
        val bridge = CountingBridge(Failure.ImageException)
        assertFailsWith<IllegalStateException> { solidBitmap(Color.Magenta).toUIImage(1.0, bridge) }
        bridge.assertBalanced()
        assertEquals(1, bridge.imagesCreated)
    }

    @OptIn(ExperimentalNativeApi::class, NativeRuntimeApi::class)
    @Test fun returnedImageOwnsItsPixelsAfterTemporaryArraysAndContextsAreCollected() = runNativeUiTest {
        val bridge = CountingBridge()
        val image = assertNotNull(solidBitmap(Color(0x8040A0E0), width = 127, height = 91).toUIImage(2.0, bridge))
        bridge.assertBalanced()
        val expected = image.drawRgba()
        repeat(20) {
            val other = assertNotNull(solidBitmap(Color.Red, width = 257, height = 193).toUIImage())
            assertEquals(257uL, CGImageGetWidth(other.CGImage))
            GC.collect()
        }
        assertContentEquals(expected, image.drawRgba())
    }

    private fun compareVectorWithCompose(vector: ImageVector, direction: LayoutDirection, density: Float) = runComposeUiTest {
        val width = (24 * density).toInt()
        val height = (16 * density).toInt()
        setContent {
            CompositionLocalProvider(LocalDensity provides Density(1f), LocalLayoutDirection provides direction) {
                Box(Modifier.size(width.dp, height.dp).background(Color.White).testTag("reference")) {
                    Image(rememberVectorPainter(vector), null, Modifier.size(width.dp, height.dp))
                }
            }
        }
        val expected = onNodeWithTag("reference").captureToImage().toPixelMap()
        var actual = byteArrayOf()
        runOnIdle {
            val image = assertNotNull(UIKitImage.Vector(vector, 24.dp, 16.dp).toUIImage(density, direction))
            actual = image.drawRgba(Color.White)
        }
        assertEquals(width, expected.width)
        assertEquals(height, expected.height)
        var differing = 0
        for (y in 0 until height) for (x in 0 until width) {
            val offset = (y * width + x) * 4
            val target = expected[x, y]
            val channels = listOf(target.red, target.green, target.blue, target.alpha)
            if (channels.indices.any { abs((actual[offset + it].toInt() and 255) / 255f - channels[it]) > 3f / 255f }) differing++
        }
        assertTrue(differing <= width * height / 100, "$differing UIImage pixels differ from Compose VectorPainter")
    }

    private enum class Failure { None, ColorSpace, Context, Data, Snapshot, Image, ImageException }

    /** Successful allocations always delegate to actual native APIs; only one failure is injected. */
    private class CountingBridge(private val failure: Failure = Failure.None) : BitmapImageBridge() {
        var colorSpaceAttempts = 0
        var colorSpacesCreated = 0
        var contextsCreated = 0
        var imagesCreated = 0
        private var colorSpacesReleased = 0
        private var contextsReleased = 0
        private var imagesReleased = 0

        override fun createColorSpace(): CGColorSpaceRef? {
            colorSpaceAttempts++
            if (failure == Failure.ColorSpace) return null
            return super.createColorSpace().also { if (it != null) colorSpacesCreated++ }
        }

        override fun createContext(width: Int, height: Int, space: CGColorSpaceRef): CGContextRef? =
            if (failure == Failure.Context) null
            else super.createContext(width, height, space).also { if (it != null) contextsCreated++ }

        override fun contextData(context: CGContextRef): COpaquePointer? =
            if (failure == Failure.Data) null else super.contextData(context)

        override fun createSnapshot(context: CGContextRef): CGImageRef? =
            if (failure == Failure.Snapshot) null
            else super.createSnapshot(context).also { if (it != null) imagesCreated++ }

        override fun createImage(image: CGImageRef, scale: Double): UIImage? = when (failure) {
            Failure.Image -> null
            Failure.ImageException -> error("Injected UIImage construction failure")
            else -> super.createImage(image, scale)
        }

        override fun releaseColorSpace(colorSpace: CGColorSpaceRef) {
            colorSpacesReleased++
            super.releaseColorSpace(colorSpace)
        }

        override fun releaseContext(context: CGContextRef) {
            contextsReleased++
            super.releaseContext(context)
        }

        override fun releaseImage(image: CGImageRef) {
            imagesReleased++
            super.releaseImage(image)
        }

        fun assertBalanced() {
            assertEquals(colorSpacesCreated, colorSpacesReleased, "color spaces: failure=$failure")
            assertEquals(contextsCreated, contextsReleased, "contexts: failure=$failure")
            assertEquals(imagesCreated, imagesReleased, "CGImages: failure=$failure")
        }
    }

    private fun solidBitmap(color: Color, width: Int = 1, height: Int = 1): ImageBitmap =
        ImageBitmap(width, height).also { bitmap ->
            Canvas(bitmap).drawRect(Rect(0f, 0f, width.toFloat(), height.toFloat()), Paint().apply {
                this.color = color
                blendMode = BlendMode.Src
            })
        }

    private fun assertChannels(expected: List<Int>, actual: ByteArray, tolerance: Int) {
        assertEquals(expected.size, actual.size)
        expected.indices.forEach { index ->
            val byte = actual[index].toInt() and 255
            assertTrue(abs(expected[index] - byte) <= tolerance, "channel $index: expected ${expected[index]}, got $byte")
        }
    }

    /** Draws the *returned native image*, not the input IntArray, into explicit premultiplied RGBA. */
    private fun UIImage.drawRgba(background: Color = Color.Transparent): ByteArray {
        val image = assertNotNull(CGImage)
        val width = CGImageGetWidth(image).toInt()
        val height = CGImageGetHeight(image).toInt()
        val colorSpace = assertNotNull(CGColorSpaceCreateWithName(kCGColorSpaceSRGB))
        try {
            val context = assertNotNull(CGBitmapContextCreate(
                null, width.convert(), height.convert(), 8u, (width * 4).convert(), colorSpace,
                CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big,
            ))
            try {
                val rect = CGRectMake(0.0, 0.0, width.toDouble(), height.toDouble())
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeCopy)
                CGContextSetRGBFillColor(context, background.red.toDouble(), background.green.toDouble(),
                    background.blue.toDouble(), background.alpha.toDouble())
                CGContextFillRect(context, rect)
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeNormal)
                CGContextDrawImage(context, rect, image)
                val data = assertNotNull(CGBitmapContextGetData(context)).reinterpret<UByteVar>()
                return ByteArray(width * height * 4) { data[it].toByte() }
            } finally {
                CGContextRelease(context)
            }
        } finally {
            CGColorSpaceRelease(colorSpace)
        }
    }

    private fun detailedVector(tint: Color = Color.Unspecified, autoMirror: Boolean = false): ImageVector =
        ImageVector.Builder("UIImage regression", 24.dp, 16.dp, 24f, 16f, tintColor = tint, autoMirror = autoMirror).apply {
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
