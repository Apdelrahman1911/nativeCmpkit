package com.mohamedrejeb.calf.geo

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Handler
import android.os.Looper
import androidx.core.content.ContextCompat
import androidx.core.location.LocationManagerCompat
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.GoogleApiAvailabilityLight
import com.google.android.gms.common.api.ApiException
import com.google.android.gms.location.LocationAvailability
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.Tasks
import java.util.concurrent.CancellationException
import java.util.concurrent.Executor

/** Narrow injectable provider boundary; the default implementation uses real Play Services. */
internal interface AndroidLocationClient {
    fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void>
    fun remove(callback: LocationCallback): Task<Void>
}

internal class AndroidLocationTrackingBackend(
    context: Context,
    private val request: LocationRequest,
    client: AndroidLocationClient? = null,
    private val permissionReader: () -> LocationPermissionAccuracy? = { context.locationPermissionAccuracy() },
) : LocationTrackingBackend {
    private val nativeClient by lazy(LazyThreadSafetyMode.NONE) {
        client ?: DefaultAndroidLocationClient(context)
    }

    override fun permissionAccuracy(): LocationPermissionAccuracy? = permissionReader()
    override fun createSubscription(): LocationSubscription = AndroidLocationSubscription(nativeClient, request, permissionReader)
}

/** Check actual foreground prerequisites on every start, never prompt or enable them. */
internal class DefaultAndroidLocationClient(
    context: Context,
    private val prerequisite: () -> LocationTrackingError? = { context.locationPrerequisiteError() },
    private val factory: () -> AndroidLocationClient = {
        object : AndroidLocationClient {
            private val delegate = LocationServices.getFusedLocationProviderClient(context)

            @SuppressLint("MissingPermission") // The subscription rechecks permissions; TOCTOU Task/security failures stay observable.
            override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> =
                delegate.requestLocationUpdates(request, callback, looper)

            override fun remove(callback: LocationCallback): Task<Void> = delegate.removeLocationUpdates(callback)
        }
    },
) : AndroidLocationClient {
    private var delegate: AndroidLocationClient? = null

    override fun request(request: LocationRequest, callback: LocationCallback, looper: Looper): Task<Void> {
        prerequisite()?.let { throw AndroidLocationPrerequisiteException(it) }
        val active = delegate ?: factory().also { delegate = it }
        return active.request(request, callback, looper)
    }

    // A failed prerequisite never constructed/registered a native client. Cleanup
    // must not initialize Play Services just to remove that nonexistent request.
    override fun remove(callback: LocationCallback): Task<Void> =
        delegate?.remove(callback) ?: Tasks.forResult<Void>(null)
}

internal class AndroidLocationPrerequisiteException(val error: LocationTrackingError) :
    Exception("Android foreground location prerequisites unavailable", error.cause)

internal fun Context.locationPrerequisiteError(): LocationTrackingError? {
    val status = GoogleApiAvailabilityLight.getInstance().isGooglePlayServicesAvailable(this)
    if (status != ConnectionResult.SUCCESS) {
        return LocationTrackingError(LocationTrackingFailure.ProviderUnavailable, platformCode = status)
    }
    val manager = getSystemService(Context.LOCATION_SERVICE) as? LocationManager
    if (manager == null || !LocationManagerCompat.isLocationEnabled(manager)) {
        return LocationTrackingError(LocationTrackingFailure.ProviderUnavailable,
            IllegalStateException("Android system location services are disabled or unavailable"))
    }
    return null
}

private fun Context.locationPermissionAccuracy(): LocationPermissionAccuracy? = when {
    ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED -> LocationPermissionAccuracy.Precise
    ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED -> LocationPermissionAccuracy.Approximate
    else -> null
}

/** All GMS completions and location callbacks are delivered on the explicit main Looper. */
internal class AndroidLocationSubscription(
    private val client: AndroidLocationClient,
    private val request: LocationRequest,
    private val permissionReader: () -> LocationPermissionAccuracy?,
) : LocationSubscription {
    private val handler = Handler(Looper.getMainLooper())
    private val executor = Executor { command ->
        if (Looper.myLooper() == Looper.getMainLooper()) command.run() else handler.post(command)
    }
    private var callbacks: LocationSubscriptionCallbacks? = null
    private var started = false
    private var requestIssued = false
    private var registrationFinished = false
    private var stopping = false
    private var removalInFlight = false
    private var removalFinished = false
    private var removalError: LocationTrackingError? = null
    private val removalCompletions = mutableListOf<(LocationTrackingError?) -> Unit>()

    private val callback = object : LocationCallback() {
        override fun onLocationResult(result: LocationResult) {
            if (stopping) return
            val location = result.lastLocation ?: return
            val fix = location.toLocationFix()
            if (fix == null) callbacks?.onFailure(LocationTrackingError(LocationTrackingFailure.InvalidLocation))
            else callbacks?.onLocation(fix)
        }

        override fun onLocationAvailability(availability: LocationAvailability) {
            if (!stopping) callbacks?.onAvailability(availability.isLocationAvailable)
        }
    }

    override fun start(callbacks: LocationSubscriptionCallbacks) {
        check(!started) { "A native location subscription may be registered only once" }
        started = true
        this.callbacks = callbacks
        try {
            if (permissionReader() == null) {
                registrationFinished = true
                callbacks.onRegistered(LocationTrackingError(LocationTrackingFailure.PermissionDenied))
                return
            }
            requestIssued = true
            client.request(request, callback, Looper.getMainLooper()).addOnCompleteListener(executor) { task ->
                registrationFinished = true
                if (stopping) {
                    // A prior removal may have completed before registration. Remove again,
                    // ordered after the terminal registration signal, to close that race.
                    if (!removalInFlight) removeAfterRegistration(finalPass = true)
                } else {
                    this.callbacks?.onRegistered(task.registrationError())
                }
            }
        } catch (failure: Exception) {
            // This typed default-client guard runs before any provider API call,
            // even if an older subscription already initialized that client.
            if (failure is AndroidLocationPrerequisiteException) requestIssued = false
            registrationFinished = true
            if (stopping) {
                if (!removalInFlight) removeAfterRegistration(finalPass = true)
            } else this.callbacks?.onRegistered(failure.locationError())
        }
    }

    override fun stop(onComplete: (LocationTrackingError?) -> Unit) {
        if (removalFinished && removalError == null) {
            onComplete(null)
            return
        }
        removalCompletions += onComplete
        if (stopping && !removalFinished) return
        stopping = true
        callbacks = null // Release the controller/session while native cleanup is pending.
        removalFinished = false
        if (!requestIssued) finishRemoval(null)
        else removeAfterRegistration(finalPass = registrationFinished)
    }

    private fun removeAfterRegistration(finalPass: Boolean) {
        if (removalInFlight) return
        removalInFlight = true
        try {
            client.remove(callback).addOnCompleteListener(executor) { task ->
                removalInFlight = false
                if (finalPass) {
                    finishRemoval(task.removalError())
                } else if (registrationFinished) {
                    removeAfterRegistration(finalPass = true)
                }
                // Otherwise wait for registration completion. We never report removal
                // success while a still-pending request could install a subscription.
            }
        } catch (failure: Exception) {
            removalInFlight = false
            if (finalPass) finishRemoval(LocationTrackingError(LocationTrackingFailure.RemovalFailed, failure))
            else if (registrationFinished) removeAfterRegistration(finalPass = true)
        }
    }

    private fun finishRemoval(error: LocationTrackingError?) {
        removalFinished = true
        removalError = error
        val completions = removalCompletions.toList()
        removalCompletions.clear()
        completions.forEach { it(error) }
    }
}

private fun Task<Void>.registrationError(): LocationTrackingError? = when {
    isCanceled -> LocationTrackingError(LocationTrackingFailure.ProviderError, CancellationException("Location registration cancelled by provider"))
    isSuccessful -> null
    else -> (exception ?: IllegalStateException("Location registration failed without an exception")).locationError()
}

private fun Task<Void>.removalError(): LocationTrackingError? = when {
    isSuccessful -> null
    else -> LocationTrackingError(
        LocationTrackingFailure.RemovalFailed,
        exception ?: CancellationException("Location removal cancelled by provider"),
    )
}

private fun Exception.locationError(): LocationTrackingError = when (this) {
    is AndroidLocationPrerequisiteException -> error
    is SecurityException -> LocationTrackingError(LocationTrackingFailure.PermissionDenied, this)
    is ApiException -> LocationTrackingError(LocationTrackingFailure.ProviderUnavailable, this, statusCode)
    else -> LocationTrackingError(LocationTrackingFailure.ProviderError, this)
}
