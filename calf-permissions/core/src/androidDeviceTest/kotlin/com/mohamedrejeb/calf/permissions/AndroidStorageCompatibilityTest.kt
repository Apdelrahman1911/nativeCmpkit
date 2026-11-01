// SPDX-License-Identifier: Apache-2.0
@file:OptIn(ExperimentalPermissionsApi::class)
package com.mohamedrejeb.calf.permissions

import android.Manifest
import android.app.AppOpsManager
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.os.Process
import android.provider.DocumentsContract
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File
import java.security.MessageDigest
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Finite selectors only. Wrong SDK/flavor fails; no assumptions, skips or fabricated grants. */
@RunWith(AndroidJUnit4::class)
class AndroidStorageCompatibilityTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val payload = ByteArray(257) { (it % 256).toByte() }
    private val expectedHash = MessageDigest.getInstance("SHA-256").digest(payload)
        .joinToString("") { "%02x".format(it.toInt() and 255) }

    @Test fun api28LegacyPermissionControlsSharedStorage() {
        assertEquals(28, Build.VERSION.SDK_INT)
        case("legacy28", 28) { probe ->
            val before = probe.request("snapshot")
            assertFalse(before.getBoolean("nativeWrite"))
            assertFalse(before.getBoolean("write.granted"))
            assertEquals("Available", before.getString("write.availability"))
            assertEquals("None", before.getString("write.access"))
            assertShared(probe.request("shared-root"), allowed = false)
            nativeWriteGrant(probe) {
                assertWriteRequest(probe, notRequired = false)
                assertShared(probe.request("shared-root"), allowed = true)
                appScopedAndSaf(probe)
            }
        }
    }

    @Test fun api29Target28LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper() {
        assertEquals(29, Build.VERSION.SDK_INT)
        legacy29("legacyTarget28", 28, legacy = true)
    }

    @Test fun api29Target29LegacyAccessStillNeedsNativeWriteDespiteNotRequiredHelper() {
        assertEquals(29, Build.VERSION.SDK_INT)
        legacy29("legacy29", 29, legacy = true)
    }

    @Test fun api29ScopedAccessStaysBoundedWithNativeWriteGrant() {
        assertEquals(29, Build.VERSION.SDK_INT)
        legacy29("scoped29", 29, legacy = false)
    }

    private fun legacy29(mode: String, target: Int, legacy: Boolean) {
        case(mode, target) { probe ->
            val before = probe.request("snapshot")
            assertEquals(legacy, before.getBoolean("legacy"))
            assertFalse(before.getBoolean("nativeWrite"))
            assertWriteRequest(probe, notRequired = true)
            assertFalse(probe.request("snapshot").getBoolean("nativeWrite"), "WriteStorage must not acquire the separate native legacy prerequisite")
            assertShared(probe.request("shared-root"), allowed = false)
            nativeWriteGrant(probe) {
                assertWriteRequest(probe, notRequired = true)
                assertShared(probe.request("shared-root"), allowed = legacy)
                appScopedAndSaf(probe)
            }
        }
    }

    @Test fun modernAppScopedAndSafDoNotNeedAllFiles() {
        assertTrue(Build.VERSION.SDK_INT in setOf(30, 35))
        case("modern", 35) { probe ->
            val initial = probe.request("snapshot")
            assertFalse(initial.getBoolean("nativeWrite")); assertFalse(initial.getBoolean("legacy"))
            assertManager(initial, allowed = false)
            assertWriteRequest(probe, notRequired = true)
            assertShared(probe.request("shared-root"), allowed = false)
            appScopedAndSaf(probe)
        }
    }

    @Test fun modernManifestAloneDoesNotGrantAllFilesAndOwnedSettingRestores() {
        assertTrue(Build.VERSION.SDK_INT in setOf(30, 35))
        case("allFiles", 35) { probe ->
            val initial = probe.request("snapshot")
            assertFalse(initial.getBoolean("nativeWrite")); assertFalse(initial.getBoolean("legacy"))
            assertManager(initial, allowed = false)
            assertWriteRequest(probe, notRequired = true)
            assertShared(probe.request("shared-root"), allowed = false)
            var failure: Throwable? = null
            try {
                setOwnedAllFiles("allow")
                probe.await { val state = probe.request("snapshot"); state.getBoolean("manager") &&
                    state.getInt("managerMode") == AppOpsManager.MODE_ALLOWED }
                assertManager(probe.request("snapshot"), allowed = true)
                assertWriteSnapshot(probe.request("snapshot"), notRequired = true)
                assertShared(probe.request("shared-root"), allowed = true)
                assertTrue(probe.request("saf-denied").getBoolean("saf.denied"),
                    "All-files access cannot bypass another UID's private document grant")
            } catch (current: Throwable) { failure = current; throw current }
            finally {
                cleanup(failure) {
                    probe.removeOwnedActivityAndSaf()
                    setOwnedAllFiles("default")
                    probe.await { val state = probe.request("snapshot"); !state.getBoolean("manager") &&
                        state.getInt("managerMode") == AppOpsManager.MODE_DEFAULT }
                    assertManager(probe.request("snapshot"), allowed = false)
                    probe.foreground()
                }
            }
            assertShared(probe.request("shared-root"), allowed = false)
            appScopedAndSaf(probe)
        }
    }

    private fun case(mode: String, target: Int, body: (OwnedStorageProbe) -> Unit) {
        assertEquals(instrumentation.context.packageName, context.packageName)
        val mapping = assertNotNull(AndroidPermissionRegistry.getMapping(Permission.WriteStorage))
        assertEquals(Manifest.permission.WRITE_EXTERNAL_STORAGE, mapping.permissionString)
        assertEquals(28, mapping.maxSdkVersion)
        val info = context.packageManager.getPackageInfo(OwnedStorageProbe.PACKAGE, PackageManager.GET_PERMISSIONS)
        val declared = info.requestedPermissions.orEmpty().toSet()
        assertEquals(mode == "allFiles", Manifest.permission.MANAGE_EXTERNAL_STORAGE in declared)
        assertEquals(mode in setOf("legacy28", "legacyTarget28", "legacy29", "scoped29"),
            Manifest.permission.WRITE_EXTERNAL_STORAGE in declared)
        assertTrue(declared.all { it in setOf(Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.MANAGE_EXTERNAL_STORAGE,
            OwnedStorageProbe.PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION") },
            "Only legacy storage compatibility implications or the explicit special test flavor are permitted")
        val authority = context.packageName + ".storage-documents"
        val provider = assertNotNull(context.packageManager.resolveContentProvider(authority, 0))
        assertEquals(Process.myUid(), provider.applicationInfo.uid)
        assertTrue(provider.exported); assertTrue(provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission)
        val root = File(context.filesDir, "nativecmpkit-storage-saf")
        assertFalse(root.exists(), "Do not reuse or erase a stale/foreign document fixture")
        assertTrue(root.mkdir())
        val caseNonce = assertNotNull(InstrumentationRegistry.getArguments().getString("nativecmpkitStorageCaseNonce"))
        assertTrue(caseNonce.matches(Regex("[a-f0-9]{32}")))
        var failure: Throwable? = null
        try {
            val document = File(root, caseNonce + ".bin")
            document.writeBytes(payload)
            val uri = DocumentsContract.buildDocumentUri(authority, document.name)
            OwnedStorageProbe(mode, target).use { probe ->
                probe.connect()
                probe.request("begin", Bundle().apply { putString("case_nonce", caseNonce); putString("document_uri", uri.toString()) })
                probe.foreground()
                body(probe)
            }
        } catch (current: Throwable) { failure = current; throw current }
        finally {
            cleanup(failure) { assertTrue(root.deleteRecursively()); assertFalse(root.exists()) }
        }
    }

    private fun nativeWriteGrant(probe: OwnedStorageProbe, body: () -> Unit) {
        assertFalse(probe.request("snapshot").getBoolean("nativeWrite"))
        var failure: Throwable? = null
        try {
            // Explicit owned test grant; no UI-dialog or library-issued grant is inferred.
            instrumentation.uiAutomation.grantRuntimePermission(OwnedStorageProbe.PACKAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            probe.await { probe.request("snapshot").getBoolean("nativeWrite") }
            body()
        } catch (current: Throwable) { failure = current; throw current }
        finally {
            var safCleanupVerified = false
            cleanupAll(failure, listOf({
                // Persisted grants survive process death; release them before native revocation.
                probe.removeOwnedActivityAndSaf()
                safCleanupVerified = true
            }, {
                assertTrue(safCleanupVerified, "Never revoke WRITE before actual SAF release and Activity removal")
                val before = context.packageManager.checkPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE, OwnedStorageProbe.PACKAGE)
                if (before == PackageManager.PERMISSION_GRANTED) {
                    probe.stopRebindingBeforeRevocation()
                    instrumentation.uiAutomation.revokeRuntimePermission(OwnedStorageProbe.PACKAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    probe.awaitDeath()
                } else assertEquals(PackageManager.PERMISSION_DENIED, before)
                assertEquals(PackageManager.PERMISSION_DENIED, context.packageManager.checkPermission(
                    Manifest.permission.WRITE_EXTERNAL_STORAGE, OwnedStorageProbe.PACKAGE))
            }))
        }
    }

    private fun cleanup(primary: Throwable?, action: () -> Unit) {
        cleanupAll(primary, listOf(action))
    }

    private fun cleanupAll(primary: Throwable?, actions: List<() -> Unit>) {
        var retained = primary
        actions.forEach { action ->
            try { action() }
            catch (failure: Throwable) {
                val earlier = retained
                if (earlier == null) retained = failure else earlier.addSuppressed(failure)
            }
        }
        if (primary == null) retained?.let { throw it }
    }

    private fun assertWriteRequest(probe: OwnedStorageProbe, notRequired: Boolean) {
        val count = probe.request("snapshot").getInt("callbackCount")
        probe.request("request-write")
        probe.await { probe.request("snapshot").getInt("callbackCount") == count + 1 }
        val actual = probe.request("snapshot")
        assertTrue(actual.containsKey("lastResult")); assertTrue(actual.getBoolean("lastResult"))
        assertEquals(if (notRequired) "NotRequired" else "Granted", actual.getString("write.lastRequest"))
        assertWriteSnapshot(actual, notRequired)
    }

    private fun assertWriteSnapshot(actual: Bundle, notRequired: Boolean) {
        assertTrue(actual.getBoolean("write.granted"))
        assertEquals(if (notRequired) "NotRequired" else "Available", actual.getString("write.availability"))
        assertEquals(if (notRequired) "Unknown" else "Full", actual.getString("write.access"))
    }

    private fun assertManager(actual: Bundle, allowed: Boolean) {
        assertTrue(actual.containsKey("manager")); assertTrue(actual.containsKey("managerMode"))
        assertEquals(allowed, actual.getBoolean("manager"))
        assertEquals(if (allowed) AppOpsManager.MODE_ALLOWED else AppOpsManager.MODE_DEFAULT, actual.getInt("managerMode"))
    }

    private fun assertShared(actual: Bundle, allowed: Boolean) {
        assertTrue(actual.containsKey("shared.allowed")); assertEquals(allowed, actual.getBoolean("shared.allowed"))
        assertTrue(actual.getBoolean("shared.cleanup"))
        if (allowed) {
            assertEquals(0, actual.getInt("shared.errno")); assertEquals(expectedHash, actual.getString("shared.sha256"))
            assertTrue(actual.getBoolean("shared.opened")); assertTrue(actual.getBoolean("shared.closed"))
        } else {
            assertTrue(actual.getInt("shared.errno") in setOf(1, 13))
            assertFalse(actual.getBoolean("shared.opened")); assertFalse(actual.getBoolean("shared.closed"))
        }
    }

    private fun appScopedAndSaf(probe: OwnedStorageProbe) {
        val app = probe.request("app-scoped")
        assertTrue(app.getBoolean("app.allowed")); assertEquals(expectedHash, app.getString("app.sha256"))
        assertTrue(app.getBoolean("app.opened")); assertTrue(app.getBoolean("app.closed")); assertTrue(app.getBoolean("app.cleanup"))
        assertTrue(probe.request("saf-denied").getBoolean("saf.denied"))
        val selected = probe.request("saf-select")
        val documentsUi = assertNotNull(selected.getString("documentsUiPackage"))
        assertTrue(documentsUi in setOf("com.android.documentsui", "com.google.android.documentsui"))
        val owner = context.packageManager.getApplicationInfo(documentsUi, 0)
        assertTrue(owner.flags and ApplicationInfo.FLAG_SYSTEM != 0)
        assertNotEquals(Process.myUid(), owner.uid)
        clickOnlyOwnedSafDocument(documentsUi)
        probe.await { probe.request("snapshot").getBoolean("saf.frameworkResult") }
        val actual = probe.request("saf-read")
        assertEquals(expectedHash, actual.getString("saf.sha256"))
        assertTrue(actual.getBoolean("saf.descriptorClosed")); assertTrue(actual.getBoolean("saf.persistedRead"))
        assertTrue(actual.getInt("saf.resultFlags") and Intent.FLAG_GRANT_READ_URI_PERMISSION != 0)
        probe.request("saf-release-finish")
        probe.await { !probe.request("saf-permission").getBoolean("saf.nativeReadGrant") }
        assertTrue(probe.request("saf-denied").getBoolean("saf.denied"))
        assertTrue(probe.request("snapshot").getBoolean("saf.persistedReleased"))
    }

    @Suppress("DEPRECATION")
    private fun clickOnlyOwnedSafDocument(documentsUi: String) {
        val document = assertNotNull(File(context.filesDir, "nativecmpkit-storage-saf").listFiles()).single().name
        val deadline = android.os.SystemClock.elapsedRealtime() + 20000
        while (android.os.SystemClock.elapsedRealtime() < deadline) {
            val root = instrumentation.uiAutomation.rootInActiveWindow
            if (root != null) {
                try {
                    if (root.packageName?.toString() == documentsUi) {
                        val matches = root.findAccessibilityNodeInfosByText(document)
                        assertTrue(matches.size <= 64)
                        try {
                            val exact = matches.filter { it.packageName?.toString() == documentsUi && it.text?.toString() == document }
                            if (exact.isNotEmpty()) {
                                assertEquals(1, exact.size)
                                var node = exact.single()
                                val parents = mutableListOf<AccessibilityNodeInfo>()
                                try {
                                    repeat(6) {
                                        assertEquals(documentsUi, node.packageName?.toString())
                                        if (node.isClickable) {
                                            assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK)); return
                                        }
                                        node = assertNotNull(node.parent).also(parents::add)
                                    }
                                    fail("Owned document has no bounded clickable system row")
                                } finally { parents.forEach { it.recycle() } }
                            }
                        } finally { matches.forEach { it.recycle() } }
                    }
                } finally { root.recycle() }
            }
            Thread.sleep(50)
        }
        fail("Actual system SAF document was not observed; do not fabricate selection or a grant")
    }

    private fun setOwnedAllFiles(mode: String) {
        assertTrue(Build.VERSION.SDK_INT in setOf(30, 35)); assertTrue(mode in setOf("allow", "default"))
        // Documented test-only ADB operation on the exact owned package. File operations stay in the probe UID.
        val command = "cmd appops set --uid " + OwnedStorageProbe.PACKAGE + " MANAGE_EXTERNAL_STORAGE " + mode
        val result = ParcelFileDescriptor.AutoCloseInputStream(instrumentation.uiAutomation.executeShellCommand(command))
            .use { stream ->
                val bytes = ByteArray(4097)
                var size = 0
                while (size < bytes.size) {
                    val count = stream.read(bytes, size, bytes.size - size)
                    if (count < 0) break
                    assertTrue(count > 0); size += count
                }
                assertTrue(size <= 4096); bytes.copyOf(size).toString(Charsets.UTF_8)
            }
        assertEquals("", result.trim())
    }
}
