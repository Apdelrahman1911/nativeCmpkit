// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions

import android.Manifest

internal actual fun registerNotificationPermission(permission: Permission) {
    AndroidPermissionRegistry.register(
        permission,
        AndroidPermissionMapping(
            permissionString = Manifest.permission.POST_NOTIFICATIONS,
            minSdkVersion = 33,
        ),
    )
}

internal actual fun registerRemoteNotificationPermission(permission: Permission) {
    // APNs is iOS-only. This intentional no-runtime-gate mapping must not rely on
    // the unsafe "unregistered means granted" fallback.
    AndroidPermissionRegistry.register(permission, AndroidPermissionMapping("", alwaysGranted = true))
}
