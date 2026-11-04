// SPDX-License-Identifier: Apache-2.0
@file:Suppress("DEPRECATION")
package com.mohamedrejeb.calf.io

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.CancellationSignal
import android.os.Looper
import android.os.OperationCanceledException
import android.os.ParcelFileDescriptor
import android.os.Process
import android.os.SystemClock
import android.os.UserHandle
import android.provider.DocumentsContract
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import java.security.MessageDigest
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.io.Buffer
import kotlinx.io.RawSource
import kotlinx.io.readByteArray
import org.junit.Test
import org.junit.runner.RunWith
import kotlin.test.*

/** Two NEW native methods only. Controlled loopback is not commercial cloud/Downloads/restart/consumer acceptance. */
@RunWith(AndroidJUnit4::class)
class AndroidIoRemoteDocumentsTest {
    private val instrumentation get() = InstrumentationRegistry.getInstrumentation()
    private val context get() = instrumentation.targetContext
    private val read = Intent.FLAG_GRANT_READ_URI_PERMISSION
    private val write = Intent.FLAG_GRANT_WRITE_URI_PERMISSION

    @Test fun controlledRemoteTreeMetadataAndBoundedSourceCloseAreBackedByLiveHttp() = runBlocking(Dispatchers.IO) {
        withRemoteSession { owner ->
            val tree = owner.selectTree()
            val root = assertNotNull(owner.root)
            val immediateBefore = folderMetadataRequests(owner.providerStats(), owner.session)
            assertOwnedRoot(root, owner.session)
            assertTrue(folderMetadataRequests(owner.providerStats(), owner.session) > immediateBefore)
            val bookmark = assertNotNull(root.createBookmark(context)); owner.bookmark = bookmark
            assertEquals(tree.toString(), bookmark)
            val persisted = context.contentResolver.persistedUriPermissions.single { it.uri == tree }
            assertTrue(persisted.isReadPermission); assertEquals(owner.optionalWriteGrant, persisted.isWritePermission)
            owner.closeCaller()
            assertTrue(assertNotNull(owner.caller).destroyed)
            val restored = assertNotNull(KmpFile.fromBookmark(bookmark, context))
            val restoredBefore = folderMetadataRequests(owner.providerStats(), owner.session)
            assertOwnedRoot(restored, owner.session)
            assertEquals(tree, restored.uri)
            assertTrue(folderMetadataRequests(owner.providerStats(), owner.session) > restoredBefore)
            // Activity destruction/bookmark restoration above is explicitly NOT a native process restart.
            val payloadUri = ownedChildren(tree, owner.session).getValue(RemoteIoContract.payload(owner.session))
            val payload = KmpFile(payloadUri)
            assertTrue(payload.exists(context)); assertTrue(payload.isFile(context)); assertFalse(payload.isDirectory(context))
            assertEquals("payload.bin", payload.getName(context)); assertEquals(RemoteIoContract.PAYLOAD_BYTES.toLong(), payload.getSize(context))
            assertEquals("application/octet-stream", payload.getMimeType(context)); assertNull(payload.getPath(context))
            assertEquals(payloadUri.toString(), payload.toUriString()); assertNativeGrant(payloadUri, PackageManager.PERMISSION_GRANTED)
            val source = payload.source(context); owner.source = source
            source.use {
                val transfer = onlyContent(owner.providerStats(), RemoteIoContract.payload(owner.session))
                assertTrue(transfer.bool("pipeAllocated")); assertTrue(transfer.bool("descriptorReturned"))
                val identity = DeviceDescriptorIdentity.fromProvider(transfer.long("pipeDevice"), transfer.long("pipeInode"),
                    transfer.int("pipeMode"), transfer.long("fdInfoInode"))
                owner.identity = identity
                assertTrue(openDeviceDescriptorsFor(identity) > 0, "The actual public source must own the newly transferred FIFO")
                val buffer = Buffer()
                while (buffer.size < RemoteIoContract.PAYLOAD_BYTES) {
                    assertTrue(it.readAtMostTo(buffer, RemoteIoContract.PAYLOAD_BYTES.toLong() - buffer.size) > 0,
                        "The real remote source must progress to its exact bounded payload")
                }
                assertEquals(RemoteIoContract.PAYLOAD_BYTES.toLong(), buffer.size)
                val digest = sha256(buffer.readByteArray())
                assertEquals(owner.payloadHash, digest)
                val tail = Buffer()
                assertEquals(-1L, it.readAtMostTo(tail, 1)); assertEquals(0L, tail.size)
                assertTrue(openDeviceDescriptorsFor(identity) > 0, "EOF is not the caller's explicit FIFO close")
            }
            owner.source = null
            assertEquals(0, openDeviceDescriptorsFor(assertNotNull(owner.identity)))
            awaitNative("positive HTTP/native producer cleanup") { owner.transportQuiescent() }
            val provider = owner.providerStats(); val backend = owner.backendStats()
            assertCleanProvider(provider); assertCleanBackend(backend)
            assertEquals(1, provider.int("descriptorReturns"))
            val transfer = onlyContent(provider, RemoteIoContract.payload(owner.session))
            val server = sameRequest(backend, transfer.string("requestId"))
            assertSocketPair(transfer, server, owner.port)
            assertTrue(transfer.bool("producerSocketEof")); assertTrue(transfer.bool("terminal")); assertTrue(transfer.bool("workerTerminal"))
            assertTrue(transfer.bool("signalDetached")); assertEquals(0, transfer.int("cancellationAcknowledgments"))
            assertFalse(transfer.bool("readNativeOpen")); assertFalse(transfer.bool("writeNativeOpen")); assertFalse(transfer.bool("forcedCleanup"))
            assertEquals(RemoteIoContract.PAYLOAD_BYTES, transfer.int("bytesPiped")); assertEquals(owner.payloadHash, transfer.string("bodyHash"))
            assertEquals(RemoteIoContract.PAYLOAD_BYTES, server.int("bytesWritten")); assertEquals(owner.payloadHash, server.string("bodyHash"))
            assertTrue(server.bool("peerEof")); assertTrue(server.bool("socketClosed")); assertTrue(server.bool("workerTerminal"))
            assertFalse(server.bool("watchdogForced")); assertNull(server.getString("error")); assertNull(transfer.getString("error"))
        }
    }

    @Test fun nativePendingRemoteOpenCancellationReleasesHttpSocketWithoutTransferringDescriptor() = runBlocking(Dispatchers.IO) {
        withRemoteSession { owner ->
            val tree = owner.selectTree()
            val heldUri = ownedChildren(tree, owner.session).getValue(RemoteIoContract.held(owner.session))
            assertNativeGrant(heldUri, PackageManager.PERMISSION_GRANTED)
            val pending = PendingNativeOpen(heldUri); owner.pendingOpen = pending
            pending.start() // Future/executor/returned-PFD owners exist before the actual background native call.
            awaitNative("genuine HTTP held pending-open admission") {
                val records = owner.providerStats().records().filter { it.getString("route") == "content" }
                if (records.size != 1) false else {
                    val transfer = records.single()
                    val server = owner.backendStats().records().singleOrNull { it.getString("requestId") == transfer.getString("requestId") }
                    transfer.getString("phase") == "PENDING_FIRST_BODY" && transfer.bool("headersRead") &&
                        transfer.bool("socketConnected") && !transfer.bool("socketClosed") && !transfer.bool("pipeAllocated") &&
                        !transfer.bool("descriptorReturned") && transfer.int("cancellationAcknowledgments") == 0 &&
                        server != null && server.bool("headersSent") && server.bool("heldWaiting") && server.int("bytesWritten") == 0
                }
            }
            val before = onlyContent(owner.providerStats(), RemoteIoContract.held(owner.session))
            assertEquals(RemoteIoContract.HELD_BYTES, before.int("expectedBytes"))
            assertSocketPair(before, sameRequest(owner.backendStats(), before.string("requestId")), owner.port)
            pending.cancelFromVerifiedPending() // This actual CancellationSignal, not future interruption/timeout/control reset.
            pending.assertNativeCancellationAndJoin()
            awaitNative("cancellation socket/native producer terminal") { owner.transportQuiescent() }
            val provider = owner.providerStats(); val backend = owner.backendStats()
            assertCleanProvider(provider); assertCleanBackend(backend)
            assertEquals(0, provider.int("descriptorReturns"))
            val transfer = onlyContent(provider, RemoteIoContract.held(owner.session))
            val server = sameRequest(backend, transfer.string("requestId"))
            assertSocketPair(transfer, server, owner.port)
            assertEquals("CANCELLED_BEFORE_TRANSFER", transfer.string("phase"))
            assertEquals(1, transfer.int("cancellationAcknowledgments")); assertTrue(transfer.bool("listenerClosedSocket"))
            assertTrue(transfer.bool("operationCanceledObserved")); assertTrue(transfer.bool("signalDetached"))
            assertFalse(transfer.bool("pipeAllocated")); assertFalse(transfer.bool("descriptorReturned"))
            assertFalse(transfer.bool("readNativeOpen")); assertFalse(transfer.bool("writeNativeOpen")); assertFalse(transfer.bool("forcedCleanup"))
            assertTrue(transfer.bool("socketClosed")); assertTrue(transfer.bool("openingTerminal")); assertTrue(transfer.bool("workerTerminal"))
            assertEquals(0, transfer.int("bytesPiped")); assertEquals("OperationCanceledException", transfer.string("error"))
            assertEquals(0, server.int("bytesWritten")); assertTrue(server.bool("peerEof")); assertTrue(server.bool("socketClosed"))
            assertTrue(server.bool("workerTerminal")); assertTrue(server.bool("watchdogTerminal")); assertFalse(server.bool("watchdogForced"))
            assertNull(server.getString("error")); assertNull(server.getString("bodyHash"))
            // No dummy zero inode/FD scan. Actual failed native return + pre-allocation branch is the no-PFD witness.
            // This does NOT certify automatic KmpFile coroutine cancellation or post-transfer disconnection.
        }
    }

    private suspend fun withRemoteSession(block: suspend (RemoteSession) -> Unit) {
        val owner = RemoteSession(); var primary: Throwable? = null
        try { owner.prepare(); block(owner) }
        catch (failure: Throwable) { primary = failure; throw failure }
        finally { owner.cleanup(primary) }
    }
    private inner class RemoteSession {
        val session = RemoteIoContract.nonce()
        private val token = RemoteIoContract.nonce()
        var control: RemoteIoEndpoint? = null
        var provider: RemoteIoEndpoint? = null
        private var backendAttempted = false
        private var providerAttempted = false
        var port = 0; private set
        var payloadHash = ""; private set
        var scenario: ActivityScenario<AndroidIoRemoteTreeGrantActivity>? = null
        var caller: AndroidIoRemoteTreeGrantActivity? = null
        var ui: NamedSystemDocumentsUi? = null
        private val originalAccessibilityFlags = instrumentation.uiAutomation.serviceInfo.flags
        var root: KmpFile? = null
        var bookmark: String? = null
        var optionalWriteGrant = false; private set
        var source: RawSource? = null
        var identity: DeviceDescriptorIdentity? = null
        var pendingOpen: PendingNativeOpen? = null
        fun prepare() {
            requireNativeContext()
            val declared = assertNotNull(context.packageManager.resolveContentProvider(RemoteIoContract.AUTHORITY, 0))
            assertEquals(RemoteIoContract.PACKAGE, declared.packageName); assertEquals(RemoteIoContract.PACKAGE + ".RemoteIoDocumentsProvider", declared.name)
            assertEquals(RemoteIoContract.AUTHORITY, declared.authority); assertEquals(RemoteIoContract.PROVIDER_PROCESS, declared.processName)
            assertTrue(declared.exported && declared.grantUriPermissions)
            assertEquals("android.permission.MANAGE_DOCUMENTS", declared.readPermission); assertEquals("android.permission.MANAGE_DOCUMENTS", declared.writePermission)
            assertNotEquals(Process.myUid(), declared.applicationInfo.uid)
            assertTrue(declared.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE != 0)
            assertNativeGrant(DocumentsContract.buildTreeDocumentUri(RemoteIoContract.AUTHORITY, RemoteIoContract.folder(session)), PackageManager.PERMISSION_DENIED)
            control = RemoteIoEndpoint.control(); val backendIdentity = assertNotNull(control).connect()
            provider = RemoteIoEndpoint.providerWitness(); val providerIdentity = assertNotNull(provider).connect()
            assertEquals(backendIdentity.int("uid"), providerIdentity.int("uid")); assertEquals(declared.applicationInfo.uid, providerIdentity.int("uid"))
            assertNotEquals(backendIdentity.int("pid"), providerIdentity.int("pid"))
            assertNotEquals(backendIdentity.string("generation"), providerIdentity.string("generation"))
            backendAttempted = true
            val backend = assertNotNull(assertNotNull(control).request("prepare", session, token).getBundle("backend"))
            port = backend.int("port"); check(port in 1024..65535); assertTrue(backend.bool("listenerLoopback"))
            assertFalse(backend.bool("listenerClosed")); assertEquals(RemoteIoContract.PAYLOAD_BYTES, backend.int("payloadBytes"))
            payloadHash = backend.string("payloadHash"); check(payloadHash.matches(Regex("[a-f0-9]{64}")))
            providerAttempted = true
            val prepared = assertNotNull(assertNotNull(provider).request("prepare", session, token, port).getBundle("provider"))
            assertTrue(prepared.bool("rootProvisionedOverHttp")); assertEquals(port, prepared.int("port"))
            awaitNative("root provisioning socket cleanup") { transportQuiescent() }
            val provision = providerStats().records().single { it.getString("route") == "root" }
            assertSocketPair(provision, sameRequest(backendStats(), provision.string("requestId")), port)
            assertTrue(provision.bool("terminal")); assertCleanProvider(providerStats()); assertCleanBackend(backendStats())
            // Public roots construction is not a grant. The ordinary reporter still cannot query owned folder content.
            assertFailsWith<SecurityException> {
                context.contentResolver.query(DocumentsContract.buildDocumentUri(RemoteIoContract.AUTHORITY, RemoteIoContract.folder(session)),
                    null, null, null, null)?.close()
            }
        }
        fun selectTree(): Uri {
            val active = ActivityScenario.launch(AndroidIoRemoteTreeGrantActivity::class.java); scenario = active
            active.onActivity { caller = it }
            val activity = assertNotNull(caller)
            awaitNative("real caller foreground/draw") { activity.firstDraw && activity.hasWindowFocus() }
            active.onActivity { it.selectRemoteTree(session) }
            ui = NamedSystemDocumentsUi(assertNotNull(activity.documentsUiPackage))
            assertNotNull(ui).selectOwnedFolder(RemoteIoContract.folderName(session))
            awaitNative("actual system tree result") { activity.resultCode != null }
            assertEquals(1, activity.resultCount); assertEquals(Activity.RESULT_OK, activity.resultCode)
            val result = assertNotNull(activity.result); val tree = assertNotNull(result.data)
            // Reject foreign references before metadata/persistence/child reads.
            check(tree.scheme == "content" && tree.authority == RemoteIoContract.AUTHORITY && tree.query == null && tree.fragment == null)
            check(DocumentsContract.isTreeUri(tree) && tree.pathSegments.size == 2 && tree.pathSegments[0] == "tree")
            check(DocumentsContract.getTreeDocumentId(tree) == RemoteIoContract.folder(session))
            val required = read or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION or Intent.FLAG_GRANT_PREFIX_URI_PERMISSION
            assertEquals(required, result.flags and required)
            result.clipData?.let { check(it.itemCount == 1 && it.getItemAt(0).uri == tree) }
            assertNativeGrant(tree, PackageManager.PERMISSION_GRANTED)
            optionalWriteGrant = result.flags and write != 0 // Genuine DocumentsUI may grant write even to readonly content.
            root = KmpFile(tree); return tree
        }
        fun closeCaller() { scenario?.close(); scenario = null }
        fun providerStats(): Bundle = assertNotNull(assertNotNull(provider).request("stats", session).getBundle("provider"))
        fun backendStats(): Bundle = assertNotNull(assertNotNull(control).request("stats", session).getBundle("backend"))
        fun transportQuiescent(): Boolean {
            val provider = providerStats(); val backend = backendStats()
            return provider.int("activeTransfers") == 0 && provider.int("activeSockets") == 0 && provider.int("activeWorkers") == 0 &&
                backend.int("activeConnections") == 0 && backend.records().all { it.bool("workerTerminal") && it.bool("watchdogTerminal") && it.bool("socketClosed") }
        }
        fun cleanup(primary: Throwable?) {
            var cleanup: Throwable? = null
            fun attempt(action: () -> Unit) {
                try { action() } catch (failure: Throwable) {
                    val first = primary ?: cleanup
                    if (first == null) cleanup = failure else if (first !== failure) first.addSuppressed(failure)
                }
            }
            attempt { pendingOpen?.close() }
            attempt { source?.close(); source = null }
            attempt { closeCaller() }
            attempt { root?.releaseBookmark(context) }
            attempt { ui?.close() }
            attempt { assertEquals(originalAccessibilityFlags, instrumentation.uiAutomation.serviceInfo.flags) }
            attempt { if (backendAttempted) assertTrue(assertNotNull(control).request("revoke", session).bool("ownerRevokeReturned")) }
            attempt {
                val tree = DocumentsContract.buildTreeDocumentUri(RemoteIoContract.AUTHORITY, RemoteIoContract.folder(session))
                assertFalse(context.contentResolver.persistedUriPermissions.any { it.uri == tree })
                assertNativeGrant(tree, PackageManager.PERMISSION_DENIED)
                assertNativeGrant(DocumentsContract.buildDocumentUriUsingTree(tree, RemoteIoContract.payload(session)), PackageManager.PERMISSION_DENIED)
                bookmark?.let { assertNull(KmpFile.fromBookmark(it, context)) }
            }
            attempt { identity?.let { assertEquals(0, openDeviceDescriptorsFor(it)) } }
            attempt {
                if (providerAttempted) {
                    val stopped = assertNotNull(assertNotNull(provider).request("stop", session).getBundle("provider"))
                    assertTrue(stopped.bool("stopped")); assertEquals(0, stopped.int("activeTransfers"))
                    assertEquals(0, stopped.int("activeSockets")); assertEquals(0, stopped.int("activeWorkers")); assertEquals(0, stopped.int("cleanupErrors"))
                }
            }
            attempt {
                if (backendAttempted) {
                    val stopped = assertNotNull(assertNotNull(control).request("stop", session).getBundle("backend"))
                    assertTrue(stopped.bool("stopped")); assertTrue(stopped.bool("dataCleared")); assertTrue(stopped.bool("listenerClosed"))
                    assertTrue(stopped.bool("acceptorTerminal")); assertEquals(0, stopped.int("activeConnections")); assertEquals(0, stopped.int("cleanupErrors"))
                }
            }
            // Independent acknowledgments + real Binder death, then reply-thread join. No controller-only green fallback.
            attempt { if (providerAttempted) assertNotNull(provider).dieAndObserveBinderDeath(session) }
            attempt { if (backendAttempted) assertNotNull(control).dieAndObserveBinderDeath(session) }
            attempt { provider?.close() }
            attempt { control?.close() }
            if (primary == null) cleanup?.let { throw it }
        }
    }

    private inner class PendingNativeOpen(private val uri: Uri) : AutoCloseable {
        private val signal = CancellationSignal()
        private val returned = AtomicReference<ParcelFileDescriptor?>()
        private var nativeThread: Thread? = null
        private val executor = Executors.newSingleThreadExecutor { task ->
            Thread(task, "nativecmpkit-remote-io-native-open").also { nativeThread = it }
        }
        private var future: Future<ParcelFileDescriptor?>? = null
        private var verifiedCancellationInvoked = false
        fun start() {
            check(future == null)
            future = executor.submit<ParcelFileDescriptor?> {
                context.contentResolver.openFileDescriptor(uri, "r", signal).also { descriptor ->
                    if (descriptor != null) check(returned.compareAndSet(null, descriptor))
                }
            }
        }
        fun cancelFromVerifiedPending() { check(!verifiedCancellationInvoked); verifiedCancellationInvoked = true; signal.cancel() }
        fun assertNativeCancellationAndJoin() {
            check(verifiedCancellationInvoked)
            val failure = try { assertNotNull(future).get(20, TimeUnit.SECONDS); fail("Native pending open unexpectedly returned a descriptor") }
                catch (failure: ExecutionException) { assertNotNull(failure.cause) }
            assertIs<OperationCanceledException>(failure)
            assertNull(returned.get(), "Actual failed native result must not transfer a PFD")
            executor.shutdown(); assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS))
            assertFalse(assertNotNull(nativeThread).isAlive, "The owned caller's actual open worker must terminate")
        }
        override fun close() {
            var primary: Throwable? = null
            fun attempt(action: () -> Unit) {
                try { action() } catch (failure: Throwable) { if (primary == null) primary = failure else primary!!.addSuppressed(failure) }
            }
            attempt { returned.getAndSet(null)?.close() }
            // Failure-only cleanup cancellation/interruption is never admitted as the verified functional cancellation above.
            attempt { if (!signal.isCanceled) signal.cancel() }
            attempt { future?.takeUnless { it.isDone }?.cancel(true); executor.shutdownNow() }
            attempt { assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS)); nativeThread?.let { assertFalse(it.isAlive) } }
            attempt { returned.getAndSet(null)?.close() } // Also close a late native result after the joined worker.
            primary?.let { throw it }
        }
    }

    private fun requireNativeContext() {
        assertEquals(35, Build.VERSION.SDK_INT); assertTrue(Build.HARDWARE in setOf("ranchu", "goldfish"))
        assertEquals(UserHandle.getUserHandleForUid(0), Process.myUserHandle())
        assertEquals("com.mohamedrejeb.calf.calfio.test", context.packageName)
        assertEquals(context.packageName, instrumentation.context.packageName); assertNotEquals(Looper.getMainLooper(), Looper.myLooper())
        assertEquals("en", context.resources.configuration.locales[0].language)
        assertTrue(context.contentResolver.persistedUriPermissions.isEmpty(), "Never release preexisting grants")
        for (permission in listOf("android.permission.MANAGE_DOCUMENTS", Manifest.permission.MANAGE_EXTERNAL_STORAGE,
            Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE,
            Manifest.permission.READ_MEDIA_IMAGES, Manifest.permission.READ_MEDIA_VIDEO, Manifest.permission.READ_MEDIA_AUDIO)) {
            assertEquals(PackageManager.PERMISSION_DENIED, context.checkSelfPermission(permission))
        }
    }
    private fun assertOwnedRoot(root: KmpFile, session: String) {
        assertTrue(root.exists(context)); assertTrue(root.isDirectory(context)); assertFalse(root.isFile(context))
        assertEquals(RemoteIoContract.folderName(session), root.getName(context)); assertNull(root.getSize(context)); assertNull(root.getPath(context))
        assertEquals(root.uri.toString(), root.toUriString())
    }
    private fun ownedChildren(tree: Uri, session: String): Map<String, Uri> {
        val folder = RemoteIoContract.folder(session)
        val uri = DocumentsContract.buildChildDocumentsUriUsingTree(tree, folder)
        return assertNotNull(context.contentResolver.query(uri, arrayOf(DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME, DocumentsContract.Document.COLUMN_MIME_TYPE, DocumentsContract.Document.COLUMN_SIZE),
            null, null, null)).use { cursor ->
            check(cursor.count == 2); val result = linkedMapOf<String, Uri>()
            val expected = listOf(Triple(RemoteIoContract.payload(session), "payload.bin", RemoteIoContract.PAYLOAD_BYTES),
                Triple(RemoteIoContract.held(session), "held.bin", RemoteIoContract.HELD_BYTES))
            for ((id, name, size) in expected) {
                check(cursor.moveToNext()); check(cursor.getString(0) == id && cursor.getString(1) == name &&
                    cursor.getString(2) == "application/octet-stream" && !cursor.isNull(3) && cursor.getLong(3) == size.toLong())
                val child = DocumentsContract.buildDocumentUriUsingTree(tree, id)
                check(child.authority == RemoteIoContract.AUTHORITY && DocumentsContract.isTreeUri(child) && DocumentsContract.isDocumentUri(context, child))
                result[id] = child
            }
            check(!cursor.moveToNext()); result
        }
    }
    private fun assertNativeGrant(uri: Uri, expected: Int) =
        assertEquals(expected, context.checkUriPermission(uri, Process.myPid(), Process.myUid(), read))
    private fun folderMetadataRequests(state: Bundle, session: String) =
        state.records().count { it.getString("route") == "metadata" && it.getString("documentId") == RemoteIoContract.folder(session) }
    private fun onlyContent(state: Bundle, id: String): Bundle =
        state.records().filter { it.getString("route") == "content" }.single().also { assertEquals(id, it.string("documentId")) }
    private fun sameRequest(backend: Bundle, requestId: String): Bundle = backend.records().single { it.getString("requestId") == requestId }
    private fun assertSocketPair(provider: Bundle, backend: Bundle, port: Int) {
        assertTrue(provider.bool("socketConnected")); assertTrue(backend.bool("nativeLoopback"))
        assertEquals(provider.string("requestId"), backend.string("requestId"))
        assertEquals(provider.string("documentId"), backend.string("documentId")); assertEquals(provider.string("route"), backend.string("route"))
        assertTrue(provider.int("localPort") > 0); assertEquals(port, provider.int("peerPort"))
        assertEquals(provider.int("localPort"), backend.int("peerPort")); assertEquals(provider.int("peerPort"), backend.int("localPort"))
    }
    private fun assertCleanProvider(state: Bundle) { assertEquals(0, state.int("errors")); assertEquals(0, state.int("cleanupErrors")) }
    private fun assertCleanBackend(state: Bundle) { assertEquals(0, state.int("errors")); assertEquals(0, state.int("cleanupErrors")) }
    private fun awaitNative(label: String, predicate: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + 20_000
        while (SystemClock.elapsedRealtime() < deadline) {
            if (predicate()) { check(SystemClock.elapsedRealtime() < deadline) { "Late native admission refused" }; return }
            Thread.sleep(20)
        }
        fail("Owned native gate timed out: $label") // Polling is cooperative, not a hard native/kernel deadline.
    }
    private fun sha256(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
        .joinToString("") { "%02x".format(it.toInt() and 255) }
    private fun Bundle.int(key: String): Int { assertTrue(containsKey(key)); return assertIs<Int>(get(key)) }
    private fun Bundle.long(key: String): Long { assertTrue(containsKey(key)); return assertIs<Long>(get(key)) }
    private fun Bundle.bool(key: String): Boolean { assertTrue(containsKey(key)); return assertIs<Boolean>(get(key)) }
    private fun Bundle.string(key: String): String { assertTrue(containsKey(key)); return assertIs<String>(get(key)) }
    private fun Bundle.records(): List<Bundle> {
        val records = assertNotNull(getParcelableArrayList<Bundle>("journal")); check(records.size <= 128)
        // A newly accepted socket may not yet have a parsed request. Preserve that partial record, never call it absence.
        val admittedIds = records.mapNotNull { it.getString("requestId") }
        check(admittedIds.all { it.matches(Regex("[a-f0-9]{32}")) } && admittedIds.distinct().size == admittedIds.size)
        return records
    }
}
