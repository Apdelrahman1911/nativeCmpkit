// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.geo

import android.content.Context
import android.content.ContextWrapper
import android.location.Location
import android.os.Looper
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.Tasks
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import org.junit.Test
import org.junit.runner.RunWith
import java.lang.ref.WeakReference
import java.util.IdentityHashMap
import kotlin.test.*

/**
 * Actual Android Looper/LifecycleRegistry/GMS Tasks/ART collection. Only the
 * injected transport completes provider Tasks: not a live GMS/GPS, Activity
 * recreation, physical-device or power-profile certification.
 */
@RunWith(AndroidJUnit4::class)
class AndroidLocationOwnershipTest {
    @Test fun nativeRebindingRestartAndTerminalCleanupReleaseOwnersDespiteRetainedCallbacks() {
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val references = mutableListOf<WeakReference<Any>>()
        val retainedCallbacks = mutableListOf<LocationCallback>()
        // A positive control stays strongly reachable while all library-owned
        // predecessors must collect. Do not silently accept an uncollected owner.
        val retainedControl = Any()
        val control = WeakReference(retainedControl)
        repeat(32) {
            instrumentation.runOnMainSync {
                references += exerciseRound(instrumentation.targetContext, retainedCallbacks)
            }
        }
        instrumentation.waitForIdleSync()
        assertEquals(32 * 5, references.size)
        assertEquals(32 * 6, retainedCallbacks.size)
        repeat(30) {
            System.gc()
            System.runFinalization()
            instrumentation.waitForIdleSync()
            if (references.all { it.get() == null }) return@repeat
            Thread.sleep(30)
        }
        assertTrue(references.all { it.get() == null },
            "Completed cleanup must release tracker, caller context and all three lifecycle owners, even with obsolete callbacks retained")
        assertSame(retainedControl, control.get(), "The positive retention control must remain live")
        assertEquals(32 * 6, retainedCallbacks.size, "Do not drop obsolete callback roots to manufacture a collection pass")
    }

    private fun exerciseRound(context: Context, retainedCallbacks: MutableList<LocationCallback>): List<WeakReference<Any>> {
        assertSame(Looper.getMainLooper(), Looper.myLooper())
        val callerContext = ContextWrapper(context.applicationContext)
        val client = RetainingClient(retainedCallbacks)
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build()
        val tracker = LocationTracker { application ->
            assertSame(context.applicationContext, application)
            AndroidLocationTrackingBackend(application, request, client) { LocationPermissionAccuracy.Approximate }
        }
        val ownerA = Owner().apply { foreground() }
        val ownerB = Owner().apply { foreground() }
        val ownerC = Owner().apply { foreground() }
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
        fun start() {
            var result: LocationStartResult? = null
            val job = scope.launch { result = tracker.startTrackingWithResult() }
            assertTrue(job.isCompleted, "Actual already-completed native Task must complete start on Main.immediate")
            assertEquals(LocationStartResult.Started, result)
        }
        try {
            tracker.bind(ownerA.lifecycle, callerContext)
            start()
            val oldCallback = client.requested.single()
            tracker.bind(ownerB.lifecycle, callerContext)
            assertEquals(0, ownerA.registry.observerCount)
            assertEquals(1, ownerB.registry.observerCount)
            assertEquals(LocationTrackingPhase.Tracking, tracker.snapshotState.value.phase)
            val second = client.requested.last()
            assertNotSame(oldCallback, second)
            assertEquals(1, client.removed[oldCallback])
            tracker.bind(ownerB.lifecycle, callerContext) // Same bind is idempotent.
            assertEquals(2, client.requested.size)
            ownerA.destroy()
            assertEquals(0, ownerA.registry.observerCount)
            assertEquals(1, ownerB.registry.observerCount)
            assertNull(client.removed[second], "Destroying the detached predecessor must not stop B")
            val active = tracker.snapshotState.value
            oldCallback.onLocationResult(fix(90.0))
            assertSame(active, tracker.snapshotState.value)
            repeat(3) {
                val previous = client.requested.last()
                tracker.stopTracking()
                assertEquals(1, client.removed[previous])
                val stopped = tracker.snapshotState.value
                previous.onLocationResult(fix(80.0))
                assertSame(stopped, tracker.snapshotState.value)
                start()
                assertNotSame(previous, client.requested.last())
            }
            val finalB = client.requested.last()
            ownerB.destroy()
            assertEquals(0, ownerB.registry.observerCount)
            assertEquals(1, client.removed[finalB], "Destroy B removes only its current callback exactly once")
            assertEquals(LocationTrackingPhase.Unbound, tracker.snapshotState.value.phase)
            tracker.bind(ownerC.lifecycle, callerContext)
            assertEquals(LocationTrackingPhase.Idle, tracker.snapshotState.value.phase)
            assertEquals(5, client.requested.size, "Destruction/rebind must not silently auto-start")
            start()
            client.requested.last().onLocationResult(fix(5.0))
            assertEquals(LatLng(5.0, 6.0), tracker.fixState.value?.coordinates)
            tracker.close()
            assertEquals(0, ownerC.registry.observerCount)
            assertEquals(LocationTrackingPhase.Closed, tracker.snapshotState.value.phase)
            val closed = tracker.snapshotState.value
            client.requested.forEach { it.onLocationResult(fix(70.0)) }
            tracker.close()
            assertSame(closed, tracker.snapshotState.value)
            assertEquals(6, client.requested.size)
            assertEquals(6, client.removed.size)
            assertTrue(client.removed.values.all { it == 1 })
            return listOf(tracker, callerContext, ownerA, ownerB, ownerC).map { WeakReference<Any>(it) }
        } finally {
            tracker.close()
            scope.cancel()
        }
    }

    private class Owner : LifecycleOwner {
        val registry = LifecycleRegistry(this)
        override val lifecycle: Lifecycle = registry
        fun foreground() { registry.currentState = Lifecycle.State.RESUMED }
        fun destroy() { registry.currentState = Lifecycle.State.DESTROYED }
    }

    private class RetainingClient(private val retainedCallbacks: MutableList<LocationCallback>) : AndroidLocationClient {
        val requested = mutableListOf<LocationCallback>()
        val removed = IdentityHashMap<LocationCallback, Int>()
        override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> {
            assertSame(Looper.getMainLooper(), looper)
            assertSame(looper, Looper.myLooper())
            requested += callback
            retainedCallbacks += callback
            return Tasks.forResult<Void>(null)
        }
        override fun remove(callback: LocationCallback): Task<Void> {
            assertSame(Looper.getMainLooper(), Looper.myLooper())
            removed[callback] = (removed[callback] ?: 0) + 1
            return Tasks.forResult<Void>(null)
        }
    }

    private fun fix(latitude: Double): LocationResult = LocationResult.create(listOf(Location("injected-provider").apply {
        this.latitude = latitude
        longitude = 6.0
        time = 1_700_000_000_000L
    }))
}
