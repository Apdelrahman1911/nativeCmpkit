// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.Manifest
import android.app.Activity
import android.content.ContentValues
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Looper
import android.os.Process
import android.os.SystemClock
import android.os.UserHandle
import android.provider.DocumentsContract
import android.provider.MediaStore
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.InputStream
import java.util.UUID
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.io.Buffer
import kotlinx.io.readByteArray
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Missing #55 C1 local named-provider checks only; no replay of accepted controlled IO/Coil cases. */
@RunWith(AndroidJUnit4::class)
class AndroidIoNamedSystemProviderTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION

    @Test fun externalStorageProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership() = runBlocking(Dispatchers.IO) {
        namedProviderCase(EXTERNAL_AUTHORITY, "com.android.externalstorage", "com.android.externalstorage.ExternalStorageProvider",
            DocumentsContract.buildDocumentUri(EXTERNAL_AUTHORITY, "primary:${Environment.DIRECTORY_DOWNLOADS}"))
    }

    @Test fun downloadsProviderTreePreservesOwnedFolderMetadataAndBoundedReadOwnership() = runBlocking(Dispatchers.IO) {
        namedProviderCase(DOWNLOADS_AUTHORITY, "com.android.providers.downloads", "com.android.providers.downloads.DownloadStorageProvider",
            DocumentsContract.buildRootUri(DOWNLOADS_AUTHORITY, "downloads"))
    }

    private suspend fun namedProviderCase(authority: String, providerPackage: String, providerClass: String, initialParent: Uri) {
        requireStockNativeContext()
        verifySystemProvider(authority, providerPackage, providerClass)
        val seed = OwnedDownload()
        var scenario: ActivityScenario<AndroidIoSystemTreeGrantActivity>? = null
        var caller: AndroidIoSystemTreeGrantActivity? = null
        var ui: NamedSystemDocumentsUi? = null
        var heldRoot: KmpFile? = null
        var descriptorIdentity: DeviceDescriptorIdentity? = null
        var primary: Throwable? = null
        try {
            seed.create()
            val activeScenario = ActivityScenario.launch(AndroidIoSystemTreeGrantActivity::class.java)
            scenario = activeScenario
            activeScenario.onActivity { caller = it }
            val activity = assertNotNull(caller)
            waitUntil { activity.firstDraw && activity.hasWindowFocus() }
            activeScenario.onActivity { it.selectSystemTree(initialParent) }
            ui = NamedSystemDocumentsUi(assertNotNull(activity.documentsUiPackage))
            ui.selectOwnedFolder(seed.folder)
            waitUntil { activity.resultCode != null }
            assertEquals(1, activity.resultCount); assertEquals(Activity.RESULT_OK, activity.resultCode)
            val result = assertNotNull(activity.result)
            val tree = assertNotNull(result.data)
            // Refuse unexpected references BEFORE querying their content or metadata.
            check(tree.scheme == "content" && tree.authority == authority && tree.query == null && tree.fragment == null)
            check(DocumentsContract.isTreeUri(tree) && tree.pathSegments.size == 2 && tree.pathSegments[0] == "tree")
            val rootId = DocumentsContract.getTreeDocumentId(tree)
            if (authority == EXTERNAL_AUTHORITY) check(rootId == "primary:${Environment.DIRECTORY_DOWNLOADS}/${seed.folder}")
            val requiredGrant = read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION
            assertEquals(requiredGrant, result.flags and requiredGrant)
            if (result.clipData != null) {
                check(result.clipData!!.itemCount == 1 && result.clipData!!.getItemAt(0).uri == tree)
            }
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkUriPermission(tree, Process.myPid(), Process.myUid(), read))
            val normalizedRoot = DocumentsContract.buildDocumentUriUsingTree(tree, rootId)
            val root = KmpFile(tree)
            assertOwnedRoot(root, seed.folder)
            heldRoot = root // Only now may the uniquely owned result be persisted/released by this fixture.
            val child = KmpFile(onlyOwnedChild(tree, rootId, seed))
            check(DocumentsContract.isDocumentUri(context, child.uri) && DocumentsContract.isTreeUri(child.uri))
            assertNotEquals(normalizedRoot, child.uri)
            assertTrue(child.exists(context)); assertTrue(child.isFile(context)); assertFalse(child.isDirectory(context))
            assertEquals(seed.fileName, child.getName(context)); assertEquals(seed.bytes.size.toLong(), child.getSize(context))
            assertEquals("application/octet-stream", child.getMimeType(context)); assertNull(child.getPath(context))
            assertEquals(child.uri.toString(), child.toUriString())
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkUriPermission(child.uri, Process.myPid(), Process.myUid(), read))
            // Calibrate using this exact actual system document URI, not MediaStore inode/mount assumptions.
            descriptorIdentity = assertNotNull(context.contentResolver.openFileDescriptor(child.uri, "r")).use {
                DeviceDescriptorIdentity.of(it)
            }
            val identity = assertNotNull(descriptorIdentity)
            assertEquals(0, openDeviceDescriptorsFor(identity))
            assertContentEquals(seed.bytes, child.readByteArray(context, maxBytes = seed.bytes.size))
            assertEquals(0, openDeviceDescriptorsFor(identity))
            assertFailsWith<IOException> { child.readByteArray(context, maxBytes = seed.bytes.size - 1) }
            assertEquals(0, openDeviceDescriptorsFor(identity))
            child.source(context).use { source ->
                assertTrue(openDeviceDescriptorsFor(identity) > 0)
                val buffer = Buffer()
                while (buffer.size < seed.bytes.size) {
                    check(source.readAtMostTo(buffer, seed.bytes.size.toLong() - buffer.size) > 0) {
                        "The owned native source ended early or made no progress"
                    }
                }
                assertEquals(seed.bytes.size.toLong(), buffer.size)
                assertContentEquals(seed.bytes, buffer.readByteArray())
                val tail = Buffer()
                assertEquals(-1L, source.readAtMostTo(tail, 1), "The owned native source must end at its exact payload")
                assertEquals(0L, tail.size)
                assertTrue(openDeviceDescriptorsFor(identity) > 0, "EOF retains the explicit native close owner")
            }
            assertEquals(0, openDeviceDescriptorsFor(identity))
            seed.assertPublishedUnchanged()
            val bookmark = assertNotNull(root.createBookmark(context))
            assertEquals(tree.toString(), bookmark)
            val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == tree }
            assertTrue(persisted.isReadPermission)
            assertEquals(result.flags and write != 0, persisted.isWritePermission)
            activeScenario.close(); scenario = null
            assertTrue(activity.destroyed)
            assertOwnedRoot(assertNotNull(KmpFile.fromBookmark(bookmark, context)), seed.folder)
            root.releaseBookmark(context)
            assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == tree })
            waitUntil { context.checkUriPermission(tree, Process.myPid(), Process.myUid(), read) == PackageManager.PERMISSION_DENIED }
            assertNull(KmpFile.fromBookmark(bookmark, context))
            for (reference in listOf(root, child)) {
                assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context))
                assertNull(reference.getName(context)); assertNull(reference.getSize(context))
            }
            assertFailsWith<SecurityException> { child.readByteArray(context, maxBytes = seed.bytes.size) }
            assertEquals(0, openDeviceDescriptorsFor(identity))
            seed.assertPublishedUnchanged()
        } catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanup: Throwable? = null
            fun attempt(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    val first = primary ?: cleanup
                    if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
            attempt { scenario?.close() }
            attempt { heldRoot?.releaseBookmark(context) }
            attempt {
                heldRoot?.let { root ->
                    check(!context.contentResolver.persistedUriPermissions.any { it.uri == root.uri })
                    check(context.checkUriPermission(root.uri, Process.myPid(), Process.myUid(), read) == PackageManager.PERMISSION_DENIED)
                }
            }
            attempt { ui?.close() }
            attempt { descriptorIdentity?.let { check(openDeviceDescriptorsFor(it) == 0) } }
            attempt { seed.closeOwnedRow() }
            // NEVER delete a tree/directory recursively. Only the controller's owned guest disposal removes an empty directory.
            if (primary == null) cleanup?.let { throw it }
        }
    }

    private fun assertOwnedRoot(root: KmpFile, folder: String) {
        check(root.getName(context) == folder) { "The native result does not identify the uniquely owned directory" }
        assertTrue(root.exists(context)); assertTrue(root.isDirectory(context)); assertFalse(root.isFile(context))
        assertNull(root.getSize(context)); assertNull(root.getPath(context))
        assertEquals(root.uri.toString(), root.toUriString())
    }

    private fun onlyOwnedChild(tree: Uri, rootId: String, seed: OwnedDownload): Uri {
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, rootId)
        return assertNotNull(context.contentResolver.query(children, arrayOf(
            DocumentsContract.Document.COLUMN_DOCUMENT_ID, DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE, DocumentsContract.Document.COLUMN_SIZE), null, null, null)).use { cursor ->
            check(cursor.moveToFirst()) { "The newly owned directory has no native child" }
            check(cursor.getString(1) == seed.fileName && cursor.getString(2) == "application/octet-stream" &&
                !cursor.isNull(3) && cursor.getLong(3) == seed.bytes.size.toLong()) { "The native child is not the owned payload" }
            val childId = cursor.getString(0)
            check(!childId.isNullOrEmpty() && childId != rootId)
            check(!cursor.moveToNext()) { "Do not read a directory with unexpected additional children" }
            DocumentsContract.buildDocumentUriUsingTree(tree, childId)
        }
    }

    private fun requireStockNativeContext() {
        assertEquals(35, Build.VERSION.SDK_INT)
        assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals(UserHandle.getUserHandleForUid(0), Process.myUserHandle())
        assertEquals(instrumentation.context.packageName, context.packageName)
        assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertEquals("en", context.resources.configuration.locales[0].language)
        assertTrue(context.contentResolver.persistedUriPermissions.isEmpty(), "Never release a preexisting grant")
        for (permission in listOf("android.permission.MANAGE_DOCUMENTS", Manifest.permission.MANAGE_EXTERNAL_STORAGE,
            Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO, Manifest.permission.READ_MEDIA_AUDIO)) {
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(permission))
        }
        val media = assertNotNull(context.packageManager.resolveContentProvider("media", 0))
        assertTrue(media.packageName in setOf("com.android.providers.media.module", "com.google.android.providers.media.module"))
        assertTrue(media.applicationInfo.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        assertNotEquals(Process.myUid(), media.applicationInfo.uid)
    }

    private fun verifySystemProvider(authority: String, providerPackage: String, providerClass: String) {
        val provider = assertNotNull(context.packageManager.resolveContentProvider(authority, 0))
        assertEquals(authority, provider.authority); assertEquals(providerPackage, provider.packageName)
        assertEquals(providerClass, provider.name)
        assertTrue(provider.exported && provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.writePermission)
        assertTrue(provider.applicationInfo.flags and (ApplicationInfo.FLAG_SYSTEM or ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0)
        assertNotEquals(Process.myUid(), provider.applicationInfo.uid)
    }

    /** Ownership is recorded immediately after insert, before any failing write/update. No directory is ever deleted here. */
    private inner class OwnedDownload {
        val folder = "NativeCmpKitIo55-" + UUID.randomUUID().toString().replace("-", "")
        val fileName = "payload-" + folder.substringAfter('-') + ".bin"
        val relativePath = "${Environment.DIRECTORY_DOWNLOADS}/$folder/"
        val bytes = ByteArray(4097) { (it % 251).toByte() }
        private val collection = MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        private var row: Uri? = null
        private var id: Long? = null
        private var published = false
        private val identityWhere = "${MediaStore.MediaColumns.OWNER_PACKAGE_NAME} = ? AND " +
            "${MediaStore.MediaColumns.DISPLAY_NAME} = ? AND ${MediaStore.MediaColumns.RELATIVE_PATH} = ?"
        private val identityArgs get() = arrayOf(context.packageName, fileName, relativePath)

        fun create() {
            check(row == null && id == null && !published)
            // Query only the proposed random relative directory; a collision refuses, not erases/reuses.
            assertNotNull(context.contentResolver.query(collection, arrayOf(MediaStore.MediaColumns._ID),
                "${MediaStore.MediaColumns.RELATIVE_PATH} = ?", arrayOf(relativePath), null)).use {
                check(!it.moveToFirst()) { "The unique MediaStore relative path already exists" }
            }
            val uri = assertNotNull(context.contentResolver.insert(collection, ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, fileName)
                put(MediaStore.MediaColumns.MIME_TYPE, "application/octet-stream")
                put(MediaStore.MediaColumns.RELATIVE_PATH, relativePath)
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }))
            row = uri // Retain the actual insertion receipt before any potentially failing operation.
            check(uri.scheme == "content" && uri.authority == collection.authority &&
                uri.pathSegments.dropLast(1) == collection.pathSegments && uri.query == null && uri.fragment == null)
            id = uri.lastPathSegment?.toLongOrNull()?.takeIf { it > 0 }
            check(id != null)
            assertIdentity()
            assertNotNull(context.contentResolver.openOutputStream(uri, "w")).use { it.write(bytes) }
            check(context.contentResolver.update(uri, ContentValues().apply { put(MediaStore.MediaColumns.IS_PENDING, 0) },
                identityWhere, identityArgs) == 1)
            published = true
            assertPublishedUnchanged()
        }

        private fun assertIdentity() {
            val uri = checkNotNull(row)
            assertNotNull(context.contentResolver.query(uri, arrayOf(MediaStore.MediaColumns._ID,
                MediaStore.MediaColumns.OWNER_PACKAGE_NAME, MediaStore.MediaColumns.DISPLAY_NAME,
                MediaStore.MediaColumns.RELATIVE_PATH, MediaStore.MediaColumns.IS_PENDING), null, null, null)).use { cursor ->
                check(cursor.moveToFirst() && cursor.getLong(0) == id && cursor.getString(1) == context.packageName &&
                    cursor.getString(2) == fileName && cursor.getString(3) == relativePath &&
                    cursor.getInt(4) in (if (published) setOf(0) else setOf(0, 1)) &&
                    !cursor.moveToNext()) { "The returned MediaStore row is not exclusively owned" }
            }
        }

        fun assertPublishedUnchanged() {
            check(published)
            assertIdentity()
            val actual = assertNotNull(context.contentResolver.openInputStream(checkNotNull(row))).use {
                it.readOwnedAtMost(bytes.size)
            }
            assertContentEquals(bytes, actual)
        }

        fun closeOwnedRow() {
            val uri = row ?: return
            assertIdentity() // Unknown/changed identity refuses any deletion.
            if (published) assertPublishedUnchanged()
            assertIdentity() // Fresh identity immediately precedes the narrow conditional item-URI delete.
            check(context.contentResolver.delete(uri, identityWhere, identityArgs) == 1) { "Exact owned MediaStore row deletion was not verified" }
            assertNotNull(context.contentResolver.query(uri, arrayOf(MediaStore.MediaColumns._ID), null, null, null)).use {
                check(!it.moveToFirst()) { "The deleted owned MediaStore row is still present" }
            }
            row = null
        }
    }

    private fun InputStream.readOwnedAtMost(maximum: Int): ByteArray {
        val output = ByteArrayOutputStream(maximum)
        val chunk = ByteArray(minOf(maximum + 1, 1024))
        while (true) {
            val read = read(chunk, 0, minOf(chunk.size, maximum + 1 - output.size()))
            if (read == -1) return output.toByteArray()
            check(read > 0) { "The owned MediaStore source made no progress" }
            output.write(chunk, 0, read)
            check(output.size() <= maximum) { "The owned MediaStore source exceeded its payload bound" }
        }
    }

    private fun waitUntil(condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 20_000
        while (true) {
            check(SystemClock.elapsedRealtime() < deadline) { "The exact named system-provider condition timed out" }
            val accepted = condition()
            check(SystemClock.elapsedRealtime() < deadline) { "A late named system-provider observation is refused" }
            if (accepted) return
            Thread.sleep(20)
        }
    }

    companion object {
        private const val EXTERNAL_AUTHORITY = "com.android.externalstorage.documents"
        private const val DOWNLOADS_AUTHORITY = "com.android.providers.downloads.documents"
    }
}
