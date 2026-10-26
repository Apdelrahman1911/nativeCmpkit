// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.utils

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.spring
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.PointerInputChange
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.util.VelocityTracker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.time.TimeSource

/**
 * Visual drag animation with two owned job lanes (value and press feedback).
 *
 * The caller owns [animationScope]. [cancel] cancels only this helper's work. The modifier observes
 * a press immediately for visual feedback; controls must arbitrate their own tap/drag gestures.
 * Cancellation is never forwarded to [onDragStopped].
 */
class DampedDragAnimation(
    private val animationScope: CoroutineScope,
    val initialValue: Float,
    val valueRange: ClosedRange<Float>,
    val visibilityThreshold: Float,
    val initialScale: Float,
    val pressedScale: Float,
    val onDragStarted: DampedDragAnimation.(position: Offset) -> Unit,
    val onDragStopped: DampedDragAnimation.() -> Unit,
    val onDrag: DampedDragAnimation.(change: PointerInputChange, dragAmount: Offset) -> Unit,
) {
    init {
        require(valueRange.start.isFinite() && valueRange.endInclusive.isFinite()) { "Range endpoints must be finite" }
        require(valueRange.start <= valueRange.endInclusive) { "Range must not be reversed" }
        require(initialValue.isFinite()) { "Initial value must be finite" }
        require(visibilityThreshold.isFinite() && visibilityThreshold > 0f) { "Visibility threshold must be positive and finite" }
        require(initialScale.isFinite() && initialScale > 0f && pressedScale.isFinite() && pressedScale > 0f) {
            "Scales must be positive and finite"
        }
    }

    private val span = valueRange.endInclusive.toDouble() - valueRange.start.toDouble()
    private val normalizedThreshold = if (span == 0.0) .001f
    else (visibilityThreshold / span).toFloat().coerceIn(Float.MIN_VALUE, 1f)
    private val valueAnimationSpec = spring(1f, 1_000f, normalizedThreshold)
    private val pressProgressAnimationSpec = spring(1f, 1_000f, .001f)
    private val scaleXAnimationSpec = spring(.6f, 250f, .001f)
    private val scaleYAnimationSpec = spring(.7f, 250f, .001f)
    private val valueAnimation = Animatable(normalize(initialValue), normalizedThreshold)
    private val pressProgressAnimation = Animatable(0f, .001f)
    private val scaleXAnimation = Animatable(initialScale, .001f)
    private val scaleYAnimation = Animatable(initialScale, .001f)
    private val velocityTracker = VelocityTracker()
    private val timeOrigin = TimeSource.Monotonic.markNow()
    private var valueJob: Job? = null
    private var feedbackJob: Job? = null
    private var programmaticAnimation = false
    private var pressed by mutableStateOf(false)
    private var requestedValue by mutableFloatStateOf(initialValue.coerceIn(valueRange))
    private var measuredVelocity by mutableFloatStateOf(0f)

    val value: Float get() = (valueRange.start.toDouble() + span * progress).toFloat().coerceIn(valueRange)
    val progress: Float get() = valueAnimation.value.coerceIn(0f, 1f)
    val targetValue: Float get() = requestedValue
    val pressProgress: Float get() = pressProgressAnimation.value
    val scaleX: Float get() = scaleXAnimation.value
    val scaleY: Float get() = scaleYAnimation.value
    val velocity: Float get() = if (pressed) measuredVelocity else 0f

    internal val activeOwnedJobCount: Int get() = listOf(valueJob, feedbackJob).count { it?.isActive == true }

    val modifier: Modifier = Modifier.pointerInput(this) {
        var active = false
        try {
            inspectDragGestures(
                onDragStart = { down ->
                    active = true
                    onDragStarted(down.position)
                    press()
                },
                onDragEnd = {
                    active = false
                    try { onDragStopped() } finally { release() }
                },
                onDragCancel = {
                    active = false
                    release()
                },
                onDrag = { change, amount -> onDrag(change, amount) },
            )
        } finally {
            if (active) release()
        }
    }

    fun press() {
        feedbackJob?.cancel()
        if (programmaticAnimation) valueJob?.cancel()
        programmaticAnimation = false
        pressed = true
        measuredVelocity = 0f
        velocityTracker.resetTracking()
        feedbackJob = animationScope.launch(start = CoroutineStart.UNDISPATCHED) {
            launch { pressProgressAnimation.animateTo(1f, pressProgressAnimationSpec) }
            launch { scaleXAnimation.animateTo(pressedScale, scaleXAnimationSpec) }
            launch { scaleYAnimation.animateTo(pressedScale, scaleYAnimationSpec) }
        }
    }

    fun release() {
        feedbackJob?.cancel()
        pressed = false
        measuredVelocity = 0f
        feedbackJob = animationScope.launch {
            // A new press cancels this delay and all three children together.
            delay(1_000L / 60L)
            launch { pressProgressAnimation.animateTo(0f, pressProgressAnimationSpec) }
            launch { scaleXAnimation.animateTo(initialScale, scaleXAnimationSpec) }
            launch { scaleYAnimation.animateTo(initialScale, scaleYAnimationSpec) }
        }
    }

    fun updateValue(value: Float) = startValueAnimation(value, releaseWhenFinished = false)

    fun animateToValue(value: Float) {
        require(value.isFinite()) { "Value must be finite" }
        press()
        startValueAnimation(value, releaseWhenFinished = true)
    }

    /** Cancels owned animation jobs without cancelling the caller's scope or committing a gesture. */
    fun cancel() {
        valueJob?.cancel()
        feedbackJob?.cancel()
        programmaticAnimation = false
        pressed = false
        measuredVelocity = 0f
    }

    private fun startValueAnimation(value: Float, releaseWhenFinished: Boolean) {
        require(value.isFinite()) { "Value must be finite" }
        val target = value.coerceIn(valueRange)
        valueJob?.cancel()
        requestedValue = target
        programmaticAnimation = releaseWhenFinished
        valueJob = animationScope.launch(start = CoroutineStart.UNDISPATCHED) {
            valueAnimation.animateTo(normalize(target), valueAnimationSpec) { updateVelocity() }
            measuredVelocity = 0f
            if (releaseWhenFinished) {
                programmaticAnimation = false
                release()
            }
        }
    }

    private fun normalize(value: Float): Float = if (span == 0.0) 0f
    else ((value.coerceIn(valueRange).toDouble() - valueRange.start.toDouble()) / span).toFloat()

    private fun updateVelocity() {
        if (!pressed || span == 0.0) {
            measuredVelocity = 0f
            return
        }
        // Normalize positions before tracking, avoiding overflow for wide but finite Float ranges.
        velocityTracker.addPosition(timeOrigin.elapsedNow().inWholeMilliseconds, Offset(progress, 0f))
        measuredVelocity = velocityTracker.calculateVelocity().x.let { if (it.isFinite()) it else 0f }
        // No coroutine or animation is launched from this per-frame callback.
    }
}
