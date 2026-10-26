package com.mohamedrejeb.calf.ui.utils

/** Converts unpremultiplied sRGB ARGB Int pixels (ImageBitmap.readPixels) to explicit RGBA bytes. */
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
