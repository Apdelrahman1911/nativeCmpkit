# SPDX-License-Identifier: Apache-2.0
"""NEW source/mock controls: no Cargo, JNI, AppKit, SDK, Git or sample execution."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import macos_share_appkit_lifecycle as runner
import macos_share_missing_only as recovery
from test_macos_share_appkit_lifecycle_runner import artifact, cargo_stdout, execution, make_reports, markers


class MissingSelection(unittest.TestCase):
    def test_fixed_six_route_compiles_once_and_excludes_all_four_accepted_bodies(self):
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no process")):
            value = runner.plan(missing_only=True)
        self.assertEqual(list(recovery.MISSING_APPKIT), value["exact_native_cases"])
        self.assertEqual([["<admitted-mh-execute>", "--case=" + name] for name in recovery.MISSING_APPKIT],
                         value["native_commands"])
        self.assertTrue(value["compile_once"])
        self.assertTrue(value["stop_on_first_failure"])
        self.assertIsNone(value["native_command"])
        self.assertIsNone(value["native_case_arguments"])
        self.assertFalse(value["stress_selected"])
        self.assertEqual([], value["publication_commands"])
        self.assertEqual(1, value["cargo_command"].count("--no-run"))
        self.assertEqual(recovery.jni_identities(), [{"classname": recovery.JNI_CLASS,
                                                     "name": recovery.JNI_METHOD + "[desktop]"}])
        self.assertEqual(2, len(value["recovery_reference"]["unchanged_passed_jni_methods_reused_not_replayed"]))

    def test_default_eight_is_unchanged_and_single_selection_never_means_a_skip_list(self):
        default = runner.plan()
        self.assertEqual(list(runner.CASES), default["exact_native_cases"])
        self.assertEqual(["<admitted-mh-execute>"], default["native_command"])
        self.assertEqual([], default["native_case_arguments"])
        self.assertNotIn("native_commands", default)
        for name in recovery.MISSING_APPKIT:
            with self.subTest(name=name):
                value = runner.plan(name)
                self.assertEqual([name], value["exact_native_cases"])
                self.assertEqual(["--case=" + name], value["native_case_arguments"])
        for invalid in (*recovery.ACCEPTED_APPKIT, "stress_2048", "unknown", "missing_content_view,real_picker_cancel", [], True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                recovery.appkit_selection(invalid)
        for population in ((), (recovery.MISSING_APPKIT[0], recovery.MISSING_APPKIT[1]),
                           tuple(reversed(recovery.MISSING_APPKIT)), list(recovery.MISSING_APPKIT)):
            with self.subTest(population=population), self.assertRaises(ValueError):
                recovery.validate_population(population)

    def test_bad_selection_is_refused_before_output_or_native_and_cli_is_read_only(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for case, missing in (("no_key_window", False), ("missing_content_view", True), (None, 1)):
                with self.subTest(case=case, missing=missing), self.assertRaises(ValueError), \
                        patch.object(runner, "build_environment", side_effect=AssertionError("no setup")):
                    runner.run(root, "build/ci-verification/new", case, missing_only=missing)
            self.assertEqual([], list(root.iterdir()))
        with patch.object(runner.sys, "argv", ["runner", "--plan", "--missing-only-share630"]), \
                patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no process")), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, runner.main())
        self.assertEqual(list(recovery.MISSING_APPKIT), json.loads(output.getvalue())["exact_native_cases"])


class NativeBatchControls(unittest.TestCase):
    def modeled_run(self, root: Path, *, failed=None, drift_after=None, fail_compile=False):
        calls, state = [], {"source": "a" * 64}
        inputs = lambda _: {"source-model": state["source"], recovery.CASES_SOURCE: recovery.CASES_SHA,
                            recovery.OPERATION_SOURCE: recovery.OPERATION_SHA}
        runtime = {"host": "source/mock-not-native", "epoch": 1}

        def logged(root, output, role, command, environment, timeout, maximum):
            calls.append((role, command))
            started = time.time_ns()
            if role == "cargo":
                _, value = artifact(root, Path(command[-1]))
                return execution(passed=not fail_compile, started=started), cargo_stdout(value)
            case = command[1].removeprefix("--case=")
            pid = 5000 + len(calls)
            make_reports(root, (case,), failed=case if failed == case else None, pid=pid)
            stdout = markers((case,), passed=failed != case)
            stderr = b"source/mock diagnostic only, not an original native stream\n" if failed == case else b""
            private_logs = []
            for stream, payload in (("stdout", stdout), ("stderr", stderr)):
                path = output / ("native." + stream + ".private.log")
                path.write_bytes(payload)
                private_logs.append({"relative_path": path.relative_to(root).as_posix(), **runner.file_identity(path)})
            result = execution(passed=failed != case, pid=pid, started=started)
            result["private_logs"] = private_logs
            if drift_after == case:
                state["source"] = "c" * 64
            return result, stdout

        with patch.object(runner, "build_environment", return_value={"NATIVECMPKIT_NATIVE_UI_TESTS": "true"}), \
                patch.object(runner, "git_identity", return_value={"source_revision": "d" * 40, "source_tree_dirty": False}), \
                patch.object(runner.library, "snapshot_inputs", side_effect=inputs), \
                patch.object(runner.native, "expected_source_files", return_value={"native-model": "b" * 64}), \
                patch.object(runner, "runtime_identity", return_value=runtime), \
                patch.object(runner, "source_contract", return_value={"raw_control_flag_exported": False,
                                                                     "raw_control_flag_independently_observed": False}), \
                patch.object(runner, "logged_execution", side_effect=logged), \
                patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no actual process")):
            result = runner.run(root, "build/ci-verification/new", missing_only=True)
        return result, calls

    def test_one_compile_six_serial_fresh_processes_exact_xml_and_unchanged_original_baseline(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            make_reports(root, recovery.ACCEPTED_APPKIT, pid=1111)
            original = runner.report_state(root)
            result, calls = self.modeled_run(root)
            self.assertTrue(result["passed"])
            self.assertEqual(["cargo"] + ["native"] * 6, [role for role, command in calls])
            self.assertEqual(["--case=" + name for name in recovery.MISSING_APPKIT],
                             [command[1] for role, command in calls if role == "native"])
            self.assertEqual(1, len({command[0] for role, command in calls if role == "native"}))
            self.assertEqual(6, len({row["native_execution"]["pid"] for row in result["native_case_runs"]}))
            self.assertEqual(6, result["native_reports"]["accepted_xml_cases"])
            self.assertEqual([], result["native_reports"]["remaining_unexecuted_cases"])
            self.assertTrue(result["reports_held"])
            self.assertTrue(result["owned_lock_released"])
            current = runner.report_state(root)
            self.assertEqual(original, {key: current[key] for key in original})
            for row in result["native_case_runs"]:
                folder = root / "build/ci-verification/new/cases" / row["case"]
                self.assertEqual(row, json.loads((folder / "receipt.json").read_text()))
                self.assertEqual(1, len(list((folder / "fresh-reports").glob("*.xml"))))
                self.assertTrue(row["inputs_after_held"])
                self.assertTrue(row["reports_held"])

    def test_failed_missing_view_stops_the_same_batch_retains_red_xml_and_unknown_observation(self):
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), failed="missing_content_view")
            self.assertFalse(result["passed"])
            self.assertEqual(["cargo", "native"], [role for role, command in calls])
            self.assertEqual(1, len(result["native_case_runs"]))
            self.assertEqual("failed", result["native_reports"]["testcases"][0]["status"])
            self.assertEqual(list(recovery.MISSING_APPKIT[1:]), result["native_reports"]["remaining_unexecuted_cases"])
            observation = result["native_case_runs"][0]["missing_view_failure_observation"]
            self.assertFalse(observation["available"])
            self.assertFalse(observation["exact_native_cause_verified"])
            self.assertTrue(result["artifact_held"])
            self.assertTrue(result["reports_held"])
            self.assertTrue(result["owned_lock_released"])

    def test_later_failure_keeps_earlier_original_passes_and_never_reaches_remaining_cases(self):
        failed = recovery.MISSING_APPKIT[2]
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), failed=failed)
            self.assertFalse(result["passed"])
            self.assertEqual(1 + 3, len(calls))
            self.assertEqual(2, result["native_reports"]["accepted_xml_cases"])
            self.assertEqual(list(recovery.MISSING_APPKIT[3:]), result["native_reports"]["remaining_unexecuted_cases"])
            self.assertEqual("failed", result["native_reports"]["testcases"][-1]["status"])

    def test_compile_failure_or_postcase_source_drift_stops_without_claiming_missing_native(self):
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), fail_compile=True)
            self.assertFalse(result["passed"])
            self.assertEqual(["cargo"], [role for role, command in calls])
            self.assertNotIn("native_case_runs", result)
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), drift_after=recovery.MISSING_APPKIT[0])
            self.assertFalse(result["passed"])
            self.assertEqual(["cargo", "native"], [role for role, command in calls])
            self.assertFalse(result["native_case_runs"][0]["inputs_after_held"])
            self.assertFalse(result["inputs_held"])

    def test_selected_case_refuses_accepted_extra_xml_and_unknown_marker_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            folder = make_reports(root, ("missing_content_view", "no_key_window"))
            out = root / "build/ci-verification/new"
            out.mkdir()
            result = runner.collect_reports(root, out, execution(), {},
                                            markers(("missing_content_view", "no_key_window")), ("missing_content_view",))
            self.assertFalse(result["passed"])
            self.assertEqual(1, result["reached_original_xml"])
            self.assertTrue((folder / "TEST-no_key_window.xml").exists())
            self.assertFalse((out / "fresh-reports/TEST-no_key_window.xml").exists())


class FailureObservation(unittest.TestCase):
    def panic(self, *, line=61, reason="Owned AppKit window did not become key", path=recovery.CASES_SOURCE):
        # Synthetic source/mock text, never inferred from the unavailable Share630 stderr.
        return (f"thread 'main' (987654) panicked at {path}:{line}:9:\n{reason}\n"
                "note: source/mock only\n").encode()

    def observe(self, payload, **extra):
        return recovery.appkit_failure(payload, source_hash=recovery.CASES_SHA,
                                      operation_hash=recovery.OPERATION_SHA,
                                      source_absolute="/source/mock/" + recovery.CASES_SOURCE,
                                      failed_case="missing_content_view", **extra)

    def test_exact_original_assertion_phase_is_bounded_not_a_guessed_native_cause_or_pid(self):
        value = self.observe(self.panic())
        self.assertTrue(value["available"])
        self.assertEqual("owned-window-key-wait", value["phase"])
        self.assertFalse(value["exact_native_cause_verified"])
        self.assertFalse(value["raw_payload_exported"])
        self.assertFalse(value["native_queries_repeated"])
        self.assertNotIn("987654", json.dumps(value))
        self.assertNotIn("Owned AppKit", json.dumps(value))

    def test_missing_unknown_wrong_frame_multiple_or_overflow_remain_unavailable(self):
        for payload in (b"", b"private text must not be exported", self.panic(line=999),
                        self.panic(reason="unreviewed private assertion"), self.panic(path="/unrelated/cases.rs"),
                        self.panic() + self.panic(), b"\xff", b"x" * (recovery.MAX_STDERR + 1)):
            with self.subTest(payload_length=len(payload)):
                value = self.observe(payload)
                self.assertFalse(value["available"])
                self.assertFalse(value["raw_payload_exported"])
                self.assertNotIn("private text", json.dumps(value))
        value = recovery.appkit_failure(self.panic(), source_hash="0" * 64,
                                       operation_hash=recovery.OPERATION_SHA, source_absolute="/source/mock",
                                       failed_case="missing_content_view")
        self.assertFalse(value["available"])

    def test_terminal_enum_requires_exact_unchanged_operation_source_and_original_assertion_pair(self):
        payload = self.panic(line=151, reason="assertion `left == right` failed").replace(
            b"note: source/mock only", b"  left: 2\n right: 3")
        value = self.observe(payload)
        self.assertEqual("Failed", value["terminal_result_enum"])
        unknown = recovery.appkit_failure(payload, source_hash=recovery.CASES_SHA,
                                          operation_hash="0" * 64,
                                          source_absolute="/source/mock/" + recovery.CASES_SOURCE,
                                          failed_case="missing_content_view")
        self.assertEqual("unavailable", unknown["terminal_result_enum"])
        self.assertFalse(unknown["exact_native_cause_verified"])

    def test_owned_private_stream_must_match_original_file_identity_size_and_checksum(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); out = root / "build/ci-verification/new"; out.mkdir(parents=True)
            path = out / "native.stderr.private.log"; path.write_bytes(self.panic())
            logged = {"passed": False, "private_logs": [{"relative_path": path.relative_to(root).as_posix(),
                                                          **runner.file_identity(path)}]}
            reports = {"testcases": [{"name": "missing_content_view", "status": "failed"}]}
            inputs = {recovery.CASES_SOURCE: recovery.CASES_SHA, recovery.OPERATION_SOURCE: recovery.OPERATION_SHA}
            with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no native query")):
                self.assertTrue(runner.missing_view_failure_observation(root, out, logged, reports, inputs)["available"])
                path.write_bytes(b"changed private body")
                value = runner.missing_view_failure_observation(root, out, logged, reports, inputs)
            self.assertFalse(value["available"])
            self.assertNotIn("changed private", json.dumps(value))

    def test_success_or_unreached_failure_never_reads_private_stream(self):
        with patch.object(runner, "ordinary_file", side_effect=AssertionError("no private read")):
            for execution_value, rows in (({"passed": True}, [{"name": "missing_content_view", "status": "passed"}]),
                                          ({"passed": False}, []),
                                          ({"passed": False}, [{"name": "real_picker_cancel", "status": "failed"}])):
                value = runner.missing_view_failure_observation(Path("/source/mock"),
                        Path("/source/mock/build/ci-verification/new"), execution_value, {"testcases": rows}, {})
                self.assertFalse(value["available"])

    def marker(self, *, phase="InitialTimeout", active="0", live="unavailable", outcome="Failed.TimedOut",
               count="1", failures="0"):
        return (f"NATIVECMPKIT_SHARE_RETENTION phase={phase} active={active} live={live} outcome={outcome} "
                f"result_count={count} failure_count={failures}\n").encode()

    def test_jni_short_circuit_and_emitted_outcome_are_not_zero_or_a_confirmed_deadline_bug(self):
        value = recovery.jni_failure(self.marker(), expected_phase="InitialTimeout")
        self.assertTrue(value["available"])
        self.assertEqual("0", value["active"])
        self.assertEqual("unavailable", value["live"])
        self.assertEqual("Failed.TimedOut", value["outcome"])
        self.assertFalse(value["exact_native_cause_verified"])
        self.assertFalse(value["native_queries_repeated"])
        not_emitted = recovery.jni_failure(self.marker(outcome="not-emitted", count="0"),
                                           expected_phase="InitialTimeout")
        self.assertTrue(not_emitted["available"])
        self.assertEqual("not-emitted", not_emitted["outcome"])
        self.assertFalse(recovery.jni_failure(b"", expected_phase="InitialTimeout")["available"])

    def test_jni_duplicate_unknown_phase_private_payload_and_inconsistent_query_are_unavailable(self):
        for payload in (self.marker() * 2, self.marker(phase="ReplacementAfterTimeout"),
                        self.marker(active="0", live="0"), self.marker(active="1", live="1"),
                        self.marker(outcome="private error message"), self.marker(count="0"),
                        self.marker(count="2"), b"\xff", b"x" * (recovery.MAX_JNI_OUTPUT + 1)):
            with self.subTest(payload_length=len(payload)):
                value = recovery.jni_failure(payload, expected_phase="InitialTimeout")
                self.assertFalse(value["available"])
                self.assertFalse(value["raw_payload_exported"])
                self.assertNotIn("private error", json.dumps(value))
        overflow = recovery.jni_failure(self.marker(count="overflow", outcome="overflow", failures="overflow"),
                                         expected_phase="InitialTimeout")
        self.assertTrue(overflow["available"])
        self.assertEqual("overflow", overflow["result_count"])


class JniSourceAndPolicy(unittest.TestCase):
    def test_current_failure_helper_keeps_original_deadline_and_short_circuit_and_no_exception_body(self):
        source = (runner.ROOT / recovery.JNI_SOURCE).read_text()
        recovery.jni_validate_source(source, [recovery.JNI_SOURCE])
        helper = source.split("private fun awaitTimeoutRetention", 1)[1].split("private fun awaitNoNativeOwners", 1)[0]
        self.assertEqual(1, helper.count("NativeShareBridge.activeRequestCount()"))
        self.assertEqual(1, helper.count("NativeShareBridge.liveUiOperationCount()"))
        self.assertIn("if (queriedActive == 1) NativeShareBridge.liveUiOperationCount() else null", helper)
        after_catch = helper.split("catch (error: AssertionError)", 1)[1]
        self.assertNotIn("NativeShareBridge.", after_catch)
        self.assertNotIn("error.toString()", helper)
        self.assertNotIn("value.message", helper)
        self.assertIn("throw error", helper)
        self.assertIn("count <= 64", helper)
        self.assertIn("failureCount <= 64", helper)
        for altered in (source.replace("desktopTimeoutMillis = 2_000, allowClipboardFallback = false",
                                        "desktopTimeoutMillis = 20_000, allowClipboardFallback = false"),
                        source.replace("RetentionPhase.InitialTimeout)", "RetentionPhase.Other)"),
                        source.replace("@Test", "@Ignore\n@Test", 1)):
            with self.assertRaises(ValueError):
                recovery.jni_validate_source(altered, [recovery.JNI_SOURCE])

    def test_one_method_policy_refuses_accepted_replay_skip_other_hosts_and_optout(self):
        case = {**recovery.jni_identities()[0], "status": "passed"}
        scenarios, errors = recovery.jni_outcomes([case], "Darwin", True)
        self.assertEqual([], errors)
        self.assertEqual("required-executed", scenarios[0]["disposition"])
        for cases, system, optin in (([], "Darwin", True), ([case, case], "Darwin", True),
                                    ([{**case, "name": recovery.ACCEPTED_JNI[0]}], "Darwin", True),
                                    ([{**case, "status": "skipped"}], "Darwin", True),
                                    ([{**case, "status": "failed"}], "Darwin", True),
                                    ([case], "Windows", True), ([case], "Darwin", False)):
            with self.subTest(cases=cases, system=system, optin=optin):
                scenarios, errors = recovery.jni_outcomes(cases, system, optin)
                self.assertTrue(errors)
                self.assertEqual("required-not-passed", scenarios[0]["disposition"])
        recovery.jni_validate_host("Darwin", "arm64")
        for system, machine in (("Darwin", "x86_64"), ("Windows", "arm64"), ("Linux", "aarch64")):
            with self.assertRaises(ValueError):
                recovery.jni_validate_host(system, machine)

    def test_fixed_native_source_diagnostic_pins_are_unchanged_and_not_native_certification(self):
        self.assertEqual(recovery.CASES_SHA, hashlib.sha256((runner.ROOT / recovery.CASES_SOURCE).read_bytes()).hexdigest())
        self.assertEqual(recovery.OPERATION_SHA, hashlib.sha256((runner.ROOT / recovery.OPERATION_SOURCE).read_bytes()).hexdigest())
        self.assertTrue(recovery.recovery_reference()["original_failures_unwaived"])
        self.assertFalse(recovery.recovery_reference()["release_readiness_certified"])


if __name__ == "__main__":
    unittest.main()
