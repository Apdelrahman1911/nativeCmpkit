@file:OptIn(com.mohamedrejeb.calf.core.ExperimentalCalfApi::class)

package com.mohamedrejeb.calf.picker

import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.awt.ComposeWindow
import com.mohamedrejeb.calf.io.KmpFile
import com.mohamedrejeb.calf.picker.platform.NativeFilePickerBridge
import com.mohamedrejeb.calf.picker.platform.saveSelectedDesktopFile
import com.mohamedrejeb.calf.picker.platform.withActiveDialogHandle
import java.io.File
import java.nio.file.Files
import java.util.concurrent.ConcurrentLinkedQueue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import javax.swing.SwingUtilities
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.jetbrains.skiko.GraphicsApi
import kotlin.coroutines.coroutineContext
import kotlin.test.*

/**
 * Actual visible Compose windows, real JNI config allocation/lease/close and actual file writer.
 * Only per-instance scheduling/result transport is controlled. Native parent0 deliberately
 * avoids the independently unresolved raw-peer lease (IO-023); this proves Kotlin parent
 * selection/snapshots, not native modality/focus, AppKit/Win32/Wayland ownership or UI selection.
 */
class NativeDesktopSaverStateTest {
    @Test fun retainedSaverSnapshotsExplicitAndCompositionLocalParentsSettingsAndCurrentCallbacks() = runBlocking {
        val root = Files.createTempDirectory("nck-saver-state-").toFile()
        val source = File(root, "original.bin").apply { writeBytes(byteArrayOf(0, 1, 127, -128, -1)) }
        val writes = ConcurrentLinkedQueue<Request>()
        val handles = ConcurrentLinkedQueue<Long>()
        val closes = AtomicInteger()
        val entered = AtomicReference<CountDownLatch>()
        val resume = AtomicReference<CountDownLatch>()
        val host = Host { directory, name, extension, title, parent, original, bytes ->
            withContext(Dispatchers.IO) {
                withActiveDialogHandle(coroutineContext, {
                    NativeFilePickerBridge.createSaveDialog(title, directory, "$name.$extension", extension, 0).also {
                        assertTrue(it > 0); handles.add(it)
                    }
                }, { NativeFilePickerBridge.destroyDialog(it); closes.incrementAndGet() }) { handle ->
                    writes.add(Request(directory, name, extension, title, parent, original, bytes))
                    entered.get().countDown(); check(resume.get().await(15, TimeUnit.SECONDS))
                    // Actual wrong-kind native dispatch cannot open a chooser; it still exercises
                    // real registry ownership. The controlled destination invokes the owning writer.
                    assertTrue(NativeFilePickerBridge.showFileDialog(handle).isEmpty())
                    saveSelectedDesktopFile(File(root, "$name.$extension").path, original, bytes)
                }
            }
        }
        val other = onEdt { ComposeWindow().apply { setSize(200, 120); isVisible = true } }
        try {
            host.ready()
            // Explicit software Skiko is an actual supported window renderer,
            // not a stub/headless GUI waiver. The focused Linux Xvfb CI job
            // isolates a proven GLX JVM-shutdown hang; no GPU certification.
            val renderer = onEdt { assertNotNull(host.window.renderApi) }
            val parentRenderer = onEdt { assertNotNull(other.renderApi) }
            assertNotEquals(GraphicsApi.UNKNOWN, renderer)
            assertNotEquals(GraphicsApi.UNKNOWN, parentRenderer)
            if (System.getenv("SKIKO_RENDER_API") == "SOFTWARE_FAST") {
                assertEquals(GraphicsApi.SOFTWARE_FAST, renderer)
                assertEquals(GraphicsApi.SOFTWARE_FAST, parentRenderer)
            }
            println("NATIVECMPKIT_SAVER_RENDERERS host=${renderer.name} parent=${parentRenderer.name}")
            val retained = host.launcher.get()
            val originals = source.readBytes()
            repeat(4) { round ->
                val local = if (round % 2 == 0) host.window else other
                val explicit = if (round < 2) null else if (round == 2) other else host.window
                val expectedParent = explicit ?: local
                val directory = File(root, "directory-$round").apply { mkdir() }.path
                val explicitDirectory = if (round == 3) root.path else null
                val name = "saved-$round"
                val title = "NativeCmpKit-state-$round"
                val bytes = byteArrayOf(round.toByte(), -1, 0)
                entered.set(CountDownLatch(1)); resume.set(CountDownLatch(1))
                host.update(FilePickerSettings(title, directory, parentWindow = explicit), local, round * 2)
                assertSame(retained, host.launcher.get())
                host.launch { launcher ->
                    if (round % 2 == 0) launcher.launch(bytes, name, "bin", explicitDirectory)
                    else launcher.launch(KmpFile(source), name, "bin", explicitDirectory)
                }
                awaitLatch(entered.get())
                val request = writes.last()
                assertSame(expectedParent, request.parent)
                if (explicit != null) assertNotSame(local, explicit, "Explicit parent must override a different local parent")
                assertEquals(explicitDirectory ?: directory, request.directory)
                assertEquals(name, request.name); assertEquals("bin", request.extension); assertEquals(title, request.title)
                assertSame(if (round % 2 == 0) null else source, request.source)
                assertSame(if (round % 2 == 0) bytes else null, request.bytes)
                host.update(FilePickerSettings("later", root.path, parentWindow = local), other, round * 2 + 1)
                assertSame(retained, host.launcher.get())
                assertSame(expectedParent, request.parent, "Live replacement must not change an admitted operation")
                host.launch { it.launch(null, "overlap", "bin") }
                assertEquals(round + 1, handles.size)
                assertEquals(round + 1, host.errors.size)
                assertEquals(round * 2 + 1, host.errors.last().first, "Overlap uses the current error callback")
                resume.get().countDown()
                awaitCondition { host.results.size == round + 1 }
                assertEquals(round + 1, closes.get())
                val delivery = host.results.last()
                assertEquals(round * 2 + 1, delivery.first, "Use the current callback after the original launch snapshot")
                val saved = assertNotNull(delivery.second)
                assertEquals(File(root, "$name.bin").canonicalFile, saved.file.canonicalFile)
                assertContentEquals(if (round % 2 == 0) bytes else originals, saved.file.readBytes())
                assertContentEquals(originals, source.readBytes())
                assertFailsWith<RuntimeException> { NativeFilePickerBridge.showFileDialog(handles.last()) }
            }
            assertEquals(4, writes.size); assertEquals(4, handles.toSet().size); assertEquals(4, closes.get())
            host.close()
            awaitLatch(host.disposed)
            val count = handles.size
            onEdt { retained.launch(null, "disposed", "bin") }
            // Actual Compose disposal was observed above; the retained launch sees its cancelled scope.
            assertEquals(count, handles.size); assertEquals(4, host.results.size); assertEquals(4, host.errors.size)
        } finally {
            resume.get()?.countDown()
            try {
                host.close()
                awaitLatch(host.disposed)
                awaitCondition { closes.get() == handles.size }
            } finally { onEdt { other.dispose() }; assertTrue(root.deleteRecursively()) }
        }
    }

    private data class Request(val directory: String?, val name: String, val extension: String, val title: String?,
                               val parent: ComposeWindow?, val source: File?, val bytes: ByteArray?)

    private class Host(operation: suspend (String?, String, String, String?, ComposeWindow?, File?, ByteArray?) -> File?) {
        private var settings by mutableStateOf<FilePickerSettings>(FilePickerSettings())
        private var localParent by mutableStateOf<ComposeWindow?>(null)
        private var version by mutableStateOf(0)
        private var token by mutableStateOf(0)
        private val applied = AtomicInteger(-1)
        val launcher = AtomicReference<FileSaverLauncher>()
        val results = ConcurrentLinkedQueue<Pair<Int, KmpFile?>>()
        val errors = ConcurrentLinkedQueue<Pair<Int, FilePickerException>>()
        val disposed = CountDownLatch(1)
        val window = onEdt { ComposeWindow().apply {
            setSize(480, 240)
            setContent {
                val callbackVersion = version
                val generation = token
                CompositionLocalProvider(LocalFilePickerParentWindow provides localParent) {
                    DisposableEffect(Unit) { onDispose { disposed.countDown() } }
                    val current = rememberDesktopFileSaverLauncher(settings, { errors.add(callbackVersion to it) },
                        { results.add(callbackVersion to it) }, operation)
                    SideEffect { launcher.set(current); applied.set(generation) }
                }
            }
            isVisible = true
        } }
        suspend fun ready() { awaitCondition { applied.get() >= 0 }; assertTrue(onEdt { window.isShowing }) }
        suspend fun update(settings: FilePickerSettings, parent: ComposeWindow?, version: Int) {
            val expected = onEdt { this.settings = settings; localParent = parent; this.version = version; ++token }
            awaitCondition { applied.get() == expected }
        }
        fun launch(action: (FileSaverLauncher) -> Unit) { onEdt { action(checkNotNull(launcher.get())) } }
        fun close() { onEdt { window.dispose() } }
    }

    companion object {
        private suspend fun awaitLatch(latch: CountDownLatch) { withTimeout(15_000) { while (latch.count != 0L) delay(10) } }
        private suspend fun awaitCondition(predicate: () -> Boolean) { withTimeout(20_000) { while (!predicate()) delay(20) } }
        private fun <T> onEdt(action: () -> T): T {
            if (SwingUtilities.isEventDispatchThread()) return action()
            val result = AtomicReference<T>(); val failure = AtomicReference<Throwable>()
            SwingUtilities.invokeAndWait { try { result.set(action()) } catch (error: Throwable) { failure.set(error) } }
            failure.get()?.let { throw it }
            return result.get()
        }
    }
}
