package com.mohamedrejeb.calf.share.platform

import org.junit.Assume.assumeTrue
import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.attribute.PosixFilePermission
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import kotlin.test.*

/** Real filesystem extraction/races over test bytes. These are not loaded Windows DLL tests. */
class NativeLibCacheTest {
    private fun withDirectory(test: (File) -> Unit) {
        // Resolve macOS /var-like symlinks before applying the production no-symlink cache policy.
        val parent = Path.of(System.getProperty("user.home")).toRealPath()
        val root = Files.createTempDirectory(parent, "nativecmpkit-share-cache-test-")
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

    @Test fun invalidPayloadAndPathNamesAreRejected() = withDirectory { directory ->
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(), directory, "a.so") }
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), directory, "../a.so") }
        val notDirectory = File(directory, "file").apply { writeText("preserve") }
        assertFails { extractShareNativeLibrary(byteArrayOf(1), notDirectory, "a.so") }
        assertEquals("preserve", notDirectory.readText())
    }

    @Test fun symlinkCacheAndSymlinkEntryDoNotEscapeOwnedDirectory() = withDirectory { directory ->
        assumeTrue("Symlink/permissions test requires a POSIX filesystem", Files.getFileStore(directory.toPath()).supportsFileAttributeView("posix"))
        val cache = File(directory, "real").apply { mkdirs() }
        val alias = directory.toPath().resolve("alias")
        Files.createSymbolicLink(alias, cache.toPath())
        assertFailsWith<IllegalArgumentException> { extractShareNativeLibrary(byteArrayOf(1), alias.toFile(), "a.so") }
        val bytes = byteArrayOf(1, 2, 3)
        val sensitive = File(directory, "not-a-library").apply { writeText("preserve") }
        Files.createSymbolicLink(cache.toPath().resolve("a-${shareNativeContentHash(bytes)}.so"), sensitive.toPath())
        assertFailsWith<IllegalStateException> { extractShareNativeLibrary(bytes, cache, "a.so") }
        assertEquals("preserve", sensitive.readText())
    }

    @Test fun ownedPosixCacheDirectoryHasPrivatePermissions() = withDirectory { directory ->
        assumeTrue("POSIX permission assertion does not apply to Windows ACLs", Files.getFileStore(directory.toPath()).supportsFileAttributeView("posix"))
        extractShareNativeLibrary(byteArrayOf(1), directory, "a.so")
        assertEquals(setOf(PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE),
            Files.getPosixFilePermissions(directory.toPath()))
    }
}
