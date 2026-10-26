package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.ui.Modifier
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.Constraints
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.constrainHeight
import androidx.compose.ui.unit.constrainWidth
import androidx.compose.ui.unit.dp
import kotlin.math.max
import kotlin.math.roundToInt

/** Bounded, RTL-aware geometry shared by the two iOS slider renderers. */
@Composable
internal fun SliderLayout(
    value: Float,
    onValueChange: (Float) -> Unit,
    modifier: Modifier,
    enabled: Boolean,
    valueRange: ClosedFloatingPointRange<Float>,
    steps: Int,
    onValueChangeFinished: (() -> Unit)?,
    interactionSource: MutableInteractionSource,
    thumb: @Composable () -> Unit,
    track: @Composable () -> Unit,
) {
    val domain = remember(valueRange, steps) { SliderValueDomain(valueRange, steps) }
    val fraction = domain.fraction(value)
    var measuredWidth by remember { mutableIntStateOf(0) }
    var measuredThumbWidth by remember { mutableIntStateOf(0) }
    val isRtl = LocalLayoutDirection.current == LayoutDirection.Rtl

    Layout(
        content = {
            Box { thumb() }
            Box { track() }
        },
        modifier = modifier
            .sizeIn(minWidth = 44.dp, minHeight = 44.dp)
            .sliderInput(
                value, onValueChange, onValueChangeFinished, enabled, valueRange, steps,
                interactionSource, measuredWidth, measuredThumbWidth, isRtl,
            ),
    ) { measurables, constraints ->
        // An unbounded parent (e.g. horizontal scrolling) must not become an Int.MAX_VALUE track.
        val width = if (constraints.hasBoundedWidth) constraints.maxWidth
        else constraints.constrainWidth(144.dp.roundToPx())
        val thumbPlaceable = measurables[0].measure(
            Constraints(maxWidth = width, maxHeight = constraints.maxHeight)
        )
        val trackWidth = (width - thumbPlaceable.width).coerceAtLeast(0)
        val trackPlaceable = measurables[1].measure(
            Constraints(minWidth = trackWidth, maxWidth = trackWidth, maxHeight = constraints.maxHeight)
        )
        val height = constraints.constrainHeight(max(thumbPlaceable.height, trackPlaceable.height))
        measuredWidth = width
        measuredThumbWidth = thumbPlaceable.width
        layout(width, height) {
            trackPlaceable.placeRelative(thumbPlaceable.width / 2, (height - trackPlaceable.height) / 2)
            thumbPlaceable.placeRelative((trackWidth * fraction).roundToInt(), (height - thumbPlaceable.height) / 2)
        }
    }
}
