@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import kotlin.test.*

/** Real coroutine Job ownership around the production controller; the callback backend is controlled. */
class CallbackExceptionOwnershipTest {
    @Test fun aThrowingUserCallbackDoesNotCancelTheCompositionScopeOrBlockRecovery() = runTest {
        val compositionJob = Job()
        val errors = mutableListOf<Throwable>()
        val scope = CoroutineScope(compositionJob + StandardTestDispatcher(testScheduler) +
            CoroutineExceptionHandler { _, error -> errors += error })
        val callbackFailure = IllegalStateException("Deliberate application callback failure")
        val requests = mutableListOf<(Boolean) -> Unit>()
        var granted = false
        var disposals = 0
        val backend = object : PermissionBackend {
            override fun query(callback: (PermissionSnapshot) -> Unit) {
                callback(PermissionSnapshot(if (granted) PermissionStatus.Granted else PermissionStatus.Denied(false),
                    PermissionDetails(PermissionAvailability.Available,
                        if (granted) PermissionAccess.Full else PermissionAccess.None,
                        PermissionRequestability.Requestable)))
            }
            override fun request(callback: (Boolean) -> Unit) { requests += callback }
            override fun dispose() { disposals++ }
        }
        var callbacks = 0
        lateinit var state: CallbackPermissionState
        state = CallbackPermissionState(Permission("callback-exception-ownership"), {
            callbacks++
            if (callbacks == 1) {
                assertTrue(state.status.isGranted, "Status must be current before the throwing callback")
                assertEquals(PermissionRequestOutcome.Granted, state.permissionDetails.lastRequest)
                throw callbackFailure
            }
            assertFalse(it)
            assertFalse(state.status.isGranted)
            assertEquals(PermissionRequestOutcome.Denied, state.permissionDetails.lastRequest)
        }, scope, StandardTestDispatcher(testScheduler)) { backend }
        try {
            runCurrent()
            state.launchPermissionRequest()
            runCurrent()
            granted = true
            requests.single()(true)
            runCurrent()
            assertEquals(listOf(callbackFailure), errors, "Application errors must be surfaced, not turned into denial")
            assertTrue(compositionJob.isActive, "An application callback cannot cancel the remembered composition scope")
            state.launchPermissionRequest()
            runCurrent()
            assertEquals(2, requests.size, "The same native owner must accept a new request after callback failure")
            granted = false
            requests.last()(false)
            runCurrent()
            assertEquals(2, callbacks)
            assertEquals(listOf(callbackFailure), errors)
            state.dispose()
            state.dispose()
            runCurrent()
            assertEquals(1, disposals)
            assertTrue(compositionJob.isActive, "Disposal owns only the permission controller's work")
            assertTrue(compositionJob.children.none(), "No owned controller job may remain after disposal")
        } finally {
            state.dispose()
            scope.cancel()
            runCurrent()
        }
    }
}
