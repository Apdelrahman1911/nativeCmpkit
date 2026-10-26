// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

class GrantedPermissionHelper : PermissionSnapshotHelper {
    override fun getPermissionStatus(onPermissionResult: (PermissionStatus) -> Unit) =
        getPermissionSnapshot { onPermissionResult(it.status) }
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) = onPermissionResult(true)
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) = onResult(PermissionSnapshot(
        PermissionStatus.Granted,
        PermissionDetails(availability = PermissionAvailability.NotRequired,
            access = PermissionAccess.Unknown, requestability = PermissionRequestability.NotRequired),
    ))
}
