package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.PermissionRequestOutcome

internal interface BluetoothProbe {
    fun start(onChange: () -> Unit)
    fun stop()
}

/** Owns the strong delegate/manager adapter and both timers for one request only. */
internal class BluetoothRequest(
    private val probe: BluetoothProbe,
    private val authorization: () -> BluetoothAuthorization,
    private val schedule: (seconds: Double, repeats: Boolean, callback: () -> Unit) -> (() -> Unit),
    private var onComplete: ((BluetoothRequest, PermissionRequestOutcome) -> Unit)?,
) {
    private var cancelTimeout: (() -> Unit)? = null
    private var cancelPoll: (() -> Unit)? = null
    private var finished = false
    private var started = false

    fun start() {
        if (started || finished) return
        started = true
        val timeout = schedule(60.0, false) { finish(PermissionRequestOutcome.TimedOut) }
        if (finished) { timeout(); return }
        cancelTimeout = timeout
        val poll = schedule(0.5, true, ::checkAuthorization)
        if (finished) { poll(); return }
        cancelPoll = poll
        try {
            probe.start(::checkAuthorization)
            checkAuthorization()
        } catch (error: Exception) {
            if (finished) throw error
            finish(PermissionRequestOutcome.Failed)
        }
    }
    private fun checkAuthorization() {
        if (finished) return
        when (authorization()) {
            BluetoothAuthorization.Allowed -> finish(PermissionRequestOutcome.Granted)
            BluetoothAuthorization.Denied -> finish(PermissionRequestOutcome.Denied)
            BluetoothAuthorization.Restricted -> finish(PermissionRequestOutcome.Restricted)
            BluetoothAuthorization.Unsupported -> finish(PermissionRequestOutcome.Unsupported)
            else -> Unit
        }
    }
    private fun finish(outcome: PermissionRequestOutcome) {
        if (finished) return
        finished = true
        val callback = onComplete
        onComplete = null
        try { cleanup() } finally { callback?.invoke(this, outcome) }
    }
    private fun cleanup() {
        val poll = cancelPoll; cancelPoll = null
        val timeout = cancelTimeout; cancelTimeout = null
        try { poll?.invoke() } finally {
            try { timeout?.invoke() } finally { probe.stop() }
        }
    }
    fun cancel() {
        if (finished) return
        finished = true
        onComplete = null
        cleanup()
    }
}
