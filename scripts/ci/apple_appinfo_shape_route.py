#!/usr/bin/env python3
"""One selected current-owned-install SDK prerequisite; never a native test route.

The fixed link task supplies a fresh ordinary-signing app. The existing owning
harness installs/verifies it and returns through its original finally before any
launch/Worker/WK/profile preparation. Only the pinned helper may query appinfo.
The output is an SDK lexical-shape receipt, not JUnit, registration or readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

import apple_appinfo_capability as capability
import apple_appinfo_shape as shape
import ios_ui_application as application
import library_tests as lt
import runtime_context as runtime

PROFILE = "ios-appinfo-shape"
OUTPUT = "build/ci-verification/apple-appinfo-shape"
BINARY = "calf-ui/build/bin/iosSimulatorArm64/applicationDebugTest/application.kexe"
LINK_TASK = ":calf-ui:linkApplicationDebugTestIosSimulatorArm64"
LINK_COMMAND = ["./gradlew", "--no-daemon", "--no-parallel", "--max-workers=1",
                "--no-configuration-cache", "--no-build-cache", "--console=plain", LINK_TASK]
LINK_SECONDS, RESERVE_MIB = 1200, 8192
HELP_RECEIPT = "docs/development/evidence/apple-appinfo-exact-template-20261101/actual006/receipt.json"
SOURCE_INPUTS = ("scripts/ci/apple_appinfo_shape_route.py", "scripts/ci/apple_appinfo_shape.py",
                 "scripts/ci/apple_appinfo_capability.py", "scripts/ci/ios_ui_application.py",
                 "calf-ui/build.gradle.kts", application.HOST_SOURCE)
FALSE_FLAGS = ("appinfo_output_schema_observed", "subsequent_appinfo_ready", "registration_observed",
               "root_cause_proven", "native_functionality_verified", "profile_passed",
               "packages_published", "release_readiness_certified",
               "raw_payload_keys_values_paths_or_inventory_uploaded")
CLEANUP_FLAGS = ("owned_app_identity_reverified", "owned_app_stopped_verified",
                 "owned_app_absence_verified", "owned_local_bundle_removed")
NATIVE_PREPARATION_KEYS = ("application_transport", "application_protocol_partial", "startup_failure_observation",
                           "webview_request_fixture", "image_memory_profile", "system_appearance_driver",
                           "owned_crash_diagnostics", "owned_launch_diagnostics", "image_diagnostics_mode")


class RouteError(ValueError):
    """Fixed source guard only; never include command output or private paths."""


def need(condition, guard):
    if not condition:
        raise RouteError(guard)


def accepted_help(root: Path) -> bytes:
    path = lt.safe_path(root, HELP_RECEIPT)
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
         0 < before.st_size <= 65536, "bounded_pinned_help_source_required")
    body = path.read_bytes()
    after = path.lstat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
         hashlib.sha256(body).hexdigest() == shape.ACCEPTED_HELP_RECEIPT_SHA256,
         "accepted_actual006_help_bytes_required")
    return body


def plan(root: Path) -> dict:
    """Fixed source-only selector; deliberately not library_tests.plan/run."""
    accepted_help(root)
    inputs = {}
    for relative in SOURCE_INPUTS:
        path = lt.safe_path(root, relative)
        need(path.is_file() and not path.is_symlink(), "owning_source_required")
        inputs[relative] = lt.sha256(path)
    return {"profile": PROFILE, "operation": "plan", "kind": "sdk-prerequisite",
            "source_only": True, "sources": inputs, "link_command": LINK_COMMAND.copy(),
            "link_timeout_seconds": LINK_SECONDS, "reserve_mib": RESERVE_MIB,
            "selected_binary": BINARY, "output": OUTPUT,
            "simulator_selector": "one task-recorded explicit UUID, no default or alternate",
            "accepted_help_receipt_sha256": shape.ACCEPTED_HELP_RECEIPT_SHA256,
            "native_tests_executed": 0, "selected_native_methods": [],
            "mandatory_library_tests_waived": False, "library_matrix_slots": [],
            "launch_worker_WK_profile_preparation_requested": False}


def observe_owned_install(context: shape.OwnedInstallation) -> dict:
    """Only three existing fixed path identities and one pinned appinfo query.

    Fixed path outputs stay in bounded memory, never logs/receipts. The unchanged
    helper owns private payload files, its persistent query latch and deletion.
    The 90s limit remains an acceptance budget, not adversarial filesystem timing.
    """
    started = time.monotonic()
    receipt = {"operation": "owned-install-appinfo-shape", "status": "unavailable",
               "tool_path_resolution": [], "shape": None}
    try:
        payload = accepted_help(context.root)
        selected = {}
        for name in ("developer", "simctl", "xcodebuild"):
            remaining = capability.TOTAL_SECONDS - (time.monotonic() - started)
            need(remaining >= capability.COMMAND_SECONDS, "path_resolution_budget_exhausted")
            result = capability.control(capability.COMMANDS[name], context.root, capability.COMMAND_SECONDS)
            need(type(result) is capability.Result and capability.valid(result) and
                 result.exit_code == 0 and not result.stderr, "fixed_selected_tool_path_unavailable")
            receipt["tool_path_resolution"].append({"name": name, **capability.metadata(result)})
            selected[name] = capability.actual_path(result)
        need(capability.TOTAL_SECONDS - (time.monotonic() - started) >= capability.COMMAND_SECONDS,
             "shape_budget_exhausted_before_query")
        receipt["shape"] = shape.collect(context, capability_bytes=payload,
            tool_paths={"xcrun": Path("/usr/bin/xcrun"), "simctl": selected["simctl"],
                        "xcodebuild": selected["xcodebuild"]}, developer=selected["developer"])
        receipt["status"] = receipt["shape"]["status"]
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        receipt["error_type"] = type(error).__name__
        if type(error) is RouteError:
            receipt["error_guard"] = str(error)
    receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
    if receipt["elapsed_seconds"] > capability.TOTAL_SECONDS:
        receipt.update(status="unavailable", budget_exhausted=True)
    return receipt


def cleanup_verified(document: dict) -> bool:
    if type(document) is not dict or type(document.get("cleanup")) is not dict:
        return False
    cleanup = document["cleanup"]
    return (all(cleanup.get(key) is True for key in CLEANUP_FLAGS) and
            type(cleanup.get("uninstall_exit_code")) is int and cleanup["uninstall_exit_code"] == 0 and
            "error_type" not in cleanup and "local_error_type" not in cleanup)


def installation_prerequisite_observed(document: dict) -> bool:
    if (type(document) is not dict or document.get("sdk_prerequisite_only") is not True or
            document.get("transport_passed") is not False or document.get("native_launch_attempted") is not False or
            type(document.get("native_tests_executed")) is not int or document["native_tests_executed"] != 0 or
            document.get("sdk_signing_mode") != "ordinary-adhoc" or
            document.get("explicit_test_focus") is not None or document.get("application_protocol") is not None or
            "error" in document or any(key in document for key in NATIVE_PREPARATION_KEYS) or
            not cleanup_verified(document)):
        return False
    observation = document.get("appinfo_shape_prerequisite")
    if type(observation) is not dict or observation.get("status") != "observed-bounded-lexical-shape":
        return False
    captured = observation.get("shape")
    return (type(captured) is dict and captured.get("status") == "observed-bounded-lexical-shape" and
            captured.get("capability_receipt_sha256") == shape.ACCEPTED_HELP_RECEIPT_SHA256 and
            captured.get("query_attempted") is True and type(captured.get("query_count")) is int and
            captured["query_count"] == 1 and captured.get("owned_private_output_removed") is True and
            all(captured.get(key) is False for key in FALSE_FLAGS) and
            captured.get("registered_container_matches_verified_container") is None and
            captured.get("registered_executable_identity_verified") is None)


def selected_environment(device: str, output: str) -> dict:
    values = {"NATIVECMPKIT_UIKIT_SIMULATOR": device, "NATIVECMPKIT_UIKIT_RESULT_ROOT": output}
    before = {key: os.environ.get(key) for key in values}
    need(all(before[key] in (None, value) for key, value in values.items()), "conflicting_native_environment")
    os.environ.update(values)
    return before


def restore_environment(before: dict, device: str, output: str):
    values = {"NATIVECMPKIT_UIKIT_SIMULATOR": device, "NATIVECMPKIT_UIKIT_RESULT_ROOT": output}
    need(all(os.environ.get(key) == value for key, value in values.items()), "native_environment_changed")
    for key, value in before.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def fresh_link_marker(log: Path) -> bool:
    """Exactly one executed fixed link task, never a test-runtime marker.

    Plain Gradle console task events attest only this linking prerequisite.
    UP-TO-DATE, FROM-CACHE, NO-SOURCE, SKIPPED, FAILED or duplicate events refuse
    availability. Fresh binary/installed identity checks remain separate.
    """
    selected = re.compile(r"^> Task " + re.escape(LINK_TASK) + r"(?: (.*))?$")
    count, all_executed = 0, True
    with log.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = selected.fullmatch(line.rstrip("\r\n"))
            if match:
                count += 1
                all_executed = all_executed and match.group(1) is None
    return count == 1 and all_executed


def run(device: str, root: Path | None = None) -> dict:
    root = lt.ROOT if root is None else root
    need(root == lt.ROOT and type(device) is str and runtime.UUID.fullmatch(device),
         "one_current_task_recorded_simulator_required")
    selected = plan(root)
    output = lt.safe_path(root, OUTPUT)
    output.mkdir(parents=True, mode=0o700, exist_ok=False)  # Persistent no-retry invocation latch.
    receipt = {"schema_version": 1, "profile": PROFILE, "operation": "appinfo-shape-sdk-prerequisite",
               "sdk_prerequisite_available": False, "started_at_utc": lt.utc_now(),
               "selected_simulator_uuid_sha256": hashlib.sha256(device.encode()).hexdigest(),
               "native_tests_executed": 0, "selected_native_methods": [], "native_launch_attempted": False,
               "transport_passed": False, "mandatory_library_tests_waived": False,
               "registration_observed": False, "appinfo_output_schema_observed": False,
               "native_functionality_verified": False, "subsequent_appinfo_ready": False,
               "registered_container_matches_verified_container": None,
               "registered_executable_identity_verified": None,
               "profile_passed": False, "root_cause_proven": False, "packages_published": False,
               "release_readiness_certified": False, "raw_payload_keys_values_paths_or_inventory_uploaded": False,
               "plan": selected, "link_execution": None, "shape_observation": None,
               "owning_install_cleanup": None, "inputs_unchanged": False}
    before, document = None, None
    try:
        context = runtime.capture(expected_arch="arm64", apple=True, device=device,
                                  require_booted=True, require_clean=True)
        accepted = json.loads(accepted_help(root))
        need(context["host"] == accepted["host"] and context["xcode"] == accepted["xcode"],
             "accepted_actual_host_and_Xcode_required")
        before = lt.snapshot_inputs(root)
        lt.write_json(output / "library-inputs-before.json", before)
        receipt.update(source_revision=context["source_revision"], library_input_count=len(before),
                       library_inputs_before_sha256=lt.input_digest(before),
                       input_map_scope="existing library snapshot, not combined map")
        binary = lt.safe_path(root, BINARY)
        need(not binary.exists(), "fresh_linked_binary_required_no_old_output_reuse")
        started_ns = time.time_ns()
        result = lt.execute(root, LINK_COMMAND.copy(), output / "private-link.log", LINK_SECONDS, RESERVE_MIB)
        need(type(result) is dict, "owning_link_result_required")
        receipt["link_execution"] = {"exit_code": result.get("exit_code"),
            "stop_reason_present": bool(result.get("stop_reason")), "elapsed_seconds": result.get("elapsed_seconds"),
            "task": LINK_TASK, "native_test_tasks_requested": False}
        need(type(result.get("exit_code")) is int and result["exit_code"] == 0 and not result.get("stop_reason"),
             "owned_fixed_link_failed_or_incomplete")
        info = binary.lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= application.MAX_BINARY_BYTES and
             started_ns - 2_000_000_000 <= info.st_mtime_ns <= time.time_ns() + 2_000_000_000 and
             fresh_link_marker(output / "private-link.log"),
             "fresh_exact_link_marker_and_binary_required")
        native_output = OUTPUT + "/native-ui-application"
        old_environment = selected_environment(device, native_output)
        try:
            document = application.run(BINARY, [], appinfo_shape_only=True)
        finally:
            restore_environment(old_environment, device, native_output)
        need(type(document) is dict, "owning_install_receipt_required")
        receipt["shape_observation"] = document.get("appinfo_shape_prerequisite")
        receipt["owning_install_cleanup"] = {
            key: document.get("cleanup", {}).get(key) for key in (*CLEANUP_FLAGS, "uninstall_exit_code")}
        receipt["owning_install_error_present"] = "error" in document
        receipt["source_revision_after_install"] = document.get("runtime_after", {}).get("source_revision")
        receipt["binary_sha256_before_install"] = document.get("binary_sha256")
        receipt["binary_sha256_after_install"] = document.get("binary_sha256_after")
        need(document.get("source_revision") == context["source_revision"] and
             document.get("runtime_after", {}).get("source_revision") == context["source_revision"],
             "same_frozen_source_required_after_install")
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as error:
        receipt["error_type"] = type(error).__name__
        if type(error) is RouteError:
            receipt["error_guard"] = str(error)
    finally:
        if before is not None:
            try:
                after = lt.snapshot_inputs(root)
                lt.write_json(output / "library-inputs-after.json", after)
                receipt["library_inputs_after_sha256"] = lt.input_digest(after)
                receipt["inputs_unchanged"] = before == after
            except (OSError, ValueError) as error:
                receipt["input_readback_error_type"] = type(error).__name__
        receipt["sdk_prerequisite_available"] = ("error_type" not in receipt and
            receipt["inputs_unchanged"] is True and installation_prerequisite_observed(document))
        receipt["finished_at_utc"] = lt.utc_now()
        lt.write_json(output / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("plan", "run"))
    parser.add_argument("--simulator")
    args = parser.parse_args()
    if args.operation == "plan":
        if args.simulator is not None:
            parser.error("plan is source-only and takes no simulator")
        print(json.dumps(plan(lt.ROOT), indent=2, sort_keys=True))
        return 0
    if args.simulator is None:
        parser.error("run requires one task-recorded explicit simulator UUID")
    receipt = run(args.simulator)
    print("NATIVECMPKIT_APPINFO_SDK_PREREQUISITE observed=" +
          str(receipt["sdk_prerequisite_available"]).lower(), flush=True)
    return 0 if receipt["sdk_prerequisite_available"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("Owned appinfo SDK prerequisite refused: " + type(error).__name__, file=sys.stderr)
        sys.exit(2)
