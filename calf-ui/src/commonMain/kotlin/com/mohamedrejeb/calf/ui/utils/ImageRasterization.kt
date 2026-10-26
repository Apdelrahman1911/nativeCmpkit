package com.mohamedrejeb.calf.ui.utils

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Canvas
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathMeasure
import androidx.compose.ui.graphics.drawscope.CanvasDrawScope
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.graphics.isSpecified
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.VectorGroup
import androidx.compose.ui.graphics.vector.VectorPath
import androidx.compose.ui.graphics.vector.toPath
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.LayoutDirection

/**
 * Non-composable vector rasterization for native managers. Uses Compose's drawing primitives,
 * matching ImageVector's scale -> rotate -> translate groups, paints, clips and trim semantics.
 * No manually owned Skia Surface/Image/Paint escapes this bridge.
 */
internal fun ImageVector.rasterize(
    width: Int,
    height: Int,
    density: Float = 1f,
    layoutDirection: LayoutDirection = LayoutDirection.Ltr,
): ImageBitmap? {
    if (!validRasterSize(width, height) || !density.isFinite() || density <= 0f) return null
    val viewportWidth = if (this.viewportWidth.isNaN()) defaultWidth.value * density else this.viewportWidth
    val viewportHeight = if (this.viewportHeight.isNaN()) defaultHeight.value * density else this.viewportHeight
    if (!viewportWidth.isFinite() || !viewportHeight.isFinite() || viewportWidth <= 0f || viewportHeight <= 0f) return null
    val bitmap = ImageBitmap(width, height)
    val canvas = Canvas(bitmap)
    val size = Size(width.toFloat(), height.toFloat())
    CanvasDrawScope().draw(Density(density), layoutDirection, canvas, size) {
        if (tintColor.isSpecified) {
            canvas.saveLayer(Rect(Offset.Zero, size), Paint().apply { colorFilter = ColorFilter.tint(tintColor, tintBlendMode) })
        } else {
            canvas.save()
        }
        try {
            withTransform({
                if (autoMirror && layoutDirection == LayoutDirection.Rtl) {
                    translate(size.width, 0f)
                    scale(-1f, 1f, Offset.Zero)
                }
                scale(size.width / viewportWidth, size.height / viewportHeight, Offset.Zero)
            }) {
                drawVectorGroup(root)
            }
        } finally {
            canvas.restore()
        }
    }
    return bitmap
}

internal fun validRasterSize(width: Int, height: Int): Boolean =
    width > 0 && height > 0 && width.toLong() * height.toLong() <= Int.MAX_VALUE / 4

private fun DrawScope.drawVectorGroup(group: VectorGroup) {
    withTransform({
        translate(group.translationX + group.pivotX, group.translationY + group.pivotY)
        rotate(group.rotation, Offset.Zero)
        scale(group.scaleX, group.scaleY, Offset.Zero)
        translate(-group.pivotX, -group.pivotY)
        if (group.clipPathData.isNotEmpty()) clipPath(group.clipPathData.toPath())
    }) {
        for (node in group) {
            when (node) {
                is VectorGroup -> drawVectorGroup(node)
                is VectorPath -> drawVectorPath(node)
            }
        }
    }
}

private fun DrawScope.drawVectorPath(node: VectorPath) {
    val source = node.pathData.toPath().apply { fillType = node.pathFillType }
    val path = if (node.trimPathStart == 0f && node.trimPathEnd == 1f) source else {
        val measure = PathMeasure().apply { setPath(source, false) }
        val start = positiveFraction(node.trimPathStart + node.trimPathOffset) * measure.length
        val end = positiveFraction(node.trimPathEnd + node.trimPathOffset) * measure.length
        Path().apply {
            fillType = node.pathFillType
            if (start > end) {
                measure.getSegment(start, measure.length, this, true)
                measure.getSegment(0f, end, this, true)
            } else {
                measure.getSegment(start, end, this, true)
            }
        }
    }
    node.fill?.let { drawPath(path, it, alpha = node.fillAlpha) }
    node.stroke?.let {
        drawPath(path, it, alpha = node.strokeAlpha, style = Stroke(
            width = node.strokeLineWidth, miter = node.strokeLineMiter,
            cap = node.strokeLineCap, join = node.strokeLineJoin,
        ))
    }
}

private fun positiveFraction(value: Float): Float = ((value % 1f) + 1f) % 1f
