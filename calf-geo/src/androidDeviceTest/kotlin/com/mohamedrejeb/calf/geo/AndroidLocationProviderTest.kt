// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.geo

import android.Manifest
import android.app.UiAutomation
import android.content.pm.PackageManager
import android.location.Location as AndroidLocation
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Build
import android.os.Process
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

/** ATE1.0.1's CSV transport cannot carry comma-containing method lists. */
@Target(AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
annotation class AndroidGeoPrerequisiteVerification

/** A real resumed Activity, not a sample app or a fabricated foreground owner. */
class GeoTrackingVerificationActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply { text = "NativeCmpKit foreground location verification" })
    }
}

/**
 * Three methods use an actual separate-UID source consumer/foreground Activity:
 * real default provider, actual denied/coarse/fine/revoked OS permissions,
 * actually user-uninstalled/disabled Play Services, system settings and recovery.
 * These are not GPS/fix accuracy, physical/minimum-device or power/heap certification.
 * The other two methods use real native GMS Tasks/Looper/threads with explicitly
 * injected transport failures and registration timing, not an available GPS.
 * Grants/revocations are only to the owned separate probe UID, never this reporter.
 * System-prerequisite mutations require the explicit disposable API35 CI fixture.
 */
@RunWith(AndroidJUnit4::class)
class AndroidLocationProviderTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext

    @AndroidGeoPrerequisiteVerification
    @Test fun nativeForegroundDeniedCoarseAndFinePermissionsUseRealGmsRegistration() {
        ownedProbe { probe ->
            val initial = probe.request("snapshot")
            assertFalse(initial.getBoolean("coarse")); assertFalse(initial.getBoolean("fine"))
            assertEquals(ConnectionResult.SUCCESS, initial.getInt("gms")); assertTrue(initial.getBoolean("settings"))
            probe.request("create")
            assertStartFailure(probe.request("start-main"), "NotBound")
            probe.foreground(); probe.request("bind")
            assertStartFailure(probe.request("start-background"), "PermissionDenied")
            grantProbe(precise = false)
            val coarse = probe.request("start-background")
            assertEquals("Started", coarse.getString("result")); assertEquals("Approximate", coarse.getString("accuracy"))
            assertEquals("Tracking", coarse.getString("phase")); assertTrue(coarse.getBoolean("foreground"))
            assertTrue(coarse.getBoolean("coarse")); assertFalse(coarse.getBoolean("fine"))
            assertEquals("AlreadyStarted", probe.request("start-main").getString("result"))
            probe.request("stop"); probe.stopped()
            grantProbe(precise = true)
            val fine = probe.request("start-main")
            assertEquals("Started", fine.getString("result")); assertEquals("Precise", fine.getString("accuracy"))
            assertTrue(fine.getBoolean("coarse")); assertTrue(fine.getBoolean("fine"))
            probe.request("stop"); probe.request("stop"); probe.stopped()
            assertNull(probe.request("snapshot").getString("cleanup"))
        }
    }

    @AndroidGeoPrerequisiteVerification
    @Test fun nativeRevocationKillsOnlyOwnedProbeAndRestartReportsDenied() {
        ownedProbe { probe ->
            probe.foreground(); probe.request("create"); probe.request("bind"); grantProbe(precise = true)
            val started = probe.request("start-background")
            assertEquals("Started", started.getString("result"))
            val reporterPid = Process.myPid()
            instrumentation.uiAutomation.revokeRuntimePermission(OwnedGeoProbe.PACKAGE, Manifest.permission.ACCESS_COARSE_LOCATION)
            probe.awaitDeath()
            probe.disconnect()
            resetProbePermissions()
            probe.connect(); probe.foreground(); probe.request("create"); probe.request("bind")
            val denied = probe.request("start-background")
            assertStartFailure(denied, "PermissionDenied")
            assertFalse(denied.getBoolean("coarse")); assertFalse(denied.getBoolean("fine"))
            assertNotEquals(started.getString("generation"), denied.getString("generation"))
            assertNotEquals(started.getInt("pid"), denied.getInt("pid"))
            assertEquals(started.getInt("uid"), denied.getInt("uid")); assertEquals(reporterPid, Process.myPid())
            grantProbe(precise = true)
            assertEquals("Started", probe.request("start-main").getString("result"))
            probe.request("stop"); probe.stopped()
        }
    }

    @AndroidGeoPrerequisiteVerification
    @Test fun nativeMissingDisabledPlayServicesAndLocationSettingsBlockStartAndRecover() {
        ownedProbe { probe ->
            val initial = probe.request("snapshot")
            assertEquals(ConnectionResult.SUCCESS, initial.getInt("gms")); assertTrue(initial.getBoolean("settings"))
            assertTrue(initial.getBoolean("gmsInstalled")); assertTrue(initial.getBoolean("gmsSystem"),
                "Only the disposable system-image package can be restored with install-existing")
            probe.foreground(); probe.request("create"); probe.request("bind"); grantProbe(precise = true)
            try {
                assertTrue(shell("pm disable-user --user 0 com.google.android.gms").contains("new state: disabled-user"))
                waitUntil { probe.request("snapshot").getInt("gms") == ConnectionResult.SERVICE_DISABLED }
                val unavailable = probe.request("start-background")
                assertStartFailure(unavailable, "ProviderUnavailable")
                assertEquals(ConnectionResult.SERVICE_DISABLED, unavailable.getInt("platformCode"))
                assertTrue(shell("pm enable --user 0 com.google.android.gms").contains("new state: enabled"))
                waitUntil { probe.request("snapshot").getInt("gms") == ConnectionResult.SUCCESS }
                assertEquals("Started", probe.request("start-main").getString("result"))
                probe.request("stop"); probe.stopped()
                // Real user0 absence, not an injected error or just a disabled package.
                // The system image copy remains available for owned local restoration.
                assertTrue(shell("pm disable-user --user 0 com.google.android.gms").contains("new state: disabled-user"))
                assertEquals("Success", shell("pm uninstall --user 0 com.google.android.gms").trim())
                waitUntil { !probe.request("snapshot").getBoolean("gmsInstalled") }
                val missing = probe.request("start-background")
                assertFalse(missing.getBoolean("gmsInstalled"))
                assertNotEquals(ConnectionResult.SUCCESS, missing.getInt("gms"))
                assertStartFailure(missing, "ProviderUnavailable")
                assertTrue(missing.containsKey("platformCode"))
                assertEquals(missing.getInt("gms"), missing.getInt("platformCode"),
                    "Retain the actual GMS status; do not invent a missing/updating code")
                assertTrue(shell("cmd package install-existing --user 0 com.google.android.gms").contains("installed for user: 0"))
                assertTrue(shell("pm enable --user 0 com.google.android.gms").contains("new state: enabled"))
                waitUntil { val restored = probe.request("snapshot"); restored.getBoolean("gmsInstalled") && restored.getInt("gms") == ConnectionResult.SUCCESS }
                assertEquals("Started", probe.request("start-main").getString("result"))
                probe.request("stop"); probe.stopped()
                assertEquals("", shell("cmd location set-location-enabled false").trim())
                waitUntil { !probe.request("snapshot").getBoolean("settings") }
                val settings = probe.request("start-background")
                assertStartFailure(settings, "ProviderUnavailable")
                assertFalse(settings.containsKey("platformCode"), "Never invent a GMS status for system settings")
                assertEquals("", shell("cmd location set-location-enabled true").trim())
                waitUntil { probe.request("snapshot").getBoolean("settings") }
                assertEquals("Started", probe.request("start-main").getString("result"))
                probe.request("stop"); probe.stopped()
                assertNull(probe.request("snapshot").getString("cleanup"))
            } finally {
                try {
                    assertTrue(shell("cmd package install-existing --user 0 com.google.android.gms").contains("installed for user: 0"))
                } finally {
                    try { assertTrue(shell("pm enable --user 0 com.google.android.gms").contains("new state: enabled")) }
                    finally { assertEquals("", shell("cmd location set-location-enabled true").trim()) }
                }
                waitUntil { val restored = probe.request("snapshot"); restored.getBoolean("gmsInstalled") &&
                    restored.getInt("gms") == ConnectionResult.SUCCESS && restored.getBoolean("settings") }
            }
        }
    }

    private fun ownedProbe(test: (OwnedGeoProbe) -> Unit) {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedGeoProbe"),
            "Prerequisite mutation requires the explicitly owned disposable fixture")
        assertEquals(35, Build.VERSION.SDK_INT)
        assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"), "Never mutate a physical/personal device")
        val reporterPid = Process.myPid()
        val probe = OwnedGeoProbe() // Signature/UID/package ownership checked before mutation.
        try {
            resetProbePermissions()
            probe.connect()
            test(probe)
        } finally {
            try { probe.close() }
            finally { resetProbePermissions(); assertEquals(reporterPid, Process.myPid()) }
        }
    }

    private fun resetProbePermissions() {
        val permissions = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        for (permission in permissions) {
            if (context.packageManager.checkPermission(permission, OwnedGeoProbe.PACKAGE) == PackageManager.PERMISSION_GRANTED) {
                instrumentation.uiAutomation.revokeRuntimePermission(OwnedGeoProbe.PACKAGE, permission)
            }
        }
        for (permission in permissions) {
            waitUntil { context.packageManager.checkPermission(permission, OwnedGeoProbe.PACKAGE) == PackageManager.PERMISSION_DENIED }
        }
    }

    private fun grantProbe(precise: Boolean) {
        val automation: UiAutomation = instrumentation.uiAutomation
        automation.grantRuntimePermission(OwnedGeoProbe.PACKAGE, Manifest.permission.ACCESS_COARSE_LOCATION)
        if (precise) automation.grantRuntimePermission(OwnedGeoProbe.PACKAGE, Manifest.permission.ACCESS_FINE_LOCATION)
        waitUntil { context.packageManager.checkPermission(Manifest.permission.ACCESS_COARSE_LOCATION, OwnedGeoProbe.PACKAGE) == PackageManager.PERMISSION_GRANTED }
        val fine = if (precise) PackageManager.PERMISSION_GRANTED else PackageManager.PERMISSION_DENIED
        waitUntil { context.packageManager.checkPermission(Manifest.permission.ACCESS_FINE_LOCATION, OwnedGeoProbe.PACKAGE) == fine }
    }

    private fun assertStartFailure(result: Bundle, reason: String) {
        assertEquals("Failed", result.getString("result")); assertEquals(reason, result.getString("reason"))
        assertEquals(if (reason == "NotBound") "Unbound" else "Failed", result.getString("phase"))
    }

    private fun shell(command: String): String {
        require(command in setOf("pm disable-user --user 0 com.google.android.gms", "pm enable --user 0 com.google.android.gms",
            "pm uninstall --user 0 com.google.android.gms", "cmd package install-existing --user 0 com.google.android.gms",
            "cmd location set-location-enabled false", "cmd location set-location-enabled true"))
        return android.os.ParcelFileDescriptor.AutoCloseInputStream(instrumentation.uiAutomation.executeShellCommand(command)).use {
            val bytes = it.readNBytes(4097)
            check(bytes.size <= 4096) { "Native prerequisite command exceeded its diagnostic bound" }
            String(bytes, Charsets.UTF_8)
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
