package com.mohamedrejeb.calf.picker

import android.net.Uri
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import com.mohamedrejeb.calf.io.KmpFile
import java.io.IOException
import kotlinx.coroutines.test.runTest
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/** Real source inodes; controlled destination-only metadata failures, not native ACLs. */
@RunWith(RobolectricTestRunner::class)
@Config(shadows = [HostFileStatShadow::class])
class DestinationIdentityBoundaryAcceptanceTest {
    @get:Rule val folder = TemporaryFolder()

    @Test fun onlyDestinationInodeZeroRefusesBeforeDestructiveWriteOrCleanup() = runTest {
        val source = folder.newFile("identified-source").apply { writeBytes(SOURCE) }
        val destination = folder.newFile("unidentified-destination").apply { writeBytes(DESTINATION) }
        val resolver = RuntimeEnvironment.getApplication().contentResolver
        val originalSource = Os.stat(source.path)
        val originalDestination = Os.stat(destination.path)
        assertNotEquals(0L, originalSource.st_ino)
        assertNotEquals(0L, originalDestination.st_ino)
        withInconclusiveFileIdentities(listOf(destination)) {
            assertEquals(originalSource.st_ino, Os.stat(source.path).st_ino,
                "Source must pass its own identity guard; do not repeat the source-zero test")
            assertEquals(0L, Os.stat(destination.path).st_ino)
            val failure = assertFailsWith<IOException> {
                resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination))
            }
            assertEquals("The destination file identity is unavailable", failure.message)
            val result = assertNotNull(resolver.writeSaveSource(
                SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination),
            ))
            assertIs<IOException>(result.cause)
            assertEquals(failure.message, result.cause?.message)
            assertContentEquals(SOURCE, source.readBytes())
            assertContentEquals(DESTINATION, destination.readBytes())
            assertTrue(source.exists() && destination.exists())
        }
        assertEquals(originalSource.st_ino, Os.stat(source.path).st_ino)
        assertEquals(originalDestination.st_ino, Os.stat(destination.path).st_ino)
    }

    @Test fun destinationAccessIoAndPolicyStatFailuresNeverBecomeAbsentDestination() = runTest {
        val source = folder.newFile("known-source").apply { writeBytes(SOURCE) }
        val destination = folder.newFile("existing-destination").apply { writeBytes(DESTINATION) }
        val resolver = RuntimeEnvironment.getApplication().contentResolver
        val sourceInode = Os.stat(source.path).st_ino
        val destinationInode = Os.stat(destination.path).st_ino
        assertNotEquals(0L, sourceInode)
        assertNotEquals(0L, destinationInode)
        for (errno in listOf(OsConstants.EACCES, OsConstants.EIO, OsConstants.EPERM)) {
            withFailingFileStat(destination, errno) {
                assertEquals(sourceInode, Os.stat(source.path).st_ino)
                val nativeShapedFailure = assertFailsWith<ErrnoException> { Os.stat(destination.path) }
                assertEquals(errno, nativeShapedFailure.errno)
                val directFailure = assertFailsWith<ErrnoException> {
                    resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination))
                }
                assertEquals(errno, directFailure.errno)
                val result = assertNotNull(resolver.writeSaveSource(
                    SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination),
                ))
                assertEquals(errno, assertIs<ErrnoException>(result.cause).errno)
                assertTrue(source.exists() && destination.exists())
                assertContentEquals(SOURCE, source.readBytes())
                assertContentEquals(DESTINATION, destination.readBytes())
            }
            assertEquals(sourceInode, Os.stat(source.path).st_ino)
            assertEquals(destinationInode, Os.stat(destination.path).st_ino,
                "Every controlled failure must release only its own injection")
        }
    }

    companion object {
        private val SOURCE = byteArrayOf(9, 8, 0, -1, 7)
        private val DESTINATION = byteArrayOf(2, 1, 4)
    }
}
