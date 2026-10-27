package com.mohamedrejeb.calf.io

import kotlinx.cinterop.BetaInteropApi
import kotlinx.cinterop.ByteVar
import kotlinx.cinterop.CPointer
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.cinterop.get
import kotlinx.cinterop.plus
import kotlinx.cinterop.reinterpret
import kotlinx.cinterop.set
import kotlinx.io.IOException
import platform.Foundation.NSData
import platform.Foundation.create
import platform.posix.MAP_ANON
import platform.posix.MAP_FAILED
import platform.posix.MAP_PRIVATE
import platform.posix.PROT_NONE
import platform.posix.PROT_READ
import platform.posix.PROT_WRITE
import platform.posix.getpagesize
import platform.posix.mmap
import platform.posix.mprotect
import platform.posix.munmap
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

/** Real Darwin mappings: any over-read/write at the payload end hits PROT_NONE, not a mock. */
@OptIn(ExperimentalForeignApi::class, BetaInteropApi::class)
class NativeGuardedCopyTest {
    @Test fun emptyFoundationDataNeedsNoPointer() {
        val empty = NSData()
        empty.copyToCheckedNativeBuffer(null, 0)
        assertContentEquals(byteArrayOf(), empty.toCheckedByteArray())
    }

    @Test fun validatedFoundationCopyDoesNotCrossSourceOrDestinationGuardPages() {
        val page = getpagesize()
        for (count in listOf(1, 6, page - 1, page)) {
            GuardedBuffer(count).use { source ->
                GuardedBuffer(count).use { destination ->
                    val expected = ByteArray(count) { (it % 251).toByte() }
                    source.write(expected)
                    // The external mapping owns these bytes. NSData must neither free them nor
                    // outlive its last use; no oversized/fabricated Foundation length is used.
                    val data = NSData.create(bytesNoCopy = source.bytes, length = count.toULong(), freeWhenDone = false)
                    data.copyToCheckedNativeBuffer(destination.bytes, count)
                    assertContentEquals(expected, destination.read())
                    assertContentEquals(expected, data.toCheckedByteArray())
                    assertEquals(if (count < page) 91 else null, destination.prefixSentinel())
                }
            }
        }
    }

    @Test fun tooSmallGuardedDestinationIsRejectedBeforeAnyNativeWrite() {
        GuardedBuffer(2).use { source ->
            source.write(byteArrayOf(4, 5))
            val data = NSData.create(bytesNoCopy = source.bytes, length = 2uL, freeWhenDone = false)
            GuardedBuffer(1).use { destination ->
                destination.write(byteArrayOf(33))
                assertFailsWith<IOException> { data.copyToCheckedNativeBuffer(destination.bytes, 1) }
                assertContentEquals(byteArrayOf(33), destination.read())
                assertEquals(91, destination.prefixSentinel())
            }
        }
    }

    @Test fun positiveLengthNeedsANonNullDestination() {
        GuardedBuffer(1).use { source ->
            source.write(byteArrayOf(7))
            val data = NSData.create(bytesNoCopy = source.bytes, length = 1uL, freeWhenDone = false)
            assertFailsWith<IOException> { data.copyToCheckedNativeBuffer(null, 1) }
            assertFailsWith<IllegalArgumentException> { data.copyToCheckedNativeBuffer(source.bytes, -1) }
        }
    }

    @Test fun nativeLengthBoundaryRejectsUnrepresentableCountsWithoutAllocation() {
        assertEquals(0, checkedByteArraySize(0uL))
        assertEquals(Int.MAX_VALUE, checkedByteArraySize(Int.MAX_VALUE.toULong()))
        assertFailsWith<IOException> { checkedByteArraySize(Int.MAX_VALUE.toULong() + 1uL) }
        assertFailsWith<IOException> { checkedByteArraySize(ULong.MAX_VALUE) }
    }

    private class GuardedBuffer(private val count: Int) : AutoCloseable {
        private val page = getpagesize()
        private val allocation = page.toULong() * 3uL
        private val base: CPointer<ByteVar>
        val bytes: CPointer<ByteVar>
        private var closed = false

        init {
            require(page > 0 && count in 1..page)
            val mapping = mmap(null, allocation, PROT_NONE, MAP_PRIVATE or MAP_ANON, -1, 0)
            check(mapping != null && mapping != MAP_FAILED) { "Owned native guard-page mmap failed" }
            base = mapping.reinterpret()
            try {
                val readable = checkNotNull(base + page)
                check(mprotect(readable, page.toULong(), PROT_READ or PROT_WRITE) == 0) {
                    "Owned native guard-page mprotect failed"
                }
                bytes = checkNotNull(readable + (page - count))
                if (count < page) checkNotNull(bytes + -1)[0] = 91
            } catch (failure: Throwable) {
                check(munmap(base, allocation) == 0) { "Guard fixture failure also failed owned unmap" }
                throw failure
            }
        }

        fun write(value: ByteArray) {
            check(!closed && value.size == count)
            for (index in value.indices) bytes[index] = value[index]
        }

        fun read(): ByteArray {
            check(!closed)
            return ByteArray(count) { bytes[it] }
        }

        fun prefixSentinel(): Int? {
            check(!closed)
            // A full page starts at PROT_NONE; it deliberately has no readable prefix.
            return if (count == page) null else checkNotNull(bytes + -1)[0].toInt()
        }

        override fun close() {
            if (!closed) {
                closed = true
                check(munmap(base, allocation) == 0) { "Owned guard-page unmap failed" }
            }
        }
    }
}
