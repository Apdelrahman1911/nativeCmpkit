package com.mohamedrejeb.calf.share.platform

// Adapted from Calf/nativeCmpkit calf-file-picker's content-addressed extraction design.
import java.io.File
import java.nio.file.*
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

internal fun shareNativeContentHash(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256")
    .digest(bytes).joinToString("") { "%02x".format(it) }

/** Immutable full-digest identities prevent versions/architectures/processes replacing each other. */
internal fun extractShareNativeLibrary(bytes: ByteArray, directory: File, libraryName: String): File {
    require(bytes.isNotEmpty()) { "Native library resource is empty" }
    require(libraryName.matches(Regex("[A-Za-z0-9_.-]+")) && libraryName != "." && libraryName != "..") { "Invalid native library basename" }
    val cache = directory.toPath().toAbsolutePath()
    require(cache == cache.normalize()) { "Native cache paths must not contain dot segments" }
    ensurePrivateShareCacheDirectory(cache)
    val hash = shareNativeContentHash(bytes)
    val extension = libraryName.substringAfterLast('.', "")
    val stem = libraryName.substringBeforeLast('.')
    val filename = if (extension.isEmpty()) "$stem-$hash" else "$stem-$hash.$extension"
    val target = cache.resolve(filename)
    if (Files.exists(target, LinkOption.NOFOLLOW_LINKS)) {
        check(verifiedNativeFile(target, bytes)) { "Native cache entry is not the expected immutable content" }
        return target.toFile()
    }
    val temporary = Files.createTempFile(cache, "calf-share-", ".tmp", privateShareCreationAttribute(cache))
    var keepTemporary = false
    try {
        checkShareCacheOwnerAndWrites(temporary)
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

private fun verifiedNativeFile(path: Path, bytes: ByteArray): Boolean {
    if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) return false
    val attributes = Files.readAttributes(path, BasicFileAttributes::class.java, LinkOption.NOFOLLOW_LINKS)
    if (attributes.isSymbolicLink || attributes.isOther) return false
    checkShareCacheOwnerAndWrites(path)
    return Files.size(path) == bytes.size.toLong() &&
        Files.newInputStream(path, LinkOption.NOFOLLOW_LINKS).use { input ->
            input.readNBytes(bytes.size).contentEquals(bytes) && input.read() == -1
        }
}

private val shareProcessFileOwner: UserPrincipal by lazy {
    // Measure the effective filesystem owner; mutable user.name is not identity.
    val probe = Files.createTempFile("nativecmpkit-share-owner-", ".tmp")
    try { Files.getOwner(probe, LinkOption.NOFOLLOW_LINKS) } finally { Files.deleteIfExists(probe) }
}

private fun ensurePrivateShareCacheDirectory(path: Path) {
    var current = path.root
    path.forEach { component ->
        current = current.resolve(component)
        if (!Files.exists(current, LinkOption.NOFOLLOW_LINKS)) {
            try { Files.createDirectory(current, privateShareCreationAttribute(current.parent)) }
            catch (_: FileAlreadyExistsException) { }
        }
        val attributes = Files.readAttributes(current, BasicFileAttributes::class.java, LinkOption.NOFOLLOW_LINKS)
        // NOFOLLOW_LINKS alone does not reject Windows directory junctions.
        require(!attributes.isSymbolicLink && !attributes.isOther && attributes.isDirectory) {
            "Native cache paths must be ordinary directories, not symbolic links or reparse points"
        }
    }
    checkShareCacheOwnerAndWrites(path)
}

private fun checkShareCacheOwnerAndWrites(path: Path) {
    check(Files.getOwner(path, LinkOption.NOFOLLOW_LINKS) == shareProcessFileOwner) { "Native cache belongs to another filesystem owner" }
    if (Files.getFileStore(path).supportsFileAttributeView("posix")) {
        val permissions = Files.getPosixFilePermissions(path, LinkOption.NOFOLLOW_LINKS)
        check(PosixFilePermission.GROUP_WRITE !in permissions && PosixFilePermission.OTHERS_WRITE !in permissions) {
            "Native cache is writable by another user"
        }
    } else {
        val view = checkNotNull(Files.getFileAttributeView(path, AclFileAttributeView::class.java, LinkOption.NOFOLLOW_LINKS)) {
            "Native cache filesystem has no verifiable POSIX permissions or ACL"
        }
        check(view.acl.none { it.type() == AclEntryType.ALLOW && it.principal() != shareProcessFileOwner &&
            it.permissions().any { permission -> permission in SHARE_CACHE_MUTATION_PERMISSIONS } }) {
            "Native cache ACL grants mutation to another principal"
        }
    }
}

private fun privateShareCreationAttribute(parent: Path): FileAttribute<*> =
    if (Files.getFileStore(parent).supportsFileAttributeView("posix")) {
        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rwx------"))
    } else {
        checkNotNull(Files.getFileAttributeView(parent, AclFileAttributeView::class.java, LinkOption.NOFOLLOW_LINKS)) {
            "Native cache filesystem has no verifiable POSIX permissions or ACL"
        }
        object : FileAttribute<List<AclEntry>> {
            override fun name() = "acl:acl"
            override fun value() = listOf(AclEntry.newBuilder().setType(AclEntryType.ALLOW)
                .setPrincipal(shareProcessFileOwner).setPermissions(EnumSet.allOf(AclEntryPermission::class.java))
                .setFlags(AclEntryFlag.FILE_INHERIT, AclEntryFlag.DIRECTORY_INHERIT).build())
        }
    }

private val SHARE_CACHE_MUTATION_PERMISSIONS = setOf(AclEntryPermission.WRITE_DATA, AclEntryPermission.APPEND_DATA,
    AclEntryPermission.DELETE, AclEntryPermission.DELETE_CHILD, AclEntryPermission.WRITE_ATTRIBUTES,
    AclEntryPermission.WRITE_NAMED_ATTRS, AclEntryPermission.WRITE_ACL, AclEntryPermission.WRITE_OWNER)
