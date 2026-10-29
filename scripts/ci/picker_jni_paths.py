#!/usr/bin/env python3
"""Run finite, host-domain-specific real embedded-JVM path regressions.

Compilation is not counted as tests. The owning JNI converter is driven directly,
not by an OS picker. Linux uses real invalid-byte entries; macOS requires actual
EILSEQ filesystem evidence plus explicitly controlled unrepresentable paths.
Only fresh source-bound JSON is public evidence; native
executables and the bounded Cargo/JVM log remain private verification outputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re
import sys

import library_tests as library

METHODS = (
    "actual_jni_keeps_non_ascii_and_supplementary_filename_bytes_exact",
    "actual_invalid_byte_file_is_rejected_without_selecting_its_replacement_character_peer",
    "actual_directory_result_raises_io_exception_instead_of_returning_a_lossy_path",
    "actual_save_path_failure_does_not_open_or_overwrite_the_lossy_peer",
    "repeated_mid_array_failure_releases_actual_jni_frame_arrays_and_clears_only_the_expected_error",
)
MACOS_METHODS = (
    "macos_domain::actual_macos_filesystem_rejects_invalid_file_and_directory_with_eilseq_before_jni",
    "macos_domain::controlled_unrepresentable_file_path_raises_io_exception_and_preserves_real_peer",
    "macos_domain::controlled_unrepresentable_directory_path_raises_io_exception_before_path_transport",
    "macos_domain::controlled_unrepresentable_save_path_never_overwrites_real_peer",
    "macos_domain::controlled_mid_array_failure_releases_actual_jni_frames_with_a_real_prefix",
)
MACOS_DOMAIN_MARKER = "NATIVECMPKIT_MACOS_FILENAME_DOMAIN rejected_invalid_file=EILSEQ92 rejected_invalid_directory=EILSEQ92 peer_bytes_preserved=true"
MACOS_CONTROLLED_MARKERS = tuple(
    f"NATIVECMPKIT_MACOS_JNI_CONTROLLED method={method.split('::', 1)[1]} real_invalid_entry=false"
    for method in MACOS_METHODS[1:]
)
JVM_MARKER = "NATIVECMPKIT_ACTUAL_PATH_JVM major=17 checked_jni=true real_filesystem=true"
METHOD_LINE = re.compile(r"^test jni_path_tests::([a-z0-9_:]+) \.\.\. (.*)$")


def expected_methods(host: str, focus: str = "all") -> tuple[str, ...]:
    if host not in {"Linux", "Darwin", "Windows"}:
        raise ValueError("JNI fixture requires an explicit supported real JVM host")
    if focus == "macos-domain":
        if host != "Darwin":
            raise ValueError("macos-domain recovery requires the actual macOS filesystem/JVM host")
        return MACOS_METHODS
    if focus != "all":
        raise ValueError("Unknown finite JNI test focus")
    return ((METHODS[0],) + MACOS_METHODS if host == "Darwin" else
            METHODS[:1] if host == "Windows" else METHODS)


def failure_details(log: str) -> dict:
    """Allowlisted outcomes/panic coordinates/OS error numbers, never raw Cargo bodies."""
    if len(log.encode("utf-8")) > 8 * 1024 ** 2:
        return {"diagnostic_too_large": True}
    cases, coordinates, errors, current = [], [], [], None
    for line in log.splitlines():
        method = METHOD_LINE.match(line)
        if method:
            current = method[1] if method[1] in METHODS + MACOS_METHODS else None
            status = method[2]
        else:
            status = line
        if current is not None and status in {"ok", "FAILED", "ignored"}:
            cases.append({"name": current, "status": {"ok": "passed", "FAILED": "failed", "ignored": "ignored"}[status]})
            current = None
        location = re.search(r"panicked at (src/(?:jni_path_tests|lib|path_encoding|registry)\.rs):(\d+):(\d+)", line)
        if location and len(coordinates) < 16:
            coordinates.append({"path": location[1], "line": int(location[2]), "column": int(location[3])})
        error = re.search(r"Os \{ code: (\d+), kind: ([A-Za-z]+),", line)
        if error and len(errors) < 16:
            errors.append({"code": int(error[1]), "rust_kind": error[2]})
    return {"actual_method_outcomes": cases, "actual_jdk17_marker_observed": JVM_MARKER in log,
            "rust_panic_coordinates": coordinates, "native_os_error_numbers": errors,
            "scope": "Failure triage only; no raw panic/data/environment/credentials or passing-gate substitution"}


def review_log(log: str, host: str, focus: str = "all") -> dict:
    if len(log.encode("utf-8")) > 8 * 1024 ** 2:
        raise ValueError("Cargo/JVM diagnostic exceeds bounded reviewer input")
    ordered = expected_methods(host, focus)
    expected = set(ordered)
    results, current = {}, None
    artifacts, finished = [], []
    for line in log.splitlines():
        if line.startswith("{"):
            entry = json.loads(line)
            if not isinstance(entry, dict):
                raise ValueError("Cargo message must be a JSON object")
            if entry.get("reason") == "build-finished":
                finished.append(entry.get("success"))
            if (entry.get("reason") == "compiler-artifact" and entry.get("target", {}).get("name") == "calf_filepicker_native"
                    and entry.get("profile", {}).get("test") is True and entry.get("executable")):
                artifacts.append(entry)
        match = METHOD_LINE.match(line)
        if match:
            if current is not None or match[1] not in expected or match[1] in results:
                raise ValueError("Duplicate/foreign/unfinished actual Rust method")
            current = match[1]
            status = match[2]
        else:
            status = line
        if current is not None and status == "ok":
            results[current] = "passed"
            current = None
        elif current is not None and status in {"FAILED", "ignored"}:
            raise ValueError("Required actual JNI method failed or was ignored")
    summaries = re.findall(r"^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;", log, re.M)
    if (set(results) != expected or current is not None or len(summaries) != 1 or
            tuple(map(int, summaries[0][:4])) != (len(expected), 0, 0, 0) or
            len(artifacts) != 1 or finished != [True]):
        raise ValueError("Actual nonzero Rust method outcomes/compiler executable do not match the finite JNI scope")
    if log.count(JVM_MARKER) != 1 or re.search(r"WARNING in native method|JNI DETECTED ERROR|FATAL ERROR in native method|JNI local refs:", log):
        raise ValueError("Actual JDK17/checked-JNI marker missing/duplicate or native checker reports errors")
    observed_domain = re.findall(r"NATIVECMPKIT_MACOS_FILENAME_DOMAIN[^\n]*", log)
    observed_controlled = re.findall(r"NATIVECMPKIT_MACOS_JNI_CONTROLLED[^\n]*", log)
    if (observed_domain != ([MACOS_DOMAIN_MARKER] if host == "Darwin" else []) or
            sorted(observed_controlled) != (sorted(MACOS_CONTROLLED_MARKERS) if host == "Darwin" else [])):
        raise ValueError("Actual filesystem-domain/controlled-input markers must match exactly; no invalid-entry or skipped-test substitution")
    return {"testcases": [{"classname": "jni_path_tests", "name": method, "status": "passed",
                           "coverage_kind": ("real-macos-filesystem-EILSEQ-boundary" if method == MACOS_METHODS[0] else
                                             "controlled-unrepresentable-path-real-JNI" if method in MACOS_METHODS else
                                             "real-filesystem-real-JNI")} for method in ordered],
            "tests": len(expected), "failures": 0, "errors": 0, "skipped": 0,
            "filtered_unchanged_tests": int(summaries[0][4]), "actual_jvm_major": 17, "checked_jni": True,
            "actual_invalid_byte_entries_required": host == "Linux",
            "macos_actual_filesystem_domain_verified": host == "Darwin",
            "controlled_unrepresentable_path_tests": 4 if host == "Darwin" else 0,
            "compiler_artifact": artifacts[0]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--focus", choices=("all", "macos-domain"), default="all",
                        help="macos-domain recovers only the failed filesystem/negative JNI cases, not accepted Unicode/Compose")
    args = parser.parse_args()
    try:
        expected_methods(platform.system(), args.focus)
    except ValueError as error:
        parser.error(str(error))
    root = library.ROOT
    requested_output = root / args.output
    output = requested_output.resolve()
    allowed = root / "build/ci-verification"
    if (output == allowed or not output.is_relative_to(allowed) or output.exists() or
            any(p.is_symlink() for p in (requested_output, *requested_output.parents))):
        parser.error("Require a new owned output directory below build/ci-verification")
    output.mkdir(parents=True)
    before = library.snapshot_inputs(root)
    library.write_json(output / "inputs-before.json", before)
    revision = library.git_revision(root)
    context = library.runtime_context.capture()
    if context["source_revision"] != revision:
        raise ValueError("Source revision changed while capturing actual JNI runtime")
    library.write_json(output / "runtime.json", context)
    method_filter = "jni_path_tests::macos_domain" if args.focus == "macos-domain" else "jni_path_tests"
    command = ["cargo", "test", "--manifest-path", "calf-file-picker/native/Cargo.toml", "--locked", "--jobs", "1",
               "--message-format=json", method_filter, "--", "--test-threads=1", "--nocapture"]
    execution = library.execute(root, command, output / "cargo.private.log", 600, 8192)
    after = library.snapshot_inputs(root)
    library.write_json(output / "inputs-after.json", after)
    receipt = {"source_revision": revision, "source_tree_dirty": context["source_tree_dirty"],
               "command": command, "execution": execution, "selected_inputs": len(before),
               "runtime_receipt_sha256": library.sha256(output / "runtime.json"),
               "inputs_before_sha256": library.input_digest(before), "inputs_after_sha256": library.input_digest(after),
               "held_inputs": before == after, "host": platform.system(), "passed": False,
               "test_focus": args.focus, "complete_suite_requested": False,
               "complete_jni_path_scope_requested": args.focus == "all",
               "scope": "Actual JNI selected-path converter/weak-array collection. Linux negatives require actual invalid-byte entries; macOS requires actual file/directory EILSEQ92 boundary plus four explicitly controlled unrepresentable PathBuf JNI cases with real valid peers, NOT actual invalid selected files. macos-domain omits accepted Unicode/Compose/other hosts. No OS picker selection/full ABI/consumer/native-parent/release certification"}
    try:
        log = output / "cargo.private.log"
        if log.stat().st_size > 8 * 1024 ** 2:
            raise ValueError("Cargo/JVM diagnostic exceeds bounded reviewer input")
        body = log.read_text(encoding="utf-8")
        receipt["failure_diagnostics"] = failure_details(body) if execution["exit_code"] != 0 else None
        result = review_log(body, platform.system(), args.focus)
        artifact = result.pop("compiler_artifact")
        declared_executable = Path(artifact["executable"])
        executable = declared_executable.resolve(strict=True)
        if (not executable.is_relative_to(root / "calf-file-picker/native/target") or
                any(p.is_symlink() for p in (declared_executable, *declared_executable.parents))):
            raise ValueError("Actual test executable must remain within this crate's owned target tree")
        result["native_test_executable_sha256"] = library.sha256(executable)
        receipt.update(result)
        receipt["passed"] = execution["exit_code"] == 0 and not execution.get("stop_reason") and before == after and library.git_revision(root) == revision
    except (OSError, ValueError, json.JSONDecodeError) as error:
        receipt["review_error"] = type(error).__name__ + ": " + str(error)
    library.write_json(output / "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("source_revision", "host", "execution", "passed", "scope", "review_error", "failure_diagnostics")
                      if key in receipt}, indent=2))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
