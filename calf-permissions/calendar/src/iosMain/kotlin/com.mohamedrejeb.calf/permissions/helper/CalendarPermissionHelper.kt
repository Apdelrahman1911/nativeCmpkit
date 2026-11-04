// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.EventKit.*
import platform.Foundation.NSBundle
import platform.UIKit.UIDevice

/** objectForInfoDictionaryKey also resolves localized InfoPlist.strings, unlike the raw infoDictionary. */
internal fun calendarUsageDescriptionConfigured(kind: CalendarRequestKind, bundle: NSBundle = NSBundle.mainBundle): Boolean =
    calendarUsageDescriptionValid(bundle.objectForInfoDictionaryKey(calendarUsageDescriptionKey(kind)))

internal class CalendarPermissionHelper(
    private val mode: CalendarAccessMode = CalendarAccessMode.Read,
) : PermissionSnapshotHelper {
    private val store = EKEventStore()
    private var outcome: PermissionRequestOutcome? = null

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        // Direct helper callers, not only the Compose backend, must never race outcome/key/native dispatch.
        runOnPermissionMainThread {
            outcome = null
            handleLaunchPermissionRequest(onPermissionResult) {
                val major = UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull() ?: 0
                val kind = calendarRequestKind(major, mode)
                // A missing/blank/wrongly typed purpose string can fail in native privacy code, outside Kotlin exceptions.
                // Fail before invoking EventKit; do not silently substitute a broader or a legacy permission request.
                if (!calendarUsageDescriptionConfigured(kind)) {
                    outcome = PermissionRequestOutcome.ConfigurationError
                    onPermissionResult(false)
                    return@handleLaunchPermissionRequest
                }
                val completion: (Boolean, platform.Foundation.NSError?) -> Unit = { granted, error ->
                    runOnPermissionMainThread {
                        outcome = if (error != null) PermissionRequestOutcome.Failed
                            else if (granted) PermissionRequestOutcome.Granted else PermissionRequestOutcome.Denied
                        onPermissionResult(granted && error == null)
                    }
                }
                when (kind) {
                    CalendarRequestKind.Legacy -> store.requestAccessToEntityType(EKEntityType.EKEntityTypeEvent, completion)
                    CalendarRequestKind.FullAccess -> store.requestFullAccessToEventsWithCompletion(completion)
                    CalendarRequestKind.WriteOnly -> store.requestWriteOnlyAccessToEventsWithCompletion(completion)
                }
            }
        }
    }

    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        runOnPermissionMainThread {
            val authorization = when (EKEventStore.authorizationStatusForEntityType(EKEntityType.EKEntityTypeEvent)) {
                EKAuthorizationStatusAuthorized -> CalendarAuthorization.Full // FullAccess aliases Authorized.
                EKAuthorizationStatusWriteOnly -> CalendarAuthorization.WriteOnly
                EKAuthorizationStatusNotDetermined -> CalendarAuthorization.NotDetermined
                EKAuthorizationStatusDenied -> CalendarAuthorization.Denied
                EKAuthorizationStatusRestricted -> CalendarAuthorization.Restricted
                else -> CalendarAuthorization.Unknown
            }
            val snapshot = calendarSnapshot(authorization, mode)
            onResult(snapshot.copy(details = snapshot.details.copy(
                lastRequest = outcome,
                requestability = if (outcome == PermissionRequestOutcome.ConfigurationError &&
                    snapshot.details.requestability == PermissionRequestability.Requestable)
                    PermissionRequestability.PrerequisiteRequired else snapshot.details.requestability,
            )))
        }
    }
}
