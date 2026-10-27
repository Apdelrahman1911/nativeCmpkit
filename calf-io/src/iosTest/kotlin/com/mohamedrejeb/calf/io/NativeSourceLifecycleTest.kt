package com.mohamedrejeb.calf.io

import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.addressOf
import kotlinx.cinterop.alloc
import kotlinx.cinterop.memScoped
import kotlinx.cinterop.ptr
import kotlinx.cinterop.usePinned
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest
import kotlinx.io.Buffer
import kotlinx.io.IOException
import kotlinx.io.buffered
import kotlinx.io.readByteArray
import platform.Foundation.NSData
import platform.Foundation.NSFileManager
import platform.Foundation.NSTemporaryDirectory
import platform.Foundation.NSURL
import platform.Foundation.NSUUID
import platform.Foundation.create
import platform.Foundation.writeToURL
import platform.posix.fstat
import platform.posix.getdtablesize
import platform.posix.stat
import kotlin.test.AfterTest
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Real Native file streams/descriptor identity, not a shadow source or timing-only leak probe. */
@OptIn(ExperimentalForeignApi::class, BetaInteropApi::class)
class NativeSourceLifecycleTest {
    private val directory = "${NSTemporaryDirectory()}/nativecmpkit-source-${NSUUID().UUIDString}"

    init { check(NSFileManager.defaultManager.createDirectoryAtPath(directory, true, null, null)) }

    @AfterTest fun cleanup() {
        check(NSFileManager.defaultManager.removeItemAtPath(directory, null))
    }

    @Test fun rawNativeSourceOpenReadAndRepeatedCloseReleaseOnlyItsDescriptor() = runTest {
        val bytes = byteArrayOf(1, 0, -1, -128)
        val file = write("raw.bin", bytes)
        assertEquals(emptySet(), descriptors(file))
        val source = file.source()
        try {
            assertEquals(1, descriptors(file).size, "The actual stream owns one descriptor for this inode")
            val buffer = Buffer()
            assertEquals(4L, source.readAtMostTo(buffer, 4))
            assertContentEquals(bytes, buffer.readByteArray())
        } finally { source.close() }
        source.close()
        assertEquals(emptySet(), descriptors(file))
        assertTrue(file.exists(), "Stream closure never deletes the readable file")
    }

    @Test fun boundedRealNativeSourceClosesOnLimitFailure() = runTest {
        val file = write("limit.bin", ByteArray(300_000) { (it % 251).toByte() })
        val source = file.source()
        assertEquals(1, descriptors(file).size)
        assertFailsWith<IOException> { source.readBounded(128) }
        assertEquals(emptySet(), descriptors(file))
        assertEquals(300_000L, file.getSize())
    }

    @Test fun cancellationAtTheFirstNativeReadYieldClosesTheActualStream() = runTest {
        val file = write("cancel.bin", ByteArray(300_000) { it.toByte() })
        var completed = false
        val job = launch(start = CoroutineStart.UNDISPATCHED) {
            file.source().readBounded(300_000)
            completed = true
        }
        try {
            assertFalse(job.isCompleted, "The bounded reader must reach an actual cancellable yield")
            assertEquals(1, descriptors(file).size, "Cancel while the real source is still open")
        } finally { job.cancelAndJoin() }
        assertFalse(completed)
        assertEquals(emptySet(), descriptors(file))
    }

    @Test fun repeatedNativeSourceAndWholeFileReadsLeaveNoOwnedDescriptors() = runTest {
        val bytes = ByteArray(8_193) { (it % 251).toByte() }
        val file = write("repeat.bin", bytes)
        repeat(20) {
            assertContentEquals(bytes, file.readByteArray())
            assertContentEquals(bytes, file.source().buffered().use { source -> source.readByteArray() })
            assertEquals(emptySet(), descriptors(file), "Owned descriptor leaked at iteration $it")
        }
    }

    @Test fun failureWhileConsumingARealNativeSourceClosesViaUse() = runTest {
        val file = write("throw.bin", byteArrayOf(2, 4, 6))
        assertFailsWith<IOException> {
            file.source().buffered().use { source ->
                assertEquals(1, descriptors(file).size)
                assertEquals(2, source.readByte().toInt())
                throw IOException("Owned consumer failure")
            }
        }
        assertEquals(emptySet(), descriptors(file))
    }

    private fun write(name: String, bytes: ByteArray): KmpFile {
        val url = NSURL.fileURLWithPath("$directory/$name")
        val data = bytes.usePinned { NSData.create(bytes = it.addressOf(0), length = bytes.size.toULong()) }
        check(data.writeToURL(url, atomically = true))
        return KmpFile(url)
    }

    private fun descriptors(file: KmpFile): Set<Int> = memScoped {
        val identity = alloc<stat>()
        check(stat(checkNotNull(file.url.path), identity.ptr) == 0)
        val limit = getdtablesize()
        check(limit in 1..65_536) { "Descriptor-table range is unavailable/unbounded; do not guess coverage" }
        val observed = alloc<stat>()
        buildSet {
            for (fd in 0 until limit) {
                if (fstat(fd, observed.ptr) == 0 && observed.st_dev == identity.st_dev && observed.st_ino == identity.st_ino) {
                    add(fd)
                }
            }
        }
    }
}
