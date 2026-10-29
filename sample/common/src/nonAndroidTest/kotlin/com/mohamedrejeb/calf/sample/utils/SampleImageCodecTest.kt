package com.mohamedrejeb.calf.sample.utils

import androidx.compose.ui.graphics.ImageBitmap
import com.mohamedrejeb.calf.sample.screens.circleCropSampleImage
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFails
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** Exercises the actual sample/Skia decoder and encoder, not a fake image implementation. */
class SampleImageCodecTest {
    @Test
    fun validPngRoundTripsAndEncoderDoesNotTakeCallerBitmapOwnership() {
        val input = ImageBitmap(8, 4)
        try {
            val first = input.toByteArray()
            assertTrue(first.isNotEmpty())
            val second = input.toByteArray() // The first encoding must not close the caller's bitmap.
            val decoded = second.decodeSampleImage()
            try {
                assertEquals(8, decoded.width)
                assertEquals(4, decoded.height)
            } finally { decoded.releaseSampleBitmap() }
        } finally { input.releaseSampleBitmap() }
    }

    @Test
    fun circleExportCapsTheOutputTo512AndHandlesSmallImages() {
        for ((width, height) in listOf(800 to 600, 8 to 4)) {
            val input = ImageBitmap(width, height)
            val bytes = try { input.toByteArray() } finally { input.releaseSampleBitmap() }
            val output = circleCropSampleImage(bytes).decodeSampleImage()
            try {
                val expected = minOf(width, height, SAMPLE_AVATAR_SIZE)
                assertEquals(expected, output.width)
                assertEquals(expected, output.height)
            } finally { output.releaseSampleBitmap() }
        }
    }

    @Test
    fun decoderRejectsCorruptInputAndEncodedSizeAboveTheLimit() {
        assertFails { byteArrayOf(1, 2, 3).decodeSampleImage() }
        assertFailsWith<IllegalArgumentException> { ByteArray(MAX_SAMPLE_IMAGE_BYTES + 1).decodeSampleImage() }
    }

    @Test
    fun rejectsOversizedPngHeaderBeforeAttemptingFullPixelDecode() {
        val input = ImageBitmap(1, 1)
        val bytes = try { input.toByteArray() } finally { input.releaseSampleBitmap() }
        // Rewrite only IHDR dimensions and its CRC. The tiny compressed pixel data
        // deliberately cannot satisfy that header: the size check must reject first.
        writeInt(bytes, 16, 4000)
        writeInt(bytes, 20, 2001)
        writeInt(bytes, 29, crc32(bytes, 12, 29))
        val error = assertFailsWith<IllegalArgumentException> { bytes.decodeSampleImage() }
        assertTrue(error.message.orEmpty().contains("8 megapixels"))
    }

    private fun writeInt(bytes: ByteArray, index: Int, value: Int) {
        repeat(4) { bytes[index + it] = (value ushr (24 - 8 * it)).toByte() }
    }

    private fun crc32(bytes: ByteArray, start: Int, end: Int): Int {
        var crc = -1
        for (index in start until end) {
            crc = crc xor (bytes[index].toInt() and 0xff)
            repeat(8) { crc = if (crc and 1 == 1) (crc ushr 1) xor 0xedb88320.toInt() else crc ushr 1 }
        }
        return crc.inv()
    }
}
