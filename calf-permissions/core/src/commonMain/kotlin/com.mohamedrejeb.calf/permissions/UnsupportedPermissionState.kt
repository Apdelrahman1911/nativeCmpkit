@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue

/** No blanket desktop grant: macOS TCC and browser permission services are distinct. */
@Stable
internal class UnsupportedPermissionState(
    override val permission: Permission,
    private val onResult: (Boolean) -> Unit,
) : MutablePermissionState, PermissionDetailsProvider {
    override var status: PermissionStatus by mutableStateOf(PermissionStatus.Denied(false))
    override var permissionDetails: PermissionDetails by mutableStateOf(PermissionDetails(
        availability = PermissionAvailability.Unsupported,
        access = PermissionAccess.None,
        requestability = PermissionRequestability.Unsupported,
    ))
        private set

    override fun launchPermissionRequest() {
        prepareRequestResult()
        onResult(false)
    }
    internal fun prepareRequestResult() {
        refreshPermissionStatus()
        permissionDetails = permissionDetails.copy(lastRequest = PermissionRequestOutcome.Unsupported)
    }
    override fun openAppSettings() = Unit // There is no portable OS/browser settings route.
    override fun refreshPermissionStatus() { status = PermissionStatus.Denied(false) }
}

@Composable
internal fun rememberUnsupportedPermissionState(
    permission: Permission,
    onResult: (Boolean) -> Unit,
): UnsupportedPermissionState {
    val callback = rememberUpdatedState(onResult)
    return remember(permission) { UnsupportedPermissionState(permission) { callback.value(it) } }
}

@Composable
internal fun rememberUnsupportedMultiplePermissionsState(
    permissions: List<Permission>,
    onResult: (Map<Permission, Boolean>) -> Unit,
): MultiplePermissionsState {
    val callback = rememberUpdatedState(onResult)
    val requested = permissions.distinct()
    val states = requested.map { permission ->
        key(permission) {
            rememberUnsupportedPermissionState(permission) { callback.value(mapOf(permission to it)) }
        }
    }
    return remember(states) {
        MutableMultiplePermissionsState(states).apply {
            onLaunch = {
                states.forEach { it.prepareRequestResult() }
                callback.value(requested.associateWith { false })
            }
        }
    }
}
