// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.ui.sheet

import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.SheetValue
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.setValue
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

@OptIn(ExperimentalMaterial3Api::class)
@Stable
actual class AdaptiveSheetState actual constructor(
    internal val skipPartiallyExpanded: Boolean,
    internal val confirmValueChange: (SheetValue) -> Boolean,
    initialValue: SheetValue,
    internal val skipHiddenState: Boolean,
    positionalThreshold: () -> Float,
    velocityThreshold: () -> Float,
) {
    init {
        require(!skipPartiallyExpanded || initialValue != SheetValue.PartiallyExpanded) {
            "PartiallyExpanded initialValue is not permitted when skipPartiallyExpanded is true"
        }
        require(!skipHiddenState || initialValue != SheetValue.Hidden) {
            "Hidden initialValue is not permitted when skipHiddenState is true"
        }
    }

    internal var iosCurrentValue by mutableStateOf(initialValue)
    internal var iosTargetValue by mutableStateOf(initialValue)
    actual val currentValue: SheetValue get() = iosCurrentValue
    actual val targetValue: SheetValue get() = iosTargetValue
    actual val isVisible: Boolean get() = currentValue != SheetValue.Hidden
    internal var iosSheetManager: BottomSheetManager? = null
    internal var showDragHandle = true
    private val operations = Mutex()

    internal fun permits(value: SheetValue): Boolean =
        !(skipHiddenState && value == SheetValue.Hidden) &&
            !(skipPartiallyExpanded && value == SheetValue.PartiallyExpanded) && confirmValueChange(value)

    internal fun detach(manager: BottomSheetManager) {
        if (iosSheetManager !== manager) return
        iosSheetManager = null
        iosCurrentValue = SheetValue.Hidden
        iosTargetValue = SheetValue.Hidden
    }

    actual suspend fun show() = withContext(Dispatchers.Main.immediate) {
        operations.withLock {
            val manager = iosSheetManager ?: return@withLock
            val destination = if (currentValue != SheetValue.Hidden) currentValue else if (skipPartiallyExpanded)
                SheetValue.Expanded else SheetValue.PartiallyExpanded
            if (permits(destination)) manager.show(skipPartiallyExpanded, showDragHandle, destination)
        }
    }

    actual suspend fun hide() = withContext(Dispatchers.Main.immediate) {
        operations.withLock {
            check(!skipHiddenState) { "hide() is not permitted when skipHiddenState is true" }
            val manager = iosSheetManager ?: return@withLock
            if (permits(SheetValue.Hidden)) manager.hide()
        }
    }

    actual companion object {
        actual fun Saver(
            skipPartiallyExpanded: Boolean,
            positionalThreshold: () -> Float,
            velocityThreshold: () -> Float,
            confirmValueChange: (SheetValue) -> Boolean,
            skipHiddenState: Boolean,
        ) = Saver<AdaptiveSheetState, SheetValue>(
            save = { it.currentValue },
            restore = { AdaptiveSheetState(skipPartiallyExpanded, confirmValueChange, it, skipHiddenState,
                positionalThreshold, velocityThreshold) },
        )
    }
}
