@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.ui.utils

import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.ImageBitmapConfig
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.colorspace.ColorSpaces
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.UByteVar
import kotlinx.cinterop.convert
import kotlinx.cinterop.get
import kotlinx.cinterop.reinterpret
import platform.CoreFoundation.CFStringCompare
import platform.CoreFoundation.kCFCompareEqualTo
import platform.CoreGraphics.CGBitmapContextCreate
import platform.CoreGraphics.CGBitmapContextGetData
import platform.CoreGraphics.CGBlendMode
import platform.CoreGraphics.CGColorSpaceCreateWithName
import platform.CoreGraphics.CGColorSpaceGetName
import platform.CoreGraphics.CGColorSpaceRef
import platform.CoreGraphics.CGColorSpaceRelease
import platform.CoreGraphics.CGContextDrawImage
import platform.CoreGraphics.CGContextRef
import platform.CoreGraphics.CGContextRelease
import platform.CoreGraphics.CGContextSetBlendMode
import platform.CoreGraphics.CGImageAlphaInfo
import platform.CoreGraphics.CGImageGetColorSpace
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

/**
 * Real CoreGraphics/UIImage conversion ownership, pixel, scale and failure-injection checks.
 *
 * These are iOS simulator/device tests. They cannot run on Linux; the portable ARGB/RGBA and
 * dimension checks live in `BitmapPixelBytesTest`.
 */
@OptIn(ExperimentalNativeApi::class, NativeRuntimeApi::class)
class ImageBitmapConversionOwnershipTest {
    @Test
    fun successfulConversionReleasesEachObjectOnceInReverseOrder() {
        val bridge = CountingBridge()
        val image = assertNotNull(solidBitmap(Color.Red, width = 3, height = 2).toUIImage(2.0, bridge))

        bridge.assertBalanced()
        assertEquals(
            listOf(
                "createColorSpace",
                "createContext",
                "contextData",
                "createSnapshot",
                "createImage",
                "releaseImage",
                "releaseContext",
                "releaseColorSpace",
            ),
            bridge.events,
        )
        assertEquals(2.0, image.scale)
        assertEquals(3uL, CGImageGetWidth(assertNotNull(image.CGImage)))
        assertEquals(2uL, CGImageGetHeight(assertNotNull(image.CGImage)))
        assertSrgb(image)
    }

    @Test
    fun transparentOpaqueAndPartialAlphaPixelsKeepTheirContract() {
        val cases = listOf(
            Color.Red to listOf(255, 0, 0, 255),
            Color.Green to listOf(0, 255, 0, 255),
            Color.Blue to listOf(0, 0, 255, 255),
            Color.Transparent to listOf(0, 0, 0, 0),
            Color.Red.copy(alpha = 0.5f) to listOf(128, 0, 0, 128),
        )
        for ((color, expected) in cases) {
            val bridge = CountingBridge()
            val image = assertNotNull(solidBitmap(color).toUIImage(1.0, bridge), "color=$color")
            bridge.assertBalanced()
            assertChannels(expected, image.drawRgba(), tolerance = 1)
        }
    }

    @Test
    fun eachAllocationFailureReleasesAllAndOnlyEarlierObjects() {
        val expectedOutcomes = mapOf(
            Failure.ColorSpace to FailureExpectation(
                events = listOf("createColorSpace"),
                colorSpacesCreated = 0,
                contextsCreated = 0,
                imagesCreated = 0,
            ),
            Failure.Context to FailureExpectation(
                events = listOf("createColorSpace", "createContext", "releaseColorSpace"),
                colorSpacesCreated = 1,
                contextsCreated = 0,
                imagesCreated = 0,
            ),
            Failure.Data to FailureExpectation(
                events = listOf(
                    "createColorSpace", "createContext", "contextData", "releaseContext", "releaseColorSpace",
                ),
                colorSpacesCreated = 1,
                contextsCreated = 1,
                imagesCreated = 0,
            ),
            Failure.Snapshot to FailureExpectation(
                events = listOf(
                    "createColorSpace", "createContext", "contextData", "createSnapshot",
                    "releaseContext", "releaseColorSpace",
                ),
                colorSpacesCreated = 1,
                contextsCreated = 1,
                imagesCreated = 0,
            ),
            Failure.Image to FailureExpectation(
                events = listOf(
                    "createColorSpace", "createContext", "contextData", "createSnapshot", "createImage",
                    "releaseImage", "releaseContext", "releaseColorSpace",
                ),
                colorSpacesCreated = 1,
                contextsCreated = 1,
                imagesCreated = 1,
            ),
        )
        for ((failure, expected) in expectedOutcomes) {
            val bridge = CountingBridge(failure)
            assertNull(solidBitmap(Color.Cyan, width = 17, height = 9).toUIImage(1.0, bridge), "failure=$failure")
            bridge.assertBalanced()
            assertEquals(expected.events, bridge.events, "failure=$failure")
            assertEquals(1, bridge.colorSpaceAttempts, "failure=$failure")
            assertEquals(expected.colorSpacesCreated, bridge.colorSpacesCreated, "failure=$failure")
            assertEquals(expected.contextsCreated, bridge.contextsCreated, "failure=$failure")
            assertEquals(expected.imagesCreated, bridge.imagesCreated, "failure=$failure")
        }
    }

    @Test
    fun exceptionAtEachStageStillReleasesEarlierObjectsAndPropagates() {
        val expectedEvents = mapOf(
            Failure.ContextException to listOf(
                "createColorSpace", "createContext", "releaseColorSpace",
            ),
            Failure.DataException to listOf(
                "createColorSpace", "createContext", "contextData", "releaseContext", "releaseColorSpace",
            ),
            Failure.SnapshotException to listOf(
                "createColorSpace", "createContext", "contextData", "createSnapshot",
                "releaseContext", "releaseColorSpace",
            ),
            Failure.ImageException to listOf(
                "createColorSpace", "createContext", "contextData", "createSnapshot", "createImage",
                "releaseImage", "releaseContext", "releaseColorSpace",
            ),
        )
        for ((failure, events) in expectedEvents) {
            val bridge = CountingBridge(failure)
            assertFailsWith<IllegalStateException>("failure=$failure") {
                solidBitmap(Color.Magenta).toUIImage(1.0, bridge)
            }
            bridge.assertBalanced()
            assertEquals(events, bridge.events, "failure=$failure")
        }
    }

    @Test
    fun invalidScaleStopsBeforeAnyNativeAllocation() {
        val bitmap = solidBitmap(Color.Red, width = 2, height = 2)
        for (scale in listOf(0.0, -1.0, Double.NaN, Double.POSITIVE_INFINITY)) {
            val bridge = CountingBridge()
            assertNull(bitmap.toUIImage(scale, bridge), "scale=$scale")
            assertEquals(0, bridge.colorSpaceAttempts)
            assertTrue(bridge.events.isEmpty(), "scale=$scale events=${bridge.events}")
        }
    }

    @Test
    fun emptyOrOverflowedDimensionsStopBeforeReadingPixelsOrAllocating() {
        val invalid = listOf(
            0 to 1,
            1 to 0,
            -1 to 1,
            Int.MAX_VALUE to 2,
            65536 to 8192,
            Int.MAX_VALUE to Int.MAX_VALUE,
        )
        for ((width, height) in invalid) {
            val bridge = CountingBridge()
            assertNull(InjectedBitmap(width, height).toUIImage(1.0, bridge), "size=${width}x$height")
            assertTrue(bridge.events.isEmpty(), "size=${width}x$height events=${bridge.events}")
        }
    }

    @Test
    fun returnedImageDoesNotBorrowKotlinPixelStorage() {
        var bitmap: ImageBitmap? = solidBitmap(Color(0x8040A0E0), width = 127, height = 91)
        val bridge = CountingBridge()
        val image = assertNotNull(bitmap!!.toUIImage(2.0, bridge))
        bridge.assertBalanced()
        val expected = image.drawRgba()

        bitmap = null
        repeat(5) { GC.collect() }

        assertContentEquals(expected, image.drawRgba())
        assertEquals(127uL, CGImageGetWidth(assertNotNull(image.CGImage)))
        assertEquals(91uL, CGImageGetHeight(assertNotNull(image.CGImage)))
        assertSrgb(image)
    }

    @Test
    fun repeatedConversionsBalanceEveryAcquiredObject() {
        val bitmap = solidBitmap(Color(0x80FF8000), width = 31, height = 17)
        val bridge = CountingBridge()
        repeat(25) { iteration ->
            val image = assertNotNull(bitmap.toUIImage(1.0, bridge), "iteration=$iteration")
            assertEquals(31uL, CGImageGetWidth(assertNotNull(image.CGImage)))
            assertEquals(17uL, CGImageGetHeight(assertNotNull(image.CGImage)))
        }
        bridge.assertBalanced()
        assertEquals(25, bridge.colorSpacesCreated)
        assertEquals(25, bridge.contextsCreated)
        assertEquals(25, bridge.imagesCreated)
    }

    /** Reports hostile dimensions without allocating pixels; the production guard must return first. */
    private class InjectedBitmap(
        override val width: Int,
        override val height: Int,
    ) : ImageBitmap {
        override val colorSpace = ColorSpaces.Srgb
        override val hasAlpha = true
        override val config = ImageBitmapConfig.Argb8888

        override fun readPixels(
            buffer: IntArray,
            startX: Int,
            startY: Int,
            width: Int,
            height: Int,
            bufferOffset: Int,
            stride: Int,
        ): Unit = error("readPixels must not run for invalid dimensions")

        override fun prepareToDraw(): Unit = Unit
    }

    private enum class Failure {
        None,
        ColorSpace,
        Context,
        Data,
        Snapshot,
        Image,
        ContextException,
        DataException,
        SnapshotException,
        ImageException,
    }

    /**
     * Exact calls and owning-object counts for one injected null allocation failure.
     *
     * The counts are written per case instead of being derived from the [Failure] ordinal, so adding,
     * removing or reordering enum values cannot silently change an expectation.
     */
    private data class FailureExpectation(
        val events: List<String>,
        val colorSpacesCreated: Int,
        val contextsCreated: Int,
        val imagesCreated: Int,
    )

    /**
     * Every successful allocation delegates to the actual production bridge. Exactly one owning
     * step fails or throws, and every create/release event is recorded in call order.
     */
    private class CountingBridge(private val failure: Failure = Failure.None) : BitmapImageBridge() {
        val events = mutableListOf<String>()
        var colorSpaceAttempts = 0
        var colorSpacesCreated = 0
        var contextsCreated = 0
        var imagesCreated = 0
        private var colorSpacesReleased = 0
        private var contextsReleased = 0
        private var imagesReleased = 0

        override fun createColorSpace(): CGColorSpaceRef? {
            events += "createColorSpace"
            colorSpaceAttempts++
            if (failure == Failure.ColorSpace) return null
            return super.createColorSpace().also { if (it != null) colorSpacesCreated++ }
        }

        override fun createContext(width: Int, height: Int, space: CGColorSpaceRef): CGContextRef? {
            events += "createContext"
            if (failure == Failure.ContextException) error("Injected context construction failure")
            if (failure == Failure.Context) return null
            return super.createContext(width, height, space).also { if (it != null) contextsCreated++ }
        }

        override fun contextData(context: CGContextRef): COpaquePointer? {
            events += "contextData"
            if (failure == Failure.DataException) error("Injected context data failure")
            if (failure == Failure.Data) return null
            return super.contextData(context)
        }

        override fun createSnapshot(context: CGContextRef): CGImageRef? {
            events += "createSnapshot"
            if (failure == Failure.SnapshotException) error("Injected snapshot failure")
            if (failure == Failure.Snapshot) return null
            return super.createSnapshot(context).also { if (it != null) imagesCreated++ }
        }

        override fun createImage(image: CGImageRef, scale: Double): UIImage? {
            events += "createImage"
            if (failure == Failure.ImageException) error("Injected UIImage construction failure")
            if (failure == Failure.Image) return null
            return super.createImage(image, scale)
        }

        override fun releaseImage(image: CGImageRef) {
            events += "releaseImage"
            imagesReleased++
            super.releaseImage(image)
        }

        override fun releaseContext(context: CGContextRef) {
            events += "releaseContext"
            contextsReleased++
            super.releaseContext(context)
        }

        override fun releaseColorSpace(colorSpace: CGColorSpaceRef) {
            events += "releaseColorSpace"
            colorSpacesReleased++
            super.releaseColorSpace(colorSpace)
        }

        fun assertBalanced() {
            assertEquals(colorSpacesCreated, colorSpacesReleased, "color spaces: failure=$failure")
            assertEquals(contextsCreated, contextsReleased, "contexts: failure=$failure")
            assertEquals(imagesCreated, imagesReleased, "CGImages: failure=$failure")
        }
    }

    private fun solidBitmap(color: Color, width: Int = 1, height: Int = 1): ImageBitmap =
        ImageBitmap(width, height).also { bitmap ->
            Canvas(bitmap).drawRect(
                Rect(0f, 0f, width.toFloat(), height.toFloat()),
                Paint().apply {
                    this.color = color
                    blendMode = BlendMode.Src
                },
            )
        }

    private fun assertSrgb(image: UIImage) {
        val space = assertNotNull(CGImageGetColorSpace(assertNotNull(image.CGImage)))
        assertEquals(
            kCFCompareEqualTo,
            CFStringCompare(assertNotNull(CGColorSpaceGetName(space)), kCGColorSpaceSRGB, 0uL),
        )
    }

    private fun assertChannels(expected: List<Int>, actual: ByteArray, tolerance: Int) {
        assertEquals(expected.size, actual.size)
        expected.indices.forEach { index ->
            val byte = actual[index].toInt() and 255
            assertTrue(
                abs(expected[index] - byte) <= tolerance,
                "channel $index: expected ${expected[index]}, got $byte",
            )
        }
    }

    /** Draws the returned native image, not the input IntArray, into explicit premultiplied RGBA. */
    private fun UIImage.drawRgba(): ByteArray {
        val native = assertNotNull(CGImage)
        val width = CGImageGetWidth(native).toInt()
        val height = CGImageGetHeight(native).toInt()
        val colorSpace = assertNotNull(CGColorSpaceCreateWithName(kCGColorSpaceSRGB))
        try {
            val context = assertNotNull(
                CGBitmapContextCreate(
                    null,
                    width.convert(),
                    height.convert(),
                    8u,
                    (width * 4).convert(),
                    colorSpace,
                    CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big,
                ),
            )
            try {
                CGContextSetBlendMode(context, CGBlendMode.kCGBlendModeCopy)
                CGContextDrawImage(context, CGRectMake(0.0, 0.0, width.toDouble(), height.toDouble()), native)
                val data = assertNotNull(CGBitmapContextGetData(context)).reinterpret<UByteVar>()
                return ByteArray(width * height * 4) { data[it].toByte() }
            } finally {
                CGContextRelease(context)
            }
        } finally {
            CGColorSpaceRelease(colorSpace)
        }
    }
}
