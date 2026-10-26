// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import platform.Foundation.NSThread
import platform.darwin.dispatch_async
import platform.darwin.dispatch_get_main_queue

/** Existing custom helpers remain source-compatible. Status reads must be passive. */
interface PermissionHelper {
    fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit)
    @OptIn(ExperimentalPermissionsApi::class)
    fun getPermissionStatus(onPermissionResult: (PermissionStatus) -> Unit)
}

/** Additive richer observation contract; no third sealed PermissionStatus case is added. */
@OptIn(ExperimentalPermissionsApi::class)
interface PermissionSnapshotHelper : PermissionHelper {
    fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit)
    override fun getPermissionStatus(onPermissionResult: (PermissionStatus) -> Unit) =
        getPermissionSnapshot { onPermissionResult(it.status) }
}

/** Optional ownership hooks. Main-thread confined, just like the native permission APIs. */
interface PermissionLifecycleHelper {
    fun onRefresh() = Unit
    fun dispose() = Unit
}

@OptIn(ExperimentalPermissionsApi::class)
fun PermissionHelper.getPermissionSnapshotCompat(onResult: (PermissionSnapshot) -> Unit) {
    if (this is PermissionSnapshotHelper) getPermissionSnapshot(onResult)
    else getPermissionStatus { status ->
        onResult(PermissionSnapshot(status, PermissionDetails(
            availability = PermissionAvailability.Available,
            access = if (status.isGranted) PermissionAccess.Full else PermissionAccess.Unknown,
            requestability = if (status.shouldShowRationale) PermissionRequestability.SettingsOnly
                else PermissionRequestability.Unknown,
        )))
    }
}

@OptIn(ExperimentalPermissionsApi::class)
fun PermissionHelper.handleLaunchPermissionRequest(
    onPermissionResult: (Boolean) -> Unit,
    launchPermissionRequest: () -> Unit,
) {
    getPermissionSnapshotCompat { snapshot ->
        runOnPermissionMainThread {
            when {
                snapshot.status.isGranted -> onPermissionResult(true)
                snapshot.details.requestability == PermissionRequestability.Requestable -> launchPermissionRequest()
                snapshot.details.requestability in setOf(PermissionRequestability.Unsupported,
                    PermissionRequestability.Restricted, PermissionRequestability.SettingsOnly,
                    PermissionRequestability.PrerequisiteRequired) -> onPermissionResult(false)
                snapshot.status.shouldShowRationale -> onPermissionResult(false)
                else -> launchPermissionRequest()
            }
        }
    }
}

/** Dispatch native completions before touching helper-owned state or UIKit. */
fun runOnPermissionMainThread(block: () -> Unit) {
    if (NSThread.isMainThread) block() else dispatch_async(dispatch_get_main_queue(), block)
}
