// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.Permission
import platform.Foundation.NSLock

object PermissionDelegateRegistry {
    private val lock = NSLock()
    private val delegates = mutableMapOf<Permission, () -> PermissionHelper>()

    fun register(permission: Permission, factory: () -> PermissionHelper) {
        lock.lock()
        try { delegates[permission] = factory } finally { lock.unlock() }
    }

    /** Null means missing integration, not a factory/query/native failure. */
    internal fun findDelegate(permission: Permission): PermissionHelper? {
        lock.lock()
        val factory = try { delegates[permission] } finally { lock.unlock() }
        // Never call application factories while holding the registry lock.
        return factory?.invoke()
    }

    // Retain the diagnostic/descriptor of the existing public lookup contract.
    fun getDelegate(permission: Permission): PermissionHelper = findDelegate(permission) ?: error(
            "No delegate registered for $permission. " +
                "Did you add the corresponding calf-permissions-* dependency?"
    )
}
