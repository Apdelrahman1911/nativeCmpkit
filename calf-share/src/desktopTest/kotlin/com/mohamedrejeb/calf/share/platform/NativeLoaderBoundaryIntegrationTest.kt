// NativeCmpKit test-only, actual separate-JVM loader boundaries (2026-10-28).
package com.mohamedrejeb.calf.share.platform

import java.io.File
import java.io.InputStream
import java.net.URLClassLoader
import java.nio.file.AccessDeniedException
import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.attribute.AclEntry
import java.nio.file.attribute.AclEntryFlag
import java.nio.file.attribute.AclEntryPermission
import java.nio.file.attribute.AclEntryType
import java.nio.file.attribute.AclFileAttributeView
import java.nio.file.attribute.PosixFilePermissions
import java.nio.file.attribute.FileAttribute
import java.util.EnumSet
import java.util.concurrent.TimeUnit
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** No dialogs or fake JNI. Missing resources are hidden by an isolated resource loader only. */
class NativeLoaderBoundaryIntegrationTest {
    @Test fun missingBundledResourceFailsVisiblyWithoutPublishingOrRetryingANativeImage() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        runBoundary(root, "missing-resource", home)
        assertFalse(Files.exists(home.resolve(".cache")))
    }

    @Test fun explicitExternalPackagerPathLoadsTheRealHostLibraryWithoutTouchingTheHomeCache() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val external = privateCacheTestDirectory("external-", root)
        val native = external.resolve(System.mapLibraryName("calf_share_native"))
        val bytes = boundaryHostPayload()
        Files.write(native, bytes)
        runBoundary(root, "trusted-external", home, external)
        assertFalse(Files.exists(home.resolve(".cache")), "A bundled fallback must not masquerade as external loading")
        assertContentEquals(bytes, Files.readAllBytes(native))
    }

    @Test fun homePermissionPolicyFollowsActualPrivateDirectoryCreationRatherThanTheWritableHint() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val restore = makeBoundaryHomeReadOnly(home)
        try {
            // Root may bypass POSIX modes. Require a real permission boundary,
            // never pretend chmod alone proves the native loader cannot write.
            assertFalse(Files.isWritable(home), "This test requires an actual non-bypassing host; Windows CI covers its ACL")
            // An NTFS parent ACL can deny ordinary file creation yet permit
            // creation with the explicit owner ACL used by the loader. That
            // is not a read-only filesystem. Measure the exact operation and
            // require either genuine native success or genuine denial to match.
            // The strict "read-only" entrypoint below still requires BOTH OS
            // denials and no successful native initialization; it is exercised
            // separately on a non-bypassing Linux host.
            runBoundary(root, "home-permissions", home)
        } finally { restore() }
    }

    @Test fun failedCacheDirectoryCreationCannotOverwriteAnExistingOrdinaryFile() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val blocker = home.resolve(".cache")
        Files.writeString(blocker, "preserve-not-a-directory")
        runBoundary(root, "blocked-directory", home)
        assertEquals("preserve-not-a-directory", Files.readString(blocker))
    }

    @Test fun redirectedHomeCacheCannotWriteOrLoadThroughTheActualDirectoryAlias() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val external = privateCacheTestDirectory("redirect-target-", root)
        val sentinel = external.resolve("sentinel")
        Files.writeString(sentinel, "preserve-external-data")
        createCacheDirectoryAlias(home.resolve(".cache"), external)
        runBoundary(root, "redirected-cache", home)
        assertEquals("preserve-external-data", Files.readString(sentinel))
        assertEquals(1L, Files.list(external).use { it.count() })
    }

    private fun withRoot(block: (Path) -> Unit) {
        val root = privateCacheTestDirectory("nativecmpkit-loader-boundary-", Path.of(System.getProperty("user.home")).toRealPath())
        var passed = false
        try { block(root); passed = true } finally {
            if (passed) Files.walk(root).use { entries -> entries.sorted(Comparator.reverseOrder()).forEach(Files::deleteIfExists) }
            else println("NATIVECMPKIT_LOADER_BOUNDARY_FAILURE retained=$root")
        }
    }
}

/** JVM entrypoint; the custom loader has no parent containing production/test classes. */
internal object NativeLoaderBoundaryEntrypoint {
    @JvmStatic fun main(args: Array<String>) {
        check(args.size == 1 && args[0] in setOf("missing-resource", "trusted-external", "read-only", "home-permissions", "blocked-directory", "redirected-cache"))
        val mode = args[0]
        val result = if (mode == "missing-resource") {
            // Unlike Gradle's worker launcher, this Java process was launched
            // with the actual full classpath in its own argument file.
            val urls = System.getProperty("java.class.path").split(File.pathSeparatorChar)
                .map { Path.of(it).toUri().toURL() }.toTypedArray()
            object : URLClassLoader(urls, ClassLoader.getPlatformClassLoader()) {
                override fun getResourceAsStream(name: String): InputStream? =
                    if (name.startsWith("native/")) null else super.getResourceAsStream(name)
            }.use { loader ->
                val work = Class.forName(NativeLoaderBoundaryWork::class.java.name, true, loader)
                check(work.classLoader === loader)
                work.getMethod("run", String::class.java).invoke(null, mode) as String
            }
        } else NativeLoaderBoundaryWork.run(mode)
        if (mode == "home-permissions") check(result in setOf("$mode denied", "$mode permitted"))
        else check(result == mode)
        println("NATIVECMPKIT_LOADER_BOUNDARY $result verified")
    }
}

internal object NativeLoaderBoundaryWork {
    @JvmStatic fun run(mode: String): String {
        val home = Path.of(System.getProperty("user.home")).toRealPath()
        if (mode == "trusted-external") {
            check(NativeShareBridge.abiVersion() == 1)
            NativeShareBridge.init()
            check(NativeShareBridge.activeRequestCount() == 0)
            check(NativeShareBridge.liveUiOperationCount() == 0)
            check(!Files.exists(home.resolve(".cache")))
            return mode
        }
        if (mode == "read-only" || mode == "home-permissions") {
            check(!Files.isWritable(home))
            try {
                Files.createFile(home.resolve("permission-precondition"))
                error("The host bypasses the claimed read-only boundary")
            } catch (_: AccessDeniedException) { /* Real OS denial, not a fabricated exception. */ }
            // Windows checks plain-file writes and explicitly attributed
            // directory creation differently. Establish the actual operation
            // used by the owning loader, not only Files.isWritable/chmod.
            val attributes: FileAttribute<*> = if (Files.getFileStore(home).supportsFileAttributeView("posix")) {
                PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rwx------"))
            } else {
                val owner = Files.getOwner(home, NOFOLLOW_LINKS)
                object : FileAttribute<List<AclEntry>> {
                    override fun name() = "acl:acl"
                    override fun value() = listOf(AclEntry.newBuilder().setType(AclEntryType.ALLOW).setPrincipal(owner)
                        .setPermissions(EnumSet.allOf(AclEntryPermission::class.java))
                        .setFlags(AclEntryFlag.FILE_INHERIT, AclEntryFlag.DIRECTORY_INHERIT).build())
                }
            }
            val precondition = home.resolve("directory-permission-precondition")
            val directoryCreationPermitted = try {
                Files.createDirectory(precondition, attributes)
                true
            } catch (_: AccessDeniedException) {
                check(!Files.exists(precondition))
                false
            }
            if (directoryCreationPermitted) Files.delete(precondition)
            if (mode == "read-only") check(!directoryCreationPermitted) {
                "The host permits the exact private-directory creation claimed to be read-only"
            }
            if (directoryCreationPermitted) {
                // Only an independently established real OS grant can reach
                // this branch. Never use a native init exception as permission
                // detection or turn a missing/failed native payload into success.
                check(NativeShareBridge.abiVersion() == 1)
                NativeShareBridge.init()
                check(NativeShareBridge.activeRequestCount() == 0)
                check(NativeShareBridge.liveUiOperationCount() == 0)
                val payload = boundaryHostPayload()
                val library = System.mapLibraryName("calf_share_native")
                val digestName = library.substringBeforeLast('.') + "-" + shareNativeContentHash(payload) +
                    "." + library.substringAfterLast('.')
                val cache = home.resolve(".cache/calf-share")
                val entries = Files.list(cache).use { it.toList() }
                check(entries == listOf(cache.resolve(digestName)))
                check(Files.readAllBytes(entries.single()).contentEquals(payload))
                return "$mode permitted"
            }
        } else if (mode == "missing-resource") {
            check(NativeLoaderBoundaryWork::class.java.classLoader.getResourceAsStream(boundaryResourcePath()) == null)
        } else check(mode == "blocked-directory" || mode == "redirected-cache")
        try {
            NativeShareBridge.init()
            error("A missing resource/read-only cache must not initialize native code successfully")
        } catch (failure: ExceptionInInitializerError) {
            val cause = checkNotNull(failure.cause)
            when (mode) {
                "read-only", "home-permissions" -> check(cause is AccessDeniedException)
                "missing-resource" -> check(cause is IllegalStateException && cause.message.orEmpty().startsWith("Native library not found in JAR resources at 'native/"))
                else -> check(cause is IllegalArgumentException && cause.message.orEmpty().startsWith("Native cache paths must be ordinary directories"))
            }
        }
        // Failed initialization cannot be reported as success on a subsequent request.
        try {
            NativeShareBridge.init()
            error("A failed native initialization must stay failed")
        } catch (_: NoClassDefFoundError) { }
        if (mode in setOf("missing-resource", "read-only", "home-permissions")) check(!Files.exists(home.resolve(".cache")))
        return if (mode == "home-permissions") "$mode denied" else mode
    }
}

private fun boundaryResourcePath(): String {
    val os = System.getProperty("os.name").lowercase().let {
        when { "mac" in it || "darwin" in it -> "macos"; "win" in it -> "windows";
            "nux" in it || "nix" in it -> "linux"; else -> error("Unsupported native test OS") }
    }
    val arch = when (System.getProperty("os.arch").lowercase()) {
        "amd64", "x86_64" -> "x64"; "arm64", "aarch64" -> "arm64"; else -> error("Unsupported native test architecture")
    }
    return "native/$os-$arch/${System.mapLibraryName("calf_share_native")}"
}

private fun boundaryHostPayload(): ByteArray = checkNotNull(
    NativeLoaderBoundaryEntrypoint::class.java.classLoader.getResourceAsStream(boundaryResourcePath())
) { "Actual host resource is required; never substitute or skip a native payload" }.use { it.readBytes() }

private fun makeBoundaryHomeReadOnly(home: Path): () -> Unit =
    if (Files.getFileStore(home).supportsFileAttributeView("posix")) {
        val before = Files.getPosixFilePermissions(home, NOFOLLOW_LINKS)
        Files.setPosixFilePermissions(home, PosixFilePermissions.fromString("r-x------"))
        val restore: () -> Unit = { Files.setPosixFilePermissions(home, before); Unit }
        restore
    } else {
        val view = checkNotNull(Files.getFileAttributeView(home, AclFileAttributeView::class.java, NOFOLLOW_LINKS))
        val before = view.acl
        view.acl = listOf(
            // Deny actual ADD_FILE/ADD_SUBDIRECTORY/mutation on this parent.
            // A reduced generic WRITE mask/readback alone did not establish
            // denial of explicitly ACL-attributed child directories on Windows.
            AclEntry.newBuilder().setType(AclEntryType.DENY).setPrincipal(view.owner)
                .setPermissions(AclEntryPermission.WRITE_DATA, AclEntryPermission.APPEND_DATA,
                    AclEntryPermission.DELETE_CHILD, AclEntryPermission.WRITE_NAMED_ATTRS,
                    AclEntryPermission.WRITE_ATTRIBUTES).build(),
            AclEntry.newBuilder().setType(AclEntryType.ALLOW).setPrincipal(view.owner)
            .setPermissions(AclEntryPermission.READ_DATA, AclEntryPermission.READ_NAMED_ATTRS,
                AclEntryPermission.EXECUTE, AclEntryPermission.READ_ATTRIBUTES,
                AclEntryPermission.READ_ACL, AclEntryPermission.SYNCHRONIZE).build())
        val restore: () -> Unit = { view.acl = before }
        restore
    }

private fun runBoundary(root: Path, mode: String, home: Path,
    external: Path = privateCacheTestDirectory("empty-system-path-", root)) {
    val classpath = checkNotNull(System.getProperty("nativecmpkit.test.runtimeClasspath"))
    check(classpath.isNotBlank() && classpath.length < 4 * 1024 * 1024)
    val own = Path.of(NativeLoaderBoundaryEntrypoint::class.java.protectionDomain.codeSource.location.toURI()).toRealPath()
    check(classpath.split(File.pathSeparatorChar).map { Path.of(it) }.filter { Files.exists(it) }.any { it.toRealPath() == own })
    val argfile = root.resolve("$mode.java-args")
    val arguments = listOf("-Xmx128m", "-Xcheck:jni", "-ea", "-Duser.home=$home", "-Djava.library.path=$external",
        "-classpath", classpath, NativeLoaderBoundaryEntrypoint::class.java.name, mode)
    fun quote(value: String): String = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    Files.writeString(argfile, arguments.joinToString("\n", transform = ::quote) + "\n")
    val java = Path.of(System.getProperty("java.home"), "bin", if (File.separatorChar == '\\') "java.exe" else "java")
    val stdout = root.resolve("$mode.stdout")
    val stderr = root.resolve("$mode.stderr")
    val process = ProcessBuilder(java.toString(), "@$argfile").redirectOutput(stdout.toFile())
        .redirectError(stderr.toFile()).start()
    try {
        assertTrue(process.waitFor(20, TimeUnit.SECONDS), "Actual loader boundary JVM timed out")
        assertEquals(0, process.exitValue(), "Actual loader boundary failed: " +
            if (process.exitValue() == 0) "" else boundedBoundaryFailure(stderr, root))
        assertTrue(Files.size(stdout) < 4096)
        val observed = Files.readString(stdout).trim()
        if (mode == "home-permissions") {
            assertTrue(observed in setOf("NATIVECMPKIT_LOADER_BOUNDARY $mode denied verified",
                "NATIVECMPKIT_LOADER_BOUNDARY $mode permitted verified"))
            println(observed) // Safe actual capability/outcome witness; no paths or classpath.
        } else assertEquals("NATIVECMPKIT_LOADER_BOUNDARY $mode verified", observed)
    } finally {
        if (process.isAlive) { process.destroyForcibly(); assertTrue(process.waitFor(10, TimeUnit.SECONDS)) }
    }
}

/** Only bounded public fixture errors; never the argument file, classpath or environment. */
private fun boundedBoundaryFailure(stderr: Path, ownedRoot: Path): String =
    Files.newInputStream(stderr).use { it.readNBytes(8192) }.toString(Charsets.UTF_8)
        .replace(ownedRoot.toString(), "<owned-fixture>")
        .replace(System.getProperty("user.home"), "<test-user-home>")
        .lineSequence().take(12).joinToString("\n") { line ->
            if (Regex("(?i)(password|passwd|secret|token|credential|authorization|BEGIN .*PRIVATE KEY)").containsMatchIn(line))
                "[redacted sensitive diagnostic]" else line.take(512)
        }
