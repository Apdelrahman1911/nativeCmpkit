@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.uikit.LocalUIViewController
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.io.readByteArray
import com.mohamedrejeb.calf.io.source
import com.mohamedrejeb.calf.picker.internal.*
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.alloc
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.ptr
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.io.buffered
import kotlinx.io.readByteArray
import platform.Foundation.*
import platform.PhotosUI.PHPickerViewController
import platform.UIKit.UIViewController
import platform.UniformTypeIdentifiers.UTTypeImage
import platform.posix.fstat
import platform.posix.getdtablesize
import platform.posix.stat
import platform.posix.usleep
import kotlin.concurrent.AtomicInt
import kotlin.test.*

/**
 * Actual public Compose/session + registered Foundation NSItemProvider transport.
 * Only post-extraction provider arrival is controlled through the installed owning
 * delegate's internal shared-guard entry. The real registered providers then follow
 * the public launcher's existing staging path. No unavailable Photos result construction,
 * hidden KVC, forged KmpFile, fake progress, manual private continuation resume,
 * Photos-library selection or cloud-scope claim.
 */
class NativePhotoProviderCancellationTest {
    @Test fun publicPhotoCancellationStopsAnInFlightNativeProviderCopyAndReleasesEarlierStaging() = runApplicationUiTest {
        val bytes = ByteArray(131_079) { ((it * 37 + 11) % 251).toByte() }
        val fixtures = mutableListOf<OwnedNativeProviderCopy>()
        var primaryFailure: Throwable? = null
        val before = pickerDirectories()
        val included = mutableStateOf(true)
        val delivered = mutableListOf<List<KmpFile>>()
        val errors = mutableListOf<FilePickerException>()
        lateinit var parent: UIViewController
        lateinit var launcher: FilePickerLauncher
        try {
            val first = OwnedNativeProviderCopy(bytes, holdAfterFirstChunk = false).also(fixtures::add)
            val pending = OwnedNativeProviderCopy(bytes, holdAfterFirstChunk = true).also(fixtures::add)
            setContent {
                parent = LocalUIViewController.current
                if (included.value) {
                    val current = rememberFilePickerLauncher(
                        FilePickerFileType.Image, FilePickerSelectionMode.Multiple(2),
                        FilePickerSettings(imageRepresentationMode = ImageRepresentationMode.Current),
                        onError = { assertTrue(NSThread.isMainThread); errors += it },
                        onResult = { assertTrue(NSThread.isMainThread); delivered += it },
                    )
                    SideEffect { launcher = current }
                }
            }
            waitForIdle()
            val retained = runOnIdle { launcher.also { it.launch() } }
            waitForNative { parent.presentedViewController is PHPickerViewController &&
                !parent.presentedViewController!!.isBeingPresented() }
            val picker = runOnIdle { assertIs<PHPickerViewController>(parent.presentedViewController) }
            val delegate = runOnIdle { assertIs<PhotoPickerDelegate>(picker.delegate) }
            val providers = listOf(first.provider, pending.provider)
            runOnIdle {
                assertTrue(sameNativeObject(providers[0], first.provider))
                assertTrue(sameNativeObject(providers[1], pending.provider))
                delegate.pickerProviders(picker, providers)
            }
            waitForNative { first.provider.clientReturned.value == 1 && pending.firstChunkCopied.value == 1 &&
                parent.presentedViewController == null }
            first.requireNoFailure()
            pending.requireNoFailure()
            assertEquals(1, first.starts.value)
            assertEquals(1, pending.starts.value)
            assertEquals(1, first.provider.loadRequests.value)
            assertEquals(1, pending.provider.loadRequests.value)
            assertEquals(0, pending.cancelled.value)
            val partialIdentity = pending.partialIdentity()
            assertEquals(listOf(1, 1), ownedDescriptorCounts(pending.sourceIdentity, partialIdentity),
                "A real provider input and partial-copy output must still be open before public cancellation")
            val staged = onlyNewPickedFile(before)
            val stagedIdentity = nativeIdentity(staged.url)
            runBlocking(Dispatchers.Default) {
                // New transport calibration, not a replay of accepted sandbox-only staging tests.
                staged.source().buffered().use { source ->
                    assertEquals(listOf(1), ownedDescriptorCounts(stagedIdentity))
                    assertContentEquals(bytes, source.readByteArray())
                }
            }
            assertEquals(listOf(0), ownedDescriptorCounts(stagedIdentity))
            runOnIdle {
                assertTrue(delivered.isEmpty()); assertTrue(errors.isEmpty())
                delegate.pickerProviders(picker, providers) // Actual delegate duplicate, not a second transport request.
            }
            assertEquals(1, first.starts.value)
            assertEquals(1, pending.starts.value)
            assertEquals(1, first.provider.loadRequests.value)
            assertEquals(1, pending.provider.loadRequests.value)
            assertEquals(before.size + 1, pickerDirectories().size)

            runOnIdle { included.value = false } // Public DisposableEffect + composition-owned Job cancel.
            waitForIdle()
            waitForNative { pending.cancelled.value == 1 && pending.closedHandles.value == 2 &&
                !NSFileManager.defaultManager.fileExistsAtPath(pending.partialPath) && pickerDirectories() == before }
            pending.requireNoFailure()
            assertEquals(2, pending.closedHandles.value)
            assertEquals(listOf(0, 0, 0),
                ownedDescriptorCounts(pending.sourceIdentity, partialIdentity, stagedIdentity))
            assertFalse(NSFileManager.defaultManager.fileExistsAtPath(pending.partialPath))
            assertTrue(NSFileManager.defaultManager.fileExistsAtPath(pending.sourcePath))

            // The actual held registered producer completion is still ours. Foundation
            // may already have acknowledged cancellation to its client; no callback order
            // or NSError identity is required. Record the paired client state descriptively,
            // then acknowledge the real producer invocation/normal return AND native client.
            assertEquals(0, pending.heldCompletionIssued.value)
            assertEquals(0, pending.heldCompletionReturned.value)
            val clientBeforeHeldCompletion = pending.provider.clientCounts()
            pending.completeCancelledTransport()
            waitForNative { pending.provider.clientReturned.value == 1 &&
                pending.heldCompletionReturned.value == 1 }
            runOnIdle {
                delegate.pickerProviders(picker, providers) // Captured old native delegate after disposal.
                retained.launch() // A disposed public launcher must not revive the old owner.
                assertTrue(delivered.isEmpty()); assertTrue(errors.isEmpty())
                assertNull(parent.presentedViewController)
            }
            assertEquals(1, first.starts.value)
            assertEquals(1, pending.starts.value)
            assertEquals(1, first.provider.loadRequests.value)
            assertEquals(1, pending.provider.loadRequests.value)
            assertEquals(1, pending.cancelled.value)
            assertEquals(1, pending.provider.clientEntered.value)
            assertEquals(1, pending.provider.clientReturned.value)
            assertEquals(1, pending.heldCompletionIssued.value)
            assertEquals(1, pending.heldCompletionReturned.value)
            assertEquals(before, pickerDirectories())
            assertEquals(listOf(0, 0, 0),
                ownedDescriptorCounts(pending.sourceIdentity, partialIdentity, stagedIdentity))
            runBlocking(Dispatchers.Default) {
                assertContentEquals(bytes, KmpFile(NSURL.fileURLWithPath(pending.sourcePath)).readByteArray())
            }
            assertEquals(listOf(0), ownedDescriptorCounts(pending.sourceIdentity))
            println("NATIVECMPKIT_PROVIDER_CANCEL starts=2 childCancel=1 pendingClosed=2 stagingBaseline=true publicCallbacks=0 nativeClientReturns=2 heldProducerReturns=1 clientBeforeHeldCompletion=" + clientBeforeHeldCompletion)
        } catch (error: Throwable) {
            primaryFailure = error
            throw error
        } finally {
            // Cleanup does not count as the cancellation witness above. Never manually
            // remove the library staging area; the public owner must release its copies.
            var cleanupFailure: Throwable? = null
            fun clean(action: () -> Unit) {
                try { action() } catch (error: Throwable) {
                    val prior = cleanupFailure
                    if (prior == null) cleanupFailure = error else prior.addSuppressed(error)
                }
            }
            clean { setContent {}; waitForIdle() }
            fixtures.forEach { fixture -> clean { fixture.close() } }
            cleanupFailure?.let { cleanup ->
                val prior = primaryFailure
                if (prior == null) throw cleanup else if (prior !== cleanup) prior.addSuppressed(cleanup)
            }
        }
    }
}

/** Instrument the real Foundation client callback and return its NSProgress unchanged. */
private class WitnessedNativeItemProvider : NSItemProvider() {
    val loadRequests = AtomicInt(0)
    val clientEntered = AtomicInt(0)
    val clientReturned = AtomicInt(0)
    private val lock = NSLock()
    private var cleanupStarted = false
    private var actualProgress: NSProgress? = null
    override fun loadFileRepresentationForTypeIdentifier(
        typeIdentifier: String, completionHandler: (NSURL?, NSError?) -> Unit,
    ): NSProgress {
        protect {
            check(!cleanupStarted) { "A closed fixture must not begin another native request" }
            loadRequests.incrementOwned()
        }
        val progress = super.loadFileRepresentationForTypeIdentifier(typeIdentifier) { url, error ->
            protect { clientEntered.incrementOwned() }
            try { completionHandler(url, error) } finally {
                protect { clientReturned.incrementOwned() }
            }
        }
        protect { actualProgress = progress }
        return progress
    }
    // A snapshot before the explicit producer call, not a causal/payload classification.
    fun clientCounts(): List<Int> = protect {
        listOf(clientEntered.value, clientReturned.value)
    }
    fun cancelForCleanup() {
        val progress = protect { cleanupStarted = true; actualProgress }
        progress?.cancel()
    }
    private fun <T> protect(action: () -> T): T { lock.lock(); try { return action() } finally { lock.unlock() } }
}

/**
 * Actual cooperative native producer: opens two NSFileHandles, copies one 64-KiB
 * chunk, then either completes or holds its real registered completion/NSProgress.
 * The advertised image representation is copied as opaque encoded bytes; no format
 * filter/decode acceptance is claimed. Source/destination are nonce-owned sandbox files.
 */
private class OwnedNativeProviderCopy(bytes: ByteArray, private val holdAfterFirstChunk: Boolean) {
    private val manager = NSFileManager.defaultManager
    private val root = "${NSTemporaryDirectory().removeSuffix("/")}/nativecmpkit-provider-${NSUUID().UUIDString}"
    val sourcePath = "$root/source.png"
    val partialPath = "$root/representation.png"
    val sourceIdentity: NativeInode
    val provider = WitnessedNativeItemProvider()
    val starts = AtomicInt(0)
    val firstChunkCopied = AtomicInt(0)
    val cancelled = AtomicInt(0)
    val closedHandles = AtomicInt(0)
    val heldCompletionIssued = AtomicInt(0)
    val heldCompletionReturned = AtomicInt(0)
    private val lock = NSLock()
    private var failure: Throwable? = null
    private var cleanupStarted = false
    private var input: NSFileHandle? = null
    private var output: NSFileHandle? = null
    private var copiedIdentity: NativeInode? = null
    private var completion: ((NSURL?, Boolean, NSError?) -> Unit)? = null
    private var nativeProgress: NSProgress? = null

    init {
        var created = false
        try {
            check(!manager.fileExistsAtPath(root)) { "Refuse a preexisting provider fixture root" }
            check(manager.createDirectoryAtPath(root, true, null, null))
            created = true
            val data = bytes.usePinned { NSData.create(bytes = it.addressOf(0), length = bytes.size.toULong()) }
            check(data.writeToURL(NSURL.fileURLWithPath(sourcePath), atomically = true))
            sourceIdentity = nativeIdentity(NSURL.fileURLWithPath(sourcePath))
            provider.registerFileRepresentationForTypeIdentifier(
                UTTypeImage.identifier, fileOptions = 0L,
                visibility = NSItemProviderRepresentationVisibilityOwnProcess,
            ) { handler ->
                val progress = NSProgress(parent = null, userInfo = null)
                progress.totalUnitCount = bytes.size.toLong()
                progress.cancellable = true
                progress.cancellationHandler = {
                    if (cancelled.compareAndSet(0, 1)) {
                        protect { closeHandlesLocked(); removePartialLocked() }
                    }
                }
                if (handler == null) {
                    recordFailure(IllegalStateException("The actual native registered completion was absent"))
                } else try {
                    val accepted = handler
                    protect {
                        completion = accepted
                        nativeProgress = progress
                        check(!cleanupStarted) { "A closing fixture must not open native producer files" }
                        check(starts.incrementOwned() == 1) { "A registered producer was started more than once" }
                        input = assertNotNull(NSFileHandle.fileHandleForReadingAtPath(sourcePath))
                        check(manager.createFileAtPath(partialPath, contents = NSData(), attributes = null))
                        output = assertNotNull(NSFileHandle.fileHandleForWritingAtPath(partialPath))
                        copiedIdentity = nativeIdentity(NSURL.fileURLWithPath(partialPath))
                        val chunk = assertNotNull(input).readDataOfLength(65_536uL)
                        check(chunk.length == 65_536uL)
                        assertNotNull(output).writeData(chunk)
                        progress.completedUnitCount = chunk.length.toLong()
                        firstChunkCopied.value = 1
                    }
                    if (!holdAfterFirstChunk) {
                        protect {
                            while (true) {
                                val chunk = assertNotNull(input).readDataOfLength(65_536uL)
                                if (chunk.length == 0uL) break
                                assertNotNull(output).writeData(chunk)
                                progress.completedUnitCount += chunk.length.toLong()
                            }
                            closeHandlesLocked()
                        }
                        resolve(NSURL.fileURLWithPath(partialPath), null)
                    }
                } catch (error: Throwable) {
                    recordFailure(error)
                    protect { closeHandlesLocked(); removePartialLocked() }
                    if (protect { completion != null }) resolve(null, cancellationError())
                }
                progress
            }
        } catch (error: Throwable) {
            if (created) {
                try { check(manager.removeItemAtPath(root, null)) } catch (cleanup: Throwable) {
                    if (cleanup !== error) error.addSuppressed(cleanup)
                }
            }
            throw error
        }
    }

    fun partialIdentity(): NativeInode = protect { assertNotNull(copiedIdentity) }
    fun requireNoFailure() { protect { failure?.let { throw it } } }

    fun completeCancelledTransport() {
        check(cancelled.value == 1) { "Observe native child cancellation before completing its transport" }
        check(closedHandles.value == 2) { "Observe both native producer handle closes before completing its transport" }
        check(!manager.fileExistsAtPath(partialPath))
        val handler = protect {
            check(holdAfterFirstChunk && !cleanupStarted) { "Only the held live producer may acknowledge this completion" }
            val pending = assertNotNull(completion)
            check(heldCompletionIssued.compareAndSet(0, 1)) { "A held producer completion must not be issued twice" }
            completion = null
            pending
        }
        // This is the actual registered Foundation producer completion. Its normal
        // return is not a client callback, a late URL, or an NSError-identity witness.
        handler.invoke(null, false, cancellationError())
        check(heldCompletionReturned.compareAndSet(0, 1)) { "A held producer completion must not return twice" }
    }

    private fun resolve(url: NSURL?, error: NSError?) {
        val handler = protect { completion.also { completion = null } }
        assertNotNull(handler).invoke(url, false, error)
    }

    private fun closeHandlesLocked() {
        val handles = listOf(input, output)
        input = null; output = null
        handles.filterNotNull().forEach { handle ->
            try { handle.closeFile(); closedHandles.incrementOwned() } catch (error: Throwable) { recordFailureLocked(error) }
        }
    }

    private fun removePartialLocked() {
        try {
            if (manager.fileExistsAtPath(partialPath)) check(manager.removeItemAtPath(partialPath, null))
        } catch (error: Throwable) { recordFailureLocked(error) }
    }

    private fun recordFailure(error: Throwable) { protect { recordFailureLocked(error) } }
    private fun recordFailureLocked(error: Throwable) {
        val prior = failure
        if (prior == null) failure = error else if (prior !== error) prior.addSuppressed(error)
    }
    private fun <T> protect(action: () -> T): T { lock.lock(); try { return action() } finally { lock.unlock() } }

    fun close() {
        // Cleanup-only native cancel: acceptance must use public composition disposal instead.
        // Gate queued callbacks before touching producer files. Unknown native ownership
        // cannot authorize deleting a provider root, even after a failed test assertion.
        var failure: Throwable? = null
        fun clean(action: () -> Unit) {
            try { action() } catch (error: Throwable) {
                val prior = failure
                if (prior == null) failure = error else if (prior !== error) prior.addSuppressed(error)
            }
        }
        clean { provider.cancelForCleanup() }
        clean { protect { cleanupStarted = true; nativeProgress }?.cancel() }
        clean { if (protect { completion != null }) resolve(null, cancellationError()) }
        clean { protect { closeHandlesLocked() } }
        var callbackAcknowledged = provider.loadRequests.value == 0
        if (!callbackAcknowledged) clean {
            val deadline = NSProcessInfo.processInfo.systemUptime + 10.0
            while (provider.clientReturned.value != 1) {
                check(NSProcessInfo.processInfo.systemUptime < deadline) { "Owned native provider callback cleanup was not acknowledged" }
                usleep(1000u)
            }
            check(provider.loadRequests.value == 1 && provider.clientEntered.value == 1)
            callbackAcknowledged = true
        }
        clean { protect { closeHandlesLocked() } }
        clean { requireNoFailure() }
        if (callbackAcknowledged) clean {
            val identities = protect { listOfNotNull(sourceIdentity, copiedIdentity) }
            check(ownedDescriptorCounts(*identities.toTypedArray()).all { it == 0 })
            check(manager.removeItemAtPath(root, null))
        }
        failure?.let { throw it }
    }
}

private fun cancellationError() = NSError(NSItemProviderErrorDomain, NSItemProviderItemUnavailableError, null)
private fun AtomicInt.incrementOwned(): Int {
    while (true) { val old = value; if (compareAndSet(old, old + 1)) return old + 1 }
}
private data class NativeInode(val device: ULong, val inode: ULong)
private fun nativeIdentity(url: NSURL): NativeInode = memScoped {
    val observed = alloc<stat>()
    check(stat(assertNotNull(url.path), observed.ptr) == 0)
    NativeInode(observed.st_dev.toULong(), observed.st_ino.toULong())
}
private fun ownedDescriptorCounts(vararg identities: NativeInode): List<Int> = memScoped {
    val limit = getdtablesize()
    check(limit in 1..65_536) { "Native descriptor-table range is unavailable/unbounded; do not guess" }
    val observed = alloc<stat>()
    val counts = IntArray(identities.size)
    for (fd in 0 until limit) {
        if (fstat(fd, observed.ptr) != 0) continue
        identities.forEachIndexed { index, identity ->
            if (observed.st_dev.toULong() == identity.device && observed.st_ino.toULong() == identity.inode) counts[index]++
        }
    }
    counts.toList()
}
private fun pickerDirectories(): Set<String> {
    val root = "${NSTemporaryDirectory().removeSuffix("/")}/calf-file-picker"
    val entries = NSFileManager.defaultManager.contentsOfDirectoryAtPath(root, null)
    if (entries == null) { check(!NSFileManager.defaultManager.fileExistsAtPath(root)); return emptySet() }
    return entries.map { entry ->
        val name = assertIs<String>(entry)
        check(name.isNotEmpty() && '/' !in name && name != "." && name != "..")
        name
    }.toSet()
}
private fun onlyNewPickedFile(before: Set<String>): KmpFile {
    val root = "${NSTemporaryDirectory().removeSuffix("/")}/calf-file-picker"
    val current = pickerDirectories()
    check(current.containsAll(before)) { "The fixture must not remove another owner's baseline staging" }
    val directory = (current - before).single()
    val names = assertNotNull(NSFileManager.defaultManager.contentsOfDirectoryAtPath("$root/$directory", null))
    val name = assertIs<String>(names.single())
    check(name.isNotEmpty() && '/' !in name && name != "." && name != "..")
    return KmpFile(NSURL.fileURLWithPath("$root/$directory/$name"))
}
