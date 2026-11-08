package com.mohamedrejeb.calf.ui.utils

/**
 * True when a [width] x [height] bitmap has a positive, representable RGBA byte count.
 *
 * The multiplication is bounded before any `IntArray`/`ByteArray` allocation or pointer indexing:
 * four bytes per pixel must fit in a Kotlin array, which also keeps the CoreGraphics bytes-per-row
 * value (`width * 4`) representable as an `Int`.
 */
internal fun validBitmapRasterSize(width: Int, height: Int): Boolean =
    width > 0 && height > 0 && width.toLong() * height.toLong() <= Int.MAX_VALUE / 4

/**
 * Converts non-premultiplied sRGB ARGB integers, as returned by `ImageBitmap.readPixels`, into the
 * premultiplied big-endian RGBA byte order expected by a `CGBitmapContext` created with
 * `kCGImageAlphaPremultipliedLast | kCGBitmapByteOrder32Big`.
 */
internal fun premultipliedRgbaBytes(argb: IntArray): ByteArray {
    require(argb.size <= Int.MAX_VALUE / 4) { "Pixel byte count overflows a Kotlin array" }
    return ByteArray(argb.size * 4).also { rgba ->
        for (index in argb.indices) {
            val pixel = argb[index]
            val alpha = pixel ushr 24
            val offset = index * 4
            rgba[offset] = ((((pixel ushr 16) and 255) * alpha + 127) / 255).toByte()
            rgba[offset + 1] = ((((pixel ushr 8) and 255) * alpha + 127) / 255).toByte()
            rgba[offset + 2] = (((pixel and 255) * alpha + 127) / 255).toByte()
            rgba[offset + 3] = alpha.toByte()
        }
    }
}
