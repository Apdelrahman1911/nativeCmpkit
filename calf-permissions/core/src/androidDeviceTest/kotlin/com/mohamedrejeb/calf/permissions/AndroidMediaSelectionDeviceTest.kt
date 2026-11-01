// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.os.Build
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import org.junit.After
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** One missing media scenario per actual API. Android14 establishes selection through the real OS. */
@RunWith(AndroidJUnit4::class)
@SdkSuppress(minSdkVersion = 33, maxSdkVersion = 35)
class AndroidMediaSelectionDeviceTest {
    private lateinit var consumer: OwnedPermissionDemo
    private lateinit var ui: PermissionDemoSystemUi
    @Before fun setUp() {
        consumer = OwnedPermissionDemo()
        consumer.connect()
        consumer.foreground()
        ui = PermissionDemoSystemUi()
    }
    @After fun tearDown() {
        try { if (::consumer.isInitialized) consumer.close() }
        finally { if (::ui.isInitialized) ui.close() }
    }

    @Test fun realPlatformMediaSelectionIsReflectedByPublicLibraryStates() {
        val initial = consumer.request("observe")
        for (permission in listOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO,
            Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED)) assertFalse(initial.getBoolean(permission))
        consumer.request("seed")
        if (Build.VERSION.SDK_INT == 33) {
            consumer.request("request-media")
            ui.permissionButton("permission_allow_button")
            val granted = consumer.await { it.getBundle("ReadImage")?.getInt("callbacks") == 1 &&
                it.getBundle("ReadVideo")?.getInt("callbacks") == 1 }
            for ((name, nativePermission) in listOf("ReadImage" to Manifest.permission.READ_MEDIA_IMAGES,
                "ReadVideo" to Manifest.permission.READ_MEDIA_VIDEO)) {
                assertTrue(granted.getBoolean(nativePermission))
                val state = assertNotNull(granted.getBundle(name))
                assertTrue(state.getBoolean("granted"))
                assertTrue(state.getBoolean("callbackResult"))
                assertEquals("Full", state.getString("access"))
                assertEquals("Granted", state.getString("lastRequest"))
                assertEquals(1, state.getInt("callbacks"))
            }
        } else {
            consumer.request("platform-selected")
            ui.permissionButton("permission_allow_selected_button")
            ui.selectedPhoto()
            ui.confirmSelectedPhoto()
            val selected = consumer.await { it.getInt("platformCallbacks") == 1 &&
                it.getBundle("ReadImage")?.getString("access") == "Limited" &&
                it.getBundle("ReadVideo")?.getString("access") == "Limited" }
            val result = assertNotNull(selected.getBundle("platformResult"))
            assertEquals(setOf(Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO,
                Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED), result.keySet())
            assertTrue(result.getBoolean(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED))
            assertTrue(selected.getBoolean(Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED))
            for ((name, nativePermission) in listOf("ReadImage" to Manifest.permission.READ_MEDIA_IMAGES,
                "ReadVideo" to Manifest.permission.READ_MEDIA_VIDEO)) {
                assertFalse(result.getBoolean(nativePermission))
                assertFalse(selected.getBoolean(nativePermission))
                val state = assertNotNull(selected.getBundle(name))
                assertFalse(state.getBoolean("granted"))
                assertEquals("Limited", state.getString("access"))
                assertEquals("Available", state.getString("availability"))
                assertEquals(0, state.getInt("callbacks"))
                assertNull(state.getString("lastRequest"), "A platform selection is not a library request result")
            }
        }
        consumer.ready()
    }
}
