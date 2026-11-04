// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.key
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.platform.LocalContext

@Composable
internal actual fun rememberMutableMultiplePermissionsState(
    permissions: List<Permission>,
    onPermissionsResult: (Map<Permission, Boolean>) -> Unit,
): MultiplePermissionsState {
    val requested = permissions.distinct()
    val context = LocalContext.current
    val activity = context.findActivity()
    val callback = rememberUpdatedState(onPermissionsResult)
    val states = remember(requested, context, activity) {
        val members = mutableListOf<MutablePermissionStateImpl>()
        requested.forEach { permission ->
            members += MutablePermissionStateImpl(permission, context, activity) { granted ->
                // A single native permission may back multiple logical states.
                members.forEach { it.refreshPermissionStatus() }
                callback.value(mapOf(permission to granted))
            }
        }
        members.toList()
    }
    for (state in states) key(state.permission) { BindPermissionState(state) }
    val group = remember(states) { MutableMultiplePermissionsState(states) }
    key(group) {
        // Keep the runner stable while launcher/callback references are updated.
        val launch = remember { arrayOfNulls<(Array<String>) -> Unit>(1) }
        val runner = remember(group) {
            AndroidPermissionRequestRunner(
                plan = { AndroidPermissionRequestPlan(requested, Build.VERSION.SDK_INT) },
                granted = context::checkPermission,
                launchNative = { launch[0]?.invoke(it) ?: error("ActivityResultLauncher cannot be null") },
                beforeResult = { states.forEach { it.refreshPermissionStatus() } },
            )
        }
        val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
            runner.onNativeResult(it)
        }
        DisposableEffect(group, launcher) {
            launch[0] = { launcher.launch(it) }
            group.onLaunch = {
                runner.launch { result ->
                    states.forEach { it.recordRequest(result.getValue(it.permission)) }
                    callback.value(result)
                }
            }
            onDispose { launch[0] = null; group.onLaunch = {} }
        }
        DisposableEffect(runner) { onDispose { runner.dispose() } }
    }
    return group
}
