// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

class NotGrantedPermissionHelper : PermissionSnapshotHelper {
    override fun getPermissionStatus(onPermissionResult: (PermissionStatus) -> Unit) =
        getPermissionSnapshot { onPermissionResult(it.status) }
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) = onPermissionResult(false)
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) = onResult(PermissionSnapshot(
        PermissionStatus.Denied(false),
        PermissionDetails(availability = PermissionAvailability.Unsupported,
            access = PermissionAccess.None, requestability = PermissionRequestability.Unsupported),
    ))
}
