#!/usr/bin/env python3
"""Run dependency-light probes against immutable upstream IO/picker sources.

This is NOT a Gradle/platform build. PlatformFilePicker uses a fake JNI dialog
and ComposeWindow/type stubs; its real JVM file-writing code is unchanged.
Native cache and Jodd sources/resources are compiled unchanged. No real user
files are touched: every destructive-save reproduction uses TemporaryDirectory.

Requires Java and Kotlin compiler jars already installed in a Gradle lib dir.
Example: python3 scripts/audit/io_jvm_probes.py
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt",
    "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/io/IOUtil.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt",
]
RESOURCE = "calf-file-picker/src/desktopMain/resources/jodd/net/MimeTypes.properties"

STUBS = {
    "ComposeWindow.kt": """
package androidx.compose.ui.awt
class ComposeWindow(val windowHandle: Long = 0)
""",
    "PickerTypes.kt": """
package com.mohamedrejeb.calf.picker
sealed class FilePickerFileType(vararg val value: String) {
    data object All: FilePickerFileType("*/*")
    data object Folder: FilePickerFileType("folder")
    data object Image: FilePickerFileType("image/*")
    class Extension(val extensions: List<String>): FilePickerFileType(*extensions.toTypedArray())
    class Custom(types: List<String>): FilePickerFileType(*types.toTypedArray())
}
sealed class FilePickerSelectionMode {
    data object Single: FilePickerSelectionMode()
    class Multiple(val maxItems: Int? = null): FilePickerSelectionMode()
}
""",
    "NativeFilePickerBridge.kt": """
package com.mohamedrejeb.calf.picker.platform
internal object NativeFilePickerBridge {
    var chosenPath: String? = null
    var lastExtensions: Array<String>? = null
    fun init() {}
    fun createFileDialog(title: String?, initialDirectory: String?, extensions: Array<String>?,
                         multiple: Boolean, parentWindow: Long): Long {
        lastExtensions = extensions
        return 1
    }
    fun createDirectoryDialog(title: String?, initialDirectory: String?, parentWindow: Long) = 1L
    fun createSaveDialog(title: String?, initialDirectory: String?, defaultName: String?,
                         extension: String?, parentWindow: Long) = 1L
    fun showFileDialog(handle: Long): Array<String> = chosenPath?.let { arrayOf(it) } ?: emptyArray()
    fun showDirectoryDialog(handle: Long): String? = chosenPath
    fun showSaveDialog(handle: Long): String? = chosenPath
    fun destroyDialog(handle: Long) {}
}
""",
}

HARNESS = r'''
import com.mohamedrejeb.calf.picker.FilePickerFileType
import com.mohamedrejeb.calf.picker.FilePickerSelectionMode
import com.mohamedrejeb.calf.picker.platform.*
import jodd.net.MimeTypes
import jodd.util.Wildcard
import kotlinx.coroutines.runBlocking
import java.io.File
import java.io.IOException
import java.util.Locale

private var count = 0
private fun probe(name: String, block: () -> Unit) {
    block()
    count++
    println("PASS $name")
}

fun main(args: Array<String>) {
    val root = File(args.single()).apply { mkdirs() }
    println("Evidence: unchanged baseline Kotlin file-write/cache/Jodd sources; native dialog mocked.")
    probe("cache hash and names") {
        val bytes = byteArrayOf(1, 2, 3)
        check(nativeLibraryContentHash(bytes) == "039058c6f2c0cb49")
        check(nativeLibraryCacheFileName("lib.so", "abcd") == "lib-abcd.so")
        check(nativeLibraryCacheFileName("lib", "abcd") == "lib-abcd")
    }
    probe("cache exact bytes, unchanged reuse, replacement, blocked-target fallback") {
        val cache = File(root, "cache")
        val bytes = byteArrayOf(1, 2, 3)
        val first = extractNativeLibrary(bytes, cache, "test.so")
        check(first.readBytes().contentEquals(bytes))
        check(first.setLastModified(1_000_000_000_000))
        check(extractNativeLibrary(bytes, cache, "test.so").lastModified() == 1_000_000_000_000)
        check(extractNativeLibrary(byteArrayOf(4), cache, "test.so").readBytes().contentEquals(byteArrayOf(4)))
        val blocked = File(cache, "blocked.so").apply { mkdirs() }
        File(blocked, "occupied").writeText("keep")
        val fallback = extractNativeLibrary(bytes, cache, "blocked.so")
        check(fallback != blocked && fallback.readBytes().contentEquals(bytes))
    }
    probe("MIME baseline positive exact and wildcard lookups") {
        check(MimeTypes.lookupMimeType("jpg") == "image/jpeg")
        check(MimeTypes.findExtensionsByMimeTypes("image/jpeg", false).toSet() == setOf("jpeg", "jpg", "jpe"))
        check(MimeTypes.findExtensionsByMimeTypes("image/*", true).contains("png"))
        val all = MimeTypes.findExtensionsByMimeTypes("*", true)
        println("  initialized MIME table: ${all.size} unique extensions")
    }
    probe("IO-015: modern image extensions absent; unknown custom MIME removes filter") {
        val images = MimeTypes.findExtensionsByMimeTypes("image/*", true)
        check(listOf("avif", "heic", "heif").none { it in images })
        PlatformFilePicker.createFilePickerHandle(null, FilePickerFileType.Custom(listOf("image/avif")), FilePickerSelectionMode.Single, null)
        check(NativeFilePickerBridge.lastExtensions == null)
        println("  image/avif -> native extensions=null (unrestricted)")
    }
    probe("IO-016: comma-without-space does not split MIME alternatives") {
        check(MimeTypes.findExtensionsByMimeTypes("image/jpeg,image/png", false).isEmpty())
        check(MimeTypes.findExtensionsByMimeTypes("image/jpeg, image/png", false).size == 4)
    }
    probe("IO-016: locale-dependent MIME lookup fails on uppercase TIFF") {
        val original = Locale.getDefault()
        try {
            Locale.setDefault(Locale.forLanguageTag("tr-TR"))
            check(MimeTypes.lookupMimeType("TIFF") == null)
            check(MimeTypes.lookupMimeType("tiff") == "image/tiff")
        } finally { Locale.setDefault(original) }
    }
    probe("wildcard expected empty/star/question/escape semantics") {
        check(Wildcard.match("", "*"))
        check(Wildcard.match("photo", "ph?to"))
        check(Wildcard.match("image/png", "image/**"))
        check(Wildcard.match("a*b", "a\\*b"))
        check(!Wildcard.match("a", "b"))
    }
    probe("normal desktop save/copy/cancel paths") {
        val source = File(root, "source.bin").apply { writeBytes(byteArrayOf(0, 127, -128, -1)) }
        val target = File(root, "target.bin")
        NativeFilePickerBridge.chosenPath = target.path
        runBlocking { check(PlatformFilePicker.showSaveDialogWithFile(1, source) == target) }
        check(source.readBytes().contentEquals(target.readBytes()))
        NativeFilePickerBridge.chosenPath = null
        runBlocking { check(PlatformFilePicker.showSaveDialog(1, byteArrayOf(1)) == null) }
        val empty = File(root, "empty.bin")
        NativeFilePickerBridge.chosenPath = empty.path
        runBlocking { PlatformFilePicker.showSaveDialog(1, null) }
        check(empty.isFile && empty.length() == 0L)
    }
    probe("IO-004: saving source onto itself deletes source before failing") {
        val source = File(root, "self-copy.bin").apply { writeText("unique source data") }
        NativeFilePickerBridge.chosenPath = source.path
        var failure: Exception? = null
        try { runBlocking { PlatformFilePicker.showSaveDialogWithFile(1, source) } }
        catch (e: IOException) { failure = e }
        check(failure != null)
        check(!source.exists())
        println("  exception=${failure.javaClass.simpleName}; source.exists=${source.exists()}")
    }
    probe("IO-004: saving null to existing destination preserves its nonempty bytes") {
        val target = File(root, "null-overwrite.bin").apply { writeText("previous data") }
        NativeFilePickerBridge.chosenPath = target.path
        runBlocking { PlatformFilePicker.showSaveDialog(1, null) }
        check(target.readText() == "previous data")
        println("  null-content save returned success; destination still has ${target.length()} bytes")
    }
    println("SUMMARY $count/$count probes passed (includes expected defect characterizations, not defect fixes)")
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gradle-lib", default="/opt/gradle/gradle-9.7.1/lib")
    args = parser.parse_args()
    libs = Path(args.gradle_lib)
    stdlib = next(libs.glob("kotlin-stdlib-*.jar"), None)
    coroutines = next(libs.glob("kotlinx-coroutines-core-jvm-*.jar"), None)
    if stdlib is None or coroutines is None:
        parser.error("installed Kotlin stdlib + coroutines jars are required; no automatic downloads")
    with tempfile.TemporaryDirectory(prefix="nativecmpkit-io-audit-") as temp:
        work = Path(temp)
        compile_sources = []
        for source in SOURCES:
            dest = work / source
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(subprocess.check_output(["git", "show", f"{BASELINE}:{source}"], cwd=ROOT))
            compile_sources.append(str(dest))
        for name, body in STUBS.items():
            dest = work / name
            dest.write_text(body)
            compile_sources.append(str(dest))
        harness = work / "Harness.kt"
        harness.write_text(HARNESS)
        compile_sources.append(str(harness))
        classes = work / "classes"
        classes.mkdir()
        resource = classes / "jodd/net/MimeTypes.properties"
        resource.parent.mkdir(parents=True)
        resource.write_bytes(subprocess.check_output(["git", "show", f"{BASELINE}:{RESOURCE}"], cwd=ROOT))
        cp = os.pathsep.join(map(str, [stdlib, coroutines]))
        print(f"Baseline: {BASELINE}", flush=True)
        subprocess.run([
            "java", "-Xmx384m", "-cp", str(libs / "*"),
            "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", "-version", "-no-stdlib", "-no-reflect", "-nowarn",
            "-classpath", cp, "-d", str(classes), *compile_sources,
        ], cwd=ROOT, check=True)
        subprocess.run(["java", "-Xmx256m", "-cp", os.pathsep.join([str(classes), cp]),
                        "HarnessKt", str(work / "fixtures")], check=True)


if __name__ == "__main__":
    main()
