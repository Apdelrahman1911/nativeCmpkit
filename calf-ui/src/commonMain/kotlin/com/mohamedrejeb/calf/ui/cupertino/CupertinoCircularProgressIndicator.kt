// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.cupertino

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.progressSemantics
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.unit.dp

/**
 * @param modifier indicator modifier
 * @param color color of the indicator
 * */
@Composable
fun CupertinoActivityIndicator(
    color: Color = Color.Gray,
    modifier: Modifier = Modifier,
) {
    // number of paths of the activity indicator
    val pathCount = 8
    // duration of a single animation cycle
    val durationMillis = 1000
    val infiniteTransition = rememberInfiniteTransition()
    val angle by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = pathCount.toFloat(),
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = durationMillis,
                easing = LinearEasing,
            ),
            repeatMode = RepeatMode.Restart,
        ),
    )

    Canvas(
        modifier = modifier
            .progressSemantics()
            .size(ActivityIndicatorDiameter),
    ) {
        drawCupertinoActivityIndicator(color, angle)
    }
}

/** Single draw per spoke: caller alpha is an opacity bound, not overwritten or accumulated twice. */
internal fun DrawScope.drawCupertinoActivityIndicator(color: Color, angle: Float) {
    val pathCount = 8
    val animatedPathCount = pathCount / 2
    val diameter = size.minDimension
    val itemWidth = diameter / 3f
    val itemHeight = diameter / pathCount
    val cornerRadius = itemWidth.coerceAtMost(itemHeight) / 2f
    val topLeft = Offset(
        (size.width - diameter) / 2f + diameter - itemWidth,
        (size.height - itemHeight) / 2f,
    )
    val head = angle.toInt() % pathCount
    for (spoke in 0 until pathCount) {
        val distance = (spoke - head + pathCount) % pathCount
        val intensity = if (distance in 1..animatedPathCount) distance.toFloat() / animatedPathCount else .1f
        rotate(spoke * 360f / pathCount) {
            drawRoundRect(
                color = color.copy(alpha = color.alpha * intensity),
                topLeft = topLeft,
                size = Size(itemWidth, itemHeight),
                cornerRadius = CornerRadius(cornerRadius, cornerRadius),
            )
        }
    }
}

internal val ActivityIndicatorDiameter =
    ActivityIndicatorTokens.Size - ActivityIndicatorTokens.ActiveIndicatorWidth * 2

internal object ActivityIndicatorTokens {
    val ActiveIndicatorWidth = 4.0.dp
    val Size = 38.0.dp
}
