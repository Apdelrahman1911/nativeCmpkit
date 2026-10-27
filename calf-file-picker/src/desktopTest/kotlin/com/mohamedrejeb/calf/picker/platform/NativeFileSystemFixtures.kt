package com.mohamedrejeb.calf.picker.platform

import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.attribute.*
import java.util.EnumSet
import java.util.concurrent.TimeUnit
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Actual host filesystem fixtures. Unsupported security operations fail, never skip. */
internal fun privateCacheTestDirectory(prefix: String, parent: Path? = null): Path {
    val directory = (if (parent == null) Files.createTempDirectory(prefix)
        else Files.createTempDirectory(parent, prefix)).toRealPath()
    if (Files.getFileStore(directory).supportsFileAttributeView("posix")) {
        Files.setPosixFilePermissions(directory, PosixFilePermissions.fromString("rwx------"))
    } else {
        val view = requireNotNull(Files.getFileAttributeView(directory, AclFileAttributeView::class.java, NOFOLLOW_LINKS))
        view.acl = listOf(AclEntry.newBuilder().setType(AclEntryType.ALLOW).setPrincipal(view.owner)
            .setPermissions(EnumSet.allOf(AclEntryPermission::class.java))
            .setFlags(AclEntryFlag.FILE_INHERIT, AclEntryFlag.DIRECTORY_INHERIT).build())
    }
    assertPrivateCacheTestDirectory(directory)
    return directory
}

internal fun assertPrivateCacheTestDirectory(directory: Path) {
    if (Files.getFileStore(directory).supportsFileAttributeView("posix")) {
        assertEquals(PosixFilePermissions.fromString("rwx------"), Files.getPosixFilePermissions(directory, NOFOLLOW_LINKS))
    } else {
        val view = requireNotNull(Files.getFileAttributeView(directory, AclFileAttributeView::class.java, NOFOLLOW_LINKS))
        assertTrue(view.acl.any { it.type() == AclEntryType.ALLOW && it.principal() == view.owner })
        assertFalse(view.acl.any { it.type() == AclEntryType.ALLOW && it.principal() != view.owner &&
            it.permissions().any { permission -> permission in CACHE_MUTATION_PERMISSIONS } })
    }
}

internal fun grantForeignCacheWrites(directory: Path) {
    if (Files.getFileStore(directory).supportsFileAttributeView("posix")) {
        Files.setPosixFilePermissions(directory, PosixFilePermissions.fromString("rwxrwxrwx"))
    } else {
        val view = requireNotNull(Files.getFileAttributeView(directory, AclFileAttributeView::class.java, NOFOLLOW_LINKS))
        // Translate the invariant well-known SID; do not assume the host uses English group names.
        val account = runOwnedWindowsCommand("powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
            "[Console]::OutputEncoding = [Text.UTF8Encoding]::new(\$false); ([System.Security.Principal.SecurityIdentifier]'S-1-1-0').Translate([System.Security.Principal.NTAccount]).Value").trim()
        require(account.isNotEmpty() && account.length < 256 && '\n' !in account && '\r' !in account)
        val everyone = directory.fileSystem.userPrincipalLookupService.lookupPrincipalByGroupName(account)
        view.acl = view.acl + AclEntry.newBuilder().setType(AclEntryType.ALLOW).setPrincipal(everyone)
            .setPermissions(CACHE_MUTATION_PERMISSIONS).build()
        assertTrue(view.acl.any { it.type() == AclEntryType.ALLOW && it.principal() == everyone &&
            it.permissions().containsAll(CACHE_MUTATION_PERMISSIONS) }, "Foreign-write fixture was not established")
    }
}

internal fun cacheTestSecuritySnapshot(path: Path): Any =
    if (Files.getFileStore(path).supportsFileAttributeView("posix")) {
        Files.getPosixFilePermissions(path, NOFOLLOW_LINKS)
    } else {
        requireNotNull(Files.getFileAttributeView(path, AclFileAttributeView::class.java, NOFOLLOW_LINKS)).acl
    }

internal fun createCacheDirectoryAlias(alias: Path, target: Path) {
    if (System.getProperty("os.name").startsWith("Windows")) {
        runOwnedWindowsCommand("cmd.exe", "/d", "/c", "mklink", "/J", alias.toString(), target.toString())
        val attributes = Files.readAttributes(alias, BasicFileAttributes::class.java, NOFOLLOW_LINKS)
        assertTrue(attributes.isOther, "Expected an actual Windows junction/reparse point")
        assertFalse(attributes.isSymbolicLink, "A junction must exercise the distinct non-symlink reparse contract")
    } else {
        Files.createSymbolicLink(alias, target)
        assertTrue(Files.isSymbolicLink(alias))
    }
}

private fun runOwnedWindowsCommand(binary: String, vararg arguments: String): String {
    val system = requireNotNull(System.getenv("SystemRoot"))
    val executable = if (binary == "powershell.exe") Path.of(system, "System32", "WindowsPowerShell", "v1.0", binary)
        else Path.of(system, "System32", binary)
    val process = ProcessBuilder(listOf(executable.toString()) + arguments).redirectErrorStream(true).start()
    try {
        assertTrue(process.waitFor(15, TimeUnit.SECONDS), "Owned Windows filesystem fixture timed out")
        val output = process.inputStream.use { it.readNBytes(4096).toString(Charsets.UTF_8) }
        assertEquals(0, process.exitValue(), "Windows security fixture failed: $output")
        return output
    } finally {
        if (process.isAlive) { process.destroyForcibly(); process.waitFor(5, TimeUnit.SECONDS) }
    }
}

private val CACHE_MUTATION_PERMISSIONS = setOf(AclEntryPermission.WRITE_DATA, AclEntryPermission.APPEND_DATA,
    AclEntryPermission.DELETE, AclEntryPermission.DELETE_CHILD, AclEntryPermission.WRITE_ATTRIBUTES,
    AclEntryPermission.WRITE_NAMED_ATTRS, AclEntryPermission.WRITE_ACL, AclEntryPermission.WRITE_OWNER)
