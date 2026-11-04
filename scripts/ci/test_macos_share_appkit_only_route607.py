# SPDX-License-Identifier: Apache-2.0
"""NEW AppKit6-only source/model controls; ZERO compiler/native/JNI/network.

Mach-O headers, runtimes, PIDs, GitHub context, logs and XML below are explicitly
synthetic ordinary fixture data. No old accepted test body is invoked. Tests
inspect only the new owning hooks and do not import the library/native runners.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager, redirect_stdout
import copy
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts/ci") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts/ci"))
import macos_share_appkit_only_route as route
import macos_share_appkit_only_source_projection as source


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def identity(path):
    before = path.lstat()
    payload = path.read_bytes()
    after = path.lstat()
    assert (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns)
    return {"device": before.st_dev, "inode": before.st_ino, "mode": before.st_mode,
            "size": before.st_size, "mtime_ns": before.st_mtime_ns, "sha256": digest(payload)}


def report_inventory(root):
    result = {}
    for path in sorted((root / route.REPORT_PARENT).rglob("*")):
        metadata = path.lstat()
        name = path.relative_to(root).as_posix()
        result[name] = ({"kind": "directory", "device": metadata.st_dev, "inode": metadata.st_ino,
                         "mtime_ns": metadata.st_mtime_ns, "mode": metadata.st_mode}
                        if stat.S_ISDIR(metadata.st_mode) else {"kind": "file", **identity(path)})
    return result


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def model_context():
    return {"repository": "Apdelrahman1911/nativeCmpkit", "workflow": "NativeCmpKit verification", "job": "library-tests",
            "run_id": "777777", "run_attempt": "1", "source_revision": "b" * 40,
            "ref": "refs/heads/development/model-fixture-not-a-real-run", "profile": route.PROFILE,
            "slot": route.SLOT, "entry_focus": route.ENTRY_FOCUS, "effective_focus": route.EFFECTIVE_FOCUS}


def model_environment():
    context = model_context()
    return {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": context["repository"], "GITHUB_WORKFLOW": context["workflow"],
            "GITHUB_JOB": context["job"], "GITHUB_RUN_ID": context["run_id"], "GITHUB_RUN_ATTEMPT": context["run_attempt"],
            "GITHUB_SHA": context["source_revision"], "GITHUB_REF": context["ref"], "SLOT": route.SLOT, "SUITE": "desktop",
            "TEST_MODULES": route.MODULE, "TEST_FOCUS": route.ENTRY_FOCUS, "NATIVECMPKIT_NATIVE_UI_TESTS": "true"}


def args(operation="plan"):
    return argparse.Namespace(operation=operation, suite="desktop", module=[route.MODULE], focus=route.ENTRY_FOCUS,
                              simulator=None, android_emulator=None, kotlin_user_home=None, reserve_mib=8192, timeout=4200,
                              output=route.OUTPUT if operation == "run" else None)


def declared_native_names(names):
    return {name for name in names if name.startswith(("calf-share/native/", "calf-share/src/desktopMain/")) or
            name in {"calf-share/build.gradle.kts", "rust-toolchain.toml", "scripts/native/artifacts.py",
                     "convention-plugins/src/main/kotlin/NativeLibraries.kt"}}


@contextmanager
def model():
    """Independent fixture authoring; no native processes, real runtime or keys."""
    with tempfile.TemporaryDirectory(prefix="appkit607-model-") as folder:
        root = Path(folder).resolve()
        source_names = source.fixture_inputs(ROOT)
        for name in sorted(source_names):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        before = {name: digest((root / name).read_bytes()) for name in sorted(source_names)}
        native = {name: before[name] for name in sorted(declared_native_names(before))}
        parent = root / route.PARENT
        parent.mkdir(parents=True)
        context = model_context()
        git = {"source_revision": context["source_revision"], "source_tree_dirty": False}
        base = time.time_ns() - 10_000_000_000
        def utc(ns):
            seconds, nanos = divmod(ns, 1_000_000_000)
            return (dt.datetime.fromtimestamp(seconds, dt.timezone.utc) + dt.timedelta(microseconds=nanos // 1000)).isoformat()
        binary_name = route.PARENT + "/cargo-target/aarch64-apple-darwin/debug/deps/appkit_lifecycle-abc607"
        binary = root / binary_name
        binary.parent.mkdir(parents=True)
        binary.write_bytes(struct.pack("<IIIIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 0, 0, 0) + b"UNEXECUTED-MODEL607")
        binary.chmod(0o700)
        os.utime(binary, ns=(base, base))
        file = identity(binary)
        compiler = {"release": "1.98.0", "host": "aarch64-apple-darwin", "commit-hash": "c" * 40, "commit-date": "2026-10-01"}
        runtime = {"host": {"system": "Darwin", "architecture": "arm64", "macos_version": "15.7.1", "macos_build": "24G200",
                            "python": "3.13.1"}, "rust": compiler.copy(), "cargo": compiler.copy(),
                   "xcode": {"version": "26.2", "build": "17C20"}, "macos_sdk": {"version": "26.2", "build": "25C20"},
                   "toolchain_executables": {name: {"path_sha256": digest(name.encode()), **file} for name in ("rustup", "rustc", "cargo", "clang")},
                   "graphical_session_probe_exit_zero": True, "native_ui_optin": True,
                   "visible_picker_or_recipient_verified": False, "launchctl_payload_archived": False}
        def execution(folder, role, pid, start, stdout):
            logs = []
            for stream, payload in (("stdout", stdout), ("stderr", b"")):
                name = folder + "/" + role + "." + stream + ".private.log"
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
                logs.append({"relative_path": name, **identity(path)})
            return {"started": True, "passed": True, "exit_code": 0, "stop_reason": None, "pid": pid,
                    "started_at_ns": start, "ended_at_ns": start + 100_000_000, "elapsed_seconds": 0.1,
                    "complete_log_within_size_bound": True, "private_logs": logs,
                    "cleanup": {"leader_reaped": True, "group_empty": True, "clean": True,
                                "forced": False, "term_sent": False, "kill_sent": False}}
        compilation = execution(route.PARENT, "cargo", 900001, base, b"UNEXECUTED cargo fixture; not a compiler result\n")
        artifact = {"relative_path": binary_name, "package": "calf-share-native@0.1.0", "test_target": "appkit_lifecycle",
                    "source_path": "calf-share/native/tests/appkit_lifecycle_main.rs",
                    "source_sha256": before["calf-share/native/tests/appkit_lifecycle_main.rs"], "rust_target": "aarch64-apple-darwin",
                    "macho_file_type": "MH_EXECUTE", "fresh_cargo_artifact": True, "diagnostics": {"errors": 0, "warnings": 0}, **file}
        cases, reports, runs = [], [], []
        for index, case in enumerate(route.CASES):
            pid, start = 900002 + index, base + (index + 1) * 200_000_000
            folder = route.PARENT + "/cases/" + case
            child_dir = root / folder; child_dir.mkdir(parents=True)
            original_name = route.REPORT_PARENT + "/process-" + str(pid) + "/TEST-" + case + ".xml"
            original = root / original_name; original.parent.mkdir(parents=True)
            xml = (f'<testsuite name="{route.SUITE}" tests="1" failures="0" errors="0" skipped="0">'
                   f'<testcase classname="{route.CLASS}" name="{case}" time="0.100000">'
                   f'<system-out>{route.WITNESS}</system-out></testcase></testsuite>').encode()
            original.write_bytes(xml); os.utime(original, ns=(start, start))
            copied = child_dir / "fresh-reports" / original.name; copied.parent.mkdir(); copied.write_bytes(xml)
            row = {"source_relative_path": original_name, "artifact_relative_path": "fresh-reports/" + original.name,
                   "case": case, **identity(original)}
            case_row = {"classname": route.CLASS, "name": case, "status": "passed"}
            marker = {"name": case, "passed": True, "live": 0, "registry": 0, "cleanup": True}
            native_execution = execution(folder, "native", pid, start,
                                         (f"NATIVECMPKIT_APPKIT_CASE name={case} passed=true seconds=0.100000 live=0 registry=0 cleanup=true\n").encode())
            record = {"case": case, "passed": True, "errors": [], "phase": "final-custody",
                      "native_case_arguments": ["--case=" + case], "native_command": [binary_name, "--case=" + case],
                      "git_before": git, "git_after": git, "runtime_before": runtime, "runtime_after": runtime,
                      "artifact_before": file, "artifact_after": file, "native_execution": native_execution,
                      "reports_held": True, "preexisting_reports_unchanged": True,
                      "native_reports": {"passed": True, "errors": [], "testcases": [case_row], "console_markers": [marker],
                                         "reports": [row], "preexisting_reports_unchanged": True}}
            for key in ("inputs_after", "native_inputs_after", "git_after", "runtime_after", "artifact_after"):
                record[key + "_held"] = True
            for name, value in (("inputs-before.json", before), ("inputs-after.json", before),
                                ("native-inputs-before.json", native), ("native-inputs-after.json", native),
                                ("runtime-before.json", runtime), ("runtime-after.json", runtime)):
                write_json(child_dir / name, value)
            write_json(child_dir / "receipt.json", record)
            cases.append(case_row); reports.append({**row, "artifact_relative_path": "cases/" + case + "/" + row["artifact_relative_path"]}); runs.append(record)
        final = report_inventory(root)
        summary = {"passed": True, "errors": [], "testcases": cases,
                   "console_markers": [{"name": case, "passed": True, "live": 0, "registry": 0, "cleanup": True} for case in route.CASES],
                   "reports": reports, "reached_original_xml": 6, "accepted_xml_cases": 6,
                   "remaining_unexecuted_cases": [], "preexisting_reports_unchanged": True,
                   "source_report_state_sha256": digest(json.dumps(final, sort_keys=True).encode())}
        receipt = {"schema_version": 1, "workflow_context": context, "platform": "macos-arm64", "rust_target": "aarch64-apple-darwin",
                   "rust_toolchain": "1.98.0", "exact_native_cases": list(route.CASES), "compile_once": True, "stop_on_first_failure": True,
                   "missing_only_share630": True, "native_command": None, "native_case_arguments": None, "stress_selected": False,
                   "publication_performed": False, "release_readiness_verified": False, "raw_control_flag_exported": False,
                   "raw_control_flag_independently_observed": False, "started_at_utc": utc(base), "finished_at_utc": utc(base + 2_000_000_000),
                   "passed": True, "errors": [], "phase": "final-custody", "inputs_held": True, "native_inputs_held": True,
                   "artifact_held": True, "reports_held": True, "owned_lock_released": True, "git_before": git, "git_after": git,
                   "inputs_after": {"count": len(before), "sha256": digest("".join(f"{d}  {n}\n" for n, d in sorted(before.items())).encode())},
                   "native_inputs_after": {"count": len(native), "sha256": digest("".join(f"{d}  {n}\n" for n, d in sorted(native.items())).encode())},
                   "runtime_before": runtime, "runtime_after": runtime, "compilation": compilation,
                   "artifact_before": artifact, "artifact_after": file,
                   "control_failure_witness": {"source_path": "calf-share/native/tests/appkit_lifecycle/cases.rs",
                                               "source_sha256": before["calf-share/native/tests/appkit_lifecycle/cases.rs"],
                                               "compiled_with_admitted_executable": True, "source_bound_failed_control_gate_verified": True,
                                               "raw_control_flag_exported": False, "raw_control_flag_independently_observed": False},
                   "native_reports": summary, "native_case_runs": runs, "reports_after": {"inventory_captured": True}}
        for name, value in (("inputs-before.json", before), ("inputs-after.json", before), ("native-inputs-before.json", native),
                            ("native-inputs-after.json", native), ("runtime-before.json", runtime), ("runtime-after.json", runtime),
                            ("reports-after.json", final), ("receipt.json", receipt)):
            write_json(parent / name, value)
        yield root, receipt, context


def save_parent(root, receipt):
    write_json(root / route.PARENT / "receipt.json", receipt)


def save_child(root, receipt, index):
    record = receipt["native_case_runs"][index]
    write_json(root / route.PARENT / "cases" / record["case"] / "receipt.json", record)
    save_parent(root, receipt)


def hook_function(node, name, namespace):
    function = ast.FunctionDef(name=name, args=ast.arguments(posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[],
                                                          kwarg=None, defaults=[]), body=[node, ast.Return(ast.Constant("unselected"))],
                               decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(module, "NEW607-owning-hook-only", "exec"), namespace)
    return namespace[name]


class AppKitOnly607Tests(unittest.TestCase):
    def test01_new_plan_six_only_no_commands_and_existing_report_ingress(self):
        value = route.plan(ROOT)
        self.assertEqual(value["profile"], "macos-share-missing-lifecycle")
        self.assertEqual(value["Gradle_tasks"], [])
        self.assertEqual([row["name"] for row in value["expected"][0]["required_testcases"]], list(route.CASES))
        self.assertEqual(value["expected"][0]["report_directory"], route.PARENT + "/cases")
        self.assertEqual(value["accepted_JNI3_reused_not_selected"], list(route.ACCEPTED_JNI))
        self.assertEqual(value["accepted_AppKit2_reused_not_selected"], ["cancel_before_dispatch", "no_key_window"])
        for key in ("native_tests_executed_here", "JNI_tests_executed_here", "Gradle_executions_here"):
            self.assertEqual(value[key], 0)
        self.assertFalse(value["release_ready"])
        self.assertFalse(value["native_cause_verified"])
        self.assertFalse(value["outer_CI_history_composition_qualified_here"])

    def test02_exact_three_postimages_roundtrip_without_workflow_or_native_change(self):
        manifest = source._document(ROOT)
        self.assertEqual(set(manifest["bindings"]), source.BOUND)
        for name, row in manifest["bindings"].items():
            raw = (ROOT / name).read_bytes()
            before = source.current_source_before_appkit_only(name, raw, ROOT)
            self.assertEqual(digest(before), row["before_sha256"])
            forward = before
            for fragment in row["fragments"]:
                self.assertEqual(forward.count(fragment["before"].encode()), 1)
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(forward, raw)
        import macos_share_ci668_composition as latest
        for name in (".github/workflows/gradle.yml", "scripts/ci/workflow_matrix.py", "calf-share/native/tests/appkit_lifecycle/cases.rs"):
            self.assertIn(name, manifest["unchanged_inputs"])
            raw = (ROOT / name).read_bytes()
            qualified = latest.current_source_in_view(name, raw, latest.SHARE_VIEW, ROOT)
            self.assertEqual(digest(qualified), manifest["unchanged_inputs"][name])

    def test03_old_is_history_not_current_and_unknown_does_not_get_certified(self):
        for name, row in source._document(ROOT)["bindings"].items():
            raw = (ROOT / name).read_bytes(); before = source.source_before_appkit_only(name, raw, ROOT)
            self.assertEqual(source.peel_appkit_only_for_history(name, before, ROOT), before)
            self.assertEqual(source.source_before_appkit_only(name, before, ROOT), before)
            with self.assertRaises(ValueError):
                source.current_source_before_appkit_only(name, before, ROOT)
            with self.assertRaises(ValueError):
                source.source_before_appkit_only(name, raw + b"\n# outside fragment\n", ROOT)
            self.assertEqual(source.peel_appkit_only_for_history(name, b"unknown", ROOT), b"unknown")

    def test04_full_source_tail_tamper_fails_current_guard(self):
        with model() as (root, _, _):
            target = root / "scripts/ci/library_tests.py"
            target.write_bytes(target.read_bytes() + b"\n# unreviewed tail\n")
            with self.assertRaises(ValueError):
                route.plan(root)

    def test05_observation609_native_and_historical_pins_stay_exact(self):
        document = source._document(ROOT)
        old = json.loads((ROOT / "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json").read_bytes())
        self.assertEqual(document["predecessor609"]["manifest_sha256"], digest((ROOT / "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json").read_bytes()))
        self.assertFalse(document["predecessor609"]["native_readiness_fix_included"])
        cases = "calf-share/native/tests/appkit_lifecycle/cases.rs"
        self.assertEqual(digest((ROOT / cases).read_bytes()), old["bindings"][cases]["after_sha256"])
        self.assertIn('pump_until("Owned AppKit window did not become key", || {', (ROOT / cases).read_text())
        self.assertIn('assert!(Instant::now() < deadline, "{reason}");', (ROOT / cases).read_text())
        self.assertIn('let deadline = Instant::now() + Duration::from_secs(10);', (ROOT / cases).read_text())
        self.assertEqual(old["bindings"][cases]["before_sha256"], "9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b")
        workflow = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertEqual(workflow.count("--missing-only-share630 --output"), 1)
        self.assertIn("JNI timeout below remains independent", workflow)  # Dated comment explicitly corrected in new docs.

    def test06_new_derivative_owner_and_union_preserve_old_observation_manifest(self):
        name = "scripts/ci/macos_share_key_wait_observation.py"
        tree = ast.parse((ROOT / name).read_text())
        old = json.loads((ROOT / "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json").read_bytes())
        namespace = {"ROOT": ROOT, "OWNER_RELATIVE": name, "SPEC_RELATIVE": "scripts/ci/fixtures/macos-share-key-wait-observation-source-inverse.json",
                     "SPEC_SHA256": source._document(ROOT)["predecessor609"]["manifest_sha256"], "MAX_SOURCE_BYTES": 4 * 1024 * 1024,
                     "sha": digest, "appkit_only": source, "Path": Path, "_ordinary_bytes": lambda root, name: source.ordinary_bytes(root, name),
                     "_document": lambda: old}
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in
                    {"_identity", "source_before_key_wait", "current_source_before_key_wait", "peel_key_wait_for_history", "validate_current_sources", "fixture_inputs"}]
        owner = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "OWNER_SHA256" for target in node.targets))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[owner, *selected], type_ignores=[])), "NEW607-derivative-hooks-only", "exec"), namespace)
        self.assertEqual(namespace["OWNER_SHA256"], source._document(ROOT)["bindings"][name]["before_sha256"])
        self.assertTrue(namespace["validate_current_sources"](ROOT))
        self.assertTrue(source.fixture_inputs(ROOT) <= namespace["fixture_inputs"]())
        path = "scripts/ci/macos_share_appkit_lifecycle.py"; raw = (ROOT / path).read_bytes()
        self.assertEqual(digest(namespace["current_source_before_key_wait"](path, raw)), old["bindings"][path]["before_sha256"])
        self.assertEqual(namespace["peel_key_wait_for_history"](path, raw), namespace["source_before_key_wait"](path, raw))

    def test07_only_exact_library_cli_hook_redirects_to_passive_route(self):
        tree = ast.parse((ROOT / "scripts/ci/library_tests.py").read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        hook = next(node for node in main.body if isinstance(node, ast.If) and ast.unparse(node.test) == "args.focus == share_missing.FOCUS")
        calls = []
        stub = types.ModuleType("macos_share_appkit_only_route")
        stub.main_for_existing_profile = lambda root, arguments: calls.append((root, arguments.operation)) or 607
        namespace = {"ROOT": ROOT, "share_missing": types.SimpleNamespace(FOCUS=route.ENTRY_FOCUS), "args": args()}
        wrapped = hook_function(hook, "only_new_cli_hook", namespace)
        with patch.dict(sys.modules, {"macos_share_appkit_only_route": stub}):
            self.assertEqual(wrapped(), 607)
            namespace["args"] = args("run"); self.assertEqual(wrapped(), 607)
            namespace["args"].focus = "another-focus"; self.assertEqual(wrapped(), "unselected")
        self.assertEqual(calls, [(ROOT, "plan"), (ROOT, "run")])

    def test08_direct_retired_run_refuses_before_any_output_or_gradle(self):
        tree = ast.parse((ROOT / "scripts/ci/library_tests.py").read_text())
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        self.assertIsInstance(run.body[0], ast.If)
        namespace = {"focus": route.ENTRY_FOCUS, "share_missing": types.SimpleNamespace(FOCUS=route.ENTRY_FOCUS)}
        wrapped = hook_function(run.body[0], "new_direct_run_refusal_only", namespace)
        with self.assertRaisesRegex(ValueError, "Accepted Share JNI3 are retired"):
            wrapped()
        namespace["focus"] = None; self.assertEqual(wrapped(), "unselected")

    def test09_missing_parent_context_hook_precedes_lock_and_compile_only(self):
        tree = ast.parse((ROOT / "scripts/ci/macos_share_appkit_lifecycle.py").read_text())
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        attempt = next(node for node in run.body if isinstance(node, ast.Try))
        self.assertEqual(ast.unparse(attempt.body[0].test), "missing_only")
        self.assertIn("workflow_context", ast.unparse(attempt.body[0]))
        self.assertIn("relative_path", ast.unparse(attempt.body[1]))
        stub = types.ModuleType("macos_share_appkit_only_route"); stub.workflow_context = lambda: model_context()
        receipt = {}; namespace = {"missing_only": True, "receipt": receipt}
        wrapped = hook_function(attempt.body[0], "only_new_context_hook", namespace)
        with patch.dict(sys.modules, {"macos_share_appkit_only_route": stub}):
            wrapped(); self.assertEqual(receipt["workflow_context"], model_context())
            receipt.clear(); namespace["missing_only"] = False; wrapped(); self.assertEqual(receipt, {})

    def test10_actual_environment_admission_is_exact_and_missing_or_foreign_refuses(self):
        values = model_environment()
        with patch.dict(os.environ, values, clear=True):
            self.assertEqual(route.workflow_context(), model_context())
        for key, wrong in (("GITHUB_ACTIONS", "false"), ("GITHUB_RUN_ID", "0001"), ("GITHUB_RUN_ATTEMPT", "0"),
                           ("GITHUB_SHA", "B" * 40), ("GITHUB_REF", "refs/heads/main"), ("GITHUB_JOB", "another"),
                           ("TEST_FOCUS", "macos-native-share-lifecycle"), ("NATIVECMPKIT_NATIVE_UI_TESTS", "1")):
            with self.subTest(key=key), patch.dict(os.environ, {**values, key: wrong}, clear=True), self.assertRaises(ValueError):
                route.workflow_context()
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            route.workflow_context()

    def test11_root_and_relative_traversal_are_never_admitted(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-path-") as folder:
            root = Path(folder).resolve(); (root / "safe").write_bytes(b"data")
            for value in ("../safe", "/safe", "safe/../safe", "./safe", "safe\\x", "safe//x", "safe\n"):
                with self.subTest(value=value), self.assertRaises((OSError, ValueError)):
                    source.ordinary_bytes(root, value)
            with self.assertRaises(ValueError):
                source.ordinary_bytes(Path("relative"), "safe")

    def test12_symlink_alias_directory_and_fifo_files_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-link-") as folder:
            root = Path(folder).resolve(); target = root / "a"; target.write_bytes(b"data")
            (root / "link").symlink_to(target); os.link(target, root / "alias"); (root / "directory").mkdir(); os.mkfifo(root / "fifo")
            for value in ("a", "alias", "link", "directory", "fifo"):
                with self.subTest(value=value), self.assertRaises((OSError, ValueError)):
                    source.ordinary_bytes(root, value)

    def test13_parent_replaced_by_symlink_to_held_directory_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-parent-") as folder:
            root = Path(folder).resolve(); (root / "parent").mkdir(); (root / "parent/file").write_bytes(b"same")
            real = os.read; changed = False
            def replace_parent(fd, count):
                nonlocal changed
                payload = real(fd, count)
                if not changed:
                    changed = True; (root / "parent").rename(root / "parked"); (root / "parent").symlink_to(root / "parked", target_is_directory=True)
                return payload
            with patch.object(source.os, "read", side_effect=replace_parent), self.assertRaisesRegex(ValueError, "directory-path-custody-changed"):
                source.ordinary_bytes(root, "parent/file")

    def test14_identical_byte_leaf_replacement_cannot_replace_inode_custody(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-leaf-") as folder:
            root = Path(folder).resolve(); (root / "file").write_bytes(b"same"); (root / "replacement").write_bytes(b"same")
            real = os.read; changed = False
            def replace_file(fd, count):
                nonlocal changed
                payload = real(fd, count)
                if not changed:
                    changed = True; os.replace(root / "replacement", root / "file")
                return payload
            with patch.object(source.os, "read", side_effect=replace_file), self.assertRaises(ValueError):
                source.ordinary_bytes(root, "file")

    def test15_large_artifact_bound_is_distinct_from_source_and_typed(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-bound-") as folder:
            root = Path(folder).resolve()
            with (root / "large").open("wb") as stream:
                stream.truncate(source.MAX_SOURCE + 1)
            with self.assertRaises(ValueError):
                source.ordinary_bytes(root, "large")
            self.assertEqual(len(source.ordinary_bytes(root, "large", source.MAX_READ)[0]), source.MAX_SOURCE + 1)
            for maximum in (True, 0, source.MAX_READ + 1):
                with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                    source.ordinary_bytes(root, "large", maximum)

    def test16_owned_cleanup_is_independent_and_preserves_primary_refusal(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-close-") as folder:
            root = Path(folder).resolve(); (root / "a").write_bytes(b"data"); os.link(root / "a", root / "alias")
            real_open, real_close = os.open, os.close
            foreign = real_open(root / "a", os.O_RDONLY); opened, closed = [], []
            def opening(*a, **kw):
                value = real_open(*a, **kw); opened.append(value); return value
            def closing(fd):
                real_close(fd); closed.append(fd)
                if len(closed) == 1:
                    raise OSError("synthetic cleanup failure, descriptor was already closed")
            try:
                with patch.object(source.os, "open", side_effect=opening), patch.object(source.os, "close", side_effect=closing):
                    with self.assertRaisesRegex(ValueError, "bounded-ordinary-unaliased") as captured:
                        source.ordinary_bytes(root, "a")
                self.assertEqual(closed, list(reversed(opened)))
                self.assertTrue(captured.exception.__notes__)
                self.assertNotIn(foreign, closed); os.fstat(foreign)
            finally:
                real_close(foreign)

    def test17_cleanup_failure_alone_cannot_turn_file_read_into_pass(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-closeonly-") as folder:
            root = Path(folder).resolve(); (root / "a").write_bytes(b"data")
            real_close = os.close; closed = []
            def closing(fd):
                real_close(fd); closed.append(fd)
                if len(closed) == 1:
                    raise OSError("synthetic failure after close")
            with patch.object(source.os, "close", side_effect=closing), self.assertRaisesRegex(ValueError, "owned-AppKit-descriptor-cleanup-refused"):
                source.ordinary_bytes(root, "a")
            self.assertEqual(len(closed), 2)

    def test18_positive_model_six_original_result_reference_executes_nothing(self):
        with model() as (root, _, context), patch.object(subprocess, "Popen", side_effect=AssertionError("native forbidden")), \
                patch.object(subprocess, "run", side_effect=AssertionError("command forbidden")):
            value = route.reference_parent(root, context, time.time_ns())
            self.assertTrue(value["passed"])
            self.assertEqual(value["native_cases_reached"], list(route.CASES))
            self.assertFalse(value["fresh_JVM_XML_created"])
            self.assertEqual(value["owning_native_test_count_referenced_not_reexecuted"], 6)
            self.assertFalse((root / route.OUTPUT).exists())

    def test19_first_failed_case_stays_failed_and_later_five_are_unexecuted(self):
        with model() as (root, receipt, context):
            receipt["passed"] = False; receipt["phase"] = "native"; receipt["errors"] = ["original-key-wait-failed"]
            receipt["native_reports"]["testcases"] = [{"classname": route.CLASS, "name": route.CASES[0], "status": "failed"}]
            save_parent(root, receipt)
            value = route.reference_parent(root, context, time.time_ns())
            self.assertFalse(value["passed"]); self.assertEqual(value["native_cases_reached"], [route.CASES[0]])
            self.assertEqual(value["native_cases_unexecuted"], list(route.CASES[1:]))
            with patch.dict(os.environ, model_environment(), clear=True), redirect_stdout(io.StringIO()):
                self.assertEqual(route.main_for_existing_profile(root, args("run")), 1)
            stored = json.loads((root / route.OUTPUT / "receipt.json").read_bytes())
            self.assertFalse(stored["passed"]); self.assertEqual(stored["JNI_tests_executed_here"], 0)

    def test20_cross_run_attempt_sha_job_slot_or_profile_is_not_reuse(self):
        with model() as (root, receipt, context):
            original = copy.deepcopy(receipt)
            for key, wrong in (("run_id", "777778"), ("run_attempt", "2"), ("source_revision", "a" * 40),
                               ("job", "another"), ("slot", "desktop-macos-x64"), ("profile", "macos-share-lifecycle")):
                receipt = copy.deepcopy(original); receipt["workflow_context"][key] = wrong; save_parent(root, receipt)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    route.reference_parent(root, context, time.time_ns())

    def test21_stale_future_long_or_non_utc_parent_is_refused(self):
        with model() as (root, receipt, context):
            original = copy.deepcopy(receipt)
            for key, wrong in (("finished_at_utc", "2000-01-01T00:00:00+00:00"), ("finished_at_utc", "2099-01-01T00:00:00+00:00"),
                               ("started_at_utc", "2000-01-01T00:00:00+00:00"), ("started_at_utc", "2026-11-04T00:00:00+02:00"),
                               ("started_at_utc", True)):
                receipt = copy.deepcopy(original); receipt[key] = wrong; save_parent(root, receipt)
                with self.subTest(key=key, wrong=wrong), self.assertRaises(ValueError):
                    route.reference_parent(root, context, time.time_ns())

    def test22_source_or_native_map_drift_and_required_omission_refuse(self):
        with model() as (root, receipt, context):
            path = root / route.PARENT / "inputs-after.json"; original = path.read_bytes()
            value = json.loads(original); value["scripts/ci/library_tests.py"] = "f" * 64; write_json(path, value)
            with self.assertRaises(ValueError):
                route.reference_parent(root, context, time.time_ns())
            path.write_bytes(original)
            for name in ("native-inputs-before.json", "native-inputs-after.json"):
                path = root / route.PARENT / name; value = json.loads(path.read_bytes()); value.pop("rust-toolchain.toml"); write_json(path, value)
            native = json.loads((root / route.PARENT / "native-inputs-before.json").read_bytes())
            receipt["native_inputs_after"] = {"count": len(native), "sha256": digest("".join(f"{d}  {n}\n" for n, d in sorted(native.items())).encode())}
            save_parent(root, receipt)
            with self.assertRaisesRegex(ValueError, "native-build-source-map-required"):
                route.reference_parent(root, context, time.time_ns())

    def test23_dirty_git_changed_runtime_or_malformed_effective_tools_refuse(self):
        with model() as (root, receipt, context):
            original = copy.deepcopy(receipt)
            for changes in ({"git_after": {"source_revision": "b" * 40, "source_tree_dirty": True}},
                            {"runtime_after": None}, {"runtime_before": {"host": None}}):
                receipt = copy.deepcopy(original); receipt.update(changes); save_parent(root, receipt)
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    route.reference_parent(root, context, time.time_ns())
            runtime = copy.deepcopy(original["runtime_before"])
            runtime["toolchain_executables"]["rustc"]["inode"] = True
            with self.assertRaises(ValueError):
                route._runtime(runtime)

    def test24_failed_compilation_or_wrong_macho_cpu_type_and_mode_refuse(self):
        with model() as (root, receipt, context):
            receipt["compilation"]["passed"] = False; save_parent(root, receipt)
            with self.assertRaises(ValueError):
                route.reference_parent(root, context, time.time_ns())
        with model() as (root, receipt, context):
            binary = root / receipt["artifact_before"]["relative_path"]; raw = bytearray(binary.read_bytes()); struct.pack_into("<I", raw, 12, 6); binary.write_bytes(raw)
            current = identity(binary); receipt["artifact_before"].update(current); receipt["artifact_after"] = current; save_parent(root, receipt)
            with self.assertRaisesRegex(ValueError, "held-actual-AppKit-executable"):
                route.reference_parent(root, context, time.time_ns())
        with self.assertRaises(ValueError):
            route._execution({"started": True, "passed": True, "elapsed_seconds": 10 ** 1000}, 240)

    def test25_duplicate_pid_or_forced_unreaped_nonempty_cleanup_refuses(self):
        with model() as (root, receipt, context):
            original = copy.deepcopy(receipt)
            for key in ("forced", "leader_reaped", "group_empty"):
                receipt = copy.deepcopy(original); execution = receipt["native_case_runs"][0]["native_execution"]
                execution["cleanup"][key] = key == "forced"; save_child(root, receipt, 0)
                with self.subTest(key=key), self.assertRaises(ValueError):
                    route.reference_parent(root, context, time.time_ns())
            receipt = copy.deepcopy(original)
            save_child(root, receipt, 0)  # Restore the prior negative-case fixture; preserve strict PID assertion.
            receipt["native_case_runs"][1]["native_execution"]["pid"] = receipt["native_case_runs"][0]["native_execution"]["pid"]
            save_child(root, receipt, 1)
            with self.assertRaisesRegex(ValueError, "serial-fresh-owned-AppKit-PIDs"):
                route.reference_parent(root, context, time.time_ns())

    def test26_skipped_failed_wrong_case_or_dtd_xml_cannot_be_accepted(self):
        case = route.CASES[0]
        valid = (f'<testsuite name="{route.SUITE}" tests="1" failures="0" errors="0" skipped="0">'
                 f'<testcase classname="{route.CLASS}" name="{case}" time="0.100000"><system-out>{route.WITNESS}</system-out></testcase></testsuite>').encode()
        route._xml(valid, case)
        for raw in (valid.replace(b'skipped="0"', b'skipped="1"'), valid.replace(b'failures="0"', b'failures="1"'),
                    valid.replace(case.encode(), b"another_case"), b'<!DOCTYPE fake>' + valid, valid.replace(b"cleanup=true", b"cleanup=false")):
            with self.subTest(raw_hash=digest(raw)), self.assertRaises((ValueError, ET.ParseError)):
                route._xml(raw, case)

    def test27_original_stdout_marker_not_just_receipt_or_duplicate_model_witness(self):
        with model() as (root, receipt, context):
            record = receipt["native_case_runs"][0]; log = record["native_execution"]["private_logs"][0]
            path = root / log["relative_path"]; path.write_bytes(path.read_bytes() * 2)
            log.update(identity(path)); save_child(root, receipt, 0)
            with self.assertRaisesRegex(ValueError, "one-original-AppKit-console-marker"):
                route.reference_parent(root, context, time.time_ns())
        with self.assertRaises(UnicodeError):
            route._console(b"\xff", route.CASES[0])

    def test28_extra_reports_and_released_lock_presence_are_not_ignored(self):
        with model() as (root, _, context):
            (root / route.REPORT_PARENT / "foreign-report.xml").write_bytes(b"FOREIGN-model")
            with self.assertRaisesRegex(ValueError, "report-inventory-held"):
                route.reference_parent(root, context, time.time_ns())
        with model() as (root, _, context):
            (root / "build/ci-verification/.macos-share-appkit-lifecycle.lock").mkdir()
            with self.assertRaisesRegex(ValueError, "lock-release-absence"):
                route.reference_parent(root, context, time.time_ns())

    def test29_malformed_data_shapes_are_consistent_refusals_not_attribute_errors(self):
        with model() as (root, receipt, context):
            original = copy.deepcopy(receipt)
            for key, value in (("native_reports", []), ("native_case_runs", [None] * 6), ("artifact_before", []),
                               ("compilation", []), ("runtime_before", [])):
                receipt = copy.deepcopy(original); receipt[key] = value; save_parent(root, receipt)
                with self.subTest(key=key), self.assertRaises((ValueError, TypeError, KeyError)):
                    route.reference_parent(root, context, time.time_ns())
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'[' * 2000 + b']' * 2000):
            with self.subTest(raw_hash=digest(raw)), self.assertRaises(ValueError):
                source.json_bytes(raw)

    def test30_writer_rejects_symlink_missing_ancestors_and_foreign_output(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-writer-") as folder:
            root = Path(folder).resolve(); (root / "outside-owned-fixture").mkdir(); (root / "build").symlink_to(root / "outside-owned-fixture", target_is_directory=True)
            with self.assertRaises((ValueError, OSError)):
                route._write_reference(root, {"passed": False})
            self.assertEqual(list((root / "outside-owned-fixture").iterdir()), [])
        with tempfile.TemporaryDirectory(prefix="appkit607-writer-missing-") as folder:
            root = Path(folder).resolve()
            with self.assertRaises((ValueError, OSError)):
                route._write_reference(root, {"passed": False})
            self.assertFalse((root / "build").exists())
        with model() as (root, _, _):
            output = root / route.OUTPUT; output.mkdir(); (output / "foreign").write_bytes(b"FOREIGN")
            with self.assertRaises(FileExistsError):
                route._write_reference(root, {"passed": True})
            self.assertEqual((output / "foreign").read_bytes(), b"FOREIGN")

    def test31_writer_partial_write_and_cleanup_preserve_owned_and_foreign_fds(self):
        with tempfile.TemporaryDirectory(prefix="appkit607-writer-fd-") as folder:
            root = Path(folder).resolve(); (root / "build/ci-verification").mkdir(parents=True); (root / "foreign").write_bytes(b"FOREIGN")
            real_open, real_close, real_write = os.open, os.close, os.write
            foreign = real_open(root / "foreign", os.O_RDONLY); opened, closed = [], []
            def opening(*a, **kw):
                fd = real_open(*a, **kw); opened.append(fd); return fd
            def closing(fd):
                real_close(fd); closed.append(fd)
            try:
                with patch.object(source.os, "open", side_effect=opening), patch.object(source.os, "close", side_effect=closing), \
                        patch.object(route.os, "write", side_effect=lambda fd, raw: real_write(fd, raw[:7])):
                    route._write_reference(root, {"passed": False, "model_only": True})
                self.assertEqual(set(opened), set(closed)); self.assertNotIn(foreign, closed); os.fstat(foreign)
                self.assertEqual(json.loads((root / route.OUTPUT / "receipt.json").read_bytes()), {"passed": False, "model_only": True})
            finally:
                real_close(foreign)

    def test32_model_main_is_same_profile_only_and_never_synthesizes_jvm_xml(self):
        with model() as (root, _, _), patch.dict(os.environ, model_environment(), clear=True), \
                patch.object(subprocess, "Popen", side_effect=AssertionError("native forbidden")), redirect_stdout(io.StringIO()):
            self.assertEqual(route.main_for_existing_profile(root, args("plan")), 0)
            self.assertFalse((root / route.OUTPUT).exists())
            self.assertEqual(route.main_for_existing_profile(root, args("run")), 0)
            stored = json.loads((root / route.OUTPUT / "receipt.json").read_bytes())
            self.assertEqual(stored["suite"], "native-AppKit-reference-not-JVM")
            self.assertFalse(stored["fresh_JVM_XML_created"])
            self.assertEqual(list((root / route.OUTPUT).iterdir()), [root / route.OUTPUT / "receipt.json"])
            self.assertEqual(stored["JNI_tests_executed_here"], 0); self.assertFalse(stored["release_ready"])
        for key, value in (("module", ["calf-ui"]), ("suite", "ios"), ("output", "build/ci-verification/foreign"),
                           ("reserve_mib", True), ("timeout", True), ("simulator", "fake-udid")):
            arguments = args("run"); setattr(arguments, key, value)
            with self.subTest(key=key), self.assertRaises(ValueError):
                route.main_for_existing_profile(ROOT, arguments)

    def test33_data_changed_after_first_read_is_not_a_final_held_reference(self):
        with model() as (root, _, context):
            original = route._reports_state; mutated = False
            def mutate_copy_at_final_inventory(*a, **kw):
                nonlocal mutated
                result = original(*a, **kw)
                if not mutated:
                    mutated = True
                    copy_path = root / route.PARENT / "cases" / route.CASES[0] / "fresh-reports" / ("TEST-" + route.CASES[0] + ".xml")
                    copy_path.write_bytes(copy_path.read_bytes() + b"\n")
                return result
            with patch.object(route, "_reports_state", side_effect=mutate_copy_at_final_inventory), self.assertRaisesRegex(ValueError, "file-custody-changed-before-final-reference"):
                route.reference_parent(root, context, time.time_ns())

    def test34_actual_pid_original_copy_freshness_and_summary_population_are_strict(self):
        with model() as (root, receipt, context):
            copied = root / route.PARENT / "cases" / route.CASES[0] / "fresh-reports" / ("TEST-" + route.CASES[0] + ".xml")
            copied.write_bytes(copied.read_bytes().replace(b"cleanup=true", b"cleanup=false"))
            with self.assertRaisesRegex(ValueError, "XML-byte-and-PID-custody"):
                route.reference_parent(root, context, time.time_ns())
        with model() as (root, receipt, context):
            receipt["native_reports"]["accepted_xml_cases"] = 5; save_parent(root, receipt)
            with self.assertRaisesRegex(ValueError, "all-six-actual-AppKit-outcomes"):
                route.reference_parent(root, context, time.time_ns())

    def test35_new_json_depth_bound_preserves_finite_data_and_refuses_deep_valid_payloads(self):
        shallow = b'[' * 32 + b'0' + b']' * 32
        value = source.json_bytes(shallow)
        for _ in range(32):
            self.assertEqual(len(value), 1); value = value[0]
        self.assertEqual(value, 0)
        with self.assertRaisesRegex(ValueError, "bounded-AppKit-JSON-depth-required"):
            source.json_bytes(b'[' * 65 + b'0' + b']' * 65)
        with self.assertRaisesRegex(ValueError, "bounded-AppKit-JSON-depth-required"):
            source.json_bytes(b'{"x":' * 65 + b'0' + b'}' * 65)


if __name__ == "__main__":
    unittest.main()
