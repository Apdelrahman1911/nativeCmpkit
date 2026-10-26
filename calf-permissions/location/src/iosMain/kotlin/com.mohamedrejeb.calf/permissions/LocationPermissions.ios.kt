// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions

import com.mohamedrejeb.calf.permissions.helper.LocationPermissionHelper
import com.mohamedrejeb.calf.permissions.helper.PermissionDelegateRegistry

internal actual fun registerFineLocationPermission(permission: Permission) {
    PermissionDelegateRegistry.register(permission) {
        LocationPermissionHelper(requirePrecise = true)
    }
}

internal actual fun registerCoarseLocationPermission(permission: Permission) {
    PermissionDelegateRegistry.register(permission) {
        LocationPermissionHelper()
    }
}

