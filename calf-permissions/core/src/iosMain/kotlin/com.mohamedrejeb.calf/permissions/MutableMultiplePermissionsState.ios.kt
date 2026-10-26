// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.key
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Composable
internal actual fun rememberMutableMultiplePermissionsState(
    permissions: List<Permission>,
    onPermissionsResult: (Map<Permission, Boolean>) -> Unit,
): MultiplePermissionsState {
    val requested = permissions.distinct()
    val scope = rememberCoroutineScope()
    val callback = rememberUpdatedState(onPermissionsResult)
    val states = remember(requested, scope) {
        requested.map { permission ->
            createIOSPermissionState(permission, scope) { callback.value(mapOf(permission to it)) }
        }
    }
    states.forEach { state -> key(state.permission) { BindIOSPermissionState(state) } }
    val group = remember(states) { MutableMultiplePermissionsState(states) }
    val batch = remember(states) {
        val byPermission = states.associateBy { it.permission }
        PermissionBatchRequest(requested) { permission, result -> byPermission.getValue(permission).request(result) }
    }
    DisposableEffect(group, batch) {
        group.onLaunch = { scope.launch(Dispatchers.Main.immediate) { batch.launch { callback.value(it) } }; Unit }
        onDispose { group.onLaunch = {}; batch.dispose() }
    }
    return group
}
