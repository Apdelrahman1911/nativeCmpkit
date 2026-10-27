package com.mohamedrejeb.calf.io

import java.io.InputStream
import java.io.ByteArrayInputStream
import java.io.IOException
import org.junit.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class ReadOwnershipTest {
    @Test fun readFailureClosesOnceAndKeepsCloseFailureSuppressed() {
        val readFailure = IOException("read")
        val closeFailure = IOException("close")
        var closes = 0
        val input = object : InputStream() {
            var reads = 0
            override fun read(): Int = if (reads++ < 9) reads else throw readFailure
            override fun close() { closes++; throw closeFailure }
        }
        assertEquals(readFailure, assertFailsWith<IOException> { input.readAndClose() })
        assertEquals(1, closes)
        assertEquals(listOf(closeFailure), readFailure.suppressed.toList())
    }

    @Test fun successfulEmptyReadClosesOnce() {
        var closes = 0
        val input = object : InputStream() {
            override fun read(): Int = -1
            override fun close() { closes++ }
        }
        assertContentEquals(byteArrayOf(), input.readAndClose())
        assertEquals(1, closes)
    }

    @Test fun successfulNonemptyReadClosesOnce() {
        val bytes = byteArrayOf(9, 0, -1, -128)
        var closes = 0
        val input = object : ByteArrayInputStream(bytes) {
            override fun close() { closes++; super.close() }
        }
        assertContentEquals(bytes, input.readAndClose())
        assertEquals(1, closes)
    }

    @Test fun successfulReadDoesNotHideAClosingFailure() {
        val failure = IOException("close failed after successful read")
        var closes = 0
        val input = object : ByteArrayInputStream(byteArrayOf(1, 2, 3)) {
            override fun close() { closes++; throw failure }
        }
        assertEquals(failure, assertFailsWith<IOException> { input.readAndClose() })
        assertEquals(1, closes)
    }
}
