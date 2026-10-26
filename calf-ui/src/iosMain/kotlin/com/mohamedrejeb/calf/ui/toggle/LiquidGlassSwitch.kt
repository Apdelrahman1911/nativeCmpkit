// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.toggle

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsDraggedAsState
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.sizeIn
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.toggleableState
import androidx.compose.ui.state.ToggleableState
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
 * Controlled glass switch. [checked] remains authoritative after a tap or drag proposal.
 * A null callback makes this read-only; cancellation never proposes a value. The whole track is
 * actionable and its semantics use ToggleableState rather than hard-coded English descriptions.
 */
@ExperimentalCalfUiApi
@Composable
fun LiquidGlassSwitch(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier = Modifier,
    thumbContent: @Composable (() -> Unit)? = null,
    enabled: Boolean = true,
    colors: LiquidGlassSwitchColors = LiquidGlassSwitchDefaults.colors(),
    interactionSource: MutableInteractionSource = remember { MutableInteractionSource() },
) = LiquidGlassSwitchImpl(checked, onCheckedChange, modifier, thumbContent, enabled, colors, interactionSource)

@Composable
internal fun LiquidGlassSwitchImpl(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier,
    thumbContent: @Composable (() -> Unit)?,
    enabled: Boolean,
    colors: LiquidGlassSwitchColors,
    interactionSource: MutableInteractionSource,
    disabledCheckedTrackBorderColor: Color = Color.Transparent,
    disabledUncheckedTrackBorderColor: Color = Color.Transparent,
) {
    val backdrop = LocalBackdrop.current ?: rememberLayerBackdrop()
    val trackBackdrop = rememberLayerBackdrop()
    val dragWidth = with(LocalDensity.current) { LiquidGlassSwitchDefaults.DragWidth.toPx() }
    val isLtr = LocalLayoutDirection.current == LayoutDirection.Ltr
    val interactive = enabled && onCheckedChange != null
    val currentChecked by rememberUpdatedState(checked)
    val currentCallback by rememberUpdatedState(onCheckedChange)
    val currentInteractive by rememberUpdatedState(interactive)
    // External changes cancel the preview immediately, even before a LaunchedEffect could run.
    val dragState = remember(checked, interactive, isLtr, dragWidth, interactionSource) { ControlledSwitchDragState() }
    val targetFraction = dragState.previewFraction ?: if (checked) 1f else 0f
    val fraction by animateFloatAsState(targetFraction, spring(1f, 1_000f))
    val pressed by interactionSource.collectIsPressedAsState()
    val dragged by interactionSource.collectIsDraggedAsState()
    val active = interactive && (pressed || dragged)
    val pressProgress by animateFloatAsState(if (active) 1f else 0f, spring(1f, 1_000f))
    val thumbScale by animateFloatAsState(if (active) 1.5f else 1f, spring(.7f, 250f))
    val trackColor = lerp(colors.trackColor(enabled, false), colors.trackColor(enabled, true), fraction)
    val thumbColor = lerp(colors.thumbColor(enabled, false), colors.thumbColor(enabled, true), fraction)
    val trackBorderColor = if (enabled) {
        lerp(colors.uncheckedTrackBorderColor, colors.checkedTrackBorderColor, fraction)
    } else {
        lerp(disabledUncheckedTrackBorderColor, disabledCheckedTrackBorderColor, fraction)
    }
    val thumbBorderColor = lerp(colors.thumbBorderColor(enabled, false), colors.thumbBorderColor(enabled, true), fraction)

    val toggle = if (onCheckedChange != null) {
        Modifier.toggleable(
            value = checked, enabled = enabled, role = Role.Switch,
            interactionSource = interactionSource, indication = null,
            onValueChange = { if (currentInteractive) currentCallback?.invoke(it) },
        )
    } else {
        Modifier.semantics {
            role = Role.Switch
            toggleableState = ToggleableState(checked)
            if (!enabled) disabled()
        }
    }

    Box(
        contentAlignment = Alignment.CenterStart,
        modifier = modifier
            .then(toggle)
            .pointerInput(interactive, dragState, interactionSource) {
                if (!interactive || dragWidth <= 0f) return@pointerInput
                var drag: DragInteraction.Start? = null
                try {
                    detectHorizontalDragGestures(
                        onDragStart = {
                            dragState.start(currentChecked)
                            drag = DragInteraction.Start().also { interactionSource.tryEmit(it) }
                        },
                        onDragEnd = {
                            val proposed = dragState.finish()
                            drag?.let { interactionSource.tryEmit(DragInteraction.Stop(it)) }
                            drag = null
                            if (currentInteractive && proposed != null && proposed != currentChecked) {
                                currentCallback?.invoke(proposed)
                            }
                        },
                        onDragCancel = {
                            dragState.cancel()
                            drag?.let { interactionSource.tryEmit(DragInteraction.Cancel(it)) }
                            drag = null
                        },
                        onHorizontalDrag = { change, delta ->
                            change.consume()
                            if (currentInteractive) dragState.dragBy(delta / dragWidth * if (isLtr) 1f else -1f)
                        },
                    )
                } finally {
                    dragState.cancel()
                    drag?.let { interactionSource.tryEmit(DragInteraction.Cancel(it)) }
                }
            }
            .sizeIn(minWidth = 44.dp, minHeight = 44.dp)
            .size(LiquidGlassSwitchDefaults.TrackWidth, 44.dp)
    ) {
        Box(
            Modifier.layerBackdrop(trackBackdrop)
                .clip(Capsule())
                .drawBehind { drawRect(trackColor) }
                .border(1.dp, trackBorderColor, Capsule())
                .size(LiquidGlassSwitchDefaults.TrackWidth, LiquidGlassSwitchDefaults.TrackHeight)
        )
        Box(
            contentAlignment = Alignment.Center,
            modifier = Modifier
                .graphicsLayer {
                    val padding = LiquidGlassSwitchDefaults.TrackPadding.toPx()
                    translationX = (padding + dragWidth * fraction) * if (isLtr) 1f else -1f
                }
                .drawBackdrop(
                    backdrop = rememberCombinedBackdrop(
                        backdrop,
                        rememberBackdrop(trackBackdrop) { drawBackdrop ->
                            scale(lerp(2f / 3f, .75f, pressProgress), .75f * pressProgress) { drawBackdrop() }
                        }
                    ),
                    shape = { Capsule() },
                    effects = {
                        blur(8.dp.toPx() * (1f - pressProgress))
                        lens(5.dp.toPx() * pressProgress, 10.dp.toPx() * pressProgress, chromaticAberration = true)
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
                    onDrawSurface = { drawRect(thumbColor.copy(alpha = thumbColor.alpha * (1f - pressProgress))) },
                )
                .border(1.dp, thumbBorderColor, Capsule())
                .size(LiquidGlassSwitchDefaults.ThumbWidth, LiquidGlassSwitchDefaults.ThumbHeight)
        ) { thumbContent?.invoke() }
    }
}

/**
 * Colors for [LiquidGlassSwitch].
 */
data class LiquidGlassSwitchColors(
    val checkedTrackColor: Color,
    val uncheckedTrackColor: Color,
    val checkedThumbColor: Color,
    val uncheckedThumbColor: Color,
    val checkedTrackBorderColor: Color,
    val uncheckedTrackBorderColor: Color,
    val checkedThumbBorderColor: Color,
    val uncheckedThumbBorderColor: Color,
    val disabledCheckedTrackColor: Color,
    val disabledUncheckedTrackColor: Color,
    val disabledCheckedThumbColor: Color,
    val disabledUncheckedThumbColor: Color,
)

@Stable
internal fun LiquidGlassSwitchColors.trackColor(enabled: Boolean, checked: Boolean): Color =
    if (enabled) {
        if (checked) checkedTrackColor else uncheckedTrackColor
    } else {
        if (checked) disabledCheckedTrackColor else disabledUncheckedTrackColor
    }

@Stable
internal fun LiquidGlassSwitchColors.thumbColor(enabled: Boolean, checked: Boolean): Color =
    if (enabled) {
        if (checked) checkedThumbColor else uncheckedThumbColor
    } else {
        if (checked) disabledCheckedThumbColor else disabledUncheckedThumbColor
    }

@Stable
internal fun LiquidGlassSwitchColors.trackBorderColor(enabled: Boolean, checked: Boolean): Color =
    if (enabled) {
        if (checked) checkedTrackBorderColor else uncheckedTrackBorderColor
    } else {
        Color.Transparent
    }

@Stable
internal fun LiquidGlassSwitchColors.thumbBorderColor(enabled: Boolean, checked: Boolean): Color =
    if (enabled) {
        if (checked) checkedThumbBorderColor else uncheckedThumbBorderColor
    } else {
        Color.Transparent
    }

/**
 * Defaults for [LiquidGlassSwitch].
 */
object LiquidGlassSwitchDefaults {

    val TrackWidth = 64.dp
    val TrackHeight = 28.dp
    val TrackShape = RoundedCornerShape(50)
    val TrackPadding = 2.dp

    val ThumbWidth = 40.dp
    val ThumbHeight = 24.dp

    /** Drag distance for the thumb (track - thumb - padding*2) */
    val DragWidth = 20.dp

    const val DisabledAlpha = 0.4f

    /** iOS 26 green accent for checked state */
    private val CheckedTrackColor = Color(0xFF34C759)

    /** Glass-like translucent track for unchecked state */
    private val UncheckedTrackColor = Color(0x33787878)

    /** Glass-like translucent white thumb */
    private val ThumbColor = Color(0xCCFFFFFF)

    /** Subtle glass border */
    private val GlassBorder = Color(0x50FFFFFF)

    /** Checked track border with slight green tint */
    private val CheckedTrackBorder = Color(0x3034C759)

    /** Unchecked track border */
    private val UncheckedTrackBorder = Color(0x40FFFFFF)

    /** Thumb border highlight */
    private val ThumbBorder = Color(0x60FFFFFF)

    fun colors(
        checkedTrackColor: Color = CheckedTrackColor,
        uncheckedTrackColor: Color = UncheckedTrackColor,
        checkedThumbColor: Color = ThumbColor,
        uncheckedThumbColor: Color = ThumbColor,
        checkedTrackBorderColor: Color = CheckedTrackBorder,
        uncheckedTrackBorderColor: Color = UncheckedTrackBorder,
        checkedThumbBorderColor: Color = ThumbBorder,
        uncheckedThumbBorderColor: Color = ThumbBorder,
        disabledCheckedTrackColor: Color = checkedTrackColor.copy(alpha = 0.3f),
        disabledUncheckedTrackColor: Color = uncheckedTrackColor.copy(alpha = 0.3f),
        disabledCheckedThumbColor: Color = checkedThumbColor.copy(alpha = 0.5f),
        disabledUncheckedThumbColor: Color = uncheckedThumbColor.copy(alpha = 0.5f),
    ): LiquidGlassSwitchColors = LiquidGlassSwitchColors(
        checkedTrackColor = checkedTrackColor,
        uncheckedTrackColor = uncheckedTrackColor,
        checkedThumbColor = checkedThumbColor,
        uncheckedThumbColor = uncheckedThumbColor,
        checkedTrackBorderColor = checkedTrackBorderColor,
        uncheckedTrackBorderColor = uncheckedTrackBorderColor,
        checkedThumbBorderColor = checkedThumbBorderColor,
        uncheckedThumbBorderColor = uncheckedThumbBorderColor,
        disabledCheckedTrackColor = disabledCheckedTrackColor,
        disabledUncheckedTrackColor = disabledUncheckedTrackColor,
        disabledCheckedThumbColor = disabledCheckedThumbColor,
        disabledUncheckedThumbColor = disabledUncheckedThumbColor,
    )
}
