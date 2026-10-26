// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.EventKit.*
import platform.UIKit.UIDevice

internal class CalendarPermissionHelper(
    private val mode: CalendarAccessMode = CalendarAccessMode.Read,
) : PermissionSnapshotHelper {
    private val store = EKEventStore()
    private var outcome: PermissionRequestOutcome? = null

    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        outcome = null
        handleLaunchPermissionRequest(onPermissionResult) {
            val completion: (Boolean, platform.Foundation.NSError?) -> Unit = { granted, error ->
                runOnPermissionMainThread {
                    outcome = if (error != null) PermissionRequestOutcome.Failed
                        else if (granted) PermissionRequestOutcome.Granted else PermissionRequestOutcome.Denied
                    onPermissionResult(granted && error == null)
                }
            }
            val major = UIDevice.currentDevice.systemVersion.substringBefore('.').toIntOrNull() ?: 0
            when (calendarRequestKind(major, mode)) {
                CalendarRequestKind.Legacy -> store.requestAccessToEntityType(EKEntityType.EKEntityTypeEvent, completion)
                CalendarRequestKind.FullAccess -> store.requestFullAccessToEventsWithCompletion(completion)
                CalendarRequestKind.WriteOnly -> store.requestWriteOnlyAccessToEventsWithCompletion(completion)
            }
        }
    }

    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val authorization = when (EKEventStore.authorizationStatusForEntityType(EKEntityType.EKEntityTypeEvent)) {
            EKAuthorizationStatusAuthorized -> CalendarAuthorization.Full // FullAccess aliases Authorized.
            EKAuthorizationStatusWriteOnly -> CalendarAuthorization.WriteOnly
            EKAuthorizationStatusNotDetermined -> CalendarAuthorization.NotDetermined
            EKAuthorizationStatusDenied -> CalendarAuthorization.Denied
            EKAuthorizationStatusRestricted -> CalendarAuthorization.Restricted
            else -> CalendarAuthorization.Unknown
        }
        val snapshot = calendarSnapshot(authorization, mode)
        onResult(snapshot.copy(details = snapshot.details.copy(lastRequest = outcome)))
    }
}
