package com.mohamedrejeb.calf.picker

import android.system.ErrnoException
import android.system.OsConstants
import android.system.StructStat
import java.io.File
import java.nio.file.AccessDeniedException
import java.nio.file.Files
import java.nio.file.NoSuchFileException
import java.nio.file.Paths
import java.util.concurrent.ConcurrentHashMap
import org.robolectric.annotation.Implementation
import org.robolectric.annotation.Implements
import org.robolectric.annotation.Resetter
import org.robolectric.shadows.ShadowLinux

/**
 * Robolectric 4.16.1's ShadowLinux.stat always returns dev=ino=0. Use the real host
 * filesystem's device/inode instead: invented per-path identities would miss hard links.
 * Other stat fields retain the existing shadow's semantics. This is a disclosed
 * Unix-host adapter, not Android kernel/device verification, and fails on non-Unix hosts.
 */
@Implements(className = "libcore.io.Linux", isInAndroidSdk = false, minSdk = 26)
class HostFileStatShadow : ShadowLinux() {
    @Implementation
    override fun stat(path: String?): StructStat {
        // The inherited fstat fallback calls stat(null), without a path whose identity we can read.
        if (path == null) return super.stat(null)
        failingStatPaths[normalizedStatPath(path)]?.let { errno ->
            throw ErrnoException("stat", errno)
        }
        val identity = try {
            Files.readAttributes(Paths.get(path), "unix:dev,ino")
        } catch (missing: NoSuchFileException) {
            throw ErrnoException("stat", OsConstants.ENOENT, missing)
        } catch (denied: AccessDeniedException) {
            throw ErrnoException("stat", OsConstants.EACCES, denied)
        }
        if (normalizedStatPath(path) in inconclusiveStatPaths) {
            return super.stat(path).withIdentity(device = 0, inode = 0)
        }
        return super.stat(path).withIdentity(
            device = (identity.getValue("dev") as Number).toLong(),
            inode = (identity.getValue("ino") as Number).toLong(),
        )
    }

    companion object {
        @JvmStatic
        @Resetter
        fun reset() {
            inconclusiveStatPaths.clear()
            failingStatPaths.clear()
        }
    }
}

private val inconclusiveStatPaths = ConcurrentHashMap.newKeySet<String>()
private val failingStatPaths = ConcurrentHashMap<String, Int>()
private fun normalizedStatPath(path: String): String = Paths.get(path).toAbsolutePath().normalize().toString()

/**
 * Explicit zero-identity injection for these fixture files only, restored even on failure.
 * Keep ONE shadow class: Robolectric can retain libcore's Linux singleton across Config changes;
 * switching sibling shadow types caused a ClassCastException before the refusal test executed.
 * This is not evidence that a real Android filesystem reports inode zero.
 */
internal suspend fun <T> withInconclusiveFileIdentities(files: List<File>, block: suspend () -> T): T {
    val paths = files.map { normalizedStatPath(it.path) }.toSet()
    check(paths.none { it in inconclusiveStatPaths }) { "Inconclusive identity fixture already active" }
    inconclusiveStatPaths.addAll(paths)
    try {
        return block()
    } finally {
        inconclusiveStatPaths.removeAll(paths)
    }
}

/** Exact destination-only errno injection, not an Android kernel/ACL assertion. */
internal suspend fun <T> withFailingFileStat(file: File, errno: Int, block: suspend () -> T): T {
    require(errno in setOf(OsConstants.EACCES, OsConstants.EIO, OsConstants.EPERM))
    val path = normalizedStatPath(file.path)
    check(path !in inconclusiveStatPaths)
    check(failingStatPaths.putIfAbsent(path, errno) == null) { "Stat failure fixture already active" }
    try {
        return block()
    } finally {
        check(failingStatPaths.remove(path, errno)) { "Stat failure fixture ownership changed" }
    }
}

private fun StructStat.withIdentity(device: Long, inode: Long): StructStat = StructStat(
    device, inode, st_mode, st_nlink, st_uid, st_gid, st_rdev, st_size,
    st_atime, st_mtime, st_ctime, st_blksize, st_blocks,
)
