// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import com.mohamedrejeb.calf.permissions.helper.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import platform.Foundation.NSURL
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationOpenNotificationSettingsURLString
import platform.UIKit.UIApplicationOpenSettingsURLString
import platform.UIKit.UIDevice

@Composable
internal actual fun rememberMutablePermissionState(
    permission: Permission,
    onPermissionResult: (Boolean) -> Unit,
): MutablePermissionState {
    val scope = rememberCoroutineScope()
    val callback = rememberUpdatedState(onPermissionResult)
    val state = remember(permission, scope) {
        createIOSPermissionState(permission, scope) { callback.value(it) }
    }
    BindIOSPermissionState(state)
    return state
}

@Composable
internal fun BindIOSPermissionState(state: CallbackPermissionState) {
    PermissionLifecycleCheckerEffect(state)
    DisposableEffect(state) { onDispose { state.dispose() } }
}

internal fun createIOSPermissionState(
    permission: Permission,
    scope: CoroutineScope,
    onResult: (Boolean) -> Unit,
) = CallbackPermissionState(permission, onResult, scope, Dispatchers.Main.immediate) {
    // Creation as well as queries/requests are on Main (CLLocationManager requires a run loop).
    val helper = PermissionDelegateRegistry.getDelegate(permission)
    object : PermissionBackend {
        override fun query(callback: (PermissionSnapshot) -> Unit) = helper.getPermissionSnapshotCompat(callback)
        override fun request(callback: (Boolean) -> Unit) = helper.launchPermissionRequest(callback)
        override fun onRefresh() { (helper as? PermissionLifecycleHelper)?.onRefresh() }
        override fun dispose() { (helper as? PermissionLifecycleHelper)?.dispose() }
        override fun openSettings() {
            val notification = permission.name == "Notification" || permission.name == "RemoteNotification"
            val major = UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull() ?: 0
            val url = NSURL.URLWithString(if (notification && major >= 16)
                UIApplicationOpenNotificationSettingsURLString else UIApplicationOpenSettingsURLString) ?: return
            if (UIApplication.sharedApplication.canOpenURL(url))
                UIApplication.sharedApplication.openURL(url, emptyMap<Any?, String>(), null)
        }
    }
}
