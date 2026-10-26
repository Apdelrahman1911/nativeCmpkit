// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.CoreLocation.*
import platform.Foundation.NSTimer
import platform.darwin.NSObject

internal class BackgroundLocationPermissionHelper : PermissionSnapshotHelper, PermissionLifecycleHelper {
    private val manager = CLLocationManager()
    private var pending: ((Boolean) -> Unit)? = null
    private var initial = BackgroundLocationAuthorization.Unknown
    private var timeout: NSTimer? = null
    private var outcome: PermissionRequestOutcome? = null
    private val delegate = object : NSObject(), CLLocationManagerDelegateProtocol {
        override fun locationManager(manager: CLLocationManager, didChangeAuthorizationStatus: CLAuthorizationStatus) {
            changed(authorization(didChangeAuthorizationStatus))
        }
        override fun locationManagerDidChangeAuthorization(manager: CLLocationManager) {
            changed(authorization(CLLocationManager.authorizationStatus()))
        }
    }
    init { manager.delegate = delegate }

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        if (pending != null) { onPermissionResult(false); return }
        outcome = null
        // A WhenInUse grant is explicitly requestable for Always; it is NOT permanent denial.
        handleLaunchPermissionRequest(onPermissionResult) {
            initial = authorization(CLLocationManager.authorizationStatus())
            pending = onPermissionResult
            timeout = NSTimer.scheduledTimerWithTimeInterval(60.0, repeats = false) {
                complete(false, PermissionRequestOutcome.TimedOut)
            }
            manager.requestAlwaysAuthorization()
        }
    }
    private fun changed(current: BackgroundLocationAuthorization) {
        if (pending != null && backgroundLocationIsTerminal(initial, current)) {
            val granted = current == BackgroundLocationAuthorization.Always
            complete(granted, if (granted) PermissionRequestOutcome.Granted else PermissionRequestOutcome.Denied)
        }
    }
    private fun complete(granted: Boolean, result: PermissionRequestOutcome) {
        val callback = pending ?: return
        pending = null
        timeout?.invalidate(); timeout = null
        outcome = result
        callback(granted)
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val snapshot = backgroundLocationSnapshot(authorization(CLLocationManager.authorizationStatus()))
        onResult(snapshot.copy(details = snapshot.details.copy(lastRequest = outcome)))
    }
    override fun dispose() {
        pending = null
        timeout?.invalidate(); timeout = null
        manager.delegate = null
    }
    private fun authorization(status: CLAuthorizationStatus) = when (status) {
        kCLAuthorizationStatusAuthorizedAlways -> BackgroundLocationAuthorization.Always
        kCLAuthorizationStatusAuthorizedWhenInUse -> BackgroundLocationAuthorization.WhenInUse
        kCLAuthorizationStatusNotDetermined -> BackgroundLocationAuthorization.NotDetermined
        kCLAuthorizationStatusDenied -> BackgroundLocationAuthorization.Denied
        kCLAuthorizationStatusRestricted -> BackgroundLocationAuthorization.Restricted
        else -> BackgroundLocationAuthorization.Unknown
    }
}
