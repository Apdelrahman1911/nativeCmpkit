// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.os.Bundle
import android.os.SystemClock
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.filters.SdkSuppress
import org.junit.After
import org.junit.Before
import org.junit.FixMethodOrder
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.MethodSorters
import kotlin.test.*

/** Three new actual OS/library scenarios only. Call declaration is confined to the approved fixture. */
@RunWith(AndroidJUnit4::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
@SdkSuppress(minSdkVersion = 33, maxSdkVersion = 35)
class AndroidPermissionDemoDeviceTest {
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

    @Test fun callOnFreshApprovedVariantUsesPublicRequestAndActualSystemGrant() {
        val initial = consumer.request("observe")
        assertFalse(initial.getBoolean(Manifest.permission.CALL_PHONE))
        assertFalse(initial.getBoolean(Manifest.permission.CALL_PHONE + ".rationale"))
        val before = assertNotNull(initial.getBundle("Call"))
        assertFalse(before.getBoolean("granted"))
        assertEquals("Available", before.getString("availability"))
        assertEquals(0, before.getInt("callbacks"))
        consumer.request("request-call")
        ui.permissionButton("permission_allow_button")
        val native = consumer.await { it.getBundle("Call")?.getInt("callbacks") == 1 }
        val state = assertNotNull(native.getBundle("Call"))
        assertTrue(native.getBoolean(Manifest.permission.CALL_PHONE))
        assertTrue(state.getBoolean("granted"))
        assertTrue(state.getBoolean("callbackResult"))
        assertEquals("Full", state.getString("access"))
        assertEquals("Granted", state.getString("lastRequest"))
        consumer.ready()
        assertEquals(1, consumer.request("observe").getBundle("Call")?.getInt("callbacks"))
    }

    @Test fun denialThenPermanentDenialKeepsActualRationaleAndOneResultPerRequest() {
        val initial = consumer.request("observe")
        assertFalse(initial.getBoolean(Manifest.permission.RECORD_AUDIO))
        assertFalse(initial.getBoolean(Manifest.permission.RECORD_AUDIO + ".rationale"))
        assertEquals(0, initial.getBundle("RecordAudio")?.getInt("callbacks"))
        consumer.request("request-microphone")
        ui.permissionButton("permission_deny_button")
        val denied = consumer.await { it.getBundle("RecordAudio")?.getInt("callbacks") == 1 }
        assertDenied(denied, rationale = true, count = 1)
        consumer.ready()
        consumer.request("request-microphone")
        ui.permissionButton("permission_deny_button", "permission_deny_and_dont_ask_again_button")
        val permanent = consumer.await { it.getBundle("RecordAudio")?.getInt("callbacks") == 2 }
        assertDenied(permanent, rationale = false, count = 2)
        consumer.ready()
        consumer.request("request-microphone")
        val deadline = SystemClock.elapsedRealtime() + 5000
        var third: Bundle
        while (true) {
            assertFalse(ui.permissionDialogVisible(), "A third request after real permanent denial must not show another permission dialog")
            third = consumer.request("observe")
            if (third.getBundle("RecordAudio")?.getInt("callbacks") == 3) break
            check(SystemClock.elapsedRealtime() < deadline)
            Thread.sleep(20)
        }
        assertDenied(third, rationale = false, count = 3)
        // Rationale=false alone is ambiguous; the public API must retain Unknown.
        assertEquals("Unknown", third.getBundle("RecordAudio")?.getString("requestability"))
        consumer.ready()
    }

    @Test fun pickersReadRealDocumentsAndImagesWithoutAllFilesOrSmsPermissions() {
        val initial = consumer.request("observe")
        assertFalse(initial.getBoolean(Manifest.permission.READ_MEDIA_IMAGES))
        assertFalse(initial.getBoolean(Manifest.permission.READ_MEDIA_VIDEO))
        val declared = assertNotNull(initial.getStringArray("declaredPermissions")).toSet()
        for (name in OwnedPermissionDemo.FORBIDDEN) assertFalse("android.permission.$name" in declared,
            "Forbidden permission android.permission.$name is declared: $declared")
        val seeded = consumer.request("seed")
        val document = assertNotNull(seeded.getBundle("seed.document"))
        val image = assertNotNull(seeded.getBundle("seed.image"))
        consumer.request("file-picker")
        ui.document(assertNotNull(document.getString("name")))
        assertRead(consumer.await { it.containsKey("read.document") }, "document", document)
        consumer.ready()
        consumer.request("image-picker")
        ui.selectedPhoto()
        assertRead(consumer.await { it.containsKey("read.image") }, "image", image)
        val end = consumer.ready()
        assertFalse(end.getBoolean(Manifest.permission.READ_MEDIA_IMAGES))
        assertFalse(end.getBoolean(Manifest.permission.READ_MEDIA_VIDEO))
        assertEquals(2, end.getInt("ownedSeedCount"))
        assertEquals(0, end.getInt("activeReads"))
    }

    private fun assertDenied(native: Bundle, rationale: Boolean, count: Int) {
        val state = assertNotNull(native.getBundle("RecordAudio"))
        assertFalse(native.getBoolean(Manifest.permission.RECORD_AUDIO))
        assertFalse(state.getBoolean("granted"))
        assertFalse(state.getBoolean("callbackResult"))
        assertEquals(rationale, state.getBoolean("rationale"))
        assertEquals(rationale, native.getBoolean(Manifest.permission.RECORD_AUDIO + ".rationale"))
        assertEquals("Denied", state.getString("lastRequest"))
        assertEquals(count, state.getInt("callbacks"))
    }
    private fun assertRead(native: Bundle, kind: String, seed: Bundle) {
        val read = assertNotNull(native.getBundle("read.$kind"))
        assertEquals(1, read.getInt("results"))
        assertTrue(read.getBoolean("realContentUri"))
        assertTrue(read.getBoolean("sourcePreserved"))
        assertEquals(seed.getString("sha256"), read.getString("sha256"))
        assertEquals(seed.getInt("bytes"), read.getInt("bytes"))
        assertEquals(0, native.getInt("activeReads"))
    }
}
