# SPDX-License-Identifier: Apache-2.0
"""Important NEW source/transport controls; ZERO Apple/native library tests.

The subprocess is an owned Python fixture, not a UIKit app or synthetic JUnit.
Finished test frames, lifecycle observations and console0 never replace the
original Worker completion, fresh native XML, runtime or owning cleanup gates.
"""
import ast
import copy
import hashlib
import io
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import ios_ui_application as application
import ios_modal_worker_source_projection as worker
import ios_worker_completion_source_projection as history
import library_tests as library
import workflow_matrix as workflow
from test_ios_ui_application import ACTIVE, COMPLETE, frame

ROOT = Path(__file__).resolve().parents[2]
HOST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
COMPILER = "scripts/ci/ios_modal_completion_compile.init.gradle.kts"
DEVICE = "11111111-2222-3333-4444-555555555555"
FIXTURE = "scripts/ci/test_android_external337_fixture_recovery.py"


def finished_frames(failed=False):
    lines = [ACTIVE]
    for group in library.UI_APPLICATION_FOCUS_SPECS[library.IOS_MODAL_WORKER_MEMORY_FOCUS]["groups"]:
        lines.append(frame("testSuiteStarted", name=group["classname"]))
        for number, method in enumerate(group["methods"]):
            lines.append(frame("testStarted", name=method))
            if failed and number == 0:
                lines.append(frame("testFailed", name=method, message="fixed synthetic failure"))
            lines.append(frame("testFinished", name=method, duration="1"))
        lines.append(frame("testSuiteFinished", name=group["classname"]))
    return lines


def observations(exit_code=0):
    return ["NATIVECMPKIT_WORKER_LIFECYCLE phase=" + phase + " runnerExit=" + str(exit_code) +
            " mainThread=" + str(main_thread).lower()
            for phase, main_thread in application.WORKER_LIFECYCLE_STEPS]


def protocol(lines):
    result = application.NativeProtocol()
    for line in lines:
        result.feed(line)
    return result


class WorkerCompletionControls(unittest.TestCase):
    def test_source_observes_future_return_consumption_and_original_cleanup_without_changing_cases(self):
        source = (ROOT / HOST).read_text()
        previous = history.current_source_before_worker_completion(HOST, source.encode()).decode()
        phases = re.findall(r'NATIVECMPKIT_WORKER_LIFECYCLE phase=([a-z-]+)', source)
        self.assertEqual([phase for phase, _ in application.WORKER_LIFECYCLE_STEPS], phases)
        for name in ("onApplicationMain", "releaseMainLeases"):
            start = "internal fun <T> " if name == "onApplicationMain" else "    private fun "
            body = source.split(start + name, 1)[1].split("\n    }" if name == "releaseMainLeases" else "\n}", 1)[0]
            old = previous.split(start + name, 1)[1].split("\n    }" if name == "releaseMainLeases" else "\n}", 1)[0]
            self.assertEqual(old, body)
        for before, after in (("val exit = testLauncherEntryPoint(it)", "phase=runner-returned"),
                              ("pending.result", "phase=runner-result-consumed"),
                              ("requestTermination()", "phase=termination-requested"),
                              ("try { stopping.result }", "phase=termination-result-consumed")):
            self.assertLess(source.index(before), source.index(after))
        tail = source.split("phase=main-leases-releasing", 1)[1]
        self.assertLess(tail.index("releaseMainLeases()"), tail.index("phase=main-leases-released"))
        self.assertLess(tail.index("phase=main-leases-released"), tail.index("NATIVECMPKIT_UIKIT_COMPLETED"))
        for marker in ("NSTimer.scheduledTimerWithTimeInterval(0.05, repeats = true)",
                       "systemUptime - startedAt > 1800.0", "exitProcess(runnerExit)",
                       "NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false"):
            self.assertIn(marker, source)
        for relative in (library.IOS_MODAL_LIFECYCLE_SOURCE, library.IOS_WORKER_OWNERSHIP_SOURCE,
                         library.IOS_SHEET_REPEAT_SOURCE, library.IOS_MODAL_XCUI_SOURCE):
            self.assertNotIn("NATIVECMPKIT_WORKER_LIFECYCLE", (ROOT / relative).read_text())

    def test_three_green_finished_cases_and_all_observations_still_require_worker_completion(self):
        result = protocol(finished_frames() + observations())
        partial = result.partial()
        self.assertEqual(3, partial["counts"]["passed"])
        self.assertEqual(6, len(partial["worker_lifecycle_observations"]))
        self.assertFalse(partial["complete_native_lifecycle"])
        self.assertIsNone(partial["completion"])
        with self.assertRaisesRegex(ValueError, "Missing native Worker/application completion"):
            result.finish(0)

    def test_complete_observed_transport_preserves_failed_cases_under_no_exit_code_contract(self):
        result = protocol(finished_frames(failed=True) + observations() + [COMPLETE]).finish(0)
        self.assertEqual(3, result["counts"]["executed"])
        self.assertEqual(2, result["counts"]["failures"])
        self.assertEqual(1, result["counts"]["passed"])
        self.assertEqual({"runner_exit": 0, "worker_terminated": True}, result["completion"])
        self.assertEqual([{"phase": phase, "runner_exit": 0, "main_thread": main}
                          for phase, main in application.WORKER_LIFECYCLE_STEPS],
                         result["worker_lifecycle_observations"])

    def test_phase_thread_order_cardinality_exit_and_payload_are_strict_before_retention(self):
        first = observations()[0]
        invalid = (observations()[1], first.replace("mainThread=false", "mainThread=true"),
                   first.replace("runnerExit=0", "runnerExit=-1"),
                   first.replace("runnerExit=0", "runnerExit=2147483648"),
                   first.replace("runnerExit=0", "runnerExit=00"), first + " untrusted=value",
                   first.replace("runner-returned", "unknown"), first + "\r")
        for value in invalid:
            with self.subTest(value=value):
                result = protocol(finished_frames())
                with self.assertRaisesRegex(ValueError, "Invalid owned Worker lifecycle observation"):
                    result.feed(value)
                self.assertEqual([], result.worker_lifecycle_observations)
        for prefix in ([], [ACTIVE], [ACTIVE, frame("testSuiteStarted", name="synthetic"),
                                    frame("testStarted", name="unfinished")],
                       finished_frames() + observations() + [COMPLETE]):
            result = protocol(prefix)
            count = len(result.worker_lifecycle_observations)
            with self.assertRaises(ValueError): result.feed(first)
            self.assertEqual(count, len(result.worker_lifecycle_observations))
        result = protocol(finished_frames() + [first])
        for value in (first, observations()[1].replace("runnerExit=0", "runnerExit=1")):
            with self.assertRaises(ValueError): result.feed(value)
        self.assertEqual(1, len(result.worker_lifecycle_observations))

    def test_incomplete_observation_cannot_be_hidden_by_completion_or_break_old_exact_protocols(self):
        for count in range(1, 6):
            result = protocol(finished_frames() + observations()[:count])
            with self.assertRaisesRegex(ValueError, "Incomplete owned Worker lifecycle observation"):
                result.feed(COMPLETE)
            self.assertIsNone(result.completed)
        # Reading the original exact protocol is backwards compatible, not a
        # replay of any previously accepted native population or report.
        result = protocol(finished_frames() + [COMPLETE]).finish(0)
        self.assertEqual(3, result["counts"]["passed"])
        self.assertNotIn("worker_lifecycle_observations", result)

    def test_real_owned_python_console_eof_zero_retains_boundary_and_remains_failed(self):
        lines = finished_frames() + observations()[:3]
        result = application.NativeProtocol()
        output = SimpleNamespace(buffer=io.BytesIO())
        code = "import sys; sys.stdout.write(" + repr("\n".join(lines) + "\n") + "); sys.stdout.flush()"
        with patch.object(application.sys, "stdout", output), self.assertRaisesRegex(
                ValueError, "Missing native Worker/application completion"):
            application.forward_application([sys.executable, "-c", code], result, timeout=10)
        self.assertEqual(("\n".join(lines) + "\n").encode(), output.buffer.getvalue())
        receipt = result.transport_observation
        self.assertEqual("protocol-finish", receipt["failure_stage"])
        self.assertEqual("missing-worker-completion", receipt["failure_reason"])
        self.assertEqual(0, receipt["console_process_exit"])
        self.assertEqual(0, receipt["console_process_exit_after_cleanup"])
        self.assertFalse(receipt["console_cleanup_requested"])
        partial = result.partial()
        self.assertEqual(3, partial["counts"]["passed"])
        self.assertEqual("termination-requested", partial["worker_lifecycle_observations"][-1]["phase"])
        self.assertFalse(partial["complete_native_lifecycle"])

    def test_one_five_case_plan_and_five_source_compiler_exclude_accepted_and_xctest_methods(self):
        focus = library.IOS_MODAL_COMPLETION_FOCUS
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
        required = library.ui_application_focus_identities(focus)
        self.assertEqual(5, len(required))
        self.assertEqual(required, plan["expected"][0]["required_testcases"])
        self.assertEqual(library.ui_application_focus_identities(library.IOS_MODAL_WORKER_MEMORY_FOCUS) +
                         library.ui_application_focus_identities(library.IOS_SHEET_REPEAT_FOCUS), required)
        command = library.gradle_command("ios", plan, DEVICE)
        self.assertEqual(1, command.count(COMPILER))
        self.assertEqual([":calf-ui:iosSimulatorArm64ApplicationTest"] + [arg
            for identity in library.ui_application_focus_filter(focus).split(",") for arg in ("--tests", identity)],
            command[command.index(":calf-ui:iosSimulatorArm64ApplicationTest"):])
        compiler = (ROOT / COMPILER).read_text()
        paths = re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', compiler)
        self.assertEqual([library.IOS_MODAL_LIFECYCLE_SOURCE, library.IOS_WORKER_OWNERSHIP_SOURCE,
                          HOST, HOST.replace("NativeUiApplicationHost", "NativeObjectIdentity"),
                          library.IOS_SHEET_REPEAT_SOURCE], paths)
        for marker in ("common.setFrom(emptyList<Any>())", '"native_tests_executed" to 0',
                       '"production_source_sets_changed" to false', 'NATIVECMPKIT_UI_FOCUSED_COMPILE sources=5'):
            self.assertIn(marker, compiler)
        self.assertNotIn(library.IOS_MODAL_XCUI_SOURCE, compiler)
        forbidden = {*library.IOS_MODAL_OWNERSHIP_METHODS, *library.IOS_MODAL_XCUI_METHODS,
                     *library.IOS_MODAL_LIFECYCLE_METHODS[1:]}
        self.assertTrue({item["name"].removesuffix("[iosSimulatorArm64]") for item in required}.isdisjoint(forbidden))

    def test_compiler_accepts_only_compile_or_the_exact_ordered_five_case_request(self):
        source = (ROOT / COMPILER).read_text()
        permitted = source.split("    val permittedTasks = setOf(\n", 1)[1].split("    check(gradle.startParameter", 1)[0]
        self.assertEqual([':calf-ui:compileTestKotlinIosSimulatorArm64'], re.findall(r'listOf\("([^"]+)"\)', permitted))
        self.assertEqual(1, permitted.count("applicationRequest,"))
        request = source.split("    val applicationRequest = ", 1)[1].split("    val permittedTasks", 1)[0]
        identities = re.findall(r'"(com\.mohamedrejeb\.[^"\n]+)"', request)
        self.assertEqual(library.ui_application_focus_filter(library.IOS_MODAL_COMPLETION_FOCUS).split(","), identities)
        self.assertNotIn("*", request)
        self.assertIn('flatMap { identity -> listOf("--tests", identity) }', request)
        self.assertIn("gradle.startParameter.taskNames in permittedTasks", source)

    def test_profile_reserves_one_real_host_and_cannot_mutate_independent_plans(self):
        profile = "ios-modal-completion-cancellation"
        original = copy.deepcopy(workflow.matrix("ios-sheet-cancellation-repeat"))
        expected = {"include": [{"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                    "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-ui",
                    "test-focus": library.IOS_MODAL_COMPLETION_FOCUS}]}
        self.assertEqual(expected, workflow.matrix(profile))
        changed = workflow.matrix(profile); changed["include"][0]["test-focus"] = "foreign"
        self.assertEqual(expected, workflow.matrix(profile))
        self.assertEqual(original, workflow.matrix("ios-sheet-cancellation-repeat"))
        for slots in (("ios-ipad",), ("desktop-macos-arm64",), ("ios-iphone", "ios-ipad")):
            with patch.dict(workflow.PROFILES, {profile: slots}), self.assertRaises(ValueError):
                workflow.matrix(profile)
        with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError):
            workflow.matrix(profile)
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(profile, source)
        self.assertIn("permissions:\n  contents: read\n", source)
        self.assertIn("persist-credentials: false", source)
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, library.IOS_MODAL_COMPLETION_FOCUS))

    def test_exact_additive_history_preserves_all_old_pins_without_recursive_readmission(self):
        self.assertEqual("8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48", worker.SPEC_SHA256)
        bindings = history._bindings()
        self.assertEqual(6, len(bindings))
        self.assertEqual(19, sum(len(b["fragments"]) for b in bindings.values()))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_worker_completion(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_worker_completion(relative, previous))
            for bad in (previous, current + b"\n", current[:-1], b"", bytearray(current)):
                with self.assertRaises(ValueError): history.current_source_before_worker_completion(relative, bad)
        for relative, binding in worker._bindings().items():
            current = (ROOT / relative).read_bytes()
            previous = worker.current_source_before_modal_worker(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, worker.source_before_modal_worker(relative, previous))
            for bad in (previous, current + b"\n", current.replace(b"\n", b"\r\n")):
                with self.assertRaises(ValueError): worker.current_source_before_modal_worker(relative, bad)

    def test_historical_reader_barrier_is_causal_not_a_brittle_latest_stage_error_message(self):
        tree = ast.parse((ROOT / FIXTURE).read_text())
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and
                     node.name == "refuse_historical_library_read"]
        self.assertEqual(1, len(functions))
        reader = Mock(return_value=b"exact-other-owned-image")
        calls = []
        namespace = {"relative": "scripts/ci/library_tests.py", "historical_library_calls": calls,
                     "historical_reader": reader}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<new-causal-reader-barrier-only>", "exec"), namespace)
        guard = namespace["refuse_historical_library_read"]
        with self.assertRaises(AssertionError): guard("scripts/ci/library_tests.py", b"synthetic-rejected-current")
        self.assertEqual(["scripts/ci/library_tests.py"], calls)
        reader.assert_not_called()
        self.assertEqual(b"exact-other-owned-image", guard("other-owned-path", b"other-current"))
        reader.assert_called_once_with("other-owned-path", b"other-current")
        source = (ROOT / FIXTURE).read_text().split("    def test_owning_manifest_check_refuses_", 1)[1]
        self.assertNotIn("assertRaisesRegex", source)
        self.assertIn('patch.object(bridge, "current_source_for_history", side_effect=refuse_historical_library_read)', source)
        self.assertIn("self.assertRaises(ValueError)", source)
        self.assertIn("self.assertEqual([], historical_library_calls)", source)


if __name__ == "__main__":
    unittest.main()
