package com.mohamedrejeb.calf.io

import java.io.InputStream
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
            override fun read(): Int = throw readFailure
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
}
