// Modified for NativeCmpKit (2026-10-29): actual GTK portal/JNI functionality regression.
package com.mohamedrejeb.calf.picker

import com.mohamedrejeb.calf.picker.platform.PlatformFilePicker
import java.io.File
import java.nio.file.Files
import java.util.UUID
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.junit.Assume.assumeTrue
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Production owning operations, packaged JNI and a real private GTK FileChooser.
 * No Compose/sample host, chooser substitute, borrowed parent or other user's bus.
 * Exact Linux-only cases are N/A on other desktop OS families, never passed there.
 */
class NativeLinuxPortalFunctionalityTest {
    @Test fun singleAndMultipleOpenReturnExactRealFilesWithoutChangingTheirBytes() = runBlocking {
        requirePortal()
        val root = Files.createTempDirectory("nck-portal-open-").toFile()
        val content = byteArrayOf(0, 1, 127, -128, -1)
        val files = listOf("alpha.txt", "beta.txt", "gamma.txt").mapIndexed { index, name ->
            File(root, name).apply { writeBytes(content + index.toByte()) }
        }
        try {
            val singleTitle = title()
            val single = dialog(singleTitle, {
                PlatformFilePicker.pick(root.path, FilePickerFileType.All, FilePickerSelectionMode.Single, singleTitle, null)
            }) { selectPath(it, files.first()) }
            assertEquals(listOf(files.first().canonicalFile), single.map { it.canonicalFile })
            val multipleTitle = title()
            val multiple = dialog(multipleTitle, {
                PlatformFilePicker.pick(root.path, FilePickerFileType.All, FilePickerSelectionMode.Multiple(), multipleTitle, null)
            }) {
                focus(it)
                xdo("key", "--window", "$it", "--clearmodifiers", "ctrl+a")
                xdo("key", "--window", "$it", "--clearmodifiers", "Return")
            }
            assertEquals(files.map { it.canonicalFile }.toSet(), multiple.map { it.canonicalFile }.toSet())
            assertEquals(3, multiple.size)
            files.forEachIndexed { index, file -> assertContentEquals(content + index.toByte(), file.readBytes()) }
        } finally { assertTrue(root.deleteRecursively()) }
    }

    @Test fun folderAndSaveDialogsReturnTheSelectedDirectoryAndExactEmptyAndBinaryFiles() = runBlocking {
        requirePortal()
        val root = Files.createTempDirectory("nck-portal-save-").toFile()
        val directory = File(root, "selected-directory").apply { assertTrue(mkdir()) }
        try {
            val folderTitle = title()
            val selected = dialog(folderTitle, {
                PlatformFilePicker.pick(root.path, FilePickerFileType.Folder, FilePickerSelectionMode.Single, folderTitle, null)
            }) { selectPath(it, directory) }
            assertEquals(listOf(directory.canonicalFile), selected.map { it.canonicalFile })
            for ((name, content) in listOf("empty" to byteArrayOf(), "binary" to byteArrayOf(0, 1, 127, -128, -1))) {
                val saveTitle = title()
                val destination = File(root, "$name.bin")
                val saved = dialog(saveTitle, {
                    PlatformFilePicker.save(root.path, name, ".bin", saveTitle, null, null, content)
                }) { selectPath(it, destination) }
                assertEquals(destination.canonicalFile, saved?.canonicalFile)
                assertTrue(destination.isFile)
                assertContentEquals(content, destination.readBytes())
            }
        } finally { assertTrue(root.deleteRecursively()) }
    }

    @Test fun cancellingEachDialogLeavesSourcesUntouchedAndAFreshNativeSessionCanStillOpen() = runBlocking {
        requirePortal()
        val root = Files.createTempDirectory("nck-portal-cancel-").toFile()
        val bytes = byteArrayOf(0, -1, -128, 127)
        val source = File(root, "source.bin").apply { writeBytes(bytes) }
        try {
            for (type in listOf(FilePickerFileType.All, FilePickerFileType.Folder)) {
                val cancelTitle = title()
                val cancelled = dialog(cancelTitle, {
                    PlatformFilePicker.pick(root.path, type, FilePickerSelectionMode.Single, cancelTitle, null)
                }) { escape(it) }
                assertTrue(cancelled.isEmpty())
                assertContentEquals(bytes, source.readBytes())
            }
            val saveTitle = title()
            assertNull(dialog(saveTitle, {
                PlatformFilePicker.save(root.path, "must-not-exist", ".bin", saveTitle, null, source, null)
            }) { escape(it) })
            assertTrue(!File(root, "must-not-exist.bin").exists())
            assertEquals(setOf("source.bin"), root.listFiles()!!.map { it.name }.toSet())
            assertContentEquals(bytes, source.readBytes())
            val freshTitle = title()
            val fresh = dialog(freshTitle, {
                PlatformFilePicker.pick(root.path, FilePickerFileType.All, FilePickerSelectionMode.Single, freshTitle, null)
            }) { selectPath(it, source) }
            assertEquals(listOf(source.canonicalFile), fresh.map { it.canonicalFile })
        } finally { assertTrue(root.deleteRecursively()) }
    }

    private fun requirePortal() {
        assumeTrue("Actual GTK portal scenarios are Linux-only", System.getProperty("os.name") == "Linux")
        check(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID")?.toLongOrNull()?.let { it > 0 } == true)
        check(System.getenv("DISPLAY") == System.getenv("NATIVECMPKIT_PICKER_OWNED_DISPLAY"))
    }

    private fun title() = "NativeCmpKit-Portal-${UUID.randomUUID()}"

    private suspend fun <T> dialog(title: String, operation: suspend () -> T, input: suspend (Long) -> Unit): T = coroutineScope {
        val owner = async { operation() }
        try {
            var id: Long? = null
            withTimeout(20_000) {
                while (id == null) {
                    val windows = visible(title)
                    check(windows.size <= 1) { "One native session must not open duplicate dialogs" }
                    id = windows.singleOrNull()
                    if (id == null) delay(20)
                }
            }
            check(windowTitle(checkNotNull(id)) == title)
            input(checkNotNull(id))
            val result = withTimeout(20_000) { owner.await() }
            withTimeout(10_000) { while (visible(title).isNotEmpty()) delay(20) }
            result
        } finally {
            // A failed fixture must release its real OS dialog before joining the native owner.
            withContext(NonCancellable) {
                for (id in visible(title)) {
                    try { check(windowTitle(id) == title); escape(id) }
                    catch (failure: IllegalStateException) { if (visible(title).contains(id)) throw failure }
                }
                withTimeout(15_000) { owner.join() }
            }
        }
    }

    private fun visible(title: String): List<Long> {
        check(title.matches(Regex("NativeCmpKit-[A-Za-z0-9-]+")))
        return xdo("search", "--all", "--onlyvisible", "--pid", checkNotNull(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID")),
            "--name", "^$title$", allowEmpty = true).lines().filter { it.isNotBlank() }.map { it.toLong() }
    }

    private fun windowTitle(id: Long): String {
        assertEquals(System.getenv("NATIVECMPKIT_PICKER_PORTAL_PID"), xdo("getwindowpid", "$id"))
        return xdo("getwindowname", "$id")
    }

    private fun focus(id: Long) = xdo("windowfocus", "--sync", "$id")
    private fun escape(id: Long) { focus(id); xdo("key", "--window", "$id", "--clearmodifiers", "Escape") }

    private suspend fun selectPath(id: Long, file: File) {
        val title = windowTitle(id)
        focus(id)
        xdo("key", "--window", "$id", "--clearmodifiers", "ctrl+l")
        xdo("type", "--window", "$id", "--clearmodifiers", "--delay", "1", file.absolutePath)
        xdo("key", "--window", "$id", "--clearmodifiers", "Return")
        delay(200)
        if (visible(title).contains(id)) xdo("key", "--window", "$id", "--clearmodifiers", "Return")
    }

    private fun xdo(vararg arguments: String, allowEmpty: Boolean = false): String {
        val process = ProcessBuilder(listOf("xdotool") + arguments).redirectErrorStream(true).start()
        check(process.waitFor(5, TimeUnit.SECONDS)) { process.destroyForcibly(); "Owned window command timed out" }
        val output = process.inputStream.bufferedReader().readText()
        check(output.length < 8192)
        check(process.exitValue() == 0 || (allowEmpty && process.exitValue() == 1 && output.isBlank())) { "Owned window command failed" }
        return output.trim()
    }
}
