@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import kotlinx.coroutines.*
import kotlinx.coroutines.test.*
import kotlin.test.*

/** Real coroutine Job ownership around the production controller; the callback backend is controlled. */
class CallbackExceptionOwnershipTest {
    @Test fun throwingNativeDisposalStillReleasesTheOwnedJobAndDropsLateCompletions() = runTest {
        val parent = Job()
        val dispatcher = StandardTestDispatcher(testScheduler)
        val scope = CoroutineScope(parent + dispatcher)
        val failure = IllegalStateException("Deliberate native disposal failure")
        var callback: ((Boolean) -> Unit)? = null
        var nativeQueries = 0
        var disposals = 0
        val state = CallbackPermissionState(Permission("callback-disposal-ownership"), { fail("Late result") },
            scope, dispatcher) {
            object : PermissionBackend {
                override fun query(callback: (PermissionSnapshot) -> Unit) { nativeQueries++ }
                override fun request(result: (Boolean) -> Unit) { callback = result }
                override fun dispose() { disposals++; throw failure }
            }
        }
        try {
            runCurrent()
            state.launchPermissionRequest()
            runCurrent()
            assertNotNull(callback)
            assertSame(failure, assertFailsWith<IllegalStateException> { state.dispose() })
            runCurrent()
            assertTrue(parent.isActive)
            assertTrue(parent.children.none())
            callback!!(true)
            state.launchPermissionRequest()
            state.refreshPermissionStatus()
            runCurrent()
            assertEquals(1, nativeQueries)
            assertEquals(1, disposals)
            assertFalse(state.status.isGranted)
            state.dispose()
        } finally { state.dispose(); scope.cancel(); runCurrent() }
    }

    @Test fun cancellingTheCompositionParentStillCancelsOwnedOperations() = runTest {
        val parent = Job()
        val dispatcher = StandardTestDispatcher(testScheduler)
        val scope = CoroutineScope(parent + dispatcher)
        val queries = mutableListOf<(PermissionSnapshot) -> Unit>()
        var disposals = 0
        val state = CallbackPermissionState(Permission("callback-parent-cancellation"), { fail("Cancelled result") },
            scope, dispatcher) {
            object : PermissionBackend {
                override fun query(callback: (PermissionSnapshot) -> Unit) { queries += callback }
                override fun request(callback: (Boolean) -> Unit) { fail("Cancelled request") }
                override fun dispose() { disposals++ }
            }
        }
        try {
            runCurrent()
            assertEquals(1, queries.size)
            assertTrue(parent.children.any())
            parent.cancel()
            runCurrent()
            queries.single()(PermissionSnapshot(PermissionStatus.Granted, PermissionDetails()))
            state.launchPermissionRequest()
            state.refreshPermissionStatus()
            runCurrent()
            assertFalse(state.status.isGranted)
            assertEquals(1, queries.size)
            assertTrue(parent.children.none())
            state.dispose()
            assertEquals(1, disposals)
        } finally { state.dispose(); scope.cancel(); runCurrent() }
    }

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
            assertEquals(1, errors.size, "Application errors must be surfaced, not turned into denial")
            assertSame(callbackFailure, errors.single())
            assertTrue(compositionJob.isActive, "An application callback cannot cancel the remembered composition scope")
            state.launchPermissionRequest()
            runCurrent()
            assertEquals(2, requests.size, "The same native owner must accept a new request after callback failure")
            granted = false
            requests.last()(false)
            runCurrent()
            assertEquals(2, callbacks)
            assertEquals(1, errors.size)
            assertSame(callbackFailure, errors.single())
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
