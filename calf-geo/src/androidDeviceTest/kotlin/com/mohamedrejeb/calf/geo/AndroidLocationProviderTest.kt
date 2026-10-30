// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.geo

import android.Manifest
import android.app.UiAutomation
import android.content.pm.PackageManager
import android.location.Location as AndroidLocation
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.GoogleApiAvailabilityLight
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.common.api.Status
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.TaskCompletionSource
import com.google.android.gms.tasks.Tasks
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** A real resumed Activity, not a sample app or a fabricated foreground owner. */
class GeoTrackingVerificationActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply { text = "NativeCmpKit foreground location verification" })
    }
}

/**
 * The first method uses actual OS denied/coarse/fine grants and the real default provider
 * in a foreground Activity: not GPS/fix, revocation/process-death,
 * physical/minimum-device or no Play Services/settings-off certification.
 * The other two methods use real native GMS Tasks/Looper/threads with explicitly
 * injected transport failures and registration timing, not an available GPS.
 * Grants are only to this fresh private test UID; the owned CI emulator is
 * disposable. Do not revoke this UID mid-instrumentation and kill the reporter.
 */
@RunWith(AndroidJUnit4::class)
class AndroidLocationProviderTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext

    @Test fun nativeForegroundDeniedCoarseAndFinePermissionsUseRealGmsRegistration() {
        runBlocking {
            assertEquals(context.applicationInfo.uid, instrumentation.context.applicationInfo.uid,
                "Only the standalone private test UID may receive fixture grants")
            assertTrue(context.packageName.endsWith(".test"))
            for (permission in listOf(Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION)) {
                assertEquals(PackageManager.PERMISSION_DENIED, ContextCompat.checkSelfPermission(context, permission),
                    "A previously granted/shared fixture must not be silently reused or revoked")
            }
            assertEquals(ConnectionResult.SUCCESS,
                GoogleApiAvailabilityLight.getInstance().isGooglePlayServicesAvailable(context),
                "This real-provider case requires an actually available Google APIs fixture")
            val tracker = onMain { LocationTracker() }
            try {
                val unbound = assertIs<LocationStartResult.Failed>(withTimeout(15_000) { tracker.startTrackingWithResult() })
                assertEquals(LocationTrackingFailure.NotBound, unbound.error.reason)
                ActivityScenario.launch(GeoTrackingVerificationActivity::class.java).use { scenario ->
                    scenario.onActivity { activity ->
                        assertTrue(activity.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED))
                        tracker.bind(activity.lifecycle, activity)
                    }
                    val denied = assertIs<LocationStartResult.Failed>(withTimeout(15_000) { tracker.startTrackingWithResult() })
                    assertEquals(LocationTrackingFailure.PermissionDenied, denied.error.reason)
                    assertEquals(LocationTrackingPhase.Failed, tracker.snapshotState.value.phase)
                    val automation: UiAutomation = instrumentation.uiAutomation
                    automation.grantRuntimePermission(context.packageName, Manifest.permission.ACCESS_COARSE_LOCATION)
                    waitUntil { ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED }
                    assertEquals(PackageManager.PERMISSION_DENIED, ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION))
                    val coarse = async(Dispatchers.Default) { withTimeout(15_000) { tracker.startTrackingWithResult() } }
                    assertEquals(LocationStartResult.Started, coarse.await())
                    assertEquals(LocationPermissionAccuracy.Approximate, tracker.snapshotState.value.permissionAccuracy)
                    assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
                    assertEquals(LocationStartResult.AlreadyStarted, withTimeout(15_000) { tracker.startTrackingWithResult() })
                    onMain { tracker.stopTracking() }
                    awaitStopped(tracker)
                    automation.grantRuntimePermission(context.packageName, Manifest.permission.ACCESS_FINE_LOCATION)
                    waitUntil { ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED }
                    val fine = async(Dispatchers.Main.immediate) { withTimeout(15_000) { tracker.startTrackingWithResult() } }
                    assertEquals(LocationStartResult.Started, fine.await())
                    assertEquals(LocationPermissionAccuracy.Precise, tracker.snapshotState.value.permissionAccuracy)
                    onMain { tracker.stopTracking(); tracker.stopTracking() }
                    awaitStopped(tracker)
                    assertNull(tracker.snapshotState.value.cleanupError)
                }
            } finally {
                onMain { tracker.close() }
                assertEquals(LocationTrackingPhase.Closed, tracker.snapshotState.value.phase)
            }
        }
    }

    @Test fun nativeProviderTaskErrorsRemovalRetryAndRecoveryAreObservable() {
        runBlocking {
            val client = TaskClient()
            val tracker = boundTracker(client)
            try {
                val denied = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val first = awaitRequest(client, 1)
                completeOffMain { first.completion.setException(SecurityException("injected native revocation")) }
                assertEquals(LocationTrackingFailure.PermissionDenied, assertIs<LocationStartResult.Failed>(denied.await()).error.reason)
                val recovered = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val second = awaitRequest(client, 2)
                completeOffMain { second.completion.setResult(null) }
                assertEquals(LocationStartResult.Started, recovered.await())
                onMain {
                    client.removalFailure = IllegalStateException("injected removal failure")
                    tracker.stopTracking()
                }
                waitUntil { tracker.snapshotState.value.phase == LocationTrackingPhase.Failed }
                assertEquals(LocationTrackingFailure.RemovalFailed, tracker.snapshotState.value.cleanupError?.reason)
                onMain { client.removalFailure = null; tracker.stopTracking() }
                awaitStopped(tracker)
                assertNull(tracker.snapshotState.value.cleanupError)
                val unavailable = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val third = awaitRequest(client, 3)
                completeOffMain { third.completion.setException(ApiException(Status(17))) }
                val error = assertIs<LocationStartResult.Failed>(unavailable.await()).error
                assertEquals(LocationTrackingFailure.ProviderUnavailable, error.reason)
                assertEquals(17, error.platformCode)
                val final = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val fourth = awaitRequest(client, 4)
                completeOffMain { fourth.completion.setResult(null) }
                assertEquals(LocationStartResult.Started, final.await())
                onMain { tracker.stopTracking() }
                awaitStopped(tracker)
                assertEquals(5, onMain { client.removals.size })
            } finally {
                onMain { tracker.close() }
            }
        }
    }

    @Test fun nativeBackgroundCancellationAndQueuedOldCallbacksCannotOwnANewStart() {
        runBlocking {
            val client = TaskClient()
            val tracker = boundTracker(client)
            try {
                val pending = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val first = awaitRequest(client, 1)
                assertEquals(LocationStartResult.InProgress, withTimeout(5_000) { tracker.startTrackingWithResult() })
                assertEquals(1, onMain { client.requests.size })
                pending.cancelAndJoin()
                waitUntil { onMain { client.removals.size == 1 } }
                assertEquals(LocationTrackingPhase.Stopping, tracker.snapshotState.value.phase)
                completeOffMain { first.completion.setResult(null) }
                awaitStopped(tracker)
                assertEquals(2, onMain { client.removals.size })
                assertTrue(onMain { client.removals.all { it === first.callback } })
                val replacement = async(Dispatchers.Default) { withTimeout(5_000) { tracker.startTrackingWithResult() } }
                val second = awaitRequest(client, 2)
                completeOffMain { second.completion.setResult(null) }
                assertEquals(LocationStartResult.Started, replacement.await())
                assertEquals(LocationStartResult.AlreadyStarted, withTimeout(5_000) { tracker.startTrackingWithResult() })
                val active = tracker.snapshotState.value
                Handler(Looper.getMainLooper()).post { first.callback.onLocationResult(fix(70.0)) }
                instrumentation.waitForIdleSync()
                assertSame(active, tracker.snapshotState.value)
                Handler(Looper.getMainLooper()).post { second.callback.onLocationResult(fix(5.0)) }
                instrumentation.waitForIdleSync()
                assertEquals(LatLng(5.0, 6.0), tracker.fixState.value?.coordinates)
                val corrected = tracker.snapshotState.value
                Handler(Looper.getMainLooper()).post { first.callback.onLocationResult(fix(80.0)) }
                instrumentation.waitForIdleSync()
                assertSame(corrected, tracker.snapshotState.value)
                onMain { tracker.stopTracking() }
                awaitStopped(tracker)
                assertEquals(3, onMain { client.removals.size })
            } finally {
                onMain { tracker.close() }
            }
        }
    }

    private fun boundTracker(client: TaskClient): LocationTracker = onMain {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build()
        LocationTracker { application -> AndroidLocationTrackingBackend(application, request, client) { LocationPermissionAccuracy.Approximate } }
            .apply { bind(Owner().apply { registry.currentState = Lifecycle.State.RESUMED }.lifecycle, context) }
    }

    private fun awaitRequest(client: TaskClient, count: Int): TaskClient.Request {
        waitUntil { onMain { client.requests.size == count } }
        return onMain { client.requests.last() }
    }

    private fun awaitStopped(tracker: LocationTracker) {
        waitUntil { tracker.snapshotState.value.phase == LocationTrackingPhase.Stopped }
    }

    private fun waitUntil(predicate: () -> Boolean) {
        val started = System.nanoTime()
        while (!predicate()) {
            check(System.nanoTime() - started < 10_000_000_000L) { "Actual native predicate did not complete within ten seconds" }
            Thread.sleep(10)
        }
    }

    private fun <T> onMain(action: () -> T): T {
        var value: T? = null
        instrumentation.runOnMainSync { value = action() }
        @Suppress("UNCHECKED_CAST")
        return value as T
    }

    private fun completeOffMain(action: () -> Unit) {
        var failure: Throwable? = null
        Thread {
            try { assertNotEquals(Looper.getMainLooper(), Looper.myLooper()); action() }
            catch (error: Throwable) { failure = error }
        }.apply { start(); join() }
        failure?.let { throw it }
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this)
        override val lifecycle: Lifecycle = registry
    }

    private class TaskClient : AndroidLocationClient {
        data class Request(val callback: LocationCallback, val completion: TaskCompletionSource<Void>)
        val requests = mutableListOf<Request>()
        val removals = mutableListOf<LocationCallback>()
        var removalFailure: Exception? = null
        override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> {
            assertEquals(Looper.getMainLooper(), looper)
            assertEquals(looper, Looper.myLooper())
            val completion = TaskCompletionSource<Void>()
            requests += Request(callback, completion)
            return completion.task
        }
        override fun remove(callback: LocationCallback): Task<Void> {
            assertEquals(Looper.getMainLooper(), Looper.myLooper())
            removals += callback
            return removalFailure?.let { Tasks.forException<Void>(it) } ?: Tasks.forResult<Void>(null)
        }
    }

    private fun fix(latitude: Double): LocationResult = LocationResult.create(listOf(AndroidLocation("injected-native-provider").apply {
        this.latitude = latitude
        longitude = 6.0
        time = 1_700_000_000_000L
    }))
}
