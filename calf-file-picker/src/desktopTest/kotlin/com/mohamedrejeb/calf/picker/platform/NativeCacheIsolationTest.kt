package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.nio.file.Files
import java.nio.file.attribute.PosixFilePermissions
import java.util.concurrent.Executors
import org.junit.Assume.assumeTrue
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

class NativeCacheIsolationTest {
    @Test fun absentHomeUsesDifferentPrivateDirectoriesRatherThanSharedPredictableCache() {
        val first = nativeCacheDirectory(null)
        val second = nativeCacheDirectory("")
        try {
            assertNotEquals(first, second)
            assertTrue(first.name.startsWith("nativecmpkit-filepicker-"))
            assertTrue(second.name.startsWith("nativecmpkit-filepicker-"))
            if (Files.getFileStore(first.toPath()).supportsFileAttributeView("posix")) {
                assertEquals(PosixFilePermissions.fromString("rwx------"), Files.getPosixFilePermissions(first.toPath()))
            }
        } finally { first.deleteRecursively(); second.deleteRecursively() }
    }

    @Test fun symlinkCacheEntryCannotOverwriteOrLoadTheExternalFile() {
        assumeTrue(!System.getProperty("os.name").startsWith("Windows"))
        val directory = Files.createTempDirectory("nativecmpkit-isolation-").toRealPath()
        try {
            val original = directory.resolve("original")
            Files.write(original, byteArrayOf(1, 2))
            val cache = Files.createDirectory(directory.resolve("cache"))
            Files.createSymbolicLink(cache.resolve("native.so"), original)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), cache.toFile(), "native.so") }
            assertContentEquals(byteArrayOf(1, 2), Files.readAllBytes(original))
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun groupOrWorldWritableCacheIsRejectedInsteadOfTrusted() {
        val directory = Files.createTempDirectory("nativecmpkit-permissions-").toRealPath()
        try {
            assumeTrue(Files.getFileStore(directory).supportsFileAttributeView("posix"))
            Files.setPosixFilePermissions(directory, PosixFilePermissions.fromString("rwxrwxrwx"))
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), directory.toFile(), "native.so") }
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun concurrentExtractionOnlyReturnsIdenticalCompleteBytes() {
        val directory = Files.createTempDirectory("nativecmpkit-concurrent-").toRealPath().toFile()
        val executor = Executors.newFixedThreadPool(4)
        val bytes = ByteArray(256 * 1024) { (it % 251).toByte() }
        try {
            val loads = (0 until 16).map { executor.submit<File> { extractNativeLibrary(bytes, directory, "native.so") } }
            loads.forEach { assertContentEquals(bytes, it.get().readBytes()) }
        } finally { executor.shutdownNow(); directory.deleteRecursively() }
    }
}
