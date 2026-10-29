// NativeCmpKit sample regressions (2026-10-29): actual Android native-graphics host, not device verification.
package com.mohamedrejeb.calf.sample.utils

import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import com.mohamedrejeb.calf.sample.screens.circleCropSampleImage
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** No fake bitmap or encoder; Robolectric loads its native graphics implementation. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], manifest = Config.NONE)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class SampleImageCodecAndroidHostTest {
    @Test fun nativePngRoundTripAndCropLeaveCallerBitmapOwnedUntilExplicitRelease() {
        val input = ImageBitmap(800, 600)
        try {
            val first = input.toByteArray()
            assertFalse(input.asAndroidBitmap().isRecycled)
            val second = input.toByteArray()
            assertTrue(first.isNotEmpty() && second.isNotEmpty())
            val decoded = second.decodeSampleImage()
            try {
                assertEquals(800, decoded.width)
                assertEquals(600, decoded.height)
            } finally {
                decoded.releaseSampleBitmap()
                assertTrue(decoded.asAndroidBitmap().isRecycled)
            }
            val crop = circleCropSampleImage(second).decodeSampleImage()
            try {
                assertEquals(SAMPLE_AVATAR_SIZE, crop.width)
                assertEquals(SAMPLE_AVATAR_SIZE, crop.height)
            } finally { crop.releaseSampleBitmap() }
        } finally {
            input.releaseSampleBitmap()
            assertTrue(input.asAndroidBitmap().isRecycled)
        }
    }

    @Test fun nativeDecoderRejectsEmptyCorruptAndOversizedEncodedInputs() {
        for (bytes in listOf(byteArrayOf(), byteArrayOf(1, 2, 3), ByteArray(MAX_SAMPLE_IMAGE_BYTES + 1))) {
            assertFailsWith<IllegalArgumentException> { bytes.decodeSampleImage() }
        }
    }

    @Test fun actualRecycledNativeBitmapCannotBecomeSilentEmptyEncodingSuccess() {
        val input = ImageBitmap(8, 4)
        input.releaseSampleBitmap()
        assertTrue(input.asAndroidBitmap().isRecycled)
        assertFailsWith<IllegalStateException> { input.toByteArray() }
    }
}
