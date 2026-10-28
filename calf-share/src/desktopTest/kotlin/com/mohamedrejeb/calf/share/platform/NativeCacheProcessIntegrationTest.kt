// NativeCmpKit test-only native/cache integration (2026-10-28).
package com.mohamedrejeb.calf.share.platform

import java.io.File
import java.net.URLClassLoader
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption.ATOMIC_MOVE
import java.nio.file.attribute.BasicFileAttributes
import java.security.MessageDigest
import java.util.Properties
import java.util.concurrent.TimeUnit
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotEquals
import kotlin.test.assertTrue

/** Actual separate JVMs/host JNI payloads. No fake native bridge and no OS dialog is opened. */
class NativeCacheProcessIntegrationTest {
    @Test fun twoSeparateJvmsReuseTheAlreadyLoadedHostLibraryAndKeepRealJniWorking() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val payload = root.resolve("host-payload").also { Files.write(it, hostPayload()) }
        val cache = home.resolve(".cache/calf-share")
        val first = child(root, "first", "packaged", home, cache, payload, nativeName())
        try {
            val one = first.ready()
            assertEquals("1", one.getProperty("version"))
            val file = Path.of(one.getProperty("path"))
            val originalIdentity = Files.readAttributes(file, BasicFileAttributes::class.java).fileKey()
            val second = child(root, "second", "packaged", home, cache, payload, nativeName())
            try {
                val two = second.ready()
                assertNotEquals(one.getProperty("pid"), two.getProperty("pid"))
                assertEquals(one.getProperty("path"), two.getProperty("path"), "Do not replace a loaded Windows DLL")
                assertEquals(one.getProperty("digest"), two.getProperty("digest"))
                assertTrue(first.process.isAlive, "The first JVM must still hold its native library")
                second.finish()
                assertTrue(first.process.isAlive, "The first library stays loaded while the second JVM exits")
                assertEquals(originalIdentity, Files.readAttributes(file, BasicFileAttributes::class.java).fileKey())
                assertContentEquals(hostPayload(), Files.readAllBytes(file))
                first.finish()
            } finally { second.close() }
        } finally { first.close() }
    }

    @Test fun differentCompiledNativeVersionsRaceInSeparateJvmsAndRetainTheirOwnDigestAndJniValue() = withRoot { root ->
        // These are independently compiled tiny test-only native versions, not
        // fabricated bytes or claims about a released library/foreign architecture.
        val firstBytes = compileNativeVersion(root, 1)
        val secondBytes = compileNativeVersion(root, 2)
        assertNotEquals(hash(Files.readAllBytes(firstBytes)), hash(Files.readAllBytes(secondBytes)))
        val home = privateCacheTestDirectory("home-", root)
        val cache = privateCacheTestDirectory("versions-", home)
        val name = System.mapLibraryName("nativecmpkit_test_versions")
        val first = child(root, "v1", "version", home, cache, firstBytes, name)
        try {
            val second = child(root, "v2", "version", home, cache, secondBytes, name)
            try {
            val extractedOne = first.extracted()
            val extractedTwo = second.extracted()
            assertNotEquals(extractedOne.getProperty("path"), extractedTwo.getProperty("path"))
            // Both actual native files are extracted before either JNI image is
            // loaded. This deterministically exercises the extraction/load gap.
            first.startLoading()
            second.startLoading()
            val one = first.ready()
            val two = second.ready()
            assertNotEquals(one.getProperty("pid"), two.getProperty("pid"))
            assertNotEquals(one.getProperty("path"), two.getProperty("path"))
            assertEquals("1", one.getProperty("version"))
            assertEquals("2", two.getProperty("version"))
            assertEquals(hash(Files.readAllBytes(firstBytes)), one.getProperty("digest"))
            assertEquals(hash(Files.readAllBytes(secondBytes)), two.getProperty("digest"))
            assertTrue(first.process.isAlive && second.process.isAlive)
            second.finish()
            assertTrue(first.process.isAlive)
            first.finish()
            assertContentEquals(Files.readAllBytes(firstBytes), Files.readAllBytes(Path.of(one.getProperty("path"))))
            assertContentEquals(Files.readAllBytes(secondBytes), Files.readAllBytes(Path.of(two.getProperty("path"))))
            } finally { second.close() }
        } finally { first.close() }
    }

    @Test fun killedPublisherCannotExposeAPartialIdentityAndTheNextJvmLoadsRealNativeFunctions() = withRoot { root ->
        val home = privateCacheTestDirectory("home-", root)
        val cache = home.resolve(".cache/calf-share")
        val payload = root.resolve("host-payload").also { Files.write(it, hostPayload()) }
        val publisher = child(root, "publisher", "stage", home, cache, payload, nativeName())
        try {
            val staged = publisher.ready()
            assertEquals("staged", staged.getProperty("phase"))
            val identity = Path.of(staged.getProperty("path"))
            assertFalse(Files.exists(identity), "The interrupted publisher must not have published any digest path")
            publisher.process.destroyForcibly()
            assertTrue(publisher.process.waitFor(10, TimeUnit.SECONDS))
            assertNotEquals(0, publisher.process.exitValue())
            assertFalse(Files.exists(identity))
            // The actual production extraction/host JNI is used, not a fake
            // replacement function. An orphan private staging file may remain
            // after SIGKILL; it must never be treated as a published identity.
            val next = child(root, "next", "packaged", home, cache, payload, nativeName())
            try {
                val loaded = next.ready()
                assertEquals("1", loaded.getProperty("version"))
                assertEquals(identity, Path.of(loaded.getProperty("path")))
                assertContentEquals(hostPayload(), Files.readAllBytes(identity))
                next.finish()
            } finally { next.close() }
        } finally { publisher.close() }
    }

    private fun withRoot(block: (Path) -> Unit) {
        val home = Path.of(System.getProperty("user.home")).toRealPath()
        val root = privateCacheTestDirectory("nativecmpkit-process-", home)
        var passed = false
        try { block(root); passed = true } finally {
            if (passed) {
                Files.walk(root).use { entries -> entries.sorted(Comparator.reverseOrder()).forEach(Files::deleteIfExists) }
            } else {
                // Bounded diagnostic files only, outside any distribution/Git.
                // Preserve a failed child's stderr/arguments for lead inspection.
                println("NATIVECMPKIT_NATIVE_PROCESS_FAILURE retained=$root")
            }
        }
    }
}

internal object NativeCacheProcessPayload {
    @JvmStatic external fun version(): Int
}

/** Non-GUI test entrypoint. Actual JNI calls are repeated while another JVM holds the same DLL. */
internal object NativeCacheProcessFixture {
    @JvmStatic fun main(args: Array<String>) {
        check(args.size == 8 && args[0] in setOf("packaged", "version", "stage"))
        val home = Path.of(args[1]).toRealPath()
        check(Path.of(System.getProperty("user.home")).toRealPath() == home)
        val cache = Path.of(args[2])
        val bytes = Files.readAllBytes(Path.of(args[3]))
        val name = args[4]
        val release = Path.of(args[5])
        val ready = Path.of(args[6])
        val done = Path.of(args[7])
        if (args[0] == "stage") {
            cacheExtract(bytes, cache, name, ShareCachePublication { complete, target ->
                check(Files.readAllBytes(complete).contentEquals(bytes))
                check(!Files.exists(target))
                witness(ready, "staged", "not-loaded", target, hash(bytes))
                awaitRelease(release)
                FileSystemShareCachePublication.publish(complete, target)
            })
            error("The owning test must terminate the paused publisher before publication")
        }
        val target = if (args[0] == "packaged") {
            check(bytes.contentEquals(hostPayload()))
            nativeHealth()
            home.resolve(".cache/calf-share").resolve(name.substringBeforeLast('.') + "-" + shareNativeContentHash(bytes) + "." + name.substringAfterLast('.'))
        } else {
            cacheExtract(bytes, cache, name).toPath().also { file ->
                witness(ready.resolveSibling(ready.fileName.toString() + ".extracted"), "extracted", "not-loaded", file, hash(bytes))
                awaitRelease(release.resolveSibling(release.fileName.toString() + ".load"))
                System.load(file.toAbsolutePath().toString())
            }
        }
        check(Files.readAllBytes(target).contentEquals(bytes))
        val value = if (args[0] == "version") NativeCacheProcessPayload.version() else nativeHealth()
        witness(ready, "ready", value.toString(), target, hash(bytes))
        awaitRelease(release)
        val after = if (args[0] == "version") NativeCacheProcessPayload.version() else nativeHealth()
        check(after == value && Files.readAllBytes(target).contentEquals(bytes))
        witness(done, "done", after.toString(), target, hash(bytes))
    }
}

private fun cacheExtract(bytes: ByteArray, directory: Path, name: String,
    publication: ShareCachePublication = FileSystemShareCachePublication): File =
    extractShareNativeLibrary(bytes, directory.toFile(), name, publication)

private fun nativeName(): String = System.mapLibraryName("calf_share_native")
private fun hostPayload(): ByteArray {
    val os = System.getProperty("os.name").lowercase().let {
        when { "mac" in it || "darwin" in it -> "macos"; "win" in it -> "windows";
            "nux" in it || "nix" in it -> "linux"; else -> error("Unsupported native test OS") }
    }
    val arch = when (System.getProperty("os.arch").lowercase()) {
        "amd64", "x86_64" -> "x64"; "arm64", "aarch64" -> "arm64"; else -> error("Unsupported native test architecture")
    }
    return checkNotNull(NativeCacheProcessFixture::class.java.classLoader.getResourceAsStream("native/$os-$arch/${nativeName()}")) {
        "Actual host native resource is missing; a skipped/fake native test is not allowed"
    }.use { it.readBytes() }
}

private fun nativeHealth(): Int {
    check(NativeShareBridge.abiVersion() == 1)
    NativeShareBridge.init()
    repeat(25) {
        check(NativeShareBridge.beginShareSheet("test", null, emptyArray(), null, 1) == 0L)
        NativeShareBridge.cancelShare(0)
        check(NativeShareBridge.activeRequestCount() == 0 && NativeShareBridge.liveUiOperationCount() == 0)
    }
    return 1
}

private fun hash(bytes: ByteArray): String = MessageDigest.getInstance("SHA-256").digest(bytes)
    .joinToString("") { "%02x".format(it) }

private fun witness(path: Path, phase: String, version: String, library: Path, digest: String) {
    val data = Properties().apply {
        setProperty("phase", phase); setProperty("version", version)
        setProperty("path", library.toAbsolutePath().toString()); setProperty("digest", digest)
        setProperty("pid", ProcessHandle.current().pid().toString())
    }
    val temporary = path.resolveSibling(path.fileName.toString() + ".tmp")
    Files.newOutputStream(temporary).use { data.store(it, null) }
    Files.move(temporary, path, ATOMIC_MOVE)
}

private fun awaitRelease(path: Path) {
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(30)
    while (!Files.exists(path)) {
        check(System.nanoTime() < deadline) { "Owning test never released this bounded child JVM" }
        Thread.sleep(10)
    }
}

private class CacheChild(val process: Process, private val readyFile: Path,
    private val releaseFile: Path, private val doneFile: Path) : AutoCloseable {
    fun extracted(): Properties = awaitWitness(readyFile.resolveSibling(readyFile.fileName.toString() + ".extracted")).also {
        check(it.getProperty("phase") == "extracted")
    }
    fun startLoading() { Files.createFile(releaseFile.resolveSibling(releaseFile.fileName.toString() + ".load")) }
    fun ready(): Properties = awaitWitness(readyFile)
    private fun awaitWitness(path: Path): Properties {
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(20)
        while (!Files.exists(path)) {
            check(process.isAlive) { "Actual native child exited before readiness: ${process.exitValue()}" }
            check(System.nanoTime() < deadline) { "Actual native child readiness timed out" }
            Thread.sleep(10)
        }
        return Files.newInputStream(path).use { input -> Properties().apply { load(input) } }.also {
            check(it.getProperty("pid") == process.pid().toString())
        }
    }
    fun finish() {
        Files.createFile(releaseFile)
        check(process.waitFor(20, TimeUnit.SECONDS)) { "Native child did not terminate after release" }
        check(process.exitValue() == 0) { "Native child failed its post-release JNI/bytes check" }
        val data = Files.newInputStream(doneFile).use { input -> Properties().apply { load(input) } }
        check(data.getProperty("phase") == "done" && data.getProperty("pid") == process.pid().toString())
        check(data.getProperty("version") == ready().getProperty("version"))
    }
    override fun close() {
        if (process.isAlive) {
            process.destroy()
            if (!process.waitFor(3, TimeUnit.SECONDS)) process.destroyForcibly()
            check(process.waitFor(10, TimeUnit.SECONDS)) { "Test-owned native child could not be stopped" }
        }
    }
}

private fun child(root: Path, id: String, mode: String, home: Path, cache: Path,
    payload: Path, libraryName: String): CacheChild {
    val ready = root.resolve("$id.ready"); val release = root.resolve("$id.release"); val done = root.resolve("$id.done")
    // Gradle's worker launcher classpath alone is not the library test classpath.
    // Use the actual defining URL loader; no reflection of private worker fields.
    val loader = NativeCacheProcessFixture::class.java.classLoader
    check(loader is URLClassLoader) { "Cannot prove the actual child JVM classpath for this test host" }
    val paths = loader.urLs.map { check(it.protocol == "file"); Path.of(it.toURI()).toString() }
    check(paths.isNotEmpty())
    val external = privateCacheTestDirectory("empty-system-path-", root)
    val arguments = listOf("-Xmx128m", "-Xcheck:jni", "-ea", "-Duser.home=$home", "-Djava.library.path=$external",
        "-classpath", paths.joinToString(File.pathSeparator), NativeCacheProcessFixture::class.java.name,
        mode, home.toString(), cache.toString(), payload.toString(), libraryName,
        release.toString(), ready.toString(), done.toString())
    // Java argument files also avoid Windows CreateProcess's short command limit.
    val argfile = root.resolve("$id.java-args")
    fun quote(value: String): String = "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\""
    Files.writeString(argfile, arguments.joinToString("\n", transform = ::quote) + "\n")
    val java = Path.of(System.getProperty("java.home"), "bin", if (File.separatorChar == '\\') "java.exe" else "java")
    val process = ProcessBuilder(java.toString(), "@$argfile").redirectOutput(root.resolve("$id.stdout").toFile())
        .redirectError(root.resolve("$id.stderr").toFile()).start()
    return CacheChild(process, ready, release, done)
}

private fun compileNativeVersion(root: Path, version: Int): Path {
    check(version in 1..2)
    val source = root.resolve("native-fixture.rs")
    if (!Files.exists(source)) Files.write(source,
        checkNotNull(NativeCacheProcessFixture::class.java.classLoader.getResourceAsStream("NativeCacheProcessPayload.rs")).use { it.readBytes() })
    val repo = generateSequence(Path.of(System.getProperty("user.dir")).toAbsolutePath()) { it.parent }
        .first { Files.isRegularFile(it.resolve("rust-toolchain.toml")) && Files.isRegularFile(it.resolve("settings.gradle.kts")) }
    val expected = Regex("(?m)^channel\\s*=\\s*\"([0-9]+\\.[0-9]+\\.[0-9]+)\"")
        .find(Files.readString(repo.resolve("rust-toolchain.toml")))!!.groupValues[1]
    val rustIdentity = root.resolve("rust-version.txt")
    val rust = ProcessBuilder("rustc", "--version").directory(repo.toFile()).redirectErrorStream(true)
        .redirectOutput(rustIdentity.toFile()).start()
    try {
        check(rust.waitFor(10, TimeUnit.SECONDS) && rust.exitValue() == 0)
        check(Files.size(rustIdentity) < 4096 && Files.readString(rustIdentity).startsWith("rustc $expected "))
    } finally { if (rust.isAlive) { rust.destroyForcibly(); check(rust.waitFor(10, TimeUnit.SECONDS)) } }
    val library = root.resolve(System.mapLibraryName("nativecmpkit_test_v$version"))
    val compiler = ProcessBuilder("rustc", "--edition=2021", "--crate-type=cdylib", "--crate-name", "nativecmpkit_cache_v$version",
        "--cfg", "fixture_v$version", "-C", "panic=abort", "-C", "opt-level=2", source.toString(), "-o", library.toString())
        .directory(repo.toFile()).redirectOutput(root.resolve("rust-v$version.stdout").toFile())
        .redirectError(root.resolve("rust-v$version.stderr").toFile()).start()
    try {
        check(compiler.waitFor(30, TimeUnit.SECONDS)) { "Pinned native fixture compilation timed out" }
        check(compiler.exitValue() == 0 && Files.isRegularFile(library)) { "Pinned native fixture compilation failed" }
    } finally {
        if (compiler.isAlive) { compiler.destroyForcibly(); check(compiler.waitFor(10, TimeUnit.SECONDS)) }
    }
    return library
}
