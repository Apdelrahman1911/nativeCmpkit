// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
// Further modified (2026-10-27): verified owner/ACL, reparse and extraction lifecycle contracts.
package com.mohamedrejeb.calf.picker.platform

import java.io.File
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.attribute.AclEntry
import java.nio.file.attribute.AclEntryFlag
import java.nio.file.attribute.AclEntryPermission
import java.nio.file.attribute.AclEntryType
import java.nio.file.attribute.AclFileAttributeView
import java.nio.file.attribute.BasicFileAttributes
import java.nio.file.attribute.FileAttribute
import java.nio.file.attribute.PosixFilePermission
import java.nio.file.attribute.PosixFilePermissions
import java.nio.file.attribute.UserPrincipal
import java.security.MessageDigest
import java.util.EnumSet

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
 * - Complete private staging is published with an atomic, no-replace hard link.
 *   A late writer cannot replace a path already returned to a native loader.
 * - A different existing payload is never overwritten. If publication is not
 *   supported, the verified unique staging file is returned and deleted on exit.
 */
internal fun extractNativeLibrary(bytes: ByteArray, cacheDir: File, fileName: String): File =
    extractNativeLibrary(bytes, cacheDir, fileName, FileSystemNativeCachePublication)

internal fun interface NativeCachePublication {
    fun publish(complete: Path, target: Path)
}

internal object FileSystemNativeCachePublication : NativeCachePublication {
    override fun publish(complete: Path, target: Path) {
        // ATOMIC_MOVE may replace an existing target even without REPLACE_EXISTING.
        // A link inserts one complete inode and fails if another process won.
        Files.createLink(target, complete)
    }
}

internal fun extractNativeLibrary(
    bytes: ByteArray,
    cacheDir: File,
    fileName: String,
    publication: NativeCachePublication,
): File {
    require(bytes.isNotEmpty()) { "Native library resource is empty" }
    require(File(fileName).name == fileName && fileName != "." && fileName != "..") { "Expected a native library file name, not a path" }
    val cache = cacheDir.toPath().toAbsolutePath()
    require(cache == cache.normalize()) { "Native cache paths must not contain dot segments" }
    ensurePrivateDirectory(cache)
    val target = cache.resolve(fileName).toFile()
    if (Files.exists(target.toPath(), NOFOLLOW_LINKS)) {
        checkOrdinaryCachePath(target.toPath())
        checkPrivateCacheOwnerAndWrites(target.toPath())
    }
    if (hasIdenticalContent(target, bytes)) return target

    val tempFile = Files.createTempFile(cache, TEMP_PREFIX, TEMP_SUFFIX, privateCacheCreationAttribute(cache))
    var keepTemporary = false
    try {
        checkPrivateCacheOwnerAndWrites(tempFile)
        Files.write(tempFile, bytes)
        check(hasIdenticalContent(tempFile.toFile(), bytes)) { "Native staging is not complete content" }

        try {
            publication.publish(tempFile, target.toPath())
        } catch (_: IOException) {
            // A competing publisher may already have returned/loaded this path.
            // Verify that winner, but never replace it (including different bytes).
            if (Files.exists(target.toPath(), NOFOLLOW_LINKS)) {
                checkOrdinaryCachePath(target.toPath())
                checkPrivateCacheOwnerAndWrites(target.toPath())
                if (hasIdenticalContent(target, bytes)) return target
            }
            check(hasIdenticalContent(tempFile.toFile(), bytes)) { "Native fallback is not complete content" }
            checkPrivateCacheOwnerAndWrites(tempFile)
            keepTemporary = true
            return tempFile.toFile().also { it.deleteOnExit() }
        } catch (_: UnsupportedOperationException) {
            // A filesystem without hard links can still load its own complete,
            // private unique file; never fall back to a potentially replacing move.
            check(hasIdenticalContent(tempFile.toFile(), bytes)) { "Native fallback is not complete content" }
            checkPrivateCacheOwnerAndWrites(tempFile)
            keepTemporary = true
            return tempFile.toFile().also { it.deleteOnExit() }
        }
        checkOrdinaryCachePath(target.toPath())
        checkPrivateCacheOwnerAndWrites(target.toPath())
        check(hasIdenticalContent(target, bytes)) { "Native cache content changed during extraction" }
        return target
    } finally {
        // Permission/write failures must not leak partially extracted executables.
        if (!keepTemporary) Files.deleteIfExists(tempFile)
    }
}

private fun hasIdenticalContent(file: File, bytes: ByteArray): Boolean =
    Files.isRegularFile(file.toPath(), NOFOLLOW_LINKS) &&
        file.length() == bytes.size.toLong() &&
        Files.newInputStream(file.toPath(), NOFOLLOW_LINKS).use { input ->
            input.readNBytes(bytes.size).contentEquals(bytes) && input.read() == -1
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
        var created = false
        if (!Files.exists(current, NOFOLLOW_LINKS)) {
            check(create) { "Native cache directory does not exist" }
            try {
                Files.createDirectory(current, privateCacheCreationAttribute(current.parent))
                created = true
            } catch (_: java.nio.file.FileAlreadyExistsException) { }
        }
        checkOrdinaryCachePath(current)
        check(Files.isDirectory(current, NOFOLLOW_LINKS)) { "Native cache ancestor is not a directory" }
        if (created) setOwnerOnlyPermissions(current)
    }
    check(Files.isDirectory(absolute, NOFOLLOW_LINKS)) { "Native cache location is not a directory" }
    checkPrivateCacheOwnerAndWrites(absolute)
}

private fun checkOrdinaryCachePath(path: Path) {
    val attributes = Files.readAttributes(path, BasicFileAttributes::class.java, NOFOLLOW_LINKS)
    // Windows junctions are isOther=true AND isDirectory=true, not symlinks.
    check(!attributes.isSymbolicLink && !attributes.isOther) { "Refusing a symbolic-link or reparse native cache path" }
}

private fun checkPrivateCacheOwnerAndWrites(path: Path) {
    check(Files.getOwner(path, NOFOLLOW_LINKS) == processFileOwner) { "Native cache belongs to another filesystem owner" }
    if (Files.getFileStore(path).supportsFileAttributeView("posix")) {
        val permissions = Files.getPosixFilePermissions(path, NOFOLLOW_LINKS)
        check(PosixFilePermission.GROUP_WRITE !in permissions && PosixFilePermission.OTHERS_WRITE !in permissions) {
            "Native cache is writable by another user"
        }
    } else {
        val view = checkNotNull(Files.getFileAttributeView(path, AclFileAttributeView::class.java, NOFOLLOW_LINKS)) {
            "Native cache filesystem has no verifiable POSIX permissions or ACL"
        }
        // Conservative: do not infer effective-access safety by reordering ALLOW/DENY
        // ACEs, or ignore inherited grants to future native files (INHERIT_ONLY).
        check(view.acl.none { it.type() == AclEntryType.ALLOW && it.principal() != processFileOwner &&
            it.permissions().any { permission -> permission in CACHE_MUTATION_PERMISSIONS } }) {
            "Native cache ACL grants mutation to another principal"
        }
    }
}

private fun setOwnerOnlyPermissions(path: Path) {
    checkOrdinaryCachePath(path)
    check(Files.getOwner(path, NOFOLLOW_LINKS) == processFileOwner) { "New native cache belongs to another filesystem owner" }
    if (Files.getFileStore(path).supportsFileAttributeView("posix")) {
        Files.setPosixFilePermissions(path, PosixFilePermissions.fromString("rwx------"))
    } else {
        checkNotNull(Files.getFileAttributeView(path, AclFileAttributeView::class.java, NOFOLLOW_LINKS)).acl = privateCacheAcl()
    }
    // Used ONLY on just-created, verified-owned directories, never to repair an
    // already untrusted cache. Java's ACL setter does not certify inheritance.
    checkPrivateCacheOwnerAndWrites(path)
}

private fun privateCacheCreationAttribute(parent: Path): FileAttribute<*> =
    if (Files.getFileStore(parent).supportsFileAttributeView("posix")) {
        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rwx------"))
    } else {
        checkNotNull(Files.getFileAttributeView(parent, AclFileAttributeView::class.java, NOFOLLOW_LINKS)) {
            "Native cache filesystem has no verifiable POSIX permissions or ACL"
        }
        object : FileAttribute<List<AclEntry>> {
            override fun name() = "acl:acl"
            override fun value() = privateCacheAcl()
        }
    }

private fun privateCacheAcl(): List<AclEntry> = listOf(AclEntry.newBuilder()
    .setType(AclEntryType.ALLOW).setPrincipal(processFileOwner)
    .setPermissions(EnumSet.allOf(AclEntryPermission::class.java))
    .setFlags(AclEntryFlag.FILE_INHERIT, AclEntryFlag.DIRECTORY_INHERIT).build())

private val CACHE_MUTATION_PERMISSIONS = setOf(AclEntryPermission.WRITE_DATA, AclEntryPermission.APPEND_DATA,
    AclEntryPermission.DELETE, AclEntryPermission.DELETE_CHILD, AclEntryPermission.WRITE_ATTRIBUTES,
    AclEntryPermission.WRITE_NAMED_ATTRS, AclEntryPermission.WRITE_ACL, AclEntryPermission.WRITE_OWNER)
