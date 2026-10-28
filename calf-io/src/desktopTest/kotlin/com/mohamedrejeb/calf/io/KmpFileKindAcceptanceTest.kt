package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext
import java.io.File
import java.nio.file.Files
import java.nio.file.LinkOption
import kotlin.io.path.createTempDirectory
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Real JVM filesystem metadata and aliases; no shadow filesystem or access-grant claim. */
class KmpFileKindAcceptanceTest {
    private val directory = createTempDirectory("nativecmpkit-file-kind-")
    private val context = PlatformContext.INSTANCE

    @AfterTest fun removeOnlyOwnedFixtures() {
        // Delete aliases themselves, never walk a symbolic link's target.
        Files.walk(directory).use { paths ->
            paths.sorted(Comparator.reverseOrder()).forEach { Files.delete(it) }
        }
    }

    @Test fun missingAndDirectoryReferencesNeverAppearAsFilesInEitherOverload() {
        val missing = KmpFile(File(directory.toFile(), "missing"))
        assertFalse(missing.exists(context))
        assertFalse(missing.exists())
        assertFalse(missing.isDirectory(context))
        assertFalse(missing.isDirectory())
        assertFalse(missing.isFile(context))
        assertFalse(missing.isFile())

        val folder = KmpFile(directory.toFile())
        assertTrue(folder.exists(context))
        assertTrue(folder.exists())
        assertTrue(folder.isDirectory(context))
        assertTrue(folder.isDirectory())
        assertFalse(folder.isFile(context))
        assertFalse(folder.isFile())
    }

    @Test fun existingExtensionlessDotfileAndOrdinaryFilesAgreeAcrossBothOverloads() {
        val bytes = byteArrayOf(1, 0, -1)
        for (name in listOf("README", "LICENSE", ".gitignore", "report.pdf")) {
            val path = directory.resolve(name)
            Files.write(path, bytes)
            val file = KmpFile(path.toFile())
            assertTrue(file.exists(context))
            assertTrue(file.exists())
            assertTrue(file.isFile(context))
            assertTrue(file.isFile())
            assertFalse(file.isDirectory(context))
            assertFalse(file.isDirectory())
            assertContentEquals(bytes, Files.readAllBytes(path))
        }
    }

    @Test fun actualSymbolicLinksFollowTheTargetAndBrokenLinksNeverBecomeFiles() {
        val bytes = byteArrayOf(9, 0, -1)
        val regular = Files.write(directory.resolve("regular"), bytes)
        val folder = Files.createDirectory(directory.resolve("folder"))
        val linkedFile = Files.createSymbolicLink(directory.resolve("file-link"), regular)
        val linkedFolder = Files.createSymbolicLink(directory.resolve("folder-link"), folder)
        val broken = Files.createSymbolicLink(directory.resolve("broken-link"), directory.resolve("missing"))
        for (path in listOf(linkedFile, linkedFolder, broken)) assertTrue(Files.isSymbolicLink(path))
        assertTrue(Files.exists(broken, LinkOption.NOFOLLOW_LINKS), "the alias itself must really exist")

        for (path in listOf(regular, linkedFile)) {
            val file = KmpFile(path.toFile())
            assertTrue(file.exists(context))
            assertTrue(file.exists())
            assertTrue(file.isFile(context))
            assertTrue(file.isFile())
            assertFalse(file.isDirectory(context))
            assertFalse(file.isDirectory())
        }
        for (path in listOf(folder, linkedFolder)) {
            val file = KmpFile(path.toFile())
            assertTrue(file.exists(context))
            assertTrue(file.exists())
            assertTrue(file.isDirectory(context))
            assertTrue(file.isDirectory())
            assertFalse(file.isFile(context))
            assertFalse(file.isFile())
        }
        val missing = KmpFile(broken.toFile())
        assertFalse(missing.exists(context))
        assertFalse(missing.exists())
        assertFalse(missing.isDirectory(context))
        assertFalse(missing.isDirectory())
        assertFalse(missing.isFile(context))
        assertFalse(missing.isFile())
        assertContentEquals(bytes, Files.readAllBytes(regular))
    }
}
