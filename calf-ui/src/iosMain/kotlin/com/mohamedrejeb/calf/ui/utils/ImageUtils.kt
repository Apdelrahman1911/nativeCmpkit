// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.utils

import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import com.mohamedrejeb.calf.ui.uikit.UIKitImage
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.convert
import kotlinx.cinterop.usePinned
import platform.CoreGraphics.CGBitmapContextCreate
import platform.CoreGraphics.CGBitmapContextCreateImage
import platform.CoreGraphics.CGBitmapContextGetData
import platform.CoreGraphics.CGColorSpaceCreateWithName
import platform.CoreGraphics.CGColorSpaceRelease
import platform.CoreGraphics.CGColorSpaceRef
import platform.CoreGraphics.CGContextRelease
import platform.CoreGraphics.CGContextRef
import platform.CoreGraphics.CGImageAlphaInfo
import platform.CoreGraphics.CGImageRelease
import platform.CoreGraphics.CGImageRef
import platform.CoreGraphics.kCGBitmapByteOrder32Big
import platform.CoreGraphics.kCGColorSpaceSRGB
import platform.UIKit.UIImage
import platform.UIKit.UIImageOrientation
import platform.posix.memcpy
import kotlin.math.roundToInt

/**
 * Converts a native image model without requiring a composition. Unknown SF Symbols remain null;
 * availability/fallback is the caller's policy. Vector direction is the owning view's direction.
 */
internal fun UIKitImage.toUIImage(density: Float, layoutDirection: LayoutDirection = LayoutDirection.Ltr): UIImage? =
    when (this) {
        is UIKitImage.SystemName -> UIImage.systemImageNamed(name)
        is UIKitImage.Vector -> imageVector.toUIImage(width, height, density, layoutDirection)
        is UIKitImage.Bitmap -> imageBitmap.toUIImage()
    }

private fun ImageVector.toUIImage(width: Dp, height: Dp, density: Float, direction: LayoutDirection): UIImage? {
    if (!density.isFinite() || density <= 0f) return null
    val pixelWidth = width.value.toDouble() * density
    val pixelHeight = height.value.toDouble() * density
    if (!pixelWidth.isFinite() || !pixelHeight.isFinite() || pixelWidth <= 0.0 || pixelHeight <= 0.0 ||
        pixelWidth > Int.MAX_VALUE || pixelHeight > Int.MAX_VALUE) return null
    return rasterize(pixelWidth.roundToInt().coerceAtLeast(1), pixelHeight.roundToInt().coerceAtLeast(1), density, direction)
        ?.toUIImage(scale = density.toDouble())
}

/**
 * readPixels returns unpremultiplied sRGB ARGB integers, not native RGBA memory. Convert explicitly,
 * copy while pinned into **CoreGraphics-owned** storage, then snapshot it. UIImage never borrows a
 * Kotlin array. Every successful allocation is released on all later failure/exception paths.
 */
@OptIn(ExperimentalForeignApi::class)
internal fun ImageBitmap.toUIImage(scale: Double = 1.0): UIImage? = toUIImage(scale, systemBitmapImageBridge)

@OptIn(ExperimentalForeignApi::class)
internal fun ImageBitmap.toUIImage(scale: Double, bridge: BitmapImageBridge): UIImage? {
    if (!scale.isFinite() || scale <= 0.0 || !validRasterSize(width, height)) return null
    val pixels = IntArray(width * height)
    readPixels(pixels)
    val rgba = premultipliedRgbaBytes(pixels)
    val colorSpace = bridge.createColorSpace() ?: return null
    try {
        val context = bridge.createContext(width, height, colorSpace) ?: return null
        try {
            val destination = bridge.contextData(context) ?: return null
            rgba.usePinned { pinned -> memcpy(destination, pinned.addressOf(0), rgba.size.convert()) }
            val image = bridge.createSnapshot(context) ?: return null
            try {
                return bridge.createImage(image, scale)
            } finally {
                bridge.releaseImage(image)
            }
        } finally {
            bridge.releaseContext(context)
        }
    } finally {
        bridge.releaseColorSpace(colorSpace)
    }
}

@OptIn(ExperimentalForeignApi::class)
private val systemBitmapImageBridge = BitmapImageBridge()

/**
 * The real CoreGraphics/UIImage boundary. Tests inject failure at a single allocation while using
 * actual native objects for every successful allocation, and count their corresponding releases.
 * No caller-owned Kotlin pointer is stored by a native object.
 */
@OptIn(ExperimentalForeignApi::class)
internal open class BitmapImageBridge {
    open fun createColorSpace(): CGColorSpaceRef? = CGColorSpaceCreateWithName(kCGColorSpaceSRGB)

    open fun createContext(width: Int, height: Int, space: CGColorSpaceRef): CGContextRef? =
        CGBitmapContextCreate(
            data = null,
            width = width.convert(), height = height.convert(), bitsPerComponent = 8.convert(),
            bytesPerRow = (width * 4).convert(), space = space,
            bitmapInfo = CGImageAlphaInfo.kCGImageAlphaPremultipliedLast.value or kCGBitmapByteOrder32Big,
        )

    open fun contextData(context: CGContextRef): COpaquePointer? = CGBitmapContextGetData(context)
    open fun createSnapshot(context: CGContextRef): CGImageRef? = CGBitmapContextCreateImage(context)

    @Suppress("DEPRECATION")
    open fun createImage(image: CGImageRef, scale: Double): UIImage? =
        UIImage(cGImage = image, scale = scale, orientation = UIImageOrientation.UIImageOrientationUp)

    open fun releaseImage(image: CGImageRef) = CGImageRelease(image)
    open fun releaseContext(context: CGContextRef) = CGContextRelease(context)
    open fun releaseColorSpace(colorSpace: CGColorSpaceRef) = CGColorSpaceRelease(colorSpace)
}
