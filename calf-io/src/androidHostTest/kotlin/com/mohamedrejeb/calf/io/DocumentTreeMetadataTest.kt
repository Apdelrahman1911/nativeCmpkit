package com.mohamedrejeb.calf.io

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.provider.DocumentsContract
import android.provider.DocumentsContract.Document
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.shadows.ShadowContentResolver
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Executes the real DocumentFile/ContentResolver queries against an in-process provider. */
@RunWith(RobolectricTestRunner::class)
class DocumentTreeMetadataTest {
    @Test fun aTreeChildDoesNotReadTheRootsMetadata() {
        val context = RuntimeEnvironment.getApplication()
        val provider = TestProvider().apply {
            attachInfo(context, ProviderInfo().apply { authority = AUTHORITY })
        }
        ShadowContentResolver.registerProviderInternal(AUTHORITY, provider)
        val tree = DocumentsContract.buildTreeDocumentUri(AUTHORITY, "root")
        val child = DocumentsContract.buildDocumentUriUsingTree(tree, "child")
        val missing = DocumentsContract.buildDocumentUriUsingTree(tree, "missing")
        val rootFile = KmpFile(tree)
        val childFile = KmpFile(child)

        assertTrue(rootFile.exists(context))
        assertTrue(rootFile.isDirectory(context))
        assertEquals("Folder", rootFile.getName(context))
        assertNull(rootFile.getSize(context))
        assertTrue(childFile.exists(context))
        assertFalse(childFile.isDirectory(context))
        assertEquals("README", childFile.getName(context))
        assertEquals(42L, childFile.getSize(context))
        assertFalse(KmpFile(missing).exists(context))
        assertEquals(tree, rootFile.uri, "preserve the grant-bearing original tree URI")
    }

    class TestProvider : ContentProvider() {
        override fun onCreate(): Boolean = true
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor {
            val columns = projection ?: arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME, Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE)
            val id = DocumentsContract.getDocumentId(uri)
            val cursor = MatrixCursor(columns)
            if (id == "missing") return cursor
            cursor.addRow(columns.map<String, Any?> {
                when (it) {
                    Document.COLUMN_DOCUMENT_ID -> id
                    Document.COLUMN_DISPLAY_NAME -> if (id == "root") "Folder" else "README"
                    Document.COLUMN_MIME_TYPE -> if (id == "root") Document.MIME_TYPE_DIR else "text/plain"
                    Document.COLUMN_SIZE -> if (id == "root") null else 42L
                    else -> null
                }
            }.toTypedArray())
            return cursor
        }
        override fun getType(uri: Uri): String = if (DocumentsContract.getDocumentId(uri) == "root") Document.MIME_TYPE_DIR else "text/plain"
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("unused")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?): Int = error("unused")
    }
    companion object { private const val AUTHORITY = "nativecmpkit.io.test.documents" }
}
