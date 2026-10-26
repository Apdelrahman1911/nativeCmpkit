package com.mohamedrejeb.calf.geo

import android.os.Looper
import android.location.Location as AndroidLocation
import androidx.compose.runtime.AbstractApplier
import androidx.compose.runtime.BroadcastFrameClock
import androidx.compose.runtime.Composition
import androidx.compose.runtime.Recomposer
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.snapshots.Snapshot
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Exercises the real Android wrapper, main Looper and LifecycleRegistry with an injectable provider. */
@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidLocationTrackerTest {
    private val dispatcher = StandardTestDispatcher()
    private val trackers = mutableListOf<LocationTracker>()

    @Before fun setUp() { Dispatchers.setMain(dispatcher) }
    @After fun tearDown() {
        trackers.forEach { it.close() }
        Dispatchers.resetMain()
    }

    @Test fun commonFactoryCreatesAnExplicitlyUnboundAndroidTracker() = runTest(dispatcher) {
        val tracker = createLocationTracker().also { trackers += it }
        assertEquals(LocationTrackingCapability.Foreground, tracker.capability)
        assertNull(tracker.fixState.value)
        val result = assertIs<LocationStartResult.Failed>(tracker.startTrackingWithResult())
        assertEquals(LocationTrackingFailure.NotBound, result.error.reason)
        assertTrue(tracker.locationState.value.latitude.isNaN())
    }

    @Test fun realLocationResultFlowsThroughNativeAdapterIntoBothPublicStates() = runTest(dispatcher) {
        val client = TestAndroidLocationClient()
        val backend = AndroidLocationTrackingBackend(
            context(), LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build(), client,
        ) { LocationPermissionAccuracy.Approximate }
        val tracker = tracker { backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        val starting = async { tracker.startTrackingWithResult() }
        runCurrent()
        client.requests.single().completion.setResult(null)
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals(LocationStartResult.Started, starting.await())
        val native = AndroidLocation("injected-provider").apply {
            latitude = 4.0
            longitude = 5.0
            accuracy = 30f
            speed = 0f
            time = 1_700_000_000_000L
        }
        client.requests.single().callback.onLocationResult(LocationResult.create(listOf(native)))
        assertEquals(LatLng(4.0, 5.0), tracker.locationState.value)
        assertEquals(tracker.locationState.value, tracker.extendedLocationState.value.location.coordinates)
        assertEquals(30.0, tracker.fixState.value?.coordinatesAccuracyMeters)
        assertEquals(0.0, tracker.extendedLocationState.value.speed.speedMps)
        assertTrue(tracker.extendedLocationState.value.altitude.altitudeMeters.isNaN())
        assertEquals(LocationPermissionAccuracy.Approximate, tracker.snapshotState.value.permissionAccuracy)

        // Exercise consecutive native callbacks, including a batch whose last fix wins.
        val second = AndroidLocation(native).apply {
            latitude = -6.0
            longitude = 8.0
            accuracy = 12f
            speed = 3.5f
            altitude = -2.5
            bearing = 90f
            time += 1_000L
        }
        val callback = client.requests.single().callback
        callback.onLocationResult(LocationResult.create(listOf(native, second)))
        assertEquals(LatLng(-6.0, 8.0), tracker.locationState.value)
        assertEquals(tracker.locationState.value, tracker.extendedLocationState.value.location.coordinates)
        assertEquals(12.0, tracker.extendedLocationState.value.location.coordinatesAccuracyMeters)
        assertEquals(3.5, tracker.extendedLocationState.value.speed.speedMps)
        assertEquals(-2.5, tracker.extendedLocationState.value.altitude.altitudeMeters)
        assertEquals(90.0, tracker.extendedLocationState.value.azimuth.azimuthDegrees)
        assertEquals(second.time, tracker.extendedLocationState.value.timestampMs)
        val latest = tracker.snapshotState.value
        callback.onLocationResult(LocationResult.create(listOf(AndroidLocation(second))))
        callback.onLocationResult(LocationResult.create(emptyList()))
        callback.onLocationResult(LocationResult.create(listOf(native))) // Older native result.
        assertSame(latest, tracker.snapshotState.value)

        tracker.stopTracking()
        assertEquals(LocationTrackingPhase.Stopping, tracker.snapshotState.value.phase)
        val stopped = tracker.snapshotState.value
        callback.onLocationResult(LocationResult.create(listOf(AndroidLocation(second).apply {
            latitude = 9.0
            time += 1_000L
        })))
        assertSame(stopped, tracker.snapshotState.value)
        client.removals.single().completion.setResult(null)
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals(LocationTrackingPhase.Stopped, tracker.snapshotState.value.phase)
    }

    @Test fun nativeFixesRecomposeBothPublicViewsWithoutDuplicateOrDisposedDelivery() = runTest(dispatcher) {
        val client = TestAndroidLocationClient()
        val tracker = tracker { nativeBackend(client) }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        val frameClock = BroadcastFrameClock()
        val recomposer = Recomposer(coroutineContext + frameClock)
        val composition = Composition(NoUiApplier(), recomposer)
        val runner = launch(frameClock) { recomposer.runRecomposeAndApplyChanges() }
        val observed = mutableListOf<Pair<LatLng, ExtendedLocation>>()
        try {
            // Recomposer invalidates pre-existing content when its runner starts. Install
            // its snapshot observer before setContent, so bootstrap is not a second
            // observation attributed to the tracker (which has not even started yet).
            Snapshot.sendApplyNotifications()
            runCurrent()
            composition.setContent {
                val coordinates = tracker.locationState.value
                val extended = tracker.extendedLocationState.value
                // Record committed compositions, not speculative composition-body calls.
                SideEffect { observed += coordinates to extended }
            }
            composeFrame(frameClock, 0L)
            assertEquals(1, observed.size)
            assertTrue(observed.single().first.latitude.isNaN())
            assertTrue(observed.single().second.location.coordinates.latitude.isNaN())

            startNative(tracker, client)
            composeFrame(frameClock, 16_000_000L)
            assertEquals(1, observed.size) // Registration alone does not invent a fix.
            val callback = client.requests.single().callback
            val first = nativeLocation(1.0, 2.0, 1_000L)
            callback.onLocationResult(LocationResult.create(listOf(first)))
            composeFrame(frameClock, 32_000_000L)
            assertEquals(2, observed.size)
            assertEquals(LatLng(1.0, 2.0), observed.last().first)
            assertEquals(observed.last().first, observed.last().second.location.coordinates)
            assertEquals(1_000L, observed.last().second.timestampMs)

            callback.onLocationResult(LocationResult.create(listOf(AndroidLocation(first))))
            composeFrame(frameClock, 48_000_000L)
            assertEquals(2, observed.size) // An identical native fix causes no new committed composition.

            callback.onLocationResult(LocationResult.create(listOf(nativeLocation(3.0, 4.0, 2_000L))))
            composeFrame(frameClock, 64_000_000L)
            assertEquals(3, observed.size)
            assertEquals(LatLng(3.0, 4.0), observed.last().first)
            assertEquals(observed.last().first, observed.last().second.location.coordinates)
            assertEquals(2_000L, observed.last().second.timestampMs)

            composition.dispose()
            callback.onLocationResult(LocationResult.create(listOf(nativeLocation(5.0, 6.0, 3_000L))))
            composeFrame(frameClock, 80_000_000L)
            assertEquals(LatLng(5.0, 6.0), tracker.locationState.value) // The real tracker still updates.
            assertEquals(3, observed.size) // The disposed composition is no longer an observer.
            tracker.stopTracking()
            client.removals.single().completion.setResult(null)
            shadowOf(Looper.getMainLooper()).idle()
        } finally {
            composition.dispose()
            recomposer.cancel()
            runner.cancelAndJoin()
            recomposer.join()
            frameClock.cancel()
        }
    }

    @Test fun permissionRevokedBetweenPreflightAndNativeRequestIsNotStarted() = runTest(dispatcher) {
        val client = TestAndroidLocationClient()
        var checks = 0
        val backend = AndroidLocationTrackingBackend(
            context(), LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build(), client,
        ) { if (++checks == 1) LocationPermissionAccuracy.Precise else null }
        val tracker = tracker { backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        val result = assertIs<LocationStartResult.Failed>(tracker.startTrackingWithResult())
        assertEquals(LocationTrackingFailure.PermissionDenied, result.error.reason)
        assertTrue(client.requests.isEmpty())
        assertTrue(client.removals.isEmpty())
        assertEquals(LocationTrackingPhase.Failed, tracker.snapshotState.value.phase)
    }

    @Test fun bindAStartBindBDestroyADoesNotStopB() = runTest(dispatcher) {
        val first = TestLocationBackend()
        val second = TestLocationBackend()
        val backends = ArrayDeque(listOf(first, second))
        val tracker = tracker { backends.removeFirst() }
        val ownerA = Owner().apply { foreground() }
        val ownerB = Owner().apply { foreground() }
        tracker.bind(ownerA.lifecycle, context())
        start(tracker, first)
        tracker.bind(ownerB.lifecycle, context())
        second.latest.callbacks.onRegistered(null)
        assertEquals(0, ownerA.registry.observerCount)
        ownerA.destroy()
        assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
        assertEquals(1, first.latest.removals)
        assertEquals(0, second.latest.removals)
        ownerB.destroy()
        assertEquals(1, second.latest.removals)
        assertEquals(0, ownerB.registry.observerCount)
        assertEquals(LocationTrackingPhase.Unbound, tracker.snapshotState.value.phase)
    }

    @Test fun repeatedBindingToSameOwnerDoesNotAddObserversOrProviders() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        var factories = 0
        val tracker = tracker { factories++; backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        tracker.bind(owner.lifecycle, context())
        assertEquals(1, factories)
        assertEquals(1, owner.registry.observerCount)
        start(tracker, backend)
        assertEquals(LocationStartResult.AlreadyStarted, tracker.startTrackingWithResult())
        assertEquals(1, backend.subscriptions.size)
        tracker.close()
        assertEquals(0, owner.registry.observerCount)
        assertEquals(1, backend.latest.removals)
    }

    @Test fun destroyedOwnerCanBeReplacedAndExplicitlyRestartedWithANewNativeSubscription() = runTest(dispatcher) {
        val firstClient = TestAndroidLocationClient()
        val secondClient = TestAndroidLocationClient()
        val backends = ArrayDeque(listOf(nativeBackend(firstClient), nativeBackend(secondClient)))
        val tracker = tracker { backends.removeFirst() }
        val ownerA = Owner().apply { foreground() }
        tracker.bind(ownerA.lifecycle, context())
        startNative(tracker, firstClient)
        val oldCallback = firstClient.requests.single().callback
        oldCallback.onLocationResult(LocationResult.create(listOf(nativeLocation(1.0, 2.0, 1_000L))))
        assertEquals(LatLng(1.0, 2.0), tracker.locationState.value)

        ownerA.destroy()
        assertEquals(0, ownerA.registry.observerCount)
        assertEquals(LocationTrackingPhase.Unbound, tracker.snapshotState.value.phase)
        assertNull(tracker.fixState.value)
        assertSame(oldCallback, firstClient.removals.single().callback)
        val unbound = tracker.snapshotState.value
        oldCallback.onLocationResult(LocationResult.create(listOf(nativeLocation(7.0, 8.0, 2_000L))))
        assertSame(unbound, tracker.snapshotState.value)

        val ownerB = Owner().apply { foreground() }
        tracker.bind(ownerB.lifecycle, context())
        assertEquals(1, ownerB.registry.observerCount)
        assertEquals(LocationTrackingPhase.Idle, tracker.snapshotState.value.phase)
        assertTrue(secondClient.requests.isEmpty()) // Destruction does not preserve an auto-start request.
        startNative(tracker, secondClient)
        val newCallback = secondClient.requests.single().callback
        newCallback.onLocationResult(LocationResult.create(listOf(nativeLocation(3.0, 4.0, 3_000L))))
        assertEquals(LatLng(3.0, 4.0), tracker.locationState.value)
        assertEquals(tracker.locationState.value, tracker.extendedLocationState.value.location.coordinates)
        val restarted = tracker.snapshotState.value

        // Late old-provider cleanup and callbacks cannot overwrite or stop the new owner.
        firstClient.removals.single().completion.setResult(null)
        shadowOf(Looper.getMainLooper()).idle()
        oldCallback.onLocationResult(LocationResult.create(listOf(nativeLocation(9.0, 10.0, 4_000L))))
        assertSame(restarted, tracker.snapshotState.value)
        assertTrue(secondClient.removals.isEmpty())
        assertEquals(1, firstClient.removals.size)

        ownerB.destroy()
        assertEquals(0, ownerB.registry.observerCount)
        assertSame(newCallback, secondClient.removals.single().callback)
        secondClient.removals.single().completion.setResult(null)
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals(LocationTrackingPhase.Unbound, tracker.snapshotState.value.phase)
    }

    @Test fun alreadyInactiveOwnerCannotStartForegroundUpdates() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        val tracker = tracker { backend }
        val owner = Owner().apply { registry.currentState = Lifecycle.State.CREATED }
        tracker.bind(owner.lifecycle, context())
        val result = assertIs<LocationStartResult.Failed>(tracker.startTrackingWithResult())
        assertEquals(LocationTrackingFailure.OwnerInactive, result.error.reason)
        assertEquals(LocationTrackingFailure.OwnerInactive, tracker.snapshotState.value.error?.reason)
        assertTrue(backend.subscriptions.isEmpty())
        owner.foreground()
        start(tracker, backend)
        assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
    }

    @Test fun activeRebindToInactiveOwnerDoesNotAutoStartHiddenUpdates() = runTest(dispatcher) {
        val first = TestLocationBackend()
        val second = TestLocationBackend()
        val backends = ArrayDeque(listOf(first, second))
        val tracker = tracker { backends.removeFirst() }
        val ownerA = Owner().apply { foreground() }
        val ownerB = Owner().apply { registry.currentState = Lifecycle.State.CREATED }
        tracker.bind(ownerA.lifecycle, context())
        start(tracker, first)
        tracker.bind(ownerB.lifecycle, context())
        assertEquals(1, first.latest.removals)
        assertTrue(second.subscriptions.isEmpty())
        assertEquals(LocationTrackingFailure.OwnerInactive, tracker.snapshotState.value.error?.reason)
        ownerA.destroy()
        assertTrue(second.subscriptions.isEmpty())
        ownerB.foreground()
        assertTrue(second.subscriptions.isEmpty()) // Foregrounding does not silently re-request.
        start(tracker, second)
        assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
    }

    @Test fun onStopCancelsDeliveryAndResumeNeedsExplicitRestart() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        val tracker = tracker { backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        start(tracker, backend)
        val previous = backend.latest
        owner.registry.currentState = Lifecycle.State.CREATED
        previous.callbacks.onLocation(LocationFix(LatLng(7.0, 0.0)))
        assertEquals(LocationTrackingPhase.Stopped, tracker.snapshotState.value.phase)
        assertNull(tracker.fixState.value)
        assertEquals(LocationTrackingFailure.OwnerInactive, assertIs<LocationStartResult.Failed>(tracker.startTrackingWithResult()).error.reason)
        owner.foreground()
        assertEquals(1, backend.subscriptions.size)
        start(tracker, backend)
        assertEquals(2, backend.subscriptions.size)
    }

    @Test fun destroyedOwnerIsRejectedWithoutDamagingCurrentOwner() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        val tracker = tracker { backend }
        val live = Owner().apply { foreground() }
        tracker.bind(live.lifecycle, context())
        start(tracker, backend)
        val destroyed = Owner().apply { foreground(); destroy() }
        assertFailsWith<IllegalStateException> { tracker.bind(destroyed.lifecycle, context()) }
        assertEquals(1, live.registry.observerCount)
        assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
    }

    @Test fun backgroundCoroutineStartDispatchesProviderWorkToMain() = runTest(dispatcher) {
        val entered = CompletableDeferred<Unit>()
        val backend = TestLocationBackend()
        var providerLooper: Looper? = null
        val provider = object : LocationTrackingBackend {
            override fun permissionAccuracy(): LocationPermissionAccuracy? = backend.permissionAccuracy()
            override fun createSubscription(): LocationSubscription {
                providerLooper = Looper.myLooper()
                val result = backend.createSubscription()
                entered.complete(Unit)
                return result
            }
        }
        val tracker = tracker { provider }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        val starting = async(Dispatchers.Default) { tracker.startTrackingWithResult() }
        entered.await()
        backend.latest.callbacks.onRegistered(null)
        assertEquals(LocationStartResult.Started, starting.await())
        assertSame(Looper.getMainLooper(), providerLooper)
    }

    @Test fun bindStopAndCloseRejectIncorrectThreadRatherThanUseImplicitLooper() {
        val tracker = tracker { TestLocationBackend() }
        var failure: Throwable? = null
        Thread {
            try { tracker.stopTracking() } catch (error: Throwable) { failure = error }
        }.apply { start(); join() }
        assertIs<IllegalStateException>(failure)
    }

    @Test fun cancellationDuringRegistrationRemovesAndRejectsLateFix() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        val tracker = tracker { backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        val starting = async { tracker.startTrackingWithResult() }
        runCurrent()
        starting.cancel()
        runCurrent()
        val snapshot = tracker.snapshotState.value
        backend.latest.callbacks.onRegistered(null)
        backend.latest.callbacks.onLocation(LocationFix(LatLng(6.0, 0.0)))
        assertEquals(1, backend.latest.removals)
        assertEquals(snapshot, tracker.snapshotState.value)
    }

    @Test fun rebindWhileStartPendingCompletesOldCallerButDoesNotCancelNewOwner() = runTest(dispatcher) {
        val first = TestLocationBackend()
        val second = TestLocationBackend()
        val backends = ArrayDeque(listOf(first, second))
        val tracker = tracker { backends.removeFirst() }
        val ownerA = Owner().apply { foreground() }
        val ownerB = Owner().apply { foreground() }
        tracker.bind(ownerA.lifecycle, context())
        val starting = async { tracker.startTrackingWithResult() }
        runCurrent()
        tracker.bind(ownerB.lifecycle, context())
        assertEquals(LocationStartResult.Cancelled, starting.await())
        second.latest.callbacks.onRegistered(null)
        assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
        assertEquals(0, second.latest.removals)
    }

    @Test fun resumeRefreshDetectsRevocationBeforeNewFixDelivery() = runTest(dispatcher) {
        val backend = TestLocationBackend()
        val tracker = tracker { backend }
        val owner = Owner().apply { foreground() }
        tracker.bind(owner.lifecycle, context())
        start(tracker, backend)
        owner.registry.currentState = Lifecycle.State.STARTED
        backend.accuracy = null
        owner.registry.currentState = Lifecycle.State.RESUMED
        assertEquals(LocationTrackingFailure.PermissionDenied, tracker.snapshotState.value.error?.reason)
        assertEquals(1, backend.latest.removals)
    }

    private fun tracker(factory: () -> LocationTrackingBackend) = LocationTracker { factory() }.also { trackers += it }
    private fun context() = RuntimeEnvironment.getApplication()
    private fun nativeBackend(client: TestAndroidLocationClient) = AndroidLocationTrackingBackend(
        context(), LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build(), client,
    ) { LocationPermissionAccuracy.Approximate }

    private fun nativeLocation(latitude: Double, longitude: Double, timeMs: Long) = AndroidLocation("injected-provider").apply {
        this.latitude = latitude
        this.longitude = longitude
        time = timeMs
    }

    private suspend fun TestScope.startNative(tracker: LocationTracker, client: TestAndroidLocationClient) {
        val result = async { tracker.startTrackingWithResult() }
        runCurrent()
        client.requests.single().completion.setResult(null)
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals(LocationStartResult.Started, result.await())
    }

    private fun TestScope.composeFrame(clock: BroadcastFrameClock, timeNanos: Long) {
        Snapshot.sendApplyNotifications()
        runCurrent()
        clock.sendFrame(timeNanos)
        runCurrent()
    }

    private suspend fun TestScope.start(tracker: LocationTracker, backend: TestLocationBackend) {
        val result = async { tracker.startTrackingWithResult() }
        runCurrent()
        backend.latest.callbacks.onRegistered(null)
        assertEquals(LocationStartResult.Started, result.await())
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this)
        override val lifecycle: Lifecycle = registry
        fun foreground() { registry.currentState = Lifecycle.State.RESUMED }
        fun destroy() { registry.currentState = Lifecycle.State.DESTROYED }
    }

    /** Real Compose runtime composition with SideEffects only; this test creates no UI nodes. */
    private class NoUiApplier : AbstractApplier<Unit>(Unit) {
        override fun insertTopDown(index: Int, instance: Unit) { error("No UI nodes expected") }
        override fun insertBottomUp(index: Int, instance: Unit) { error("No UI nodes expected") }
        override fun remove(index: Int, count: Int) { error("No UI nodes expected") }
        override fun move(from: Int, to: Int, count: Int) { error("No UI nodes expected") }
        override fun onClear() = Unit
    }
}
