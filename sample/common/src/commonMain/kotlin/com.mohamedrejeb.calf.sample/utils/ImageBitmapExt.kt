// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.sample.utils

import androidx.compose.ui.graphics.ImageBitmap

/** Encodes a PNG without taking ownership of the caller's bitmap; fails on encoding errors. */
expect fun ImageBitmap.toByteArray(): ByteArray

internal const val MAX_SAMPLE_IMAGE_BYTES = 8 * 1024 * 1024
internal const val MAX_SAMPLE_IMAGE_PIXELS = 8_000_000L
internal const val MAX_SAMPLE_IMAGE_DIMENSION = 4096
internal const val SAMPLE_AVATAR_SIZE = 512

/** Check decoder header dimensions before allocating pixel storage, using non-overflowing arithmetic. */
internal fun validateSampleImageDimensions(width: Int, height: Int) {
    require(width > 0 && height > 0) { "The selected file is not a decodable image" }
    require(width <= MAX_SAMPLE_IMAGE_DIMENSION && height <= MAX_SAMPLE_IMAGE_DIMENSION &&
        width.toLong() * height.toLong() <= MAX_SAMPLE_IMAGE_PIXELS
    ) { "This demo accepts images up to 8 megapixels and 4096 pixels per side" }
}

/**
 * Header-checks before full decode. Returns a privately owned software bitmap;
 * the sample must call [releaseSampleBitmap] after its synchronous work completes.
 */
internal expect fun ByteArray.decodeSampleImage(): ImageBitmap

/** Only for bitmaps privately allocated by this sample, never an AsyncImage/Coil-owned bitmap. */
internal expect fun ImageBitmap.releaseSampleBitmap()
