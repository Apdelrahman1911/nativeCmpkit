package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.awt.ComposeWindow
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.picker.platform.NativeFilePickerBridge
import com.mohamedrejeb.calf.picker.platform.PlatformFilePicker
import com.mohamedrejeb.calf.picker.platform.withActiveDialogHandle
import java.io.File
import java.nio.file.Files
import java.util.UUID
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.Assume.assumeTrue
import kotlin.coroutines.coroutineContext
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertSame
import kotlin.test.assertTrue

/**
 * Actual Compose/packaged JNI owners. Three portable methods intercept only per-instance
 * scheduling/result transport; real configuration allocation/build/close are retained.
 * Three Linux methods operate the actual private GTK portal, not a mock chooser.
 * No raw parent is used: native peer acquisition/thread affinity is separate IO-023.
 */
class NativePickerComposeLifetimeTest {
    @Test fun composeDisposalBeforeQueuedJniEntryDoesNotAllocateOrShow() = runBlocking {
        val executor = Executors.newSingleThreadExecutor()
        val lane = executor.asCoroutineDispatcher()
        val blocked = CountDownLatch(1)
        val release = CountDownLatch(1)
        val admitted = CountDownLatch(1)
        val creates = AtomicInteger()
        val uses = AtomicInteger()
        val closes = AtomicInteger()
        val blocker = executor.submit { blocked.countDown(); check(release.await(15, TimeUnit.SECONDS)) }
        awaitLatch(blocked)
        val host = Host(operation = { _, _, _, title, _ ->
            admitted.countDown()
            withContext(lane) {
                withActiveDialogHandle(coroutineContext, {
                    creates.incrementAndGet()
                    NativeFilePickerBridge.createDirectoryDialog(title, null, 0)
                }, {
                    NativeFilePickerBridge.destroyDialog(it); closes.incrementAndGet()
                }) {
                    uses.incrementAndGet()
                    NativeFilePickerBridge.showFileDialog(it).map(::File) // Directory kind cannot open a modal.
                }
            }
        }, immediate = true)
        try {
            host.ready(); awaitLatch(admitted)
            host.unmount() // Actual rememberCoroutineScope disposal, not cancelling a standalone job.
            assertFalse(host.windowClosed())
            release.countDown(); blocker.get(10, TimeUnit.SECONDS)
            withContext(lane) { } // Drain the actual serialized entry queue after cancellation.
            assertEquals(0, creates.get())
            assertEquals(0, uses.get())
            assertEquals(0, closes.get())
            assertTrue(host.results.isEmpty() && host.errors.isEmpty())
            host.launch() // An externally retained disposed launcher cannot create another owner.
            withContext(lane) { }
            assertEquals(0, creates.get())
        } finally {
            release.countDown()
            try { host.close() } finally { lane.close(); executor.shutdownNow(); assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS)) }
        }
    }

    @Test fun composeDisposalInsideRealJniCreationHandoffClosesExactlyOnce() = runBlocking {
        val allocated = CountDownLatch(1)
        val release = CountDownLatch(1)
        val closed = CountDownLatch(1)
        val handle = AtomicLong()
        val creates = AtomicInteger()
        val uses = AtomicInteger()
        val closes = AtomicInteger()
        val host = Host(operation = { _, _, _, title, _ ->
            withContext(Dispatchers.IO) {
                withActiveDialogHandle(coroutineContext, {
                    NativeFilePickerBridge.createDirectoryDialog(title, null, 0).also {
                        assertTrue(it > 0); handle.set(it); creates.incrementAndGet(); allocated.countDown()
                        check(release.await(15, TimeUnit.SECONDS)) { "Creation handoff was not released" }
                    }
                }, {
                    try { NativeFilePickerBridge.destroyDialog(it); closes.incrementAndGet() } finally { closed.countDown() }
                }) {
                    uses.incrementAndGet()
                    NativeFilePickerBridge.showFileDialog(it).map(::File)
                }
            }
        }, immediate = true)
        try {
            host.ready(); awaitLatch(allocated)
            host.unmount()
            assertFalse(host.windowClosed()) // UI remains responsive while the real worker owns the config.
            assertEquals(0, closes.get())
            release.countDown(); awaitLatch(closed)
            assertEquals(1, creates.get()); assertEquals(1, closes.get()); assertEquals(0, uses.get())
            assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handle.get()) }
            assertTrue(host.results.isEmpty() && host.errors.isEmpty())
        } finally {
            release.countDown()
            try { host.close() } finally { if (handle.get() > 0) NativeFilePickerBridge.destroyDialog(handle.get()) }
        }
    }

    @Test fun retainedComposeLauncherSnapshotsLimitsParentsAndLatestCallbackPerNativeSession() = runBlocking {
        val root = Files.createTempDirectory("nck-picker-results-").toFile()
        val files = (0..5).map { index -> File(root, "$index.txt").apply { writeText("owned-$index") } }
        val requested = ConcurrentLinkedQueue<Pair<FilePickerSelectionMode, ComposeWindow?>>()
        val handles = ConcurrentLinkedQueue<Long>()
        val entered = AtomicReference<CountDownLatch>()
        val resume = AtomicReference<CountDownLatch>()
        val host = Host(operation = { _, _, mode, _, parent ->
            withContext(Dispatchers.IO) {
                withActiveDialogHandle(coroutineContext, {
                    NativeFilePickerBridge.createDirectoryDialog(null, null, 0).also { handles.add(it) }
                }, NativeFilePickerBridge::destroyDialog) {
                    requested.add(mode to parent)
                    entered.get().countDown(); check(resume.get().await(15, TimeUnit.SECONDS))
                    assertEquals(0, NativeFilePickerBridge.showFileDialog(it).size)
                    files // Controlled result transport; real config/lease/close, not real six-file OS selection.
                }
            }
        })
        val otherParent = onEdt { ComposeWindow().apply { setSize(200, 120); isVisible = true } }
        try {
            host.ready()
            for ((round, mode) in listOf(FilePickerSelectionMode.Multiple(2), FilePickerSelectionMode.Multiple(5),
                    FilePickerSelectionMode.Multiple(), FilePickerSelectionMode.Multiple(1)).withIndex()) {
                val start = CountDownLatch(1); val release = CountDownLatch(1)
                entered.set(start); resume.set(release)
                val parent = if (round % 2 == 0) host.window else otherParent
                val priorLauncher = host.launcher.get()
                host.update(mode = mode, parent = parent, version = round * 2)
                assertSame(priorLauncher, host.launcher.get())
                host.launch(); awaitLatch(start)
                host.update(mode = FilePickerSelectionMode.Multiple(6), parent = otherParent, version = round * 2 + 1)
                host.launch() // Must reject overlap without allocating another config or changing the open session.
                assertEquals(round + 1, handles.size)
                assertEquals(round + 1, host.errors.size)
                assertEquals(mode to parent, requested.last())
                release.countDown()
                awaitCondition { host.results.size == round + 1 }
                val result = host.results.last()
                assertEquals(round * 2 + 1, result.version)
                assertEquals(if (round == 2) 6 else listOf(2, 5, 6, 1)[round], result.files.size)
                assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handles.last()) }
            }
            assertEquals(handles.size, handles.toSet().size, "No stale ID reuse or duplicate native configuration")
        } finally {
            resume.get()?.countDown()
            try { host.close() } finally { onEdt { otherParent.dispose() }; assertTrue(root.deleteRecursively()) }
        }
    }

    @Test fun firstPublicCompositionLaunchAndSettingsUpdatesUseOneActualNativeDialog() = runBlocking {
        requireLinuxPortal()
        val root = Files.createTempDirectory("nck-picker-native-").toFile()
        val file = File(root, "selected.txt").apply { writeBytes(byteArrayOf(0, 1, 127, -128, -1)) }
        val host = Host(immediate = true, directory = root.absolutePath)
        var title = host.title
        try {
            host.ready()
            var native = awaitDialog(title)
            for (round in 0..2) {
                host.launch() // Reject double launch while preserving the current actual dialog.
                assertEquals(round + 1, host.errors.size)
                val nextTitle = "NativeCmpKit-next-${UUID.randomUUID()}"
                host.update(mode = FilePickerSelectionMode.Multiple(5), version = round + 1, title = nextTitle)
                assertEquals(title, dialogName(native)) // New settings cannot reconfigure the already-visible session.
                selectFile(native, file)
                awaitCondition { host.results.size == round + 1 }
                val result = host.results.last()
                assertEquals(round + 1, result.version)
                assertContentEquals(file.readBytes(), result.files.single().file.readBytes())
                assertEquals(file.canonicalFile, result.files.single().file.canonicalFile)
                if (round < 2) {
                    host.launch(); title = nextTitle; native = awaitDialog(title)
                }
            }
            assertEquals(3, host.results.size)
        } finally {
            try { cancelDialogIfPresent(title); cancelDialogIfPresent(host.title); host.close() } finally { assertTrue(root.deleteRecursively()) }
        }
    }

    @Test fun closingComposeWindowWithAnActualDialogVisibleCancelsDeliveryNotNativeOwnership() = runBlocking {
        requireLinuxPortal()
        val finished = CountDownLatch(1)
        val host = Host(operation = { directory, type, mode, title, parent ->
            try {
                PlatformFilePicker.pick(directory, type, mode, title, parent) // Actual owning implementation/OS modal.
            } finally { finished.countDown() }
        }, immediate = true)
        try {
            host.ready()
            val native = awaitDialog(host.title)
            assertTrue(native > 0)
            host.close()
            assertTrue(host.windowClosed())
            // Synchronous rfd cannot promise prompt OS dismissal. The actual in-flight worker
            // keeps its lease until the user cancels; closing Compose must not free it first.
            cancelDialogIfPresent(host.title)
            awaitCondition { visibleDialogs(host.title).isEmpty() }
            awaitLatch(finished) // Real worker returned and native owning finally ran; not just a quiet delay.
            assertTrue(host.results.isEmpty() && host.errors.isEmpty())
            host.launch()
            delay(150)
            assertTrue(visibleDialogs(host.title).isEmpty())
            assertTrue(host.results.isEmpty() && host.errors.isEmpty())
        } finally { cancelDialogIfPresent(host.title); host.close() }
    }

    @Test fun closingTheRealRegistryIdWhileItsDialogIsVisibleKeepsTheShowLeaseValid() = runBlocking {
        requireLinuxPortal()
        val handle = AtomicLong()
        val closed = CountDownLatch(1)
        val host = Host(operation = { _, _, _, title, _ ->
            withContext(Dispatchers.IO) {
                withActiveDialogHandle(coroutineContext, {
                    NativeFilePickerBridge.createFileDialog(title, null, null, false, 0).also { handle.set(it) }
                }, {
                    try { NativeFilePickerBridge.destroyDialog(it) } finally { closed.countDown() }
                }) { NativeFilePickerBridge.showFileDialog(it).map(::File) }
            }
        }, immediate = true)
        try {
            host.ready()
            val native = awaitDialog(host.title)
            assertTrue(handle.get() > 0)
            NativeFilePickerBridge.destroyDialog(handle.get())
            assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handle.get()) }
            assertEquals(host.title, dialogName(native)) // The existing real show still owns its config.
            cancelDialogIfPresent(host.title)
            awaitLatch(closed); awaitCondition { host.results.size == 1 }
            assertTrue(host.results.single().files.isEmpty())
            assertTrue(host.errors.isEmpty())
        } finally {
            cancelDialogIfPresent(host.title)
            try { host.close() } finally { if (handle.get() > 0) NativeFilePickerBridge.destroyDialog(handle.get()) }
        }
    }

    private data class Delivery(val version: Int, val files: List<KmpFile>)
    private class Host(
        val operation: (suspend (String?, FilePickerFileType, FilePickerSelectionMode, String?, ComposeWindow?) -> List<File>)? = null,
        immediate: Boolean = false,
        directory: String? = null,
    ) : AutoCloseable {
        val launcher = AtomicReference<FilePickerLauncher>()
        val results = ConcurrentLinkedQueue<Delivery>()
        val errors = ConcurrentLinkedQueue<FilePickerException>()
        private var mounted by mutableStateOf(true)
        private var mode by mutableStateOf<FilePickerSelectionMode>(FilePickerSelectionMode.Multiple(2))
        private var settings by mutableStateOf<FilePickerSettings>(FilePickerSettings(
            title = "NativeCmpKit-first-${UUID.randomUUID()}", initialDirectory = directory,
        ))
        private var version by mutableStateOf(0)
        private var changeToken by mutableStateOf(0)
        private val applied = AtomicInteger(-1)
        private val removed = CountDownLatch(1)
        private val first = AtomicBoolean(immediate)
        val window = onEdt {
            ComposeWindow().apply {
                title = "NativeCmpKit-owned-library-host"
                setSize(480, 240)
                setContent {
                    val currentVersion = version
                    val currentChange = changeToken
                    if (mounted) {
                        val onResult: (List<KmpFile>) -> Unit = { results.add(Delivery(currentVersion, it)) }
                        val remembered = if (operation == null) rememberFilePickerLauncher(
                            FilePickerFileType.All, mode, settings, { errors.add(it) }, onResult,
                        ) else rememberDesktopFilePickerLauncher(
                            FilePickerFileType.All, mode, settings, { errors.add(it) }, onResult, operation,
                        )
                        SideEffect {
                            launcher.set(remembered)
                            applied.set(currentChange)
                            if (first.compareAndSet(true, false)) remembered.launch()
                        }
                    } else SideEffect { removed.countDown() }
                }
                isVisible = true
            }
        }
        val title: String get() = onEdt { checkNotNull(settings.title) }
        suspend fun ready() { awaitCondition { applied.get() >= 0 }; assertTrue(onEdt { window.isShowing }) }
        suspend fun update(mode: FilePickerSelectionMode, version: Int, parent: ComposeWindow? = null, title: String? = null) {
            val change = onEdt {
                this.mode = mode; this.version = version
                settings = FilePickerSettings(title ?: settings.title, settings.initialDirectory, parentWindow = parent)
                ++changeToken
            }
            awaitCondition { applied.get() == change }
        }
        fun launch() { onEdt { checkNotNull(launcher.get()).launch() } }
        suspend fun unmount() { onEdt { mounted = false }; awaitLatch(removed) }
        fun windowClosed(): Boolean = onEdt { !window.isDisplayable }
        override fun close() { onEdt { window.dispose() } }
    }

    companion object {
        private suspend fun awaitLatch(latch: CountDownLatch) { withTimeout(15_000) { while (latch.count != 0L) delay(10) } }
        private suspend fun awaitCondition(predicate: () -> Boolean) { withTimeout(20_000) { while (!predicate()) delay(20) } }
        private fun <T> onEdt(action: () -> T): T {
            if (SwingUtilities.isEventDispatchThread()) return action()
            val value = AtomicReference<T>()
            val failure = AtomicReference<Throwable>()
            SwingUtilities.invokeAndWait { try { value.set(action()) } catch (error: Throwable) { failure.set(error) } }
            failure.get()?.let { throw it }
            return value.get()
        }
        private fun requireLinuxPortal() {
            assumeTrue("Linux-only real GTK portal scenario; explicitly N/A on other OS families", System.getProperty("os.name") == "Linux")
            check(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID")?.toLongOrNull()?.let { it > 0 } == true) { "Owned real portal PID is required; no UI skip" }
            check(System.getenv("DISPLAY") == System.getenv("NATIVECMPKIT_PICKER_OWNED_DISPLAY")) { "Never drive another desktop display" }
        }
        private fun xdo(vararg arguments: String, allowEmpty: Boolean = false): String {
            val process = ProcessBuilder(listOf("xdotool") + arguments).redirectErrorStream(true).start()
            check(process.waitFor(5, TimeUnit.SECONDS)) { process.destroyForcibly(); "Owned window command timed out" }
            val output = process.inputStream.bufferedReader().readText()
            check(output.length < 8192) { "Unbounded native window output" }
            check(process.exitValue() == 0 || (allowEmpty && process.exitValue() == 1 && output.isBlank())) { "Owned native window command failed: $output" }
            return output.trim()
        }
        private fun visibleDialogs(title: String): List<Long> {
            check(title.matches(Regex("NativeCmpKit-[A-Za-z0-9-]+")))
            return xdo("search", "--onlyvisible", "--pid", checkNotNull(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID")),
                "--name", "^$title$", allowEmpty = true).lines().filter { it.isNotBlank() }.map { it.toLong() }
        }
        private fun dialogName(id: Long): String {
            assertEquals(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID"), xdo("getwindowpid", id.toString()))
            return xdo("getwindowname", id.toString())
        }
        private suspend fun awaitDialog(title: String): Long {
            var result = 0L
            awaitCondition {
                val windows = visibleDialogs(title)
                check(windows.size <= 1) { "Duplicate native dialogs for one session" }
                windows.singleOrNull()?.also { assertEquals(title, dialogName(it)); result = it } != null
            }
            return result
        }
        private suspend fun selectFile(id: Long, file: File) {
            val title = dialogName(id)
            xdo("windowfocus", "--sync", id.toString())
            xdo("key", "--window", id.toString(), "--clearmodifiers", "ctrl+l")
            xdo("type", "--window", id.toString(), "--clearmodifiers", "--delay", "1", file.absolutePath)
            xdo("key", "--window", id.toString(), "--clearmodifiers", "Return")
            delay(200)
            // GTK may first validate/load the location. Submit only the same still-owned dialog.
            if (visibleDialogs(title).contains(id)) xdo("key", "--window", id.toString(), "--clearmodifiers", "Return")
        }
        private fun cancelDialogIfPresent(title: String) {
            if (System.getProperty("os.name") != "Linux" || System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID") == null) return
            for (id in visibleDialogs(title)) {
                try {
                    assertEquals(title, dialogName(id))
                    xdo("windowfocus", "--sync", id.toString())
                    xdo("key", "--window", id.toString(), "--clearmodifiers", "Escape")
                } catch (failure: IllegalStateException) {
                    // Cancellation/window close may race between owned lookup and input.
                    // Only an actually vanished same PID/title window is benign cleanup.
                    if (visibleDialogs(title).contains(id)) throw failure
                }
            }
        }
    }
}
