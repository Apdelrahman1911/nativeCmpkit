// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.provider.Settings
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Three exact, independent API35 source-app/native-library cases. Each focus owns a fresh installation. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 35, maxSdkVersion = 35)
class AndroidPermissionLifecycleDeviceTest {
    private lateinit var consumer: OwnedPermissionLifecycle
    private lateinit var ui: PermissionLifecycleSystemUi
    @Before fun setUp() {
        consumer = OwnedPermissionLifecycle()
        consumer.connect()
        consumer.foreground()
        ui = PermissionLifecycleSystemUi()
    }
    @After fun tearDown() {
        var failure: Throwable? = null
        try { if (::consumer.isInitialized) consumer.close() }
        catch (error: Throwable) { failure = error }
        finally {
            try { if (::ui.isInitialized) ui.close() }
            catch (error: Throwable) { if (failure == null) failure = error else failure!!.addSuppressed(error) }
        }
        failure?.let { throw it }
    }

    @Test fun api35ApproximateFineRequestAndForegroundBackgroundBatchUseRealDialogs() {
        consumer.requireFocus("android-permission-location-api35")
        val initial = consumer.request("observe")
        for (permission in listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION,
            Manifest.permission.ACCESS_BACKGROUND_LOCATION)) assertFalse(assertIs<Boolean>(initial.get(permission)))
        assertEquals(0, nativeResults(initial).size)

        consumer.request("request-background")
        val prerequisite = consumer.await { it.getBundle("BackgroundLocation")?.getInt("callbacks") == 1 }
        assertState(prerequisite, "BackgroundLocation", granted = false, callbacks = 1, outcome = "RequiresForeground")
        assertEquals("PrerequisiteRequired", state(prerequisite, "BackgroundLocation").getString("requestability"))
        ui.assertOwnedHost()
        assertEquals(0, nativeResults(prerequisite).size)

        consumer.request("request-fine")
        ui.locationGrant(precise = false)
        val approximate = consumer.await { it.getBundle("FineLocation")?.getInt("callbacks") == 1 }
        assertTrue(assertIs<Boolean>(approximate.get(Manifest.permission.ACCESS_COARSE_LOCATION)))
        assertFalse(assertIs<Boolean>(approximate.get(Manifest.permission.ACCESS_FINE_LOCATION)))
        assertFalse(assertIs<Boolean>(approximate.get(Manifest.permission.ACCESS_BACKGROUND_LOCATION)))
        assertState(approximate, "FineLocation", granted = false, callbacks = 1, outcome = "Denied")
        assertEquals("Approximate", state(approximate, "FineLocation").getString("access"))
        assertNativePermissionResult(approximate, 0, precise = false)
        assertEquals(1, nativeResults(approximate).size)

        // Coarse-only logical request is already granted here. This is NOT a fresh coarse-only dialog matrix.
        consumer.request("request-coarse")
        val coarse = consumer.await { it.getBundle("CoarseLocation")?.getInt("callbacks") == 1 }
        assertState(coarse, "CoarseLocation", granted = true, callbacks = 1, outcome = "Granted")
        assertEquals("Approximate", state(coarse, "CoarseLocation").getString("access"))
        ui.assertOwnedHost()
        assertEquals(1, nativeResults(coarse).size)

        consumer.request("request-location-batch")
        ui.locationGrant(precise = true)
        val precise = consumer.await { it.getInt("locationCallbacks") == 1 }
        val result = assertNotNull(precise.getBundle("locationResult"))
        assertEquals(setOf("FineLocation", "CoarseLocation", "BackgroundLocation"), result.keySet())
        assertTrue(assertIs<Boolean>(result.get("FineLocation")))
        assertTrue(assertIs<Boolean>(result.get("CoarseLocation")))
        assertFalse(assertIs<Boolean>(result.get("BackgroundLocation")))
        for (permission in listOf(Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION))
            assertTrue(assertIs<Boolean>(precise.get(permission)))
        assertFalse(assertIs<Boolean>(precise.get(Manifest.permission.ACCESS_BACKGROUND_LOCATION)))
        assertEquals("RequiresSettings", state(precise, "batch.BackgroundLocation").getString("lastRequest"))
        assertEquals("SettingsOnly", state(precise, "batch.BackgroundLocation").getString("requestability"))
        assertNativePermissionResult(precise, 1, precise = true)
        assertEquals(2, nativeResults(precise).size)
        consumer.assertSameIdentity(initial, precise)
        ui.assertOwnedHost()

        consumer.request("request-background")
        val settingsOnly = consumer.await { it.getBundle("BackgroundLocation")?.getInt("callbacks") == 2 }
        assertState(settingsOnly, "BackgroundLocation", granted = false, callbacks = 2, outcome = "RequiresSettings")
        assertEquals("SettingsOnly", state(settingsOnly, "BackgroundLocation").getString("requestability"))
        assertEquals(2, nativeResults(settingsOnly).size)
        assertEquals(1, settingsOnly.getInt("locationCallbacks"))
        ui.assertOwnedHost()
        // No background Settings grant/denial, legacy target, old SDK or disabled-service inference.
    }

    @Test fun settingsGrantRepeatedResumeAndDisposedBatchKeepTheSameNativeProcess() {
        consumer.requireFocus("android-permission-lifecycle-grant-api35")
        val initial = consumer.request("observe")
        assertFalse(assertIs<Boolean>(initial.get(Manifest.permission.CAMERA)))
        assertFalse(assertIs<Boolean>(initial.get(Manifest.permission.POST_NOTIFICATIONS)))
        assertState(initial, "Camera", granted = false, callbacks = 0)
        assertState(initial, "Notification", granted = false, callbacks = 0)
        assertFalse(assertIs<Boolean>(state(initial, "batch.Camera").get("granted")))

        val opened = consumer.request("open-camera-settings")
        assertSettingsTarget(opened, Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
        ui.cameraGrant()
        consumer.returnFromSettings(initial, ui)
        var granted = consumer.await { it.getBoolean(Manifest.permission.CAMERA) &&
            it.getBundle("Camera")?.getBoolean("granted") == true && it.getBundle("batch.Camera")?.getBoolean("granted") == true }
        consumer.assertSameIdentity(initial, granted)
        assertState(granted, "Camera", granted = true, callbacks = 0)
        assertEquals(0, granted.getInt("lifecycleCallbacks"))

        repeat(2) {
            val before = granted
            assertSettingsTarget(consumer.request("open-camera-settings"), Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            ui.assertSettingsVisible()
            granted = consumer.returnFromSettings(before, ui)
            consumer.assertSameIdentity(initial, granted)
            assertState(granted, "Camera", granted = true, callbacks = 0)
            assertTrue(assertIs<Boolean>(state(granted, "batch.Camera").get("granted")))
            assertEquals(0, granted.getInt("lifecycleCallbacks"))
        }

        consumer.request("dispose-content")
        val disposed = consumer.await { !it.getBoolean("mounted") && it.getInt("disposalCount") == 1 }
        consumer.assertSameIdentity(initial, disposed)
        assertFalse(assertIs<Boolean>(state(disposed, "retained.Notification").get("granted")))
        assertFalse(assertIs<Boolean>(state(disposed, "batch.Notification").get("granted")))
        assertSettingsTarget(consumer.request("open-notification-settings"), Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        ui.notificationToggle(true)
        consumer.returnFromSettings(disposed, ui)
        val after = consumer.await { it.getBoolean(Manifest.permission.POST_NOTIFICATIONS) }
        consumer.assertSameIdentity(initial, after)
        assertFalse(assertIs<Boolean>(after.get("mounted")))
        assertEquals(1, after.getInt("disposalCount"))
        // Retained disposed public states must not be refreshed by an unregistered lifecycle observer.
        assertState(after, "retained.Notification", granted = false, callbacks = 0)
        assertFalse(assertIs<Boolean>(state(after, "batch.Notification").get("granted")))
        assertEquals(0, after.getInt("lifecycleCallbacks"))
        assertEquals(0, nativeResults(after).size)
    }

    @Test fun notificationSettingsRevocationRefreshesSingleAndBatchWithoutProcessDeath() {
        consumer.requireFocus("android-permission-lifecycle-revoke-api35")
        val initial = consumer.request("observe")
        assertFalse(assertIs<Boolean>(initial.get(Manifest.permission.POST_NOTIFICATIONS)))
        consumer.request("request-notification")
        ui.notificationGrant()
        val granted = consumer.await { it.getBundle("Notification")?.getInt("callbacks") == 1 &&
            it.getBoolean(Manifest.permission.POST_NOTIFICATIONS) && it.getBundle("Notification")?.getBoolean("granted") == true &&
            it.getBundle("batch.Notification")?.getBoolean("granted") == true && it.getBoolean("resumed") && it.getBoolean("focused") }
        assertTrue(assertIs<Boolean>(granted.get(Manifest.permission.POST_NOTIFICATIONS)))
        assertState(granted, "Notification", granted = true, callbacks = 1, outcome = "Granted")
        assertTrue(assertIs<Boolean>(state(granted, "batch.Notification").get("granted")))
        assertEquals(1, nativeResults(granted).size)
        val native = nativeResults(granted).single()
        assertEquals(listOf(Manifest.permission.POST_NOTIFICATIONS), assertNotNull(native.getStringArray("permissions")).toList())
        assertEquals(listOf(PackageManager.PERMISSION_GRANTED), assertNotNull(native.getIntArray("results")).toList())

        assertSettingsTarget(consumer.request("open-notification-settings"), Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        ui.notificationToggle(false)
        // If Android kills this process on revocation, Binder/PID validation fails. No replacement is admitted.
        consumer.returnFromSettings(granted, ui)
        val revoked = consumer.await { !it.getBoolean(Manifest.permission.POST_NOTIFICATIONS) &&
            it.getBundle("Notification")?.getBoolean("granted") == false &&
            it.getBundle("batch.Notification")?.getBoolean("granted") == false }
        consumer.assertSameIdentity(initial, revoked)
        assertState(revoked, "Notification", granted = false, callbacks = 1, outcome = "Granted")
        assertTrue(assertIs<Boolean>(state(revoked, "Notification").get("callbackResult")), "Settings is not a second permission-request callback")
        assertFalse(assertIs<Boolean>(state(revoked, "batch.Notification").get("granted")))
        assertEquals(0, revoked.getInt("lifecycleCallbacks"))
        assertEquals(1, nativeResults(revoked).size)

        assertSettingsTarget(consumer.request("open-notification-settings"), Settings.ACTION_APP_NOTIFICATION_SETTINGS)
        ui.assertSettingsVisible()
        val repeated = consumer.returnFromSettings(revoked, ui)
        consumer.assertSameIdentity(initial, repeated)
        assertState(repeated, "Notification", granted = false, callbacks = 1, outcome = "Granted")
        assertFalse(assertIs<Boolean>(state(repeated, "batch.Notification").get("granted")))
    }

    private fun state(native: Bundle, name: String): Bundle = assertNotNull(native.getBundle(name), "Missing real public permission state $name")
    private fun assertState(native: Bundle, name: String, granted: Boolean, callbacks: Int, outcome: String? = null) {
        val actual = state(native, name)
        assertEquals(granted, assertIs<Boolean>(actual.get("granted")))
        assertEquals(callbacks, assertIs<Int>(actual.get("callbacks")))
        if (outcome != null) assertEquals(outcome, actual.getString("lastRequest"))
    }
    private fun assertSettingsTarget(native: Bundle, action: String) {
        assertEquals(action, native.getString("lastSettingsAction"))
        assertEquals(OwnedPermissionLifecycle.PACKAGE, native.getString("lastSettingsPackage"))
        assertTrue(assertIs<Int>(native.get("settingsOpens")) > 0)
    }
    @Suppress("DEPRECATION")
    private fun nativeResults(native: Bundle): List<Bundle> = assertNotNull(native.getParcelableArrayList<Bundle>("nativePermissionResults"))
    private fun assertNativePermissionResult(native: Bundle, index: Int, precise: Boolean) {
        val actual = nativeResults(native)[index]
        assertEquals(listOf(Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION),
            assertNotNull(actual.getStringArray("permissions")).toList())
        assertEquals(listOf(PackageManager.PERMISSION_GRANTED,
            if (precise) PackageManager.PERMISSION_GRANTED else PackageManager.PERMISSION_DENIED),
            assertNotNull(actual.getIntArray("results")).toList())
    }
}
