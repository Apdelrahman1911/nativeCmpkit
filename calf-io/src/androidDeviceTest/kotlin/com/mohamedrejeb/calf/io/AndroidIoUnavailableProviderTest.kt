// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ProviderInfo
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.UserHandle
import android.net.Uri
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.FileNotFoundException
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** One real unavailable-provider window, not ordinary provider death/recovery or a system/cloud matrix. */
@RunWith(AndroidJUnit4::class)
class AndroidIoUnavailableProviderTest {
    companion object { private const val CHILD_ID = "bookmark.txt" }
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION
    private val providerComponent get() = ComponentName(AndroidIoProviderContract.PACKAGE,
        "${AndroidIoProviderContract.PACKAGE}.OwnedIoDocumentsProvider")

    @Test fun publicTreeAndChildLookupRefuseDuringOwnedProviderUnavailability() = runBlocking(Dispatchers.IO) {
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedIoDocuments"))
        assertEquals(35, Build.VERSION.SDK_INT); assertEquals(UserHandle.getUserHandleForUid(0), Process.myUserHandle())
        assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals(instrumentation.context.packageName, context.packageName)
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission("android.permission.MANAGE_DOCUMENTS"))
        val originalProvider = assertOwnedAuthorityPresent()
        assertNotEquals(Process.myUid(), originalProvider.applicationInfo.uid)
        assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DEFAULT, context.packageManager.getComponentEnabledSetting(providerComponent))
        val control = OwnedIoEndpoint.control()
        var witness: OwnedIoEndpoint? = null
        var leaseToken: String? = null
        var restored = true
        var primary: Throwable? = null
        try {
            control.connect() // The main control-process identity is not the provider identity.
            assertNotNull(control.request("reset").getBundle("provider"))
            assertQuiescent(control)
            assertUriPermission(AndroidIoProviderContract.tree, read, PackageManager.PERMISSION_DENIED)
            assertUriPermission(AndroidIoProviderContract.tree, write, PackageManager.PERMISSION_DENIED)
            val bookmark = grantAndPersistTree()
            val root = KmpFile(AndroidIoProviderContract.tree)
            val child = KmpFile(AndroidIoProviderContract.child(CHILD_ID))
            assertTrue(root.exists(context)); assertTrue(root.isDirectory(context))
            assertEquals(AndroidIoProviderContract.ROOT_NAME, root.getName(context)); assertNull(root.getSize(context))
            assertTrue(child.exists(context)); assertFalse(child.isDirectory(context))
            assertEquals(CHILD_ID, child.getName(context)); assertEquals(AndroidIoProviderContract.bytes(CHILD_ID).size.toLong(), child.getSize(context))
            assertStillGranted(bookmark, root, child)

            // This nested provider Bundle, obtained before outage, is the only PID/generation correlation source.
            val providerStatsBefore = stats(control, CHILD_ID)
            assertEquals(0, providerStatsBefore.getInt("opens")); assertEquals(0, providerStatsBefore.getInt("closes"))
            assertQuiescent(control) // All cursors are scoped closed; no stream or provider client is held at death.
            val boundWitness = OwnedIoEndpoint.providerWitness()
            witness = boundWitness
            val providerWitness = boundWitness.connect()
            assertEquals(providerStatsBefore.getInt("uid"), providerWitness.getInt("uid"))
            assertEquals(providerStatsBefore.getInt("pid"), providerWitness.getInt("pid"))
            assertEquals(providerStatsBefore.getString("generation"), providerWitness.getString("generation"))
            val runnerPid = Process.myPid()

            // Save the local token before acquisition can partially fail; finally always attempts this exact restore.
            val token = UUID.randomUUID().toString().replace("-", "")
            leaseToken = token; restored = false
            control.unavailable("acquire-unavailable", token)
            assertOwnedAuthorityAbsent()
            val stopped = boundWitness.dieAndObserveBinderDeath()
            assertEquals(providerStatsBefore.getInt("pid"), stopped.getInt("pid"))
            assertEquals(providerStatsBefore.getString("generation"), stopped.getString("generation"))
            witness = null // The acknowledged real Binder death method has already unbound its witness.
            assertEquals(runnerPid, Process.myPid(), "Never kill the reporter or the surviving main control process")

            // BEGIN OWNED UNAVAILABLE WINDOW: no stats/reset/revoke, cursor, PFD or provider-client acquisition here.
            assertOwnedAuthorityAbsent()
            var windowFailure: Throwable? = null
            try {
                assertStillGranted(bookmark, root, child)
                for (reference in listOf(root, child)) {
                    assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context))
                    assertNull(reference.getName(context)); assertNull(reference.getSize(context))
                    assertNull(reference.getPath(context))
                }
                assertEquals(AndroidIoProviderContract.tree.toString(), root.toUriString())
                assertEquals(AndroidIoProviderContract.child(CHILD_ID).toString(), child.toUriString())
                assertQualifiedAbsence(child) { child.readByteArray(context); fail("Unavailable public read unexpectedly returned bytes") }
                assertQualifiedAbsence(child) {
                    val unexpected = child.source(context)
                    var sourceFailure: Throwable? = null
                    try { fail("Unavailable public source unexpectedly returned an owned stream") }
                    catch (failure: Throwable) { sourceFailure = failure; throw failure }
                    finally {
                        try { unexpected.close() }
                        catch (failure: Throwable) {
                            val first = sourceFailure
                            if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
                        }
                    }
                }
                assertStillGranted(bookmark, root, child)
            } catch (failure: Throwable) { windowFailure = failure; throw failure }
            finally {
                try { assertOwnedAuthorityAbsent() }
                catch (failure: Throwable) {
                    val first = windowFailure
                    if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
            // END OWNED UNAVAILABLE WINDOW.

            control.unavailable("restore-unavailable", token)
            restored = true; leaseToken = null
            assertOwnedAuthorityPresent()
            assertStillGranted(bookmark, root, child)
            // Only a bounded restoration/setup witness, not a replay of accepted provider-death or Coil methods.
            assertContentEquals(AndroidIoProviderContract.bytes(CHILD_ID), child.readByteArray(context))
            assertQuiescent(control)
            val providerStatsAfter = stats(control, CHILD_ID)
            assertNotEquals(providerStatsBefore.getInt("pid"), providerStatsAfter.getInt("pid"))
            assertNotEquals(providerStatsBefore.getString("generation"), providerStatsAfter.getString("generation"))
            // onCreate resets counters: no fresh post-restart count is claimed to prove zero opens during outage.
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanup: Throwable? = null
            fun cleanupAttempt(action: () -> Unit) {
                try { action() }
                catch (failure: Throwable) {
                    val first = primary ?: cleanup
                    if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
            val token = leaseToken
            if (token != null) cleanupAttempt {
                control.unavailable("restore-unavailable", token)
                restored = true; leaseToken = null
            }
            // A failed restore must never permit provider reacquisition. Failure cannot skip unbind/bookmark cleanup.
            cleanupAttempt { witness?.close() }
            cleanupAttempt { KmpFile(AndroidIoProviderContract.tree).releaseBookmark(context) }
            if (restored) cleanupAttempt { assertQuiescent(control); control.request("reset") }
            cleanupAttempt { control.close() }
            if (primary == null) cleanup?.let { throw it }
        }
    }

    /** Android15_r1 ContentResolver: null unstable provider in read-mode typed open is exactly this FNF. */
    private suspend fun assertQualifiedAbsence(reference: KmpFile, operation: suspend () -> Unit) {
        val absent = try {
            operation()
            fail("An unavailable-provider operation must fail")
        } catch (failure: FileNotFoundException) { failure }
        assertEquals(FileNotFoundException::class.java, absent.javaClass)
        assertEquals("No content provider: ${reference.uri}", absent.message)
        assertNull(absent.cause, "A wrapped transport, permission or arbitrary error is not qualified absence")
    }

    private fun assertUriPermission(uri: Uri, flags: Int, expected: Int) {
        assertEquals(expected, context.checkUriPermission(uri, Process.myPid(), Process.myUid(), flags))
    }
    private fun assertStillGranted(bookmark: String, root: KmpFile, child: KmpFile) {
        assertEquals(AndroidIoProviderContract.tree.toString(), bookmark)
        assertEquals(root.uri, assertNotNull(KmpFile.fromBookmark(bookmark, context)).uri)
        val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == AndroidIoProviderContract.tree }
        assertTrue(persisted.isReadPermission); assertFalse(persisted.isWritePermission)
        for (reference in listOf(root, child)) {
            assertUriPermission(reference.uri, read, PackageManager.PERMISSION_GRANTED)
            assertUriPermission(reference.uri, write, PackageManager.PERMISSION_DENIED)
        }
    }
    private fun assertOwnedAuthorityPresent(): ProviderInfo {
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(AndroidIoProviderContract.PACKAGE, provider.packageName)
        assertEquals(providerComponent.className, provider.name); assertEquals(AndroidIoProviderContract.AUTHORITY, provider.authority)
        assertEquals(context.packageManager.getApplicationInfo(AndroidIoProviderContract.PACKAGE, 0).uid, provider.applicationInfo.uid)
        assertTrue(provider.exported); assertTrue(provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission); assertEquals("android.permission.MANAGE_DOCUMENTS", provider.writePermission)
        return provider
    }
    private fun assertOwnedAuthorityAbsent() {
        assertEquals(PackageManager.COMPONENT_ENABLED_STATE_DISABLED, context.packageManager.getComponentEnabledSetting(providerComponent))
        assertNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
    }
    private fun stats(control: OwnedIoEndpoint, id: String): Bundle = assertNotNull(control.request("stats", id).getBundle("provider")).also {
        for (key in listOf("uid", "pid", "process", "generation", "opens", "closes", "closeErrors", "writes"))
            assertTrue(it.containsKey(key), "Missing exact pre/post-restoration native provider field")
        assertEquals(assertOwnedAuthorityPresent().applicationInfo.uid, it.getInt("uid"))
        assertTrue(it.getInt("pid") > 0); assertNotEquals(Process.myPid(), it.getInt("pid"))
        assertEquals("${AndroidIoProviderContract.PACKAGE}:nativecmpkit_io_provider", it.getString("process"))
        assertTrue(assertNotNull(it.getString("generation")).matches(Regex("[a-f0-9-]{36}")))
    }
    private fun assertQuiescent(control: OwnedIoEndpoint) {
        waitUntil { listOf("bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin").all { id ->
            val state = stats(control, id); state.getInt("opens") == state.getInt("closes")
        } }
        for (id in listOf("bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin")) {
            val state = stats(control, id)
            assertEquals(0, state.getInt("closeErrors")); assertEquals(0, state.getInt("writes"))
        }
    }
    private fun grantAndPersistTree(): String {
        var bookmark: String? = null
        ActivityScenario.launch(AndroidIoGrantActivity::class.java).use { scenario ->
            var activity: AndroidIoGrantActivity? = null
            scenario.onActivity { activity = it }
            val caller = assertNotNull(activity)
            waitUntil { caller.firstDraw && caller.hasWindowFocus() }
            scenario.onActivity { it.selectOwnedTree() }
            waitUntil { caller.ioDocumentResultCode != null }
            assertEquals(Activity.RESULT_OK, caller.ioDocumentResultCode)
            val result = assertNotNull(caller.ioDocumentResult)
            assertEquals(AndroidIoProviderContract.tree, result.data)
            assertEquals(AndroidIoProviderContract.tree, assertNotNull(result.clipData).getItemAt(0).uri)
            val grantMask = read or write or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION
            assertEquals(read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION, result.flags and grantMask)
            assertUriPermission(AndroidIoProviderContract.tree, read, PackageManager.PERMISSION_GRANTED)
            assertUriPermission(AndroidIoProviderContract.tree, write, PackageManager.PERMISSION_DENIED)
            bookmark = assertNotNull(KmpFile(AndroidIoProviderContract.tree).createBookmark(context))
        } // Destroy the actual grant Activity before the unavailable window.
        return assertNotNull(bookmark)
    }
    private fun waitUntil(condition: () -> Boolean) {
        val deadline = System.nanoTime() + 20_000_000_000L
        while (!condition()) { check(System.nanoTime() < deadline) { "Actual native unavailable-provider condition timed out" }; Thread.sleep(20) }
    }
}
