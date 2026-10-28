package com.mohamedrejeb.calf.permissions

import java.io.File
import java.net.URLClassLoader
import java.nio.file.Files
import java.nio.file.FileSystemException
import java.nio.file.Path
import java.nio.file.StandardOpenOption
import java.util.concurrent.TimeUnit
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import kotlin.test.fail

/**
 * An actual macOS Seatbelt child JVM, not a synthetic Granted value or a TCC grant.
 * The OS denies a witnessed write, all outbound networking and TCC-service lookup.
 * No App-Sandbox entitlement, portable permission service or native prompt is claimed.
 */
internal object UnsupportedPermissionSandboxProbe {
    private const val MARKER = "NATIVECMPKIT_PERMISSION_SANDBOX "
    private const val SENTINEL = "outside-sandbox-write-succeeded"

    fun verifyOnMacOs() {
        if (!System.getProperty("os.name").startsWith("Mac")) return
        val sandbox = Path.of("/usr/bin/sandbox-exec")
        assertTrue(Files.isExecutable(sandbox), "The required macOS sandbox check must not be skipped")
        val home = Files.createTempDirectory("nativecmpkit-permission-sandbox-")
        val probe = home.resolve("denied-write")
        val output = home.resolve("child.log")
        var child: Process? = null
        try {
            // The same user/path/operation succeeds outside Seatbelt, before and after.
            Files.writeString(probe, SENTINEL)
            val literal = probe.toString().replace("\\", "\\\\").replace("\"", "\\\"")
            require(literal.none { it == '\n' || it == '\r' || it == '\u0000' })
            val profile = """
                (version 1)
                (allow default)
                (deny file-write* (literal "$literal"))
                (deny network-outbound)
                (deny mach-lookup (global-name "com.apple.tccd") (global-name "com.apple.tccd.system"))
            """.trimIndent()
            val javaExecutable = Path.of(System.getProperty("java.home"), "bin", "java")
            val codeSource = Path.of(UnsupportedPermissionSandboxProbe::class.java.protectionDomain.codeSource.location.toURI())
            val classpath = (System.getProperty("java.class.path").split(File.pathSeparator) +
                generateSequence(UnsupportedPermissionSandboxProbe::class.java.classLoader) { it.parent }
                    .filterIsInstance<URLClassLoader>().flatMap { it.getURLs().asSequence() }
                    .filter { it.protocol == "file" }.map { Path.of(it.toURI()).toString() }.toList())
                .map { Path.of(it).toAbsolutePath().normalize() }.distinct()
            assertTrue(codeSource.toAbsolutePath().normalize() in classpath, "The child must load the real compiled test/fixture classes")
            child = ProcessBuilder(
                sandbox.toString(), "-p", profile, javaExecutable.toString(), "-Xcheck:jni",
                "-cp", classpath.joinToString(File.pathSeparator),
                UnsupportedPermissionSandboxProbe::class.java.name, probe.toString(),
            ).redirectErrorStream(true).redirectOutput(output.toFile()).start()
            assertTrue(child.waitFor(60, TimeUnit.SECONDS), "The owned sandbox child must finish, not be accepted on a timeout")
            assertTrue(Files.size(output) <= 32_768, "Sandbox diagnostics must remain bounded")
            val result = Files.readString(output)
            assertEquals(0, child.exitValue(), "The actual sandbox child failed:\n$result")
            val marker = result.lineSequence().filter { it.startsWith(MARKER) }.toList()
            assertEquals(listOf(MARKER + "{\"schema_version\":1,\"java_major\":17,\"denied_write\":true,\"unsupported_modes\":2}"), marker)
            assertEquals(SENTINEL, Files.readString(probe), "The rejected write must not change the file")
            Files.writeString(probe, SENTINEL + "-after", StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)
            assertEquals(SENTINEL + "-after", Files.readString(probe))
            println(marker.single()) // Public, bounded OS/runtime observation in actual JUnit XML.
        } finally {
            child?.let {
                if (it.isAlive) {
                    it.descendants().forEach { descendant -> descendant.destroyForcibly() }
                    it.destroyForcibly()
                    check(it.waitFor(10, TimeUnit.SECONDS)) { "The owned sandbox child did not terminate" }
                }
            }
            Files.deleteIfExists(output)
            Files.deleteIfExists(probe)
            Files.deleteIfExists(home)
        }
    }

    @JvmStatic fun main(args: Array<String>) {
        require(System.getProperty("os.name").startsWith("Mac"))
        require(Runtime.version().feature() == 17)
        require(args.size == 1)
        val probe = Path.of(args.single())
        assertTrue(Files.isRegularFile(probe))
        assertEquals(SENTINEL, Files.readString(probe))
        try {
            Files.writeString(probe, "must-not-be-written", StandardOpenOption.WRITE, StandardOpenOption.TRUNCATE_EXISTING)
            fail("Actual sandbox enforcement is required before accepting an Unsupported result")
        } catch (error: FileSystemException) {
            assertTrue(error.reason in setOf("Operation not permitted", "Permission denied", "Read-only file system"),
                "A missing/invalid file or unrelated IO failure is not sandbox-denial evidence")
        }
        assertEquals(SENTINEL, Files.readString(probe))
        // Real public factories/actuals, real Compose runtime, two guarded environments.
        // runTest's JVM TestResult completes synchronously or throws; no Promise is discarded.
        UnsupportedPublicFactoryFixture().environmentAndLegacyFlagsCannotManufactureAuthorization()
        println(MARKER + "{\"schema_version\":1,\"java_major\":17,\"denied_write\":true,\"unsupported_modes\":2}")
    }
}
