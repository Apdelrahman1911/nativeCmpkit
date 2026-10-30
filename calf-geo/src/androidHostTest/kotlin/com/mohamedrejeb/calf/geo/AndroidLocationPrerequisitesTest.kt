// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.geo

import android.os.Looper
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.Tasks
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import kotlin.test.*

/** Injected prerequisite/client boundaries; actual OS/GMS prerequisite tests are separate. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class AndroidLocationPrerequisitesTest {
    private val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build()
    private val callback = object : LocationCallback() {}

    @Test fun unavailableNativePrerequisiteDoesNotConstructOrRemoveANonexistentClient() {
        var constructed = 0
        val error = LocationTrackingError(LocationTrackingFailure.ProviderUnavailable, platformCode = 3)
        val client = DefaultAndroidLocationClient(RuntimeEnvironment.getApplication(), { error }) {
            constructed++
            FakeClient()
        }
        val thrown = assertFailsWith<AndroidLocationPrerequisiteException> { client.request(request, callback, Looper.getMainLooper()) }
        assertSame(error, thrown.error)
        assertTrue(client.remove(callback).isSuccessful)
        assertEquals(0, constructed)
    }

    @Test fun settingsFailureRetainsItsActualErrorAndRechecksBeforeSuccessfulRecovery() {
        var prerequisite: LocationTrackingError? = LocationTrackingError(LocationTrackingFailure.ProviderUnavailable,
            IllegalStateException("injected disabled location settings"))
        val native = FakeClient()
        var constructed = 0
        val client = DefaultAndroidLocationClient(RuntimeEnvironment.getApplication(), { prerequisite }) {
            constructed++; native
        }
        assertSame(prerequisite, assertFailsWith<AndroidLocationPrerequisiteException> {
            client.request(request, callback, Looper.getMainLooper())
        }.error)
        prerequisite = null
        assertTrue(client.request(request, callback, Looper.getMainLooper()).isSuccessful)
        assertTrue(client.remove(callback).isSuccessful)
        assertEquals(1, constructed)
        assertEquals(1, native.requests)
        assertEquals(1, native.removals)
    }

    @Test fun cachedClientStillRechecksPrerequisitesAndCanRemoveItsExistingSubscription() {
        var unavailable: LocationTrackingError? = null
        val native = FakeClient()
        var checks = 0
        val client = DefaultAndroidLocationClient(RuntimeEnvironment.getApplication(), { checks++; unavailable }) { native }
        client.request(request, callback, Looper.getMainLooper())
        unavailable = LocationTrackingError(LocationTrackingFailure.ProviderUnavailable, platformCode = 1)
        assertSame(unavailable, assertFailsWith<AndroidLocationPrerequisiteException> {
            client.request(request, callback, Looper.getMainLooper())
        }.error)
        assertTrue(client.remove(callback).isSuccessful)
        assertEquals(2, checks)
        assertEquals(1, native.requests)
        assertEquals(1, native.removals)
    }

    @Test fun nativeRegistrationAndRemovalFailuresRemainTheOriginalTasks() {
        val registration = Tasks.forException<Void>(SecurityException("injected TOCTOU revocation"))
        val removal = Tasks.forException<Void>(IllegalStateException("injected native removal failure"))
        val native = object : AndroidLocationClient {
            override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> = registration
            override fun remove(callback: LocationCallback): Task<Void> = removal
        }
        val client = DefaultAndroidLocationClient(RuntimeEnvironment.getApplication(), { null }) { native }
        assertSame(registration, client.request(request, callback, Looper.getMainLooper()))
        assertSame(removal, client.remove(callback))
    }

    @Test fun knownPreRegistrationFailureDoesNotRemoveARequestFromAnOlderInitializedClient() {
        var error: LocationTrackingError? = null
        val native = FakeClient()
        val client = DefaultAndroidLocationClient(RuntimeEnvironment.getApplication(), { error }) { native }
        client.request(request, callback, Looper.getMainLooper())
        client.remove(callback)
        error = LocationTrackingError(LocationTrackingFailure.ProviderUnavailable, platformCode = 3)
        var registered: LocationTrackingError? = null
        val subscription = AndroidLocationSubscription(client, request) { LocationPermissionAccuracy.Precise }
        subscription.start(object : LocationSubscriptionCallbacks {
            override fun onRegistered(error: LocationTrackingError?) { registered = error }
            override fun onLocation(fix: LocationFix) { fail("No provider request may run") }
            override fun onAvailability(available: Boolean) { fail("No provider request may run") }
            override fun onFailure(error: LocationTrackingError) { fail("Registration error must use its owning callback") }
        })
        assertSame(error, registered)
        var cleaned = false
        subscription.stop { assertNull(it); cleaned = true }
        assertTrue(cleaned)
        assertEquals(1, native.requests)
        assertEquals(1, native.removals)
    }

    private class FakeClient : AndroidLocationClient {
        var requests = 0
        var removals = 0
        override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> {
            requests++; return Tasks.forResult<Void>(null)
        }
        override fun remove(callback: LocationCallback): Task<Void> {
            removals++; return Tasks.forResult<Void>(null)
        }
    }
}
