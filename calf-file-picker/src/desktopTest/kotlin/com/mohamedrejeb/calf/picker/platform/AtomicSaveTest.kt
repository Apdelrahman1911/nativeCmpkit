package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.AtomicMoveNotSupportedException
import kotlin.io.path.createTempDirectory
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class AtomicSaveTest {
    private val directory = createTempDirectory("nativecmpkit-save-test").toFile()
    @AfterTest fun cleanup() { directory.deleteRecursively() }
    private fun file(name: String, bytes: ByteArray = byteArrayOf(1, 2, 3)) = File(directory, name).apply { writeBytes(bytes) }

    @Test fun selfCopyAndNormalizedPathAreNoOps() {
        val source = file("source")
        val bytes = source.readBytes()
        saveFileCopy(source, source)
        saveFileCopy(source, File(directory, "./source"))
        assertContentEquals(bytes, source.readBytes())
    }
    @Test fun symlinkAndHardlinkAliasesNeverDeleteSource() {
        val source = file("source")
        val hard = File(directory, "hard")
        Files.createLink(hard.toPath(), source.toPath())
        saveFileCopy(source, hard)
        assertContentEquals(byteArrayOf(1, 2, 3), source.readBytes())
        // Windows may require developer-mode privileges for symbolic links. Linux/macOS execute it.
        if (!System.getProperty("os.name").startsWith("Windows")) {
            val sym = File(directory, "sym")
            Files.createSymbolicLink(sym.toPath(), source.toPath())
            saveFileCopy(source, sym)
            assertTrue(Files.isSymbolicLink(sym.toPath()))
            assertContentEquals(byteArrayOf(1, 2, 3), source.readBytes())
        }
    }
    @Test fun nullContentReplacesExistingAndCreatesMissingAsEmpty() {
        val existing = file("existing")
        val missing = File(directory, "missing")
        saveBytes(existing, null); saveBytes(missing, null)
        assertEquals(0L, existing.length()); assertEquals(0L, missing.length())
    }
    @Test fun stagingFailurePreservesPreviousDestinationAndRemovesStaging() {
        val destination = file("destination")
        assertFailsWith<IOException> {
            replaceFileContents(destination, { it.write(byteArrayOf(9)); throw IOException("injected writer failure") })
        }
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
        assertEquals(listOf("destination"), directory.list()?.toList())
    }
    @Test fun cancellationBeforeCommitPreservesDestination() {
        val destination = file("destination")
        assertFailsWith<kotlinx.coroutines.CancellationException> {
            replaceFileContents(destination, { it.write(byteArrayOf(9)) }) { throw kotlinx.coroutines.CancellationException("cancel") }
        }
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
        assertEquals(1, directory.listFiles()?.size)
    }
    @Test fun streamsLargerCopiesAndKeepsOriginal() {
        val bytes = ByteArray(512 * 1024) { (it % 251).toByte() }
        val source = file("source", bytes)
        val destination = file("destination")
        saveFileCopy(source, destination)
        assertContentEquals(bytes, destination.readBytes())
        assertContentEquals(bytes, source.readBytes())
    }
    @Test fun unsupportedAtomicMoveFailsClosedAfterStaging() {
        val destination = file("destination")
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path) {
                assertContentEquals(byteArrayOf(9), Files.readAllBytes(source))
                throw AtomicMoveNotSupportedException(source.toString(), target.toString(), "injected unsupported filesystem")
            }
            override fun delete(path: Path) { Files.deleteIfExists(path) }
        }
        assertFailsWith<AtomicMoveNotSupportedException> {
            replaceFileContents(destination, { it.write(byteArrayOf(9)) }, operations)
        }
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
        assertEquals(listOf("destination"), directory.list()?.toList())
    }
    @Test fun moveFailureKeepsPrimaryAndSuppressesCleanupFailure() {
        val destination = file("destination")
        val primary = IOException("commit failed")
        val cleanup = IOException("cleanup failed")
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path): Unit = throw primary
            override fun delete(path: Path): Unit = throw cleanup
        }
        assertEquals(primary, assertFailsWith<IOException> { replaceFileContents(destination, { it.write(9) }, operations) })
        assertEquals(listOf(cleanup), primary.suppressed.toList())
        assertContentEquals(byteArrayOf(1, 2, 3), destination.readBytes())
    }
    @Test fun committedSaveDoesNotRunFailedStagingCleanup() {
        val destination = file("destination")
        val operations = object : AtomicSaveOperations {
            override fun move(source: Path, target: Path) = FileSystemAtomicSaveOperations.move(source, target)
            override fun delete(path: Path): Unit = error("Must not run after a committed move")
        }
        replaceFileContents(destination, { it.write(9) }, operations)
        assertContentEquals(byteArrayOf(9), destination.readBytes())
    }
}
