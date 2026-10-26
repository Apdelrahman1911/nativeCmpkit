// Modified for nativeCmpkit (2026-10-24): permission safety, capability and request-lifecycle fixes.
@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*

import platform.Contacts.*

internal class ContactPermissionHelper : PermissionSnapshotHelper {
    private val store = CNContactStore()
    private var outcome: PermissionRequestOutcome? = null
    override fun launchPermissionRequest(onPermissionResult: (Boolean) -> Unit) {
        outcome = null
        handleLaunchPermissionRequest(onPermissionResult) {
            store.requestAccessForEntityType(CNEntityType.CNEntityTypeContacts) { _, error ->
                runOnPermissionMainThread {
                    if (error != null) {
                        outcome = PermissionRequestOutcome.Failed
                        onPermissionResult(false)
                    } else getPermissionSnapshot { onPermissionResult(it.status.isGranted) }
                }
            }
        }
    }
    override fun getPermissionSnapshot(onResult: (PermissionSnapshot) -> Unit) {
        val authorization = when (CNContactStore.authorizationStatusForEntityType(CNEntityType.CNEntityTypeContacts)) {
            CNAuthorizationStatusAuthorized -> ContactAuthorization.Full
            CNAuthorizationStatusLimited -> ContactAuthorization.Limited
            CNAuthorizationStatusNotDetermined -> ContactAuthorization.NotDetermined
            CNAuthorizationStatusDenied -> ContactAuthorization.Denied
            CNAuthorizationStatusRestricted -> ContactAuthorization.Restricted
            else -> ContactAuthorization.Unknown
        }
        val snapshot = contactSnapshot(authorization)
        onResult(snapshot.copy(details = snapshot.details.copy(lastRequest = outcome)))
    }
}
