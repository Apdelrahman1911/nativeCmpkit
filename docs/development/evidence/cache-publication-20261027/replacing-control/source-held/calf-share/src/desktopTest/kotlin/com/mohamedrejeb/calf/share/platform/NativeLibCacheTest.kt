package com.mohamedrejeb.calf.share.platform

import java.io.File
import java.io.FileInputStream
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.attribute.BasicFileAttributes
import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.test.*

/** Real filesystem extraction/races over test bytes. These are not loaded Windows DLL tests. */
class NativeLibCacheTest {
    private fun withDirectory(test: (File) -> Unit) {
        // Resolve macOS /var-like symlinks before applying the production no-symlink cache policy.
        val parent = Path.of(System.getProperty("user.home")).toRealPath()
        val root = privateCacheTestDirectory("nativecmpkit-share-cache-test-", parent)
        try { test(root.toFile()) } finally {
            Files.walk(root).use { entries -> entries.sorted(Comparator.reverseOrder()).forEach { Files.deleteIfExists(it) } }
        }
    }

    @Test fun fullDigestIdentityAndBytesAreStable() = withDirectory { directory ->
        val bytes = byteArrayOf(1, 2, 3)
        val digest = "039058c6f2c0cb492c533b0a4d14ef77cc0f78abccced5287d84a1a2011cfb81"
        assertEquals(digest, shareNativeContentHash(bytes))
        val first = extractShareNativeLibrary(bytes, directory, "libcalf_share_native.so")
        val second = extractShareNativeLibrary(bytes, directory, "libcalf_share_native.so")
        assertEquals(first, second)
        assertEquals("libcalf_share_native-$digest.so", first.name)
        assertContentEquals(bytes, first.readBytes())
    }

    @Test fun differentVersionOrArchitectureBytesNeverReplaceEachOther() = withDirectory { directory ->
        val first = extractShareNativeLibrary(byteArrayOf(1, 2), directory, "calf_share_native.dll")
        val second = extractShareNativeLibrary(byteArrayOf(3, 4), directory, "calf_share_native.dll")
        assertNotEquals(first, second)
        assertContentEquals(byteArrayOf(1, 2), first.readBytes())
        assertContentEquals(byteArrayOf(3, 4), second.readBytes())
    }

    @Test fun corruptExistingEntryIsRejectedWithoutOverwritingIt() = withDirectory { directory ->
        val bytes = byteArrayOf(1, 2, 3)
        val target = extractShareNativeLibrary(bytes, directory, "libcalf_share_native.so")
        target.writeBytes(byteArrayOf(9))
        assertFailsWith<IllegalStateException> { extractShareNativeLibrary(bytes, directory, "libcalf_share_native.so") }
        assertContentEquals(byteArrayOf(9), target.readBytes())
    }

    @Test fun concurrentSameContentWritersConvergeOnOneVerifiedIdentity() = withDirectory { directory ->
        val executor = Executors.newFixedThreadPool(4)
        val bytes = ByteArray(32_768) { (it % 251).toByte() }
        try {
            val files = executor.invokeAll(List(16) { Callable { extractShareNativeLibrary(bytes, directory, "libcalf_share_native.so") } })
                .map { it.get() }
            assertEquals(1, files.toSet().size)
            files.forEach { assertContentEquals(bytes, it.readBytes()) }
            assertFalse(directory.listFiles()!!.any { it.name.endsWith(".tmp") })
        } finally { executor.shutdownNow() }
    }

    @Test fun latePublisherCannotReplaceAnIdentityAlreadyReturnedToAnOpenReader() = withDirectory { directory ->
        val executor = Executors.newSingleThreadExecutor()
        val staged = CountDownLatch(1)
        val publish = CountDownLatch(1)
        val bytes = ByteArray(256 * 1024) { (it % 251).toByte() }
        try {
            val late = executor.submit<File> {
                extractShareNativeLibrary(bytes, directory, "native.so", ShareCachePublication { complete, target ->
                    assertContentEquals(bytes, Files.readAllBytes(complete))
                    staged.countDown()
                    assertTrue(publish.await(10, TimeUnit.SECONDS))
                    FileSystemShareCachePublication.publish(complete, target)
                })
            }
            assertTrue(staged.await(10, TimeUnit.SECONDS))
            val first = extractShareNativeLibrary(bytes, directory, "native.so")
            val identity = Files.readAttributes(first.toPath(), BasicFileAttributes::class.java).fileKey()
            FileInputStream(first).use { reader ->
                publish.countDown()
                assertEquals(first, late.get(10, TimeUnit.SECONDS), "A late writer must reuse the winner, not replace a native loader's identity")
                assertEquals(identity, Files.readAttributes(first.toPath(), BasicFileAttributes::class.java).fileKey())
                assertContentEquals(bytes, reader.readBytes())
                assertContentEquals(bytes, first.readBytes())
                assertFalse(directory.listFiles()!!.any { it.name.endsWith(".tmp") })
            }
        } finally {
            publish.countDown()
            executor.shutdownNow()
            assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS))
        }
    }

    @Test fun unsupportedPublicationUsesCompletePrivateStagingWithoutCreatingAnIdentity() = withDirectory { directory ->
        val bytes = byteArrayOf(9, 8, 7)
        for (failure in listOf(IOException("hard links unavailable"), UnsupportedOperationException("hard links unavailable"))) {
            val loaded = extractShareNativeLibrary(bytes, directory, "native.so", ShareCachePublication { complete, target ->
                assertContentEquals(bytes, Files.readAllBytes(complete))
                assertFalse(Files.exists(target))
                throw failure
            })
            assertEquals(directory, loaded.parentFile)
            assertTrue(loaded.name.endsWith(".tmp"))
            assertContentEquals(bytes, loaded.readBytes())
            assertPrivateCacheTestDirectory(loaded.toPath())
            assertTrue(loaded.delete())
        }
        assertTrue(directory.listFiles()!!.isEmpty())
    }

    @Test fun invalidPayloadAndPathNamesAreRejected() = withDirectory { directory ->
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(), directory, "a.so") }
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), directory, "../a.so") }
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), directory, ".") }
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), directory, "..") }
        val notDirectory = File(directory, "file").apply { writeText("preserve") }
        assertFails { extractShareNativeLibrary(byteArrayOf(1), notDirectory, "a.so") }
        assertEquals("preserve", notDirectory.readText())
    }

    @Test fun symlinkCacheAndSymlinkEntryDoNotEscapeOwnedDirectory() = withDirectory { directory ->
        val cache = privateCacheTestDirectory("real-", directory.toPath()).toFile()
        val alias = directory.toPath().resolve("alias")
        createCacheDirectoryAlias(alias, cache.toPath())
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), alias.toFile(), "a.so") }
        val bytes = byteArrayOf(1, 2, 3)
        val sensitive = File(directory, "not-a-library").apply { writeText("preserve") }
        Files.createSymbolicLink(cache.toPath().resolve("a-${shareNativeContentHash(bytes)}.so"), sensitive.toPath())
        assertFailsWith<IllegalStateException> { extractShareNativeLibrary(bytes, cache, "a.so") }
        assertEquals("preserve", sensitive.readText())
    }

    @Test fun ownedPosixCacheDirectoryHasPrivatePermissions() = withDirectory { directory ->
        extractShareNativeLibrary(byteArrayOf(1), directory, "a.so")
        assertPrivateCacheTestDirectory(directory.toPath())
    }

    @Test fun foreignWritableCacheIsRejectedWithoutRepairingItsPermissions() = withDirectory { directory ->
        grantForeignCacheWrites(directory.toPath())
        val before = cacheTestSecuritySnapshot(directory.toPath())
        assertFailsWith<IllegalStateException> { extractShareNativeLibrary(byteArrayOf(1), directory, "a.so") }
        val after = cacheTestSecuritySnapshot(directory.toPath())
        assertEquals(before, after, "Do not repair or trust a directory another principal could already have modified")
        assertTrue(directory.listFiles()!!.isEmpty())
    }

    @Test fun foreignWritablePayloadIsRejectedWithoutReplacingOrLoadingIt() = withDirectory { directory ->
        val bytes = byteArrayOf(1, 2)
        val payload = extractShareNativeLibrary(bytes, directory, "a.so").toPath()
        grantForeignCacheWrites(payload)
        val before = cacheTestSecuritySnapshot(payload)
        assertFailsWith<IllegalStateException> { extractShareNativeLibrary(bytes, directory, "a.so") }
        assertEquals(before, cacheTestSecuritySnapshot(payload))
        assertContentEquals(bytes, Files.readAllBytes(payload))
        assertEquals(1L, Files.list(directory.toPath()).use { it.count() })
    }

    @Test fun newlyCreatedNestedCacheIsActuallyPrivateBeforeExtraction() = withDirectory { directory ->
        val first = directory.toPath().resolve("new cache")
        val cache = first.resolve("nested")
        val file = extractShareNativeLibrary(byteArrayOf(9), cache.toFile(), "a.so")
        assertPrivateCacheTestDirectory(first)
        assertPrivateCacheTestDirectory(cache)
        assertContentEquals(byteArrayOf(9), file.readBytes())
    }

    @Test fun dotSegmentsAreRejectedRatherThanValidatingADifferentWritePath() = withDirectory { directory ->
        assertFailsWith<IllegalArgumentException> {
            extractShareNativeLibrary(byteArrayOf(9), directory.toPath().resolve(".").toFile(), "a.so")
        }
        assertTrue(directory.listFiles()!!.isEmpty())
    }
}
