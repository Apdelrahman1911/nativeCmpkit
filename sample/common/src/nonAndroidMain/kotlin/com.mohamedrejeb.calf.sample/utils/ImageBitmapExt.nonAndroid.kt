// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.sample.utils

import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asComposeImageBitmap
import androidx.compose.ui.graphics.asSkiaBitmap
import org.jetbrains.skia.Bitmap
import org.jetbrains.skia.Codec
import org.jetbrains.skia.Data
import org.jetbrains.skia.EncodedImageFormat
import org.jetbrains.skia.Image

actual fun ImageBitmap.toByteArray(): ByteArray {
    val image = Image.makeFromBitmap(asSkiaBitmap())
    try {
        val data = checkNotNull(image.encodeToData(EncodedImageFormat.PNG, 100)) { "PNG encoding failed" }
        try {
            return data.bytes
        } finally {
            data.close()
        }
    } finally {
        image.close()
    }
}

internal actual fun ByteArray.decodeSampleImage(): ImageBitmap {
    require(size <= MAX_SAMPLE_IMAGE_BYTES) { "The selected image exceeds the 8 MiB demo limit" }
    val data = Data.makeFromBytes(this)
    try {
        val codec = Codec.makeFromData(data)
        try {
            validateSampleImageDimensions(codec.width, codec.height)
            val bitmap = Bitmap()
            var delivered = false
            try {
                // Use fixed 32-bit software pixels rather than decoder-selected large/HDR formats.
                check(bitmap.allocN32Pixels(codec.width, codec.height)) { "Image pixel allocation failed" }
                codec.readPixels(bitmap)
                return bitmap.asComposeImageBitmap().also { delivered = true }
            } finally {
                if (!delivered) bitmap.close()
            }
        } finally {
            codec.close()
        }
    } finally {
        data.close()
    }
}

internal actual fun ImageBitmap.releaseSampleBitmap() {
    asSkiaBitmap().close()
}
