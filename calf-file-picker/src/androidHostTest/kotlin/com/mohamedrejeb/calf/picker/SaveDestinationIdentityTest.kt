package com.mohamedrejeb.calf.picker

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract
import android.system.Os
import com.mohamedrejeb.calf.io.KmpFile
import java.io.File
import java.io.FileNotFoundException
import java.nio.file.Files
import kotlinx.coroutines.test.runTest
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Real ContentResolver streams from one file exposed under tree and single-document URIs. */
@RunWith(RobolectricTestRunner::class)
@Config(shadows = [HostFileStatShadow::class])
class SaveDestinationIdentityTest {
    @get:Rule val folder = TemporaryFolder()

    @Test fun treeAndSingleDocumentAliasesNeverOpenTheOriginalForWrite() = runTest {
        val provider = provider()
        val tree = DocumentsContract.buildTreeDocumentUri(AUTHORITY, "root")
        val source = DocumentsContract.buildDocumentUriUsingTree(tree, "report")
        val destination = DocumentsContract.buildDocumentUri(AUTHORITY, "report")
        val resolver = RuntimeEnvironment.getApplication().contentResolver

        assertTrue(resolver.saveUrisReferToSameFile(source, destination))
        assertNull(resolver.writeSaveSource(SaveSource.File(KmpFile(source)), destination))
        assertContentEquals(CONTENT, provider.file.readBytes())
        assertEquals(1, provider.reads)
        assertEquals(0, provider.writes)
        assertEquals(0, provider.deletes)
    }

    @Test fun unreadableAliasReportsFailureWithoutDeletingTheOriginal() = runTest {
        val provider = provider().apply { readable = false }
        val tree = DocumentsContract.buildTreeDocumentUri(AUTHORITY, "root")
        val source = DocumentsContract.buildDocumentUriUsingTree(tree, "report")
        val destination = DocumentsContract.buildDocumentUri(AUTHORITY, "report")

        assertNotNull(RuntimeEnvironment.getApplication().contentResolver.writeSaveSource(SaveSource.File(KmpFile(source)), destination))
        assertContentEquals(CONTENT, provider.file.readBytes())
        assertEquals(0, provider.writes)
        assertEquals(0, provider.deletes)
    }

    @Test fun fileSymlinkAndCanonicalPathAliasesAreNotTruncated() = runTest {
        val original = folder.newFile("original").apply { writeBytes(CONTENT) }
        val alias = folder.root.resolve("alias")
        Files.createSymbolicLink(alias.toPath(), original.toPath())
        val resolver = RuntimeEnvironment.getApplication().contentResolver
        for (destination in listOf(alias, File(folder.root, "./original"))) {
            assertNull(resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(original))), Uri.fromFile(destination)))
            assertContentEquals(CONTENT, original.readBytes())
        }
    }

    @Test fun distinctFilesHaveRealDifferentIdentitiesAndCopyEveryByte() = runTest {
        val source = folder.newFile("source").apply { writeBytes(CONTENT) }
        val destination = folder.newFile("destination").apply { writeBytes(byteArrayOf(8)) }
        val resolver = RuntimeEnvironment.getApplication().contentResolver
        val sourceStat = Os.stat(source.path)
        val destinationStat = Os.stat(destination.path)
        assertEquals((Files.getAttribute(source.toPath(), "unix:ino") as Number).toLong(), sourceStat.st_ino)
        assertEquals((Files.getAttribute(destination.toPath(), "unix:ino") as Number).toLong(), destinationStat.st_ino)
        assertTrue(sourceStat.st_ino != destinationStat.st_ino)
        assertFalse(resolver.saveUrisReferToSameFile(Uri.fromFile(source), Uri.fromFile(destination)))

        assertNull(resolver.writeSaveSource(SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination)))

        assertContentEquals(CONTENT, source.readBytes())
        assertContentEquals(CONTENT, destination.readBytes())
    }

    @Test fun hardLinkIdentityPreservesBothNamesAndOriginalContent() = runTest {
        val original = folder.newFile("original-hardlink").apply { writeBytes(CONTENT) }
        val alias = folder.root.resolve("hardlink")
        Files.createLink(alias.toPath(), original.toPath())
        val resolver = RuntimeEnvironment.getApplication().contentResolver
        val source = Uri.fromFile(original)
        val destination = Uri.fromFile(alias)
        assertEquals(Os.stat(original.path).st_ino, Os.stat(alias.path).st_ino)
        assertTrue(resolver.saveUrisReferToSameFile(source, destination))

        assertNull(resolver.writeSaveSource(SaveSource.File(KmpFile(source)), destination))

        assertTrue(original.exists())
        assertTrue(alias.exists())
        assertContentEquals(CONTENT, original.readBytes())
        assertContentEquals(CONTENT, alias.readBytes())
    }

    @Test fun missingSourceIdentityNeverOverwritesOrDeletesDestination() = runTest {
        val source = folder.root.resolve("missing-source")
        val destination = folder.newFile("existing-destination").apply { writeBytes(CONTENT) }

        assertNotNull(RuntimeEnvironment.getApplication().contentResolver.writeSaveSource(
            SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination),
        ))

        assertContentEquals(CONTENT, destination.readBytes())
    }

    @Test fun onlyMissingDestinationCanBeCreatedAfterSourceIdentityWasEstablished() = runTest {
        val source = folder.newFile("known-source").apply { writeBytes(CONTENT) }
        val destination = folder.root.resolve("new-destination")

        assertNull(RuntimeEnvironment.getApplication().contentResolver.writeSaveSource(
            SaveSource.File(KmpFile(Uri.fromFile(source))), Uri.fromFile(destination),
        ))

        assertContentEquals(CONTENT, source.readBytes())
        assertContentEquals(CONTENT, destination.readBytes())
    }

    private fun provider(): AliasProvider = AliasProvider(folder.newFile("data").apply { writeBytes(CONTENT) }).also {
        it.attachInfo(RuntimeEnvironment.getApplication(), ProviderInfo().apply { authority = AUTHORITY })
        ShadowContentResolver.registerProviderInternal(AUTHORITY, it)
    }

    class AliasProvider(val file: File) : ContentProvider() {
        var readable = true
        var reads = 0
        var writes = 0
        var deletes = 0
        override fun onCreate(): Boolean = true
        override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
            if (mode == "r") { reads++; if (!readable) throw FileNotFoundException("Access revoked") }
            else writes++
            return ParcelFileDescriptor.open(file, ParcelFileDescriptor.parseMode(mode))
        }
        override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
            if (method == "android:deleteDocument") { deletes++; file.delete() }
            return Bundle()
        }
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null
        override fun getType(uri: Uri): String = "application/octet-stream"
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int { deletes++; return if (file.delete()) 1 else 0 }
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }

    companion object {
        private const val AUTHORITY = "nativecmpkit.picker.test.documents"
        private val CONTENT = byteArrayOf(1, 2, 0, -1, 3)
    }
}
