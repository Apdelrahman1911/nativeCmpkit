// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.attribute.PosixFilePermission
import java.nio.file.attribute.PosixFilePermissions
import java.nio.file.attribute.UserPrincipal
import java.security.MessageDigest

private const val HASH_ALGORITHM = "SHA-256"
private const val HASH_LENGTH = 16
private const val TEMP_PREFIX = "calf-native-"
private const val TEMP_SUFFIX = ".tmp"

/**
 * Short, stable fingerprint of a native library's bytes.
 *
 * Used to name the cached copy so that different builds of the library
 * never share a file on disk.
 */
internal fun nativeLibraryContentHash(bytes: ByteArray): String =
    MessageDigest.getInstance(HASH_ALGORITHM)
        .digest(bytes)
        .joinToString("") { "%02x".format(it) }
        .take(HASH_LENGTH)

/**
 * Inserts [contentHash] before the extension of [libFileName],
 * e.g. `calf_filepicker_native.dll` -> `calf_filepicker_native-<hash>.dll`.
 */
internal fun nativeLibraryCacheFileName(libFileName: String, contentHash: String): String {
    val extension = libFileName.substringAfterLast('.', missingDelimiterValue = "")
    val baseName = libFileName.substringBeforeLast('.')
    return if (extension.isEmpty()) "$baseName-$contentHash" else "$baseName-$contentHash.$extension"
}

/**
 * Makes [bytes] available as a file inside [cacheDir] and returns the file to load.
 *
 * - An existing target with identical content is reused untouched, so a library
 *   that another process has already loaded (and locked, on Windows) is never
 *   replaced.
 * - Otherwise the bytes are written to a temp file and moved over the target.
 * - If the move fails for any reason, the unique temp file itself is returned
 *   and scheduled for deletion on exit, so loading still succeeds.
 */
internal fun extractNativeLibrary(bytes: ByteArray, cacheDir: File, fileName: String): File {
    require(File(fileName).name == fileName && fileName != "." && fileName != "..") { "Expected a native library file name, not a path" }
    ensurePrivateDirectory(cacheDir.toPath())
    val target = File(cacheDir, fileName)
    check(!Files.isSymbolicLink(target.toPath())) { "Refusing a symbolic-link native cache entry" }
    if (hasIdenticalContent(target, bytes)) return target

    val tempFile = Files.createTempFile(cacheDir.toPath(), TEMP_PREFIX, TEMP_SUFFIX)
    Files.write(tempFile, bytes)

    return runCatching { moveReplacing(tempFile, target.toPath()) }
        .map { target }
        .getOrElse { tempFile.toFile().also { it.deleteOnExit() } }
}

private fun hasIdenticalContent(file: File, bytes: ByteArray): Boolean =
    Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) &&
        file.length() == bytes.size.toLong() &&
        file.readBytes().contentEquals(bytes)

private fun moveReplacing(source: Path, target: Path) {
    try {
        Files.move(source, target, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
    } catch (_: AtomicMoveNotSupportedException) {
        // ATOMIC_MOVE is not supported on every filesystem; retry with a plain replace.
        Files.move(source, target, StandardCopyOption.REPLACE_EXISTING)
    }
}

/** Home is optional, but a shared predictable tmp/.cache path is never a fallback. */
internal fun nativeCacheDirectory(home: String? = System.getProperty("user.home")): File {
    if (!home.isNullOrBlank()) {
        try {
            val homePath = File(home).toPath().toAbsolutePath().normalize()
            ensurePrivateDirectory(homePath, create = false)
            val parent = homePath.resolve(".cache")
            ensurePrivateDirectory(parent)
            val cache = parent.resolve("nativecmpkit-filepicker")
            ensurePrivateDirectory(cache)
            return cache.toFile()
        } catch (_: Exception) {
            // Read-only, symlinked or incorrectly owned home: use a fresh private directory.
        }
    }
    // Resolve OS-managed aliases (notably macOS /var -> /private/var) only after creating a
    // randomized directory; subsequent validation/load use this stable real path.
    val directory = Files.createTempDirectory("nativecmpkit-filepicker-").toRealPath()
    setOwnerOnlyPermissions(directory)
    ensurePrivateDirectory(directory)
    return directory.toFile().also { it.deleteOnExit() }
}

private val processFileOwner: UserPrincipal by lazy {
    // A file created by this process identifies the effective filesystem user without trusting
    // the mutable user.name/user.home properties. This probe never contains library/user data.
    val probe = Files.createTempFile("nativecmpkit-owner-", ".tmp")
    try { Files.getOwner(probe, NOFOLLOW_LINKS) } finally { Files.deleteIfExists(probe) }
}

internal fun ensurePrivateDirectory(directory: Path, create: Boolean = true) {
    val absolute = directory.toAbsolutePath().normalize()
    var current = absolute.root
    for (part in absolute) {
        current = current.resolve(part)
        check(!Files.isSymbolicLink(current)) { "Refusing a symbolic-link native cache directory" }
        if (!Files.exists(current, NOFOLLOW_LINKS)) {
            check(create) { "Native cache directory does not exist" }
            try {
                if (Files.getFileStore(current.parent).supportsFileAttributeView("posix")) {
                    Files.createDirectory(current, PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rwx------")))
                } else Files.createDirectory(current)
            } catch (_: java.nio.file.FileAlreadyExistsException) { }
            check(!Files.isSymbolicLink(current)) { "Native cache directory changed during creation" }
        }
    }
    check(Files.isDirectory(absolute, NOFOLLOW_LINKS)) { "Native cache location is not a directory" }
    check(Files.getOwner(absolute, NOFOLLOW_LINKS) == processFileOwner) { "Native cache directory belongs to another user" }
    if (Files.getFileStore(absolute).supportsFileAttributeView("posix")) {
        val permissions = Files.getPosixFilePermissions(absolute, NOFOLLOW_LINKS)
        check(PosixFilePermission.GROUP_WRITE !in permissions && PosixFilePermission.OTHERS_WRITE !in permissions) {
            "Native cache directory is writable by another user"
        }
    }
}

private fun setOwnerOnlyPermissions(path: Path) {
    if (Files.getFileStore(path).supportsFileAttributeView("posix")) {
        Files.setPosixFilePermissions(path, PosixFilePermissions.fromString("rwx------"))
    }
}
