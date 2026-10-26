package com.mohamedrejeb.calf.picker

import android.net.Uri
import android.system.Os
import com.mohamedrejeb.calf.io.KmpFile
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
import kotlin.test.assertNotNull
import kotlin.test.assertNotEquals

@RunWith(RobolectricTestRunner::class)
@Config(shadows = [HostFileStatShadow::class])
class InconclusiveSaveIdentityTest {
    @get:Rule val folder = TemporaryFolder()

    @Test fun unknownDeviceAndInodeCannotInventSuccessOrAuthorizeDestructiveWrite() = runTest {
        val original = byteArrayOf(9, 8, 7)
        val oldDestination = byteArrayOf(1, 0, -1, 2)
        val source = folder.newFile("source").apply { writeBytes(original) }
        val destination = folder.newFile("destination").apply { writeBytes(oldDestination) }
        withInconclusiveFileIdentities(listOf(source, destination)) {
            assertEquals(0L, Os.stat(source.path).st_ino, "explicit inconclusive identity fixture")
            assertEquals(0L, Os.stat(destination.path).st_ino)

            val failure = RuntimeEnvironment.getApplication().contentResolver.writeSaveSource(
                SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination),
            )

            assertNotNull(failure, "unknown identity must report an error, not successful empty output")
            assertContentEquals(original, source.readBytes(), "never truncate the possible original")
            assertContentEquals(oldDestination, destination.readBytes(), "no write or cleanup before identity is known")
        }
        assertNotEquals(0L, Os.stat(source.path).st_ino, "fixture must restore real host identity")
        assertNotEquals(0L, Os.stat(destination.path).st_ino)
    }
}
