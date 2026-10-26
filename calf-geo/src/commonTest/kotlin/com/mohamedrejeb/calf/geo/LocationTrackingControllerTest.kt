package com.mohamedrejeb.calf.geo

import androidx.compose.runtime.snapshots.Snapshot
import androidx.compose.runtime.snapshots.SnapshotStateObserver
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class LocationTrackingControllerTest {
    @Test fun initialAbsenceIsNotARealZeroCoordinate() {
        val controller = controller()
        assertEquals(LocationTrackingPhase.Unbound, controller.snapshotState.value.phase)
        assertNull(controller.fixState.value)
        assertTrue(controller.locationState.value.latitude.isNaN())
        assertTrue(controller.locationState.value.longitude.isNaN())
        assertTrue(controller.extendedLocationState.value.location.coordinatesAccuracyMeters.isNaN())
    }

    @Test fun noFixAfterSuccessfulRegistrationRemainsExplicit() {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        val results = mutableListOf<LocationStartResult>()
        controller.start(results::add)
        assertEquals(LocationTrackingPhase.Starting, controller.snapshotState.value.phase)
        assertTrue(results.isEmpty())
        backend.latest.callbacks.onRegistered(null)
        assertEquals(listOf<LocationStartResult>(LocationStartResult.Started), results)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
        assertNull(controller.fixState.value)
    }

    @Test fun nativeFixUpdatesAllViewsFromOneSnapshot() {
        val (controller, backend) = started()
        val first = fix(1.0)
        backend.latest.callbacks.onLocation(first)
        assertEquals(first, controller.snapshotState.value.fix)
        assertEquals(first, controller.fixState.value)
        assertEquals(first.coordinates, controller.locationState.value)
        assertEquals(first.coordinates, controller.extendedLocationState.value.location.coordinates)
        assertEquals(first.timestampMs, controller.extendedLocationState.value.timestampMs)
        val second = fix(2.0, timestamp = 2_000)
        backend.latest.callbacks.onLocation(second)
        assertEquals(second.coordinates, controller.locationState.value)
        assertEquals(second.coordinates, controller.extendedLocationState.value.location.coordinates)
    }

    @Test fun realComposeSnapshotObserversSeeLocationViewInvalidation() {
        val (controller, backend) = started()
        var invalidations = 0
        val observer = SnapshotStateObserver { it() }
        observer.start()
        try {
            observer.observeReads(Any(), { invalidations++ }) {
                controller.locationState.value
                controller.extendedLocationState.value
            }
            backend.latest.callbacks.onLocation(fix(1.0))
            Snapshot.sendApplyNotifications()
            assertEquals(1, invalidations)
        } finally {
            observer.stop()
            observer.clear()
        }
    }

    @Test fun fixBeforeRegistrationIsBufferedButNotPresentedAsSuccess() {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        controller.start { }
        backend.latest.callbacks.onLocation(fix(1.0))
        assertNull(controller.fixState.value)
        backend.latest.callbacks.onRegistered(null)
        assertEquals(fix(1.0), controller.fixState.value)
    }

    @Test fun trueZeroAndIndependentlyAbsentMeasurementsArePreserved() {
        val (controller, backend) = started()
        backend.latest.callbacks.onLocation(LocationFix(LatLng(0.0, 0.0), speedAccuracyMps = 0.0))
        assertEquals(LatLng(0.0, 0.0), controller.locationState.value)
        assertNull(controller.fixState.value?.speedMps)
        assertEquals(0.0, controller.fixState.value?.speedAccuracyMps)
        assertTrue(controller.extendedLocationState.value.speed.speedMps.isNaN())
        assertEquals(0.0, controller.extendedLocationState.value.speed.speedAccuracyMps)
        backend.latest.callbacks.onLocation(LocationFix(LatLng(0.0, 0.0), speedMps = 0.0, courseDegrees = 0.0, altitudeMeters = 0.0))
        assertEquals(0.0, controller.extendedLocationState.value.speed.speedMps)
        assertEquals(0.0, controller.extendedLocationState.value.azimuth.azimuthDegrees)
        assertEquals(0.0, controller.extendedLocationState.value.altitude.altitudeMeters)
    }

    @Test fun unboundStartReturnsFailureInsteadOfPretendingToStart() {
        val controller = controller()
        var result: LocationStartResult? = null
        controller.start { result = it }
        assertEquals(LocationTrackingFailure.NotBound, assertIs<LocationStartResult.Failed>(result).error.reason)
        assertEquals(LocationTrackingPhase.Unbound, controller.snapshotState.value.phase)
    }

    @Test fun deniedPermissionDoesNotCreateNativeSubscription() {
        val controller = controller()
        val backend = TestLocationBackend().apply { accuracy = null }
        controller.bind(backend)
        var result: LocationStartResult? = null
        controller.start { result = it }
        assertEquals(LocationTrackingFailure.PermissionDenied, assertIs<LocationStartResult.Failed>(result).error.reason)
        assertTrue(backend.subscriptions.isEmpty())
    }

    @Test fun approximateForegroundPermissionIsSufficient() {
        val controller = controller()
        val backend = TestLocationBackend().apply { accuracy = LocationPermissionAccuracy.Approximate }
        controller.bind(backend)
        controller.start { }
        backend.latest.callbacks.onRegistered(null)
        assertEquals(LocationPermissionAccuracy.Approximate, controller.snapshotState.value.permissionAccuracy)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
    }

    @Test fun providerCreationFailureCanRecoverWithoutAStuckStartedFlag() {
        val controller = controller()
        val backend = TestLocationBackend().apply { createFailure = IllegalStateException("provider missing") }
        controller.bind(backend)
        controller.start { }
        assertEquals(LocationTrackingPhase.Failed, controller.snapshotState.value.phase)
        backend.createFailure = null
        controller.start { }
        backend.latest.callbacks.onRegistered(null)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
    }

    @Test fun registrationFailureCompletesOnceAndRollsBack() {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        val results = mutableListOf<LocationStartResult>()
        controller.start(results::add)
        val old = backend.latest
        val error = LocationTrackingError(LocationTrackingFailure.ProviderUnavailable)
        old.callbacks.onRegistered(error)
        old.callbacks.onRegistered(null)
        old.callbacks.onLocation(fix(10.0))
        assertEquals(listOf<LocationStartResult>(LocationStartResult.Failed(error)), results)
        assertEquals(1, old.removals)
        assertNull(controller.fixState.value)
        assertEquals(LocationTrackingPhase.Failed, controller.snapshotState.value.phase)
    }

    @Test fun duplicateStartsDoNotCreateDuplicateSubscriptions() {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        controller.start { }
        var result: LocationStartResult? = null
        controller.start { result = it }
        assertEquals(LocationStartResult.InProgress, result)
        backend.latest.callbacks.onRegistered(null)
        controller.start { result = it }
        assertEquals(LocationStartResult.AlreadyStarted, result)
        assertEquals(1, backend.subscriptions.size)
    }

    @Test fun stoppingPendingRegistrationCompletesCancelledAndRejectsLateEvents() {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        val results = mutableListOf<LocationStartResult>()
        controller.start(results::add)
        val old = backend.latest
        controller.stop()
        val stopped = controller.snapshotState.value
        old.callbacks.onRegistered(null)
        old.callbacks.onLocation(fix(3.0))
        old.callbacks.onAvailability(true)
        assertEquals(listOf<LocationStartResult>(LocationStartResult.Cancelled), results)
        assertEquals(stopped, controller.snapshotState.value)
        controller.stop()
        assertEquals(1, old.removals)
    }

    @Test fun cancellingSuspendedStartOwnsOnlyItsRegistration() = runTest {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        val start = async { controller.awaitStart() }
        runCurrent()
        val old = backend.latest
        start.cancel()
        runCurrent()
        assertEquals(1, old.removals)
        assertEquals(LocationTrackingPhase.Stopped, controller.snapshotState.value.phase)
        old.callbacks.onRegistered(null)
        assertNull(controller.fixState.value)
    }

    @Test fun oldCancellationAndCallbacksCannotAffectNewBinding() {
        val controller = controller()
        val first = TestLocationBackend()
        controller.bind(first)
        val cancel = controller.start { }
        first.latest.callbacks.onRegistered(null)
        val second = TestLocationBackend()
        controller.bind(second)
        second.latest.callbacks.onRegistered(null)
        cancel()
        first.latest.callbacks.onLocation(fix(9.0))
        first.latest.callbacks.onFailure(LocationTrackingError(LocationTrackingFailure.PermissionDenied))
        second.latest.callbacks.onLocation(fix(4.0))
        assertEquals(1, first.latest.removals)
        assertEquals(0, second.latest.removals)
        assertEquals(fix(4.0), controller.fixState.value)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
    }

    @Test fun oldRemovalFailureDoesNotStopNewOwner() {
        val (controller, first) = started()
        first.latest.automaticRemoval = false
        val second = TestLocationBackend()
        controller.bind(second)
        second.latest.callbacks.onRegistered(null)
        first.latest.finishRemoval(LocationTrackingError(LocationTrackingFailure.RemovalFailed))
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
        assertEquals(LocationTrackingFailure.RemovalFailed, controller.snapshotState.value.cleanupError?.reason)
        assertEquals(0, second.latest.removals)
    }

    @Test fun removalFailureIsVisibleAndRepeatedStopCanRetry() {
        val (controller, backend) = started()
        backend.latest.automaticRemoval = false
        controller.stop()
        assertEquals(LocationTrackingPhase.Stopping, controller.snapshotState.value.phase)
        backend.latest.finishRemoval(LocationTrackingError(LocationTrackingFailure.RemovalFailed))
        assertEquals(LocationTrackingPhase.Failed, controller.snapshotState.value.phase)
        controller.stop()
        assertEquals(2, backend.latest.removals)
        backend.latest.finishRemoval(null)
        assertEquals(LocationTrackingPhase.Stopped, controller.snapshotState.value.phase)
        assertNull(controller.snapshotState.value.cleanupError)
    }

    @Test fun aNewStartDoesNotHideAnOutstandingRemovalFailure() {
        val (controller, backend) = started()
        backend.latest.automaticRemoval = false
        controller.stop()
        val error = LocationTrackingError(LocationTrackingFailure.RemovalFailed)
        backend.latest.finishRemoval(error)
        controller.start { }
        backend.latest.callbacks.onRegistered(null)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
        assertEquals(error, controller.snapshotState.value.cleanupError)
        controller.bind(TestLocationBackend())
        assertEquals(error, controller.snapshotState.value.cleanupError)
    }

    @Test fun unbindInvalidatesOldResultsAndAllowsExplicitNewBinding() {
        val (controller, backend) = started()
        controller.unbind()
        backend.latest.callbacks.onLocation(fix(8.0))
        assertNull(controller.fixState.value)
        assertEquals(LocationTrackingPhase.Unbound, controller.snapshotState.value.phase)
        controller.bind(TestLocationBackend())
        assertEquals(LocationTrackingPhase.Idle, controller.snapshotState.value.phase)
    }

    @Test fun closeIsTerminalAndNoLateNativeEventMutatesClosedState() {
        val (controller, backend) = started()
        backend.latest.automaticRemoval = false
        controller.close()
        val closed = controller.snapshotState.value
        backend.latest.callbacks.onLocation(fix(8.0))
        backend.latest.callbacks.onRegistered(null)
        backend.latest.finishRemoval(LocationTrackingError(LocationTrackingFailure.RemovalFailed))
        assertEquals(closed, controller.snapshotState.value)
        assertEquals(LocationTrackingPhase.Closed, closed.phase)
        assertFailsWith<IllegalStateException> { controller.bind(TestLocationBackend()) }
        var result: LocationStartResult? = null
        controller.start { result = it }
        assertEquals(LocationTrackingFailure.Closed, assertIs<LocationStartResult.Failed>(result).error.reason)
    }

    @Test fun permissionIsRecheckedOnResumeAndOnEveryDeliveredFix() {
        val (controller, backend) = started()
        backend.accuracy = LocationPermissionAccuracy.Approximate
        controller.refreshPermission()
        assertEquals(LocationPermissionAccuracy.Approximate, controller.snapshotState.value.permissionAccuracy)
        backend.accuracy = null
        backend.latest.callbacks.onLocation(fix(7.0))
        assertEquals(LocationTrackingFailure.PermissionDenied, controller.snapshotState.value.error?.reason)
        assertEquals(1, backend.latest.removals)
        assertNull(controller.fixState.value)
    }

    @Test fun invalidCoordinatesAreRejectedRatherThanPublished() {
        val (controller, backend) = started()
        backend.latest.callbacks.onLocation(fix(Double.NaN))
        assertEquals(LocationTrackingFailure.InvalidLocation, controller.snapshotState.value.error?.reason)
        assertNull(controller.fixState.value)
    }

    @Test fun duplicateAndOlderFixesDoNotReplaceNewerState() {
        val (controller, backend) = started()
        val current = fix(2.0, timestamp = 2000).copy(elapsedRealtimeNanos = 20)
        backend.latest.callbacks.onLocation(current)
        val snapshot = controller.snapshotState.value
        backend.latest.callbacks.onLocation(current)
        assertSame(snapshot, controller.snapshotState.value)
        backend.latest.callbacks.onLocation(fix(1.0, timestamp = 9999).copy(elapsedRealtimeNanos = 10))
        assertEquals(current, controller.fixState.value)
        backend.latest.callbacks.onLocation(fix(1.0, timestamp = 1000))
        assertEquals(current, controller.fixState.value)
    }

    @Test fun providerAvailabilityIsSeparateFromPermissionAndRegistration() {
        val (controller, backend) = started()
        backend.latest.callbacks.onAvailability(false)
        assertEquals(false, controller.snapshotState.value.isProviderAvailable)
        assertEquals(LocationTrackingPhase.Tracking, controller.snapshotState.value.phase)
        assertEquals(LocationPermissionAccuracy.Precise, controller.snapshotState.value.permissionAccuracy)
    }

    @Test fun unsupportedControllerHasDeterministicResultAndNoFix() = runTest {
        val controller = LocationTrackingController(LocationTrackingCapability.Unsupported)
        assertEquals(LocationStartResult.Unsupported, controller.awaitStart())
        controller.stop()
        assertEquals(LocationTrackingPhase.Unsupported, controller.snapshotState.value.phase)
        assertNull(controller.fixState.value)
        assertFalse(controller.locationState.value.isValid)
    }

    private fun controller() = LocationTrackingController(LocationTrackingCapability.Foreground)
    private fun started(): Pair<LocationTrackingController, TestLocationBackend> {
        val controller = controller()
        val backend = TestLocationBackend()
        controller.bind(backend)
        controller.start { }
        backend.latest.callbacks.onRegistered(null)
        return controller to backend
    }

    private fun fix(latitude: Double, timestamp: Long = 1000) = LocationFix(LatLng(latitude, 0.0), timestampMs = timestamp)
}

internal class TestLocationBackend : LocationTrackingBackend {
    var accuracy: LocationPermissionAccuracy? = LocationPermissionAccuracy.Precise
    var createFailure: Exception? = null
    val subscriptions = mutableListOf<TestLocationSubscription>()
    val latest get() = subscriptions.last()
    override fun permissionAccuracy() = accuracy
    override fun createSubscription(): LocationSubscription {
        createFailure?.let { throw it }
        return TestLocationSubscription().also { subscriptions += it }
    }
}

internal class TestLocationSubscription : LocationSubscription {
    lateinit var callbacks: LocationSubscriptionCallbacks
    var removals = 0
    var automaticRemoval = true
    private var completion: ((LocationTrackingError?) -> Unit)? = null
    override fun start(callbacks: LocationSubscriptionCallbacks) { this.callbacks = callbacks }
    override fun stop(onComplete: (LocationTrackingError?) -> Unit) {
        removals++
        completion = onComplete
        if (automaticRemoval) finishRemoval(null)
    }
    fun finishRemoval(error: LocationTrackingError?) {
        val callback = completion
        completion = null
        callback?.invoke(error)
    }
}
