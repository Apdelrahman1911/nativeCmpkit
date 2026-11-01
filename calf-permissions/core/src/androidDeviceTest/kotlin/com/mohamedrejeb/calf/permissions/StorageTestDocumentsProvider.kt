// SPDX-License-Identifier: Apache-2.0
package com.mohamedrejeb.calf.permissions

import android.database.Cursor
import android.database.MatrixCursor
import android.os.CancellationSignal
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract.Document
import android.provider.DocumentsContract.Root
import android.provider.DocumentsProvider
import java.io.File

/** Reporter-owned private bytes. Cross-UID access requires a genuine Android SAF grant. */
class StorageTestDocumentsProvider : DocumentsProvider() {
    private val directory get() = File(checkNotNull(context).filesDir, "nativecmpkit-storage-saf")
    override fun onCreate() = true

    override fun queryRoots(projection: Array<out String>?): Cursor {
        val columns = projection ?: arrayOf(Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID,
            Root.COLUMN_TITLE, Root.COLUMN_FLAGS, Root.COLUMN_MIME_TYPES)
        return MatrixCursor(columns).apply {
            val values = mapOf(Root.COLUMN_ROOT_ID to "storage-root", Root.COLUMN_DOCUMENT_ID to "root",
                Root.COLUMN_TITLE to "NativeCmpKit storage test", Root.COLUMN_FLAGS to 0,
                Root.COLUMN_MIME_TYPES to "application/octet-stream")
            addRow(columns.map(values::get).toTypedArray<Any?>())
        }
    }

    override fun queryDocument(documentId: String, projection: Array<out String>?): Cursor =
        cursor(projection).apply { add(documentId) }

    override fun queryChildDocuments(parentDocumentId: String, projection: Array<out String>?, sortOrder: String?): Cursor {
        check(parentDocumentId == "root")
        val files = checkNotNull(directory.listFiles()).filter { it.name.matches(Regex("[a-f0-9]{32}\\.bin")) }
        check(files.size == 1)
        return cursor(projection).apply { add(files.single().name) }
    }

    override fun openDocument(documentId: String, mode: String, signal: CancellationSignal?): ParcelFileDescriptor {
        check(mode == "r"); signal?.throwIfCanceled()
        return ParcelFileDescriptor.open(document(documentId), ParcelFileDescriptor.MODE_READ_ONLY)
    }

    private fun document(id: String): File {
        check(id.matches(Regex("[a-f0-9]{32}\\.bin")))
        return File(directory, id).also { check(it.isFile && it.parentFile?.canonicalFile == directory.canonicalFile) }
    }

    private fun cursor(projection: Array<out String>?): MatrixCursor {
        val columns = projection ?: arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
            Document.COLUMN_MIME_TYPE, Document.COLUMN_FLAGS, Document.COLUMN_SIZE, Document.COLUMN_LAST_MODIFIED)
        return MatrixCursor(columns)
    }

    private fun MatrixCursor.add(id: String) {
        val isRoot = id == "root"
        val file = if (isRoot) null else document(id)
        val values = mapOf(Document.COLUMN_DOCUMENT_ID to id,
            Document.COLUMN_DISPLAY_NAME to if (isRoot) "NativeCmpKit storage test" else id,
            Document.COLUMN_MIME_TYPE to if (isRoot) Document.MIME_TYPE_DIR else "application/octet-stream",
            Document.COLUMN_FLAGS to 0, Document.COLUMN_SIZE to (file?.length() ?: 0),
            Document.COLUMN_LAST_MODIFIED to (file?.lastModified() ?: 0))
        addRow(columnNames.map(values::get).toTypedArray<Any?>())
    }
}
