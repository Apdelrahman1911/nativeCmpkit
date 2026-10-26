// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.CoreLocation.*
import platform.Foundation.NSTimer
import platform.UIKit.UIDevice
import platform.darwin.NSObject

internal class LocationPermissionHelper(private val requirePrecise: Boolean = false) : PermissionSnapshotHelper, PermissionLifecycleHelper {
    private val manager = CLLocationManager()
    private var pending: ((Boolean) -> Unit)? = null
    private var timeout: NSTimer? = null
    private var outcome: PermissionRequestOutcome? = null
    private val delegate = object : NSObject(), CLLocationManagerDelegateProtocol {
        override fun locationManager(manager: CLLocationManager, didChangeAuthorizationStatus: CLAuthorizationStatus) {
            if (foregroundLocationIsTerminal(authorization(didChangeAuthorizationStatus))) completeCurrent()
        }
        override fun locationManagerDidChangeAuthorization(manager: CLLocationManager) {
            if (foregroundLocationIsTerminal(authorization(CLLocationManager.authorizationStatus()))) completeCurrent()
        }
    }
    init { manager.delegate = delegate }

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        if (pending != null) { onPermissionResult(false); return } // State owner coalesces public overlapping calls.
        outcome = null
        handleLaunchPermissionRequest(onPermissionResult) {
            pending = onPermissionResult
            timeout = NSTimer.scheduledTimerWithTimeInterval(60.0, repeats = false) {
                complete(false, PermissionRequestOutcome.TimedOut)
            }
            manager.requestWhenInUseAuthorization()
        }
    }

    private fun completeCurrent() {
        if (pending == null) return
        getPermissionSnapshot { complete(it.status.isGranted, if (it.status.isGranted)
            PermissionRequestOutcome.Granted else PermissionRequestOutcome.Denied) }
    }
    private fun complete(granted: Boolean, result: PermissionRequestOutcome) {
        val callback = pending ?: return
        pending = null
        timeout?.invalidate(); timeout = null
        outcome = result
        callback(granted)
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val major = UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull() ?: 0
        val precise = major < 14 || manager.accuracyAuthorization == CLAccuracyAuthorization.CLAccuracyAuthorizationFullAccuracy
        val snapshot = foregroundLocationSnapshot(authorization(CLLocationManager.authorizationStatus()), precise, requirePrecise)
        onResult(snapshot.copy(details = snapshot.details.copy(lastRequest = outcome)))
    }
    override fun dispose() {
        pending = null
        timeout?.invalidate(); timeout = null
        manager.delegate = null
    }
    private fun authorization(status: CLAuthorizationStatus) = when (status) {
        kCLAuthorizationStatusAuthorizedAlways -> ForegroundLocationAuthorization.Always
        kCLAuthorizationStatusAuthorizedWhenInUse -> ForegroundLocationAuthorization.WhenInUse
        kCLAuthorizationStatusNotDetermined -> ForegroundLocationAuthorization.NotDetermined
        kCLAuthorizationStatusDenied -> ForegroundLocationAuthorization.Denied
        kCLAuthorizationStatusRestricted -> ForegroundLocationAuthorization.Restricted
        else -> ForegroundLocationAuthorization.Unknown
    }
}
