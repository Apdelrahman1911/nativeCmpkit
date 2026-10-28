@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

/** Callback APIs may answer on any queue; this owner serializes observations on its dispatcher. */
internal interface PermissionBackend {
    fun query(callback: (PermissionSnapshot) -> Unit)
    fun request(callback: (Boolean) -> Unit)
    fun onRefresh() = Unit
    fun openSettings() = Unit
    fun dispose() = Unit
}

/** Production iOS state controller, injectable for deterministic library-level ownership tests. */
internal class CallbackPermissionState(
    override val permission: Permission,
    private val onResult: (Boolean) -> Unit,
    scope: CoroutineScope,
    private val dispatcher: CoroutineDispatcher,
    private val backendFactory: () -> PermissionBackend,
) : MutablePermissionState, PermissionDetailsProvider {
    // Composition cancellation still cancels our work. A user callback failure,
    // however, must surface through its inherited exception handler without
    // cancelling the remembered composition scope or all subsequent requests.
    private val operationJob = SupervisorJob(scope.coroutineContext[Job])
    private val operationScope = CoroutineScope(scope.coroutineContext + operationJob)
    override var status: PermissionStatus by mutableStateOf(PermissionStatus.Denied(false))
    override var permissionDetails: PermissionDetails by mutableStateOf(PermissionDetails())
        private set
    private var backend: PermissionBackend? = null
    private fun backend() = backend ?: backendFactory().also { backend = it }
    private var disposed = false
    private var observation = 0L
    private val gate = PermissionRequestGate<Boolean>()

    init { refreshPermissionStatus() }

    override fun refreshPermissionStatus() {
        operationScope.launch(dispatcher) {
            if (disposed || gate.isActive) return@launch
            val version = ++observation
            try {
                backend().onRefresh()
                var answered = false
                backend().query { snapshot ->
                    operationScope.launch(dispatcher) {
                        if (!disposed && !answered && observation == version) {
                            answered = true
                            apply(snapshot)
                        }
                    }
                }
            } catch (_: Exception) {
                if (!disposed && observation == version) recordFailure()
            }
        }
    }

    override fun launchPermissionRequest() = request(onResult)

    internal fun request(callback: (Boolean) -> Unit) {
        operationScope.launch(dispatcher) {
            if (disposed) return@launch
            val token = gate.begin(callback) ?: return@launch
            ++observation // Older asynchronous status reads cannot overwrite the result.
            var answered = false
            try {
                backend().request { granted ->
                    operationScope.launch(dispatcher) result@ {
                        if (!gate.isCurrent(token) || answered) return@result
                        answered = true
                        observeRequestResult(token, granted)
                    }
                }
            } catch (error: Exception) {
                if (!gate.isCurrent(token)) throw error // Never disguise an application callback exception.
                recordFailure()
                gate.complete(token, false)
            }
        }
    }

    private fun observeRequestResult(token: Long, granted: Boolean) {
        try {
            backend().query { snapshot ->
                operationScope.launch(dispatcher) {
                    if (gate.isCurrent(token)) {
                        val success = granted && snapshot.status.isGranted
                        apply(snapshot.copy(details = snapshot.details.copy(
                            lastRequest = snapshot.details.lastRequest ?: when {
                                snapshot.details.availability == PermissionAvailability.NotRequired -> PermissionRequestOutcome.NotRequired
                                snapshot.details.availability == PermissionAvailability.Unsupported -> PermissionRequestOutcome.Unsupported
                                success -> PermissionRequestOutcome.Granted
                                snapshot.details.requestability == PermissionRequestability.Restricted -> PermissionRequestOutcome.Restricted
                                snapshot.details.requestability == PermissionRequestability.SettingsOnly -> PermissionRequestOutcome.RequiresSettings
                                snapshot.details.requestability == PermissionRequestability.PrerequisiteRequired -> PermissionRequestOutcome.RequiresForeground
                                else -> PermissionRequestOutcome.Denied
                            },
                        )))
                        gate.complete(token, success)
                    }
                }
            }
        } catch (error: Exception) {
            if (!gate.isCurrent(token)) throw error
            recordFailure()
            gate.complete(token, false)
        }
    }

    private fun recordFailure() {
        status = PermissionStatus.Denied(false)
        permissionDetails = PermissionDetails(lastRequest = PermissionRequestOutcome.Failed)
    }

    override fun openAppSettings() {
        operationScope.launch(dispatcher) { if (!disposed) backend().openSettings() }
    }

    private fun apply(snapshot: PermissionSnapshot) {
        status = snapshot.status
        permissionDetails = snapshot.details.copy(lastRequest = snapshot.details.lastRequest ?: permissionDetails.lastRequest)
    }

    /** Called by composition disposal on the owning/main thread, even if its scope is cancelled. */
    internal fun dispose() {
        if (disposed) return
        disposed = true
        ++observation
        gate.dispose()
        val owned = backend
        backend = null
        try { owned?.dispose() } finally { operationJob.cancel() }
    }
}
