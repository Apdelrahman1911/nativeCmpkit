// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions

import com.mohamedrejeb.calf.permissions.helper.CalendarPermissionHelper
import com.mohamedrejeb.calf.permissions.helper.CalendarAccessMode
import com.mohamedrejeb.calf.permissions.helper.PermissionDelegateRegistry

internal actual fun registerReadCalendarPermission(permission: Permission) {
    PermissionDelegateRegistry.register(permission) {
        CalendarPermissionHelper(CalendarAccessMode.Read)
    }
}

internal actual fun registerWriteCalendarPermission(permission: Permission) {
    PermissionDelegateRegistry.register(permission) {
        CalendarPermissionHelper(CalendarAccessMode.Write)
    }
}
