// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.getValue

@ExperimentalPermissionsApi
@Composable
internal expect fun rememberMutableMultiplePermissionsState(
    permissions: List<Permission>,
    onPermissionsResult: (Map<Permission, Boolean>) -> Unit = {},
): MultiplePermissionsState

/** Shared aggregation only; native request ownership stays in the platform factory. */
@ExperimentalPermissionsApi
@Stable
internal class MutableMultiplePermissionsState(
    private val mutablePermissions: List<MutablePermissionState>,
) : MultiplePermissionsState {
    override val permissions: List<PermissionState> = mutablePermissions
    override val revokedPermissions: List<PermissionState> by derivedStateOf {
        permissions.filter { !it.status.isGranted }
    }
    override val allPermissionsGranted: Boolean by derivedStateOf {
        permissions.all { it.status.isGranted }
    }
    override val shouldShowRationale: Boolean by derivedStateOf {
        permissions.any { it.status.shouldShowRationale }
    }

    internal var onLaunch: () -> Unit = { error("Permission request owner is not attached") }
    override fun launchMultiplePermissionRequest() = onLaunch()

    internal fun updatePermissionsStatus(permissionsStatus: Map<Permission, Boolean>) {
        // Refresh every alias/duplicate, not just the first matching state.
        mutablePermissions.filter { it.permission in permissionsStatus }.forEach {
            it.refreshPermissionStatus()
        }
    }
}
