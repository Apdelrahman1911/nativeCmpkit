package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.FilterInputStream
import java.io.FilterOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.nio.file.Path
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.io.path.createTempDirectory
import kotlin.test.*
import kotlinx.coroutines.*

class SelectedFileSaveTest {
    private val directory = createTempDirectory("nativecmpkit-selected-save").toFile()
    @AfterTest fun cleanup() { directory.deleteRecursively() }
    private fun file(name: String, bytes: ByteArray = byteArrayOf(1, 2, 3)) =
        File(directory, name).apply { writeBytes(bytes) }

    @Test fun selectedPathSavesAndCancelledSelectionTouchesNoFiles() = runBlocking {
        val source = file("source", byteArrayOf(4, 5, 6))
        val destination = file("selected-文档.txt")
        assertEquals(destination, saveSelectedDesktopFile(destination.path, source, null))
        assertContentEquals(byteArrayOf(4, 5, 6), destination.readBytes())
        assertContentEquals(byteArrayOf(4, 5, 6), source.readBytes())
        assertEquals(destination, saveSelectedDesktopFile(destination.path, null, byteArrayOf(8, 9)))
        assertContentEquals(byteArrayOf(8, 9), destination.readBytes())
        assertEquals(destination, saveSelectedDesktopFile(destination.path, null, null))
        assertEquals(0, destination.readBytes().size)
        val absent = File(directory, "absent")
        assertNull(saveSelectedDesktopFile(null, absent, null))
        assertFalse(absent.exists())
        assertEquals(setOf("source", destination.name), directory.list()!!.toSet())
    }

    @Test fun readFailureClosesBothStreamsAndPreservesOldDestination() = runBlocking {
        val source = file("source", ByteArray(192 * 1024) { (it % 251).toByte() })
        val destination = file("destination")
        val closes = AtomicInteger()
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path): Unit = error("No failed read may commit")
            override fun delete(path: Path) = FileSystemAtomicSaveOperations.delete(path)
            override fun openSource(source: File): InputStream = object : FilterInputStream(super.openSource(source)) {
                var reads = 0
                override fun read(bytes: ByteArray, offset: Int, length: Int): Int {
                    if (reads++ != 0) throw IOException("read failed after one real chunk")
                    return super.read(bytes, offset, length)
                }
                override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
            }
            override fun openStaging(path: Path): OutputStream = closingOutput(super.openStaging(path), closes)
        }
        assertFailsWith<IOException> { saveSelectedDesktopFile(destination.path, source, null, operations) }
        assertEquals(2, closes.get())
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
        assertEquals(192 * 1024L, source.length())
        assertEquals(setOf("source", "destination"), directory.list()!!.toSet())
    }

    @Test fun writeFailureClosesBothStreamsAndPreservesOldDestination() = runBlocking {
        val source = file("source", ByteArray(192 * 1024) { (it % 251).toByte() })
        val destination = file("destination")
        val closes = AtomicInteger()
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path): Unit = error("No failed write may commit")
            override fun delete(path: Path) = FileSystemAtomicSaveOperations.delete(path)
            override fun openSource(source: File): InputStream = object : FilterInputStream(super.openSource(source)) {
                override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
            }
            override fun openStaging(path: Path): OutputStream = object : FilterOutputStream(super.openStaging(path)) {
                var writes = 0
                override fun write(bytes: ByteArray, offset: Int, length: Int) {
                    if (writes++ != 0) throw IOException("write failed after one staged chunk")
                    out.write(bytes, offset, length)
                }
                override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
            }
        }
        assertFailsWith<IOException> { saveSelectedDesktopFile(destination.path, source, null, operations) }
        assertEquals(2, closes.get())
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
        assertEquals(192 * 1024L, source.length())
        assertEquals(setOf("source", "destination"), directory.list()!!.toSet())
    }

    @Test fun cancellationInterruptsGenuinelyBlockedCopyAndReleasesItsResources() = runBlocking {
        val original = ByteArray(4 * 1024 * 1024) { (it % 251).toByte() }
        val source = file("source", original)
        val destination = file("destination")
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        val interrupted = AtomicBoolean()
        val closes = AtomicInteger()
        val commits = AtomicInteger()
        val outcome = CompletableDeferred<Throwable>()
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path) { commits.incrementAndGet(); FileSystemAtomicSaveOperations.move(source, target) }
            override fun delete(path: Path) = FileSystemAtomicSaveOperations.delete(path)
            override fun openSource(source: File): InputStream = object : FilterInputStream(super.openSource(source)) {
                var reads = 0
                override fun read(bytes: ByteArray, offset: Int, length: Int): Int {
                    if (reads++ == 1) {
                        entered.countDown()
                        try { release.await() } catch (failure: InterruptedException) {
                            interrupted.set(true)
                            throw IOException("blocked read interrupted", failure)
                        }
                    }
                    return super.read(bytes, offset, length)
                }
                override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
            }
            override fun openStaging(path: Path): OutputStream = closingOutput(super.openStaging(path), closes)
        }
        val worker = launch(Dispatchers.Default) {
            try {
                saveSelectedDesktopFile(destination.path, source, null, operations)
                outcome.complete(AssertionError("A blocked cancelled copy must not succeed"))
            } catch (failure: Throwable) { outcome.complete(failure) }
        }
        try {
            assertTrue(entered.await(10, TimeUnit.SECONDS), "Copy must actually write one chunk then block inside its source read")
            worker.cancel()
            withTimeout(10_000) { worker.join() }
            assertEquals(1L, release.count, "Cancellation must unwind without the test releasing the source gate")
            assertIs<CancellationException>(withTimeout(1_000) { outcome.await() })
            assertTrue(interrupted.get())
            assertEquals(2, closes.get(), "Both owned streams must close before cancellation completes")
            assertEquals(0, commits.get())
            assertContentEquals(original, source.readBytes())
            assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
            assertEquals(setOf("source", "destination"), directory.list()!!.toSet())
        } finally {
            release.countDown()
            worker.cancel()
            withTimeout(10_000) { worker.join() }
        }
    }

    private fun closingOutput(output: OutputStream, closes: AtomicInteger): OutputStream = object : FilterOutputStream(output) {
        override fun write(bytes: ByteArray, offset: Int, length: Int) = out.write(bytes, offset, length)
        override fun close() { try { super.close() } finally { closes.incrementAndGet() } }
    }
}
