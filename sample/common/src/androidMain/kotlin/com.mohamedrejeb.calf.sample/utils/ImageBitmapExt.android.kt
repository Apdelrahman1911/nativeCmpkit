// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.sample.utils

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.graphics.asImageBitmap
import java.io.ByteArrayOutputStream

actual fun ImageBitmap.toByteArray(): ByteArray = ByteArrayOutputStream().use { output ->
    check(asAndroidBitmap().compress(Bitmap.CompressFormat.PNG, 100, output)) {
        "PNG encoding failed"
    }
    output.toByteArray()
}

internal actual fun ByteArray.decodeSampleImage(): ImageBitmap {
    require(size <= MAX_SAMPLE_IMAGE_BYTES) { "The selected image exceeds the 8 MiB demo limit" }
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(this, 0, size, bounds)
    validateSampleImageDimensions(bounds.outWidth, bounds.outHeight)
    val bitmap = requireNotNull(BitmapFactory.decodeByteArray(this, 0, size,
        BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888 })) {
        "The selected file could not be decoded"
    }
    return bitmap.asImageBitmap()
}

internal actual fun ImageBitmap.releaseSampleBitmap() {
    asAndroidBitmap().recycle()
}
