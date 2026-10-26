package com.mohamedrejeb.calf.io

import com.mohamedrejeb.calf.core.PlatformContext
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.test.runTest
import kotlinx.io.IOException
import org.w3c.dom.events.Event
import org.w3c.files.File
import org.w3c.files.FileReader
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

internal expect fun browserFixtureFile(name: String, content: String): File
internal expect fun installBrowserReaderErrorFixture(reader: FileReader, nonStringName: Boolean)
internal expect fun removeBrowserReaderErrorFixture(reader: FileReader): Boolean

/** Native browser File/FileReader and DOM events; no JVM reader substitute. */
class BrowserFileReadTest {
    @Test fun emptyAndBinaryFilesReadExactlyAndDetachAllHandlers() = runTest {
        for ((content, bytes) in listOf("" to byteArrayOf(), "\u0000\u0001\u007f" to byteArrayOf(0, 1, 127))) {
            val reader = FileReader()
            assertContentEquals(bytes, readBrowserFile(browserFixtureFile("binary", content), reader))
            assertDetached(reader)
        }
    }

    @Test fun nativeAbortIsAnErrorNotAnEmptyFile() = runTest {
        supervisorScope {
            val reader = FileReader()
            val read = async(start = CoroutineStart.UNDISPATCHED) { readBrowserFile(browserFixtureFile("data", "abc"), reader) }
            reader.abort()
            assertFailsWith<IOException> { read.await() }
            assertDetached(reader)
        }
    }

    @Test fun coroutineCancellationAbortsTheNativeReadAndDetachesHandlers() = runTest {
        val reader = FileReader()
        val read = async(start = CoroutineStart.UNDISPATCHED) { readBrowserFile(browserFixtureFile("large", "a".repeat(100_000)), reader) }
        read.cancel()
        read.join()
        assertTrue(reader.readyState != FileReader.LOADING)
        assertDetached(reader)
    }

    @Test fun errorEventDoesNotResumeAsSuccessAndLateAbortCannotResumeTwice() = runTest {
        val reader = FileReader()
        assertNull(reader.error)
        assertSyntheticErrorBeforeLateAbort(reader, "Browser file read failed: unknown error")
    }

    @Test fun nativeDomExceptionReportsOnlyItsNameAndDetachesHandlers() = runTest {
        val reader = FileReader()
        // The instance-local getter returns a real DOMException, not a real OS read denial.
        installBrowserReaderErrorFixture(reader, nonStringName = false)
        try {
            assertSyntheticErrorBeforeLateAbort(reader, "Browser file read failed: NotReadableError")
        } finally {
            assertTrue(removeBrowserReaderErrorFixture(reader))
        }
    }

    @Test fun nonStringErrorNameUsesUnknownErrorAndDetachesHandlers() = runTest {
        val reader = FileReader()
        installBrowserReaderErrorFixture(reader, nonStringName = true)
        try {
            assertSyntheticErrorBeforeLateAbort(reader, "Browser file read failed: unknown error")
        } finally {
            assertTrue(removeBrowserReaderErrorFixture(reader))
        }
    }

    @Test fun extensionlessFilesAndDotfilesAreNeverDirectoriesAndHaveNoFilesystemPath() {
        for (name in listOf("README", "LICENSE", ".gitignore", "report.pdf")) {
            val file = KmpFile(browserFixtureFile(name, "x"))
            assertEquals(name, file.getName())
            assertFalse(file.isDirectory())
            assertFalse(file.isDirectory(PlatformContext.INSTANCE))
            assertTrue(file.isFile())
            assertTrue(file.isFile(PlatformContext.INSTANCE))
            assertNull(file.getPath())
            assertNull(file.toUriString())
        }
    }

    private suspend fun assertSyntheticErrorBeforeLateAbort(reader: FileReader, expectedMessage: String) {
        supervisorScope {
            val read = async(start = CoroutineStart.UNDISPATCHED) { readBrowserFile(browserFixtureFile("data", "abc"), reader) }
            try {
                // Synthetic dispatch tests the native reader's listener path, not OS access denial.
                reader.dispatchEvent(Event("error"))
                assertDetached(reader)
                assertEquals(expectedMessage, assertFailsWith<IOException> { read.await() }.message)
                // An abort must not supply the first failure or replace the error-event outcome.
                reader.abort()
                assertDetached(reader)
                assertEquals(expectedMessage, assertFailsWith<IOException> { read.await() }.message)
            } finally {
                read.cancel()
                // Dispatching a synthetic error does not itself stop the native read.
                reader.abort()
            }
        }
    }

    private fun assertDetached(reader: FileReader) {
        assertNull(reader.onload)
        assertNull(reader.onerror)
        assertNull(reader.onabort)
    }
}
