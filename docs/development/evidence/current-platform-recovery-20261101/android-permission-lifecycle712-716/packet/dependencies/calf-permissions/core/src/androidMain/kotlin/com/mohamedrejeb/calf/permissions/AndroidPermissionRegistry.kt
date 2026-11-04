// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
package com.mohamedrejeb.calf.permissions

/**
 * Mapping of a logical permission to one native grant. The four-argument constructor
 * is retained for custom integrations. Use alwaysGranted=true to explicitly describe
 * a platform with no corresponding runtime gate, never an unregistered permission.
 */
class AndroidPermissionMapping(
    val permissionString: String,
    val minSdkVersion: Int = 0,
    val maxSdkVersion: Int = Int.MAX_VALUE,
    val alwaysGranted: Boolean = false,
)

object AndroidPermissionRegistry {
    private val lock = Any()
    private val mappings = mutableMapOf<Permission, AndroidPermissionMapping>()

    fun register(permission: Permission, mapping: AndroidPermissionMapping) {
        require(mapping.minSdkVersion >= 0 && mapping.maxSdkVersion >= mapping.minSdkVersion) {
            "Invalid SDK interval for $permission"
        }
        require(mapping.permissionString.isNotBlank() || mapping.alwaysGranted) {
            "An empty native mapping must explicitly set alwaysGranted=true"
        }
        synchronized(lock) { mappings[permission] = mapping }
    }

    internal fun getMapping(permission: Permission): AndroidPermissionMapping? =
        synchronized(lock) { mappings[permission] }

    // Retained for internal compatibility only. Request results MUST NOT use a global
    // first-match reverse lookup: Gallery and ReadStorage can share a native grant.
    internal fun findByAndroidString(androidPermission: String, sdkInt: Int): Permission? =
        synchronized(lock) {
            mappings.entries.firstOrNull { (_, mapping) ->
                mapping.permissionString == androidPermission &&
                    sdkInt in mapping.minSdkVersion..mapping.maxSdkVersion
            }?.key
        }
}
