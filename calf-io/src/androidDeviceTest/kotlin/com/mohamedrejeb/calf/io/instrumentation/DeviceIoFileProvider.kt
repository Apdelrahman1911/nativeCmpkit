package com.mohamedrejeb.calf.io.instrumentation

import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.provider.OpenableColumns
import android.system.OsConstants
import androidx.core.content.FileProvider
import com.mohamedrejeb.calf.io.DeviceDescriptorIdentity
import java.io.FileNotFoundException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/**
 * OS-registered, private, separate-process FileProvider over test-owned cache files only.
 * Normal opens delegate unchanged to AndroidX FileProvider. Two explicit fixture modes exercise
 * legal unknown-size metadata and a real reliable-pipe read error; no Android classes are shadowed.
 */
class DeviceIoFileProvider : FileProvider() {
    private class OpenRecord {
        val opens = AtomicInteger()
        @Volatile var pipeDevice: Long = 0
        @Volatile var pipeInode: Long = 0
        @Volatile var pipeMode: Int = 0
        @Volatile var pipeFdInfoInode: Long = 0
        val workerFinished = AtomicBoolean()
        val workerFailed = AtomicBoolean()
    }

    private val records = ConcurrentHashMap<String, OpenRecord>()

    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
        val faultingRead = uri.getQueryParameter(FIXTURE_MODE) == READ_ERROR
        if (faultingRead) require(mode == "r")
        // Use FileProvider's actual path validation and native file descriptor in every mode.
        val source = super.openFile(uri, mode)
            ?: throw FileNotFoundException("Real fixture FileProvider returned no descriptor")
        try {
            check(OsConstants.S_ISREG(DeviceDescriptorIdentity.of(source).mode)) {
                "The actual FileProvider source must be a calibrated regular file"
            }
        } catch (failure: Throwable) {
            try { source.close() } catch (closeFailure: Throwable) {
                if (closeFailure !== failure) failure.addSuppressed(closeFailure)
            }
            throw failure
        }
        val record = records.getOrPut(uri.toString()) { OpenRecord() }
        record.opens.incrementAndGet()
        if (!faultingRead) return source
        val pipe = try {
            ParcelFileDescriptor.createReliablePipe()
        } catch (failure: Exception) {
            source.close()
            throw failure
        }
        try {
            val identity = DeviceDescriptorIdentity.of(pipe[0])
            check(OsConstants.S_ISFIFO(identity.mode)) { "The reliable pipe must be a real FIFO" }
            record.pipeDevice = identity.device
            record.pipeInode = identity.inode
            record.pipeMode = identity.mode
            record.pipeFdInfoInode = identity.fdInfoInode
            thread(name = "nativecmpkit-device-read-error", isDaemon = true) {
                val output = ParcelFileDescriptor.AutoCloseOutputStream(pipe[1])
                try {
                    ParcelFileDescriptor.AutoCloseInputStream(source).use { input ->
                        val prefix = ByteArray(64)
                        val count = input.read(prefix)
                        if (count > 0) output.write(prefix, 0, count)
                    }
                    // This is delivered by the real Android PFD/ContentResolver read path.
                    pipe[1].closeWithError(READ_ERROR_MESSAGE)
                } catch (failure: Exception) {
                    record.workerFailed.set(true)
                    runCatching { pipe[1].closeWithError("Device fixture producer failed") }
                } finally {
                    runCatching { source.close() }
                    runCatching { output.close() }
                    record.workerFinished.set(true)
                }
            }
            return pipe[0]
        } catch (failure: Throwable) {
            (listOf(source) + pipe).forEach { owned ->
                try { owned.close() } catch (closeFailure: Throwable) {
                    if (closeFailure !== failure) failure.addSuppressed(closeFailure)
                }
            }
            throw failure
        }
    }

    override fun query(
        uri: Uri,
        projection: Array<out String>?,
        selection: String?,
        selectionArgs: Array<out String>?,
        sortOrder: String?,
    ): Cursor {
        val original = super.query(uri, projection, selection, selectionArgs, sortOrder)
        if (uri.getQueryParameter(FIXTURE_MODE) !in setOf(UNKNOWN_SIZE, READ_ERROR)) return original
        return original.use { cursor ->
            MatrixCursor(cursor.columnNames).apply {
                while (cursor.moveToNext()) {
                    addRow(cursor.columnNames.mapIndexed { index, name ->
                        if (name == OpenableColumns.SIZE) null else when (cursor.getType(index)) {
                            Cursor.FIELD_TYPE_NULL -> null
                            Cursor.FIELD_TYPE_INTEGER -> cursor.getLong(index)
                            Cursor.FIELD_TYPE_FLOAT -> cursor.getDouble(index)
                            Cursor.FIELD_TYPE_BLOB -> cursor.getBlob(index)
                            else -> cursor.getString(index)
                        }
                    }.toTypedArray())
                }
            }
        }
    }

    override fun call(method: String, arg: String?, extras: Bundle?): Bundle? {
        if (method != STATS) return super.call(method, arg, extras)
        val record = arg?.let { records[it] }
        return Bundle().apply {
            putInt("opens", record?.opens?.get() ?: 0)
            putLong("pipeDevice", record?.pipeDevice ?: 0)
            putLong("pipeInode", record?.pipeInode ?: 0)
            putInt("pipeMode", record?.pipeMode ?: 0)
            putLong("pipeFdInfoInode", record?.pipeFdInfoInode ?: 0)
            putBoolean("workerFinished", record?.workerFinished?.get() ?: false)
            putBoolean("workerFailed", record?.workerFailed?.get() ?: false)
            putInt("providerPid", android.os.Process.myPid())
        }
    }

    companion object {
        const val FIXTURE_MODE = "nativecmpkitFixture"
        const val UNKNOWN_SIZE = "unknown-size"
        const val READ_ERROR = "read-error"
        const val READ_ERROR_MESSAGE = "Intentional nativeCmpkit device-fixture read error"
        const val STATS = "nativecmpkit-device-stats"
    }
}
