// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.cValue
import platform.CoreBluetooth.*
import platform.Foundation.NSProcessInfo
import platform.Foundation.NSTimer
import platform.darwin.NSObject

@OptIn(ExperimentalForeignApi::class)
private fun bluetoothAuthorization(): BluetoothAuthorization {
    // The class-level authorization accessor is available from iOS 13.1. Do not
    // construct a manager merely to query old systems (that can itself prompt).
    val supported = NSProcessInfo.processInfo.isOperatingSystemAtLeastVersion(cValue {
        majorVersion = 13; minorVersion = 1; patchVersion = 0
    })
    if (!supported) return BluetoothAuthorization.Unsupported
    return when (CBManager.authorization) {
        CBManagerAuthorizationAllowedAlways -> BluetoothAuthorization.Allowed
        CBManagerAuthorizationNotDetermined -> BluetoothAuthorization.NotDetermined
        CBManagerAuthorizationDenied -> BluetoothAuthorization.Denied
        CBManagerAuthorizationRestricted -> BluetoothAuthorization.Restricted
        else -> BluetoothAuthorization.Unknown
    }
}

internal class BluetoothPermissionHelper : PermissionSnapshotHelper, PermissionLifecycleHelper {
    private var current: BluetoothRequest? = null
    private var outcome: PermissionRequestOutcome? = null
    private var disposed = false

    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) =
        onResult(bluetoothSnapshot(bluetoothAuthorization(), outcome))

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        if (disposed) return
        if (current != null) { onPermissionResult(false); return }
        outcome = null
        handleLaunchPermissionRequest(onPermissionResult) {
            val request = BluetoothRequest(AppleBluetoothProbe(), ::bluetoothAuthorization, schedule = { seconds, repeats, action ->
                val timer = NSTimer.scheduledTimerWithTimeInterval(seconds, repeats) { action() }
                val cancel: () -> Unit = { timer.invalidate() }
                cancel
            }) { completed, result ->
                if (current === completed && !disposed) {
                    current = null
                    outcome = result
                    onPermissionResult(result == PermissionRequestOutcome.Granted)
                }
            }
            current = request
            request.start()
        }
    }
    override fun dispose() {
        disposed = true
        val request = current
        current = null
        request?.cancel()
    }
}

/** Kotlin ownership stays separate from the Objective-C delegate's inheritance. */
private class AppleBluetoothProbe : BluetoothProbe {
    private var manager: CBCentralManager? = null
    private var delegate: AppleBluetoothDelegate? = null
    private var callback: (() -> Unit)? = null
    private var active = false
    private var scanning = false

    override fun start(onChange: () -> Unit) {
        active = true
        callback = onChange
        // CBCentralManager's delegate is weak; the request-owned adapter retains it.
        val ownedDelegate = AppleBluetoothDelegate(::onStateChanged)
        delegate = ownedDelegate
        val native = CBCentralManager(ownedDelegate, null)
        // A synchronous authorization callback can complete while construction runs.
        if (active && delegate === ownedDelegate) manager = native
        else { native.delegate = null; native.stopScan() }
    }
    private fun onStateChanged(central: CBCentralManager) {
        if (!active) return
        callback?.invoke()
        if (active && !scanning && central.state == CBManagerStatePoweredOn &&
            bluetoothAuthorization() == BluetoothAuthorization.NotDetermined) {
            scanning = true
            central.scanForPeripheralsWithServices(null, null)
        }
    }
    override fun stop() {
        active = false
        callback = null
        val ownedDelegate = delegate
        delegate = null
        ownedDelegate?.onChange = null // Reject queued callbacks and release the forwarding closure.
        val native = manager
        manager = null
        native?.delegate = null
        native?.stopScan()
    }
}

/** Objective-C protocol conformance only; no Kotlin probe interface on NSObject subclasses. */
private class AppleBluetoothDelegate(
    var onChange: ((CBCentralManager) -> Unit)?,
) : NSObject(), CBCentralManagerDelegateProtocol {
    override fun centralManagerDidUpdateState(central: CBCentralManager) {
        onChange?.invoke(central)
    }
}
