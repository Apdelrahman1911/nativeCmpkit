#!/usr/bin/env python3
"""Fresh, bounded library test runs with source-bound, sanitized JUnit receipts.

This repository-specific runner deliberately has no arbitrary Gradle arguments,
publication command, source fallback, arbitrary skip list, or cached-report
success path. Two exact native host-inapplicable scenarios are reported N/A,
never counted as passed; every applicable native scenario remains required.
It is NOT a sandbox or a trusted-builder attestation. Coordinate other builds;
its lock covers only other invocations of this helper in the same checkout.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import runtime_context
import native_test_policy

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    "desktop": ("desktopTest", ("commonTest", "materialTest", "nonAndroidTest", "desktopTest")),
    "android-host": ("testAndroidHostTest", ("commonTest", "materialTest", "androidHostTest")),
    "js": ("jsBrowserTest", ("commonTest", "materialTest", "nonAndroidTest", "webTest", "jsTest")),
    "wasm": ("wasmJsBrowserTest", ("commonTest", "materialTest", "nonAndroidTest", "webTest", "wasmJsTest")),
    "ios": ("iosSimulatorArm64Test", ("commonTest", "nonAndroidTest", "nativeTest", "appleTest", "iosTest", "iosSimulatorArm64Test")),
}
# Guard the current minimum, independently of discovery, so deleting a module's
# last tests cannot turn a missing suite into a green "not applicable" entry.
PERMISSION_MODULES = tuple("calf-permissions/" + name for name in (
    "core", "camera", "gallery", "location", "background-location", "bluetooth",
    "contacts", "calendar", "notifications", "wifi", "microphone",
))
SHARED_MINIMUM = ("calf-io", "calf-file-picker", "calf-ui", "calf-navigation", "calf-geo",
                  "calf-camera-picker", "calf-share", "calf-webview", *PERMISSION_MODULES)
MINIMUM_MODULES = {suite: SHARED_MINIMUM for suite in SUITES}
MINIMUM_MODULES["desktop"] = (*SHARED_MINIMUM, "calf-file-picker-coil", "calf-cupertino-icons")
KNOWN_TEST_SETS = set(name for _, names in SUITES.values() for name in names) | {"androidDeviceTest", "iosArm64Test"}
ROOT_INPUTS = (
    "build.gradle.kts", "settings.gradle.kts", "gradle.properties", "gradle.lockfile",
    "gradlew", "gradlew.bat", "rust-toolchain.toml", ".cargo/config", ".cargo/config.toml",
    "package.json", "yarn.lock", "package-lock.json", "pnpm-lock.yaml",
)
IGNORED_INPUT_DIRS = {".git", ".gradle", "build", "target", "node_modules", "__pycache__", ".kotlin"}
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_TOTAL_REPORT_BYTES = 256 * 1024 * 1024
MAX_REPORTS = 10000
MAX_CASES = 200000
COUNTS = ("tests", "failures", "errors", "skipped")
PROJECT_PATH = re.compile(r":[a-z][a-z0-9-]*(?::[a-z][a-z0-9-]*)*\Z")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_digest(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{value}  {name}\n" for name, value in sorted(files.items())).encode()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    """Reject traversal and symlinks before inspecting or mutating owned outputs."""
    parts = Path(relative).parts
    if not parts or Path(relative).is_absolute() or any(part in {".", ".."} for part in parts):
        raise ValueError("Expected a confined repository-relative path")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is outside the test receipt contract: {relative}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError("Test path escapes the checkout")
    return current


def source_files(root: Path, relative: str) -> list[Path]:
    folder = safe_path(root, relative)
    if not folder.exists():
        return []
    if not folder.is_dir():
        raise ValueError(f"Expected source directory: {relative}")
    result = []
    for base, directories, names in os.walk(folder, followlinks=False):
        directories[:] = sorted(name for name in directories if name not in IGNORED_INPUT_DIRS)
        for name in [*directories, *names]:
            path = Path(base) / name
            if path.is_symlink():
                raise ValueError(f"Symlinked source input: {path.relative_to(root).as_posix()}")
        for name in sorted(names):
            path = Path(base) / name
            if not path.is_file():
                raise ValueError("Non-regular source input")
            result.append(path)
    return result


def projects(root: Path) -> dict[str, str]:
    """Read this repository's literal include/rename idiom; fail on changed syntax.

    This is not a general Gradle parser. A computed include/rename or different
    source hierarchy requires a deliberate update and new fixture, not guessing.
    """
    settings = safe_path(root, "settings.gradle.kts").read_text(encoding="utf-8")
    blocks = re.findall(r"(?ms)^include\(\s*(.*?)^\)", settings)
    if len(blocks) != 1:
        raise ValueError("Expected one literal settings include block; review CI project discovery")
    block = re.sub(r"(?m)//[^\n]*", "", blocks[0])
    paths = re.findall(r'"([^"\n]+)"', block)
    remainder = re.sub(r'"[^"\n]+"', "", block)
    if not paths or remainder.strip(" \t\r\n,") or len(paths) != len(set(paths)):
        raise ValueError("Computed or duplicate settings includes require explicit review")
    renames = dict(re.findall(r'(?m)^project\("([^"\n]+)"\)\.name = "([a-z][a-z0-9-]*)"\s*$', settings))
    if len(renames) != len(re.findall(r'(?m)^project\([^\n]+\)\.name\s*=', settings)):
        raise ValueError("Computed or duplicate project renames require explicit review")
    result = {}
    for original in paths:
        if not PROJECT_PATH.fullmatch(original):
            raise ValueError("Unrecognized included Gradle project path")
        if original.startswith(":sample:"):
            continue
        if not original.startswith(":calf-"):
            raise ValueError("Unknown non-sample project; classify its library test coverage explicitly")
        parts = original[1:].split(":")
        module = "/".join(parts)
        if not safe_path(root, module + "/build.gradle.kts").is_file():
            raise ValueError(f"Included library build file is missing: {module}")
        target = ":" + ":".join(renames.get(":" + ":".join(parts[:i + 1]), part)
                                 for i, part in enumerate(parts))
        if target in result.values():
            raise ValueError("Duplicate renamed library Gradle path")
        result[module] = target
    if set(renames) - set(paths):
        raise ValueError("Rename refers to a non-included project")
    return dict(sorted(result.items()))


def plan(root: Path, suite: str, minimum_modules: tuple[str, ...] | None = None,
         only_modules: tuple[str, ...] | None = None) -> dict:
    task_name, inherited = SUITES[suite]
    selected, uncovered = [], []
    for module, project in projects(root).items():
        source_root = safe_path(root, module + "/src")
        if source_root.is_dir():
            unknown = {path.name for path in source_root.iterdir()
                       if path.name.endswith("Test") and path.name not in KNOWN_TEST_SETS
                       and source_files(root, path.relative_to(root).as_posix())}
            if unknown:
                raise ValueError(f"Unknown test source sets in {module}: {sorted(unknown)}; update hierarchy mapping")
        inputs, source_sets = [], []
        for source_set in inherited:
            files = [path for path in source_files(root, f"{module}/src/{source_set}") if path.suffix in {".kt", ".java"}]
            if files:
                inputs.extend(path.relative_to(root).as_posix() for path in files)
                source_sets.append(source_set)
        if inputs:
            selected.append({"module": module, "project": project, "task": f"{project}:{task_name}",
                             "report_directory": f"{module}/build/test-results/{task_name}",
                             "test_source_sets": source_sets, "test_source_files": sorted(inputs)})
        else:
            uncovered.append({"module": module, "reason": f"No inherited test source files for {suite}; not executed or counted as passing"})
    not_selected = []
    if only_modules:
        if len(only_modules) != len(set(only_modules)):
            raise ValueError("Duplicate explicitly selected module")
        missing_selection = set(only_modules) - {item["module"] for item in selected}
        if missing_selection:
            raise ValueError(f"Selected modules do not have {suite} library test sources: {sorted(missing_selection)}")
        not_selected = sorted(item["module"] for item in selected if item["module"] not in only_modules)
        selected = [item for item in selected if item["module"] in only_modules]
        uncovered = [item for item in uncovered if item["module"] in only_modules]
    minimum = set((only_modules or MINIMUM_MODULES[suite]) if minimum_modules is None else minimum_modules)
    missing = minimum - {item["module"] for item in selected}
    if missing:
        raise ValueError(f"Required {suite} library test modules are absent: {sorted(missing)}")
    if not selected:
        raise ValueError(f"No library test sources for {suite}; a zero-test plan is not success")
    if suite == "desktop":
        for item in selected:
            if item["module"] == native_test_policy.MODULE and native_test_policy.SOURCE not in item["test_source_files"]:
                raise ValueError("Required native share scenario source is missing; do not silently reduce native coverage")
    return {"schema_version": 1, "suite": suite, "inherited_test_source_sets": list(inherited),
            "expected": selected, "uncovered": uncovered,
            "complete_suite_requested": not bool(only_modules), "explicit_module_subset": list(only_modules or ()),
            "test_bearing_modules_not_requested": not_selected,
            "scope": "Library tests only; discovery is source-set-aware, not a promise of native/device integration coverage"}


def snapshot_inputs(root: Path) -> dict[str, str]:
    inputs = set()
    for relative in ROOT_INPUTS:
        path = safe_path(root, relative)
        if path.is_file():
            inputs.add(path)
    for tree in ("gradle", "convention-plugins", "scripts/ci", "scripts/native", "kotlin-js-store"):
        inputs.update(source_files(root, tree))
    for module in projects(root):
        for relative in (f"{module}/src", f"{module}/native", f"{module}/.cargo", f"{module}/gradle"):
            inputs.update(source_files(root, relative))
        for name in ("build.gradle.kts", "gradle.properties", "gradle.lockfile"):
            path = safe_path(root, f"{module}/{name}")
            if path.is_file():
                inputs.add(path)
    # Sample build configuration is evaluated even in a library-only invocation;
    # sample source/tests are deliberately not substitutes for library execution.
    for path in safe_path(root, "sample").glob("*/build.gradle.kts"):
        inputs.add(safe_path(root, path.relative_to(root).as_posix()))
    result = {}
    for path in sorted(inputs):
        before = path.stat()
        value = sha256(path)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise ValueError("Source input changed while capturing its hash")
        result[path.relative_to(root).as_posix()] = value
    return result


class NoDtdBuilder(ET.TreeBuilder):
    def doctype(self, name, public_id, system_id):
        raise ValueError("DTD/entity declarations are not JUnit evidence")


def junit_cases(payload: bytes) -> list[dict]:
    if len(payload) > MAX_REPORT_BYTES:
        raise ValueError("JUnit report exceeds bounded input size")
    document = ET.fromstring(payload, parser=ET.XMLParser(target=NoDtdBuilder()))

    def visit(suite: ET.Element, depth: int = 0) -> list[dict]:
        if depth > 32:
            raise ValueError("JUnit nesting exceeds bounded report depth")
        if suite.tag not in {"testsuite", "testsuites"}:
            raise ValueError("Unrecognized JUnit root or nested suite")
        cases = []
        for item in suite:
            if item.tag in {"testsuite", "testsuites"}:
                cases.extend(visit(item, depth + 1))
            elif item.tag == "testcase" and suite.tag == "testsuite":
                name, classname = item.get("name", ""), item.get("classname", suite.get("name", ""))
                if not name or not classname or len(name) > 4096 or len(classname) > 4096:
                    raise ValueError("Missing or invalid actual testcase identity")
                statuses = [child.tag for child in item if child.tag in {"skipped", "failure", "error"}]
                if len(statuses) > 1:
                    raise ValueError("Conflicting or duplicate testcase outcome elements")
                if any(child.tag not in {"skipped", "failure", "error", "system-out", "system-err", "properties"} for child in item):
                    raise ValueError("Unrecognized testcase content")
                cases.append({"classname": classname, "name": name,
                              "status": {"failure": "failed", "error": "error", "skipped": "skipped"}.get(next(iter(statuses), ""), "passed")})
            elif item.tag not in {"properties", "system-out", "system-err"}:
                raise ValueError("Unrecognized JUnit suite content")
            if len(cases) > MAX_CASES:
                raise ValueError("JUnit testcase count exceeds bounded input size")
        counts = case_counts(cases)
        for key in COUNTS:
            declared = suite.get(key)
            if declared is not None and (not re.fullmatch(r"[0-9]+", declared) or int(declared) != counts[key]):
                raise ValueError("Declared JUnit summary differs from actual testcase elements")
        return cases

    cases = visit(document)
    identities = [(item["classname"], item["name"]) for item in cases]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate testcase identity in JUnit document")
    return cases


def case_counts(cases: list[dict]) -> dict[str, int]:
    statuses = Counter(case["status"] for case in cases)
    not_applicable = sum(case.get("disposition") == "not-applicable" for case in cases)
    return {"tests": len(cases), "failures": statuses["failed"], "errors": statuses["error"],
            "skipped": statuses["skipped"], "passed": statuses["passed"],
            "executed": len(cases) - statuses["skipped"], "not_applicable": not_applicable,
            "unexpected_skipped": statuses["skipped"] - not_applicable}


def collect_reports(root: Path, test_plan: dict, started_ns: int, ended_ns: int, marker_counts: Counter,
                    host_system: str | None = None, native_ui_opt_in: bool = False) -> dict:
    modules, errors, total_bytes, file_count = [], [], 0, 0
    for expected in test_plan["expected"]:
        module_cases, identities, reports, cases_by_report = [], set(), [], []
        task = expected["task"]
        if marker_counts[task] != 1:
            errors.append({"module": expected["module"], "error": "Expected exactly one fresh task execution marker", "markers": marker_counts[task]})
        folder = safe_path(root, expected["report_directory"])
        paths = []
        for base, directories, names in os.walk(folder, followlinks=False):
            directories.sort()
            for name in [*directories, *names]:
                safe_path(root, (Path(base) / name).relative_to(root).as_posix())
            paths.extend(Path(base) / name for name in sorted(names) if name.startswith("TEST-") and name.endswith(".xml"))
            if len(paths) + file_count > MAX_REPORTS:
                raise ValueError("JUnit report tree exceeds bounded file count")
        for path in paths:
            relative = path.relative_to(root).as_posix()
            try:
                path = safe_path(root, relative)
                stat = path.stat()
                if not path.is_file() or stat.st_nlink > 1:
                    raise ValueError("Non-regular or hardlinked JUnit evidence")
                if not started_ns - 2_000_000_000 <= stat.st_mtime_ns <= ended_ns + 2_000_000_000:
                    raise ValueError("Stale or future-dated JUnit report")
                total_bytes += stat.st_size
                file_count += 1
                if stat.st_size > MAX_REPORT_BYTES or total_bytes > MAX_TOTAL_REPORT_BYTES or file_count > MAX_REPORTS:
                    raise ValueError("JUnit evidence exceeds bounded input size")
                payload = path.read_bytes()
                after_read = path.stat()
                if (stat.st_size, stat.st_mtime_ns, stat.st_ino) != (after_read.st_size, after_read.st_mtime_ns, after_read.st_ino):
                    raise ValueError("JUnit report changed during evidence capture")
                cases = junit_cases(payload)
                keys = {(item["classname"], item["name"]) for item in cases}
                if keys & identities:
                    raise ValueError("Duplicate testcase identity across reports for one task")
                identities.update(keys)
                module_cases.extend(cases)
                if len(module_cases) > MAX_CASES:
                    raise ValueError("JUnit testcase total exceeds bounded input size")
                reports.append({"path": relative, "sha256": hashlib.sha256(payload).hexdigest(), **case_counts(cases)})
                cases_by_report.append(cases)
            except (OSError, ET.ParseError, ValueError) as error:
                # Do not export XML/system-out/failure bodies or machine paths.
                errors.append({"module": expected["module"], "path": relative, "error": type(error).__name__})
        scenarios, policy_errors = native_test_policy.apply(expected["module"], test_plan["suite"], module_cases,
                                                           host_system or platform.system(), native_ui_opt_in)
        errors.extend({"module": expected["module"], "error": error} for error in policy_errors)
        for report, cases in zip(reports, cases_by_report):
            report.update(case_counts(cases))
        counts = case_counts(module_cases)
        if not reports or not counts["executed"]:
            errors.append({"module": expected["module"], "error": "No actual non-skipped library testcases"})
        if counts["failures"] or counts["errors"] or counts["unexpected_skipped"]:
            errors.append({"module": expected["module"], "error": "Failed, errored or unexpected skipped tests are not accepted by this verification gate"})
        modules.append({"module": expected["module"], "task": task, **counts, "reports": reports,
                        "testcases": module_cases, "native_scenarios": scenarios})
    return {"modules": modules, "errors": errors,
            "native_matrix_scope": "Current host only; exact N/A cases are not passed and do not establish other host scenarios",
            "totals": {key: sum(module[key] for module in modules) for key in (*COUNTS, "passed", "executed", "not_applicable", "unexpected_skipped")}}


def quarantine_reports(root: Path, output: Path, test_plan: dict) -> list[str]:
    """Move only selected generated task-report trees, never caches or sources."""
    paths = []
    for item in test_plan["expected"]:
        source = safe_path(root, item["report_directory"])
        if source.exists() and not source.is_dir():
            raise ValueError("Selected generated report path is not a directory")
        # Validate all existing report-tree entries before the first mutation.
        if source.exists():
            for base, directories, names in os.walk(source, followlinks=False):
                for name in [*directories, *names]:
                    safe_path(root, (Path(base) / name).relative_to(root).as_posix())
        paths.append(source)
    moved = []
    for source in paths:
        if source.exists():
            relative = source.relative_to(root)
            destination = output / "previous-reports" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append(relative.as_posix())
    return moved


def gradle_command(suite: str, test_plan: dict, simulator: str | None = None) -> list[str]:
    if suite == "ios" and (not simulator or not runtime_context.UUID.fullmatch(simulator)):
        raise ValueError("iOS execution requires an explicitly selected, recorded simulator UDID")
    if suite != "ios" and simulator:
        raise ValueError("A simulator must not be supplied to a non-iOS test plan")
    command = [".\\gradlew.bat" if os.name == "nt" else "./gradlew", "--continue", "--no-daemon",
               "--console=plain", "--no-configuration-cache", f"--max-workers={1 if suite == 'ios' else 2}",
               "-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8",
               "-Pkotlin.compiler.execution.strategy=in-process", "-Pkotlin.native.jvmArgs=-Xmx2048m",
               "--init-script", "scripts/ci/fresh-tests.init.gradle.kts"]
    if simulator:
        command.append(f"-PnativecmpkitSimulatorDevice={simulator}")
    command.extend(item["task"] for item in test_plan["expected"])
    return command


def terminate_owned(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        # PID belongs to this invocation. /T includes only its descendants.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    else:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=30)


def execute(root: Path, command: list[str], log_path: Path, timeout: int, reserve_mib: int) -> dict:
    reserve = reserve_mib * 1024 * 1024
    if shutil.disk_usage(root).free < reserve:
        return {"exit_code": 75, "stop_reason": "Disk reserve unavailable; command not started"}
    started = time.monotonic()
    result = {}
    with log_path.open("w", encoding="utf-8") as log:
        kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT, **kwargs)
        try:
            while process.poll() is None:
                if shutil.disk_usage(root).free < reserve:
                    result["stop_reason"] = "Disk reserve reached; terminated only this invocation's process group"
                elif time.monotonic() - started > timeout:
                    result["stop_reason"] = "Timeout; terminated only this invocation's process group"
                if result:
                    terminate_owned(process)
                    break
                time.sleep(1)
        except BaseException:
            terminate_owned(process)
            raise
        result.update(exit_code=process.returncode, elapsed_seconds=round(time.monotonic() - started, 2))
    return result


def execution_markers(log: Path) -> Counter:
    markers = Counter()
    if log.is_file():
        with log.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                match = re.match(r"^NATIVECMPKIT_TEST_RUNTIME task=(:[a-zA-Z0-9:_-]+) gradle=", line)
                if match:
                    markers[match.group(1)] += 1
    return markers


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_revision(root: Path) -> str:
    value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, timeout=30).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Unable to establish full source revision")
    return value


def run(root: Path, suite: str, output_relative: str, simulator: str | None, timeout: int, reserve_mib: int,
        only_modules: tuple[str, ...] | None = None) -> dict:
    output = safe_path(root, output_relative)
    allowed = root / "build/ci-verification"
    if output == allowed or not output.is_relative_to(allowed) or output.exists():
        raise ValueError("Use a new, dedicated output directory below build/ci-verification; old evidence must not be overwritten")
    test_plan = plan(root, suite, only_modules=only_modules)
    command = gradle_command(suite, test_plan, simulator)
    allowed.mkdir(parents=True, exist_ok=True)
    lock = allowed / ".library-tests.lock"
    # Do not auto-remove an existing lock: another coordinated run may own it.
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode())
        output.mkdir(parents=True)
        revision_before = git_revision(root)
        before = snapshot_inputs(root)
        write_json(output / "inputs-before.json", before)
        write_json(output / "plan.json", test_plan)
        context = runtime_context.capture(apple=suite == "ios", device=simulator,
                                          require_booted=suite == "ios",
                                          android_package="android-37.0" if suite == "android-host" else None,
                                          browser=suite in {"js", "wasm"})
        if context["source_revision"] != revision_before:
            raise ValueError("Source revision changed while preparing the test invocation")
        write_json(output / "runtime.json", context)
        moved = quarantine_reports(root, output, test_plan)
        started_ns = time.time_ns()
        started_utc = utc_now()
        execution = execute(root, command, output / "gradle.log", timeout, reserve_mib)
        ended_ns = time.time_ns()
        receipt = {"schema_version": 1, "suite": suite, "started_at_utc": started_utc, "finished_at_utc": utc_now(),
                   "source_revision": context["source_revision"], "source_tree_dirty": context["source_tree_dirty"],
                   "command": command, "execution": execution, "quarantined_prior_reports": moved,
                   "inputs_before_sha256": input_digest(before), "runtime_receipt_sha256": sha256(output / "runtime.json"),
                   "uncovered": test_plan["uncovered"],
                   "complete_suite_requested": test_plan["complete_suite_requested"],
                   "explicit_module_subset": test_plan["explicit_module_subset"],
                   "test_bearing_modules_not_requested": test_plan["test_bearing_modules_not_requested"],
                   "scope": "Fresh source-bound library suite executions; not whole-library/device/ABI/release certification"}
        try:
            after = snapshot_inputs(root)
            write_json(output / "inputs-after.json", after)
            receipt["inputs_after_sha256"] = input_digest(after)
            receipt["changed_inputs"] = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
            receipt["source_revision_after"] = git_revision(root)
            if receipt["source_revision_after"] != revision_before:
                receipt["input_capture_error"] = "Git source revision changed during test invocation"
        except (OSError, ValueError):
            receipt["input_capture_error"] = "Unable to establish unchanged source inputs after execution"
        receipt.update(collect_reports(root, test_plan, started_ns, ended_ns, execution_markers(output / "gradle.log"),
                                       host_system=context["host"]["system"],
                                       native_ui_opt_in=os.environ.get("NATIVECMPKIT_NATIVE_UI_TESTS") == "true"))
        receipt["passed"] = (execution["exit_code"] == 0 and not execution.get("stop_reason") and not receipt["errors"]
                             and not receipt.get("input_capture_error") and not receipt.get("changed_inputs"))
        write_json(output / "receipt.json", receipt)
        return receipt
    finally:
        os.close(descriptor)
        lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "run"])
    parser.add_argument("--suite", choices=sorted(SUITES), required=True)
    parser.add_argument("--module", action="append", help="Explicit module-directory subset for investigation only; never reported as the complete CI suite")
    parser.add_argument("--output", help="A new repository-relative directory below build/ci-verification (run only)")
    parser.add_argument("--simulator", help="The actual selected and booted iOS simulator UDID")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--reserve-mib", type=int, default=8192)
    args = parser.parse_args()
    if args.timeout < 1 or args.reserve_mib < 1024:
        parser.error("Require a positive timeout and at least a 1GiB disk reserve")
    if args.operation == "plan":
        if args.output or args.simulator:
            parser.error("plan is read-only and takes neither output nor simulator")
        print(json.dumps(plan(ROOT, args.suite, only_modules=tuple(args.module or ())), indent=2, sort_keys=True))
        return 0
    if not args.output:
        parser.error("run requires a new --output directory")
    receipt = run(ROOT, args.suite, args.output, args.simulator, args.timeout, args.reserve_mib, tuple(args.module or ()))
    print(json.dumps({key: receipt[key] for key in ("suite", "source_revision", "passed", "complete_suite_requested", "explicit_module_subset", "execution", "totals", "errors")}, indent=2, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Library test verification refused: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(2)
