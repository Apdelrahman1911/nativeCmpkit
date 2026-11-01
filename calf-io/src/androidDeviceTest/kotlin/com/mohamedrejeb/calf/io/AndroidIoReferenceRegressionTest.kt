// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import androidx.core.content.FileProvider
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.mohamedrejeb.calf.io.instrumentation.DeviceIoFileProvider
import java.io.File
import java.io.FileNotFoundException
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.io.buffered
import kotlinx.io.readByteArray
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** New public reference regressions only. Accepted lifecycle/Coil classes are not selected or replayed. */
@RunWith(AndroidJUnit4::class)
class AndroidIoReferenceRegressionTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION
    private val grantMask = read or write or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION

    @Test fun nativeFileProviderSingleFileMetadataAndNonPersistableAccessStayDistinctFromTrees() = runBlocking(Dispatchers.IO) {
        sandbox { directory ->
            val bytes = ByteArray(8197) { (it % 251).toByte() }
            val file = File(directory, "single % résumé-日本語.txt").apply { writeBytes(bytes) }
            val authority = verifyPrivateFileProvider()
            val uri = FileProvider.getUriForFile(context, authority, file)
            val reference = KmpFile(uri)
            val identity = DeviceDescriptorIdentity.of(file)
            assertEquals(0, openDeviceDescriptorsFor(identity))
            assertNull(uri.query, "Use the unmodified normal FileProvider path, not a fault/metadata fixture mode")
            assertFalse(DocumentsContract.isDocumentUri(context, uri))
            assertFalse(DocumentsContract.isTreeUri(uri))
            assertNotEquals(AndroidIoProviderContract.tree, uri)
            // FileProvider's real openable contract, NOT DocumentsProvider-only mime_type columns.
            assertNotNull(context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE), null, null, null)).use {
                assertTrue(it.moveToFirst()); assertEquals(file.name, it.getString(0)); assertEquals(bytes.size.toLong(), it.getLong(1))
                assertFalse(it.moveToNext())
            }
            assertTrue(reference.exists(context)); assertTrue(reference.isFile(context)); assertFalse(reference.isDirectory(context))
            assertEquals(file.name, reference.getName(context)); assertEquals(bytes.size.toLong(), reference.getSize(context))
            assertEquals("text/plain", reference.getMimeType(context)); assertNull(reference.getPath(context))
            assertEquals(uri.toString(), reference.toUriString())
            assertEquals(uri, assertNotNull(KmpFile.fromUriString(uri.toString())).uri)
            assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == uri })
            assertNull(reference.createBookmark(context), "Inherent same-UID FileProvider access is not a persistable grant")
            assertNull(KmpFile.fromBookmark(uri.toString(), context))
            reference.releaseBookmark(context)
            assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == uri })
            assertEquals(0, fileProviderStats(uri).getInt("opens"), "Metadata/bookmark attempts must not become byte-stream existence probes")
            assertContentEquals(bytes, reference.readByteArray(context))
            assertEquals(0, openDeviceDescriptorsFor(identity))
            reference.source(context).buffered().use { source ->
                assertTrue(openDeviceDescriptorsFor(identity) > 0)
                assertContentEquals(bytes, source.readByteArray())
                assertTrue(openDeviceDescriptorsFor(identity) > 0, "EOF does not transfer close ownership away from the consumer")
            }
            assertEquals(0, openDeviceDescriptorsFor(identity)); assertEquals(2, fileProviderStats(uri).getInt("opens"))
            assertContentEquals(bytes, file.readBytes(), "Reading/releasing a caller-owned content reference cannot modify its file")
            assertTrue(file.delete(), "Delete only this test-owned source to produce a real missing-content failure")
            assertFailsWith<FileNotFoundException> { reference.readByteArray(context) }
            assertFailsWith<FileNotFoundException> { reference.source(context).buffered().use { it.readByteArray() } }
            assertEquals(0, openDeviceDescriptorsFor(identity)); assertEquals(2, fileProviderStats(uri).getInt("opens"))
            // FileProvider may still expose a metadata row after deletion. Do not silently
            // assert nonexistent content metadata is accurate, or call a missing read empty success.
        }
    }

    @Test fun nativeSandboxFileUriSupportsDecodedPathsBookmarksDirectoriesAndMissingReadFailures() = runBlocking(Dispatchers.IO) {
        sandbox { directory ->
            val bytes = ByteArray(513) { (it % 251).toByte() }
            val file = File(directory, "sandbox % résumé-日本語.txt").apply { writeBytes(bytes) }
            val reference = file.toKmpFile()
            val uri = Uri.fromFile(file)
            val identity = DeviceDescriptorIdentity.of(file)
            assertEquals(uri, reference.uri)
            assertFalse(DocumentsContract.isDocumentUri(context, uri)); assertFalse(DocumentsContract.isTreeUri(uri))
            assertTrue(reference.exists(context)); assertTrue(reference.isFile(context)); assertFalse(reference.isDirectory(context))
            assertEquals(file.name, reference.getName(context)); assertEquals(bytes.size.toLong(), reference.getSize(context))
            assertEquals("text/plain", reference.getMimeType(context)); assertEquals(file.path, reference.getPath(context))
            assertContentEquals(bytes, File(assertNotNull(reference.getPath(context))).readBytes())
            assertEquals(uri.toString(), reference.toUriString())
            assertEquals(uri, assertNotNull(KmpFile.fromUriString(uri.toString())).uri)
            assertEquals(uri, assertNotNull(KmpFile.fromUriString(file.path)).uri)
            assertEquals(0, openDeviceDescriptorsFor(identity))
            assertContentEquals(bytes, reference.readByteArray(context))
            assertEquals(0, openDeviceDescriptorsFor(identity))
            reference.source(context).buffered().use { source ->
                assertTrue(openDeviceDescriptorsFor(identity) > 0)
                assertContentEquals(bytes, source.readByteArray())
                assertTrue(openDeviceDescriptorsFor(identity) > 0)
            }
            assertEquals(0, openDeviceDescriptorsFor(identity))
            val bookmark = assertNotNull(reference.createBookmark(context))
            assertEquals(uri.toString(), bookmark)
            assertEquals(uri, assertNotNull(KmpFile.fromBookmark(bookmark, context)).uri)
            assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == uri })
            reference.releaseBookmark(context); reference.releaseBookmark(context)
            assertTrue(file.exists(), "File-URI release is a no-op, not deletion or a synthetic URI-permission revoke")
            assertContentEquals(bytes, assertNotNull(KmpFile.fromBookmark(bookmark, context)).readByteArray(context))
            assertEquals(0, openDeviceDescriptorsFor(identity))
            val folder = File(directory, "folder").apply { assertTrue(mkdir()) }
            val folderReference = folder.toKmpFile()
            assertTrue(folderReference.exists(context)); assertTrue(folderReference.isDirectory(context)); assertFalse(folderReference.isFile(context))
            assertEquals("folder", folderReference.getName(context)); assertEquals(folder.path, folderReference.getPath(context))
            assertNull(folderReference.getSize(context))
            assertNotNull(KmpFile.fromBookmark(assertNotNull(folderReference.createBookmark(context)), context))
            assertFailsWith<IOException> { folderReference.readByteArray(context) }
            assertFailsWith<IOException> { folderReference.source(context).buffered().use { it.readByteArray() } }
            assertTrue(file.delete())
            assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context)); assertFalse(reference.isFile(context))
            assertEquals(file.name, reference.getName(context)); assertEquals(file.path, reference.getPath(context))
            assertNull(reference.getSize(context)); assertNull(reference.createBookmark(context)); assertNull(KmpFile.fromBookmark(bookmark, context))
            assertNotNull(KmpFile.fromUriString(bookmark), "Serialization restores a reference, not a missing file or access")
            assertFailsWith<FileNotFoundException> { reference.readByteArray(context) }
            assertFailsWith<FileNotFoundException> { reference.source(context).buffered().use { it.readByteArray() } }
            assertEquals(0, openDeviceDescriptorsFor(identity)); assertTrue(folder.exists())
        }
    }

    @Test fun nativeOrdinaryDocumentGrantBookmarkAndOwnerRevokeNeverBecomeTreeAccess() = runBlocking(Dispatchers.IO) {
        requireNativeContext()
        OwnedIoEndpoint.control().use { control ->
            val owner = control.connect()
            control.request("reset")
            val uri = DocumentsContract.buildDocumentUri(AndroidIoProviderContract.AUTHORITY, "bookmark.txt")
            val sibling = DocumentsContract.buildDocumentUri(AndroidIoProviderContract.AUTHORITY, "survivor.bin")
            var primary: Throwable? = null
            try {
                ownerTransaction(owner, revoke = true) // Establish actual fixed-owner grant absence, never grant by control.
                assertUriPermission(uri, read, PackageManager.PERMISSION_DENIED)
                assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == uri })
                val reference = KmpFile(uri)
                var heldBookmark: String? = null
                ownerTransaction(owner, revoke = false) { result ->
                    assertEquals(uri, result.data); assertEquals("text/plain", result.type)
                    assertEquals(1, assertNotNull(result.clipData).itemCount); assertEquals(uri, assertNotNull(result.clipData).getItemAt(0).uri)
                    assertEquals(read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION, result.flags and grantMask)
                    assertTrue(DocumentsContract.isDocumentUri(context, uri)); assertFalse(DocumentsContract.isTreeUri(uri))
                    assertEquals(listOf("document", "bookmark.txt"), uri.pathSegments)
                    assertUriPermission(uri, read, PackageManager.PERMISSION_GRANTED); assertUriPermission(uri, write, PackageManager.PERMISSION_DENIED)
                    assertUriPermission(AndroidIoProviderContract.tree, read, PackageManager.PERMISSION_DENIED)
                    assertUriPermission(sibling, read, PackageManager.PERMISSION_DENIED)
                    assertTrue(reference.exists(context)); assertTrue(reference.isFile(context)); assertFalse(reference.isDirectory(context))
                    assertEquals("bookmark.txt", reference.getName(context)); assertEquals(AndroidIoProviderContract.bytes("bookmark.txt").size.toLong(), reference.getSize(context))
                    assertEquals("text/plain", reference.getMimeType(context)); assertNull(reference.getPath(context)); assertEquals(uri.toString(), reference.toUriString())
                    assertFalse(KmpFile(sibling).exists(context)); assertFailsWith<SecurityException> { KmpFile(sibling).readByteArray(context) }
                    // Take persistable access while the real result-owning Activity is still alive.
                    heldBookmark = assertNotNull(reference.createBookmark(context))
                    assertEquals(uri.toString(), heldBookmark)
                    val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == uri }
                    assertTrue(persisted.isReadPermission); assertFalse(persisted.isWritePermission)
                }
                val bookmark = assertNotNull(heldBookmark)
                // Only NOW has ownerTransaction destroyed the grant-owning Activity/callback session.
                val restored = assertNotNull(KmpFile.fromBookmark(bookmark, context))
                assertEquals(uri, restored.uri); assertContentEquals(AndroidIoProviderContract.bytes("bookmark.txt"), restored.readByteArray(context))
                waitUntil { documentStats(control).getInt("closes") == 1 }
                val state = documentStats(control)
                assertEquals(1, state.getInt("opens")); assertEquals(1, state.getInt("closes")); assertEquals(0, state.getInt("closeErrors")); assertEquals(0, state.getInt("writes"))
                val identity = DeviceDescriptorIdentity.fromProviderRegularFile(state.getLong("device"), state.getLong("inode"), state.getInt("mode"), state.getLong("fdInfoInode"))
                assertEquals(0, openDeviceDescriptorsFor(identity))
                val revoked = ownerTransaction(owner, revoke = true)
                assertNull(revoked.data); assertNull(revoked.clipData); assertEquals(0, revoked.flags and grantMask)
                assertUriPermission(uri, read, PackageManager.PERMISSION_DENIED); assertUriPermission(uri, write, PackageManager.PERMISSION_DENIED)
                assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == uri })
                assertNull(KmpFile.fromBookmark(bookmark, context)); assertNotNull(KmpFile.fromUriString(bookmark))
                assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context)); assertFalse(reference.isFile(context))
                assertNull(reference.getName(context)); assertNull(reference.getSize(context)); assertNull(reference.getPath(context))
                assertFailsWith<SecurityException> { reference.readByteArray(context) }
                assertFailsWith<SecurityException> { reference.source(context).buffered().use { it.readByteArray() } }
                reference.releaseBookmark(context); reference.releaseBookmark(context)
                assertNull(KmpFile.fromBookmark(bookmark, context))
                val final = documentStats(control)
                assertEquals(1, final.getInt("opens")); assertEquals(1, final.getInt("closes")); assertEquals(0, final.getInt("closeErrors")); assertEquals(0, final.getInt("writes"))
                assertEquals(0, openDeviceDescriptorsFor(identity))
            } catch (failure: Throwable) { primary = failure; throw failure }
            finally {
                // Cleanup retains the original refusal and cannot be skipped because a grant/revoke assertion failed.
                var cleanup: Throwable? = null
                try { ownerTransaction(owner, revoke = true) } catch (failure: Throwable) { cleanup = failure }
                try { control.request("reset") } catch (failure: Throwable) {
                    val first = cleanup
                    if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
                }
                val failure = cleanup
                if (failure != null) {
                    val first = primary
                    if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
        }
    }

    private fun requireNativeContext() {
        assertEquals(35, Build.VERSION.SDK_INT)
        assertEquals(instrumentation.context.packageName, context.packageName)
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "Public file opening/reading is scheduled off the main Looper")
    }

    private fun verifyPrivateFileProvider(): String {
        val authority = "${context.packageName}.io-device-files"
        val provider = assertNotNull(context.packageManager.resolveContentProvider(authority, 0))
        assertEquals(Process.myUid(), provider.applicationInfo.uid); assertFalse(provider.exported); assertTrue(provider.grantUriPermissions)
        assertEquals("${context.packageName}:nativecmpkit_io_device_provider", provider.processName)
        return authority
    }

    private fun fileProviderStats(uri: Uri): Bundle = assertNotNull(context.contentResolver.call(Uri.parse("content://${uri.authority}"),
        DeviceIoFileProvider.STATS, uri.toString(), null)).also {
        for (field in listOf("opens", "providerPid")) assertTrue(it.containsKey(field))
        assertTrue(it.getInt("providerPid") > 0); assertNotEquals(Process.myPid(), it.getInt("providerPid"))
    }

    private fun documentStats(control: OwnedIoEndpoint): Bundle = assertNotNull(control.request("stats", "bookmark.txt").getBundle("provider")).also {
        for (field in listOf("uid", "pid", "process", "generation", "opens", "closes", "closeErrors", "writes", "device", "inode", "mode", "fdInfoInode"))
            assertTrue(it.containsKey(field), "Missing actual single-document provider receipt field")
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(provider.applicationInfo.uid, it.getInt("uid")); assertNotEquals(Process.myUid(), it.getInt("uid"))
        assertTrue(it.getInt("pid") > 0); assertNotEquals(Process.myPid(), it.getInt("pid"))
        assertEquals("${AndroidIoProviderContract.PACKAGE}:nativecmpkit_io_provider", it.getString("process"))
        assertTrue(assertNotNull(it.getString("generation")).matches(Regex("[a-f0-9-]{36}")))
    }

    private fun assertUriPermission(uri: Uri, flags: Int, expected: Int) =
        assertEquals(expected, context.checkUriPermission(uri, Process.myPid(), Process.myUid(), flags))

    private suspend fun ownerTransaction(owner: Bundle, revoke: Boolean, onResult: suspend (Intent) -> Unit = {}): Intent {
        val component = ComponentName(AndroidIoProviderContract.PACKAGE,
            "${AndroidIoProviderContract.PACKAGE}.IoSingleDocumentGrantActivity")
        val dispatch = context.packageManager.getActivityInfo(component, 0)
        assertEquals(owner.getInt("uid"), dispatch.applicationInfo.uid)
        assertTrue(dispatch.exported); assertEquals(AndroidIoProviderContract.PERMISSION, dispatch.permission)
        assertEquals(AndroidIoProviderContract.PACKAGE, dispatch.processName)
        val nonce = UUID.randomUUID().toString().replace("-", "")
        var result: Intent? = null
        ActivityScenario.launch(AndroidIoSingleDocumentGrantActivity::class.java).use { scenario ->
            var activity: AndroidIoSingleDocumentGrantActivity? = null
            scenario.onActivity { activity = it }
            val caller = assertNotNull(activity)
            waitUntil { caller.firstDraw && caller.hasWindowFocus() }
            scenario.onActivity { if (revoke) it.revokeOwnedSingleDocument(nonce) else it.selectOwnedSingleDocument(nonce) }
            waitUntil { caller.resultCode != null }
            assertEquals(Activity.RESULT_OK, caller.resultCode); assertEquals(1, caller.resultCount)
            result = assertNotNull(caller.result)
            val actual = assertNotNull(result)
            assertEquals(nonce, actual.getStringExtra(AndroidIoSingleDocumentGrantActivity.EXTRA_NONCE))
            assertEquals(if (revoke) "revoke" else "grant", actual.getStringExtra("operation"))
            assertNull(actual.getStringExtra("protocolError"))
            for (field in listOf("uid", "pid", "process", "generation")) assertTrue(actual.hasExtra(field))
            assertEquals(owner.getInt("uid"), actual.getIntExtra("uid", -1)); assertEquals(owner.getInt("pid"), actual.getIntExtra("pid", -1))
            assertEquals(owner.getString("process"), actual.getStringExtra("process")); assertEquals(owner.getString("generation"), actual.getStringExtra("generation"))
            onResult(actual) // Background callback before Scenario.close destroys the temporary grant owner.
        }
        return assertNotNull(result)
    }

    private suspend fun sandbox(body: suspend (File) -> Unit) {
        requireNativeContext()
        val root = File(context.cacheDir, "nativecmpkit-io-device")
        assertTrue(root.isDirectory || root.mkdirs()) // Shared fixed provider root is never removed.
        val nonce = UUID.randomUUID().toString()
        val directory = File(root, "reference-$nonce")
        val sibling = File(root, "reference-sibling-$nonce.txt")
        val sentinel = "Unrelated sandbox sibling remains unchanged".encodeToByteArray()
        var ownedDirectory = false; var ownedSibling = false; var sentinelWritten = false
        var primary: Throwable? = null
        try {
            assertFalse(directory.exists()); assertFalse(sibling.exists())
            assertTrue(directory.mkdir()); ownedDirectory = true
            assertTrue(sibling.createNewFile()); ownedSibling = true
            sibling.writeBytes(sentinel); sentinelWritten = true
            assertEquals(root.canonicalFile, directory.canonicalFile.parentFile)
            body(directory)
            assertContentEquals(sentinel, sibling.readBytes())
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanup: Throwable? = null
            fun attempt(operation: () -> Unit) {
                try { operation() } catch (failure: Throwable) {
                    val first = cleanup
                    if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
            // A failed sibling witness is retained but cannot skip safe owned-directory cleanup.
            if (sentinelWritten) attempt { assertContentEquals(sentinel, sibling.readBytes()) }
            if (ownedDirectory) attempt {
                assertEquals(root.canonicalFile, directory.canonicalFile.parentFile)
                assertTrue(directory.deleteRecursively()); assertFalse(directory.exists())
            }
            if (ownedSibling) attempt {
                assertEquals(root.canonicalFile, sibling.canonicalFile.parentFile)
                assertTrue(sibling.delete()); assertFalse(sibling.exists())
            }
            val failure = cleanup
            if (failure != null) {
                val first = primary
                if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
            }
        }
    }

    private fun waitUntil(predicate: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        while (!predicate() && SystemClock.elapsedRealtime() < deadline) SystemClock.sleep(10)
        assertTrue(predicate(), "Bounded native single-document/descriptor observation timed out")
    }
}
