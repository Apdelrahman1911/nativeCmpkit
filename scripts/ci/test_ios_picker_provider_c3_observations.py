# SPDX-License-Identifier: Apache-2.0
"""NEW stdlib tooling controls only; not native/Foundation/UI acceptance.

These declarations must be independently reviewed before their first execution.
No accepted tests/native method bodies are imported or replayed. ps is always
mocked; any child used below is a local stdlib Python synthetic console only.
"""
import ast
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ios_ui_application as a

BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
CASE = ("com.mohamedrejeb.calf.picker.NativePhotoProviderCancellationTest",
        "publicPhotoCancellationStopsAnInFlightNativeProviderCopyAndReleasesEarlierStaging")
FILTER = "--ktest_gradle_filter=" + ".".join(CASE)
ARGS = ["--ktest_logger=TEAMCITY", "--ktest_no_exit_code", FILTER]
HOST = {"module": "calf-file-picker", **a.APPLICATION_HOSTS["calf-file-picker"]}
FOCUS = a.lt.IOS_PICKER_PROVIDER_CANCELLATION_FOCUS
EXE = Path("/private/owned-nonce/NativeCmpkitLibraryTests.app") / a.APP_EXECUTABLE
MISSING = "Missing native Worker/application completion"
ACTIVE = "NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2"
COMPLETE = "NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true"


def frame(event, name):
    return "##teamcity[" + event + " name='" + name + "']"


def begun(enabled=True, case=CASE):
    protocol = a.NativeProtocol(bundle_id=BUNDLE, provider_c3_only=enabled)
    for line in [BUNDLE + ": 321", ACTIVE, frame("testSuiteStarted", case[0]), frame("testStarted", case[1])]:
        protocol.feed(line)
    return protocol


class ProviderC3ObservationRouteControls(unittest.TestCase):
    def test_only_exact_sole_owned_c3_route_opts_in_regardless_of_argument_order(self):
        self.assertEqual(CASE, a.PICKER_PROVIDER_C3_CASE)
        self.assertEqual((CASE[1],), a.lt.IOS_PICKER_PROVIDER_CANCELLATION_METHODS)
        self.assertTrue(a.provider_c3_observation_route(HOST, FOCUS, ARGS))
        self.assertTrue(a.provider_c3_observation_route(HOST, FOCUS, list(reversed(ARGS))))

    def test_full_other_module_focus_duplicate_extra_wildcard_or_malformed_route_stays_out(self):
        cases = [(HOST, None, ARGS[:2]), (HOST, "picker-ios-batch", ARGS),
                 ({**HOST, "module": "calf-ui"}, FOCUS, ARGS),
                 ({**HOST, "task": ":calf-ui:iosSimulatorArm64ApplicationTest"}, FOCUS, ARGS),
                 ({**HOST, "binary_directory": "foreign"}, FOCUS, ARGS),
                 (HOST, FOCUS, ARGS + [FILTER]), (HOST, FOCUS, ARGS[:2] + [ARGS[0]]),
                 (HOST, FOCUS, ARGS[:2] + [FILTER + "," + FILTER]),
                 (HOST, FOCUS, ARGS[:2] + [FILTER + "*"]), (HOST, FOCUS, tuple(ARGS)),
                 (HOST, FOCUS, ARGS[:2] + [[]])]
        for host, focus, arguments in cases:
            with self.subTest(host=host, focus=focus, arguments=arguments):
                self.assertFalse(a.provider_c3_observation_route(host, focus, arguments))

    def test_observation_protocol_requires_exact_boolean_and_owned_bundle(self):
        for flag in [1, 0, None, "true"]:
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                a.NativeProtocol(bundle_id=BUNDLE, provider_c3_only=flag)
        with self.assertRaises(ValueError): a.NativeProtocol(provider_c3_only=True)
        self.assertFalse(a.NativeProtocol().provider_c3_only)


class ProviderC3ReturnMarkerControls(unittest.TestCase):
    def test_exact_c3_main_return_is_typed_failure_never_native_completion(self):
        protocol = begun()
        with self.assertRaisesRegex(ValueError, "native lifecycle failure"):
            protocol.feed(a.PICKER_PROVIDER_C3_MAIN_RETURNED)
        partial = protocol.partial()
        self.assertEqual({"stage": "application_main_return", "worker_termination_verified": False},
                         partial["lifecycle_failure_observation"])
        self.assertEqual(0, partial["counts"]["executed"])
        self.assertEqual("incomplete", partial["unfinished_testcase"]["status"])
        self.assertIsNone(partial["completion"])
        with self.assertRaises(ValueError): protocol.finish(0)
        with self.assertRaises(ValueError): protocol.feed(a.PICKER_PROVIDER_C3_MAIN_RETURNED)

    def test_exact_selected_preworker_return_is_a_boundary_not_activation_or_execution(self):
        protocol = a.NativeProtocol(bundle_id=BUNDLE, provider_c3_only=True)
        with self.assertRaisesRegex(ValueError, "native lifecycle failure"):
            protocol.feed(a.PICKER_PROVIDER_C3_MAIN_RETURNED)
        self.assertIsNone(protocol.active)
        self.assertEqual(0, protocol.partial()["counts"]["executed"])

    def test_non_c3_completed_foreign_case_and_malformed_markers_are_not_typed(self):
        completed = begun()
        for line in [frame("testFinished", CASE[1]), frame("testSuiteFinished", CASE[0]), COMPLETE]:
            completed.feed(line)
        for protocol in [begun(False), a.NativeProtocol(), completed, begun(case=(CASE[0], "foreign"))]:
            with self.subTest(protocol=protocol), self.assertRaises(ValueError):
                protocol.feed(a.PICKER_PROVIDER_C3_MAIN_RETURNED)
            self.assertIsNone(protocol.lifecycle_failure_observation)
        for suffix in [" private=payload", "\n", "x"]:
            protocol = begun()
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                protocol.feed(a.PICKER_PROVIDER_C3_MAIN_RETURNED + suffix)
            self.assertIsNone(protocol.lifecycle_failure_observation)


class ProviderC3ExactPidControls(unittest.TestCase):
    def test_one_bounded_exact_pid_path_match_retains_only_fixed_qualified_scalars(self):
        result = SimpleNamespace(returncode=0, stdout=str(EXE).encode() + b"\n", stderr=b"")
        with patch.object(a, "execute_control", return_value=result) as command:
            observation = a.observe_preverified_owned_launch_pid(321, EXE)
        command.assert_called_once_with(["/bin/ps", "-p", "321", "-o", "comm="], 1)
        self.assertEqual({"state": "live-matched-preverified-owned-executable-path",
                          "raw_process_text_or_paths_uploaded": False, "native_exit_cause_proven": False}, observation)
        self.assertNotIn(str(EXE), repr(observation))
        self.assertNotIn("321", repr(observation))

    def test_invalid_pid_or_unowned_relative_path_never_starts_a_command(self):
        for pid, path in [(None, EXE), (True, EXE), (0, EXE), (-1, EXE), (2**31, EXE), ("321", EXE),
                          (321, Path("relative/NativeCmpkitLibraryTests.app") / a.APP_EXECUTABLE),
                          (321, EXE.parent / "foreign"), (321, Path("/private/foreign.app") / a.APP_EXECUTABLE),
                          (321, str(EXE)), (321, Path("/private/unsafe\n/NativeCmpkitLibraryTests.app") / a.APP_EXECUTABLE),
                          (321, Path("/" + "a" * 4096 + "/NativeCmpkitLibraryTests.app") / a.APP_EXECUTABLE)]:
            with self.subTest(pid=pid, path=path), patch.object(a, "execute_control") as command:
                self.assertEqual("unavailable", a.observe_preverified_owned_launch_pid(pid, path)["state"])
                command.assert_not_called()

    def test_empty_missing_mismatched_unbounded_or_errored_rows_never_prove_exit(self):
        raw = str(EXE).encode()
        variants = [(1, b"", b"", "not-observed"), (0, b"", b"", "unavailable"),
                    (False, raw + b"\n", b"", "unavailable"), (0, raw + b"\n", b"error", "unavailable"),
                    (0, raw + b"\n" + raw + b"\n", b"", "unavailable"),
                    (0, b" " + raw + b"\n", b"", "unavailable"),
                    (0, raw + b"x\n", b"", "unavailable"), (0, b"\xff", b"", "unavailable"),
                    (0, b"x" * 4097, b"", "unavailable"), (0, raw, b"x" * 4097, "unavailable"),
                    (2, b"", b"", "unavailable"), (0, str(EXE), b"", "unavailable")]
        for code, stdout, stderr, state in variants:
            result = SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)
            with self.subTest(code=code, state=state), patch.object(a, "execute_control", return_value=result):
                observation = a.observe_preverified_owned_launch_pid(321, EXE)
                self.assertEqual(state, observation["state"])
                self.assertFalse(observation["native_exit_cause_proven"])
        for error in [OSError("synthetic"), ValueError("synthetic"), subprocess.TimeoutExpired("synthetic", 1)]:
            with self.subTest(error=type(error)), patch.object(a, "execute_control", side_effect=error):
                self.assertEqual("unavailable", a.observe_preverified_owned_launch_pid(321, EXE)["state"])


class ProviderC3FailureBoundaryControls(unittest.TestCase):
    def test_only_plain_missing_completion_valueerror_exact_stage_integer_zero_and_sole_open_c3_can_probe(self):
        protocol = begun()
        sentinel = {"state": "unavailable", "raw_process_text_or_paths_uploaded": False, "native_exit_cause_proven": False}
        with patch.object(a, "observe_preverified_owned_launch_pid", return_value=sentinel) as probe:
            self.assertIs(sentinel, a.observe_provider_c3_protocol_failure(protocol, ValueError(MISSING), "protocol-finish", 0, EXE))
        probe.assert_called_once_with(321, EXE)
        for error, stage, code in [(KeyboardInterrupt(), "protocol-finish", 0), (SystemExit(), "protocol-finish", 0),
                                   (RuntimeError(MISSING), "protocol-finish", 0), (ValueError("other"), "protocol-finish", 0),
                                   (ValueError(MISSING), "protocol-feed", 0), (ValueError(MISSING), "console-wait", 0),
                                   (ValueError(MISSING), "protocol-finish", False), (ValueError(MISSING), "protocol-finish", 1),
                                   (ValueError(MISSING), "protocol-finish", None)]:
            with self.subTest(error=type(error), stage=stage, code=code), patch.object(a, "observe_preverified_owned_launch_pid") as probe:
                self.assertIsNone(a.observe_provider_c3_protocol_failure(protocol, error, stage, code, EXE))
                probe.assert_not_called()
        for protocol in [begun(False), a.NativeProtocol(bundle_id=BUNDLE, provider_c3_only=True),
                         begun(case=(CASE[0], "foreign"))]:
            with self.subTest(protocol=protocol), patch.object(a, "observe_preverified_owned_launch_pid") as probe:
                self.assertIsNone(a.observe_provider_c3_protocol_failure(protocol, ValueError(MISSING), "protocol-finish", 0, EXE))
                probe.assert_not_called()
        protocol = begun()
        protocol.cases[(CASE[0], "foreign")] = {"status": "running"}
        with patch.object(a, "observe_preverified_owned_launch_pid") as probe:
            self.assertIsNone(a.observe_provider_c3_protocol_failure(protocol, ValueError(MISSING), "protocol-finish", 0, EXE))
            probe.assert_not_called()

    def test_observer_error_keeps_original_protocol_refusal_and_incomplete_counts(self):
        lines = [BUNDLE + ": 321", ACTIVE, frame("testSuiteStarted", CASE[0]), frame("testStarted", CASE[1])]
        code = "\n".join("print(" + repr(line) + ",flush=True)" for line in lines)
        protocol = a.NativeProtocol(bundle_id=BUNDLE, provider_c3_only=True)
        output = SimpleNamespace(buffer=io.BytesIO())
        observed_before_cleanup = []
        def unavailable(pid, path):
            observed_before_cleanup.append(protocol.transport_observation)
            raise RuntimeError("synthetic diagnostic error")
        with tempfile.TemporaryDirectory() as directory, patch.object(a.lt, "ROOT", Path(directory)), \
                patch.object(a.sys, "stdout", output), patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)), \
                patch.object(a, "observe_preverified_owned_launch_pid", side_effect=unavailable) as probe:
            with self.assertRaisesRegex(ValueError, "^" + MISSING + "$"):
                a.forward_application([sys.executable, "-u", "-c", code], protocol, 5, provider_c3_installed_executable=EXE)
        probe.assert_called_once_with(321, EXE)
        self.assertEqual([None], observed_before_cleanup)
        observation = protocol.transport_observation
        self.assertEqual("protocol-finish", observation["failure_stage"])
        self.assertEqual("missing-worker-completion", observation["failure_reason"])
        self.assertEqual(0, observation["console_process_exit"])
        self.assertFalse(observation["console_cleanup_requested"])
        self.assertEqual("unavailable", observation["owned_launch_pid_at_console_failure"]["state"])
        self.assertEqual(0, protocol.partial()["counts"]["executed"])
        self.assertEqual(("\n".join(lines) + "\n").encode(), output.buffer.getvalue())

    def test_source_call_shape_and_native_marker_are_c3_only_without_changed_native_method(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / "scripts/ci/ios_ui_application.py").read_text()
        tree = ast.parse(source)
        run = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run")
        options = next(node for node in run.body if isinstance(node, ast.Try)).body
        branches = [node for node in options if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "provider_c3_only"]
        self.assertEqual(1, len(branches))
        self.assertIn('provider_c3_options["provider_c3_installed_executable"] = installed_executable', source)
        self.assertNotIn("provider_c3_installed_executable=None", source)
        forward = next(node for node in ast.walk(run) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "forward_application")
        self.assertTrue(any(keyword.arg is None and isinstance(keyword.value, ast.Name) and keyword.value.id == "provider_c3_options" for keyword in forward.keywords))
        host = (root / "calf-file-picker/src/iosTest/kotlin/com/mohamedrejeb/calf/picker/internal/NativePickerApplicationHost.kt").read_text()
        body = host.split("fun nativeApplicationMain(arguments: Array<String>) {", 1)[1]
        self.assertLess(body.index("UIApplicationMain(0, null, null, NSStringFromClass(delegate))"), body.index("if (arguments.size == 3"))
        self.assertIn("arguments.toSet() == setOf(", body)
        for literal in ARGS[:2]: self.assertIn('"' + literal + '"', body)
        self.assertIn('"--ktest_gradle_filter=' + CASE[0] + '." +', body)
        self.assertIn('"' + CASE[1] + '"', body)
        self.assertEqual(1, body.count('println("NATIVECMPKIT_UIKIT_MAIN_RETURNED")'))


if __name__ == "__main__":
    unittest.main()
