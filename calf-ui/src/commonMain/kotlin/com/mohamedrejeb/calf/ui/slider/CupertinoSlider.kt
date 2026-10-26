// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.hoverable
import androidx.compose.foundation.interaction.Interaction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.State
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.lerp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp

/**
 * A Cupertino-style slider for iOS < 26.
 *
 * Based on the compose-cupertino library implementation:
 * https://github.com/alexzhirkevich/compose-cupertino/blob/master/cupertino/src/commonMain/kotlin/io/github/alexzhirkevich/cupertino/CupertinoSlider.kt
 *
 * @param value current value of the slider. If outside of [valueRange] provided, value will be
 * coerced to this range.
 * @param onValueChange callback in which value should be updated
 * @param modifier the [Modifier] to be applied to this slider
 * @param enabled controls the enabled state of this slider.
 * @param valueRange range of values that this slider can take.
 * @param steps if greater than 0, specifies the amount of discrete allowable values.
 * @param onValueChangeFinished called when value change has ended.
 * @param colors [CupertinoSliderColors] that will be used to resolve the colors.
 * @param interactionSource the [MutableInteractionSource] representing the stream of [Interaction]s.
 */
@Composable
internal fun CupertinoSlider(
    value: Float,
    onValueChange: (Float) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    valueRange: ClosedFloatingPointRange<Float> = 0f..1f,
    steps: Int = 0,
    onValueChangeFinished: (() -> Unit)? = null,
    colors: CupertinoSliderColors = CupertinoSliderDefaults.colors(),
    interactionSource: MutableInteractionSource = remember { MutableInteractionSource() },
) {
    require(steps >= 0) { "steps should be >= 0" }

    CupertinoSliderImpl(
        modifier = modifier,
        enabled = enabled,
        interactionSource = interactionSource,
        onValueChange = onValueChange,
        onValueChangeFinished = onValueChangeFinished,
        steps = steps,
        value = value,
        valueRange = valueRange,
        thumb = {
            CupertinoSliderDefaults.Thumb(
                interactionSource = interactionSource,
                colors = colors,
                enabled = enabled,
            )
        },
        track = { sliderPositions ->
            CupertinoSliderDefaults.Track(
                colors = colors,
                enabled = enabled,
                sliderPositions = sliderPositions,
            )
        },
    )
}

// region Colors

/**
 * Represents the colors used by a [CupertinoSlider] in different states.
 */
@Immutable
internal class CupertinoSliderColors(
    private val thumbColor: Color,
    private val activeTrackColor: Color,
    private val activeTickColor: Color,
    private val inactiveTrackColor: Color,
    private val inactiveTickColor: Color,
    private val disabledThumbColor: Color,
    private val disabledActiveTrackColor: Color,
    private val disabledActiveTickColor: Color,
    private val disabledInactiveTrackColor: Color,
    private val disabledInactiveTickColor: Color,
) {
    @Composable
    internal fun thumbColor(enabled: Boolean): State<Color> =
        rememberUpdatedState(if (enabled) thumbColor else disabledThumbColor)

    @Composable
    internal fun trackColor(enabled: Boolean, active: Boolean): State<Color> =
        rememberUpdatedState(
            if (enabled) {
                if (active) activeTrackColor else inactiveTrackColor
            } else {
                if (active) disabledActiveTrackColor else disabledInactiveTrackColor
            }
        )

    @Composable
    internal fun tickColor(enabled: Boolean, active: Boolean): State<Color> =
        rememberUpdatedState(
            if (enabled) {
                if (active) activeTickColor else inactiveTickColor
            } else {
                if (active) disabledActiveTickColor else disabledInactiveTickColor
            }
        )

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is CupertinoSliderColors) return false
        if (thumbColor != other.thumbColor) return false
        if (activeTrackColor != other.activeTrackColor) return false
        if (activeTickColor != other.activeTickColor) return false
        if (inactiveTrackColor != other.inactiveTrackColor) return false
        if (inactiveTickColor != other.inactiveTickColor) return false
        if (disabledThumbColor != other.disabledThumbColor) return false
        if (disabledActiveTrackColor != other.disabledActiveTrackColor) return false
        if (disabledActiveTickColor != other.disabledActiveTickColor) return false
        if (disabledInactiveTrackColor != other.disabledInactiveTrackColor) return false
        if (disabledInactiveTickColor != other.disabledInactiveTickColor) return false
        return true
    }

    override fun hashCode(): Int {
        var result = thumbColor.hashCode()
        result = 31 * result + activeTrackColor.hashCode()
        result = 31 * result + activeTickColor.hashCode()
        result = 31 * result + inactiveTrackColor.hashCode()
        result = 31 * result + inactiveTickColor.hashCode()
        result = 31 * result + disabledThumbColor.hashCode()
        result = 31 * result + disabledActiveTrackColor.hashCode()
        result = 31 * result + disabledActiveTickColor.hashCode()
        result = 31 * result + disabledInactiveTrackColor.hashCode()
        result = 31 * result + disabledInactiveTickColor.hashCode()
        return result
    }
}

// endregion

// region Defaults

/**
 * Defaults for the Cupertino slider.
 */
internal object CupertinoSliderDefaults {

    /**
     * Creates a [CupertinoSliderColors] with default iOS-style colors.
     */
    fun colors(
        thumbColor: Color = Color.White,
        activeTrackColor: Color = CupertinoAccentBlue,
        activeTickColor: Color = CupertinoSeparator,
        inactiveTrackColor: Color = CupertinoSeparator,
        inactiveTickColor: Color = activeTickColor,
        disabledThumbColor: Color = thumbColor,
        disabledActiveTrackColor: Color = activeTrackColor.copy(alpha = 0.5f),
        disabledActiveTickColor: Color = activeTickColor,
        disabledInactiveTrackColor: Color = inactiveTrackColor.copy(alpha = 0.5f),
        disabledInactiveTickColor: Color = activeTickColor,
    ): CupertinoSliderColors = CupertinoSliderColors(
        thumbColor = thumbColor,
        activeTrackColor = activeTrackColor,
        activeTickColor = activeTickColor,
        inactiveTrackColor = inactiveTrackColor,
        inactiveTickColor = inactiveTickColor,
        disabledThumbColor = disabledThumbColor,
        disabledActiveTrackColor = disabledActiveTrackColor,
        disabledActiveTickColor = disabledActiveTickColor,
        disabledInactiveTrackColor = disabledInactiveTrackColor,
        disabledInactiveTickColor = disabledInactiveTickColor,
    )

    /**
     * The default thumb for [CupertinoSlider].
     */
    @Composable
    fun Thumb(
        interactionSource: MutableInteractionSource,
        modifier: Modifier = Modifier,
        colors: CupertinoSliderColors = colors(),
        enabled: Boolean = true,
        thumbSize: DpSize = ThumbSize,
    ) {
        val shape = CircleShape
        Spacer(
            modifier
                .size(thumbSize)
                .hoverable(interactionSource = interactionSource)
                .shadow(if (enabled) ThumbElevation else 0.dp, shape, clip = false)
                .background(colors.thumbColor(enabled).value, shape)
        )
    }

    /**
     * The default track for [CupertinoSlider].
     */
    @Composable
    fun Track(
        sliderPositions: CupertinoSliderPositions,
        modifier: Modifier = Modifier,
        colors: CupertinoSliderColors = colors(),
        enabled: Boolean = true,
    ) {
        val inactiveTrackColor = colors.trackColor(enabled, active = false)
        val activeTrackColor = colors.trackColor(enabled, active = true)
        val inactiveTickColor = colors.tickColor(enabled, active = false)
        val activeTickColor = colors.tickColor(enabled, active = true)
        Canvas(
            modifier
                .fillMaxWidth()
                .height(TrackHeight)
        ) {
            val isRtl = layoutDirection == LayoutDirection.Rtl
            val sliderLeft = Offset(0f, center.y)
            val sliderRight = Offset(size.width, center.y)
            val sliderStart = if (isRtl) sliderRight else sliderLeft
            val sliderEnd = if (isRtl) sliderLeft else sliderRight
            val tickSize = TickSize.toPx()
            val trackStrokeWidth = TrackHeight.toPx()

            drawLine(
                color = inactiveTrackColor.value,
                start = sliderStart,
                end = sliderEnd,
                strokeWidth = trackStrokeWidth,
                cap = StrokeCap.Round,
            )

            val sliderValueEnd = Offset(
                sliderStart.x +
                    (sliderEnd.x - sliderStart.x) * sliderPositions.activeRange.endInclusive,
                center.y,
            )
            val sliderValueStart = Offset(
                sliderStart.x +
                    (sliderEnd.x - sliderStart.x) * sliderPositions.activeRange.start,
                center.y,
            )

            drawLine(
                color = activeTrackColor.value,
                start = sliderValueStart,
                end = sliderValueEnd,
                strokeWidth = trackStrokeWidth,
                cap = StrokeCap.Round,
            )

            sliderPositions.tickFractions.forEach { fraction ->
                val active = fraction in sliderPositions.activeRange
                drawLine(
                    color = (if (active) activeTickColor else inactiveTickColor).value,
                    start = Offset(lerp(sliderStart, sliderEnd, fraction).x, center.y - 2.dp.toPx()),
                    end = Offset(lerp(sliderStart, sliderEnd, fraction).x, center.y + 2.dp.toPx()),
                    strokeWidth = tickSize,
                    cap = StrokeCap.Square,
                )
            }
        }
    }
}

// iOS-style colors
private val CupertinoAccentBlue = Color(0xFF007AFF)
private val CupertinoSeparator = Color(0x4D3C3C43)

// endregion

// region Tokens & dimensions

private val ThumbElevation = 8.dp
private val TrackHeight = 4.0.dp
private val TickSize = 3.0.dp

private val ThumbWidth = 26.dp
private val ThumbHeight = 26.dp
private val ThumbSize = DpSize(ThumbWidth, ThumbHeight)


// endregion

// region SliderPositions

/**
 * Class that holds information about [CupertinoSlider]'s active track
 * and fractional positions where the discrete ticks should be drawn on the track.
 */
@Stable
internal class CupertinoSliderPositions(
    initialActiveRange: ClosedFloatingPointRange<Float> = 0f..1f,
    initialTickFractions: FloatArray = floatArrayOf(),
) {
    var activeRange: ClosedFloatingPointRange<Float> by mutableStateOf(initialActiveRange)
        internal set

    var tickFractions: FloatArray by mutableStateOf(initialTickFractions)
        internal set

    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is CupertinoSliderPositions) return false
        if (activeRange != other.activeRange) return false
        if (!tickFractions.contentEquals(other.tickFractions)) return false
        return true
    }

    override fun hashCode(): Int {
        var result = activeRange.hashCode()
        result = 31 * result + tickFractions.contentHashCode()
        return result
    }
}

// endregion

// region SliderImpl

@Composable
private fun CupertinoSliderImpl(
    modifier: Modifier,
    enabled: Boolean,
    interactionSource: MutableInteractionSource,
    onValueChange: (Float) -> Unit,
    onValueChangeFinished: (() -> Unit)?,
    steps: Int,
    value: Float,
    valueRange: ClosedFloatingPointRange<Float>,
    thumb: @Composable (CupertinoSliderPositions) -> Unit,
    track: @Composable (CupertinoSliderPositions) -> Unit,
) {
    val domain = remember(valueRange, steps) { SliderValueDomain(valueRange, steps) }
    val ticks = remember(steps) { sliderTickFractions(steps) }
    val positions = remember { CupertinoSliderPositions() }
    positions.activeRange = 0f..domain.fraction(value)
    positions.tickFractions = ticks
    SliderLayout(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier,
        enabled = enabled,
        valueRange = valueRange,
        steps = steps,
        onValueChangeFinished = onValueChangeFinished,
        interactionSource = interactionSource,
        thumb = { thumb(positions) },
        track = { track(positions) },
    )
}

// endregion
