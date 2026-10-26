package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.PermissionRequestOutcome

internal interface LocalNetworkProbe {
    fun start(onResult: (PermissionRequestOutcome) -> Unit)
    fun stop()
}

/** Production native ownership, with injected service/timer adapters for library tests. */
internal class LocalNetworkRequest(
    private val probe: LocalNetworkProbe,
    private val scheduleTimeout: (() -> Unit) -> (() -> Unit),
    private var onComplete: ((LocalNetworkRequest, PermissionRequestOutcome) -> Unit)?,
) {
    private var cancelTimeout: (() -> Unit)? = null
    private var finished = false
    private var started = false

    fun start() {
        if (started || finished) return
        started = true
        val cancel = scheduleTimeout { finish(PermissionRequestOutcome.TimedOut) }
        if (finished) { cancel(); return }
        cancelTimeout = cancel
        try { probe.start(::finish) } catch (error: Exception) {
            if (finished) throw error
            finish(PermissionRequestOutcome.Failed)
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
        val cancel = cancelTimeout
        cancelTimeout = null
        try { cancel?.invoke() } finally { probe.stop() }
    }
    fun cancel() {
        if (finished) return
        finished = true
        onComplete = null
        cleanup()
    }
}
