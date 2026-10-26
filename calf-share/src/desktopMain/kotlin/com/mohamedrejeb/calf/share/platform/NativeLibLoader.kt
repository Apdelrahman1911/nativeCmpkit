// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.share.platform

import java.io.File
import java.io.InputStream

private const val LIB_NAME = "calf_share_native"

/**
 * Loads the native share library from JAR resources.
 *
 * The library is expected at: native/<os>-<arch>/<libFileName>
 * It is extracted to a user-scoped cache directory and loaded via [System.load].
 */
internal fun loadNativeLibrary() {
    // Try the system path first (packagers like Conveyor extract natives
    // out of the jar), then fall back to the bundled resource.
    try {
        System.loadLibrary(LIB_NAME)
        return
    } catch (_: UnsatisfiedLinkError) {
    }

    val osName = System.getProperty("os.name")?.lowercase().orEmpty()
    val osArch = System.getProperty("os.arch")?.lowercase().orEmpty()

    val (osPart, libFileName) = when {
        "mac" in osName || "darwin" in osName ->
            "macos" to "lib$LIB_NAME.dylib"

        "win" in osName ->
            "windows" to "$LIB_NAME.dll"

        "nux" in osName || "nix" in osName ->
            "linux" to "lib$LIB_NAME.so"

        else -> error("Unsupported OS: $osName")
    }

    val archPart = when {
        osArch == "aarch64" || osArch == "arm64" -> "arm64"
        osArch == "amd64" || osArch == "x86_64" -> "x64"
        else -> error("Unsupported architecture: $osArch")
    }

    val resourcePath = "native/$osPart-$archPart/$libFileName"

    val inputStream: InputStream = NativeShareBridge::class.java.classLoader
        ?.getResourceAsStream(resourcePath)
        ?: error(
            "Native library not found in JAR resources at '$resourcePath'. " +
                "Ensure the native library is built for $osPart-$archPart."
        )

    val userHome = System.getProperty("user.home") ?: error("No user.home for the private native cache; configure a trusted system library")
    val cacheDir = File(userHome, ".cache/calf-share")
    val targetFile = inputStream.use { input -> extractShareNativeLibrary(input.readBytes(), cacheDir, libFileName) }

    @Suppress("UnsafeDynamicallyLoadedCode")
    System.load(targetFile.absolutePath)
}
