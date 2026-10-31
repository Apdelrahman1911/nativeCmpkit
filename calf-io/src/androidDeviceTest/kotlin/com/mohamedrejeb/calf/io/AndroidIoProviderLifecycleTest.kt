// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.io

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.DeadObjectException
import android.os.Looper
import android.os.Process
import android.provider.DocumentsContract
import android.provider.OpenableColumns
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import coil3.ImageLoader
import coil3.decode.DataSource
import coil3.decode.Decoder
import coil3.request.CachePolicy
import coil3.request.ErrorResult
import coil3.request.ImageRequest
import com.mohamedrejeb.calf.picker.coil.KmpFileFetcher
import java.io.IOException
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.*
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Real Android grants/processes/descriptors and actual Coil pipeline; deterministic source/decoder fixtures. */
@RunWith(AndroidJUnit4::class)
class AndroidIoProviderLifecycleTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION

    @Test fun persistedTreeBookmarkSurvivesOwnedClientRestartAndExplicitRelease() = owned { control ->
        val runnerPid = Process.myPid()
        lateinit var first: Bundle
        OwnedIoEndpoint.bookmarkClient().use { client ->
            first = client.connect()
            grantTree { assertBookmarkReadable(client.request("remember")) }
            assertBookmarkReadable(client.request("restore"))
            val stopped = client.dieAndObserveBinderDeath()
            assertEquals(first.getInt("pid"), stopped.getInt("pid"))
            assertEquals(runnerPid, Process.myPid(), "Restart only the owned library client, never the reporter")
        }
        OwnedIoEndpoint.bookmarkClient().use { restarted ->
            val next = restarted.connect()
            assertNotEquals(first.getInt("pid"), next.getInt("pid"))
            assertNotEquals(first.getString("generation"), next.getString("generation"))
            assertBookmarkReadable(restarted.request("restore"))
            val released = restarted.request("release")
            assertFalse(released.getBoolean("restored")); assertFalse(released.getBoolean("persistedRead"))
            assertFalse(released.getBoolean("persistedWrite")); assertFalse(released.getBoolean("readGranted"))
            assertFalse(released.getBoolean("writeGranted")); assertNull(released.getString("uri"))
            assertFalse(released.getBoolean("exists")); assertFalse(released.getBoolean("directory"))
            assertNull(released.getString("name")); assertEquals("SecurityException", released.getString("readError"))
            restarted.request("clear")
        }
        assertQuiescent(control)
    }

    @Test fun ownerRevocationDeniesTreeAndChildMetadataAndActualContentRead() = owned { control ->
        val bookmark = grantAndPersistTree()
        val root = KmpFile(AndroidIoProviderContract.tree)
        val child = KmpFile(AndroidIoProviderContract.child("bookmark.txt"))
        assertTreeMetadata(root)
        assertTrue(child.exists(context)); assertFalse(child.isDirectory(context))
        assertEquals("bookmark.txt", child.getName(context))
        assertEquals(AndroidIoProviderContract.bytes("bookmark.txt").size.toLong(), child.getSize(context))
        assertNull(child.getPath(context)); assertEquals(AndroidIoProviderContract.child("bookmark.txt").toString(), child.toUriString())
        val childrenUri = DocumentsContract.buildChildDocumentsUriUsingTree(AndroidIoProviderContract.tree, AndroidIoProviderContract.ROOT)
        val ids = assertNotNull(context.contentResolver.query(childrenUri, arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID), null, null, null)).use { cursor ->
            buildSet { while (cursor.moveToNext()) add(cursor.getString(0)) }
        }
        assertEquals(setOf("bookmark.txt", "decoder.bin", "cancel.bin", "survivor.bin"), ids)
        runBlocking(Dispatchers.IO) { assertContentEquals(AndroidIoProviderContract.bytes("bookmark.txt"), child.readByteArray(context)) }
        waitUntil { stats(control, "bookmark.txt").getInt("closes") == 1 }
        control.request("revoke")
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), read))
        assertNull(KmpFile.fromBookmark(bookmark, context))
        for (reference in listOf(root, child)) {
            assertFalse(reference.exists(context)); assertFalse(reference.isDirectory(context))
            assertNull(reference.getName(context)); assertNull(reference.getSize(context))
        }
        runBlocking(Dispatchers.IO) { assertFailsWith<SecurityException> { child.readByteArray(context) } }
        assertEquals(1, stats(control, "bookmark.txt").getInt("opens"), "Denied read must not reach the real provider's open")
        assertEquals(1, stats(control, "bookmark.txt").getInt("closes"))
    }

    @Test fun ownedProviderDeathProducesRealBinderFailureAndTreeMetadataRecovers() = owned { control ->
        val bookmark = grantAndPersistTree()
        val runnerPid = Process.myPid()
        val child = AndroidIoProviderContract.child("survivor.bin")
        val before = stats(control, "survivor.bin")
        assertEquals(0, before.getInt("opens")); assertEquals(0, before.getInt("closes"))
        // A stable ContentResolver PFD/cursor lease at death can cause Android to kill
        // its clients. This explicit case holds only an unstable client, with every
        // prior cursor/PFD closed. It does not reinterpret the historical signal-9.
        assertNotNull(context.contentResolver.acquireUnstableContentProviderClient(AndroidIoProviderContract.AUTHORITY)).use { stale ->
            assertNotNull(stale.query(child, arrayOf(OpenableColumns.SIZE), null, null, null)).use { cursor ->
                assertTrue(cursor.moveToFirst()); assertEquals(AndroidIoProviderContract.bytes("survivor.bin").size.toLong(), cursor.getLong(0))
            }
            OwnedIoEndpoint.providerWitness().use { witness ->
                val native = witness.connect()
                assertEquals(before.getInt("pid"), native.getInt("pid"))
                assertEquals(before.getString("generation"), native.getString("generation"))
                witness.dieAndObserveBinderDeath()
            }
            assertFailsWith<DeadObjectException> {
                stale.query(child, arrayOf(OpenableColumns.SIZE), null, null, null).use {
                    error("A dead owned provider unexpectedly returned a query result")
                }
            }
        }
        assertEquals(runnerPid, Process.myPid())
        assertNotNull(KmpFile.fromBookmark(bookmark, context))
        assertTreeMetadata(KmpFile(AndroidIoProviderContract.tree))
        assertEquals(AndroidIoProviderContract.bytes("survivor.bin").size.toLong(), KmpFile(child).getSize(context))
        runBlocking(Dispatchers.IO) { assertContentEquals(AndroidIoProviderContract.bytes("survivor.bin"), KmpFile(child).readByteArray(context)) }
        val after = stats(control, "survivor.bin")
        assertNotEquals(before.getInt("pid"), after.getInt("pid")); assertNotEquals(before.getString("generation"), after.getString("generation"))
        val identity = nativeRegularIdentity(after)
        assertNativeReleased(control, "survivor.bin", identity)
    }

    @Test fun nativeCoilDecoderFailureClosesCrossUidSourceAfterExactBinaryRead() = owned { control ->
        grantAndPersistTree()
        val id = "decoder.bin"
        val identity = AtomicReference<DeviceDescriptorIdentity>()
        val failure = IOException("NativeCmpKit decoder failed after actual remote binary read")
        withImageLoader { loader ->
            val request = imageRequest(id).decoderFactory(Decoder.Factory { result, _, _ -> Decoder {
                assertNotEquals(Looper.getMainLooper(), Looper.myLooper(), "The real provider read is dispatched off the UI Looper")
                assertEquals(DataSource.DISK, result.dataSource); assertEquals("application/octet-stream", result.mimeType)
                val actual = nativeRegularIdentity(stats(control, id)); identity.set(actual)
                assertTrue(openDeviceDescriptorsFor(actual) > 0)
                assertContentEquals(AndroidIoProviderContract.bytes(id), result.source.source().readByteArray())
                assertTrue(openDeviceDescriptorsFor(actual) > 0, "EOF retains close ownership until Coil ends decoding")
                throw failure
            } }).build()
            val reported = runBlocking(Dispatchers.IO) { assertIs<IOException>(assertIs<ErrorResult>(loader.execute(request)).throwable) }
            assertEquals(failure.message, reported.message)
            val causes = mutableSetOf<Throwable>(); var cause: Throwable? = reported
            while (cause != null && causes.size < 8 && causes.add(cause)) cause = cause.cause
            assertTrue(causes.any { it === failure }, "Coroutine recovery must retain the exact injected decoder origin")
            assertNativeReleased(control, id, assertNotNull(identity.get()))
        }
    }

    @Test fun nativeCoilCancellationClosesTransferredSourceWithoutLateSuccess() = owned { control ->
        grantAndPersistTree()
        val id = "cancel.bin"
        withImageLoader { loader ->
            runBlocking(Dispatchers.Default) {
                val entered = CompletableDeferred<DeviceDescriptorIdentity>()
                var succeeded = false
                val request = imageRequest(id).decoderFactory(Decoder.Factory { result, _, _ -> Decoder {
                    assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
                    val actual = nativeRegularIdentity(stats(control, id))
                    assertTrue(openDeviceDescriptorsFor(actual) > 0)
                    assertEquals(0, result.source.source().readByte().toInt())
                    entered.complete(actual)
                    awaitCancellation()
                } }).build()
                val job = launch { loader.execute(request); succeeded = true }
                var primary: Throwable? = null
                try {
                    val identity = withTimeout(20_000) { entered.await() }
                    assertEquals(0, stats(control, id).getInt("closes"))
                    assertTrue(openDeviceDescriptorsFor(identity) > 0)
                    withTimeout(20_000) { job.cancelAndJoin() }
                    assertTrue(job.isCancelled); assertFalse(succeeded)
                    assertNativeReleased(control, id, identity)
                } catch (failure: Throwable) { primary = failure; throw failure }
                finally {
                    try { withContext(NonCancellable) { withTimeout(20_000) { job.cancelAndJoin() } } }
                    catch (failure: Throwable) {
                        val first = primary
                        if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
                    }
                }
            }
        }
    }

    private fun imageLoader() = ImageLoader.Builder(context).components { add(KmpFileFetcher.Factory()) }.build()
    private fun imageRequest(id: String) = ImageRequest.Builder(context).data(KmpFile(AndroidIoProviderContract.child(id)))
        .memoryCachePolicy(CachePolicy.DISABLED).diskCachePolicy(CachePolicy.DISABLED).coroutineContext(Dispatchers.IO)

    /** ImageLoader cleanup cannot be skipped by cancelled join or replace the actual failure. */
    private fun withImageLoader(body: (ImageLoader) -> Unit) {
        val loader = imageLoader(); var primary: Throwable? = null
        try { body(loader) }
        catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            try { loader.shutdown() }
            catch (failure: Throwable) {
                val first = primary
                if (first == null) throw failure else if (first !== failure) first.addSuppressed(failure)
            }
        }
    }

    private fun assertBookmarkReadable(result: Bundle) {
        assertTrue(result.getBoolean("restored")); assertTrue(result.getBoolean("persistedRead")); assertFalse(result.getBoolean("persistedWrite"))
        assertTrue(result.getBoolean("readGranted")); assertFalse(result.getBoolean("writeGranted"))
        assertTrue(result.getBoolean("exists")); assertTrue(result.getBoolean("directory"))
        assertEquals(AndroidIoProviderContract.ROOT_NAME, result.getString("name"))
        assertEquals(AndroidIoProviderContract.tree.toString(), result.getString("uri"))
        assertNull(result.getString("readError")); assertEquals(AndroidIoProviderContract.bytes("bookmark.txt").size, result.getInt("bytes"))
        val expected = MessageDigest.getInstance("SHA-256").digest(AndroidIoProviderContract.bytes("bookmark.txt")).joinToString("") { "%02x".format(it.toInt() and 255) }
        assertEquals(expected, result.getString("sha256"))
    }
    private fun assertTreeMetadata(root: KmpFile) {
        assertTrue(root.exists(context)); assertTrue(root.isDirectory(context)); assertEquals(AndroidIoProviderContract.ROOT_NAME, root.getName(context))
        assertNull(root.getSize(context)); assertNull(root.getPath(context)); assertEquals(AndroidIoProviderContract.tree.toString(), root.toUriString())
    }
    private fun grantAndPersistTree(): String {
        var bookmark: String? = null
        grantTree { bookmark = assertNotNull(KmpFile(AndroidIoProviderContract.tree).createBookmark(context)) }
        return assertNotNull(bookmark)
    }
    private fun grantTree(takeBookmark: () -> Unit) {
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
            assertEquals(read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION,
                result.flags and (read or write or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION))
            assertEquals(PackageManager.PERMISSION_GRANTED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), read))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), write))
            takeBookmark()
        } // Destroy the native grant-owning Activity before restart, release or revocation assertions.
        val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == AndroidIoProviderContract.tree }
        assertTrue(persisted.isReadPermission); assertFalse(persisted.isWritePermission)
    }
    private fun stats(control: OwnedIoEndpoint, id: String): Bundle = assertNotNull(control.request("stats", id).getBundle("provider")).also {
        for (key in listOf("uid", "pid", "process", "generation", "opens", "closes", "closeErrors", "writes"))
            assertTrue(it.containsKey(key), "Missing native provider field")
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(provider.applicationInfo.uid, it.getInt("uid")); assertNotEquals(Process.myUid(), it.getInt("uid"))
        assertTrue(it.getInt("pid") > 0)
        assertNotEquals(Process.myPid(), it.getInt("pid")); assertEquals("${AndroidIoProviderContract.PACKAGE}:nativecmpkit_io_provider", it.getString("process"))
        assertTrue(assertNotNull(it.getString("generation")).matches(Regex("[a-f0-9-]{36}")))
    }
    private fun nativeRegularIdentity(state: Bundle): DeviceDescriptorIdentity {
        assertEquals(1, state.getInt("opens"))
        for (key in listOf("device", "inode", "mode", "fdInfoInode")) assertTrue(state.containsKey(key))
        return DeviceDescriptorIdentity.fromProviderRegularFile(state.getLong("device"), state.getLong("inode"), state.getInt("mode"), state.getLong("fdInfoInode"))
    }
    private fun assertNativeReleased(control: OwnedIoEndpoint, id: String, identity: DeviceDescriptorIdentity) {
        waitUntil { stats(control, id).getInt("closes") == 1 }
        val final = stats(control, id)
        assertEquals(1, final.getInt("opens")); assertEquals(1, final.getInt("closes"))
        assertEquals(0, final.getInt("closeErrors")); assertEquals(0, final.getInt("writes"))
        assertEquals(AndroidIoProviderContract.bytes(id).size.toLong(), final.getLong("length"))
        assertEquals(0, openDeviceDescriptorsFor(identity), "The real cross-UID transferred descriptor must be gone")
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
    private fun owned(body: (OwnedIoEndpoint) -> Unit) {
        assertEquals("true", InstrumentationRegistry.getArguments().getString("nativecmpkitOwnedIoDocuments"))
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals(instrumentation.context.packageName, context.packageName)
        assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission("android.permission.MANAGE_DOCUMENTS"))
        val provider = assertNotNull(context.packageManager.resolveContentProvider(AndroidIoProviderContract.AUTHORITY, 0))
        assertEquals(AndroidIoProviderContract.PACKAGE, provider.packageName); assertTrue(provider.exported); assertTrue(provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission); assertEquals("android.permission.MANAGE_DOCUMENTS", provider.writePermission)
        val control = OwnedIoEndpoint.control(); var primary: Throwable? = null
        try {
            control.connect()
            val prepared = assertNotNull(control.request("reset").getBundle("provider"))
            assertTrue(prepared.containsKey("uid") && prepared.containsKey("pid"))
            assertEquals(provider.applicationInfo.uid, prepared.getInt("uid")); assertTrue(prepared.getInt("pid") > 0)
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), read))
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkUriPermission(AndroidIoProviderContract.tree, Process.myPid(), Process.myUid(), write))
            body(control)
        }
        catch (failure: Throwable) { primary = failure; throw failure }
        finally {
            var cleanup: Throwable? = null
            for (action in listOf<() -> Unit>(
                { KmpFile(AndroidIoProviderContract.tree).releaseBookmark(context) },
                { assertQuiescent(control); control.request("reset") },
                { control.close() },
            )) try { action() } catch (failure: Throwable) {
                val first = primary ?: cleanup
                if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
            }
            if (primary == null) cleanup?.let { throw it }
        }
    }
    private fun waitUntil(condition: () -> Boolean) {
        val deadline = System.nanoTime() + 20_000_000_000L
        while (!condition()) { check(System.nanoTime() < deadline) { "Actual native IO condition timed out" }; Thread.sleep(20) }
    }
}
