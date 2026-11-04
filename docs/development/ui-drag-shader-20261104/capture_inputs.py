# SPDX-License-Identifier: Apache-2.0
"""Capture scoped source/configuration custody; not a compiler or runtime test."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PREFIX = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/"
TEST_INPUTS = (
    PREFIX + "utils/DampedDragLifecycleRegressionTest.kt",
    PREFIX + "utils/InteractiveHighlightResourceLifecycleTest.kt",
    PREFIX + "button/LiquidButtonConstructionTraceTest.kt",
    PREFIX + "utils/UiDragShaderTestHost.kt",
    PREFIX + "internal/PointerCancellation.kt",
    PREFIX + "internal/NativeUiApplicationHost.kt",
    PREFIX + "internal/NativeObjectIdentity.kt",
)
INIT = "scripts/ci/ui_drag_shader_compile.init.gradle.kts"
PRESERVED = (
    PREFIX + "utils/DragAnimationAndHighlightTest.kt",
    "scripts/ci/adaptive_controls_compile.init.gradle.kts",
    "scripts/ci/ios_adaptive_controls_native.init.gradle.kts",
    "scripts/ci/ios_adaptive_controls_native_focus.py",
    "scripts/ci/ios_ui_application.py",
    "calf-ui/build.gradle.kts",
    "gradle/libs.versions.toml",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture() -> dict:
    configured = [Path(name) for name in subprocess.check_output(
        ["git", "ls-files", "-z", "*.gradle.kts", "gradle/*", "gradle.properties",
         "gradlew", "gradlew.bat", "convention-plugins/src/main/kotlin/*"],
        cwd=ROOT).decode().split("\0") if name]
    production = sorted({file for module in ("calf-ui", "calf-core")
        for source_set in ("commonMain", "nonAndroidMain", "iosMain")
        for file in (ROOT / module / "src" / source_set).rglob("*.kt")})
    production_paths = [str(path.relative_to(ROOT)) for path in production]
    configuration_paths = sorted(str(path) for path in configured if (ROOT / path).is_file())
    all_paths = sorted(set(production_paths + configuration_paths + list(TEST_INPUTS) + [INIT]))
    for name in all_paths:
        path = ROOT / name
        assert path.is_file() and not path.is_symlink() and path.absolute() == path.resolve()
    native = Path("/root/.konan/kotlin-native-prebuilt-linux-x86_64-2.4.20")
    external = [native / "konan/konan.properties", native / "bin/konanc",
                native / "konan/lib/kotlin-native-compiler-embeddable.jar"]
    java = Path(subprocess.check_output(["bash", "-c", "readlink -f $(command -v java)"]).decode().strip())
    external += [java, java.parent.parent / "release"]
    return {
        "captured_at_ns": time.time_ns(),
        "scope": "Ordinary calf-ui/calf-core iOS production chain, exactly seven test inputs and repository configuration candidates; inventory is not proof every configuration was evaluated or every source compiled, no native execution",
        "baseline_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "production_sources": production_paths,
        "effective_test_sources": list(TEST_INPUTS),
        "common_test_sources": [],
        "configuration_inputs": configuration_paths,
        "source_sha256": {name: sha(ROOT / name) for name in all_paths},
        "preserved_not_compiled_or_executed_here_sha256": {name: sha(ROOT / name) for name in PRESERVED},
        "external_toolchain_inputs_sha256": {str(path): sha(path) for path in external if path.is_file()},
        "java_version": subprocess.check_output([str(java), "--version"]).decode().strip(),
        "apple_links": 0,
        "native_tests_executed": 0,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Use one new output path; never overwrite an original receipt")
    output = Path(sys.argv[1])
    if output.exists():
        raise SystemExit("Refusing to overwrite original input custody")
    output.write_text(json.dumps(capture(), indent=2, sort_keys=True) + "\n")
    print("Scoped input custody captured; no compiler, native or library test result attested")
