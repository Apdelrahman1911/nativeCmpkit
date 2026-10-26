package com.mohamedrejeb.calf.picker.instrumentation

import android.database.Cursor
import android.database.MatrixCursor
import android.os.Bundle
import android.os.CancellationSignal
import android.os.Handler
import android.os.Looper
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract.Document
import android.provider.DocumentsContract.Root
import android.provider.DocumentsProvider
import com.mohamedrejeb.calf.picker.DeviceFileIdentity
import java.io.File
import java.io.FileNotFoundException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

/**
 * A genuine, OS-registered DocumentsProvider with real native descriptors and close callbacks.
 * It is a deterministic test fixture, not evidence about DocumentsUI, cloud vendors or URI grants.
 * Its only storage is this test APK's explicitly bounded synthetic cache subtree.
 */
class DeviceSaveDocumentsProvider : DocumentsProvider() {
    private class Record {
        val readAttempts = AtomicInteger()
        val readOpens = AtomicInteger()
        val readCloses = AtomicInteger()
        val writeAttempts = AtomicInteger()
        val writeOpens = AtomicInteger()
        val writeCloses = AtomicInteger()
        val deletes = AtomicInteger()
        val closeErrors = AtomicInteger()
    }

    private val records = ConcurrentHashMap<String, Record>()
    private val closeHandler by lazy { Handler(Looper.getMainLooper()) }
    private val root: File get() = File(checkNotNull(context).cacheDir, CACHE_DIRECTORY).canonicalFile

    override fun onCreate(): Boolean = root.isDirectory || root.mkdirs()

    override fun openDocument(documentId: String, mode: String, signal: CancellationSignal?): ParcelFileDescriptor {
        signal?.throwIfCanceled()
        val file = resolve(documentId)
        val record = record(documentId)
        val reading = mode == "r"
        if (reading) {
            record.readAttempts.incrementAndGet()
            if (file.name.startsWith("unreadable-")) {
                throw FileNotFoundException("Intentional device-fixture access revocation")
            }
        } else {
            record.writeAttempts.incrementAndGet()
        }
        val descriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.parseMode(mode), closeHandler) { error ->
            if (reading) record.readCloses.incrementAndGet() else record.writeCloses.incrementAndGet()
            if (error != null) record.closeErrors.incrementAndGet()
        }
        try {
            DeviceFileIdentity.of(descriptor)
        } catch (failure: Throwable) {
            try { descriptor.close() } catch (closeFailure: Throwable) {
                if (closeFailure !== failure) failure.addSuppressed(closeFailure)
            }
            throw failure
        }
        if (reading) record.readOpens.incrementAndGet() else record.writeOpens.incrementAndGet()
        return descriptor
    }

    override fun createDocument(parentDocumentId: String, mimeType: String, displayName: String): String {
        require(displayName.isNotBlank() && displayName !in setOf(".", "..") &&
            displayName.none { it == '/' || it == '\\' || it.isISOControl() })
        val parent = resolve(parentDocumentId)
        if (!parent.isDirectory) throw FileNotFoundException("Not a fixture directory")
        val file = File(parent, displayName)
        val created = if (mimeType == Document.MIME_TYPE_DIR) file.mkdir() else file.createNewFile()
        if (!created) throw FileNotFoundException("Fixture creation never overwrites an existing document")
        return if (parentDocumentId == ROOT_ID) displayName else "$parentDocumentId/$displayName"
    }

    override fun deleteDocument(documentId: String) {
        record(documentId).deletes.incrementAndGet()
        if (!resolve(documentId).delete()) throw FileNotFoundException("Could not delete fixture document")
    }

    override fun isChildDocument(parentDocumentId: String, documentId: String): Boolean {
        val parent = resolve(parentDocumentId)
        val child = resolve(documentId)
        return child.path.startsWith(parent.path + File.separator)
    }

    override fun queryDocument(documentId: String, projection: Array<out String>?): Cursor {
        val file = resolve(documentId)
        if (!file.exists()) throw FileNotFoundException("Fixture document is absent")
        return MatrixCursor(projection ?: DOCUMENT_COLUMNS).apply { addDocument(documentId, file) }
    }

    override fun queryChildDocuments(parentDocumentId: String, projection: Array<out String>?, sortOrder: String?): Cursor =
        MatrixCursor(projection ?: DOCUMENT_COLUMNS).apply {
            resolve(parentDocumentId).listFiles().orEmpty().forEach { file ->
                val id = if (parentDocumentId == ROOT_ID) file.name else "$parentDocumentId/${file.name}"
                addDocument(id, file)
            }
        }

    override fun queryRoots(projection: Array<out String>?): Cursor =
        MatrixCursor(projection ?: ROOT_COLUMNS).apply {
            addRow(columnNames.map { column ->
                when (column) {
                    Root.COLUMN_ROOT_ID -> ROOT_ID
                    Root.COLUMN_DOCUMENT_ID -> ROOT_ID
                    Root.COLUMN_TITLE -> "nativeCmpkit instrumentation fixtures"
                    Root.COLUMN_FLAGS -> Root.FLAG_SUPPORTS_CREATE or Root.FLAG_LOCAL_ONLY
                    else -> null
                }
            }.toTypedArray<Any?>())
        }

    override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
        if (method != STATS) return super.call(method, arg, extras)
        val record = arg?.let { records[it] }
        return Bundle().apply {
            putInt("readAttempts", record?.readAttempts?.get() ?: 0)
            putInt("readOpens", record?.readOpens?.get() ?: 0)
            putInt("readCloses", record?.readCloses?.get() ?: 0)
            putInt("writeAttempts", record?.writeAttempts?.get() ?: 0)
            putInt("writeOpens", record?.writeOpens?.get() ?: 0)
            putInt("writeCloses", record?.writeCloses?.get() ?: 0)
            putInt("deletes", record?.deletes?.get() ?: 0)
            putInt("closeErrors", record?.closeErrors?.get() ?: 0)
            putInt("providerPid", android.os.Process.myPid())
        }
    }

    private fun MatrixCursor.addDocument(documentId: String, file: File) {
        addRow(columnNames.map { column ->
            when (column) {
                Document.COLUMN_DOCUMENT_ID -> documentId
                Document.COLUMN_DISPLAY_NAME -> file.name
                Document.COLUMN_MIME_TYPE -> if (file.isDirectory) Document.MIME_TYPE_DIR else "application/octet-stream"
                Document.COLUMN_SIZE -> if (file.isDirectory) null else file.length()
                Document.COLUMN_FLAGS -> if (file.isDirectory) Document.FLAG_DIR_SUPPORTS_CREATE
                    else Document.FLAG_SUPPORTS_WRITE or Document.FLAG_SUPPORTS_DELETE
                else -> null
            }
        }.toTypedArray<Any?>())
    }

    private fun resolve(documentId: String): File {
        if (documentId == ROOT_ID) return root
        require(!documentId.startsWith('/') && documentId.split('/').all {
            it.isNotBlank() && it !in setOf(".", "..") && '\\' !in it && it.none(Char::isISOControl)
        })
        return File(root, documentId).canonicalFile.also {
            require(it.path.startsWith(root.path + File.separator)) { "Outside the test-owned fixture root" }
        }
    }

    private fun record(documentId: String): Record = records.getOrPut(documentId) { Record() }

    companion object {
        const val CACHE_DIRECTORY = "nativecmpkit-picker-device"
        const val ROOT_ID = "root"
        const val STATS = "nativecmpkit-device-stats"
        private val DOCUMENT_COLUMNS = arrayOf(Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME,
            Document.COLUMN_MIME_TYPE, Document.COLUMN_SIZE, Document.COLUMN_FLAGS)
        private val ROOT_COLUMNS = arrayOf(Root.COLUMN_ROOT_ID, Root.COLUMN_DOCUMENT_ID, Root.COLUMN_TITLE, Root.COLUMN_FLAGS)
    }
}
