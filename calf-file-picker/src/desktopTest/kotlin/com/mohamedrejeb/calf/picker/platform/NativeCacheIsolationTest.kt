package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.nio.file.Files
import java.util.concurrent.Executors
import kotlin.test.Test
import kotlin.test.assertContentEquals
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
            assertPrivateCacheTestDirectory(first.toPath())
            assertPrivateCacheTestDirectory(second.toPath())
        } finally { first.deleteRecursively(); second.deleteRecursively() }
    }

    @Test fun symlinkCacheEntryCannotOverwriteOrLoadTheExternalFile() {
        val directory = privateCacheTestDirectory("nativecmpkit-isolation-")
        try {
            val original = directory.resolve("original")
            Files.write(original, byteArrayOf(1, 2))
            val cache = privateCacheTestDirectory("cache-", directory)
            Files.createSymbolicLink(cache.resolve("native.so"), original)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), cache.toFile(), "native.so") }
            assertContentEquals(byteArrayOf(1, 2), Files.readAllBytes(original))
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun groupOrWorldWritableCacheIsRejectedInsteadOfTrusted() {
        val directory = privateCacheTestDirectory("nativecmpkit-permissions-")
        try {
            grantForeignCacheWrites(directory)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), directory.toFile(), "native.so") }
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun directoryAliasesCannotRedirectTheNativeCache() {
        val directory = privateCacheTestDirectory("nativecmpkit-junction-")
        try {
            val external = privateCacheTestDirectory("external-", directory)
            val original = external.resolve("preserve")
            Files.write(original, byteArrayOf(1, 2))
            val alias = directory.resolve("alias with spaces")
            createCacheDirectoryAlias(alias, external)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), alias.toFile(), "native.so") }
            assertContentEquals(byteArrayOf(1, 2), Files.readAllBytes(original))
            assertTrue(Files.list(external).use { it.count() } == 1L, "No native payload may be written through an alias")
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun concurrentExtractionOnlyReturnsIdenticalCompleteBytes() {
        val directory = privateCacheTestDirectory("nativecmpkit-concurrent-").toFile()
        val executor = Executors.newFixedThreadPool(4)
        val bytes = ByteArray(256 * 1024) { (it % 251).toByte() }
        try {
            val loads = (0 until 16).map { executor.submit<File> { extractNativeLibrary(bytes, directory, "native.so") } }
            loads.forEach { assertContentEquals(bytes, it.get().readBytes()) }
        } finally { executor.shutdownNow(); directory.deleteRecursively() }
    }
}
