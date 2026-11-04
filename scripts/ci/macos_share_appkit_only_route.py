# SPDX-License-Identifier: Apache-2.0
"""Existing Share profile: AppKit6 once, then same-job owning-result reference.

No JNI/Gradle/native command is executed here. The preceding unchanged workflow
step owns actual Rust/AppKit execution and cleanup. This reader holds its exact
same-job context, source/runtime/PID/report custody; no fresh JVM XML or trusted
builder attestation is inferred. Original failed630/650 and accepted JNI3 stay.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import time
import xml.etree.ElementTree as ET

import macos_share_appkit_only_source_projection as source

PROFILE = "macos-share-missing-lifecycle"
ENTRY_FOCUS = "macos-share-timeout-retention-recovery"  # Existing workflow entry; JNI execution retired.
EFFECTIVE_FOCUS = "macos-share-appkit6-only-recovery"
MODULE = "calf-share"
SLOT = "desktop-macos-arm64"
OUTPUT = "build/ci-verification/" + SLOT
PARENT = OUTPUT + "-appkit"
REPORT_PARENT = "build/ci-verification/share-appkit-native"
CLASS = "com.mohamedrejeb.calf.share.native.AppKitLifecycle"
SUITE = "NativeCmpKitAppKitLifecycle"
CASES = ("missing_content_view", "real_picker_cancel", "controlled_picker_dismissal",
         "controlled_success_duplicate_late", "controlled_service_failure", "bounded_concurrent_requests")
ACCEPTED_JNI = ("independentRealNativeOwnersRejectOverlapWithoutReplacingTheRetainedRequest",
                "cancellingRetainedAppKitRequestFreesOwnersAndDoesNotOccupySingleCoroutineWorker",
                "realNativeTimeoutReportsOnceWithoutFallbackAndAllowsFreshRequestAfterMainCleanup")
WITNESS = "actual-native=true live=0 registry=0 cleanup=true controlled-callbacks-not-recipient=true"
MAX_JSON = 4 * 1024 * 1024
MAX_XML = 32768
MAX_MAP = 4096
FRESHNESS_SLOP = 2_000_000_000
MAX_FINISHED_AGE = 300_000_000_000
MAX_JOB_SPAN = 90 * 60 * 1_000_000_000
IDENTITY_KEYS = ("device", "inode", "mode", "size", "mtime_ns", "sha256")


def need(value, code):
    source.need(value, code)


def _context(value):
    constants = {"repository": "Apdelrahman1911/nativeCmpkit", "workflow": "NativeCmpKit verification",
                 "job": "library-tests", "profile": PROFILE, "slot": SLOT,
                 "entry_focus": ENTRY_FOCUS, "effective_focus": EFFECTIVE_FOCUS}
    need(type(value) is dict and set(value) == {*constants, "run_id", "run_attempt", "source_revision", "ref"} and
         all(value.get(key) == wanted for key, wanted in constants.items()) and
         all(type(value.get(key)) is str for key in ("run_id", "run_attempt", "source_revision", "ref")) and
         re.fullmatch(r"[1-9][0-9]{0,19}", value["run_id"]) and
         re.fullmatch(r"[1-9][0-9]{0,5}", value["run_attempt"]) and
         re.fullmatch(r"[0-9a-f]{40}", value["source_revision"]) and
         re.fullmatch(r"refs/heads/development/[A-Za-z0-9][A-Za-z0-9._/-]{0,240}", value["ref"]) and
         ".." not in value["ref"] and "//" not in value["ref"] and not value["ref"].endswith("/"),
         "complete-same-AppKit-workflow-job-identity-required")
    return value


def workflow_context():
    """Only actual existing-job identifiers; missing/foreign inputs are refusal."""
    need(os.environ.get("GITHUB_ACTIONS") == "true" and
         os.environ.get("GITHUB_REPOSITORY") == "Apdelrahman1911/nativeCmpkit" and
         os.environ.get("GITHUB_WORKFLOW") == "NativeCmpKit verification" and
         os.environ.get("GITHUB_JOB") == "library-tests" and
         os.environ.get("SLOT") == SLOT and os.environ.get("SUITE") == "desktop" and
         os.environ.get("TEST_MODULES") == MODULE and os.environ.get("TEST_FOCUS") == ENTRY_FOCUS and
         os.environ.get("NATIVECMPKIT_NATIVE_UI_TESTS") == "true", "exact-existing-AppKit-workflow-job-required")
    return _context({"repository": "Apdelrahman1911/nativeCmpkit", "workflow": "NativeCmpKit verification",
                     "job": "library-tests", "run_id": os.environ.get("GITHUB_RUN_ID", ""),
                     "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", ""),
                     "source_revision": os.environ.get("GITHUB_SHA", ""), "ref": os.environ.get("GITHUB_REF", ""),
                     "profile": PROFILE, "slot": SLOT, "entry_focus": ENTRY_FOCUS, "effective_focus": EFFECTIVE_FOCUS})


def plan(root: Path):
    expected = source.validate_current_sources(root)
    return {"schema_version": 1, "suite": "desktop", "profile": PROFILE,
            "explicit_test_focus": ENTRY_FOCUS, "effective_test_focus": EFFECTIVE_FOCUS,
            "complete_suite_requested": False, "explicit_module_subset": [MODULE],
            "expected": [{"module": MODULE, "project": ":calf-share", "task": "native-AppKit-standalone",
                          "test_kind": "Rust-AppKit-not-JVM", "report_directory": PARENT + "/cases", "required_testcases":
                          [{"classname": CLASS, "name": name} for name in CASES]}],
            "native_command_owned_by_prior_workflow_step": ["python3", "scripts/ci/macos_share_appkit_lifecycle.py",
                                                           "--missing-only-share630", "--output", PARENT],
            "compile_once": True, "stop_on_first_failure": True, "workflow_context_required_before_parent_compile": True,
            "later_CLI_operation": "same-job-owning-AppKit-receipt-reference-only",
            "same_job_parent_receipt": PARENT + "/receipt.json", "source_sha256": expected,
            "accepted_AppKit2_reused_not_selected": ["cancel_before_dispatch", "no_key_window"],
            "accepted_JNI3_reused_not_selected": list(ACCEPTED_JNI), "Gradle_tasks": [],
            "native_tests_executed_here": 0, "JNI_tests_executed_here": 0, "Gradle_executions_here": 0,
            "original650_reference": {"run": 41791895471, "attempt": 1,
                                      "source": "ef6aae6da0c0879431d9c4712f8f914eaf6194ea", "status": "FAILED"},
            "readiness_fix_included": False, "native_cause_verified": False,
            "outer_CI_history_composition_qualified_here": False, "release_ready": False,
            "scope": "Six missing AppKit cases only; same-job original Rust receipts, no JNI or fresh JVM result"}


def _load(root, relative, maximum=MAX_JSON):
    payload, identity = source.ordinary_bytes(root, relative, maximum)
    need(0 < len(payload) <= maximum, "bounded-existing-AppKit-data-required")
    return source.json_bytes(payload), identity


def _map_digest(mapping):
    return hashlib.sha256("".join(f"{digest}  {name}\n" for name, digest in sorted(mapping.items())).encode()).hexdigest()


def _map(value):
    need(type(value) is dict and 0 < len(value) <= MAX_MAP, "bounded-full-AppKit-input-map-required")
    for name, digest in value.items():
        source._path(name)
        need(type(digest) is str and source.DIGEST.fullmatch(digest), "exact-AppKit-input-map-digest-required")
    return value


def _ns(value):
    need(type(value) is str and len(value) <= 64, "UTC-AppKit-parent-time-required")
    date = dt.datetime.fromisoformat(value)
    need(date.utcoffset() == dt.timedelta(0), "UTC-AppKit-parent-time-required")
    delta = date - dt.datetime(1970, 1, 1, tzinfo=dt.timezone.utc)
    result = ((delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds) * 1000
    need(result > 0, "positive-UTC-AppKit-parent-time-required")
    return result


def _execution(value, maximum):
    need(type(value) is dict and value.get("started") is True and value.get("passed") is True and
         type(value.get("exit_code")) is int and value["exit_code"] == 0 and value.get("stop_reason") is None and
         value.get("complete_log_within_size_bound") is True and type(value.get("pid")) is int and value["pid"] > 0 and
         all(type(value.get(k)) is int and value[k] > 0 for k in ("started_at_ns", "ended_at_ns")) and
         value["started_at_ns"] <= value["ended_at_ns"] and
         0 <= value["ended_at_ns"] - value["started_at_ns"] <= (maximum + 5) * 1_000_000_000 and
         type(value.get("elapsed_seconds")) in {int, float} and 0 <= value["elapsed_seconds"] <= maximum + 5 and
         math.isfinite(value["elapsed_seconds"]), "actual-clean-AppKit-execution-required")
    cleanup = value.get("cleanup")
    need(type(cleanup) is dict and all(cleanup.get(k) is True for k in ("leader_reaped", "group_empty", "clean")) and
         all(cleanup.get(k) is False for k in ("forced", "term_sent", "kill_sent")) and
         "cleanup_error" not in cleanup, "independent-owned-AppKit-process-cleanup-required")


def _file_identity(value):
    need(type(value) is dict and set(value) == set(IDENTITY_KEYS) and
         all(type(value[key]) is int for key in IDENTITY_KEYS if key != "sha256") and
         value["device"] >= 0 and value["inode"] > 0 and value["size"] >= 0 and value["mtime_ns"] > 0 and
         stat.S_ISREG(value["mode"]) and type(value["sha256"]) is str and source.DIGEST.fullmatch(value["sha256"]),
         "strict-ordinary-AppKit-file-identity-required")
    return value


def _identity_subset(value):
    need(type(value) is dict and set(IDENTITY_KEYS) <= set(value), "complete-AppKit-file-identity-required")
    return _file_identity({key: value[key] for key in IDENTITY_KEYS})


def _runtime(value):
    keys = {"host", "rust", "cargo", "xcode", "macos_sdk", "toolchain_executables",
            "graphical_session_probe_exit_zero", "native_ui_optin", "visible_picker_or_recipient_verified", "launchctl_payload_archived"}
    need(type(value) is dict and set(value) == keys and type(value.get("host")) is dict and
         set(value["host"]) == {"system", "architecture", "macos_version", "macos_build", "python"} and
         value["host"].get("system") == "Darwin" and value["host"].get("architecture") == "arm64" and
         value.get("graphical_session_probe_exit_zero") is True and value.get("native_ui_optin") is True and
         value.get("visible_picker_or_recipient_verified") is False and value.get("launchctl_payload_archived") is False,
         "actual-opted-in-macOS-arm64-parent-runtime-required")
    for key, pattern in (("macos_version", r"[0-9]+(?:\.[0-9]+)*"), ("macos_build", r"[0-9A-Za-z]+"),
                         ("python", r"[0-9]+(?:\.[0-9]+){2}")):
        need(type(value["host"].get(key)) is str and 0 < len(value["host"][key]) <= 64 and
             re.fullmatch(pattern, value["host"][key]), "complete-AppKit-host-runtime-required")
    for key in ("rust", "cargo"):
        compiler = value.get(key)
        need(type(compiler) is dict and set(compiler) == {"release", "host", "commit-hash", "commit-date"} and
             compiler.get("release") == "1.98.0" and compiler.get("host") == "aarch64-apple-darwin" and
             type(compiler.get("commit-hash")) is str and re.fullmatch(r"[0-9a-f]{40}", compiler["commit-hash"]) and
             type(compiler.get("commit-date")) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", compiler["commit-date"]),
             "effective-AppKit-compiler-identity-required")
    for key in ("xcode", "macos_sdk"):
        version = value.get(key)
        need(type(version) is dict and set(version) == {"version", "build"} and
             all(type(version.get(field)) is str and 0 < len(version[field]) <= 64 for field in ("version", "build")) and
             re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version["version"]) and re.fullmatch(r"[0-9A-Za-z.]+", version["build"]),
             "effective-AppKit-Xcode-SDK-identity-required")
    tools = value.get("toolchain_executables")
    need(type(tools) is dict and set(tools) == {"rustup", "rustc", "cargo", "clang"}, "effective-AppKit-tool-files-required")
    for tool in tools.values():
        need(type(tool) is dict and set(tool) == {*IDENTITY_KEYS, "path_sha256"} and
             type(tool.get("path_sha256")) is str and source.DIGEST.fullmatch(tool["path_sha256"]), "owning-AppKit-tool-path-identity-required")
        identity = _identity_subset(tool)
        need(identity["mode"] & 0o111, "owning-AppKit-tool-executable-mode-required")


def _logs(root, execution, folder, role, maximum, *, read):
    rows = execution.get("private_logs")
    need(type(rows) is list and len(rows) == 2, "two-original-AppKit-owned-logs-required")
    payloads, total = [], 0
    for stream, row in zip(("stdout", "stderr"), rows):
        expected = folder + "/" + role + "." + stream + ".private.log"
        need(type(row) is dict and set(row) == {*IDENTITY_KEYS, "relative_path"} and row.get("relative_path") == expected,
             "exact-AppKit-owned-log-path-required")
        raw, identity = read(expected, maximum)
        need(identity == _identity_subset(row), "held-AppKit-owning-private-log-required")
        total += len(raw); payloads.append(raw)
    need(total <= maximum, "bounded-complete-AppKit-owned-log-pair-required")
    return payloads[0]  # Raw bytes stay private; only the finite stdout marker below is observed.


def _console(payload, case):
    pattern = re.compile(r"NATIVECMPKIT_APPKIT_CASE name=([a-z0-9_]+) passed=(true|false) "
                         r"seconds=([0-9]+\.[0-9]{6}) live=([0-9]+) registry=([0-9]+) cleanup=(true|false)\Z")
    markers = [line for line in payload.decode("utf-8", errors="strict").splitlines()
               if line.startswith("NATIVECMPKIT_APPKIT_CASE")]
    need(len(markers) == 1, "one-original-AppKit-console-marker-required")
    marker = pattern.fullmatch(markers[0])
    need(marker is not None and marker[1] == case and marker[2] == "true" and float(marker[3]) <= 240 and
         marker[4] == "0" and marker[5] == "0" and marker[6] == "true", "passed-native-AppKit-console-owner-cleanup-required")


def _xml(payload, case):
    need(0 < len(payload) <= MAX_XML and b"<!" not in payload, "bounded-no-DTD-AppKit-XML-required")
    document = ET.fromstring(payload)
    need(document.tag == "testsuite" and document.attrib == {"name": SUITE, "tests": "1", "failures": "0", "errors": "0", "skipped": "0"} and
         len(document) == 1, "one-original-passed-AppKit-case-required")
    node = document[0]
    need(node.tag == "testcase" and set(node.attrib) == {"classname", "name", "time"} and
         node.get("classname") == CLASS and node.get("name") == case and
         re.fullmatch(r"[0-9]+\.[0-9]{6}", node.get("time", "")) and 0 <= float(node.get("time")) <= 240 and
         len(node) == 1 and node[0].tag == "system-out" and not node[0].attrib and len(node[0]) == 0 and
         node[0].text == WITNESS, "exact-Rust-AppKit-XML-and-owner-witness-required")


def _reports_state(root, *, read=None):
    descriptors, primary = [], None
    if read is None:
        read = lambda relative, maximum: source.ordinary_bytes(root, relative, maximum)
    try:
        _, chain = source.open_directory(root, REPORT_PARENT, descriptors)
        folder = root / REPORT_PARENT
        result, total = {}, 0
        def refuse_walk(error):
            raise error
        for base, directories, names in os.walk(folder, followlinks=False, onerror=refuse_walk):
            for name in sorted([*directories, *names]):
                path = Path(base) / name
                relative = path.relative_to(root).as_posix()
                metadata = path.lstat()
                need(not stat.S_ISLNK(metadata.st_mode), "ordinary-AppKit-original-report-entry-required")
                if stat.S_ISDIR(metadata.st_mode):
                    result[relative] = {"kind": "directory", "inode": metadata.st_ino, "device": metadata.st_dev,
                                        "mtime_ns": metadata.st_mtime_ns, "mode": metadata.st_mode}
                else:
                    payload, identity = read(relative, MAX_XML)
                    total += len(payload)
                    need(total <= 32 * 1024 * 1024, "AppKit-original-report-byte-bound")
                    result[relative] = {"kind": "file", **identity}
                need(len(result) <= MAX_MAP, "AppKit-original-report-count-bound")
        for relative, row in result.items():
            if row["kind"] == "directory":
                metadata = (root / relative).lstat()
                need(stat.S_ISDIR(metadata.st_mode) and
                     row == {"kind": "directory", "inode": metadata.st_ino, "device": metadata.st_dev,
                             "mtime_ns": metadata.st_mtime_ns, "mode": metadata.st_mode},
                     "AppKit-original-report-directory-custody-changed")
        source.verify_directories(root, chain)
        return dict(sorted(result.items()))
    except BaseException as error:
        primary = error
        raise
    finally:
        source.close_owned(descriptors, primary)


def reference_parent(root: Path, context: dict, now_ns: int):
    """Passive same-job custody; never query/relaunch native objects/processes/JNI."""
    _context(context)
    expected = source.validate_current_sources(root)
    observed = {}
    def read(relative, maximum=source.MAX_SOURCE):
        raw, identity = source.ordinary_bytes(root, relative, maximum)
        if relative in observed:
            need(observed[relative][1] == identity, "AppKit-owned-reference-input-changed-between-reads")
        observed[relative] = (maximum, identity)
        return raw, identity
    def load(relative, maximum=MAX_JSON):
        payload, identity = read(relative, maximum)
        need(0 < len(payload) <= maximum, "bounded-existing-AppKit-data-required")
        return source.json_bytes(payload), identity
    parent, parent_identity = load(PARENT + "/receipt.json")
    need(type(parent) is dict and parent.get("workflow_context") == context,
         "same-job-attempt-slot-source-AppKit-parent-required")
    need(parent.get("schema_version") == 1 and type(parent.get("schema_version")) is int and
         parent.get("platform") == "macos-arm64" and parent.get("rust_target") == "aarch64-apple-darwin" and
         parent.get("rust_toolchain") == "1.98.0" and parent.get("exact_native_cases") == list(CASES) and
         parent.get("compile_once") is True and parent.get("stop_on_first_failure") is True and
         parent.get("missing_only_share630") is True and parent.get("native_command") is None and
         parent.get("native_case_arguments") is None and parent.get("stress_selected") is False and
         parent.get("publication_performed") is False and parent.get("release_readiness_verified") is False and
         parent.get("raw_control_flag_exported") is False and parent.get("raw_control_flag_independently_observed") is False,
         "exact-AppKit-six-owning-scope-required")
    start, finish = _ns(parent.get("started_at_utc")), _ns(parent.get("finished_at_utc"))
    need(type(now_ns) is int and start <= finish <= now_ns + FRESHNESS_SLOP and
         now_ns - finish <= MAX_FINISHED_AGE and finish - start <= MAX_JOB_SPAN,
         "current-job-bounded-AppKit-parent-time-required")
    summary = parent.get("native_reports")
    need(summary is None or type(summary) is dict, "ordinary-AppKit-report-summary-object-required")
    reached = summary.get("testcases", []) if summary is not None else []
    need(type(reached) is list and len(reached) <= len(CASES) and
         [row.get("name") for row in reached if type(row) is dict] == list(CASES[:len(reached)]) and
         all(type(row) is dict and set(row) == {"classname", "name", "status"} and
             row["classname"] == CLASS and row["status"] in {"passed", "failed", "error"} for row in reached),
         "finite-original-AppKit-reached-population-required")
    if parent.get("passed") is not True:
        # A failed owning step already makes the job red. Retain reached/unexecuted,
        # never turn cleanup, compilation or an independently accepted JNI into pass.
        return {"passed": False, "errors": ["owning-AppKit-result-failed-or-refused"],
                "parent_receipt": PARENT + "/receipt.json", "parent_receipt_sha256": parent_identity["sha256"],
                "native_cases_reached": [row["name"] for row in reached],
                "native_cases_unexecuted": list(CASES[len(reached):])}
    need(parent.get("errors") == [] and parent.get("phase") == "final-custody" and
         all(parent.get(k) is True for k in ("inputs_held", "native_inputs_held", "artifact_held", "reports_held", "owned_lock_released")),
         "all-independent-AppKit-parent-custody-required")
    git = {"source_revision": context["source_revision"], "source_tree_dirty": False}
    need(parent.get("git_before") == git == parent.get("git_after"), "same-workflow-source-revision-AppKit-parent-required")
    before, _ = load(PARENT + "/inputs-before.json"); after, _ = load(PARENT + "/inputs-after.json")
    native_before, _ = load(PARENT + "/native-inputs-before.json"); native_after, _ = load(PARENT + "/native-inputs-after.json")
    before, after, native_before, native_after = _map(before), _map(after), _map(native_before), _map(native_after)
    need(before == after and native_before == native_after and
         parent.get("inputs_after") == {"count": len(before), "sha256": _map_digest(before)} and
         parent.get("native_inputs_after") == {"count": len(native_before), "sha256": _map_digest(native_before)},
         "full-before-after-AppKit-parent-input-maps-required")
    for name, digest in before.items():
        need(source.sha(read(name)[0]) == digest, "AppKit-parent-source-changed-before-reference")
    for name, digest in native_before.items():
        need(source.sha(read(name)[0]) == digest, "AppKit-parent-native-source-changed-before-reference")
    required = {name: digest for name, digest in expected.items() if name.startswith(("scripts/", "calf-share/"))}
    need(all(before.get(name) == digest for name, digest in required.items()), "complete-AppKit-owning-reader-source-map-required")
    native_required = {name: digest for name, digest in expected.items()
                       if name.startswith(("calf-share/native/", "calf-share/src/desktopMain/")) or name in {
                           "calf-share/build.gradle.kts", "rust-toolchain.toml", "scripts/native/artifacts.py",
                           "convention-plugins/src/main/kotlin/NativeLibraries.kt"}}
    need(all(before.get(name) == digest == native_before.get(name) for name, digest in native_required.items()),
         "complete-AppKit-native-build-source-map-required")
    _runtime(parent.get("runtime_before"))
    need(parent["runtime_before"] == parent.get("runtime_after"), "held-AppKit-parent-runtime-required")
    for name in ("runtime-before.json", "runtime-after.json"):
        value, _ = load(PARENT + "/" + name)
        need(value == parent["runtime_before"], "original-AppKit-runtime-payload-held-required")
    _execution(parent.get("compilation"), 1200)
    compile_execution = parent["compilation"]
    need(start - FRESHNESS_SLOP <= compile_execution["started_at_ns"] <= compile_execution["ended_at_ns"] <= finish + FRESHNESS_SLOP,
         "same-parent-compile-time-window-required")
    _logs(root, compile_execution, PARENT, "cargo", 64 * 1024 * 1024, read=read)
    artifact = parent.get("artifact_before")
    need(type(artifact) is dict and artifact.get("macho_file_type") == "MH_EXECUTE" and
         artifact.get("rust_target") == "aarch64-apple-darwin" and artifact.get("fresh_cargo_artifact") is True and
         artifact.get("source_path") == "calf-share/native/tests/appkit_lifecycle_main.rs" and
         artifact.get("source_sha256") == before.get(artifact["source_path"]) and
         artifact.get("package") == "calf-share-native@0.1.0" and artifact.get("test_target") == "appkit_lifecycle" and
         type(artifact.get("diagnostics")) is dict and type(artifact["diagnostics"].get("errors")) is int and artifact["diagnostics"]["errors"] == 0 and
         type(artifact["diagnostics"].get("warnings")) is int and artifact["diagnostics"]["warnings"] >= 0 and
         type(artifact.get("relative_path")) is str and
         re.fullmatch(re.escape(PARENT) + r"/cargo-target/aarch64-apple-darwin/debug/deps/appkit_lifecycle-[0-9a-f]+", artifact["relative_path"]),
         "original-admitted-AppKit-MH-executable-required")
    binary, binary_identity = read(artifact["relative_path"], 64 * 1024 * 1024)
    need(len(binary) >= 32 and struct.unpack_from("<I", binary)[0] == 0xFEEDFACF and
         struct.unpack_from("<I", binary, 4)[0] == 0x0100000C and struct.unpack_from("<I", binary, 12)[0] == 2 and
         binary_identity == _identity_subset(artifact) == _file_identity(parent.get("artifact_after")) and
         binary_identity["mode"] & 0o111 and
         compile_execution["started_at_ns"] - FRESHNESS_SLOP <= binary_identity["mtime_ns"] <= compile_execution["ended_at_ns"] + FRESHNESS_SLOP,
         "held-actual-AppKit-executable-reference-required")
    witness = parent.get("control_failure_witness")
    cases_source = "calf-share/native/tests/appkit_lifecycle/cases.rs"
    need(type(witness) is dict and witness.get("source_path") == cases_source and
         witness.get("source_sha256") == before.get(cases_source) and witness.get("compiled_with_admitted_executable") is True and
         witness.get("source_bound_failed_control_gate_verified") is True and
         witness.get("raw_control_flag_exported") is False and witness.get("raw_control_flag_independently_observed") is False,
         "same-admitted-AppKit-control-and-cleanup-source-required")
    summary = parent.get("native_reports")
    expected_cases = [{"classname": CLASS, "name": name, "status": "passed"} for name in CASES]
    expected_markers = [{"name": name, "passed": True, "live": 0, "registry": 0, "cleanup": True} for name in CASES]
    need(type(summary) is dict and summary.get("passed") is True and summary.get("errors") == [] and
         summary.get("testcases") == expected_cases and summary.get("console_markers") == expected_markers and
         type(summary.get("reached_original_xml")) is int and summary["reached_original_xml"] == 6 and
         type(summary.get("accepted_xml_cases")) is int and summary["accepted_xml_cases"] == 6 and
         summary.get("remaining_unexecuted_cases") == [] and summary.get("preexisting_reports_unchanged") is True,
         "all-six-actual-AppKit-outcomes-and-cleanup-required")
    runs = parent.get("native_case_runs")
    need(type(runs) is list and len(runs) == 6 and all(type(row) is dict for row in runs) and
         [row.get("case") for row in runs] == list(CASES),
         "six-serial-AppKit-owning-process-receipts-required")
    pids, report_rows, previous_end = {compile_execution["pid"]}, [], compile_execution["ended_at_ns"]
    for case, row in zip(CASES, runs):
        folder = PARENT + "/cases/" + case
        record, _ = load(folder + "/receipt.json")
        need(type(record) is dict and row == record and record.get("passed") is True and record.get("errors") == [] and
             record.get("phase") == "final-custody" and record.get("native_case_arguments") == ["--case=" + case] and
             record.get("native_command") == [artifact["relative_path"], "--case=" + case] and
             all(record.get(k) is True for k in ("inputs_after_held", "native_inputs_after_held", "git_after_held", "runtime_after_held", "artifact_after_held", "reports_held", "preexisting_reports_unchanged")) and
             record.get("git_before") == git == record.get("git_after") and
             record.get("runtime_before") == parent["runtime_before"] == record.get("runtime_after") and
             record.get("artifact_before") == binary_identity == record.get("artifact_after"),
             "independent-held-AppKit-child-source-runtime-owner-custody-required")
        for name, expected_map in (("inputs-before.json", before), ("inputs-after.json", before),
                                   ("native-inputs-before.json", native_before), ("native-inputs-after.json", native_before)):
            value, _ = load(folder + "/" + name)
            need(value == expected_map, "complete-AppKit-child-input-map-held-required")
        for name in ("runtime-before.json", "runtime-after.json"):
            value, _ = load(folder + "/" + name)
            need(value == parent["runtime_before"], "AppKit-child-runtime-payload-held-required")
        execution = record.get("native_execution")
        _execution(execution, 240)
        _console(_logs(root, execution, folder, "native", 4 * 1024 * 1024, read=read), case)
        need(execution["pid"] not in pids and previous_end <= execution["started_at_ns"] <= execution["ended_at_ns"] <= finish + FRESHNESS_SLOP,
             "serial-fresh-owned-AppKit-PIDs-required")
        pids.add(execution["pid"]); previous_end = execution["ended_at_ns"]
        child = record.get("native_reports")
        need(type(child) is dict and child.get("passed") is True and child.get("errors") == [] and
             child.get("testcases") == [{"classname": CLASS, "name": case, "status": "passed"}] and
             child.get("console_markers") == [{"name": case, "passed": True, "live": 0, "registry": 0, "cleanup": True}] and
             child.get("preexisting_reports_unchanged") is True and type(child.get("reports")) is list and len(child["reports"]) == 1,
             "one-original-AppKit-child-XML-console-and-cleanup-required")
        report = child["reports"][0]
        original = REPORT_PARENT + "/process-" + str(execution["pid"]) + "/TEST-" + case + ".xml"
        copy_name = "fresh-reports/TEST-" + case + ".xml"
        need(type(report) is dict and report.get("source_relative_path") == original and report.get("artifact_relative_path") == copy_name and report.get("case") == case,
             "exact-owned-PID-AppKit-report-path-required")
        raw, identity = read(original, MAX_XML)
        copied, _ = read(folder + "/" + copy_name, MAX_XML)
        need(raw == copied and identity == _identity_subset(report) and
             execution["started_at_ns"] - FRESHNESS_SLOP <= identity["mtime_ns"] <= execution["ended_at_ns"] + FRESHNESS_SLOP,
             "fresh-original-AppKit-XML-byte-and-PID-custody-required")
        _xml(raw, case)
        with os.scandir(root / folder / "fresh-reports") as entries:
            need([entry.name for entry in entries] == ["TEST-" + case + ".xml"], "no-extra-AppKit-copy-report-required")
        report_rows.append({**report, "artifact_relative_path": "cases/" + case + "/" + copy_name})
    need(summary.get("reports") == report_rows, "same-six-parent-child-AppKit-report-rows-required")
    reported_state, _ = load(PARENT + "/reports-after.json")
    actual_state = _reports_state(root, read=read)
    need(reported_state == actual_state and parent.get("reports_after") == {"inventory_captured": True} and
         hashlib.sha256(json.dumps(actual_state, sort_keys=True).encode()).hexdigest() == summary.get("source_report_state_sha256"),
         "original-AppKit-report-inventory-held-through-reference-required")
    for mapping in (before, native_before):
        for name, digest in mapping.items():
            need(source.sha(read(name)[0]) == digest, "AppKit-source-changed-during-reference")
    for relative, (maximum, identity) in list(observed.items()):
        need(source.ordinary_bytes(root, relative, maximum)[1] == identity,
             "AppKit-owned-file-custody-changed-before-final-reference")
    need(_reports_state(root) == actual_state, "AppKit-original-report-tree-changed-before-final-reference")
    lock = root / "build/ci-verification/.macos-share-appkit-lifecycle.lock"
    need(not lock.exists() and not lock.is_symlink(), "owning-AppKit-lock-release-absence-required")
    need(read(PARENT + "/receipt.json")[1] == parent_identity and
         source.validate_current_sources(root) == expected, "AppKit-parent-or-owning-source-changed-during-reference")
    return {"passed": True, "errors": [], "parent_receipt": PARENT + "/receipt.json",
            "parent_receipt_sha256": parent_identity["sha256"], "native_cases_reached": list(CASES),
            "native_cases_unexecuted": [], "same_job_source_runtime_PID_XML_cleanup_held": True,
            "owning_native_test_count_referenced_not_reexecuted": 6,
            "original_Rust_XML_referenced_not_synthesized": True, "fresh_JVM_XML_created": False}


def _write_reference(root, receipt):
    """Create only a fresh owned sidecar through held ordinary parent descriptors."""
    descriptors, primary = [], None
    try:
        parent, chain = source.open_directory(root, "build/ci-verification", descriptors)
        payload = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
        need(len(payload) <= MAX_JSON, "bounded-AppKit-reference-receipt-required")
        # The owning prior step already created these ancestors. Do not create
        # or traverse an unverified build directory or overwrite a foreign slot.
        os.mkdir(SLOT, mode=0o700, dir_fd=parent)
        output_before = os.stat(SLOT, dir_fd=parent, follow_symlinks=False)
        need(stat.S_ISDIR(output_before.st_mode), "ordinary-owned-AppKit-reference-output-required")
        output = os.open(SLOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        descriptors.append(output)
        need(source.directory_identity(output_before) == source.directory_identity(os.fstat(output)),
             "owned-AppKit-reference-output-replaced")
        chain.append((root / OUTPUT, output, source.directory_identity(output_before)))
        source.verify_directories(root, chain)
        leaf = os.open("receipt.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=output)
        descriptors.append(leaf)
        remaining = memoryview(payload)
        while remaining:
            count = os.write(leaf, remaining)
            need(count > 0, "owned-AppKit-reference-write-refused")
            remaining = remaining[count:]
        os.fsync(leaf)
        metadata = os.fstat(leaf)
        path_metadata = os.stat("receipt.json", dir_fd=output, follow_symlinks=False)
        need(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and metadata.st_size == len(payload) and
             source._identity(metadata) == source._identity(path_metadata), "owned-AppKit-reference-file-custody-changed")
        source.verify_directories(root, chain)
        written, identity = source.ordinary_bytes(root, OUTPUT + "/receipt.json", MAX_JSON)
        need(written == payload and identity["inode"] == metadata.st_ino and identity["device"] == metadata.st_dev,
             "owned-AppKit-reference-bytes-changed-after-write")
    except BaseException as error:
        primary = error
        raise
    finally:
        source.close_owned(descriptors, primary)


def main_for_existing_profile(root: Path, args):
    need(args.operation in {"plan", "run"} and args.suite == "desktop" and args.module == [MODULE] and
         args.focus == ENTRY_FOCUS and args.simulator is None and getattr(args, "android_emulator", None) is None and
         getattr(args, "kotlin_user_home", None) is None and type(args.reserve_mib) is int and args.reserve_mib >= 8192 and
         type(args.timeout) is int and 1 <= args.timeout <= 4200, "exact-existing-AppKit-only-CLI-required")
    if args.operation == "plan":
        need(args.output is None, "read-only-AppKit-plan-has-no-output")
        print(json.dumps(plan(root), indent=2, sort_keys=True))
        return 0
    need(args.output == OUTPUT, "exact-existing-AppKit-result-reference-output-required")
    source.validate_current_sources(root)
    context = workflow_context()
    receipt = {"schema_version": 1, "suite": "native-AppKit-reference-not-JVM", "profile": PROFILE,
               "entry_focus": ENTRY_FOCUS, "effective_focus": EFFECTIVE_FOCUS,
               "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "workflow_context": context,
               "passed": False, "errors": [], "complete_suite_requested": False, "explicit_module_subset": [MODULE],
               "native_tests_executed_here": 0, "JNI_tests_executed_here": 0, "Gradle_executions_here": 0,
               "native_cases_reached": [], "native_cases_unexecuted": list(CASES),
               "native_causes_verified": False, "release_ready": False, "publication_performed": False}
    try:
        receipt.update(reference_parent(root, context, time.time_ns()))
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        receipt.update(passed=False, errors=["owning-AppKit-reference-refused-" + type(error).__name__])
    receipt["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    _write_reference(root, receipt)
    print(json.dumps({key: receipt[key] for key in ("suite", "passed", "errors", "native_tests_executed_here", "JNI_tests_executed_here", "Gradle_executions_here")}, sort_keys=True))
    return 0 if receipt["passed"] else 1
