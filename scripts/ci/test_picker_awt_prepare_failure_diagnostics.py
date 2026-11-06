"""Five NEW essential synthetic controls; no compiler/native/control replay.

Every process, Git revision, runtime and JDK/resource capture is mocked. Owned
temporary fixtures are data only. No actual Java/Gradle/Rust/AWT/network runs.
"""
import ast
from contextlib import ExitStack, redirect_stdout
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import picker_awt_generation as r
import picker_awt_prepare_failure as d
import picker_awt_preparation as p

ROOT = Path("/trusted-owned-root")
PRIVATE_SENTINEL = "PRIVATE_SYNTHETIC_OPERAND_NEVER_EXPORT"


def budget(clock=None):
    return r.shared.NativeBudget(clock=(lambda: 0) if clock is None else clock)


def failed_phase(body):
    payload = body.encode("utf-8")
    return {"started": True, "exit_code": 1, "capture_complete": True, "captured_bytes": len(payload),
            "private_capture_sha256": hashlib.sha256(payload).hexdigest(), "private_capture_fd_stat9": [1] * 9,
            "post_exit_group_state": "absent", "stop_reason": None, "elapsed_seconds": 0.1,
            "command": [PRIVATE_SENTINEL]}


def compiler_body(message="Unresolved reference: " + PRIVATE_SENTINEL):
    return "e: " + (ROOT / d.SOURCES["awt_generation_test"]).as_uri() + ":31:7 " + message + "\n"


def preparation():
    return "\n".join("> Task " + task for task in (d.TASKS["host_native_build"], *r.PREPARE_TASKS)) + "\nBUILD SUCCESSFUL in 1s\n"


def runtime(revision):
    return {"source_revision": revision, "source_tree_dirty": False, "host": {"system": "Darwin", "architecture": "arm64"},
            "java": {"major": 17, "version": "17.0.20"}, "rust": {"release": "1.98.0", "host": r.shared.TARGET},
            "compiler_runtime_fingerprint": "b" * 64}


class PickerAwtPreparationDiagnostics(unittest.TestCase):
    def assert_public(self, value):
        self.assertEqual({"schema_version", "status", "category", "diagnostic_code", "failed_task_id", "location",
                          "ambiguity", "cause_established", "required_task_states", "unavailable_code"}, set(value))
        self.assertIs(False, value["cause_established"])
        self.assertEqual(set(d.REQUIRED_TASK_IDS), set(value["required_task_states"]))
        encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        self.assertLessEqual(len(encoded), 4096)
        for forbidden in (PRIVATE_SENTINEL, ROOT.as_posix(), "https://", "file://", "Unresolved reference", "command", "Authorization"):
            self.assertNotIn(forbidden.encode(), encoded)

    def test_fixed_categories_tasks_and_pinned_numeric_locations_only(self):
        for message, code in (("Unresolved reference: " + PRIVATE_SENTINEL, "kotlin_unresolved_reference"),
                              ("Argument type mismatch: " + PRIVATE_SENTINEL, "kotlin_type_mismatch"),
                              ("Overload resolution ambiguity: " + PRIVATE_SENTINEL, "kotlin_overload_ambiguity"),
                              ("Cannot infer type for this parameter: " + PRIVATE_SENTINEL, "kotlin_type_inference")):
            with self.subTest(code=code):
                value = d.classify(ROOT, compiler_body(message))
                self.assert_public(value)
                self.assertEqual(("classified", "kotlin_compilation", code),
                                 (value["status"], value["category"], value["diagnostic_code"]))
                self.assertEqual({"source_id": "awt_generation_test", "line": 31, "column": 7}, value["location"])
        for key, relative in d.SOURCES.items():
            value = d.classify(ROOT, "e: " + (ROOT / relative).as_posix() + ": (1000000, 1): Type mismatch: " + PRIVATE_SENTINEL)
            self.assertEqual({"source_id": key, "line": 1000000, "column": 1}, value["location"])
            self.assert_public(value)
        for body, category, code in (("error: invalid source release: 99", "java_compilation", "java_compiler_error"),
                                     ("error[E0308]: " + PRIVATE_SENTINEL, "rust_compilation", "rust_compiler_error"),
                                     ("Plugin [id: 'fixed.synthetic', version: '1.0'] was not found in any of the following sources:",
                                      "gradle_configuration", "gradle_plugin_resolution"),
                                     ("Script compilation errors:", "gradle_configuration", "gradle_configuration_error"),
                                     ("Could not resolve all files for configuration ':synthetic'.", "dependency_resolution", "dependency_resolution_error")):
            value = d.classify(ROOT, body)
            self.assertEqual(("classified", category, code), (value["status"], value["category"], value["diagnostic_code"]))
            self.assert_public(value)
        for key, task in d.TASKS.items():
            value = d.classify(ROOT, "> Task " + task + " FAILED\nExecution failed for task '" + task + "'.")
            self.assertEqual("classified", value["status"])
            self.assertEqual(key, value["failed_task_id"])
            self.assertEqual("native_resource_task" if key in d.NATIVE_TASK_IDS else "task_execution", value["category"])
            self.assert_public(value)
        lines = ["> Task " + d.TASKS[key] + suffix for key, suffix in
                 (("desktop_resources", ""), ("runtime_classpath", " FROM-CACHE"), ("native_resources", " FAILED"))]
        value = d.classify(ROOT, "\n".join(lines))
        self.assertEqual({"desktop_resources": "executed_line", "runtime_classpath": "cached_line", "native_resources": "failed_line"},
                         value["required_task_states"])
        value = d.classify(ROOT, "Build file '" + (ROOT / d.SOURCES["root_build"]).as_posix() + "' line: 41\nScript compilation errors:")
        self.assertEqual({"source_id": "root_build", "line": 41, "column": None}, value["location"])
        self.assert_public(value)

    def test_unknown_ambiguous_and_oversize_private_text_never_exports_paths_urls_or_secrets(self):
        good = compiler_body()
        foreign = good.replace(ROOT.as_posix(), "/foreign-user/" + PRIVATE_SENTINEL)
        for body in (PRIVATE_SENTINEL + " https://invalid.example/private Authorization: PRIVATE", foreign,
                     "e: https://invalid.example/" + d.SOURCES["awt_generation_test"] + ":31:7 Unresolved reference: SECRET",
                     good.replace(":31:7 ", ":1000001:7 "), good.replace(":31:7 ", ":0:7 "),
                     good.replace("Unresolved reference: " + PRIVATE_SENTINEL, "Unsupported diagnostic: " + PRIVATE_SENTINEL),
                     "Build file '/foreign/" + PRIVATE_SENTINEL + "/build.gradle.kts' line: 41", good + good,
                     good + "error[E0308]: " + PRIVATE_SENTINEL,
                     "Execution failed for task ':foreign:PRIVATE'.\n" + good,
                     "> Task " + d.TASKS["native_resources"] + "\n> Task " + d.TASKS["native_resources"],
                     "Execution failed for task '" + d.TASKS["native_resources"] + "'.\nExecution failed for task '" + d.TASKS["desktop_test_compiler"] + "'."):
            value = d.classify(ROOT, body)
            self.assertEqual("unclassified", value["status"])
            self.assertIsNone(value["location"])
            self.assertIsNone(value["failed_task_id"])
            self.assert_public(value)
        self.assertTrue(d.classify(ROOT, good + good)["ambiguity"])
        for body, code in (("x" * (65536 + 1), "diagnostic_limit"), ("x" * 4097, "diagnostic_limit"),
                           ("\n" * 4097, "diagnostic_limit"), ("\x1b[31m" + good, "diagnostic_limit"),
                           ("\ud800", "UTF8_refused")):
            value = d.classify(ROOT, body)
            self.assertEqual(("unavailable", code), (value["status"], value["unavailable_code"]))
            self.assert_public(value)
        self.assertEqual("unclassified", d.classify(ROOT, ("x" * 4095 + "\n") * 16)["status"])
        self.assertEqual("unclassified", d.classify(ROOT, "\n" * 4096)["status"])
        for wrong_root in (Path("relative"), Path("/"), Path("/unsafe:root")):
            self.assertEqual("classifier_error", d.classify(wrong_root, good)["unavailable_code"])
        self.assert_public(d.unavailable(PRIVATE_SENTINEL))
        malformed = d.unavailable("classifier_error")
        malformed["diagnostic_code"] = PRIVATE_SENTINEL
        self.assertEqual("classifier_error", d.bounded_public(malformed)["unavailable_code"])

    def test_nonzero_complete_owned_prepare_is_the_only_eligible_phase(self):
        body, private = compiler_body(), ROOT / "build/ci-verification/synthetic/private"
        execution = failed_phase(body)
        with mock.patch.object(r.shared, "owned_phase", return_value=execution) as owner, mock.patch.object(r.shared, "read_private_log", return_value=body) as read:
            receipt = {"phases": {}}
            with self.assertRaisesRegex(r.Refusal, "^exact-owned-phase-exit-capture-or-group-refusal$"):
                r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(), receipt)
            self.assertEqual(1, owner.call_count)
            self.assertEqual(1, read.call_count)
            self.assertEqual("classified", receipt["prepare_failure_diagnostic"]["status"])
            self.assertNotIn("command", receipt["phases"]["prepare"])
            self.assert_public(receipt["prepare_failure_diagnostic"])
        cases = [(stage, execution) for stage in ("inventory", "junit")]
        cases += [("prepare", {**execution, key: value}) for key, value in
                  (("started", False), ("exit_code", True), ("exit_code", None), ("capture_complete", False),
                   ("post_exit_group_state", "unknown"), ("post_exit_group_state", "present"), ("stop_reason", PRIVATE_SENTINEL))]
        for stage, execution_case in cases:
            with mock.patch.object(r.shared, "owned_phase", return_value=execution_case), mock.patch.object(r.shared, "read_private_log") as read, mock.patch.object(d, "classify") as classify:
                receipt = {"phases": {}}
                with self.assertRaises(r.Refusal):
                    r.phase(ROOT, private, stage, [PRIVATE_SENTINEL], budget(), receipt)
                read.assert_not_called()
                classify.assert_not_called()
                self.assertNotIn("prepare_failure_diagnostic", receipt)
        with mock.patch.object(r.shared, "owned_phase", return_value={**execution, "exit_code": 0}), mock.patch.object(r.shared, "read_private_log", return_value=body) as read, mock.patch.object(d, "classify") as classify:
            receipt = {"phases": {}}
            self.assertEqual(body, r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(), receipt))
            self.assertEqual(1, read.call_count)
            classify.assert_not_called()
            self.assertNotIn("prepare_failure_diagnostic", receipt)
        for changes, code in (({"captured_bytes": 65537}, "diagnostic_limit"), ({"captured_bytes": -1}, "capture_identity_refused"),
                              ({"private_capture_sha256": PRIVATE_SENTINEL}, "capture_identity_refused")):
            with mock.patch.object(r.shared, "read_private_log") as read:
                value = r.prepare_failure_diagnostic(ROOT, "prepare", private / "prepare.log", {**execution, **changes}, budget())
                self.assertEqual(code, value["unavailable_code"])
                read.assert_not_called()
                self.assert_public(value)
        with mock.patch.object(r.shared, "read_private_log", return_value=body + PRIVATE_SENTINEL), mock.patch.object(d, "classify") as classify:
            value = r.prepare_failure_diagnostic(ROOT, "prepare", private / "prepare.log", execution, budget())
            self.assertEqual("capture_identity_refused", value["unavailable_code"])
            classify.assert_not_called()

    def test_classifier_and_cleanup_refusals_preserve_primary_exit_failure(self):
        body, private = compiler_body(), ROOT / "build/ci-verification/synthetic/private"
        execution = failed_phase(body)
        utf8 = r.Refusal("private-capture-not-valid-utf8")
        utf8.__cause__ = UnicodeError(PRIVATE_SENTINEL)
        for read_error, classify_error, code in ((OSError(PRIVATE_SENTINEL), None, "capture_unavailable"),
                                                 (r.Refusal("private-capture-payload-changed-after-owned-phase"), None, "capture_identity_refused"),
                                                 (utf8, None, "UTF8_refused"), (None, RuntimeError(PRIVATE_SENTINEL), "classifier_error")):
            primary = r.Refusal("exact-owned-phase-exit-capture-or-group-refusal")
            with mock.patch.object(r.shared, "owned_phase", return_value=execution), mock.patch.object(r.shared, "require_phase_success", side_effect=primary), mock.patch.object(r.shared, "read_private_log", side_effect=read_error, return_value=body), mock.patch.object(d, "classify", side_effect=classify_error, wraps=d.classify):
                receipt = {"phases": {}}
                with self.assertRaises(r.Refusal) as caught:
                    r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(), receipt)
                self.assertIs(primary, caught.exception)
                self.assertEqual(code, receipt["prepare_failure_diagnostic"]["unavailable_code"])
                self.assert_public(receipt["prepare_failure_diagnostic"])
        for malformed in ({"PRIVATE": PRIVATE_SENTINEL * 4096}, {**d.unavailable("classifier_error"), "diagnostic_code": PRIVATE_SENTINEL}):
            primary = r.Refusal("exact-owned-phase-exit-capture-or-group-refusal")
            with mock.patch.object(r.shared, "owned_phase", return_value=execution), mock.patch.object(r.shared, "require_phase_success", side_effect=primary), mock.patch.object(r.shared, "read_private_log", return_value=body), mock.patch.object(d, "classify", return_value=malformed):
                receipt = {"phases": {}}
                with self.assertRaises(r.Refusal) as caught:
                    r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(), receipt)
                self.assertIs(primary, caught.exception)
                self.assertEqual("classifier_error", receipt["prepare_failure_diagnostic"]["unavailable_code"])
                self.assert_public(receipt["prepare_failure_diagnostic"])
        clock, primary = [0], r.Refusal("exact-owned-phase-exit-capture-or-group-refusal")
        def exhaust_read(*args):
            clock[0] = 601
            return body
        with mock.patch.object(r.shared, "owned_phase", return_value=execution), mock.patch.object(r.shared, "require_phase_success", side_effect=primary), mock.patch.object(r.shared, "read_private_log", side_effect=exhaust_read), mock.patch.object(d, "classify") as classify:
            receipt = {"phases": {}}
            with self.assertRaises(r.Refusal) as caught:
                r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(lambda: clock[0]), receipt)
            self.assertIs(primary, caught.exception)
            classify.assert_not_called()
            self.assertEqual("remaining_budget_refused", receipt["prepare_failure_diagnostic"]["unavailable_code"])
        class RefusingDiagnostic(dict):
            def __setitem__(self, key, value):
                if key == "prepare_failure_diagnostic":
                    raise OSError(PRIVATE_SENTINEL)
                super().__setitem__(key, value)
        with mock.patch.object(r.shared, "owned_phase", return_value=execution), mock.patch.object(r.shared, "require_phase_success", side_effect=primary), mock.patch.object(r.shared, "read_private_log", return_value=body):
            with self.assertRaises(r.Refusal) as caught:
                r.phase(ROOT, private, "prepare", [PRIVATE_SENTINEL], budget(), RefusingDiagnostic(phases={}))
            self.assertIs(primary, caught.exception)
        # Actual descriptor close still runs; then its synthetic refusal remains
        # secondary to the already established nonzero preparation exit.
        original_close = r.OwnedJavaDirectories.close
        def close_then_refuse(owner):
            original_close(owner)
            raise r.Refusal("owned-jvm-descriptor-cleanup-unestablished")
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root, revision = Path(directory).resolve(), "a" * 40
            source = {"synthetic-source": "c" * 64}
            for context in (mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(r.library, "ROOT", root),
                            mock.patch.object(p, "source_snapshot", return_value=source), mock.patch.object(r.library, "git_revision", return_value=revision),
                            mock.patch.object(r.library.runtime_context, "capture", return_value=runtime(revision)),
                            mock.patch.object(r, "qualify_jdk", return_value=(Path("/synthetic-jdk"), {"synthetic": "jdk"})),
                            mock.patch.object(r, "default_version", return_value="0.1.0-SNAPSHOT"), mock.patch.object(r.shared, "NativeBudget", return_value=budget()),
                            mock.patch.object(r.shared, "owned_phase", return_value=execution), mock.patch.object(r.shared, "read_private_log", return_value=body),
                            mock.patch.object(r.OwnedJavaDirectories, "close", close_then_refuse),
                            mock.patch.object(r, "native_identity", side_effect=AssertionError("must not reach native resources after failed preparation"))):
                stack.enter_context(context)
            with redirect_stdout(io.StringIO()):
                result = p.run(Path("build/ci-verification/synthetic"))
            output = root / "build/ci-verification/synthetic"
            receipt = json.loads((output / "receipt.json").read_text())
            self.assertEqual(1, result)
            self.assertEqual("exact-owned-phase-exit-capture-or-group-refusal", receipt["reason_code"])
            self.assertEqual("Refusal", receipt["failure_owned_java_descriptor_cleanup_error_type"])
            self.assertIs(False, receipt["passed"])
            self.assertIs(False, receipt["preparation_passed"])
            self.assertEqual({"prepare"}, set(receipt["phases"]))
            self.assertFalse((output / "runtime-after.json").exists())
            self.assertIs(False, receipt["test_counts_complete"])
            self.assert_public(receipt["prepare_failure_diagnostic"])

    def test_manual_preparation_only_job_never_invokes_native_or_accepted_controls_and_keeps_five_JSON(self):
        self.assertIn("scripts/ci/picker_awt_prepare_failure.py", r.OWNING_INPUTS)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            owning_workflow = root / p.WORKFLOW
            owning_workflow.parent.mkdir(parents=True)
            payload = b"on:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
            owning_workflow.write_bytes(payload)
            with mock.patch.object(r, "source_snapshot", return_value={}):
                with self.assertRaisesRegex(r.Refusal, "^preparation-only-owning-source-input-missing$"):
                    p.source_snapshot(root)
            owning = {name: "a" * 64 for name in p.OWNING_INPUTS}
            owning[p.WORKFLOW] = hashlib.sha256(payload).hexdigest()
            with mock.patch.object(r, "source_snapshot", return_value=dict(owning)):
                self.assertEqual(owning, p.source_snapshot(root))
        workflow = (r.library.ROOT / p.WORKFLOW).read_text()
        original_workflow = (r.library.ROOT / r.shared.WORKFLOW).read_bytes()
        self.assertEqual("26edb07e55079f72f8637b3d69f56ab4b202df2baa143b1d8a133c3cc187a838", hashlib.sha256(original_workflow).hexdigest())
        self.assertEqual("92bd04abe994c31d8fc5854e91f5af3bdb68912e203224281d360dd6b6c29a97",
                         hashlib.sha256((r.library.ROOT / r.TEST_SOURCE).read_bytes()).hexdigest())
        for required in ("on:\n  workflow_dispatch:\n", "permissions:\n  contents: read", "github.repository == 'Apdelrahman1911/nativeCmpkit'",
                         "github.event_name == 'workflow_dispatch'", "runs-on: macos-26", "timeout-minutes: 15", "persist-credentials: false",
                         "toolchain: '1.98.0'", "distribution: temurin", "java-version: '17'", "verify-signature: true", "overwrite-settings: false",
                         "python3 -B scripts/ci/picker_awt_preparation.py --output build/ci-verification/picker-awt-preparation", "if: always()"):
            self.assertIn(required, workflow)
        uploads = workflow.split("          path: |\n", 1)[1].splitlines()
        self.assertEqual(["            build/ci-verification/picker-awt-preparation/" + name for name in r.PUBLIC_FILES], uploads)
        for forbidden in ("unittest", "test_picker_", "push:", "pull_request:", "schedule:", "matrix:", "*.json", "*.log", "**",
                          "private/", ".dylib", "target/", "printenv", "set -x", "write-all", "actions: write", "packages: write"):
            self.assertNotIn(forbidden, workflow)
        source = (r.library.ROOT / "scripts/ci/picker_awt_preparation.py").read_text()
        self.assertEqual(1, source.count("budget = r.shared.NativeBudget()"))
        self.assertEqual(1, source.count("r.phase("))
        self.assertIn('r.phase(root, private, stage, [*r.prepare_command(root, private), "--stacktrace"], budget, receipt)', source)
        self.assertEqual(1, source.count('"--stacktrace"'))
        for forbidden in ("r.exact_command(", "r.review_inventory(", "r.review_junit(", "subprocess", "--rerun-tasks", "r.run("):
            self.assertNotIn(forbidden, source)
        calls = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)]
        self.assertFalse(any(isinstance(node.func, ast.Attribute) and node.func.attr in {"execute", "Popen"} for node in calls))
        for mode in ("positive", "changed-native", "deadline"):
            with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root, revision, clock = Path(directory).resolve(), "a" * 40, [0]
                source_map = {"synthetic-source": "c" * 64}
                native = {"files": {name: {"sha256": "d" * 64, "size": 1} for name in (r.NATIVE_RESOURCE, r.MANIFEST_RESOURCE)}}
                cp = {"resources": {name: [{"entry_index": 0, "sha256": "d" * 64, "size": 1}] for name in r.REQUIRED_RESOURCES}}
                native_after = copy.deepcopy(native)
                if mode == "changed-native": native_after["files"][r.NATIVE_RESOURCE]["sha256"] = "e" * 64
                phases = []
                selected_budget = budget(lambda: clock[0])
                def synthetic_phase(actual_root, private, stage, command, actual_budget, receipt):
                    self.assertEqual(root, actual_root)
                    self.assertIs(selected_budget, actual_budget)
                    self.assertEqual("prepare", stage)
                    self.assertEqual([*r.prepare_command(root, private), "--stacktrace"], command)
                    phases.append(stage)
                    receipt["phases"][stage] = {key: value for key, value in failed_phase(preparation()).items()
                                                if key not in {"command", "private_capture_fd_stat9"}}
                    receipt["phases"][stage]["exit_code"] = 0
                    if mode == "deadline": clock[0] = 601
                    return preparation()
                for context in (mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(r.library, "ROOT", root),
                                mock.patch.object(p, "source_snapshot", return_value=source_map), mock.patch.object(r.library, "git_revision", return_value=revision),
                                mock.patch.object(r.library.runtime_context, "capture", return_value=runtime(revision)),
                                mock.patch.object(r, "qualify_jdk", return_value=(Path("/synthetic-jdk"), {"synthetic": "jdk"})),
                                mock.patch.object(r, "default_version", return_value="0.1.0-SNAPSHOT"),
                                mock.patch.object(r, "native_identity", side_effect=[native, native_after]),
                                mock.patch.object(r, "classpath_identity", return_value=("synthetic-cp", cp)),
                                mock.patch.object(r, "phase", side_effect=synthetic_phase),
                                mock.patch.object(r.shared, "NativeBudget", return_value=selected_budget)):
                    stack.enter_context(context)
                with redirect_stdout(io.StringIO()): result = p.run(Path("build/ci-verification/synthetic"))
                output = root / "build/ci-verification/synthetic"
                receipt = json.loads((output / "receipt.json").read_text())
                self.assertEqual(["prepare"], phases)
                self.assertEqual(mode == "positive", receipt["passed"])
                self.assertEqual(mode == "positive", receipt["preparation_passed"])
                self.assertEqual(0 if mode == "positive" else 1, result)
                self.assertEqual(0, receipt["native_processes_requested"])
                self.assertEqual(0, receipt["inventory_processes_requested"])
                self.assertEqual(0, receipt["native_JUnit_requested"])
                self.assertIs(False, receipt["test_counts_complete"])
                self.assertIs(False, receipt["native_reuse_certificate"])
                self.assertTrue(receipt["owned_java_descriptors_closed"])
                self.assertLessEqual({path.name for path in output.glob("*.json")}, set(r.PUBLIC_FILES))
                if mode == "positive":
                    self.assertTrue(receipt["held_owned_java_directories"])
                    self.assertEqual(set(r.PUBLIC_FILES), {path.name for path in output.glob("*.json")})
                elif mode == "changed-native":
                    self.assertFalse(receipt["held_native_bundle"])
                else:
                    self.assertEqual("shared-native-deadline-exhausted-or-clock-invalid", receipt["reason_code"])


    def test_standalone_owning_workflow_missing_from_shared_route_is_hashed_and_held_without_relaxing_required_inputs(self):
        # Real routed shape: scripts/ci are generic inputs; only the existing
        # registered workflow is added by shared.source_snapshot. The original
        # preparation guard fails this first capture because its standalone
        # workflow was never entered in that map.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workflow = root / p.WORKFLOW
            workflow.parent.mkdir(parents=True)
            payload = b"on:\n  workflow_dispatch:\npermissions:\n  contents: read\n"
            workflow.write_bytes(payload)
            # Capture the real generic scripts/ci file map, not a map
            # prefilled with every OWNING_INPUTS member. Only unrelated module
            # discovery/provenance is mocked; these three script files are data
            # and never imported or executed from the temporary tree.
            script_names = ("scripts/ci/picker_awt_preparation.py",
                            "scripts/ci/picker_awt_prepare_failure.py",
                            "scripts/ci/test_picker_awt_prepare_failure_diagnostics.py")
            for index, name in enumerate(script_names):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(("# synthetic source data " + str(index) + "\n").encode())
            registered_workflow = root / r.shared.WORKFLOW
            registered_workflow.write_bytes(payload + b"# original registered route\n")
            with mock.patch.object(r.library, "projects", return_value=()), \
                    mock.patch.object(r.library.secure_alert, "held_provenance_sources", return_value=()):
                generic = r.library.snapshot_inputs(root)
            self.assertEqual(set(script_names), set(generic))
            self.assertNotIn(p.WORKFLOW, generic)
            self.assertNotIn(r.shared.WORKFLOW, generic)
            # The existing shared route adds only its registered workflow.
            routed = {**generic, r.shared.WORKFLOW: hashlib.sha256(registered_workflow.read_bytes()).hexdigest()}
            self.assertNotIn(p.WORKFLOW, routed)
            with mock.patch.object(r, "source_snapshot", side_effect=lambda unused: dict(routed)):
                before = p.source_snapshot(root)
                self.assertEqual({**routed, p.WORKFLOW: hashlib.sha256(payload).hexdigest()}, before)
                self.assertEqual(routed, {name: value for name, value in before.items() if name != p.WORKFLOW})
                changed = payload + b"# changed owned routing input\n"
                workflow.write_bytes(changed)
                after = p.source_snapshot(root)
                self.assertNotEqual(before[p.WORKFLOW], after[p.WORKFLOW])
                self.assertEqual(hashlib.sha256(changed).hexdigest(), after[p.WORKFLOW])
                self.assertEqual(routed, {name: value for name, value in after.items() if name != p.WORKFLOW})
                original_hash = r.library.sha256
                def change_during_hash(path):
                    self.assertEqual(workflow, path)
                    value = original_hash(path)
                    path.write_bytes(changed + b"# changed during capture\n")
                    return value
                with mock.patch.object(r.library, "sha256", side_effect=change_during_hash):
                    with self.assertRaisesRegex(r.Refusal, "^preparation-only-workflow-changed-during-source-capture$"):
                        p.source_snapshot(root)
                workflow.unlink()
                workflow.mkdir()
                with self.assertRaisesRegex(r.Refusal, "^preparation-only-workflow-is-not-one-owned-regular-input$"):
                    p.source_snapshot(root)
                workflow.rmdir()
                workflow.write_bytes(payload)
                alias = root / "owned-workflow-hardlink"
                os.link(workflow, alias)
                try:
                    with self.assertRaisesRegex(r.Refusal, "^preparation-only-workflow-is-not-one-owned-regular-input$"):
                        p.source_snapshot(root)
                finally:
                    alias.unlink()
            missing_script = dict(routed)
            del missing_script["scripts/ci/picker_awt_preparation.py"]
            with mock.patch.object(r, "source_snapshot", return_value=missing_script):
                with self.assertRaisesRegex(r.Refusal, "^preparation-only-owning-source-input-missing$"):
                    p.source_snapshot(root)


    def test_private_gradle_stacktrace_exports_only_fixed_exception_family_and_preserves_primary_ambiguity_caps_and_secrets(self):
        # Message operands are intentionally private; ONLY constant observation
        # enums may appear in the existing public diagnostic_code field.
        private = PRIVATE_SENTINEL + " https://invalid.example/private Authorization=PRIVATE"
        header = ("FAILURE: Build failed with an exception.\n\n* What went wrong:\n"
                  "A problem occurred configuring project '" + private + "'.\n\n* Exception is:\n"
                  "org.gradle.api.ProjectConfigurationException: " + private + "\n")
        footer = "\nBUILD FAILED in 2s\n"
        cases = (("java.lang.NoSuchMethodError", "gradle_api_linkage_observed"),
                 ("javax.net.ssl.SSLHandshakeException", "gradle_tls_observed"),
                 ("org.gradle.kotlin.dsl.support.ScriptCompilationException", "gradle_script_compilation_observed"),
                 ("org.gradle.internal.resolve.ModuleVersionResolveException", "gradle_dependency_resolution_observed"))
        expected_keys = {"schema_version", "status", "category", "diagnostic_code", "failed_task_id", "location",
                         "ambiguity", "cause_established", "required_task_states", "unavailable_code"}
        for klass, code in cases:
            with self.subTest(exception_family=code):
                body = header + "Caused by: " + klass + ": " + private + footer
                value = d.classify(ROOT, body)
                self.assertEqual(("unclassified", "unknown", code), (value["status"], value["category"], value["diagnostic_code"]))
                self.assertEqual(expected_keys, set(value))
                self.assertEqual(1, value["schema_version"])
                self.assertFalse(value["ambiguity"])
                self.assertIs(value["cause_established"], False)
                self.assertIsNone(value["failed_task_id"])
                self.assertIsNone(value["location"])
                self.assertEqual({key: "unobserved" for key in d.REQUIRED_TASK_IDS}, value["required_task_states"])
                self.assert_public(value)
                encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
                self.assertNotIn(klass, encoded)
                self.assertNotIn(private, encoded)
                self.assertLessEqual(len(encoded.encode("ascii")), 4096)
        specific = header + "Caused by: org.gradle.internal.resolve.ModuleVersionResolveException: " + private + "\n"
        specific += "Caused by: javax.net.ssl.SSLHandshakeException: " + private + footer
        self.assertEqual("gradle_tls_observed", d.classify(ROOT, specific)["diagnostic_code"])
        repeated = header + ("Caused by: java.lang.NoSuchMethodError: " + private + "\n") * 2 + footer
        self.assertEqual("gradle_api_linkage_observed", d.classify(ROOT, repeated)["diagnostic_code"])
        conflicting = header + "Caused by: java.lang.NoSuchMethodError: " + private + "\n"
        conflicting += "Caused by: javax.net.ssl.SSLHandshakeException: " + private + footer
        value = d.classify(ROOT, conflicting)
        self.assertEqual(("unclassified", "unknown", True), (value["status"], value["diagnostic_code"], value["ambiguity"]))
        self.assert_public(value)
        # A real wrapper-download stack can fail before any Gradle banner/task;
        # fixed Download/Install frames qualify only the observed wrapper type.
        wrapper = 'Exception in thread "main" java.io.FileNotFoundException: ' + private + "\n"
        wrapper += "\tat org.gradle.wrapper.Download.downloadInternal(Download.java:97)\n"
        wrapper += "\tat org.gradle.wrapper.Install.forceFetch(Install.java:167)\n"
        value = d.classify(ROOT, wrapper)
        self.assertEqual(("unclassified", "gradle_wrapper_download_missing_observed"), (value["status"], value["diagnostic_code"]))
        self.assert_public(value)
        # A frame preceding the main exception is outside its selected trace.
        # Partial/duplicate Gradle frames and task banners are not bootstrap.
        preceding = "\tat org.gradle.wrapper.Download.downloadInternal(Download.java:97)\n"
        preceding += 'Exception in thread "main" java.io.FileNotFoundException: ' + private + "\n"
        mixed = (preceding,
                 "FAILURE: Build failed with an exception.\n" + wrapper,
                 "* What went wrong:\n" + wrapper,
                 "* Exception is:\n" + wrapper,
                 "BUILD FAILED\n" + wrapper,
                 "BUILD FAILED in 2s\n" + wrapper,
                 "FAILURE: Build failed with an exception.\n" * 2 + wrapper,
                 "> Task :unrelated:bootstrap\n" + wrapper,
                 wrapper + "> Task :unrelated:bootstrap\n")
        for body in mixed:
            with self.subTest(refused_bootstrap_context=body[:32]):
                value = d.classify(ROOT, body)
                self.assertEqual(("unclassified", "unknown"), (value["status"], value["category"]))
                self.assertIn(value["diagnostic_code"], d.CONTEXT_CODES)
                self.assertNotIn(value["diagnostic_code"], d.TRACE_CODES)
                self.assertIs(value["cause_established"], False)
                self.assert_public(value)
        for body, code in ((header + "Caused by: private.UnknownException: " + private + footer,
                            "gradle_project_configuration_observed"),
                           (header.replace("* Exception is:", "* Unknown:") + "Caused by: java.lang.NoSuchMethodError: " + private + footer,
                            "gradle_failure_frame_partial_observed"),
                           ('Exception in thread "main" java.io.FileNotFoundException: ' + private,
                            "gradle_wrapper_context_refused_observed"),
                           (header + "Caused by: java.lang.NoSuchMethodError: " + private,
                            "gradle_failure_frame_partial_observed"),
                           (header + "Caused by: java.lang.NoSuchMethodError: " + private + footer + footer,
                            "gradle_failure_frame_multiple_observed")):
            self.assertEqual(code, d.classify(ROOT, body)["diagnostic_code"])
            self.assert_public(d.classify(ROOT, body))
        # Never replace original supported source classification or its refusal
        # of conflicting supported compiler locations/candidates.
        known = compiler_body() + header + "Caused by: java.lang.NoSuchMethodError: " + private + footer
        self.assertEqual(("classified", "kotlin_unresolved_reference"),
                         (d.classify(ROOT, known)["status"], d.classify(ROOT, known)["diagnostic_code"]))
        prior_ambiguity = compiler_body() + compiler_body() + header + "Caused by: java.lang.NoSuchMethodError: " + private + footer
        value = d.classify(ROOT, prior_ambiguity)
        self.assertEqual("unclassified", value["status"])
        self.assertTrue(value["ambiguity"])
        self.assertIsNone(value["location"])
        self.assert_public(value)
        for body in (header + ("x" * 65537), header + "\x1b[31m" + footer):
            value = d.classify(ROOT, body)
            self.assertEqual(("unavailable", "diagnostic_limit"), (value["status"], value["unavailable_code"]))
            self.assert_public(value)


    def test_safe_trace_context_presence_and_configuration_family_observations_do_not_establish_prepare_cause(self):
        # All bodies below are SYNTHETIC controls, never reconstructions of the
        # unavailable 01b4 capture. Class/context enums observe strings only.
        private = PRIVATE_SENTINEL + " https://invalid.example/private Authorization=PRIVATE"
        header = ("FAILURE: Build failed with an exception.\n\n* What went wrong:\n"
                  "Unrecognized synthetic failure " + private + "\n\n* Exception is:\n")
        footer = "\nBUILD FAILED in 2s\n"
        trace = header + "private.UnknownException: " + private + footer
        wrapper = 'Exception in thread "main" private.UnknownException: ' + private + "\n"
        wrapper += "\tat org.gradle.wrapper.Download.downloadInternal(Download.java:97)\n"
        cases = ((private, "gradle_failure_frame_absent_observed"),
                 ("> Task :unrelated:bootstrap\n" + private, "gradle_task_banners_without_trace_observed"),
                 (header + private, "gradle_failure_frame_partial_observed"),
                 (trace + footer, "gradle_failure_frame_multiple_observed"),
                 (header.replace("* What went wrong:\n", "").replace("* Exception is:\n", "* Exception is:\n* What went wrong:\n") + footer,
                  "gradle_failure_frame_order_refused_observed"),
                 (trace, "gradle_build_trace_without_allowed_family_observed"),
                 (wrapper, "gradle_wrapper_trace_without_allowed_family_observed"),
                 (wrapper + "> Task :unrelated:bootstrap\n", "gradle_wrapper_context_refused_observed"))
        for body, code in cases:
            with self.subTest(context=code):
                value = d.classify(ROOT, body)
                self.assertEqual(("unclassified", "unknown", code), (value["status"], value["category"], value["diagnostic_code"]))
                self.assertIn(code, d.CONTEXT_CODES)
                self.assertIsNone(value["location"])
                self.assertIsNone(value["failed_task_id"])
                self.assertFalse(value["ambiguity"])
                self.assertEqual("none", value["unavailable_code"])
                self.assert_public(value)
        families = (("org.gradle.api.ProjectConfigurationException", "gradle_project_configuration_observed"),
                    ("com.android.builder.errors.EvalIssueException", "gradle_android_configuration_observed"),
                    ("org.gradle.api.internal.artifacts.verification.exceptions.DependencyVerificationException", "gradle_dependency_verification_observed"),
                    ("org.gradle.launcher.daemon.client.DaemonDisappearedException", "gradle_daemon_disappearance_observed"))
        for klass, code in families:
            with self.subTest(exception_family=code):
                # Direct exception and caused-by syntax both require the same
                # complete frame; class names/messages never leave the body.
                for prefix in ("", "Caused by: "):
                    value = d.classify(ROOT, header + prefix + klass + ": " + private + footer)
                    self.assertEqual(("unclassified", "unknown", code), (value["status"], value["category"], value["diagnostic_code"]))
                    self.assertIn(code, d.TRACE_CODES)
                    self.assertNotIn(klass, json.dumps(value))
                    self.assert_public(value)
        # Broad ProjectConfigurationException stays below EVERY original tier.
        broad = header + "org.gradle.api.ProjectConfigurationException: " + private + "\n"
        for klass, code in (("javax.net.ssl.SSLHandshakeException", "gradle_tls_observed"),
                            ("org.gradle.kotlin.dsl.support.ScriptCompilationException", "gradle_script_compilation_observed"),
                            ("org.gradle.internal.resolve.ModuleVersionResolveException", "gradle_dependency_resolution_observed")):
            value = d.classify(ROOT, broad + "Caused by: " + klass + ": " + private + footer)
            self.assertEqual(code, value["diagnostic_code"])
            self.assertFalse(value["ambiguity"])
            self.assert_public(value)
        # Exact allowlist: message/class lookalikes and rejected mixed contexts
        # do not promote a family or establish a cause.
        value = d.classify(ROOT, header + "private.UnknownException: org.gradle.api.ProjectConfigurationException " + private + footer)
        self.assertEqual("gradle_build_trace_without_allowed_family_observed", value["diagnostic_code"])
        self.assert_public(value)
        for klass, _ in families:
            value = d.classify(ROOT, "* Exception is:\n" + klass + ": " + private)
            self.assertEqual("gradle_failure_frame_partial_observed", value["diagnostic_code"])
            self.assertNotIn(value["diagnostic_code"], d.TRACE_CODES)
            self.assert_public(value)
        # An unsupported original source line remains unclassified/unselected;
        # a secondary complete-frame observation does not repair that refusal.
        refused = compiler_body().replace(ROOT.as_posix(), "/foreign/" + PRIVATE_SENTINEL)
        value = d.classify(ROOT, refused + trace)
        self.assertEqual(("unclassified", "gradle_build_trace_without_allowed_family_observed"), (value["status"], value["diagnostic_code"]))
        self.assertIsNone(value["location"])
        self.assertIsNone(value["failed_task_id"])
        self.assert_public(value)
        ambiguous = compiler_body() + compiler_body() + trace
        value = d.classify(ROOT, ambiguous)
        self.assertTrue(value["ambiguity"])
        self.assertEqual("unclassified", value["status"])
        self.assert_public(value)
        # Synthetic boundary sizes exercise diagnostics only, not missing logs.
        # Every padding line stays within the unchanged 4096-byte line cap.
        for size in (53748, 65536):
            needed = size - len((header + footer).encode("utf-8"))
            chunks, remainder = divmod(needed, 4001)
            padded = header + ("x" * 4000 + "\n") * chunks + "x" * remainder + footer
            self.assertEqual(size, len(padded.encode("utf-8")))
            value = d.classify(ROOT, padded)
            self.assertEqual(("unclassified", "gradle_build_trace_without_allowed_family_observed", "none"),
                             (value["status"], value["diagnostic_code"], value["unavailable_code"]))
            self.assert_public(value)
        for body in ("x" * 65537, "x" * 4097, "\x1b[31m" + trace):
            value = d.classify(ROOT, body)
            self.assertEqual(("unavailable", "diagnostic_limit"), (value["status"], value["unavailable_code"]))
            self.assert_public(value)


    def test_one_complete_private_gradle_what_block_exports_only_fixed_heading_categories_and_preserves_existing_trace_and_primary_guards(self):
        # SYNTHETIC only; no reconstruction or retrospective classification of
        # original00cf. Every operand remains private and every enum is fixed.
        private = PRIVATE_SENTINEL + " https://invalid.example/private Authorization=PRIVATE"
        start = "FAILURE: Build failed with an exception.\n\n* What went wrong:\n"
        tail = "\n* Exception is:\nprivate.UnknownException: " + private + "\n\nBUILD FAILED in 2s\n"
        cases = (
            ("SDK location not found. Define a valid SDK location " + private, "gradle_android_sdk_location_heading_observed"),
            ("Failed to install the following Android SDK packages as some licences have not been accepted.", "gradle_android_licenses_heading_observed"),
            ("Android Gradle plugin requires Java 21 to run. You are currently using Java 17.", "gradle_android_jdk_requirement_heading_observed"),
            ("Minimum supported Gradle version is 9.0. Current version is 8.9. " + private, "gradle_version_requirement_heading_observed"),
            ("Dependency verification failed for configuration '" + private + "':", "gradle_dependency_verification_heading_observed"),
            ("Gradle build daemon disappeared unexpectedly (it may have been killed or may have crashed)", "gradle_daemon_disappearance_heading_observed"),
            ("Cannot find a Java installation on your machine matching: " + private, "gradle_java_toolchain_heading_observed"),
            ("Could not GET '" + private + "'. Received status code 403 from server: " + private, "gradle_repository_auth_heading_observed"),
            ("Could not HEAD '" + private + "'. Received status code 429 from server: " + private, "gradle_repository_rate_limit_heading_observed"),
            ("An exception occurred applying plugin request [id: '" + private + "']", "gradle_plugin_application_heading_observed"),
            ("Plugin [id: '" + private + "'] was not found in any of the following sources:", "gradle_plugin_resolution_heading_observed"),
            ("Could not resolve all task dependencies for configuration '" + private + "'.", "gradle_dependency_resolution_heading_observed"),
            ("Script compilation errors:", "gradle_script_compilation_heading_observed"),
            ("A problem occurred configuring project '" + private + "'.", "gradle_configuration_heading_observed"),
            ("Could not determine the dependencies of task ':foreign:" + PRIVATE_SENTINEL + "'.", "gradle_task_setup_heading_observed"),
            ("Execution failed for task ':foreign:" + PRIVATE_SENTINEL + "'.", "gradle_task_failure_heading_observed"),
        )
        for heading, code in cases:
            with self.subTest(heading_category=code):
                # Only one official cause prefix is admitted, not arbitrary
                # substring/private-message matching or exception printing.
                body = start + "  > " + heading + tail
                value = d.classify(ROOT, body)
                self.assertEqual(("unclassified", "unknown", code), (value["status"], value["category"], value["diagnostic_code"]))
                self.assertIn(code, d.HEADING_CODES)
                self.assertNotIn(code, d.TRACE_CODES)
                self.assertIsNone(value["location"])
                self.assertIsNone(value["failed_task_id"])
                self.assertEqual("none", value["unavailable_code"])
                self.assertFalse(value["ambiguity"])
                self.assert_public(value)
                self.assertNotIn(heading, json.dumps(value))
        sdk = cases[0][0]
        broad = "A problem occurred configuring project '" + private + "'.\n"
        value = d.classify(ROOT, start + broad + "  > " + sdk + tail)
        self.assertEqual("gradle_android_sdk_location_heading_observed", value["diagnostic_code"])
        self.assert_public(value)
        repeated = start + ("  > " + sdk + "\n") * 2 + tail
        self.assertEqual("gradle_android_sdk_location_heading_observed", d.classify(ROOT, repeated)["diagnostic_code"])
        conflicting = start + "  > " + sdk + "\n  > " + cases[4][0] + tail
        value = d.classify(ROOT, conflicting)
        self.assertEqual(("unclassified", "unknown", True), (value["status"], value["diagnostic_code"], value["ambiguity"]))
        self.assert_public(value)
        # A heading outside What, in Try/help, in the exception MESSAGE, in an
        # unqualified partial/multiple/wrapper frame or as a substring cannot
        # activate this last-resort classifier.
        negatives = (sdk + "\n" + start + private + tail,
                     start + private + "\n* Try:\n> " + sdk + tail,
                     start + private + "\n* Get more help at https://invalid.example\n> " + sdk + tail,
                     start + private + tail.replace("private.UnknownException: " + private, "private.UnknownException: " + sdk),
                     start + "Quoted private text: " + sdk + tail,
                     start + "> > " + sdk + tail,
                     start + sdk,
                     start + sdk + tail + tail,
                     'Exception in thread "main" private.UnknownException: ' + sdk + "\n\tat org.gradle.wrapper.Download.downloadInternal(Download.java:97)\n")
        for body in negatives:
            value = d.classify(ROOT, body)
            self.assertEqual(("unclassified", "unknown"), (value["status"], value["category"]))
            self.assertNotIn(value["diagnostic_code"], d.HEADING_CODES)
            self.assert_public(value)
        # Original allowlisted trace families and their ambiguity win; do not
        # replace them with a plausible but independently printed heading.
        known_trace = (start + sdk + tail.replace("private.UnknownException: " + private,
                      "java.lang.NoSuchMethodError: " + private))
        self.assertEqual("gradle_api_linkage_observed", d.classify(ROOT, known_trace)["diagnostic_code"])
        conflicting_trace = known_trace.replace("\n\nBUILD FAILED", "\nCaused by: javax.net.ssl.SSLHandshakeException: " + private + "\n\nBUILD FAILED")
        value = d.classify(ROOT, conflicting_trace)
        self.assertEqual(("unknown", True), (value["diagnostic_code"], value["ambiguity"]))
        self.assert_public(value)
        known_primary = compiler_body() + start + sdk + tail
        self.assertEqual(("classified", "kotlin_unresolved_reference"),
                         (d.classify(ROOT, known_primary)["status"], d.classify(ROOT, known_primary)["diagnostic_code"]))
        refused_primary = compiler_body().replace(ROOT.as_posix(), "/foreign/" + PRIVATE_SENTINEL) + start + sdk + tail
        value = d.classify(ROOT, refused_primary)
        self.assertEqual(("unclassified", "gradle_android_sdk_location_heading_observed"), (value["status"], value["diagnostic_code"]))
        self.assertIsNone(value["location"])
        self.assertIsNone(value["failed_task_id"])
        self.assert_public(value)
        prior_ambiguity = compiler_body() + compiler_body() + start + sdk + tail
        value = d.classify(ROOT, prior_ambiguity)
        self.assertEqual("unclassified", value["status"])
        self.assertTrue(value["ambiguity"])
        self.assert_public(value)
        for body in ("x" * 65537, start + "x" * 4097 + tail, "\x1b[31m" + start + sdk + tail):
            value = d.classify(ROOT, body)
            self.assertEqual(("unavailable", "diagnostic_limit"), (value["status"], value["unavailable_code"]))
            self.assert_public(value)


if __name__ == "__main__":
    unittest.main()
