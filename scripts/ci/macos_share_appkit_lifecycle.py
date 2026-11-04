#!/usr/bin/env python3
"""One fresh, bounded macOS-arm64 AppKit lifecycle executable; never publish.

The fixed eight cases are native ownership/controlled-callback verification, not
visible-picker, recipient delivery, stress, Instruments or sanitizer evidence.
Only sanitized receipts and exact reached XML are suitable for artifact upload;
Cargo/native logs and the compiled executable stay private verification output.
Import and --plan are side-effect-free. This controller is not a sandbox or
trusted-builder attestation; the lead must serialize this with other GUI/builds.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET

import library_tests as library
import macos_share_missing_only as recovery
import macos_share_key_wait_observation as key_wait
import runtime_context

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/native"))
import artifacts as native  # Side-effect-free source/toolchain/container helpers.

PLATFORM = "macos-arm64"
TARGET = "aarch64-apple-darwin"
PINNED = "1.98.0"
MODULE = "calf-share"
MANIFEST = MODULE + "/native/Cargo.toml"
MAIN = MODULE + "/native/tests/appkit_lifecycle_main.rs"
CASES_SOURCE = MODULE + "/native/tests/appkit_lifecycle/cases.rs"
# These exact reviewed harness bytes qualify the non-exported failed-control
# assertion and default finite population, independently of a claimed XML pass.
HARNESS_PINS = {
    MAIN: "b31cad1ca8403b8649b33f43067d778459fe5816099c90c40059465d6b6bbd79",
    CASES_SOURCE: "9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b",
}
CASES = (
    "cancel_before_dispatch", "no_key_window", "missing_content_view",
    "real_picker_cancel", "controlled_picker_dismissal",
    "controlled_success_duplicate_late", "controlled_service_failure",
    "bounded_concurrent_requests",
)
CLASS = "com.mohamedrejeb.calf.share.native.AppKitLifecycle"
SUITE = "NativeCmpKitAppKitLifecycle"
REPORT_PARENT = "build/ci-verification/share-appkit-native"
DEFAULT_OUTPUT = "build/ci-verification/share-appkit-lifecycle"
COMPILE_SECONDS = 1200
NATIVE_SECONDS = 240
CONTEXT_SECONDS = 60
CLEANUP_SECONDS = 5
DISK_RESERVE = 8 * 1024 ** 3
MAX_LOG = 64 * 1024 ** 2
MAX_NATIVE_LOG = 4 * 1024 ** 2
MAX_XML = 32 * 1024
MAX_CONTEXT = 128 * 1024
# Same filesystem/wall-clock envelope as the owning library runner. Time alone
# NEVER proves freshness: exclusive target/artifact origin, absent actual-PID
# baseline, ordinary-file identity and full before/after custody are mandatory.
FRESHNESS_SLOP_NS = 2_000_000_000
MARKER = re.compile(
    r"NATIVECMPKIT_APPKIT_CASE name=([a-z0-9_]+) passed=(true|false) "
    r"seconds=([0-9]+\.[0-9]{6}) live=([0-9]+) registry=([0-9]+) cleanup=(true|false)\Z"
)
WITNESS = "actual-native=true live=0 registry=0 cleanup=true controlled-callbacks-not-recipient=true"


class Refusal(ValueError):
    """Fixed allowlisted error codes, never native/exception/environment bodies."""

    def __init__(self, code: str, evidence: dict | None = None):
        super().__init__(code)
        self.evidence = evidence


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Refusal(code)


def relative_path(root: Path, relative: str) -> Path:
    value = Path(relative)
    require(isinstance(relative, str) and bool(relative) and not value.is_absolute()
            and relative == value.as_posix() and ".." not in value.parts
            and "\\" not in relative and not any(ord(c) < 32 for c in relative), "unsafe-output-path")
    return library.safe_path(root, relative)


def ordinary_file(root: Path, relative: str, *, maximum: int | None = None) -> Path:
    path = relative_path(root, relative)
    metadata = path.lstat()
    require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1, "nonordinary-or-aliased-file")
    if maximum is not None:
        require(0 < metadata.st_size <= maximum, "file-outside-size-bound")
    return path


def file_identity(path: Path) -> dict:
    before = path.stat()
    value = native.digest(path)
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_mode) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_mode), "file-changed-during-read")
    return {"sha256": value, "size": before.st_size, "inode": before.st_ino,
            "device": before.st_dev, "mtime_ns": before.st_mtime_ns, "mode": before.st_mode}


def report_state(root: Path) -> dict:
    """Preserve complete preexisting report children, including directory identity."""
    parent = relative_path(root, REPORT_PARENT)
    if not parent.exists():
        return {}
    require(parent.is_dir(), "native-report-parent-not-directory")
    result, total = {}, 0
    for base, directories, files in os.walk(parent, followlinks=False):
        for name in sorted(directories + files):
            path = Path(base) / name
            rel = path.relative_to(root).as_posix()
            relative_path(root, rel)
            meta = path.lstat()
            require(stat.S_ISDIR(meta.st_mode) or stat.S_ISREG(meta.st_mode), "nonordinary-native-report-entry")
            if stat.S_ISDIR(meta.st_mode):
                result[rel] = {"kind": "directory", "inode": meta.st_ino, "device": meta.st_dev,
                               "mtime_ns": meta.st_mtime_ns, "mode": meta.st_mode}
            else:
                require(meta.st_nlink == 1, "aliased-native-report-entry")
                total += meta.st_size
                require(total <= 32 * 1024 ** 2, "native-report-inventory-byte-bound")
                result[rel] = {"kind": "file", **file_identity(path)}
            require(len(result) <= 4096, "native-report-inventory-count-bound")
    return dict(sorted(result.items()))


def group_alive(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def cleanup_group(process: subprocess.Popen, *, force: bool) -> dict:
    """Only the new-session child's owned PGID; reap even after leader exit."""
    result = {"term_sent": False, "kill_sent": False, "leader_reaped": False, "group_empty": False}
    try:
        # A normal leader exit does not authorize leaving live descendants behind.
        alive = group_alive(process.pid)
        if alive:
            result["term_sent"] = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # Owned group exited between the read and signal; still forced/red.
            deadline = time.monotonic() + CLEANUP_SECONDS
            while group_alive(process.pid) and time.monotonic() < deadline:
                process.poll()
                time.sleep(0.05)
            if group_alive(process.pid):
                result["kill_sent"] = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                deadline = time.monotonic() + CLEANUP_SECONDS
                while group_alive(process.pid) and time.monotonic() < deadline:
                    process.poll()
                    time.sleep(0.05)
        process.wait(timeout=CLEANUP_SECONDS)
        result.update(leader_reaped=True, group_empty=not group_alive(process.pid))
        result["forced"] = force or alive
    except (OSError, subprocess.TimeoutExpired):
        # Failure remains separate from the primary timeout/compiler/native cause.
        result["cleanup_error"] = "owned-process-cleanup-refused-or-timed-out"
        result["forced"] = True
    result["clean"] = (result["leader_reaped"] and result["group_empty"] and not result["forced"])
    return result


def execute(root: Path, command: list[str], stdout, stderr, environment: dict[str, str],
            timeout: int, maximum: int, *, discard: bool = False) -> dict:
    """Clock/disk/output-bound process controller with independent cleanup receipt."""
    result = {"started": False, "exit_code": None, "stop_reason": None, "started_at_ns": time.time_ns()}
    process, started = None, time.monotonic()
    try:
        require(shutil.disk_usage(root).free >= DISK_RESERVE, "eight-gib-disk-reserve-unavailable")
        process = subprocess.Popen(command, cwd=root, env=environment,
                                   stdout=subprocess.DEVNULL if discard else stdout,
                                   stderr=subprocess.DEVNULL if discard else stderr, start_new_session=True)
        result.update(started=True, pid=process.pid)
        while process.poll() is None:
            if shutil.disk_usage(root).free < DISK_RESERVE:
                result["stop_reason"] = "eight-gib-disk-reserve-reached"
            elif time.monotonic() - started >= timeout:
                result["stop_reason"] = "owned-process-timeout"
            elif not discard and sum(os.fstat(stream.fileno()).st_size for stream in (stdout, stderr)) > maximum:
                result["stop_reason"] = "process-output-size-bound"
            if result["stop_reason"]:
                break
            time.sleep(0.1)
        if not discard and sum(os.fstat(stream.fileno()).st_size for stream in (stdout, stderr)) > maximum:
            result["stop_reason"] = result["stop_reason"] or "process-output-size-bound"
    except (OSError, Refusal, KeyboardInterrupt) as error:
        result["stop_reason"] = str(error) if isinstance(error, Refusal) else (
            "owner-interrupted" if isinstance(error, KeyboardInterrupt) else "owned-process-start-or-monitor-error")
    finally:
        if process is not None:
            result["cleanup"] = cleanup_group(process, force=result["stop_reason"] is not None)
            result["exit_code"] = process.returncode
        result.update(ended_at_ns=time.time_ns(), elapsed_seconds=round(time.monotonic() - started, 6))
    result["passed"] = (result["started"] and result["exit_code"] == 0 and result["stop_reason"] is None
                        and result.get("cleanup", {}).get("clean") is True)
    return result


def private_capture(root: Path, command: list[str], environment: dict[str, str], *, discard=False) -> str:
    # Quiet context commands do not leave toolchain paths/Git status/launchctl
    # job/environment payloads in public or private artifact files.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        result = execute(root, command, stdout, stderr, environment, CONTEXT_SECONDS, MAX_CONTEXT, discard=discard)
        if not result["passed"]:
            raise Refusal("runtime-context-command-refused-" + Path(command[0]).name,
                          {"role": Path(command[0]).name, "execution": result, "payload_archived": False})
        if discard:
            return ""
        stdout.seek(0)
        stderr.seek(0)
        out, err = stdout.read(MAX_CONTEXT + 1), stderr.read(MAX_CONTEXT + 1)
        require(len(out) + len(err) <= MAX_CONTEXT and not err, "runtime-context-output-refused")
        return out.decode("utf-8", errors="strict").strip()


def git_identity(root: Path, environment: dict[str, str]) -> dict:
    revision = private_capture(root, ["git", "rev-parse", "HEAD"], environment)
    require(re.fullmatch(r"[0-9a-f]{40}", revision) is not None, "invalid-source-revision")
    dirty = bool(private_capture(root, ["git", "status", "--porcelain", "--untracked-files=normal"], environment))
    return {"source_revision": revision, "source_tree_dirty": dirty}


def build_environment(root: Path) -> dict[str, str]:
    environment = native._build_environment()
    extra = {"CARGO_BUILD_RUSTC", "CARGO_BUILD_RUSTC_WRAPPER", "CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER",
             "CARGO_BUILD_RUSTFLAGS", "CARGO_BUILD_TARGET_DIR", "SDKROOT", "MACOSX_DEPLOYMENT_TARGET",
             "RUSTUP_DIST_SERVER", "RUSTUP_UPDATE_ROOT", "CC", "CXX", "AR", "LD", "RANLIB"}
    require(not any(environment.get(key) for key in extra) and
            not any(key.startswith(("DYLD_", "LD_")) and environment[key] for key in environment),
            "ambient-build-or-native-injection-override")
    require(environment.get("RUSTUP_TOOLCHAIN") in (None, PINNED), "inherited-rust-toolchain-mismatch")
    # Cargo reads ancestor/CARGO_HOME configuration beyond tracked sources.
    # This fixed command admits none; do not silently trust wrappers/aliases.
    config_dirs = {(root / MODULE / "native") / ".cargo", *(p / ".cargo" for p in
                   (root / MODULE / "native").parents)}
    config_dirs.add(Path(environment.get("CARGO_HOME", str(Path.home() / ".cargo"))))
    require(not any((folder / name).exists() or (folder / name).is_symlink()
                    for folder in config_dirs for name in ("config", "config.toml")), "ambient-cargo-configuration")
    environment.update(CARGO_BUILD_JOBS="2", CARGO_TERM_COLOR="never")
    return environment


def executable_tool(path: str) -> dict:
    value = Path(path)
    require(value.is_absolute() and value.is_file() and os.access(value, os.X_OK), "missing-effective-toolchain-executable")
    canonical = value.resolve()
    metadata = canonical.stat()
    require(stat.S_ISREG(metadata.st_mode), "nonordinary-effective-toolchain-executable")
    return {"path_sha256": hashlib.sha256(os.fsencode(canonical)).hexdigest(), **file_identity(canonical)}


def runtime_identity(root: Path, environment: dict[str, str]) -> dict:
    require(native.current_platform() == PLATFORM and platform.system() == "Darwin", "actual-macos-arm64-required")
    require(environment.get("NATIVECMPKIT_NATIVE_UI_TESTS") == "true", "exact-native-gui-optin-required")
    require(native.toolchain(root) == PINNED, "reviewed-rust-toolchain-mismatch")
    prefix = ["rustup", "run", PINNED]
    rust = runtime_context.parse_rust(private_capture(root, [*prefix, "rustc", "--version", "--verbose"], environment))
    require(rust["release"] == PINNED and rust["host"] == TARGET, "effective-rust-host-or-version-mismatch")
    cargo = private_capture(root, [*prefix, "cargo", "--version", "--verbose"], environment)
    require(re.match(r"cargo " + re.escape(PINNED) + r" \([0-9a-f]+ [0-9-]+\)(?:\n|$)", cargo) is not None,
            "effective-cargo-version-mismatch")
    cargo_lines = dict(line.split(": ", 1) for line in cargo.splitlines() if ": " in line)
    require(cargo_lines.get("release") == PINNED and cargo_lines.get("host") == TARGET and
            re.fullmatch(r"[0-9a-f]{40}", cargo_lines.get("commit-hash", "")) is not None and
            re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", cargo_lines.get("commit-date", "")) is not None,
            "effective-cargo-identity-incomplete")
    rustup_path = shutil.which("rustup", path=environment.get("PATH"))
    require(rustup_path is not None, "rustup-executable-unavailable")
    tools = {"rustup": executable_tool(rustup_path)}
    for role in ("rustc", "cargo"):
        tools[role] = executable_tool(private_capture(root, ["rustup", "which", "--toolchain", PINNED, role], environment))
    xcode = runtime_context.parse_xcode(private_capture(root, ["xcodebuild", "-version"], environment))
    sdk = runtime_context.sdk_version(private_capture(root, ["xcrun", "--sdk", "macosx", "--show-sdk-version"], environment))
    sdk_build = private_capture(root, ["xcrun", "--sdk", "macosx", "--show-sdk-build-version"], environment)
    require(re.fullmatch(r"[0-9A-Za-z.]+", sdk_build) is not None, "macos-sdk-build-unidentified")
    tools["clang"] = executable_tool(private_capture(root, ["xcrun", "--sdk", "macosx", "--find", "clang"], environment))
    version = private_capture(root, ["sw_vers", "-productVersion"], environment)
    build = private_capture(root, ["sw_vers", "-buildVersion"], environment)
    require(re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version) is not None and
            re.fullmatch(r"[0-9A-Za-z]+", build) is not None, "macos-runtime-unidentified")
    private_capture(root, ["launchctl", "print", "gui/" + str(os.getuid())], environment, discard=True)
    return {"host": {"system": "Darwin", "architecture": "arm64", "macos_version": version,
                     "macos_build": build, "python": platform.python_version()},
            "rust": rust, "cargo": {key: cargo_lines[key] for key in ("release", "host", "commit-hash", "commit-date")},
            "xcode": xcode, "macos_sdk": {"version": sdk, "build": sdk_build}, "toolchain_executables": tools,
            "graphical_session_probe_exit_zero": True, "native_ui_optin": True,
            "visible_picker_or_recipient_verified": False, "launchctl_payload_archived": False}


def source_contract(root: Path, sources: dict) -> dict:
    key_wait.validate_current_sources(root)
    for relative, expected in HARNESS_PINS.items():
        payload = key_wait._ordinary_bytes(root, relative)[0]
        require(sources.get(relative) == hashlib.sha256(payload).hexdigest() and
                hashlib.sha256(key_wait.current_source_before_key_wait(relative, payload)).hexdigest() == expected,
                "unqualified-native-harness-bytes")
    manifest = tomllib.loads(ordinary_file(root, MANIFEST).read_text())
    require(manifest["package"]["name"] == "calf-share-native" and manifest["package"]["version"] == "0.1.0"
            and manifest["package"]["publish"] is False and manifest.get("test") == [{
                "name": "appkit_lifecycle", "path": "tests/appkit_lifecycle_main.rs", "harness": False,
                "required-features": ["appkit-lifecycle-tests"]}], "native-target-contract-changed")
    return {"source_path": CASES_SOURCE, "source_sha256": sources[CASES_SOURCE],
            "original_harness_sha256": HARNESS_PINS[CASES_SOURCE],
            "source_bound_failed_control_gate_verified": True,
            "raw_control_flag_exported": False, "raw_control_flag_independently_observed": False,
            "weak_release_witnesses": "source-qualified native assertions, not separate exported readings"}


def cargo_command(target: str) -> list[str]:
    return ["rustup", "run", PINNED, "cargo", "test", "--locked", "--features", "appkit-lifecycle-tests",
            "--test", "appkit_lifecycle", "--manifest-path", MANIFEST, "--no-run", "--message-format=json",
            "--target", TARGET, "--target-dir", target]


def unique_object(items):
    value = {}
    for key, entry in items:
        require(key not in value, "duplicate-cargo-json-key")
        value[key] = entry
    return value


def admit_artifact(root: Path, target: Path, stdout: bytes, execution: dict) -> tuple[Path, dict]:
    require(execution.get("passed") is True, "cargo-compilation-not-accepted")
    require(0 < len(stdout) <= MAX_LOG, "cargo-json-size-bound")
    candidates, finished, diagnostics = [], [], {"warnings": 0, "errors": 0}
    for line in stdout.splitlines():
        require(line.startswith(b"{"), "nonjson-cargo-stdout")
        entry = json.loads(line, object_pairs_hook=unique_object)
        require(isinstance(entry, dict), "cargo-message-not-object")
        if entry.get("reason") == "build-finished":
            finished.append(entry.get("success"))
        elif entry.get("reason") == "compiler-message":
            level = entry.get("message", {}).get("level")
            if level in ("warning", "error"):
                diagnostics[level + "s"] += 1
        elif entry.get("reason") == "compiler-artifact" and entry.get("executable") is not None:
            candidates.append(entry)
    require(finished == [True] and len(candidates) == 1 and diagnostics["errors"] == 0,
            "cargo-artifact-or-terminal-population-mismatch")
    entry = candidates[0]
    expected_package = "path+" + (root / MODULE / "native").as_uri() + "#calf-share-native@0.1.0"
    spec = entry.get("target", {})
    profile = entry.get("profile", {})
    require(entry.get("package_id") == expected_package and spec.get("name") == "appkit_lifecycle" and
            spec.get("kind") == ["test"] and spec.get("crate_types") == ["bin"] and
            spec.get("src_path") == str(root / MAIN) and spec.get("edition") == "2021" and
            profile.get("test") is True and profile.get("opt_level") == "0" and
            profile.get("debug_assertions") is True and entry.get("features") == ["appkit-lifecycle-tests"] and
            entry.get("fresh") is False, "cargo-executable-origin-mismatch")
    executable = entry.get("executable")
    require(isinstance(executable, str) and entry.get("filenames") == [executable], "cargo-executable-filenames-mismatch")
    path = Path(executable)
    require(path.parent == target / TARGET / "debug/deps" and
            re.fullmatch(r"appkit_lifecycle-[0-9a-f]+", path.name) is not None, "cargo-target-executable-path-mismatch")
    relative = path.relative_to(root).as_posix()
    ordinary_file(root, relative)
    require(os.access(path, os.X_OK), "native-artifact-not-executable")
    native.validate_binary(path, PLATFORM)
    with path.open("rb") as stream:
        header = stream.read(32)
    require(len(header) == 32 and struct.unpack_from("<I", header, 12)[0] == 2, "macho-is-not-mh-execute")
    identity = file_identity(path)
    require(execution["started_at_ns"] - FRESHNESS_SLOP_NS <= identity["mtime_ns"] <=
            execution["ended_at_ns"] + FRESHNESS_SLOP_NS, "native-artifact-not-fresh")
    return path, {"relative_path": relative, "package": "calf-share-native@0.1.0", "test_target": "appkit_lifecycle",
                  "source_path": MAIN, "source_sha256": HARNESS_PINS[MAIN], "rust_target": TARGET,
                  "macho_file_type": "MH_EXECUTE", "fresh_cargo_artifact": True,
                  "diagnostics": diagnostics, **identity}


def read_xml(payload: bytes, case: str) -> dict:
    require(0 < len(payload) <= MAX_XML, "native-xml-size-bound")
    root = ET.fromstring(payload, parser=ET.XMLParser(target=library.NoDtdBuilder()))
    failed = root.get("failures") == "1"
    require(root.tag == "testsuite" and root.attrib == {"name": SUITE, "tests": "1", "failures": "1" if failed else "0",
            "errors": "0", "skipped": "0"} and len(root) == 1, "native-xml-suite-mismatch")
    node = root[0]
    require(node.tag == "testcase" and set(node.attrib) == {"classname", "name", "time"} and
            node.get("classname") == CLASS and node.get("name") == case and
            re.fullmatch(r"[0-9]+\.[0-9]{6}", node.get("time", "")) is not None and
            0 <= float(node.get("time")) <= NATIVE_SECONDS and len(node) == (2 if failed else 1), "native-xml-case-mismatch")
    if failed:
        require(node[0].tag == "failure" and node[0].attrib == {
            "message": "Native assertion, control or owned cleanup failed; see original process log"}
            and len(node[0]) == 0 and not node[0].text, "native-xml-failure-shape-mismatch")
    witness = node[-1]
    require(witness.tag == "system-out" and not witness.attrib and len(witness) == 0 and
            re.fullmatch(r"actual-native=true live=[0-9]+ registry=[0-9]+ cleanup=(true|false) "
                         r"controlled-callbacks-not-recipient=true", witness.text or "") is not None,
            "native-xml-cleanup-witness-mismatch")
    require(failed or witness.text == WITNESS, "native-xml-passed-without-cleanup")
    cases = library.junit_cases(payload)
    require(cases == [{"classname": CLASS, "name": case, "status": "failed" if failed else "passed"}],
            "native-junit-outcome-mismatch")
    return cases[0]


def collect_reports(root: Path, output: Path, execution: dict, baseline: dict, stdout: bytes,
                    selected_cases: tuple[str, ...] = CASES) -> dict:
    """Preserve reached original XML even if the native process failed/stopped early."""
    recovery.validate_population(selected_cases)
    final = report_state(root)
    prefix = REPORT_PARENT + "/process-" + str(execution.get("pid", "unstarted"))
    collision = any(name == prefix or name.startswith(prefix + "/") for name in baseline)
    owned = {} if collision else {name: value for name, value in final.items()
                                  if name == prefix or name.startswith(prefix + "/")}
    nonowned = {name: value for name, value in final.items() if name not in owned}
    errors, reports, cases, markers = [], [], [], []
    if nonowned != baseline or collision:
        errors.append("preexisting-native-reports-changed-or-pid-collision")
    expected_files = {prefix + "/TEST-" + name + ".xml": name for name in selected_cases}
    if set(owned) - {prefix, *expected_files}:
        errors.append("unexpected-owned-native-report-entry")
    folder = output / "fresh-reports"
    folder.mkdir(mode=0o700)
    for relative, case in expected_files.items():
        if relative not in owned:
            continue
        try:
            path = ordinary_file(root, relative, maximum=MAX_XML)
            identity = file_identity(path)
            require({"kind": "file", **identity} == owned[relative], "native-xml-custody-changed-before-copy")
            payload = path.read_bytes()
            require(hashlib.sha256(payload).hexdigest() == identity["sha256"], "native-xml-changed-during-copy")
            require(execution.get("started_at_ns", 0) - FRESHNESS_SLOP_NS <= identity["mtime_ns"] <=
                    execution.get("ended_at_ns", 0) + FRESHNESS_SLOP_NS,
                    "native-xml-not-fresh")
            # Exclusively copy reached raw bytes after custody, including red XML.
            with (folder / path.name).open("xb") as stream:
                stream.write(payload)
            require(native.digest(folder / path.name) == identity["sha256"], "native-xml-copy-checksum-mismatch")
            reports.append({"source_relative_path": relative, "artifact_relative_path": "fresh-reports/" + path.name,
                            "case": case, **identity})
            row = read_xml(payload, case)
            cases.append(row)
            if row["status"] != "passed":
                errors.append("native-case-failed-" + case)
        except (OSError, ValueError, ET.ParseError) as error:
            errors.append(str(error) if isinstance(error, Refusal) else "native-xml-read-or-parse-refused")
    if len(stdout) > MAX_NATIVE_LOG:
        errors.append("native-console-size-bound")
    else:
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            if line.startswith("NATIVECMPKIT_APPKIT_CASE"):
                match = MARKER.fullmatch(line)
                if match is None or match[1] not in selected_cases or float(match[3]) > NATIVE_SECONDS:
                    errors.append("native-console-marker-mismatch")
                    continue
                markers.append({"name": match[1], "passed": match[2] == "true", "live": int(match[4]),
                                "registry": int(match[5]), "cleanup": match[6] == "true"})
    if ([row["name"] for row in markers] != list(selected_cases) or
            any(not row["passed"] or row["live"] != 0 or row["registry"] != 0 or not row["cleanup"] for row in markers)):
        errors.append("native-console-population-or-cleanup-not-accepted")
    if [case["name"] for case in cases] != list(selected_cases) or len(reports) != len(selected_cases):
        errors.append("native-eight-xml-population-not-accepted" if selected_cases == CASES
                      else "native-selected-xml-population-not-accepted")
    if execution.get("passed") is not True:
        errors.append("native-process-not-accepted")
    return {"passed": not errors, "errors": errors, "reports": reports, "testcases": cases,
            "console_markers": markers, "preexisting_reports_unchanged": nonowned == baseline,
            "reached_original_xml": len(reports), "accepted_xml_cases": sum(row["status"] == "passed" for row in cases),
            "source_report_state_sha256": hashlib.sha256(json.dumps(final, sort_keys=True).encode()).hexdigest(),
            "raw_control_flag_exported": False, "raw_control_flag_independently_observed": False,
            "remaining_witness_limits": ["visible presentation", "recipient/service delivery", "stress_2048",
                                        "Instruments/leaks", "ASan", "unbounded/concurrent stress"]}


def logged_execution(root: Path, output: Path, role: str, command: list[str], environment: dict, timeout: int,
                     maximum: int) -> tuple[dict, bytes]:
    paths = [output / (role + "." + stream + ".private.log") for stream in ("stdout", "stderr")]
    with paths[0].open("xb") as stdout, paths[1].open("xb") as stderr:
        execution = execute(root, command, stdout, stderr, environment, timeout, maximum)
    execution["private_logs"] = [{"relative_path": path.relative_to(root).as_posix(), **file_identity(path)} for path in paths]
    size_ok = sum(path.stat().st_size for path in paths) <= maximum
    execution["complete_log_within_size_bound"] = size_ok
    if not size_ok:
        execution.update(passed=False, stop_reason=execution["stop_reason"] or "process-output-size-bound")
    return execution, paths[0].read_bytes() if size_ok else b""


def missing_view_failure_observation(root: Path, output: Path, execution: dict,
                                     reports: dict, inputs: dict) -> dict:
    """Failure-only bounded reader of THIS owned sealed stderr, without another native query."""
    if (execution.get("passed") is not False or not any(
            row.get("name") == "missing_content_view" and row.get("status") == "failed"
            for row in reports.get("testcases", []))):
        return recovery.unavailable("missing-view-failure-not-reached")
    expected_path = (output / "native.stderr.private.log").relative_to(root).as_posix()
    logs = [row for row in execution.get("private_logs", []) if row.get("relative_path") == expected_path]
    if len(logs) != 1:
        return recovery.unavailable("owned-private-failure-stream-not-captured")
    sealed = logs[0]
    if type(sealed.get("size")) is not int or not 0 <= sealed["size"] <= recovery.MAX_STDERR:
        return recovery.unavailable("private-stream-outside-observation-bound")
    try:
        path = ordinary_file(root, expected_path)
        before = path.lstat()
        keys = ("device", "inode", "size", "mtime_ns", "mode")
        metadata = lambda value: {"device": value.st_dev, "inode": value.st_ino,
                                  "size": value.st_size, "mtime_ns": value.st_mtime_ns,
                                  "mode": value.st_mode}
        require(metadata(before) == {key: sealed[key] for key in keys}, "private-stream-identity-changed")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            require(metadata(opened) == metadata(before) and opened.st_nlink == 1,
                    "private-stream-open-identity-changed")
            payload = stream.read(recovery.MAX_STDERR + 1)
            after = os.fstat(stream.fileno())
        final = path.lstat()
        require(metadata(after) == metadata(before) == metadata(final) and
                after.st_nlink == final.st_nlink == 1 and
                len(payload) == sealed["size"] and hashlib.sha256(payload).hexdigest() == sealed["sha256"],
                "private-stream-read-custody-changed")
        value = recovery.appkit_failure(payload, source_hash=inputs.get(CASES_SOURCE),
                                        operation_hash=inputs.get(recovery.OPERATION_SOURCE),
                                        source_absolute=str(root / CASES_SOURCE),
                                        failed_case="missing_content_view")
        if inputs.get(CASES_SOURCE) == key_wait.cases_after_sha256():
            value["post_failure_owned_key_wait_snapshot"] = key_wait.post_failure_snapshot(
                payload, source_hash=inputs[CASES_SOURCE], failed_case="missing_content_view",
                source_absolute=str(root / CASES_SOURCE))
        value["owned_stream_sha256"] = sealed["sha256"]
        value["owned_stream_bytes"] = sealed["size"]
        return value
    except (OSError, ValueError, KeyError):
        return recovery.unavailable("private-failure-stream-custody-refused")


def run_missing_six(root: Path, output: Path, artifact_path: Path, artifact: dict,
                    environment: dict, before: dict, native_before: dict,
                    git_before: dict, runtime_before: dict, baseline: dict) -> tuple[dict, list[dict]]:
    """One admitted compilation; SIX fixed cases, serial fresh processes, stop on first refusal."""
    runs, current_baseline = [], baseline
    folders = output / "cases"
    folders.mkdir(mode=0o700)
    for case in recovery.MISSING_APPKIT:
        case_output = folders / case
        case_output.mkdir(mode=0o700)
        record = {"case": case, "passed": False, "errors": [],
                  "native_command": [artifact["relative_path"], "--case=" + case],
                  "native_case_arguments": ["--case=" + case], "phase": "pre-native"}
        runs.append(record)
        case_before, case_native_before, case_runtime_before, case_git_before = None, None, None, None
        try:
            case_before = library.snapshot_inputs(root)
            case_native_before = native.expected_source_files(root, MODULE)
            case_git_before = git_identity(root, environment)
            case_runtime_before = runtime_identity(root, environment)
            record.update(inputs_before_sha256=library.input_digest(case_before),
                          native_inputs_before_sha256=library.input_digest(case_native_before),
                          git_before=case_git_before, runtime_before=case_runtime_before)
            library.write_json(case_output / "inputs-before.json", case_before)
            library.write_json(case_output / "native-inputs-before.json", case_native_before)
            library.write_json(case_output / "runtime-before.json", case_runtime_before)
            require(case_before == before and case_native_before == native_before and
                    case_git_before == git_before, "source-changed-before-selected-native-case")
            require(case_runtime_before == runtime_before, "runtime-changed-before-selected-native-case")
            identity = file_identity(ordinary_file(root, artifact["relative_path"]))
            record["artifact_before"] = identity
            require(all(identity[key] == artifact[key] for key in identity),
                    "executable-changed-before-selected-native-case")
            require(report_state(root) == current_baseline, "reports-changed-before-selected-native-case")
            library.write_json(case_output / "preexisting-native-reports.json", current_baseline)
            record["phase"] = "native"
            execution, stdout = logged_execution(root, case_output, "native",
                                                 [str(artifact_path), "--case=" + case], environment,
                                                 NATIVE_SECONDS, MAX_NATIVE_LOG)
            record["native_execution"] = execution
            record["native_reports"] = collect_reports(root, case_output, execution,
                                                        current_baseline, stdout, (case,))
            if case == "missing_content_view" and execution.get("passed") is False:
                record["missing_view_failure_observation"] = missing_view_failure_observation(
                    root, case_output, execution, record["native_reports"], before)
            require(record["native_reports"]["passed"], "selected-native-case-not-accepted")
            record["phase"] = "final-custody"
        except (Exception, KeyboardInterrupt) as error:
            record["errors"].append(str(error) if isinstance(error, Refusal) else (
                "owner-interrupted" if isinstance(error, KeyboardInterrupt) else
                "selected-case-stage-refused-" + type(error).__name__))
        finally:
            for name, acquire, expected in (
                ("inputs_after", lambda: library.snapshot_inputs(root), case_before),
                ("native_inputs_after", lambda: native.expected_source_files(root, MODULE), case_native_before),
                ("git_after", lambda: git_identity(root, environment), case_git_before),
                ("runtime_after", lambda: runtime_identity(root, environment), case_runtime_before),
                ("artifact_after", lambda: file_identity(ordinary_file(root, artifact["relative_path"])),
                 record.get("artifact_before")),
            ):
                try:
                    value = acquire()
                    record[name + "_held"] = expected is not None and value == expected
                    if name in {"inputs_after", "native_inputs_after"}:
                        record[name + "_sha256"] = library.input_digest(value)
                    else:
                        record[name] = value
                    library.write_json(case_output / (name.replace("_", "-") + ".json"), value)
                    if not record[name + "_held"]:
                        record["errors"].append("selected-case-custody-changed-" + name)
                except (Exception, KeyboardInterrupt):
                    record["errors"].append("selected-case-final-custody-refused-" + name)
            try:
                final = report_state(root)
                digest = hashlib.sha256(json.dumps(final, sort_keys=True).encode()).hexdigest()
                reports = record.get("native_reports")
                record["reports_held"] = (digest == reports["source_report_state_sha256"]
                                           if reports is not None else final == current_baseline)
                record["preexisting_reports_unchanged"] = (reports["preexisting_reports_unchanged"]
                                                            if reports is not None else final == current_baseline)
                record["source_report_state_sha256"] = digest
                library.write_json(case_output / "reports-after.json", final)
                if not record["reports_held"]:
                    record["errors"].append("selected-case-final-report-custody-changed")
                current_baseline = final
            except (Exception, KeyboardInterrupt):
                record["errors"].append("selected-case-final-report-custody-refused")
            record["passed"] = (not record["errors"] and record.get("native_execution", {}).get("passed") is True
                                and record.get("native_reports", {}).get("passed") is True
                                and record.get("reports_held") is True
                                and all(record.get(name + "_held") is True for name in
                                        ("inputs_after", "native_inputs_after", "git_after", "runtime_after", "artifact_after")))
            library.write_json(case_output / "receipt.json", record)
        # A failed/unknown population never reaches a later selected case.
        if not record["passed"]:
            break
    reports, cases, markers = [], [], []
    for record in runs:
        value = record.get("native_reports", {})
        reports.extend({**row, "artifact_relative_path": "cases/" + record["case"] + "/" + row["artifact_relative_path"]}
                       for row in value.get("reports", []))
        cases.extend(value.get("testcases", []))
        markers.extend(value.get("console_markers", []))
    passed = len(runs) == len(recovery.MISSING_APPKIT) and all(row["passed"] for row in runs)
    summary = {"passed": passed, "errors": [] if passed else ["native-six-missing-case-batch-not-accepted"],
               "reports": reports, "testcases": cases, "console_markers": markers,
               "reached_original_xml": len(reports),
               "accepted_xml_cases": sum(row["status"] == "passed" for row in cases),
               "preexisting_reports_unchanged": all(row.get("preexisting_reports_unchanged") is True for row in runs),
               "source_report_state_sha256": runs[-1].get("source_report_state_sha256"),
               "remaining_unexecuted_cases": [case for case in recovery.MISSING_APPKIT
                                               if case not in {row["name"] for row in cases}],
               "compile_once": True, "stop_on_first_failure": True,
               "raw_control_flag_exported": False, "raw_control_flag_independently_observed": False,
               "remaining_witness_limits": ["visible presentation", "recipient/service delivery", "stress_2048",
                                             "Instruments/leaks", "ASan", "unbounded/concurrent stress"]}
    return summary, runs


def plan(case: str | None = None, *, missing_only: bool = False) -> dict:
    selected = recovery.appkit_selection(case, missing_only=missing_only)
    arguments = [] if case is None else ["--case=" + case]
    value = {"schema_version": 1, "platform": PLATFORM, "rust_target": TARGET, "rust_toolchain": PINNED,
            "cargo_command": cargo_command("<fresh-owned-target>"),
            "native_command": ["<admitted-mh-execute>", *arguments],
            "exact_native_cases": list(selected), "native_case_arguments": arguments, "stress_selected": False,
            "compile_timeout_seconds": COMPILE_SECONDS, "native_timeout_seconds": NATIVE_SECONDS,
            "filesystem_wallclock_envelope_ns": FRESHNESS_SLOP_NS,
            "disk_reserve_bytes": DISK_RESERVE, "read_only_plan": True, "publication_commands": []}
    if case is not None or missing_only:
        value["recovery_reference"] = recovery.recovery_reference()
    if "missing_content_view" in selected:
        value["key_wait_post_failure_snapshot"] = key_wait.plan_description()
    if missing_only:
        value.update(native_command=None, native_case_arguments=None,
                     native_commands=[["<admitted-mh-execute>", "--case=" + name] for name in selected],
                     compile_once=True, stop_on_first_failure=True, missing_only_share630=True)
    return value


def run(root: Path, output_relative: str, case: str | None = None, *, missing_only: bool = False) -> dict:
    selected = recovery.appkit_selection(case, missing_only=missing_only)
    arguments = [] if case is None else ["--case=" + case]
    root = root.resolve()
    output = relative_path(root, output_relative)
    allowed = root / "build/ci-verification"
    reports = root / REPORT_PARENT
    require(output != allowed and output.is_relative_to(allowed) and
            not (output == reports or output.is_relative_to(reports) or reports.is_relative_to(output)),
            "require-dedicated-ci-verification-output")
    require(not output.exists(), "refuse-existing-output")
    output.mkdir(parents=True, mode=0o700)
    receipt = {"schema_version": 1, "scope": "actual-macos-arm64-default-eight-AppKit-ownership",
               "started_at_utc": now(), "passed": False, "errors": [], "phase": "preflight",
               "platform": PLATFORM, "rust_target": TARGET, "rust_toolchain": PINNED,
               "exact_native_cases": list(selected), "stress_selected": False, "release_readiness_verified": False,
               "publication_performed": False, "raw_control_flag_exported": False,
               "raw_control_flag_independently_observed": False}
    if case is not None or missing_only:
        receipt.update(scope="actual-macos-arm64-Share630-missing-only-AppKit-ownership",
                       recovery_reference=recovery.recovery_reference(),
                       missing_only_share630=missing_only)
    lock = allowed / ".macos-share-appkit-lifecycle.lock"
    locked, environment, before, native_before, baseline, artifact_path, artifact = False, None, None, None, None, None, None
    try:
        if missing_only:
            import macos_share_appkit_only_route as appkit_only
            receipt["workflow_context"] = appkit_only.workflow_context()
        relative_path(root, lock.relative_to(root).as_posix())
        lock.mkdir(mode=0o700)
        locked = True
        environment = build_environment(root)
        receipt["git_before"] = git_identity(root, environment)
        require(not receipt["git_before"]["source_tree_dirty"], "immutable-clean-git-source-required")
        before = library.snapshot_inputs(root)
        native_before = native.expected_source_files(root, MODULE)
        library.write_json(output / "inputs-before.json", before)
        library.write_json(output / "native-inputs-before.json", native_before)
        receipt["control_failure_witness"] = source_contract(root, before)
        receipt["runtime_before"] = runtime_identity(root, environment)
        library.write_json(output / "runtime-before.json", receipt["runtime_before"])
        baseline = report_state(root)
        library.write_json(output / "preexisting-native-reports.json", baseline)
        target = output / "cargo-target"
        target.mkdir(mode=0o700)
        receipt.update(phase="compile", cargo_command=cargo_command("<fresh-owned-target>"))
        execution, stdout = logged_execution(root, output, "cargo", cargo_command(str(target)), environment,
                                             COMPILE_SECONDS, MAX_LOG)
        receipt["compilation"] = execution
        artifact_path, artifact = admit_artifact(root, target, stdout, execution)
        receipt["artifact_before"] = artifact
        require(library.snapshot_inputs(root) == before and native.expected_source_files(root, MODULE) == native_before
                and git_identity(root, environment) == receipt["git_before"], "source-changed-before-native-launch")
        require(runtime_identity(root, environment) == receipt["runtime_before"], "toolchain-or-runtime-changed-before-native-launch")
        launch_identity = file_identity(ordinary_file(root, artifact["relative_path"]))
        require(launch_identity == {key: artifact[key] for key in launch_identity},
                "native-executable-changed-before-launch")
        require(report_state(root) == baseline, "native-reports-changed-before-launch")
        receipt["phase"] = "native"
        if missing_only:
            receipt.update(native_command=None, native_case_arguments=None, compile_once=True,
                           stop_on_first_failure=True)
            summary, runs = run_missing_six(root, output, artifact_path, artifact, environment,
                                            before, native_before, receipt["git_before"],
                                            receipt["runtime_before"], baseline)
            receipt.update(native_reports=summary, native_case_runs=runs)
        else:
            receipt.update(native_command=[artifact["relative_path"], *arguments], native_case_arguments=arguments)
            execution, stdout = logged_execution(root, output, "native", [str(artifact_path), *arguments], environment,
                                                 NATIVE_SECONDS, MAX_NATIVE_LOG)
            receipt["native_execution"] = execution
            receipt["native_reports"] = collect_reports(root, output, execution, baseline, stdout, selected)
            if any(row["name"] == "missing_content_view" and row["status"] == "failed"
                   for row in receipt["native_reports"]["testcases"]):
                receipt["missing_view_failure_observation"] = missing_view_failure_observation(
                    root, output, execution, receipt["native_reports"], before)
        receipt["control_failure_witness"]["compiled_with_admitted_executable"] = True
        require(receipt["native_reports"]["passed"], "actual-native-eight-case-verification-not-accepted" if selected == CASES
                else "actual-native-selected-case-verification-not-accepted")
        receipt["phase"] = "final-custody"
    except (Exception, KeyboardInterrupt) as error:
        receipt["errors"].append(str(error) if isinstance(error, Refusal) else (
            "owner-interrupted" if isinstance(error, KeyboardInterrupt) else "runner-stage-refused-" + type(error).__name__))
        if isinstance(error, Refusal) and error.evidence is not None:
            receipt["refusal_evidence"] = error.evidence
    finally:
        # Failure capture is independent: no compiler/native exception may waive
        # final source, report-preservation, toolchain or owned-process cleanup.
        for name, acquire in (
            ("inputs_after", lambda: library.snapshot_inputs(root)),
            ("native_inputs_after", lambda: native.expected_source_files(root, MODULE)),
            ("git_after", lambda: git_identity(root, environment) if environment is not None else None),
            ("runtime_after", lambda: runtime_identity(root, environment) if "runtime_before" in receipt else None),
            ("reports_after", lambda: report_state(root) if baseline is not None else None),
        ):
            try:
                value = acquire()
                if value is not None:
                    if name in {"inputs_after", "native_inputs_after", "runtime_after", "reports_after"}:
                        library.write_json(output / (name.replace("_", "-") + ".json"), value)
                    receipt[name] = value if name in {"git_after", "runtime_after"} else (
                        {"count": len(value), "sha256": library.input_digest(value)} if name in {"inputs_after", "native_inputs_after"}
                        else {"inventory_captured": True})
                    if name == "inputs_after":
                        receipt["inputs_held"] = before is not None and value == before
                    if name == "native_inputs_after":
                        receipt["native_inputs_held"] = native_before is not None and value == native_before
                    if name == "reports_after":
                        report_digest = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
                        receipt["reports_held"] = (report_digest == receipt["native_reports"]["source_report_state_sha256"]
                                                   if "native_reports" in receipt else value == baseline)
                        if not receipt["reports_held"]:
                            receipt["errors"].append("final-native-report-custody-changed")
            except (Exception, KeyboardInterrupt) as error:
                receipt["errors"].append("final-custody-refused-" + name + "-" + type(error).__name__)
        if artifact_path is not None:
            try:
                ordinary_file(root, artifact["relative_path"])
                receipt["artifact_after"] = file_identity(artifact_path)
                receipt["artifact_held"] = all(receipt["artifact_after"][key] == artifact[key] for key in receipt["artifact_after"])
            except (OSError, ValueError):
                receipt["errors"].append("final-executable-custody-refused")
        for key, code in (("inputs_held", "complete-library-inputs-changed"),
                          ("native_inputs_held", "complete-native-inputs-changed"),
                          ("artifact_held", "actual-native-executable-changed")):
            if key in receipt and receipt[key] is not True:
                receipt["errors"].append(code)
        for key in ("git", "runtime"):
            if key + "_before" in receipt and receipt.get(key + "_before") != receipt.get(key + "_after"):
                receipt["errors"].append("final-" + key + "-identity-changed-or-missing")
        if locked:
            try:
                lock.rmdir()
                receipt["owned_lock_released"] = True
            except OSError:
                receipt["errors"].append("owned-runner-lock-cleanup-refused")
        receipt["passed"] = (not receipt["errors"] and receipt.get("inputs_held") is True and
                             receipt.get("native_inputs_held") is True and receipt.get("artifact_held") is True and
                             receipt.get("reports_held") is True and
                             receipt.get("git_before") == receipt.get("git_after") and
                             receipt.get("runtime_before") == receipt.get("runtime_after") and
                             receipt.get("native_reports", {}).get("passed") is True and
                             receipt.get("owned_lock_released") is True)
        receipt["finished_at_utc"] = now()
        library.write_json(output / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--plan", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--case", choices=recovery.MISSING_APPKIT,
                           help="One exact failed/unexecuted Share630 case, never an accepted case or stress")
    selection.add_argument("--missing-only-share630", action="store_true",
                           help="Compile once; six exact missing cases serially, stopping on the first failure")
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(plan(args.case, missing_only=args.missing_only_share630), indent=2, sort_keys=True))
        return 0
    try:
        receipt = run(ROOT, args.output, args.case, missing_only=args.missing_only_share630)
    except (OSError, ValueError):
        print("AppKit runner refused output ownership; no existing output was modified.", file=sys.stderr)
        return 1
    print(json.dumps({"passed": receipt["passed"], "phase": receipt["phase"], "errors": receipt["errors"]}, sort_keys=True))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
