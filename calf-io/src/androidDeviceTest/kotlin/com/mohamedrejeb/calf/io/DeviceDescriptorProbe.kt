package com.mohamedrejeb.calf.io

import android.os.ParcelFileDescriptor
import android.system.ErrnoException
import android.system.Os
import android.system.OsConstants
import java.io.File
import java.io.IOException
import kotlin.test.assertNotEquals

/** Only real REG/FIFO references whose kernel fdinfo and stat inode were cross-checked. */
internal data class DeviceDescriptorIdentity private constructor(
    val device: Long,
    val inode: Long,
    val mode: Int,
    val fdInfoInode: Long,
) {
    companion object {
        fun of(file: File): DeviceDescriptorIdentity {
            val named = Os.stat(file.path)
            assertNotEquals(0L, named.st_ino, "The real filesystem must supply an identity for this test")
            return ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { opened ->
                of(opened).also {
                    check(OsConstants.S_ISREG(it.mode)) { "The file reference must be a real regular file" }
                    check(named.st_dev == it.device && named.st_ino == it.inode) { "File identity changed while opening" }
                }
            }
        }

        fun of(descriptor: ParcelFileDescriptor): DeviceDescriptorIdentity {
            val stat = Os.fstat(descriptor.fileDescriptor)
            return verified(stat.st_dev, stat.st_ino, stat.st_mode, readDeviceFdInfoInode(descriptor).toLong())
        }

        fun fromProvider(device: Long, inode: Long, mode: Int, fdInfoInode: Long): DeviceDescriptorIdentity {
            check(OsConstants.S_ISFIFO(mode)) { "The provider must report its actual FIFO descriptor" }
            return verified(device, inode, mode, fdInfoInode)
        }

        private fun verified(device: Long, inode: Long, mode: Int, fdInfoInode: Long): DeviceDescriptorIdentity {
            check(OsConstants.S_ISREG(mode) || OsConstants.S_ISFIFO(mode)) { "Only calibrated files and pipes are measured" }
            check(inode != 0L && fdInfoInode == inode) { "Kernel fdinfo and stat inode do not identify the same fixture" }
            return DeviceDescriptorIdentity(device, inode, mode, fdInfoInode)
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

internal fun openDeviceDescriptorsFor(identity: DeviceDescriptorIdentity): Int {
    // Snapshot before duplicating: never count a probe-owned transient descriptor.
    val descriptorNumbers = checkNotNull(File("/proc/self/fd").list()) {
        "Cannot inspect the test process's real descriptors; lifetime verification is unavailable"
    }.map { it.toInt() }
    return descriptorNumbers.count { number ->
        val duplicate = try {
            ParcelFileDescriptor.fromFd(number)
        } catch (failure: IOException) {
            if ((failure.cause as? ErrnoException)?.errno == OsConstants.EBADF) return@count false
            throw failure
        }
        duplicate.use {
            // mnt_id is not an identity filter: provider mount namespaces may differ.
            if (readDeviceFdInfoInode(it) != identity.inode.toULong()) return@use false
            // Same-inode candidates still need actual device+inode; every error fails closed.
            val stat = Os.fstat(it.fileDescriptor)
            stat.st_dev == identity.device && stat.st_ino == identity.inode
        }
    }
}
