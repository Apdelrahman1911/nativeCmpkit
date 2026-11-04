package com.mohamedrejeb.calf.permissions

import androidx.compose.runtime.Immutable

/** Whether this library can check/request the named platform capability. */
enum class PermissionAvailability { Available, NotRequired, Unsupported, Unknown }

/** The usable scope, not a guarantee that a particular operation will succeed. */
enum class PermissionAccess { Unknown, None, Full, Limited, Approximate, WriteOnly, Provisional, Ephemeral }

enum class PermissionRequestability {
    Unknown, Requestable, SettingsOnly, Restricted, PrerequisiteRequired, NotRequired, Unsupported
}

/** Result of the last explicit request. A timeout/error is deliberately not a denial. */
enum class PermissionRequestOutcome {
    Granted, Denied, NotRequired, Unsupported, RequiresSettings, RequiresForeground,
    Restricted, TimedOut, Failed, AppInactive, ConfigurationError
}

/**
 * Supplemental information for the legacy two-case [PermissionStatus] API.
 *
 * `Granted`/`Full` describe only the named permission, not unrestricted files, precise
 * location, enabled hardware, APNs token delivery, or success of a subsequent operation.
 * On iOS the historical Wi-Fi properties probe **local-network access**, not Wi-Fi
 * configuration or SSID access; [capability] identifies that narrower scope.
 */
@Immutable
data class PermissionDetails(
    val availability: PermissionAvailability = PermissionAvailability.Unknown,
    val access: PermissionAccess = PermissionAccess.Unknown,
    val requestability: PermissionRequestability = PermissionRequestability.Unknown,
    val lastRequest: PermissionRequestOutcome? = null,
    val capability: String? = null,
)

/** Optional contract; existing third-party [PermissionState] implementations remain valid. */
interface PermissionDetailsProvider {
    val permissionDetails: PermissionDetails
}

/** Unknown is intentional for third-party states that only implement the legacy API. */
@ExperimentalPermissionsApi
val PermissionState.details: PermissionDetails
    get() = (this as? PermissionDetailsProvider)?.permissionDetails ?: PermissionDetails()

/** A coherent observation used by platform helpers; reading it must not request permission. */
@ExperimentalPermissionsApi
@Immutable
data class PermissionSnapshot(val status: PermissionStatus, val details: PermissionDetails)
