#!/usr/bin/env python3
"""Two new private-entry/parser methods in a genuine JDK17, never an OS picker.

This branch compiles once into a fresh owned macOS arm64 target and executes each
fully qualified method separately. There is no multi-filter assumption, old JNI
method replay, accepted report fallback, package publication or GUI operation.
Only allowlisted JSON is public; bounded native output/executables stay private.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time

import library_tests as library

FOCUS = "actual-jvm2"
TARGET = "aarch64-apple-darwin"
METHODS = (
    "jni_path_tests::actual_jni_pending_primary_stops_parsers_results_and_picker_entry_body",
    "jni_path_tests::actual_jni_optional_nulls_and_unicode_parser_arguments_keep_their_meaning",
)
JVM_MARKER = "NATIVECMPKIT_ACTUAL_PATH_JVM major=17 checked_jni=true real_filesystem=true"
METHOD_MARKERS = (
    "NATIVECMPKIT_ACTUAL_JNI_GUARD same_primary=true picker_entry_body=0",
    "NATIVECMPKIT_ACTUAL_JNI_PARSERS unicode_exact=true optional_nulls=true",
)
MAX_LOG_BYTES = 8 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
DISK_RESERVE_BYTES = 8192 * 1024 * 1024
NATIVE_BUDGET_SECONDS = 600
WORKFLOW = ".github/workflows/build-native-libs.yml"
# Reviewed R3 endpoints, not a global registered/current source enrollment map.
R3_SOURCE_SHA256 = {
    "calf-file-picker/native/Cargo.lock": "fa8c3f7f44ca315bc1aad51e4f7021ba503b3aae3c2f36fb7cd6316268ddea13",
    "calf-file-picker/native/Cargo.toml": "2f32946e7699e9e647c818812bd3e10e04e1eddc9d2325c84a191fcbdcf8f755",
    "calf-file-picker/native/src/jni_path_tests.rs": "7671d22565ad37783a3734142b99016de57d59599d0121ca94d20a5eaaed8bd7",
    "calf-file-picker/native/src/lib.rs": "9002e8d901e138d537ac2520d3c49925b298eaa58f4223d890d36c43059469b0",
    "calf-file-picker/native/src/macos_parent.rs": "b60cbed17e8a38229391aa9a371657b41b53935dbb8246287eff771ca4af38ae",
    "calf-file-picker/native/src/macos_release_slots.rs": "70ed4377ce37dc3f6fd7e35a970c2cdb0de3ff10a1ce2c34a83fabd068103ac5",
    "calf-file-picker/native/src/parent_retain_slot.rs": "87f1fe1011c2115e07491ed430c628b9a01e8c664ec161cbf3b7c3fd49eec109",
    "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/NativeFilePickerBridge.kt": "99bca84680d8078832317f9165abc5f69d36562164c4232144a6bca1f265ad6c",
    "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/platform/PlatformFilePicker.kt": "5b92a689b8fb29ecaec4fbd9c99c88a5a5c1699d459cee75d73a9cbc44c18d88",
}

OWNING_INPUTS = (
    "scripts/ci/picker_jni_paths.py", "scripts/ci/picker_jni_actual_jvm2.py",
    "scripts/ci/test_picker_jni_paths.py", "scripts/ci/test_picker_jni_actual_jvm2.py",
    "scripts/ci/library_tests.py", "scripts/ci/runtime_context.py", "rust-toolchain.toml",
    WORKFLOW,
)
SCOPE = (
    "Only two separately exact private-entry/parser methods in genuine embedded JDK17. "
    "The inherited real_filesystem=true VM marker is NOT filesystem coverage for these2. "
    "Each process owns its local-frame test operation; no shared VM across processes, "
    "VM shutdown/epoch/global-ref/memory-lifecycle proof, picker opening/selection, "
    "parent acquisition/CFRetain/release completion, AppKit fault coverage, old JNI "
    "filesystem-negative acceptance, full ABI/security/consumer or release certification."
)


class Refusal(ValueError):
    """Constant, public reason code; never include native output or environment."""


class NativeBudget:
    """One immutable600s deadline shared by compile, two inventories and two runs."""
    def __init__(self, clock=None):
        self.clock = time.monotonic if clock is None else clock
        self.started = self.clock()

    def remaining(self) -> int:
        elapsed = self.clock() - self.started
        if not 0 <= elapsed < NATIVE_BUDGET_SECONDS - 1:
            raise Refusal("shared-native-deadline-exhausted-or-clock-invalid")
        return int(NATIVE_BUDGET_SECONDS - elapsed)

    def elapsed(self) -> float:
        elapsed = self.clock() - self.started
        if not 0 <= elapsed <= NATIVE_BUDGET_SECONDS:
            raise Refusal("shared-native-deadline-exhausted-or-clock-invalid")
        return round(elapsed, 6)


def expected_methods(host: str) -> tuple[str, ...]:
    if host != "Darwin":
        raise Refusal("actual-jvm2-requires-real-macos-host")
    return METHODS


def checked_method(method: str) -> int:
    if method not in METHODS:
        raise Refusal("unknown-or-broad-actual-jvm2-selector")
    return METHODS.index(method)


def compile_command(root: Path, target: Path) -> list[str]:
    return ["cargo", "test", "--manifest-path", "calf-file-picker/native/Cargo.toml",
            "--locked", "--jobs", "1", "--no-run", "--lib", "--target", TARGET,
            "--target-dir", target.relative_to(root).as_posix(), "--message-format=json"]


def exact_command(executable: Path, method: str, *, inventory: bool = False) -> list[str]:
    checked_method(method)
    return [executable.as_posix(), method, "--exact", *( ["--list"] if inventory else
            ["--nocapture", "--test-threads=1"])]


def _bounded_text(body: str) -> None:
    if not isinstance(body, str) or len(body.encode("utf-8")) > MAX_LOG_BYTES:
        raise Refusal("native-diagnostic-review-limit")


def review_compile(body: str, root: Path) -> dict:
    _bounded_text(body)
    artifacts, finished = [], []
    for line in body.splitlines():
        if line.startswith("{"):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as error:
                raise Refusal("malformed-cargo-compile-message") from error
            if not isinstance(entry, dict):
                raise Refusal("nonobject-cargo-compile-message")
            if entry.get("reason") == "build-finished":
                finished.append(entry.get("success"))
            if entry.get("reason") == "compiler-artifact" and entry.get("executable"):
                artifacts.append(entry)
        if re.match(r"^(?:test |running [0-9]+ tests?\b)", line) or "NATIVECMPKIT_" in line:
            raise Refusal("compile-only-phase-must-not-execute-tests")
    if len(artifacts) != 1 or finished != [True]:
        raise Refusal("one-successful-held-test-compile-required")
    artifact = artifacts[0]
    target, profile = artifact.get("target"), artifact.get("profile")
    if (not isinstance(target, dict) or not isinstance(profile, dict) or
            target.get("name") != "calf_filepicker_native" or
            target.get("src_path") != (root / "calf-file-picker/native/src/lib.rs").as_posix() or
            profile.get("test") is not True or artifact.get("fresh") is not False or
            not isinstance(artifact.get("executable"), str)):
        raise Refusal("foreign-nontest-or-cached-cargo-executable")
    return artifact


def review_inventory(body: str, method: str) -> dict:
    checked_method(method)
    _bounded_text(body)
    lines = [line for line in body.splitlines() if line]
    if lines != [method + ": test", "1 test, 0 benchmarks"]:
        raise Refusal("exact-one-name-inventory-required")
    return {"listed_method": method, "listed_tests": 1, "executed_tests": 0,
            "enabled_or_passed_inferred_from_listing": False}


def review_method(body: str, method: str) -> dict:
    index = checked_method(method)
    _bounded_text(body)
    current, passed, observations = None, [], []
    for line in body.splitlines():
        observations.extend(re.findall(r"NATIVECMPKIT_[A-Z0-9_]+[^\r\n]*", line))
        if line.startswith("test result:") and passed != [method]:
            raise Refusal("successful-summary-before-owned-method-return")
        match = re.fullmatch(r"test ([^\r\n]+?) \.\.\. (.*)", line)
        if match:
            if current is not None or match[1] != method or passed:
                raise Refusal("duplicate-foreign-or-unfinished-exact-method")
            current, status = match[1], match[2]
        else:
            status = line
        if current is not None and status == "ok":
            if observations != [JVM_MARKER, METHOD_MARKERS[index]]:
                raise Refusal("method-pass-before-own-jvm-observation")
            passed.append(current)
            current = None
        elif current is not None and status in {"FAILED", "ignored"}:
            raise Refusal("required-exact-method-failed-or-ignored")
        if line.startswith("{"):
            raise Refusal("test-phase-cannot-substitute-cargo-json")
    summaries = [line for line in body.splitlines() if line.startswith("test result:")]
    summary = re.fullmatch(r"test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; "
                           r"([0-9]+) filtered out; finished in ([0-9]+(?:\.[0-9]+)?)s",
                           summaries[0]) if len(summaries) == 1 else None
    running = re.findall(r"^running ([0-9]+) tests?$", body, re.M)
    markers = re.findall(r"NATIVECMPKIT_[A-Z0-9_]+[^\r\n]*", body)
    if (passed != [method] or current is not None or summary is None or running != ["1"]):
        raise Refusal("nonzero-one-method-pass-after-cleanup-required")
    if (markers != [JVM_MARKER, METHOD_MARKERS[index]] or
            re.search(r"WARNING in native method|JNI DETECTED ERROR|FATAL ERROR in native method|"
                      r"JNI local refs:|R3 owned JNI (?:exception|frame) cleanup failed:", body)):
        raise Refusal("exact-process-jdk17-observation-or-checked-jni-cleanup-refusal")
    return {"classname": "jni_path_tests", "name": method.split("::", 1)[1], "status": "passed",
            "coverage_kind": ("real-JDK17-pending-primary-private-entry" if index == 0 else
                              "real-JDK17-optional-null-and-supplementary-unicode-private-parser"),
            "actual_vm_major": 17, "checked_jni": True, "fresh_process_vm_marker_count": 1,
            "observed_filtered_tests": int(summary[1]), "filesystem_operations_verified": False,
            "vm_shutdown_verified": False, "native_parent_or_release_completion_verified": False}


def _stat9(value) -> tuple:
    return tuple(getattr(value, key) for key in ("st_dev", "st_ino", "st_mode", "st_nlink",
                 "st_size", "st_mtime_ns", "st_ctime_ns", "st_uid", "st_gid"))


def executable_identity(executable: Path, target: Path) -> dict:
    if (not executable.is_absolute() or ".." in executable.parts or
            executable.parent != target / TARGET / "debug/deps" or
            not re.fullmatch(r"calf_filepicker_native-[a-f0-9]{8,64}", executable.name) or
            any(path.is_symlink() for path in (executable, *executable.parents))):
        raise Refusal("test-executable-outside-owned-target")
    with os.fdopen(os.open(executable, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
        before = os.fstat(handle.fileno())
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
                not 0 < before.st_size <= MAX_EXECUTABLE_BYTES or not before.st_mode & 0o111):
            raise Refusal("one-bounded-owned-regular-executable-required")
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
        after = os.fstat(handle.fileno())
        if _stat9(before) != _stat9(after) or _stat9(after) != _stat9(executable.lstat()):
            raise Refusal("test-executable-changed-during-descriptor-read")
    return {"target_relative_path": executable.relative_to(target).as_posix(),
            "sha256": digest.hexdigest(), "fd_stat9": list(_stat9(after))}


def append_capture(handle, chunk: bytes, captured: int) -> tuple[int, bool]:
    available = MAX_LOG_BYTES - captured
    retained = chunk[:available]
    if handle.write(retained) != len(retained):
        raise Refusal("private-capture-short-write")
    return captured + len(retained), len(chunk) <= available


def observe_exited_group(pid: int) -> str:
    """Read-only observation only: never terminate a post-exit/reused group."""
    try:
        os.killpg(pid, 0)
    except ProcessLookupError:
        return "absent"
    except OSError:
        return "unknown"
    return "present"


def cleanup_live_owned_leader(process) -> dict:
    """Signals only a still-owned unreaped live leader's original session."""
    result = {"term_requested": False, "kill_requested": False}
    if process.poll() is not None:
        result["status"] = "leader-already-exited-no-signals"
        return result
    try:
        if os.getsid(process.pid) != process.pid:
            result["status"] = "live-session-ownership-unknown-no-signals"
            return result
        os.killpg(process.pid, signal.SIGTERM)
        result["term_requested"] = True
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            # Timeout leaves this direct child unreaped; its PID cannot be reused.
            # Recheck the live original session before the only escalation.
            if process.poll() is not None:
                result["status"] = "leader-exited-after-term"
                return result
            if os.getsid(process.pid) != process.pid:
                result["status"] = "live-session-ownership-unknown-no-escalation"
                return result
            os.killpg(process.pid, signal.SIGKILL)
            result["kill_requested"] = True
            process.wait(timeout=30)
        result["status"] = "owned-leader-reaped"
    except (OSError, subprocess.TimeoutExpired):
        result["status"] = "owned-live-cleanup-not-established"
    return result


def owned_phase(root: Path, command: list[str], log_path: Path, receipt_path: Path,
                budget: NativeBudget) -> dict:
    """NEW branch only: bounded private capture and factual, refusal-first custody.

    Safety cleanup can exceed an exhausted deadline; such a phase NEVER passes.
    Post-exit presence/unknown refuses without signalling a potentially foreign
    reused group. The snapshot/source workflow is not a trusted-builder sandbox.
    """
    result = {"command": command, "started": False, "exit_code": None,
              "captured_bytes": 0, "capture_complete": False,
              "post_exit_group_state": "not-observed", "stop_reason": None}
    process, capture, selector, primary, eof = None, None, None, None, False
    capture_digest = hashlib.sha256()
    started = time.monotonic()
    try:
        budget.remaining()
        if shutil.disk_usage(root).free < DISK_RESERVE_BYTES:
            result["stop_reason"] = "disk-reserve-unavailable-command-not-started"
        else:
            capture = os.fdopen(os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb")
            process = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            result.update(started=True, owned_leader_pid=process.pid)
            os.set_blocking(process.stdout.fileno(), False)
            selector = selectors.DefaultSelector()
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                try:
                    budget.remaining()
                except Refusal:
                    result["stop_reason"] = "shared-native-deadline-exhausted-or-clock-invalid"
                    break
                if shutil.disk_usage(root).free < DISK_RESERVE_BYTES:
                    result["stop_reason"] = "disk-reserve-reached"
                    break
                exited = process.poll() is not None
                events = selector.select(0 if exited else min(0.2, budget.remaining()))
                if events:
                    chunk = os.read(process.stdout.fileno(), 64 * 1024)
                    if chunk:
                        previous_bytes = result["captured_bytes"]
                        result["captured_bytes"], retained_all = append_capture(capture, chunk, previous_bytes)
                        capture_digest.update(chunk[:result["captured_bytes"] - previous_bytes])
                        if not retained_all:
                            result["stop_reason"] = "private-capture-limit-refused"
                            break
                    else:
                        eof = True
                if exited:
                    # Drain immediately available bytes only; no inherited-pipe
                    # wait or speculative cleanup after this leader was reaped.
                    if eof or not events:
                        break
                elif eof:
                    time.sleep(0.01)
    except BaseException as error:
        primary = error
        result["primary_error_type"] = type(error).__name__
        result["stop_reason"] = "owned-phase-primary-error"
    finally:
        def secondary(error):
            nonlocal primary
            result.setdefault("cleanup_error_types", []).append(type(error).__name__)
            if primary is None:
                primary = error
        if process is not None:
            try:
                if process.poll() is None:
                    result["live_cleanup"] = cleanup_live_owned_leader(process)
                result["exit_code"] = process.poll()
                if result["exit_code"] is not None:
                    result["post_exit_group_state"] = observe_exited_group(process.pid)
                else:
                    result["post_exit_group_state"] = "leader-still-live"
            except BaseException as error:
                secondary(error)
            if process.stdout is not None:
                try:
                    process.stdout.close()
                except BaseException as error:
                    secondary(error)
        if selector is not None:
            try:
                selector.close()
            except BaseException as error:
                secondary(error)
        if capture is not None:
            try:
                capture.flush()
                shape = os.fstat(capture.fileno())
                if (not stat.S_ISREG(shape.st_mode) or shape.st_nlink != 1 or
                        shape.st_size != result["captured_bytes"] or
                        _stat9(shape) != _stat9(log_path.lstat())):
                    raise Refusal("private-capture-descriptor-custody")
                result["private_capture_sha256"] = capture_digest.hexdigest()
                result["private_capture_fd_stat9"] = list(_stat9(shape))
            except BaseException as error:
                secondary(error)
            finally:
                try:
                    capture.close()
                except BaseException as error:
                    secondary(error)
        result["capture_complete"] = eof and result["stop_reason"] is None and primary is None
        result["elapsed_seconds"] = round(time.monotonic() - started, 6)
        try:
            library.write_json(receipt_path, result)
        except BaseException as error:
            if primary is None:
                primary = error
    if primary is not None:
        raise primary
    return result


def require_phase_success(result: dict, budget: NativeBudget) -> None:
    budget.elapsed()
    if (result.get("started") is not True or type(result.get("exit_code")) is not int or
            result["exit_code"] != 0 or result.get("stop_reason") is not None or
            result.get("capture_complete") is not True or result.get("post_exit_group_state") != "absent"):
        raise Refusal("exact-owned-phase-exit-capture-or-group-refusal")


def source_snapshot(root: Path) -> dict:
    result = library.snapshot_inputs(root)
    workflow = library.safe_path(root, WORKFLOW)
    before = workflow.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise Refusal("workflow-is-not-one-owned-regular-input")
    result[WORKFLOW] = library.sha256(workflow)
    if _stat9(before) != _stat9(workflow.lstat()):
        raise Refusal("workflow-changed-during-source-capture")
    if any(relative not in result for relative in OWNING_INPUTS):
        raise Refusal("missing-actual-jvm2-owning-input")
    if any(result.get(relative) != expected for relative, expected in R3_SOURCE_SHA256.items()):
        raise Refusal("actual-jvm2-requires-exact-reviewed-r3-source")
    return result


def require_runtime(context: dict, revision: str) -> None:
    if (context.get("source_revision") != revision or context.get("source_tree_dirty") is not False or
            context.get("host", {}).get("system") != "Darwin" or
            context.get("host", {}).get("architecture") != "arm64" or
            context.get("java", {}).get("major") != 17 or
            context.get("rust", {}).get("release") != "1.98.0" or
            context.get("rust", {}).get("host") != TARGET or
            not re.fullmatch(r"[a-f0-9]{64}", context.get("compiler_runtime_fingerprint", ""))):
        raise Refusal("actual-jvm2-runtime-revision-clean-host-jdk-rust-mismatch")


def read_private_log(path: Path, execution: dict) -> str:
    if any(value.is_symlink() for value in (path, *path.parents)):
        raise Refusal("private-capture-size-or-path-custody")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
        shape = os.fstat(handle.fileno())
        if (not stat.S_ISREG(shape.st_mode) or shape.st_nlink != 1 or
                shape.st_size != execution["captured_bytes"] or shape.st_size > MAX_LOG_BYTES or
                list(_stat9(shape)) != execution.get("private_capture_fd_stat9")):
            raise Refusal("private-capture-size-or-path-custody")
        payload = handle.read(MAX_LOG_BYTES + 1)
        if (len(payload) != shape.st_size or _stat9(shape) != _stat9(os.fstat(handle.fileno())) or
                _stat9(shape) != _stat9(path.lstat()) or
                hashlib.sha256(payload).hexdigest() != execution.get("private_capture_sha256")):
            raise Refusal("private-capture-payload-changed-after-owned-phase")
    try:
        return payload.decode("utf-8")
    except UnicodeError as error:
        raise Refusal("private-capture-not-valid-utf8") from error


def run(output_argument: Path) -> int:
    expected_methods(platform.system())
    root = library.ROOT
    requested = root / output_argument
    output, allowed = requested.resolve(), root / "build/ci-verification"
    if (output == allowed or not output.is_relative_to(allowed) or output.exists() or
            any(path.is_symlink() for path in (requested, *requested.parents))):
        raise Refusal("new-owned-output-below-ci-verification-required")
    output.mkdir(parents=True, mode=0o700)
    receipt = {"schema_version": 1, "test_focus": FOCUS, "passed": False,
               "required_methods": list(METHODS), "testcases": [], "scope": SCOPE,
               "complete_suite_requested": False, "complete_jni_path_scope_requested": False,
               "native_operation_budget_seconds": NATIVE_BUDGET_SECONDS,
               "native_processes_requested": 2, "multi_filter_support_assumed": False,
               "tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    before, revision, context, budget = None, None, None, None
    stage = "source-and-runtime-before"
    try:
        before = source_snapshot(root)
        revision = library.git_revision(root)
        context = library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        require_runtime(context, revision)
        library.write_json(output / "inputs-before.json", before)
        library.write_json(output / "runtime-before.json", context)
        receipt.update(source_revision=revision, source_tree_dirty=False,
                       selected_inputs=len(before), inputs_before_sha256=library.input_digest(before),
                       runtime_before_sha256=library.sha256(output / "runtime-before.json"))
        target = output / "native-build.private"
        if target.exists():
            raise Refusal("fresh-owned-cargo-target-required")
        target.mkdir(mode=0o700)
        budget = NativeBudget()
        stage = "compile-only"
        execution = owned_phase(root, compile_command(root, target), output / "compile.private.log",
                                output / "compile-receipt.json", budget)
        require_phase_success(execution, budget)
        artifact = review_compile(read_private_log(output / "compile.private.log", execution), root)
        executable = Path(artifact["executable"])
        identity = executable_identity(executable, target)
        receipt["compiler_executable"] = identity
        receipt["compile_only_executed_tests"] = 0
        for index, method in enumerate(METHODS, 1):
            for listing in (True, False):
                stage = ("inventory-" if listing else "method-") + str(index)
                if executable_identity(executable, target) != identity or source_snapshot(root) != before:
                    raise Refusal("source-or-executable-changed-before-exact-phase")
                log_path = output / (stage + ".private.log")
                execution = owned_phase(root, exact_command(executable.relative_to(root), method, inventory=listing),
                                        log_path, output / (stage + "-receipt.json"), budget)
                require_phase_success(execution, budget)
                body = read_private_log(log_path, execution)
                if executable_identity(executable, target) != identity or source_snapshot(root) != before:
                    raise Refusal("source-or-executable-changed-after-exact-phase")
                if listing:
                    receipt.setdefault("inventories", []).append(review_inventory(body, method))
                else:
                    receipt["testcases"].append(review_method(body, method))
                    receipt["tests"] += 1
        stage = "final-source-runtime-and-deadline"
        after = source_snapshot(root)
        context_after = library.runtime_context.capture(expected_arch="arm64", apple=True, require_clean=True)
        require_runtime(context_after, revision)
        library.write_json(output / "inputs-after.json", after)
        library.write_json(output / "runtime-after.json", context_after)
        receipt.update(inputs_after_sha256=library.input_digest(after), held_inputs=before == after,
                       runtime_after_sha256=library.sha256(output / "runtime-after.json"),
                       held_runtime_identity=context["compiler_runtime_fingerprint"] == context_after["compiler_runtime_fingerprint"])
        if (before != after or not receipt["held_runtime_identity"] or
                library.git_revision(root) != revision or executable_identity(executable, target) != identity or
                len(receipt["testcases"]) != 2 or len(receipt.get("inventories", [])) != 2):
            raise Refusal("final-held-source-runtime-executable-and-exact-two-required")
        receipt["native_operation_elapsed_seconds"] = budget.elapsed()
        receipt["passed"] = True
    except Exception as error:
        receipt.update(failed_stage=stage, error_type=type(error).__name__,
                       reason_code=str(error) if isinstance(error, Refusal) else "verification-error-details-private")
    finally:
        # Retain a separate passive failure readback without replacing the primary
        # stage/error. There is no failed-method replay or source repair here.
        if not receipt["passed"] and before is not None:
            try:
                after = source_snapshot(root)
                library.write_json(output / "inputs-after.json", after)
                receipt.update(held_inputs=before == after, inputs_after_sha256=library.input_digest(after))
            except Exception as error:
                receipt["failure_source_readback_error_type"] = type(error).__name__
        library.write_json(output / "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("source_revision", "test_focus", "tests", "passed",
                       "failed_stage", "reason_code", "scope") if key in receipt}, indent=2))
    return 0 if receipt["passed"] else 1
