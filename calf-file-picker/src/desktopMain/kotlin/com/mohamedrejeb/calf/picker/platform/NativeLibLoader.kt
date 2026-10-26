// Modified for nativeCmpkit (2026-10-24): correctness, lifecycle, testing and build hardening.
package com.mohamedrejeb.calf.picker.platform

import java.io.File

private const val LIB_NAME = "calf_filepicker_native"

/**
 * Loads the native file picker library.
 *
 * Bundled resources are preferred. Packagers extracting natives out of the JAR may explicitly
 * opt into their trusted search path with `-Dnativecmpkit.picker.trustSystemLibrary=true`.
 * Never add user-writable/untrusted directories to that search path. Otherwise the library is read at
 * `native/<os>-<arch>/<libFileName>`, cached under a content-hashed name in a
 * user-scoped directory, and loaded via [System.load].
 *
 * Called once from [NativeFilePickerBridge]'s object init block.
 */
internal fun loadNativeLibrary() {
    if (System.getProperty("nativecmpkit.picker.trustSystemLibrary", "false").toBoolean()) {
        try {
            System.loadLibrary(LIB_NAME)
            return
        } catch (_: UnsatisfiedLinkError) {
            // A missing trusted external library may still be satisfied by the bundled payload.
        }
    }

    val (resourcePath, libFileName) = bundledLibraryLocation()
    val bytes = NativeFilePickerBridge::class.java.classLoader
        ?.getResourceAsStream(resourcePath)
        ?.use { it.readBytes() }
        ?: error(
            "Native library not found in JAR resources at '$resourcePath'. " +
                "Ensure the native library is built for this platform."
        )

    val cacheFileName = nativeLibraryCacheFileName(libFileName, nativeLibraryContentHash(bytes))
    val libraryFile = try {
        extractNativeLibrary(bytes, nativeCacheDirectory(), cacheFileName)
    } catch (e: Exception) {
        error("Failed to extract native file picker library '$cacheFileName': ${e.message}")
    }

    @Suppress("UnsafeDynamicallyLoadedCode")
    System.load(libraryFile.absolutePath)
}

/** Resource path inside the JAR and the platform file name of the bundled library. */
private fun bundledLibraryLocation(): Pair<String, String> {
    val osName = System.getProperty("os.name")?.lowercase().orEmpty()
    val osArch = System.getProperty("os.arch")?.lowercase().orEmpty()

    val (osPart, libFileName) = when {
        "mac" in osName || "darwin" in osName -> "macos" to "lib$LIB_NAME.dylib"
        "win" in osName -> "windows" to "$LIB_NAME.dll"
        "nux" in osName || "nix" in osName -> "linux" to "lib$LIB_NAME.so"
        else -> error("Unsupported OS: $osName")
    }

    val archPart = when (osArch) {
        "aarch64", "arm64" -> "arm64"
        "amd64", "x86_64" -> "x64"
        else -> error("Unsupported architecture: $osArch")
    }

    return "native/$osPart-$archPart/$libFileName" to libFileName
}
