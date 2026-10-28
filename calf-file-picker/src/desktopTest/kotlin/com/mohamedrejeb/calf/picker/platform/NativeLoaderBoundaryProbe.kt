// NativeCmpKit actual Linux JNI/filesystem boundary probe (2026-10-28).
// Explicit privileged fixture driver only: not a default/zero-assert JUnit test.
package com.mohamedrejeb.calf.picker.platform

import java.nio.file.Files
import java.nio.file.LinkOption.NOFOLLOW_LINKS
import java.nio.file.Path
import java.nio.file.attribute.PosixFilePermissions
import java.security.MessageDigest
import java.util.Properties

internal object NativeRejectedAbiDiagnostics {
    @JvmStatic external fun initCalls(): Int
}

/** Uses production extraction/loader/bridge. No fake native API or OS chooser is opened. */
internal object NativeLoaderBoundaryProbe {
    @JvmStatic fun main(args: Array<String>) {
        check(args.size == 2)
        val mode = args[0]
        check(mode in setOf("foreign-cache", "noexec", "loaded", "read-only-home", "missing-home", "bad-abi", "bundled-preference"))
        check(System.getProperty("os.name").lowercase().contains("linux"))
        val witness = Path.of(args[1])
        if (mode == "missing-home") System.clearProperty("user.home")
        val bytes = checkNotNull(NativeLoaderBoundaryProbe::class.java.classLoader.getResourceAsStream(resourcePath())).use { it.readBytes() }
        val digest = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
        val name = nativeLibraryCacheFileName(System.mapLibraryName("calf_filepicker_native"), nativeLibraryContentHash(bytes))
        val home = System.getProperty("user.home")?.let { Path.of(it).toRealPath() }
        val cache = home?.resolve(".cache/nativecmpkit-filepicker")
        val native = when (mode) {
            "foreign-cache" -> {
                val directory = checkNotNull(cache)
                val probe = Files.createTempFile("nativecmpkit-boundary-owner-", ".tmp")
                val owner = try { Files.getOwner(probe, NOFOLLOW_LINKS) } finally { Files.delete(probe) }
                check(Files.getOwner(directory, NOFOLLOW_LINKS) != owner)
                try {
                    extractNativeLibrary(bytes, directory.toFile(), name)
                    error("A real foreign-owned cache must not be trusted even by a privileged caller")
                } catch (failure: IllegalStateException) {
                    check(failure.message == "Native cache belongs to another filesystem owner")
                }
                check(Files.list(directory).use { it.count() } == 0L)
                null
            }
            "bad-abi" -> {
                check(System.getProperty("nativecmpkit.picker.trustSystemLibrary") == "true")
                try {
                    NativeFilePickerBridge.init()
                    error("An explicitly selected real ABI2 native library must not initialize")
                } catch (failure: ExceptionInInitializerError) {
                    check(failure.cause is IllegalStateException && failure.cause!!.message == "Incompatible native file-picker ABI (expected 1)")
                }
                check(NativeRejectedAbiDiagnostics.initCalls() == 0)
                check(!Files.exists(checkNotNull(home).resolve(".cache")))
                null
            }
            "noexec" -> {
                try {
                    NativeFilePickerBridge.init()
                    error("An actual noexec mount must not load its cached executable")
                } catch (failure: UnsatisfiedLinkError) {
                    check(failure.message.orEmpty().contains(name))
                    check(failure.message.orEmpty().contains("failed to map segment from shared object"))
                }
                checkNotNull(cache).resolve(name).also { check(Files.readAllBytes(it).contentEquals(bytes)) }
            }
            else -> {
                check(NativeFilePickerBridge.abiVersion() == 1)
                NativeFilePickerBridge.init()
                repeat(25) {
                    val id = NativeFilePickerBridge.createFileDialog("Résumé 研究 😀", null, arrayOf("png"), false, 0)
                    check(id > 0)
                    NativeFilePickerBridge.destroyDialog(id)
                    NativeFilePickerBridge.destroyDialog(id)
                }
                val mapped = Files.readAllLines(Path.of("/proc/self/maps"))
                    .mapNotNull { it.substringAfter("/", "").takeIf(String::isNotEmpty)?.let { tail -> Path.of("/$tail") } }
                    .filter { it.fileName.toString() == name }.distinct()
                check(mapped.size == 1) { "Actual host native image must have exactly one verified mapped file identity" }
                mapped.single().toRealPath().also { image ->
                    check(Files.readAllBytes(image).contentEquals(bytes))
                    if (mode == "read-only-home" || mode == "missing-home") {
                        check(image.parent.fileName.toString().startsWith("nativecmpkit-filepicker-"))
                        check(Files.getPosixFilePermissions(image.parent, NOFOLLOW_LINKS) == PosixFilePermissions.fromString("rwx------"))
                        check(Files.getOwner(image, NOFOLLOW_LINKS) == Files.getOwner(image.parent, NOFOLLOW_LINKS))
                        if (home != null) { check(!image.startsWith(home)); check(!Files.exists(home.resolve(".cache"))) }
                    } else {
                        check(image == checkNotNull(cache).resolve(name))
                        if (mode == "bundled-preference") check(System.getProperty("nativecmpkit.picker.trustSystemLibrary", "false") == "false")
                    }
                }
            }
        }
        val result = Properties().apply {
            setProperty("mode", mode)
            setProperty("digest", digest)
            setProperty("pid", ProcessHandle.current().pid().toString())
            if (native != null) setProperty("path", native.toString())
        }
        Files.newOutputStream(witness).use { result.store(it, null) }
        println("NATIVECMPKIT_PICKER_BOUNDARY $mode verified")
    }

    private fun resourcePath(): String {
        val arch = when (System.getProperty("os.arch").lowercase()) {
            "amd64", "x86_64" -> "x64"; "arm64", "aarch64" -> "arm64"; else -> error("Unsupported host architecture")
        }
        return "native/linux-$arch/${System.mapLibraryName("calf_filepicker_native")}"
    }
}
