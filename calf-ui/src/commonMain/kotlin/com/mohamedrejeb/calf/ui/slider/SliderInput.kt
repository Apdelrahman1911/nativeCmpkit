package com.mohamedrejeb.calf.ui.slider

import androidx.compose.foundation.focusable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.interaction.DragInteraction
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.PressInteraction
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.disabled
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.setProgress

/**
 * Input only: the existing Cupertino and glass renderers remain independent of it.
 *
 * A tap is an atomic request, never an animation that writes into caller state. A horizontal drag
 * waits for Foundation's touch slop; cancellation emits Cancel, not a completion callback. Changes
 * to the contract/geometry/source cancel the old gesture, while callback/value changes stay fresh.
 */
@Composable
internal fun Modifier.sliderInput(
    value: Float,
    onValueChange: (Float) -> Unit,
    onValueChangeFinished: (() -> Unit)?,
    enabled: Boolean,
    valueRange: ClosedFloatingPointRange<Float>,
    steps: Int,
    interactionSource: MutableInteractionSource,
    width: Int,
    thumbWidth: Int,
    isRtl: Boolean,
): Modifier {
    val domain = remember(valueRange, steps) { SliderValueDomain(valueRange, steps) }
    val currentValue by rememberUpdatedState(domain.coerce(value))
    val change by rememberUpdatedState(onValueChange)
    val finished by rememberUpdatedState(onValueChangeFinished)
    val interactive = enabled && !domain.isConstant
    val currentInteractive by rememberUpdatedState(interactive)

    fun request(target: Float): Boolean {
        if (!currentInteractive || !target.isFinite()) return false
        val next = domain.snap(target)
        if (next == currentValue) return false
        change(next)
        return true
    }

    val keyboard = remember(domain, interactive, isRtl, interactionSource) { SliderKeyboardGesture() }
    return this
        .semantics {
            progressBarRangeInfo = ProgressBarRangeInfo(currentValue, valueRange, steps)
            if (!enabled) disabled()
            setProgress { target ->
                request(target).also { changed -> if (changed) finished?.invoke() }
            }
        }
        .onKeyEvent { event ->
            if (!currentInteractive) return@onKeyEvent false
            val target = when (event.key) {
                Key.DirectionRight -> domain.keyboardValue(currentValue, if (isRtl) -1 else 1)
                Key.DirectionLeft -> domain.keyboardValue(currentValue, if (isRtl) 1 else -1)
                Key.DirectionUp -> domain.keyboardValue(currentValue, 1)
                Key.DirectionDown -> domain.keyboardValue(currentValue, -1)
                Key.MoveHome -> valueRange.start
                Key.MoveEnd -> valueRange.endInclusive
                Key.PageUp -> domain.keyboardValue(currentValue, 1, page = true)
                Key.PageDown -> domain.keyboardValue(currentValue, -1, page = true)
                else -> return@onKeyEvent false
            }
            when (event.type) {
                KeyEventType.KeyDown -> keyboard.changed = request(target) || keyboard.changed
                KeyEventType.KeyUp -> {
                    if (keyboard.changed) finished?.invoke()
                    keyboard.changed = false
                }
            }
            true
        }
        .onFocusChanged { if (!it.isFocused) keyboard.changed = false }
        .focusable(enabled, interactionSource)
        .pointerInput(interactive, domain, width, thumbWidth, isRtl, interactionSource) {
            if (!interactive || width <= thumbWidth) return@pointerInput
            detectTapGestures(
                onPress = { offset ->
                    val press = PressInteraction.Press(offset)
                    interactionSource.emit(press)
                    var released = false
                    try {
                        released = tryAwaitRelease()
                    } finally {
                        // Also pairs the press when this pointer-input node is disposed/re-keyed.
                        interactionSource.tryEmit(
                            if (released) PressInteraction.Release(press) else PressInteraction.Cancel(press)
                        )
                    }
                },
                onTap = { offset ->
                    if (currentInteractive) {
                        request(domain.offsetValue(offset.x, width, thumbWidth, isRtl))
                        finished?.invoke()
                    }
                },
            )
        }
        .pointerInput(interactive, domain, width, thumbWidth, isRtl, interactionSource) {
            if (!interactive || width <= thumbWidth) return@pointerInput
            var drag: DragInteraction.Start? = null
            var lastRequested = currentValue

            fun update(x: Float) {
                if (!currentInteractive) return
                val next = domain.offsetValue(x, width, thumbWidth, isRtl)
                if (next != lastRequested) {
                    lastRequested = next
                    change(next)
                }
            }

            try {
                detectHorizontalDragGestures(
                    onDragStart = { offset ->
                        lastRequested = currentValue
                        drag = DragInteraction.Start().also { interactionSource.tryEmit(it) }
                        update(offset.x)
                    },
                    onDragEnd = {
                        drag?.let { interactionSource.tryEmit(DragInteraction.Stop(it)) }
                        drag = null
                        if (currentInteractive) finished?.invoke()
                    },
                    onDragCancel = {
                        drag?.let { interactionSource.tryEmit(DragInteraction.Cancel(it)) }
                        drag = null
                    },
                    onHorizontalDrag = { change, _ ->
                        change.consume()
                        update(change.position.x)
                    },
                )
            } finally {
                drag?.let { interactionSource.tryEmit(DragInteraction.Cancel(it)) }
            }
        }
}

private class SliderKeyboardGesture(var changed: Boolean = false)
