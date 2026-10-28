package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.FileInputStream
import java.io.IOException
import java.nio.file.Files
import java.nio.file.attribute.BasicFileAttributes
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
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
            val before = cacheTestSecuritySnapshot(directory)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(9), directory.toFile(), "native.so") }
            assertEquals(before, cacheTestSecuritySnapshot(directory), "Never silently repair an already untrusted cache")
            assertEquals(0L, Files.list(directory).use { it.count() })
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun foreignWritablePayloadIsRejectedWithoutReplacingOrLoadingIt() {
        val directory = privateCacheTestDirectory("nativecmpkit-payload-permissions-")
        try {
            val payload = extractNativeLibrary(byteArrayOf(1, 2), directory.toFile(), "native.so").toPath()
            grantForeignCacheWrites(payload)
            val before = cacheTestSecuritySnapshot(payload)
            assertFailsWith<IllegalStateException> { extractNativeLibrary(byteArrayOf(1, 2), directory.toFile(), "native.so") }
            assertEquals(before, cacheTestSecuritySnapshot(payload))
            assertContentEquals(byteArrayOf(1, 2), Files.readAllBytes(payload))
            assertEquals(1L, Files.list(directory).use { it.count() })
        } finally { directory.toFile().deleteRecursively() }
    }

    @Test fun newlyCreatedNestedCacheIsActuallyPrivateBeforeExtraction() {
        val root = privateCacheTestDirectory("nativecmpkit-private-creation-")
        try {
            val first = root.resolve("new cache")
            val cache = first.resolve("nested")
            val file = extractNativeLibrary(byteArrayOf(9), cache.toFile(), "native.so")
            assertPrivateCacheTestDirectory(first)
            assertPrivateCacheTestDirectory(cache)
            assertContentEquals(byteArrayOf(9), file.readBytes())
        } finally { root.toFile().deleteRecursively() }
    }

    @Test fun dotSegmentsAreRejectedRatherThanValidatingADifferentWritePath() {
        val root = privateCacheTestDirectory("nativecmpkit-dot-segments-")
        try {
            assertFailsWith<IllegalArgumentException> {
                extractNativeLibrary(byteArrayOf(9), root.resolve(".").toFile(), "native.so")
            }
            assertEquals(0L, Files.list(root).use { it.count() })
        } finally { root.toFile().deleteRecursively() }
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

    @Test fun latePublisherCannotReplaceAnIdentityAlreadyReturnedToAnOpenReader() {
        val directory = privateCacheTestDirectory("nativecmpkit-late-publisher-").toFile()
        val executor = Executors.newSingleThreadExecutor()
        val staged = CountDownLatch(1)
        val publish = CountDownLatch(1)
        val bytes = ByteArray(256 * 1024) { (it % 251).toByte() }
        try {
            val late = executor.submit<File> {
                extractNativeLibrary(bytes, directory, "native.so", NativeCachePublication { complete, target ->
                    assertContentEquals(bytes, Files.readAllBytes(complete))
                    staged.countDown()
                    assertTrue(publish.await(10, TimeUnit.SECONDS), "First publisher must be returned before the late publisher proceeds")
                    FileSystemNativeCachePublication.publish(complete, target)
                })
            }
            assertTrue(staged.await(10, TimeUnit.SECONDS))
            val first = extractNativeLibrary(bytes, directory, "native.so")
            val identity = Files.readAttributes(first.toPath(), BasicFileAttributes::class.java).fileKey()
            FileInputStream(first).use { reader ->
                publish.countDown()
                assertEquals(first, late.get(10, TimeUnit.SECONDS), "Same-content loser must reuse, never replace, the verified winner")
                assertEquals(identity, Files.readAttributes(first.toPath(), BasicFileAttributes::class.java).fileKey())
                assertContentEquals(bytes, reader.readBytes())
                assertContentEquals(bytes, first.readBytes())
                assertEquals(listOf("native.so"), directory.list()!!.toList())
            }
        } finally {
            publish.countDown()
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS))
            directory.deleteRecursively()
        }
    }

    @Test fun unsupportedPublicationRetainsOnlyVerifiedPrivateStagingAndNeverUsesRename() {
        val directory = privateCacheTestDirectory("nativecmpkit-unsupported-publication-").toFile()
        val bytes = byteArrayOf(9, 8, 7)
        try {
            for (failure in listOf(IOException("hard links unavailable"), UnsupportedOperationException("hard links unavailable"))) {
                val loaded = extractNativeLibrary(bytes, directory, "native.so", NativeCachePublication { complete, target ->
                    assertContentEquals(bytes, Files.readAllBytes(complete))
                    assertTrue(!Files.exists(target))
                    throw failure
                })
                assertNotEquals(File(directory, "native.so"), loaded)
                assertEquals(directory, loaded.parentFile)
                assertContentEquals(bytes, loaded.readBytes())
                assertPrivateCacheTestDirectory(loaded.toPath())
                assertTrue(!File(directory, "native.so").exists())
                assertTrue(loaded.delete())
            }
            assertEquals(0, directory.list()!!.size)
        } finally { directory.deleteRecursively() }
    }
}
