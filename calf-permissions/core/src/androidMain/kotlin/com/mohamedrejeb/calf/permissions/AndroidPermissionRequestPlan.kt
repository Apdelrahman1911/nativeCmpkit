@file:OptIn(ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions

import android.Manifest

/** Immutable, request-local identities and mappings; SDK is explicit for host tests. */
internal class AndroidPermissionRequestPlan(
    permissions: List<Permission>,
    private val sdkInt: Int,
    mapping: (Permission) -> AndroidPermissionMapping? = AndroidPermissionRegistry::getMapping,
) {
    private val entries = permissions.distinct().associateWith(mapping)

    private fun AndroidPermissionMapping.isNotRequired() =
        alwaysGranted || sdkInt !in minSdkVersion..maxSdkVersion

    fun foregroundPermissions(granted: (String) -> Boolean): List<String> =
        entries.values.filterNotNull().flatMap { mapping ->
            val native = mapping.permissionString
            when {
                mapping.isNotRequired() || native == BACKGROUND || granted(native) -> emptyList()
                native == FINE && sdkInt >= 31 -> listOf(COARSE, FINE)
                else -> listOf(native)
            }
        }.distinct()

    fun backgroundPermissions(granted: (String) -> Boolean): List<String> {
        // Android 11+ requires an explicit educational/settings flow. Never silently
        // escalate from foreground, or launch settings without the application's UI.
        if (sdkInt != 29 || (!granted(COARSE) && !granted(FINE))) return emptyList()
        return entries.values.filterNotNull().filter {
            !it.isNotRequired() && it.permissionString == BACKGROUND && !granted(BACKGROUND)
        }.map { it.permissionString }.distinct()
    }

    fun results(granted: (String) -> Boolean): Map<Permission, Boolean> =
        entries.mapValues { (_, mapping) ->
            mapping != null && (mapping.isNotRequired() || granted(mapping.permissionString))
        }

    fun snapshot(permission: Permission, granted: (String) -> Boolean, rationale: (String) -> Boolean): PermissionSnapshot {
        val mapping = entries[permission]
            ?: return PermissionSnapshot(PermissionStatus.Denied(false), PermissionDetails(
                availability = PermissionAvailability.Unsupported,
                access = PermissionAccess.None,
                requestability = PermissionRequestability.Unsupported,
            ))
        if (mapping.isNotRequired()) return PermissionSnapshot(PermissionStatus.Granted, PermissionDetails(
            availability = PermissionAvailability.NotRequired,
            access = PermissionAccess.Unknown,
            requestability = PermissionRequestability.NotRequired,
        ))
        val native = mapping.permissionString
        val allowed = granted(native)
        val requestability = when {
            allowed -> PermissionRequestability.NotRequired
            native == BACKGROUND && !granted(COARSE) && !granted(FINE) -> PermissionRequestability.PrerequisiteRequired
            native == BACKGROUND && sdkInt >= 30 -> PermissionRequestability.SettingsOnly
            else -> PermissionRequestability.Unknown // rationale=false cannot distinguish first-use from permanent denial.
        }
        return PermissionSnapshot(
            if (allowed) PermissionStatus.Granted else PermissionStatus.Denied(rationale(native)),
            PermissionDetails(
                availability = PermissionAvailability.Available,
                access = when {
                    allowed && native == COARSE && !granted(FINE) -> PermissionAccess.Approximate
                    allowed -> PermissionAccess.Full
                    native == FINE && granted(COARSE) -> PermissionAccess.Approximate
                    sdkInt >= 34 && native in listOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO) &&
                        granted(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED) -> PermissionAccess.Limited
                    else -> PermissionAccess.None
                },
                requestability = requestability,
            ),
        )
    }

    companion object {
        const val FINE = Manifest.permission.ACCESS_FINE_LOCATION
        const val COARSE = Manifest.permission.ACCESS_COARSE_LOCATION
        const val BACKGROUND = Manifest.permission.ACCESS_BACKGROUND_LOCATION
    }
}

/** One launcher, at most two sequential OS requests, one full logical result. */
internal class AndroidPermissionRequestRunner(
    private val plan: () -> AndroidPermissionRequestPlan,
    private val granted: (String) -> Boolean,
    private val launchNative: (Array<String>) -> Unit,
    private val beforeResult: () -> Unit,
) {
    private class Pending(val token: Long, val plan: AndroidPermissionRequestPlan) {
        var stage = 0
        var awaiting: Set<String>? = null
    }
    private val gate = PermissionRequestGate<Map<Permission, Boolean>>()
    private var pending: Pending? = null

    fun launch(onResult: (Map<Permission, Boolean>) -> Unit) {
        val token = gate.begin(onResult) ?: return
        val request = Pending(token, plan())
        pending = request
        advance(request)
    }

    fun onNativeResult(result: Map<String, Boolean>) {
        val request = pending ?: return
        val awaiting = request.awaiting ?: return
        // Ignore late results for another stage/identity. An empty map means cancelled.
        if (result.isNotEmpty() && result.keys.any { it !in awaiting }) return
        request.awaiting = null
        advance(request)
    }

    private fun advance(request: Pending) {
        if (!gate.isCurrent(request.token)) return
        try {
            while (request.stage < 2) {
                val strings = if (request.stage++ == 0) request.plan.foregroundPermissions(granted)
                    else request.plan.backgroundPermissions(granted)
                if (strings.isNotEmpty()) {
                    request.awaiting = strings.toSet()
                    launchNative(strings.toTypedArray())
                    return
                }
            }
            val result = request.plan.results(granted)
            pending = null
            beforeResult()
            gate.complete(request.token, result)
        } catch (error: Throwable) {
            if (pending === request) pending = null
            gate.abort(request.token)
            throw error
        }
    }

    fun dispose() {
        pending = null
        gate.dispose()
    }
}
