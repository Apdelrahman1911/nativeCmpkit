package com.mohamedrejeb.calf.ui.utils

import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asSkiaPath
import androidx.compose.ui.graphics.toComposeImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.VectorGroup
import androidx.compose.ui.graphics.vector.VectorNode
import androidx.compose.ui.graphics.vector.VectorPath
import androidx.compose.ui.graphics.vector.toPath
import androidx.compose.ui.unit.Dp
import com.mohamedrejeb.calf.ui.uikit.UIKitImage
import kotlinx.cinterop.COpaquePointer
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.convert
import kotlinx.cinterop.usePinned
import org.jetbrains.skia.Color
import org.jetbrains.skia.Surface
import platform.CoreGraphics.CGBitmapContextCreate
import platform.CoreGraphics.CGBitmapContextCreateImage
import platform.CoreGraphics.CGBitmapContextGetData
import platform.CoreGraphics.CGColorSpaceCreateWithName
import platform.CoreGraphics.CGColorSpaceRef
import platform.CoreGraphics.CGColorSpaceRelease
import platform.CoreGraphics.CGContextRef
import platform.CoreGraphics.CGContextRelease
import platform.CoreGraphics.CGImageAlphaInfo
import platform.CoreGraphics.CGImageRef
import platform.CoreGraphics.CGImageRelease
import platform.CoreGraphics.kCGBitmapByteOrder32Big
import platform.CoreGraphics.kCGColorSpaceSRGB
import platform.UIKit.UIImage
import platform.UIKit.UIImageOrientation
import platform.posix.memcpy

/**
 * Converts a [UIKitImage] to a native iOS [UIImage].
 *
 * @param density The screen density (pixels per dp) used for rasterization of vector images.
 * @return The converted [UIImage], or null if the conversion fails.
 */
internal fun UIKitImage.toUIImage(density: Float): UIImage? =
    when (this) {
        is UIKitImage.SystemName -> UIImage.systemImageNamed(name)
        is UIKitImage.Vector -> imageVector.toUIImage(width, height, density)
        is UIKitImage.Bitmap -> imageBitmap.toUIImage()
    }

private fun ImageVector.toUIImage(width: Dp, height: Dp, density: Float): UIImage? {
    val pixelWidth = (width.value * density).toInt()
    val pixelHeight = (height.value * density).toInt()
    return this.toImageBitmap(pixelWidth, pixelHeight).toUIImage(scale = density.toDouble())
}

private fun ImageVector.toImageBitmap(width: Int, height: Int): ImageBitmap {
    val surface = Surface.makeRasterN32Premul(width, height)
    val canvas = surface.canvas

    canvas.clear(Color.TRANSPARENT)

    // Scale from viewport coordinates to pixel dimensions
    val scaleX = width.toFloat() / viewportWidth
    val scaleY = height.toFloat() / viewportHeight
    canvas.scale(scaleX, scaleY)

    with(canvas) {
        val paint = org.jetbrains.skia.Paint().apply {
            color = Color.BLACK
        }
        drawPath(toPath().asSkiaPath(), paint)
    }

    return surface.makeImageSnapshot().toComposeImageBitmap()
}

@OptIn(ExperimentalForeignApi::class)
internal fun ImageBitmap.toUIImage(scale: Double = 1.0): UIImage? = toUIImage(scale, systemBitmapImageBridge)

/**
 * Converts the bitmap into a [UIImage] with a new CoreGraphics-owned pixel buffer.
 *
 * [ImageBitmap.readPixels] exposes non-premultiplied sRGB ARGB integers; CoreGraphics receives
 * explicit premultiplied RGBA bytes copied while that Kotlin array is pinned. No native object
 * borrows Kotlin storage: the bitmap context allocates its own data (`data = null`), and the
 * snapshot is created before the context is released.
 *
 * Every successfully acquired color space, context and CGImage snapshot is released exactly once on
 * success and on every later null/throw path, in reverse acquisition order. [bridge] exists so native
 * tests can inject a failure at one owning step while all other steps use actual CoreGraphics.
 */
@OptIn(ExperimentalForeignApi::class)
internal fun ImageBitmap.toUIImage(scale: Double, bridge: BitmapImageBridge): UIImage? {
    if (!scale.isFinite() || scale <= 0.0 || !validBitmapRasterSize(width, height)) return null

    val argb = IntArray(width * height)
    readPixels(argb)
    val rgba = premultipliedRgbaBytes(argb)

    val colorSpace = bridge.createColorSpace() ?: return null
    try {
        val context = bridge.createContext(width, height, colorSpace) ?: return null
        try {
            val destination = bridge.contextData(context) ?: return null
            rgba.usePinned { pinned ->
                memcpy(destination, pinned.addressOf(0), rgba.size.convert())
            }
            val cgImage = bridge.createSnapshot(context) ?: return null
            try {
                return bridge.createImage(cgImage, scale)
            } finally {
                bridge.releaseImage(cgImage)
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
 * The owning CoreGraphics/UIImage boundary.
 *
 * [createColorSpace], [createContext] and [createSnapshot] wrap CoreGraphics `Create` functions and
 * return +1 objects that the caller owns; each successful acquisition is handed back exactly once
 * through its matching `release*` function.
 *
 * [createImage] is different: it returns a Kotlin/Objective-C managed [UIImage]. Kotlin/Native owns
 * that UIImage through the Objective-C interop, so this bridge never releases the UIImage manually,
 * and [releaseImage] only releases the intermediate CoreGraphics snapshot passed to it.
 */
@OptIn(ExperimentalForeignApi::class)
internal open class BitmapImageBridge {
    open fun createColorSpace(): CGColorSpaceRef? = CGColorSpaceCreateWithName(kCGColorSpaceSRGB)

    open fun createContext(width: Int, height: Int, space: CGColorSpaceRef): CGContextRef? =
        CGBitmapContextCreate(
            data = null,
            width = width.convert(),
            height = height.convert(),
            bitsPerComponent = 8.convert(),
            bytesPerRow = (width * 4).convert(),
            space = space,
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

private fun ImageVector.toPath(): Path = Path().apply {
    traverseNodes(root, this)
}

private fun traverseNodes(node: VectorNode, path: Path) {
    when (node) {
        is VectorGroup -> {
            node.iterator().forEach { childNode ->
                traverseNodes(childNode, path)
            }
        }
        is VectorPath -> {
            path.addPath(node.pathData.toPath())
        }
    }
}
