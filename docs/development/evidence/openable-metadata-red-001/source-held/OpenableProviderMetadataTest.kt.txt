package com.mohamedrejeb.calf.io

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.provider.DocumentsContract.Document
import android.provider.OpenableColumns
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Actual AndroidX/ContentResolver calls on the host; this does not certify Binder behavior. */
@RunWith(RobolectricTestRunner::class)
class OpenableProviderMetadataTest {
    private val context = RuntimeEnvironment.getApplication()
    private lateinit var provider: OpenableProvider
    private val file = KmpFile(Uri.parse("content://$AUTHORITY/openable/report.bin"))

    @Before fun registerOpenableProvider() {
        provider = OpenableProvider().apply {
            attachInfo(context, ProviderInfo().apply { authority = AUTHORITY })
        }
        ShadowContentResolver.registerProviderInternal(AUTHORITY, provider)
    }

    @Test fun openableFilesNeverReceiveDocumentsProviderOnlyMimeQueries() {
        assertFalse(file.isDirectory(context))
        assertEquals(64L, file.getSize(context))
        assertEquals("report.bin", file.getName(context))
        assertEquals("application/octet-stream", file.getMimeType(context))
        assertEquals(0, provider.unsupportedProjections,
            "An openable provider is not required to support Document.COLUMN_MIME_TYPE")
        assertEquals(1, provider.sizeQueries)
    }

    @Test fun anExplicitDirectoryMimeTypeDoesNotReadSizeAsAnOrdinaryFile() {
        provider.mimeType = Document.MIME_TYPE_DIR
        assertTrue(file.isDirectory(context))
        assertNull(file.getSize(context))
        assertEquals(0, provider.sizeQueries)
        assertEquals(0, provider.unsupportedProjections)
    }

    @Test fun missingOrDeniedMimeMetadataDoesNotInventAFileSizeOrQueryDocumentColumns() {
        for (denyType in listOf(false, true)) {
            provider.mimeType = null
            provider.denyType = denyType
            assertFalse(file.isDirectory(context))
            assertEquals(64L, file.getSize(context), "A readable size query remains independent of denied type metadata")
            provider.size = null
            assertNull(file.getSize(context))
            provider.size = 64L
        }
        assertEquals(0, provider.unsupportedProjections)
        assertEquals(4, provider.sizeQueries)
    }

    class OpenableProvider : ContentProvider() {
        var mimeType: String? = "application/octet-stream"
        var denyType = false
        var size: Long? = 64L
        var unsupportedProjections = 0
        var sizeQueries = 0

        override fun onCreate(): Boolean = true

        override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
                           selectionArgs: Array<out String>?, sortOrder: String?): Cursor {
            val columns = projection ?: arrayOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE)
            if (columns.any { it !in setOf(OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE) }) {
                unsupportedProjections++
                throw IllegalArgumentException("Openable provider does not expose document-specific columns")
            }
            if (OpenableColumns.SIZE in columns) sizeQueries++
            return MatrixCursor(columns).apply {
                addRow(columns.map<String, Any?> {
                    if (it == OpenableColumns.SIZE) size else "report.bin"
                }.toTypedArray())
            }
        }

        override fun getType(uri: Uri): String? {
            if (denyType) throw SecurityException("Fixture type metadata permission denied")
            return mimeType
        }

        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }

    companion object { private const val AUTHORITY = "nativecmpkit.io.test.openable" }
}
