# SPDX-License-Identifier: Apache-2.0
"""Lead-granted single serial offline compiler; finite timeout and disk guard."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MIN_FREE = 8 * 1024 ** 3
LIMIT_SECONDS = 600
TERM_GRACE_SECONDS = 30
JAVA = Path("/usr/lib/jvm/java-17-openjdk-amd64")
COMMAND = [
    "./gradlew", "--offline", "--no-daemon", "--console=plain",
    "--no-configuration-cache", "--max-workers=1",
    "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
    "-Pkotlin.compiler.execution.strategy=in-process",
    "-Pkotlin.native.jvmArgs=-Xmx2048m",
    "--init-script", "scripts/ci/ui_drag_shader_compile.init.gradle.kts",
    ":calf-ui:compileTestKotlinIosSimulatorArm64",
]


def capture(name: str, env: dict) -> dict:
    path = OUT / name
    subprocess.run([sys.executable, str(OUT / "capture_inputs.py"), str(path)],
                   cwd=ROOT, env=env, check=True)
    return json.loads(path.read_text())


if __name__ == "__main__":
    prefix = "compiler" if len(sys.argv) == 1 else sys.argv[1] if len(sys.argv) == 2 else ""
    if prefix != "compiler" and re.fullmatch(r"compiler-recovery[1-9][0-9]*", prefix) is None:
        raise SystemExit("Use the original or a separately lead-granted numbered failed-task recovery")
    before_name, after_name, log_name, run_name = (
        prefix + "-before.json", prefix + "-after.json", prefix + ".log", prefix + "-run.json")
    if any((OUT / name).exists() for name in (before_name, after_name, log_name, run_name)):
        raise SystemExit("Refusing to overwrite original compiler evidence")
    if not (JAVA / "bin/java").is_file() or shutil.disk_usage(ROOT).free < MIN_FREE:
        raise SystemExit("No compiler executed: actual JDK17 and at least8 GiB free are mandatory")
    env = os.environ.copy()
    env["JAVA_HOME"] = str(JAVA)
    env["PATH"] = str(JAVA / "bin") + os.pathsep + env["PATH"]
    before = capture(before_name, env)
    free_before = shutil.disk_usage(ROOT).free
    if free_before < MIN_FREE:
        raise SystemExit("No compiler executed: free disk fell below8 GiB before launch")
    started_wall_ns = time.time_ns()
    started = time.monotonic()
    samples = [{"elapsed_seconds": 0, "free_bytes": free_before}]
    stopped = None
    with (OUT / log_name).open("xb") as log:
        process = subprocess.Popen(COMMAND, cwd=ROOT, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        while process.poll() is None:
            elapsed = time.monotonic() - started
            free = shutil.disk_usage(ROOT).free
            samples.append({"elapsed_seconds": elapsed, "free_bytes": free})
            if elapsed >= LIMIT_SECONDS or free < MIN_FREE:
                stopped = "timeout600s" if elapsed >= LIMIT_SECONDS else "disk_below8GiB"
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=TERM_GRACE_SECONDS)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            time.sleep(1)
        code = process.wait()
    elapsed = time.monotonic() - started
    after = capture(after_name, env)
    keys = ("source_sha256", "external_toolchain_inputs_sha256",
            "preserved_not_compiled_or_executed_here_sha256")
    held = all(before[key] == after[key] for key in keys)
    admission = ROOT / "build/ci-verification/ui-drag-shader-focused-compilation.json"
    if admission.is_file():
        shutil.copyfile(admission, OUT / (prefix + "-focused-compilation.json"))
    receipt = {
        "command": COMMAND,
        "java_home": str(JAVA),
        "started_at_ns": started_wall_ns,
        "elapsed_seconds": elapsed,
        "exit_code": code,
        "guard_stop": stopped,
        "timeout_seconds": LIMIT_SECONDS,
        "term_grace_seconds": TERM_GRACE_SECONDS,
        "minimum_required_free_bytes": MIN_FREE,
        "minimum_observed_free_bytes": min(row["free_bytes"] for row in samples),
        "disk_samples": samples,
        "source_input_count": len(before["source_sha256"]),
        "before_after_inputs_held": held,
        "precompiler_admission_present": admission.is_file(),
        "compiler_tests_executed": 0,
        "apple_links": 0,
        "native_library_tests": 0,
        "scope": "Actual compiler process only; exact original task log decides compilation, no native/consumer/API-ABI or performance acceptance",
        "original_log_sha256": hashlib.sha256((OUT / log_name).read_bytes()).hexdigest(),
    }
    (OUT / run_name).write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in (
        "exit_code", "elapsed_seconds", "guard_stop", "source_input_count",
        "before_after_inputs_held", "minimum_observed_free_bytes", "native_library_tests")}, indent=2))
    raise SystemExit(code if held else 1)
