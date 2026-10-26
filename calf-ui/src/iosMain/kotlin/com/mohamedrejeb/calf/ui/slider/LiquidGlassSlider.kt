// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.slider

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsDraggedAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.util.lerp
import com.kyant.backdrop.backdrops.layerBackdrop
import com.kyant.backdrop.backdrops.rememberBackdrop
import com.kyant.backdrop.backdrops.rememberCombinedBackdrop
import com.kyant.backdrop.backdrops.rememberLayerBackdrop
import com.kyant.backdrop.drawBackdrop
import com.kyant.backdrop.effects.blur
import com.kyant.backdrop.effects.lens
import com.kyant.backdrop.highlight.Highlight
import com.kyant.backdrop.shadow.InnerShadow
import com.kyant.backdrop.shadow.Shadow
import com.kyant.shapes.Capsule
import com.mohamedrejeb.calf.ui.ExperimentalCalfUiApi
import com.mohamedrejeb.calf.ui.utils.LocalBackdrop

/**
 * Controlled Liquid Glass slider. Values must be finite; out-of-range values are clamped.
 * A constant range is inert. Pointer cancellation never calls [onValueChangeFinished].
 * The full track supports touch, keyboard focus and adjustable accessibility semantics.
 */
@ExperimentalCalfUiApi
@Composable
fun LiquidGlassSlider(
    value: Float,
    onValueChange: (Float) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    valueRange: ClosedFloatingPointRange<Float> = 0f..1f,
    onValueChangeFinished: (() -> Unit)? = null,
    colors: LiquidGlassSliderColors = LiquidGlassSliderDefaults.colors(),
    interactionSource: MutableInteractionSource = remember { MutableInteractionSource() },
) = LiquidGlassSliderImpl(
    value, onValueChange, modifier, enabled, valueRange, 0, onValueChangeFinished, colors, interactionSource,
)

/** Keeps the existing public signature while the adaptive API forwards its existing steps argument. */
@Composable
internal fun LiquidGlassSliderImpl(
    value: Float,
    onValueChange: (Float) -> Unit,
    modifier: Modifier,
    enabled: Boolean,
    valueRange: ClosedFloatingPointRange<Float>,
    steps: Int,
    onValueChangeFinished: (() -> Unit)?,
    colors: LiquidGlassSliderColors,
    interactionSource: MutableInteractionSource,
    disabledAlpha: Float = LiquidGlassSliderDefaults.DisabledAlpha,
    activeTickColor: Color = colors.thumbColor,
    inactiveTickColor: Color = colors.thumbColor,
) {
    val backdrop = LocalBackdrop.current ?: rememberLayerBackdrop()
    val trackBackdrop = rememberLayerBackdrop()
    val domain = remember(valueRange, steps) { SliderValueDomain(valueRange, steps) }
    val fraction = domain.fraction(value)
    val ticks = remember(steps) { sliderTickFractions(steps) }
    val pressed by interactionSource.collectIsPressedAsState()
    val dragged by interactionSource.collectIsDraggedAsState()
    val active = enabled && (pressed || dragged)
    val pressProgress by animateFloatAsState(if (active) 1f else 0f, spring(1f, 1_000f))
    val thumbScale by animateFloatAsState(
        if (active) LiquidGlassSliderDefaults.PressedScale else 1f, spring(.7f, 250f)
    )

    SliderLayout(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier.graphicsLayer { alpha = if (enabled) 1f else disabledAlpha },
        enabled = enabled,
        valueRange = valueRange,
        steps = steps,
        onValueChangeFinished = onValueChangeFinished,
        interactionSource = interactionSource,
        track = {
            Canvas(Modifier.layerBackdrop(trackBackdrop).clip(Capsule()).fillMaxWidth().height(LiquidGlassSliderDefaults.TrackHeight)) {
                val corner = CornerRadius(size.height / 2f)
                drawRoundRect(colors.trackColor, cornerRadius = corner)
                val activeWidth = size.width * fraction
                if (activeWidth > 0f) {
                    drawRoundRect(
                        colors.activeTrackColor,
                        topLeft = Offset(if (layoutDirection == LayoutDirection.Rtl) size.width - activeWidth else 0f, 0f),
                        size = Size(activeWidth, size.height), cornerRadius = corner,
                    )
                }
                for (tick in ticks) {
                    val x = size.width * if (layoutDirection == LayoutDirection.Rtl) 1f - tick else tick
                    drawCircle(
                        if (tick <= fraction) activeTickColor else inactiveTickColor,
                        radius = 1.dp.toPx(), center = Offset(x, center.y),
                    )
                }
            }
        },
        thumb = {
            Box(
                Modifier.drawBackdrop(
                    backdrop = rememberCombinedBackdrop(
                        backdrop,
                        rememberBackdrop(trackBackdrop) { drawBackdrop ->
                            scale(lerp(2f / 3f, 1f, pressProgress), pressProgress) { drawBackdrop() }
                        }
                    ),
                    shape = { Capsule() },
                    effects = {
                        blur(8.dp.toPx() * (1f - pressProgress))
                        lens(10.dp.toPx() * pressProgress, 14.dp.toPx() * pressProgress, chromaticAberration = true)
                    },
                    highlight = {
                        Highlight.Ambient.copy(
                            width = Highlight.Ambient.width / 1.5f,
                            blurRadius = Highlight.Ambient.blurRadius / 1.5f,
                            alpha = pressProgress,
                        )
                    },
                    shadow = { Shadow(radius = 4.dp, color = Color.Black.copy(alpha = .05f)) },
                    innerShadow = { InnerShadow(radius = 4.dp * pressProgress, alpha = pressProgress) },
                    layerBlock = { scaleX = thumbScale; scaleY = thumbScale },
                    onDrawSurface = { drawRect(colors.thumbColor.copy(alpha = colors.thumbColor.alpha * (1f - pressProgress))) },
                ).size(LiquidGlassSliderDefaults.ThumbWidth, LiquidGlassSliderDefaults.ThumbHeight)
            )
        },
    )
}

/**
 * Color configuration for [LiquidGlassSlider].
 */
@Immutable
class LiquidGlassSliderColors internal constructor(
    val thumbColor: Color,
    val activeTrackColor: Color,
    val trackColor: Color,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (other !is LiquidGlassSliderColors) return false
        if (thumbColor != other.thumbColor) return false
        if (activeTrackColor != other.activeTrackColor) return false
        if (trackColor != other.trackColor) return false
        return true
    }

    override fun hashCode(): Int {
        var result = thumbColor.hashCode()
        result = 31 * result + activeTrackColor.hashCode()
        result = 31 * result + trackColor.hashCode()
        return result
    }
}

/**
 * Defaults for [LiquidGlassSlider].
 *
 * Dimensions and colors match the reference LiquidSlider from AndroidLiquidGlass:
 * - 6dp track height
 * - 40x24dp capsule thumb
 * - Accent blue active track
 * - Translucent gray track background
 */
object LiquidGlassSliderDefaults {

    /** Track height, matching reference .height(6f.dp) */
    val TrackHeight = 6.dp

    /** Thumb width, matching reference .size(40f.dp, 24f.dp) */
    val ThumbWidth = 40.dp

    /** Thumb height, matching reference .size(40f.dp, 24f.dp) */
    val ThumbHeight = 24.dp

    /** Scale factor when thumb is pressed/dragged, matching reference pressedScale = 1.5f */
    const val PressedScale = 1.5f

    /** Opacity when disabled */
    const val DisabledAlpha = 0.4f

    /** iOS 26 accent blue for active track (light theme) */
    private val AccentColor = Color(0xFF0088FF)

    /** Translucent track background (light theme) */
    private val TrackColor = Color(0x33787878)

    /** Glass-like white thumb */
    private val ThumbColor = Color.White

    fun colors(
        thumbColor: Color = ThumbColor,
        activeTrackColor: Color = AccentColor,
        trackColor: Color = TrackColor,
    ): LiquidGlassSliderColors = LiquidGlassSliderColors(
        thumbColor = thumbColor,
        activeTrackColor = activeTrackColor,
        trackColor = trackColor,
    )
}
