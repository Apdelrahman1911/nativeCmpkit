@file:OptIn(com.mohamedrejeb.calf.permissions.ExperimentalPermissionsApi::class)

package com.mohamedrejeb.calf.permissions.helper

import com.mohamedrejeb.calf.permissions.*
import kotlin.test.*

class LocalNetworkPermissionPolicyTest {
    @Test fun passiveObservationIsUnknownNotAProbeOrAPermanentDenial() {
        val snapshot = localNetworkSnapshot()
        assertFalse(snapshot.status.isGranted)
        assertFalse(snapshot.status.shouldShowRationale)
        assertEquals(PermissionAccess.Unknown, snapshot.details.access)
        assertEquals("local-network-probe", snapshot.details.capability)
        assertNull(snapshot.details.lastRequest)
    }
    @Test fun errorsAndTimeoutsDoNotBecomeUserDenial() {
        listOf(PermissionRequestOutcome.Failed, PermissionRequestOutcome.TimedOut,
            PermissionRequestOutcome.ConfigurationError, PermissionRequestOutcome.AppInactive).forEach {
            val snapshot = localNetworkSnapshot(it)
            assertEquals(it, snapshot.details.lastRequest)
            assertFalse(snapshot.status.shouldShowRationale)
            assertEquals(PermissionAccess.Unknown, snapshot.details.access)
        }
    }
    @Test fun publicationIsReportedAsLocalNetworkScopeOnly() {
        val snapshot = localNetworkSnapshot(PermissionRequestOutcome.Granted)
        assertTrue(snapshot.status.isGranted)
        assertEquals("local-network-probe", snapshot.details.capability)
    }
    @Test fun configurationRequiresBothUsageTextAndDeclaredBonjourService() {
        assertFalse(localNetworkConfigurationValid(null, listOf("_lnp._tcp.")))
        assertFalse(localNetworkConfigurationValid(" ", listOf("_lnp._tcp.")))
        assertFalse(localNetworkConfigurationValid("Find devices", null))
        assertFalse(localNetworkConfigurationValid("Find devices", listOf("_http._tcp.")))
        assertTrue(localNetworkConfigurationValid("Find devices", listOf("_lnp._tcp.")))
    }
}
