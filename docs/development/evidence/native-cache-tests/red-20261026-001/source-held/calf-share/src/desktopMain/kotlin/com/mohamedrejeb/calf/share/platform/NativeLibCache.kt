package com.mohamedrejeb.calf.share.platform

// Adapted from Calf/nativeCmpkit calf-file-picker's content-addressed extraction design.
import java.io.File
import java.nio.file.*
import java.nio.file.attribute.PosixFilePermission
import java.security.MessageDigest

internal fun shareNativeContentHash(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
    .digest(bytes).joinToString("") { "%02x".format(it) }

/** Immutable full-digest identities prevent versions/architectures/processes replacing each other. */
internal fun extractShareNativeLibrary(bytes: ByteArray, directory: File, libraryName: String): File {
    require(bytes.isNotEmpty()) { "Native library resource is empty" }
    require(libraryName.matches(Regex("[A-Za-z0-9_.-]+"))) { "Invalid native library basename" }
    val cache = directory.toPath().toAbsolutePath().normalize()
    rejectSymlinkPath(cache)
    Files.createDirectories(cache)
    rejectSymlinkPath(cache)
    require(Files.isDirectory(cache, LinkOption.NOFOLLOW_LINKS)) { "Native cache is not a directory" }
    if (Files.getFileStore(cache).supportsFileAttributeView("posix")) {
        Files.setPosixFilePermissions(cache, setOf(PosixFilePermission.OWNER_READ, PosixFilePermission.OWNER_WRITE, PosixFilePermission.OWNER_EXECUTE))
    }
    val hash = shareNativeContentHash(bytes)
    val extension = libraryName.substringAfterLast('.', "")
    val stem = libraryName.substringBeforeLast('.')
    val filename = if (extension.isEmpty()) "$stem-$hash" else "$stem-$hash.$extension"
    val target = cache.resolve(filename)
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
        check(verifiedNativeFile(target, bytes)) { "Native cache entry is not the expected immutable content" }
        return target.toFile()
    }
    val temporary = Files.createTempFile(cache, "calf-share-", ".tmp")
    var keepTemporary = false
    try {
        Files.write(temporary, bytes, StandardOpenOption.TRUNCATE_EXISTING)
        check(verifiedNativeFile(temporary, bytes)) { "Native extraction verification failed" }
        try {
            try { Files.move(temporary, target, StandardCopyOption.ATOMIC_MOVE) }
            catch (_: AtomicMoveNotSupportedException) { Files.move(temporary, target) }
        } catch (failure: Exception) {
            if (verifiedNativeFile(target, bytes)) return target.toFile()
            // A loaded Windows DLL or unsupported atomic move must not cause another version to
            // be overwritten. A verified private unique file is a safe extraction fallback.
            if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) throw failure
            keepTemporary = true
            return temporary.toFile().also { it.deleteOnExit() }
        }
        check(verifiedNativeFile(target, bytes)) { "Native cache content changed during extraction" }
        return target.toFile()
    } finally { if (!keepTemporary) Files.deleteIfExists(temporary) }
}

private fun verifiedNativeFile(path: Path, bytes: ByteArray): Boolean =
    Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) == bytes.size.toLong() &&
        Files.newInputStream(path, LinkOption.NOFOLLOW_LINKS).use { it.readBytes().contentEquals(bytes) }

private fun rejectSymlinkPath(path: Path) {
    var current = path.root
    path.forEach { component ->
        current = current.resolve(component)
        require(!Files.isSymbolicLink(current)) { "Native cache paths must not contain symbolic links" }
    }
}
