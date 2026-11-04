// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext

@Composable
internal actual fun rememberMutablePermissionState(
    permission: Permission,
    onPermissionResult: (Boolean) -> Unit,
): MutablePermissionState {
    val context = LocalContext.current
    val activity = context.findActivity()
    val callback = rememberUpdatedState(onPermissionResult)
    val state = remember(permission, context, activity) {
        MutablePermissionStateImpl(permission, context, activity) { callback.value(it) }
    }
    BindPermissionState(state)
    return state
}

@Composable
internal fun BindPermissionState(state: MutablePermissionStateImpl) {
    PermissionLifecycleCheckerEffect(state)
    key(state) {
        val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
            state.onNativeResult(it)
        }
        DisposableEffect(state, launcher) {
            state.launcher = launcher
            onDispose { state.launcher = null }
        }
    }
    DisposableEffect(state) { onDispose { state.dispose() } }
}

@Stable
internal class MutablePermissionStateImpl(
    override val permission: Permission,
    private val context: Context,
    private val activity: Activity,
    private val onPermissionResult: (Boolean) -> Unit,
) : MutablePermissionState, PermissionDetailsProvider {
    private fun plan() = AndroidPermissionRequestPlan(listOf(permission), Build.VERSION.SDK_INT)
    private fun snapshot() = plan().snapshot(permission, context::checkPermission, activity::shouldShowRationale)
    private val initial = snapshot()
    override var status: PermissionStatus by mutableStateOf(initial.status)
    override var permissionDetails: PermissionDetails by mutableStateOf(initial.details)
        private set
    internal var launcher: ActivityResultLauncher<Array<String>>? = null
    private val runner = AndroidPermissionRequestRunner(
        plan = ::plan,
        granted = context::checkPermission,
        launchNative = { launcher?.launch(it) ?: error("ActivityResultLauncher cannot be null") },
        beforeResult = ::refreshPermissionStatus,
    )

    override fun launchPermissionRequest() {
        runner.launch { result ->
            val granted = result.getValue(permission)
            recordRequest(granted)
            onPermissionResult(granted)
        }
    }

    internal fun onNativeResult(result: Map<String, Boolean>) = runner.onNativeResult(result)
    internal fun dispose() = runner.dispose()

    internal fun recordRequest(granted: Boolean) {
        permissionDetails = permissionDetails.copy(lastRequest = when {
            permissionDetails.availability == PermissionAvailability.NotRequired -> PermissionRequestOutcome.NotRequired
            permissionDetails.availability == PermissionAvailability.Unsupported -> PermissionRequestOutcome.Unsupported
            granted -> PermissionRequestOutcome.Granted
            permissionDetails.requestability == PermissionRequestability.PrerequisiteRequired -> PermissionRequestOutcome.RequiresForeground
            permissionDetails.requestability == PermissionRequestability.SettingsOnly -> PermissionRequestOutcome.RequiresSettings
            else -> PermissionRequestOutcome.Denied
        })
    }

    override fun openAppSettings() {
        val intent = if (permission.name == "Notification" && Build.VERSION.SDK_INT >= 26) {
            Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).apply {
                putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
        } else {
            Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        context.startActivity(intent)
    }

    override fun refreshPermissionStatus() {
        val snapshot = snapshot()
        status = snapshot.status
        permissionDetails = snapshot.details.copy(lastRequest = permissionDetails.lastRequest)
    }
}
