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
        with mock.patch.object(r, "source_snapshot", return_value={}):
            with self.assertRaisesRegex(r.Refusal, "^preparation-only-owning-source-input-missing$"):
                p.source_snapshot(ROOT)
        owning = {name: "a" * 64 for name in p.OWNING_INPUTS}
        with mock.patch.object(r, "source_snapshot", return_value=owning):
            self.assertEqual(owning, p.source_snapshot(ROOT))
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
        self.assertIn('r.phase(root, private, stage, r.prepare_command(root, private), budget, receipt)', source)
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
                    self.assertEqual(r.prepare_command(root, private), command)
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


if __name__ == "__main__":
    unittest.main()
