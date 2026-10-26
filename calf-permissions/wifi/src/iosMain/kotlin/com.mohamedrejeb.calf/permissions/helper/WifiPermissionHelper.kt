// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.Foundation.NSBundle
import platform.Foundation.NSNetService
import platform.Foundation.NSNetServiceDelegateProtocol
import platform.Foundation.NSTimer
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationState.UIApplicationStateActive
import platform.darwin.NSObject

/** Legacy Wi-Fi aliases only probe local-network access, not SSID/configuration rights. */
internal class WifiPermissionHelper : PermissionSnapshotHelper, PermissionLifecycleHelper {
    private var current: LocalNetworkRequest? = null
    private var snapshot = localNetworkSnapshot()
    private var disposed = false

    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) = onResult(snapshot)

    // iOS has no passive local-network authorization query. Never publish from remember,
    // status reads, or lifecycle refresh; invalidate the last probe instead of faking certainty.
    override fun onRefresh() { if (current == null) snapshot = localNetworkSnapshot() }

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        if (disposed) return
        if (current != null) { onPermissionResult(false); return }
        val bundle = NSBundle.mainBundle
        val failure = when {
            !localNetworkConfigurationValid(bundle.objectForInfoDictionaryKey("NSLocalNetworkUsageDescription"),
                bundle.objectForInfoDictionaryKey("NSBonjourServices")) -> PermissionRequestOutcome.ConfigurationError
            UIApplication.sharedApplication.applicationState != UIApplicationStateActive -> PermissionRequestOutcome.AppInactive
            else -> null
        }
        if (failure != null) {
            snapshot = localNetworkSnapshot(failure)
            onPermissionResult(false)
            return
        }
        val request = LocalNetworkRequest(AppleLocalNetworkProbe(), scheduleTimeout = { expired ->
            val timer = NSTimer.scheduledTimerWithTimeInterval(60.0, repeats = false) { expired() }
            val cancel: () -> Unit = { timer.invalidate() }
            cancel
        }) { completed, outcome ->
            if (current === completed && !disposed) {
                current = null // Clear native ownership BEFORE the application can reenter.
                snapshot = localNetworkSnapshot(outcome)
                onPermissionResult(outcome == PermissionRequestOutcome.Granted)
            }
        }
        current = request
        request.start()
    }
    override fun dispose() {
        disposed = true
        val request = current
        current = null
        request?.cancel()
    }
}

/** The Kotlin request adapter owns, but does not inherit from, its native delegate. */
private class AppleLocalNetworkProbe : LocalNetworkProbe {
    private var service: NSNetService? = null
    private var delegate: AppleLocalNetworkDelegate? = null

    override fun start(onResult: (PermissionRequestOutcome) -> Unit) {
        val ownedDelegate = AppleLocalNetworkDelegate(onResult)
        delegate = ownedDelegate
        val native = NSNetService(domain = "local.", type = "_lnp._tcp.", name = "nativeCmpkitLocalNetworkProbe", port = 0)
        service = native
        native.delegate = ownedDelegate
        native.publish()
    }
    override fun stop() {
        val ownedDelegate = delegate
        delegate = null
        ownedDelegate?.onResult = null // Drop late delivery before stopping the native service.
        val native = service
        service = null
        native?.delegate = null
        native?.stop()
    }
}

/** Objective-C protocol conformance is separate from the Kotlin LocalNetworkProbe interface. */
private class AppleLocalNetworkDelegate(
    var onResult: ((PermissionRequestOutcome) -> Unit)?,
) : NSObject(), NSNetServiceDelegateProtocol {
    override fun netServiceDidPublish(sender: NSNetService) {
        onResult?.invoke(PermissionRequestOutcome.Granted)
    }
    override fun netService(sender: NSNetService, didNotPublish: Map<Any?, *>) {
        onResult?.invoke(PermissionRequestOutcome.Failed)
    }
}
