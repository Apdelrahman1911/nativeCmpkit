// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.mohamedrejeb.calf.ui.sheet.AdaptiveSheetState.Companion.Saver
import kotlinx.coroutines.CancellationException

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun rememberAdaptiveSheetState(
    skipPartiallyExpanded: Boolean = false,
    confirmValueChange: (SheetValue) -> Boolean = { true },
): AdaptiveSheetState {
    val density = LocalDensity.current
    val currentConfirmValueChange = rememberUpdatedState(confirmValueChange)
    val currentDensity = rememberUpdatedState(density)

    val initialValue = SheetValue.Hidden
    val skipHiddenState = false
    val positionalThreshold = PositionalThreshold
    val velocityThreshold = VelocityThreshold


    val positionalThresholdToPx = { with(currentDensity.value) { positionalThreshold.toPx() } }
    val velocityThresholdToPx = { with(currentDensity.value) { velocityThreshold.toPx() } }
    val confirmLatestValue: (SheetValue) -> Boolean = { currentConfirmValueChange.value(it) }
    return rememberSaveable(
        skipPartiallyExpanded,
        skipHiddenState,
        saver =
            Saver(
                skipPartiallyExpanded = skipPartiallyExpanded,
                positionalThreshold = positionalThresholdToPx,
                velocityThreshold = velocityThresholdToPx,
                confirmValueChange = confirmLatestValue,
                skipHiddenState = skipHiddenState,
            ),
    ) {
        AdaptiveSheetState(
            skipPartiallyExpanded = skipPartiallyExpanded,
            confirmValueChange = confirmLatestValue,
            initialValue = initialValue,
            skipHiddenState = skipHiddenState,
            positionalThreshold = positionalThresholdToPx,
            velocityThreshold = velocityThresholdToPx,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Stable
expect class AdaptiveSheetState(
    skipPartiallyExpanded: Boolean = false,
    confirmValueChange: (SheetValue) -> Boolean = { true },
    initialValue: SheetValue = SheetValue.Hidden,
    skipHiddenState: Boolean = false,
    positionalThreshold: () -> Float,
    velocityThreshold: () -> Float,
) {
    val currentValue: SheetValue
    val targetValue: SheetValue
    val isVisible: Boolean

    /**
     * Expand the bottom sheet with animation and suspend until it is [PartiallyExpanded] if defined
     * else [Expanded].
     * @throws [CancellationException] if the animation is interrupted
     */
    suspend fun show()

    /**
     * Hide the bottom sheet with animation and suspend until it is fully hidden or animation has
     * been cancelled.
     * @throws [CancellationException] if the animation is interrupted
     */
    suspend fun hide()

    companion object {
        /**
         * The default [Saver] implementation for [AdaptiveSheetState].
         */
        fun Saver(
            skipPartiallyExpanded: Boolean,
            positionalThreshold: () -> Float,
            velocityThreshold: () -> Float,
            confirmValueChange: (SheetValue) -> Boolean,
            skipHiddenState: Boolean,
        ): Saver<AdaptiveSheetState, SheetValue>
    }
}

internal val PositionalThreshold = 56.dp

internal val VelocityThreshold = 125.dp
