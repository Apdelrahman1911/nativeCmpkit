package nativecmpkit.consumer

import com.mohamedrejeb.calf.core.PlatformContext
import com.mohamedrejeb.calf.io.*
import kotlinx.coroutines.*
import kotlinx.io.buffered
import kotlinx.io.readByteArray
import java.nio.file.Files
import kotlin.test.*

/** Real files, library classes and kotlinx-io from staged Maven artifacts; no mocks/stubs. */
class PublishedIoConsumerTest {
    private fun withDirectory(body: (java.io.File) -> Unit) {
        val directory = Files.createTempDirectory("nativecmpkit-consumer-").toFile()
        try { body(directory) } finally { check(directory.deleteRecursively()) }
    }

    @Test fun emptyFileReadsThroughBothPublicOverloads() = withDirectory { directory ->
        val file = java.io.File(directory, "empty").apply { writeBytes(byteArrayOf()) }.toKmpFile()
        runBlocking {
            assertContentEquals(byteArrayOf(), file.readByteArray())
            assertContentEquals(byteArrayOf(), file.readByteArray(PlatformContext.INSTANCE))
            file.source().buffered().use { assertContentEquals(byteArrayOf(), it.readByteArray()) }
        }
    }

    @Test fun boundaryAndLargeStreamsPreserveAllBytes() = withDirectory { directory ->
        runBlocking {
            for (size in listOf(1, 8191, 8192, 8193, 65536, 1_048_577)) {
                val bytes = ByteArray(size) { (it * 37).toByte() }
                val original = java.io.File(directory, "bytes-$size").apply { writeBytes(bytes) }
                val file = KmpFile(original)
                assertContentEquals(bytes, file.readByteArray())
                file.source(PlatformContext.INSTANCE).buffered().use {
                    assertContentEquals(bytes, it.readByteArray())
                }
                assertTrue(original.delete(), "The closed stream must not retain a Windows file handle")
            }
        }
    }

    @Test fun concurrentSourcesHaveIndependentPositions() = withDirectory { directory ->
        val expected = ByteArray(32769) { (it * 19).toByte() }
        val file = java.io.File(directory, "parallel.bin").apply { writeBytes(expected) }.toKmpFile()
        runBlocking {
            List(16) {
                async(Dispatchers.IO) {
                    file.source().buffered().use { assertContentEquals(expected, it.readByteArray()) }
                }
            }.awaitAll()
        }
    }

    @Test fun existingDirectoryAndMissingFileAreNotRegularFiles() = withDirectory { directory ->
        val absent = java.io.File(directory, "absent").toKmpFile()
        assertFalse(absent.exists())
        assertFalse(absent.isFile())
        assertFalse(absent.isFile(PlatformContext.INSTANCE))
        assertFalse(directory.toKmpFile().isFile())
        assertTrue(directory.toKmpFile().isDirectory())
    }

    @Test fun extensionlessFileAndUnicodeNameArePreserved() = withDirectory { directory ->
        val original = java.io.File(directory, "README-資料").apply { writeText("content") }
        val file = original.toKmpFile()
        assertTrue(file.isFile())
        assertEquals(original.name, file.getName())
        assertEquals(original.path, file.getPath())
        assertEquals(file.getName(), file.getName(PlatformContext.INSTANCE))
    }

    @Test fun repeatedStreamUseLeavesSourceReadableAndDeletable() = withDirectory { directory ->
        val original = java.io.File(directory, "repeated.bin").apply { writeBytes(byteArrayOf(1, 2, 3)) }
        runBlocking {
            repeat(64) {
                original.toKmpFile().source().buffered().use { assertContentEquals(byteArrayOf(1, 2, 3), it.readByteArray()) }
            }
        }
        assertContentEquals(byteArrayOf(1, 2, 3), original.readBytes())
        assertTrue(original.delete())
    }
}
