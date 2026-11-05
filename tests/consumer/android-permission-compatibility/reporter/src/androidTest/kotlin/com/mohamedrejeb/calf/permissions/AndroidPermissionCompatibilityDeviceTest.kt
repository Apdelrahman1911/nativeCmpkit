// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** NEW real public-library tests. Exact one-method focuses; no samples or fake native grants. */
@RunWith(AndroidJUnit4::class)
class AndroidPermissionCompatibilityDeviceTest {
    @Test fun freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs() {
        PermissionCompatibilityProfiles.requireMethod("freshFineCoarsePairAndBackgroundUseRealApiTargetDialogs")
        val seenUids = mutableSetOf<Int>()
        PermissionCompatibilitySystemUi().use { ui ->
            for (role in listOf("fine", "coarse", "pair", "batch")) {
                OwnedPermissionCompatibility(role).use { owner ->
                    val installed = owner.connect()
                    assertTrue(seenUids.add(assertIs<Int>(installed.get("uid"))), "Each request shape needs its own fresh native UID")
                    val initial = owner.foreground()
                    for (permission in listOf(FINE, COARSE, BACKGROUND)) assertFalse(initial.getBoolean(permission))
                    assertTrue(owner.framework(initial).isEmpty())
                    when (role) {
                        "fine" -> {
                            owner.request("request-fine")
                            ui.locationGrant(if (Build.VERSION.SDK_INT >= 31) true else null)
                            val granted = owner.await { state(it, "FineLocation").getInt("callbacks") == 1 }
                            assertTrue(granted.getBoolean(FINE))
                            assertSingle(state(granted, "FineLocation"), true, "Full", "Granted")
                            assertFramework(owner, granted, listOf(if (Build.VERSION.SDK_INT >= 31) listOf(COARSE, FINE) else listOf(FINE)))
                        }
                        "coarse" -> {
                            owner.request("request-coarse")
                            ui.locationGrant(null) // No fine/accuracy chooser is requested by this manifest or public state.
                            val granted = owner.await { state(it, "CoarseLocation").getInt("callbacks") == 1 }
                            assertTrue(granted.getBoolean(COARSE)); assertFalse(granted.getBoolean(FINE))
                            assertSingle(state(granted, "CoarseLocation"), true, "Approximate", "Granted")
                            assertFramework(owner, granted, listOf(listOf(COARSE)))
                        }
                        "pair" -> {
                            owner.request("request-batch")
                            ui.locationGrant(if (Build.VERSION.SDK_INT >= 31) false else null)
                            val result = owner.await { it.getInt("batchCallbacks") == 1 }
                            val expected = mapOf("FineLocation" to (Build.VERSION.SDK_INT < 31), "CoarseLocation" to true)
                            assertResultMap(result, expected)
                            assertEquals(expected.getValue("FineLocation"), result.getBoolean(FINE))
                            assertTrue(result.getBoolean(COARSE))
                            assertEquals(if (Build.VERSION.SDK_INT >= 31) "Approximate" else "Full", state(result, "FineLocation", batch = true).getString("access"))
                            assertFramework(owner, result, listOf(foregroundArray()))
                        }
                        "batch" -> backgroundStages(owner, ui)
                    }
                    ui.assertOwnedHost(owner.packageName)
                }
            }
        }
    }

    private fun backgroundStages(owner: OwnedPermissionCompatibility, ui: PermissionCompatibilitySystemUi) {
        owner.request("request-background")
        val prerequisite = owner.await { state(it, "BackgroundLocation").getInt("callbacks") == 1 }
        assertTrue(owner.framework(prerequisite).isEmpty(), "Background cannot launch before foreground or when no runtime gate exists")
        val required = Build.VERSION.SDK_INT >= 29
        assertEquals(!required, state(prerequisite, "BackgroundLocation").getBoolean("callbackResult"))
        assertEquals(if (required) "RequiresForeground" else "NotRequired", state(prerequisite, "BackgroundLocation").getString("lastRequest"))
        owner.request("request-batch")
        ui.locationGrant(if (Build.VERSION.SDK_INT >= 31) true else null)
        val foreground = owner.await { owner.framework(it).isNotEmpty() }
        assertEquals(foregroundArray(), owner.framework(foreground).first().getStringArray("permissions")?.toList())
        assertFalse(foregroundArray().contains(BACKGROUND))
        assertTrue(foreground.getBoolean(FINE) && foreground.getBoolean(COARSE))
        if (Build.VERSION.SDK_INT == 29 && foreground.getInt("batchCallbacks") == 0) ui.denyRuntime()
        val complete = owner.await { it.getInt("batchCallbacks") == 1 }
        val physicalBackground = complete.getBoolean(BACKGROUND)
        assertResultMap(complete, mapOf("FineLocation" to true, "CoarseLocation" to true,
            "BackgroundLocation" to (!required || physicalBackground)))
        val requests = owner.framework(complete)
        assertTrue(requests.size in 1..2)
        if (requests.size == 2) {
            assertEquals(29, Build.VERSION.SDK_INT)
            assertEquals(listOf(BACKGROUND), requests[1].getStringArray("permissions")?.toList())
            assertEquals(listOf(PackageManager.PERMISSION_DENIED), requests[1].getIntArray("results")?.toList())
            assertFalse(physicalBackground)
        }
        if (Build.VERSION.SDK_INT >= 30) {
            assertEquals(1, requests.size)
            assertFalse(physicalBackground)
            assertEquals("RequiresSettings", state(complete, "BackgroundLocation", batch = true).getString("lastRequest"))
        }
        if (!required) {
            assertEquals("NotRequired", state(complete, "BackgroundLocation", batch = true).getString("availability"))
            assertFalse(physicalBackground, "NotRequired is not an actual unsupported native background grant")
            return
        }
        if (Build.VERSION.SDK_INT == 29 && PermissionCompatibilityProfiles.selected().second.target == 37) {
            assertFalse(physicalBackground, "Current target must retain the actual background denial")
            assertEquals(2, requests.size)
        }
        // A legacy API29 target may obtain background through its actual OS compatibility
        // policy. Do not fabricate a denial or revoke that grant merely to force two stages.
        var before = complete
        if (!physicalBackground) {
            owner.request("open-background-settings")
            ui.permissionSetting("android.permission-group.LOCATION", "foreground-only")
            before = owner.returnFromSettings(before, ui)
            assertFalse(before.getBoolean(BACKGROUND))
            assertFalse(state(before, "BackgroundLocation", batch = true).getBoolean("granted"))
            owner.request("open-background-settings")
            ui.permissionSetting("android.permission-group.LOCATION", "background-grant")
        } else owner.request("open-background-settings")
        val resumed = owner.returnFromSettings(before, ui)
        assertEquals(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, resumed.getString("lastSettingsAction"))
        assertEquals(owner.packageName, resumed.getString("lastSettingsPackage"))
        assertTrue(resumed.getBoolean(BACKGROUND))
        assertTrue(state(resumed, "BackgroundLocation").getBoolean("granted"))
        assertTrue(state(resumed, "BackgroundLocation", batch = true).getBoolean("granted"))
        assertEquals(1, state(resumed, "BackgroundLocation").getInt("callbacks"))
        assertEquals(1, resumed.getInt("batchCallbacks"))
        assertEquals(requests.size, owner.framework(resumed).size, "Settings refresh cannot manufacture a request callback")
    }

    @Test fun manifestOmissionAndServicesOffKeepDifferentNativeAndPermissionSemantics() {
        PermissionCompatibilityProfiles.requireMethod("manifestOmissionAndServicesOffKeepDifferentNativeAndPermissionSemantics")
        PermissionCompatibilitySystemUi().use { ui ->
            OwnedPermissionCompatibility("omitted").use { owner ->
                owner.connect(); val initial = owner.foreground()
                assertTrue(PermissionCompatibilityProfiles.declarations.getValue("omitted").isEmpty())
                assertFalse(initial.getBoolean(FINE)); assertFalse(initial.getBoolean(COARSE))
                owner.request("request-fine")
                val denied = owner.await { state(it, "FineLocation").getInt("callbacks") == 1 }
                assertFalse(denied.getBoolean(FINE)); assertFalse(denied.getBoolean(COARSE))
                assertSingle(state(denied, "FineLocation"), false, "None", "Denied")
                assertEquals("Available", state(denied, "FineLocation").getString("availability"))
                assertEquals(1, owner.framework(denied).size)
                assertTrue(owner.framework(denied).single().getIntArray("results")!!.all { it == PackageManager.PERMISSION_DENIED })
                ui.assertOwnedHost(owner.packageName)
                // Current public details have no manifest/service diagnostic field. This
                // verifies honest permission-only semantics, not a ConfigurationError API.
            }
            OwnedPermissionCompatibility("batch").use { owner ->
                owner.connect(); val initial = owner.foreground()
                val originalEnabled = assertIs<Boolean>(initial.get("locationServicesEnabled"))
                var primary: Throwable? = null
                try {
                    if (!originalEnabled) {
                        owner.request("open-location-services"); ui.setLocationServices(true)
                        val enabled = owner.returnFromSettings(initial, ui)
                        assertTrue(enabled.getBoolean("locationServicesEnabled"))
                    }
                    owner.request("request-fine")
                    ui.locationGrant(true)
                    val granted = owner.await { state(it, "FineLocation").getInt("callbacks") == 1 }
                    assertTrue(granted.getBoolean(FINE))
                    owner.request("open-location-services"); ui.setLocationServices(false)
                    val disabled = owner.returnFromSettings(granted, ui)
                    assertEquals("isLocationEnabled", disabled.getString("locationServiceObservation"))
                    assertFalse(disabled.getBoolean("locationServicesEnabled"))
                    assertTrue(disabled.getBoolean(FINE))
                    assertTrue(state(disabled, "FineLocation").getBoolean("granted"), "Disabled hardware is not a revoked permission")
                    assertEquals("Full", state(disabled, "FineLocation").getString("access"))
                } catch (failure: Throwable) { primary = failure; throw failure }
                finally {
                    try {
                        val before = owner.request("observe")
                        owner.request("open-location-services"); ui.setLocationServices(originalEnabled)
                        val restored = owner.returnFromSettings(before, ui)
                        assertEquals(originalEnabled, restored.getBoolean("locationServicesEnabled"))
                    } catch (cleanup: Throwable) { if (primary == null) throw cleanup else primary!!.addSuppressed(cleanup) }
                }
            }
        }
    }

    @Test fun cameraSettingsRevocationRefreshesSingleBatchAtSameIdentity() {
        PermissionCompatibilityProfiles.requireMethod("cameraSettingsRevocationRefreshesSingleBatchAtSameIdentity")
        revokeAtSameIdentity("camera", "Camera", CAMERA, "android.permission-group.CAMERA", "request-camera", "open-camera-settings")
    }

    @Test fun locationSettingsRevocationRefreshesSingleBatchAtSameIdentity() {
        PermissionCompatibilityProfiles.requireMethod("locationSettingsRevocationRefreshesSingleBatchAtSameIdentity")
        revokeAtSameIdentity("fine", "FineLocation", FINE, "android.permission-group.LOCATION", "request-fine", "open-fine-settings")
    }

    private fun revokeAtSameIdentity(role: String, name: String, nativePermission: String, group: String, request: String, settings: String) {
        PermissionCompatibilitySystemUi().use { ui ->
            OwnedPermissionCompatibility(role).use { owner ->
                owner.connect(); val initial = owner.foreground()
                assertFalse(initial.getBoolean(nativePermission))
                owner.request(request)
                if (role == "camera") ui.cameraGrant() else ui.locationGrant(true)
                val requested = owner.await { state(it, name).getInt("callbacks") == 1 }
                assertTrue(requested.getBoolean(nativePermission)); assertTrue(state(requested, name).getBoolean("granted"))
                owner.request(settings) // Actual no-change Settings resume also refreshes the separately mounted batch.
                val granted = owner.returnFromSettings(requested, ui)
                assertTrue(state(granted, name, batch = true).getBoolean("granted"))
                owner.request(settings); ui.permissionSetting(group, "deny")
                var denied = owner.returnFromSettings(granted, ui) // OS kill is a failure, never restart/rebind success.
                assertFalse(denied.getBoolean(nativePermission))
                assertFalse(state(denied, name).getBoolean("granted")); assertFalse(state(denied, name, batch = true).getBoolean("granted"))
                for (repeat in 0 until 2) {
                    owner.request(settings)
                    denied = owner.returnFromSettings(denied, ui)
                    assertFalse(denied.getBoolean(nativePermission))
                    assertFalse(state(denied, name).getBoolean("granted")); assertFalse(state(denied, name, batch = true).getBoolean("granted"))
                    assertEquals(1, state(denied, name).getInt("callbacks"))
                    assertEquals(0, denied.getInt("batchCallbacks"))
                    assertEquals(1, owner.framework(denied).size)
                }
            }
        }
    }

    @Test fun pendingNativeCameraDialogDisposalSuppressesRealLateResult() {
        PermissionCompatibilityProfiles.requireMethod("pendingNativeCameraDialogDisposalSuppressesRealLateResult")
        PermissionCompatibilitySystemUi().use { ui ->
            OwnedPermissionCompatibility("camera").use { owner ->
                owner.connect(); val initial = owner.foreground()
                assertFalse(initial.getBoolean(CAMERA)); assertEquals(0, initial.getInt("batchCallbacks"))
                owner.request("request-batch"); ui.assertPermissionDialog()
                owner.request("dispose-content")
                val disposed = owner.await { !it.getBoolean("mounted") && it.getInt("disposalCount") == 1 }
                ui.denyRuntime()
                ui.backToOwned(owner.packageName)
                val late = owner.await { !it.getBoolean("mounted") && it.getBoolean("resumed") && it.getBoolean("focused") && owner.framework(it).size == 1 }
                owner.assertSameIdentity(disposed, late)
                assertEquals(listOf(CAMERA), owner.framework(late).single().getStringArray("permissions")?.toList())
                assertEquals(listOf(PackageManager.PERMISSION_DENIED), owner.framework(late).single().getIntArray("results")?.toList())
                owner.request("request-batch-retained")
                for (observation in 0 until 3) {
                    val after = owner.request("observe")
                    owner.assertSameIdentity(late, after)
                    assertFalse(after.getBoolean(CAMERA)); assertFalse(after.getBoolean("mounted"))
                    assertEquals(0, after.getInt("batchCallbacks"))
                    assertEquals(0, state(after, "Camera", retained = true).getInt("callbacks"))
                    assertFalse(state(after, "Camera", retained = true).getBoolean("granted"))
                    assertFalse(state(after, "Camera", batch = true).getBoolean("granted"))
                    assertEquals(1, owner.framework(after).size)
                    ui.assertOwnedHost(owner.packageName)
                }
            }
        }
    }

    private fun state(native: Bundle, name: String, batch: Boolean = false, retained: Boolean = false): Bundle =
        assertNotNull(native.getBundle(if (batch) "batch.$name" else if (retained) "retained.$name" else name))

    private fun assertSingle(state: Bundle, granted: Boolean, access: String, outcome: String) {
        assertEquals(granted, state.getBoolean("granted")); assertEquals(granted, state.getBoolean("callbackResult"))
        assertEquals(access, state.getString("access")); assertEquals(outcome, state.getString("lastRequest"))
        assertEquals(1, state.getInt("callbacks"))
    }

    private fun assertResultMap(native: Bundle, expected: Map<String, Boolean>) {
        val result = assertNotNull(native.getBundle("batchResult"))
        assertEquals(expected.keys, result.keySet())
        for ((name, value) in expected) {
            assertEquals(value, assertIs<Boolean>(result.get(name)))
            assertEquals(value, state(native, name, batch = true).getBoolean("granted"))
        }
        assertEquals(1, native.getInt("batchCallbacks"))
    }

    private fun assertFramework(owner: OwnedPermissionCompatibility, native: Bundle, arrays: List<List<String>>) {
        val actual = owner.framework(native)
        assertEquals(arrays.size, actual.size)
        for ((index, expected) in arrays.withIndex()) assertEquals(expected, actual[index].getStringArray("permissions")?.toList())
    }

    private fun foregroundArray() = if (Build.VERSION.SDK_INT >= 31) listOf(COARSE, FINE) else listOf(FINE, COARSE)

    companion object {
        private const val FINE = "android.permission.ACCESS_FINE_LOCATION"
        private const val COARSE = "android.permission.ACCESS_COARSE_LOCATION"
        private const val BACKGROUND = "android.permission.ACCESS_BACKGROUND_LOCATION"
        private const val CAMERA = "android.permission.CAMERA"
    }
}
