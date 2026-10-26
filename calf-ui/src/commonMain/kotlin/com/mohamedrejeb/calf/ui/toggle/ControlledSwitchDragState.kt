package com.mohamedrejeb.calf.ui.toggle

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/** A drag preview, not another owner of the switch's checked value. */
internal class ControlledSwitchDragState {
    var previewFraction: Float? by mutableStateOf(null)
        private set

    fun start(checked: Boolean) {
        previewFraction = if (checked) 1f else 0f
    }

    fun dragBy(deltaFraction: Float) {
        if (!deltaFraction.isFinite()) return
        previewFraction = previewFraction?.let { (it + deltaFraction).coerceIn(0f, 1f) }
    }

    fun finish(): Boolean? {
        val result = previewFraction?.let { it >= .5f }
        previewFraction = null
        return result
    }

    fun cancel() {
        previewFraction = null
    }
}
