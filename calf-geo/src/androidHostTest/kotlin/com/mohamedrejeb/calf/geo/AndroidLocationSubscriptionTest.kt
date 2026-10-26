package com.mohamedrejeb.calf.geo

import android.location.Location as AndroidLocation
import android.Manifest
import android.os.Looper
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.common.api.Status
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.TaskCompletionSource
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.annotation.LooperMode
import java.util.concurrent.CancellationException
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

/** Real GMS Tasks, callbacks, LocationResult and Android main Looper; only the provider is injected. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
@LooperMode(LooperMode.Mode.PAUSED)
class AndroidLocationSubscriptionTest {
    @Test fun registrationWaitsForRealTaskAndUsesExplicitMainLooper() {
        val (subscription, client, callbacks) = setup()
        assertTrue(callbacks.registered.isEmpty())
        assertSame(Looper.getMainLooper(), client.requests.single().looper)
        client.requests.single().completion.setResult(null)
        idle()
        assertEquals(listOf<LocationTrackingError?>(null), callbacks.registered)
        assertSame(Looper.getMainLooper(), callbacks.registrationLooper)
        client.requests.single().callback.onLocationResult(result(3.0))
        assertEquals(LatLng(3.0, 0.0), callbacks.fixes.single().coordinates)
        subscription.stop { }
    }

    @Test fun permissionDeniedAtNativeBoundaryDoesNotIssueRequest() {
        val client = TestAndroidLocationClient()
        val callbacks = RecordedCallbacks()
        val subscription = AndroidLocationSubscription(client, request()) { null }
        subscription.start(callbacks)
        assertEquals(LocationTrackingFailure.PermissionDenied, callbacks.registered.single()?.reason)
        assertTrue(client.requests.isEmpty())
        subscription.stop { assertNull(it) }
        assertTrue(client.removals.isEmpty())
    }

    @Test fun defaultPermissionReaderSeparatesDeniedCoarseAndFineGrants() {
        val application = RuntimeEnvironment.getApplication()
        val permissions = shadowOf(application)
        permissions.denyPermissions(Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION)
        val backend = AndroidLocationTrackingBackend(application, request(), TestAndroidLocationClient())
        assertNull(backend.permissionAccuracy())
        permissions.grantPermissions(Manifest.permission.ACCESS_COARSE_LOCATION)
        assertEquals(LocationPermissionAccuracy.Approximate, backend.permissionAccuracy())
        permissions.grantPermissions(Manifest.permission.ACCESS_FINE_LOCATION)
        assertEquals(LocationPermissionAccuracy.Precise, backend.permissionAccuracy())
        permissions.denyPermissions(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        assertNull(backend.permissionAccuracy())
    }

    @Test fun synchronousSecurityFailureIsMappedRatherThanThrown() {
        val client = TestAndroidLocationClient().apply { requestFailure = SecurityException("revoked") }
        val (_, _, callbacks) = setup(client)
        assertEquals(LocationTrackingFailure.PermissionDenied, callbacks.registered.single()?.reason)
    }

    @Test fun asynchronousSecurityAndApiFailuresCarryUsefulReasons() {
        val (_, client, callbacks) = setup()
        client.requests.single().completion.setException(SecurityException("revoked"))
        idle()
        assertEquals(LocationTrackingFailure.PermissionDenied, callbacks.registered.single()?.reason)
        val (_, second, otherCallbacks) = setup()
        second.requests.single().completion.setException(ApiException(Status(17)))
        idle()
        assertEquals(LocationTrackingFailure.ProviderUnavailable, otherCallbacks.registered.single()?.reason)
        assertEquals(17, otherCallbacks.registered.single()?.platformCode)
    }

    @Test fun providerTaskCancellationIsNotRegistrationSuccess() {
        val cancellation = CancellationTokenSource()
        val client = TestAndroidLocationClient().apply { nextRegistration = TaskCompletionSource(cancellation.token) }
        val (_, _, callbacks) = setup(client)
        cancellation.cancel()
        idle()
        val failure = callbacks.registered.single()
        assertEquals(LocationTrackingFailure.ProviderError, failure?.reason)
        assertIs<CancellationException>(failure?.cause)
    }

    @Test fun backgroundTaskCompletionIsMarshalledToMain() {
        val (_, client, callbacks) = setup()
        Thread { client.requests.single().completion.setResult(null) }.apply { start(); join() }
        assertTrue(callbacks.registered.isEmpty())
        idle()
        assertEquals(listOf<LocationTrackingError?>(null), callbacks.registered)
        assertSame(Looper.getMainLooper(), callbacks.registrationLooper)
    }

    @Test fun nullLastLocationDoesNotInventAZeroFix() {
        val (_, client, callbacks) = setup()
        client.requests.single().callback.onLocationResult(LocationResult.create(emptyList()))
        assertTrue(callbacks.fixes.isEmpty())
    }

    @Test fun stopBeforeRegistrationCleansAgainAfterLateSuccess() {
        val (subscription, client, callbacks) = setup()
        val stops = mutableListOf<LocationTrackingError?>()
        subscription.stop(stops::add)
        assertEquals(1, client.removals.size)
        client.removals[0].completion.setResult(null)
        idle()
        assertTrue(stops.isEmpty())
        client.requests.single().completion.setResult(null)
        idle()
        assertEquals(2, client.removals.size)
        assertTrue(stops.isEmpty())
        client.removals[1].completion.setResult(null)
        idle()
        assertEquals(listOf<LocationTrackingError?>(null), stops)
        assertTrue(callbacks.registered.isEmpty())
        client.requests.single().callback.onLocationResult(result(8.0))
        assertTrue(callbacks.fixes.isEmpty())
        assertTrue(client.removals.all { it.callback === client.requests.single().callback })
    }

    @Test fun registrationCompletingDuringRemovalStillRequiresFinalRemovalPass() {
        val (subscription, client, _) = setup()
        val stops = mutableListOf<LocationTrackingError?>()
        subscription.stop(stops::add)
        client.requests.single().completion.setResult(null)
        idle()
        assertEquals(1, client.removals.size)
        client.removals[0].completion.setResult(null)
        idle()
        assertEquals(2, client.removals.size)
        client.removals[1].completion.setResult(null)
        idle()
        assertEquals(listOf<LocationTrackingError?>(null), stops)
    }

    @Test fun failedPendingRegistrationStillCompletesRequestedCleanup() {
        val (subscription, client, callbacks) = setup()
        val stops = mutableListOf<LocationTrackingError?>()
        subscription.stop(stops::add)
        client.requests.single().completion.setException(IllegalStateException("provider gone"))
        client.removals[0].completion.setResult(null)
        idle()
        client.removals[1].completion.setResult(null)
        idle()
        assertEquals(listOf<LocationTrackingError?>(null), stops)
        assertTrue(callbacks.registered.isEmpty())
    }

    @Test fun removalFailureIsReportedAndExplicitRetryCanSucceed() {
        val (subscription, client, _) = setup()
        client.requests.single().completion.setResult(null)
        idle()
        val stops = mutableListOf<LocationTrackingError?>()
        subscription.stop(stops::add)
        client.removals[0].completion.setException(IllegalStateException("temporary removal failure"))
        idle()
        assertEquals(LocationTrackingFailure.RemovalFailed, stops.single()?.reason)
        subscription.stop(stops::add)
        assertEquals(2, client.removals.size)
        client.removals[1].completion.setResult(null)
        idle()
        assertEquals(2, stops.size)
        assertNull(stops.last())
    }

    @Test fun synchronousRemovalFailureIsNotSilentlyIgnored() {
        val (subscription, client, _) = setup()
        client.requests.single().completion.setResult(null)
        idle()
        client.removeFailure = IllegalStateException("provider disconnected")
        var error: LocationTrackingError? = null
        subscription.stop { error = it }
        assertEquals(LocationTrackingFailure.RemovalFailed, error?.reason)
    }

    @Test fun repeatedStopSharesOneRemovalAndCompletesEveryWaiterOnce() {
        val (subscription, client, _) = setup()
        client.requests.single().completion.setResult(null)
        idle()
        val stops = mutableListOf<LocationTrackingError?>()
        subscription.stop(stops::add)
        subscription.stop(stops::add)
        assertEquals(1, client.removals.size)
        client.removals[0].completion.setResult(null)
        idle()
        assertEquals(listOf<LocationTrackingError?>(null, null), stops)
        subscription.stop(stops::add)
        assertEquals(listOf<LocationTrackingError?>(null, null, null), stops)
        assertEquals(1, client.removals.size)
    }

    private fun setup(client: TestAndroidLocationClient = TestAndroidLocationClient()): Triple<AndroidLocationSubscription, TestAndroidLocationClient, RecordedCallbacks> {
        val callbacks = RecordedCallbacks()
        val subscription = AndroidLocationSubscription(client, request()) { LocationPermissionAccuracy.Precise }
        subscription.start(callbacks)
        return Triple(subscription, client, callbacks)
    }

    private fun request() = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 1000L).build()
    private fun result(latitude: Double) = LocationResult.create(listOf(AndroidLocation("test-provider").apply {
        this.latitude = latitude
        longitude = 0.0
    }))
    private fun idle() = shadowOf(Looper.getMainLooper()).idle()
}

internal class TestAndroidLocationClient : AndroidLocationClient {
    data class Request(val callback: LocationCallback, val looper: Looper, val completion: TaskCompletionSource<Void>)
    data class Removal(val callback: LocationCallback, val completion: TaskCompletionSource<Void>)
    val requests = mutableListOf<Request>()
    val removals = mutableListOf<Removal>()
    var nextRegistration: TaskCompletionSource<Void>? = null
    var requestFailure: Exception? = null
    var removeFailure: Exception? = null
    override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> {
        requestFailure?.let { throw it }
        val completion = nextRegistration ?: TaskCompletionSource<Void>()
        nextRegistration = null
        requests += Request(callback, looper, completion)
        return completion.task
    }
    override fun remove(callback: LocationCallback): Task<Void> {
        removeFailure?.let { throw it }
        val completion = TaskCompletionSource<Void>()
        removals += Removal(callback, completion)
        return completion.task
    }
}

private class RecordedCallbacks : LocationSubscriptionCallbacks {
    val registered = mutableListOf<LocationTrackingError?>()
    val fixes = mutableListOf<LocationFix>()
    val errors = mutableListOf<LocationTrackingError>()
    var registrationLooper: Looper? = null
    override fun onRegistered(error: LocationTrackingError?) {
        registrationLooper = Looper.myLooper()
        registered += error
    }
    override fun onLocation(fix: LocationFix) { fixes += fix }
    override fun onAvailability(available: Boolean) = Unit
    override fun onFailure(error: LocationTrackingError) { errors += error }
}
