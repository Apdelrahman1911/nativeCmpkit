@file:OptIn(ExperimentalPermissionsApi::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)

package com.mohamedrejeb.calf.permissions

import kotlinx.coroutines.test.*
import kotlin.test.*

class CallbackPermissionStateTest {
    private class Backend : PermissionBackend {
        val queries = mutableListOf<(PermissionSnapshot) -> Unit>()
        val requests = mutableListOf<(Boolean) -> Unit>()
        var disposals = 0
        var refreshes = 0
        var failQuery = false
        override fun query(callback: (PermissionSnapshot) -> Unit) {
            if (failQuery) error("native observation failed")
            queries += callback
        }
        override fun request(callback: (Boolean) -> Unit) { requests += callback }
        override fun onRefresh() { refreshes++ }
        override fun dispose() { disposals++ }
    }
    private val granted = PermissionSnapshot(PermissionStatus.Granted, PermissionDetails(
        PermissionAvailability.Available, PermissionAccess.Full, PermissionRequestability.NotRequired))
    private val denied = PermissionSnapshot(PermissionStatus.Denied(true), PermissionDetails(
        PermissionAvailability.Available, PermissionAccess.None, PermissionRequestability.SettingsOnly))

    @Test fun resultIsDispatchedAndStateIsUpdatedBeforeUserCallback() = runTest {
        val backend = Backend()
        var calls = 0
        lateinit var state: CallbackPermissionState
        state = CallbackPermissionState(Permission("Camera"), {
            calls++; assertTrue(it); assertEquals(granted.status, state.status)
            assertEquals(PermissionAccess.Full, state.details.access)
        }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent()
        backend.queries[0](denied)
        runCurrent()
        state.launchPermissionRequest()
        runCurrent()
        backend.requests.single()(true)
        assertEquals(0, calls)
        runCurrent()
        backend.queries.last()(granted)
        assertEquals(0, calls) // A native callback does not mutate state on its calling queue.
        runCurrent()
        assertEquals(1, calls)
    }

    @Test fun oldStatusObservationCannotOverwriteNewRequestResult() = runTest {
        val backend = Backend()
        val state = CallbackPermissionState(Permission("Camera"), {}, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent()
        val oldQuery = backend.queries.single()
        state.launchPermissionRequest(); runCurrent()
        backend.requests.single()(true); runCurrent()
        backend.queries.last()(granted); runCurrent()
        oldQuery(denied); runCurrent()
        assertTrue(state.status.isGranted)
    }

    @Test fun repeatedRequestsCoalesceNativeWorkAndRejectDuplicateCompletion() = runTest {
        val backend = Backend(); var calls = 0
        val state = CallbackPermissionState(Permission("Camera"), { calls++ }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent()
        state.launchPermissionRequest(); state.launchPermissionRequest(); runCurrent()
        assertEquals(1, backend.requests.size)
        backend.requests.single()(true); backend.requests.single()(false); runCurrent()
        assertEquals(2, backend.queries.size)
        backend.queries.last()(granted); backend.queries.last()(denied); runCurrent()
        assertEquals(2, calls)
        assertTrue(state.status.isGranted)
    }

    @Test fun disposalCleansOnceAndSuppressesQueuedQueriesAndRequests() = runTest {
        val backend = Backend()
        val state = CallbackPermissionState(Permission("Camera"), { fail("late callback") }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent()
        state.launchPermissionRequest(); runCurrent()
        state.dispose(); state.dispose()
        backend.requests.single()(true); backend.queries.single()(granted); runCurrent()
        state.launchPermissionRequest(); state.refreshPermissionStatus(); runCurrent()
        assertEquals(1, backend.disposals)
        assertEquals(1, backend.requests.size)
        assertFalse(state.status.isGranted)
    }

    @Test fun refreshDetectsRevocationOfPreviouslyGrantedState() = runTest {
        val backend = Backend()
        val state = CallbackPermissionState(Permission("Camera"), {}, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent(); backend.queries.single()(granted); runCurrent()
        assertTrue(state.status.isGranted)
        state.refreshPermissionStatus(); runCurrent()
        backend.queries.last()(denied); runCurrent()
        assertFalse(state.status.isGranted)
        assertEquals(2, backend.refreshes)
    }

    @Test fun reentrantRequestIsNotClearedByPreviousCompletion() = runTest {
        val backend = Backend(); var calls = 0
        lateinit var state: CallbackPermissionState
        state = CallbackPermissionState(Permission("Camera"), {
            calls++; if (calls == 1) state.launchPermissionRequest()
        }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent(); state.launchPermissionRequest(); runCurrent()
        backend.requests[0](true); runCurrent(); backend.queries.last()(granted); runCurrent()
        assertEquals(2, backend.requests.size)
        backend.requests[1](false); runCurrent(); backend.queries.last()(denied); runCurrent()
        assertEquals(2, calls)
    }

    @Test fun failedPostRequestQueryCompletesFalseAndReleasesNativeOwnership() = runTest {
        val backend = Backend(); var calls = 0
        val state = CallbackPermissionState(Permission("Camera"), { assertFalse(it); calls++ }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent(); state.launchPermissionRequest(); runCurrent()
        backend.failQuery = true
        backend.requests.single()(true); runCurrent()
        assertEquals(1, calls)
        assertEquals(PermissionRequestOutcome.Failed, state.details.lastRequest)
        backend.failQuery = false
        state.launchPermissionRequest(); runCurrent()
        assertEquals(2, backend.requests.size)
    }

    @Test fun failedPassiveQueryDoesNotFabricateGrantOrPermanentDenial() = runTest {
        val backend = Backend().apply { failQuery = true }
        val state = CallbackPermissionState(Permission("Camera"), { fail("not a request") }, this, StandardTestDispatcher(testScheduler)) { backend }
        runCurrent()
        assertFalse(state.status.isGranted)
        assertFalse(state.status.shouldShowRationale)
        assertEquals(PermissionRequestOutcome.Failed, state.details.lastRequest)
    }
}
