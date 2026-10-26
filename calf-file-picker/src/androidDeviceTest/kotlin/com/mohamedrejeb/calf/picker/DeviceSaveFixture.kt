package com.mohamedrejeb.calf.picker

import android.content.Context
import android.net.Uri
import android.os.Bundle
import android.os.Process
import android.os.ParcelFileDescriptor
import android.os.SystemClock
import android.provider.DocumentsContract
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import androidx.core.content.FileProvider
import androidx.test.platform.app.InstrumentationRegistry
import com.mohamedrejeb.calf.picker.instrumentation.DeviceSaveDocumentsProvider
import java.io.File
import java.io.IOException
import java.util.UUID
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

internal class DeviceSaveFixture : AutoCloseable {
    val context: Context = InstrumentationRegistry.getInstrumentation().targetContext
    val resolver get() = context.contentResolver
    val documentsAuthority = context.packageName + ".picker-device-documents"
    private val filesAuthority = context.packageName + ".picker-device-files"
    val directory: File

    init {
        assertEquals(InstrumentationRegistry.getInstrumentation().context.packageName, context.packageName,
            "This fixture requires AGP's self-instrumenting KMP library test APK")
        val provider = assertNotNull(context.packageManager.resolveContentProvider(documentsAuthority, 0))
        assertEquals(Process.myUid(), provider.applicationInfo.uid)
        assertTrue(provider.grantUriPermissions)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.readPermission)
        assertEquals("android.permission.MANAGE_DOCUMENTS", provider.writePermission)
        val files = assertNotNull(context.packageManager.resolveContentProvider(filesAuthority, 0))
        assertEquals(Process.myUid(), files.applicationInfo.uid)
        assertFalse(files.exported)
        directory = File(context.cacheDir, DeviceSaveDocumentsProvider.CACHE_DIRECTORY + "/" + UUID.randomUUID())
        assertTrue(directory.mkdirs())
    }

    fun file(name: String, bytes: ByteArray): File = File(directory, name).apply { writeBytes(bytes) }

    fun documentUri(file: File): Uri = DocumentsContract.buildDocumentUri(documentsAuthority, documentId(file))

    fun treeDocumentUri(file: File): Uri = DocumentsContract.buildDocumentUriUsingTree(
        DocumentsContract.buildTreeDocumentUri(documentsAuthority, directory.name), documentId(file),
    )

    fun fileProviderUri(file: File): Uri = FileProvider.getUriForFile(context, filesAuthority, file).also { uri ->
        // Calibrate an actual received FileProvider descriptor, not only the caller's path view.
        checkNotNull(resolver.openFileDescriptor(uri, "r")) { "FileProvider returned no calibration descriptor" }
            .use { DeviceFileIdentity.of(it) }
    }

    fun createDocument(name: String): Pair<File, Uri> {
        val parent = DocumentsContract.buildDocumentUri(documentsAuthority, directory.name)
        val uri = assertNotNull(DocumentsContract.createDocument(resolver, parent, "application/octet-stream", name))
        val file = File(directory, name)
        assertTrue(file.isFile, "The real DocumentsContract call must create the destination")
        assertEquals(documentUri(file), uri)
        return file to uri
    }

    fun stats(uri: Uri): Bundle = assertNotNull(resolver.call(
        Uri.parse("content://$documentsAuthority"), DeviceSaveDocumentsProvider.STATS,
        DocumentsContract.getDocumentId(uri), null,
    ))

    fun assertClosed(uri: Uri, reads: Int, writes: Int) {
        val deadline = SystemClock.elapsedRealtime() + 10_000
        var record = stats(uri)
        while ((record.getInt("readCloses") != reads || record.getInt("writeCloses") != writes) &&
            SystemClock.elapsedRealtime() < deadline) {
            SystemClock.sleep(10)
            record = stats(uri)
        }
        assertNotEquals(Process.myPid(), record.getInt("providerPid"), "exercise actual IPC/native close notifications")
        assertEquals(reads, record.getInt("readOpens"))
        assertEquals(reads, record.getInt("readCloses"))
        assertEquals(writes, record.getInt("writeOpens"))
        assertEquals(writes, record.getInt("writeCloses"))
        assertEquals(0, record.getInt("closeErrors"))
    }

    override fun close() { assertTrue(directory.deleteRecursively()) }

    private fun documentId(file: File): String {
        require(file.parentFile?.canonicalFile == directory.canonicalFile)
        return directory.name + "/" + file.name
    }
}

/** Only a real regular-file reference whose kernel fdinfo and stat inode agree. */
internal data class DeviceFileIdentity private constructor(val device: Long, val inode: Long) {
    companion object {
        fun of(descriptor: ParcelFileDescriptor): DeviceFileIdentity {
            val stat = Os.fstat(descriptor.fileDescriptor)
            check(OsConstants.S_ISREG(stat.st_mode)) { "Only a calibrated regular fixture file is measured" }
            check(stat.st_ino != 0L && readDeviceFdInfoInode(descriptor) == stat.st_ino.toULong()) {
                "Kernel fdinfo and stat inode do not identify the same fixture"
            }
            return DeviceFileIdentity(stat.st_dev, stat.st_ino)
        }
    }
}

/** Strict kernel header parsing: absent, duplicate or malformed ino never means no match. */
internal fun parseDeviceFdInfoInode(lines: Sequence<String>): ULong {
    var inode: ULong? = null
    for (line in lines) {
        if (!line.startsWith("ino:")) continue
        check(inode == null) { "Duplicate kernel fdinfo inode" }
        val value = line.substringAfter(':').trim()
        check(value.isNotEmpty() && value.all { it in '0'..'9' }) { "Invalid kernel fdinfo inode" }
        inode = checkNotNull(value.toULongOrNull()) { "Out-of-range kernel fdinfo inode" }
    }
    return checkNotNull(inode) { "Missing kernel fdinfo inode" }
}

internal fun readDeviceFdInfoInode(descriptor: ParcelFileDescriptor): ULong =
    File("/proc/self/fdinfo/${descriptor.fd}").useLines { parseDeviceFdInfoInode(it) }

/** Actual kernel metadata only; never substitute zero/shadow inode values for device evidence. */
internal fun assertNoDeviceFileDescriptors(file: File) {
    val named = Os.stat(file.path)
    assertNotEquals(0L, named.st_ino)
    val identity = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { DeviceFileIdentity.of(it) }
    check(named.st_dev == identity.device && named.st_ino == identity.inode) { "File identity changed while opening" }
    assertEquals(0, openDeviceFileDescriptorsFor(identity), "Library operation leaked a real descriptor for its owned fixture file")
}

internal fun openDeviceFileDescriptorsFor(identity: DeviceFileIdentity): Int {
    val descriptorNumbers = checkNotNull(File("/proc/self/fd").list()) {
        "Native descriptor inspection unavailable"
    }.map { it.toInt() }
    return descriptorNumbers.count { number ->
        val duplicate = try {
            ParcelFileDescriptor.fromFd(number)
        } catch (failure: IOException) {
            if ((failure.cause as? ErrnoException)?.errno == OsConstants.EBADF) return@count false
            throw failure
        }
        duplicate.use {
            // Different provider mount namespaces are allowed; mnt_id must not exclude aliases.
            if (readDeviceFdInfoInode(it) != identity.inode.toULong()) return@use false
            val stat = Os.fstat(it.fileDescriptor)
            stat.st_dev == identity.device && stat.st_ino == identity.inode
        }
    }
}
