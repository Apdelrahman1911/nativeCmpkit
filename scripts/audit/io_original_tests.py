#!/usr/bin/env python3
"""Compile/run the 15 original baseline desktop IO/picker tests without Gradle.

All sources are read from the immutable Git baseline without modification or
platform stubs. This verifies the selected JVM sources, not Gradle publication,
Compose integration, native loading/dialogs, or other targets. Only pre-existing
Gradle cache jars are used; no downloads or writes to shared caches occur.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

BASELINE = "af388bd3ad0325b2afdd8c0149cb7ff6f24c5da6"
ROOT = Path(__file__).resolve().parents[2]
COMMON = [
    "calf-core/src/commonMain/kotlin/com.mohamedrejeb.calf/core/PlatformContext.kt",
    *["calf-io/src/commonMain/kotlin/com.mohamedrejeb.calf/io/" + f
      for f in ["InternalContext.kt", "KmpFile.kt", "KmpFileSource.kt"]],
]
SOURCES = [
    *COMMON,
    "calf-core/src/nonAndroidMain/kotlin/com.mohamedrejeb.calf/core/PlatformContext.nonAndroid.kt",
    *["calf-io/src/desktopMain/kotlin/com/mohamedrejeb/calf/io/" + f
      for f in ["InternalContext.desktop.kt", "KmpFile.desktop.kt", "KmpFileSource.desktop.kt"]],
    "calf-io/src/desktopTest/kotlin/com/mohamedrejeb/calf/io/KmpFileSourceTest.kt",
    "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCache.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/io/IOUtil.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/net/MimeTypes.kt",
    "calf-file-picker/src/desktopMain/kotlin/jodd/util/Wildcard.kt",
    "calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/platform/NativeLibCacheTest.kt",
    "calf-file-picker/src/desktopTest/kotlin/jodd/net/MimeTypesTest.kt",
]
RESOURCE = "calf-file-picker/src/desktopMain/resources/jodd/net/MimeTypes.properties"
DEPENDENCIES = [
    ("org.jetbrains.kotlin", "kotlin-stdlib", "2.4.20"),
    ("org.jetbrains.kotlin", "kotlin-test", "2.4.20"),
    ("org.jetbrains.kotlin", "kotlin-test-junit", "2.4.20"),
    ("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.11.0"),
    ("org.jetbrains.kotlinx", "kotlinx-io-core-jvm", "0.9.1"),
    ("org.jetbrains.kotlinx", "kotlinx-io-bytestring-jvm", "0.9.1"),
    ("junit", "junit", "4.13.2"),
    ("org.hamcrest", "hamcrest-core", "1.3"),
    ("org.jetbrains", "annotations", "13.0"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path,
                        default=Path.home() / ".gradle/caches/modules-2/files-2.1")
    parser.add_argument("--compiler-support-lib", type=Path,
                        default=Path("/opt/gradle/gradle-9.7.1/lib"))
    args = parser.parse_args()

    def jar(group, artifact, version):
        matches = list((args.cache / group / artifact / version).glob(f"*/{artifact}-{version}.jar"))
        if not matches:
            parser.error(f"required cached jar missing: {group}:{artifact}:{version}; no downloads attempted")
        return matches[0]

    jars = [jar(*d) for d in DEPENDENCIES]
    compiler = jar("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.4.20")
    runtime_cp = os.pathsep.join(map(str, jars))
    compiler_cp = os.pathsep.join([str(compiler), runtime_cp, str(args.compiler_support_lib / "*")])
    print(f"Baseline: {BASELINE}", flush=True)
    print("Mode: unchanged extracted sources; no stubs; exact Kotlin/IO/coroutines versions; no Gradle/native UI", flush=True)
    print("Dependencies: " + ", ".join(":".join(d) for d in DEPENDENCIES), flush=True)
    with tempfile.TemporaryDirectory(prefix="nativecmpkit-io-original-tests-") as temp:
        work = Path(temp)
        for source in SOURCES:
            dest = work / source
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(subprocess.check_output(["git", "show", f"{BASELINE}:{source}"], cwd=ROOT))
        classes = work / "classes"
        resource = classes / "jodd/net/MimeTypes.properties"
        resource.parent.mkdir(parents=True)
        resource.write_bytes(subprocess.check_output(["git", "show", f"{BASELINE}:{RESOURCE}"], cwd=ROOT))
        subprocess.run([
            "java", "-Xmx384m", "-cp", compiler_cp,
            "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", "-version", "-no-stdlib", "-no-reflect",
            "-Xmulti-platform", "-Xexpect-actual-classes",
            "-Xcommon-sources=" + ",".join(str(work / s) for s in COMMON),
            "-classpath", runtime_cp, "-d", str(classes), *[str(work / s) for s in SOURCES],
        ], cwd=ROOT, check=True)
        subprocess.run([
            "java", "-Xmx256m", "-cp", os.pathsep.join([str(classes), runtime_cp]),
            "org.junit.runner.JUnitCore",
            "com.mohamedrejeb.calf.io.KmpFileSourceTest",
            "com.mohamedrejeb.calf.picker.platform.NativeLibCacheTest",
            "jodd.net.MimeTypesTest",
        ], cwd=work, check=True)


if __name__ == "__main__":
    main()
