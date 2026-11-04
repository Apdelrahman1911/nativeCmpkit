"""NEW source/mock/file-custody controls only; no Cargo, AppKit, JNI or Git execution."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import struct
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

import macos_share_appkit_lifecycle as runner
import macos_share_key_wait_observation as key_wait


def execution(*, passed=True, pid=4242, started=0, ended=None):
    return {"started": True, "passed": passed, "pid": pid, "exit_code": 0 if passed else 1,
            "started_at_ns": started, "ended_at_ns": time.time_ns() if ended is None else ended,
            "stop_reason": None, "cleanup": {"leader_reaped": True, "group_empty": True,
                                             "forced": False, "clean": True}}


def xml(case, *, failed=False, live=0, registry=0, cleanup=True):
    failure = ('<failure message="Native assertion, control or owned cleanup failed; see original process log"/>'
               if failed else "")
    return (f'<?xml version="1.0" encoding="UTF-8"?><testsuite name="{runner.SUITE}" tests="1" '
            f'failures="{int(failed)}" errors="0" skipped="0"><testcase classname="{runner.CLASS}" '
            f'name="{case}" time="0.000001">{failure}<system-out>actual-native=true live={live} '
            f'registry={registry} cleanup={str(cleanup).lower()} controlled-callbacks-not-recipient=true'
            '</system-out></testcase></testsuite>\n').encode()


def markers(cases=runner.CASES, *, passed=True, live=0, registry=0, cleanup=True):
    return "".join(f"NATIVECMPKIT_APPKIT_CASE name={case} passed={str(passed).lower()} seconds=0.000001 "
                   f"live={live} registry={registry} cleanup={str(cleanup).lower()}\n" for case in cases).encode()


def make_reports(root: Path, cases=runner.CASES, *, failed=None, pid=4242):
    folder = root / runner.REPORT_PARENT / ("process-" + str(pid))
    folder.mkdir(parents=True)
    for case in cases:
        (folder / ("TEST-" + case + ".xml")).write_bytes(xml(case, failed=case == failed))
    return folder


def artifact(root: Path, target: Path, *, file_type=2):
    path = target / runner.TARGET / "debug/deps/appkit_lifecycle-0123abcd"
    path.parent.mkdir(parents=True)
    # Synthetic ordinary Mach-O header only. This file is NEVER executed.
    header = struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, file_type, 0, 0, 0, 0)
    path.write_bytes(header + b"source/mock-control-not-a-native-program")
    path.chmod(0o700)
    value = {"reason": "compiler-artifact", "package_id": "path+" + (root / "calf-share/native").as_uri()
             + "#calf-share-native@0.1.0", "target": {"name": "appkit_lifecycle", "kind": ["test"],
             "crate_types": ["bin"], "src_path": str(root / runner.MAIN), "edition": "2021"},
             "profile": {"test": True, "opt_level": "0", "debug_assertions": True},
             "features": ["appkit-lifecycle-tests"], "fresh": False,
             "filenames": [str(path)], "executable": str(path)}
    return path, value


def cargo_stdout(value, *other):
    return b"\n".join(json.dumps(entry).encode() for entry in (value, *other,
                         {"reason": "build-finished", "success": True})) + b"\n"


class SourceAndAdmission(unittest.TestCase):
    def test_readonly_plan_has_fixed_default_eight_no_selector_or_publication(self):
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no process")):
            value = runner.plan()
        self.assertEqual(list(runner.CASES), value["exact_native_cases"])
        self.assertEqual([], value["native_case_arguments"])
        self.assertFalse(value["stress_selected"])
        self.assertEqual([], value["publication_commands"])
        command = value["cargo_command"]
        self.assertEqual(["rustup", "run", "1.98.0", "cargo", "test"], command[:5])
        self.assertIn("--no-run", command)
        self.assertNotIn("--release", command)
        self.assertEqual(["<admitted-mh-execute>"], value["native_command"])
        self.assertEqual(8 * 1024 ** 3, value["disk_reserve_bytes"])
        self.assertNotRegex(" ".join(command), r"--case|stress|publish|\bbuild --release\b")

    def test_exact_reviewed_source_gate_does_not_invent_exported_flag_or_visibility(self):
        value = runner.source_contract(runner.ROOT, {
            name: hashlib.sha256((runner.ROOT / name).read_bytes()).hexdigest() for name in runner.HARNESS_PINS})
        self.assertTrue(value["source_bound_failed_control_gate_verified"])
        self.assertFalse(value["raw_control_flag_exported"])
        self.assertFalse(value["raw_control_flag_independently_observed"])
        source = (runner.ROOT / runner.CASES_SOURCE).read_text()
        finite = source.split("const FINITE:", 1)[1].split("struct Witness", 1)[0]
        self.assertEqual(list(runner.CASES), re.findall(r'"([a-z0-9_]+)"', finite))
        self.assertIn("result.is_ok() && cleanup.is_ok() && !CONTROL_FAILED.load(AtomicOrdering::Acquire)", source)
        self.assertIn("CONTROL_FAILED.store(true, AtomicOrdering::Release)", source)
        self.assertNotIn("raw-control-flag=", source)
        self.assertEqual(runner.HARNESS_PINS[runner.CASES_SOURCE],
            hashlib.sha256(key_wait.source_before_key_wait(runner.CASES_SOURCE, source.encode())).hexdigest())

    def test_changed_harness_hash_is_refused_before_native(self):
        altered = {**runner.HARNESS_PINS, runner.CASES_SOURCE: "0" * 64}
        with self.assertRaisesRegex(runner.Refusal, "unqualified-native-harness-bytes"):
            runner.source_contract(runner.ROOT, altered)

    def test_actual_wrong_host_and_optout_refused_without_tool_commands(self):
        with patch.object(runner.native, "current_platform", return_value="linux-x64"), \
                patch.object(runner, "private_capture", side_effect=AssertionError("no context process")):
            with self.assertRaisesRegex(runner.Refusal, "actual-macos-arm64-required"):
                runner.runtime_identity(runner.ROOT, {"NATIVECMPKIT_NATIVE_UI_TESTS": "true"})
        with patch.object(runner.native, "current_platform", return_value=runner.PLATFORM), \
                patch.object(runner.platform, "system", return_value="Darwin"), \
                patch.object(runner, "private_capture", side_effect=AssertionError("no context process")):
            for optin in (None, "false", "TRUE", "1", True):
                with self.subTest(optin=optin), self.assertRaisesRegex(runner.Refusal, "exact-native-gui-optin-required"):
                    runner.runtime_identity(runner.ROOT, {"NATIVECMPKIT_NATIVE_UI_TESTS": optin})

    def test_ambient_injection_and_cargo_config_are_refused_without_disclosing_values(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            clean = {"PATH": "/source-model-only", "CARGO_HOME": str(root / "cargo-home")}
            for key in ("DYLD_INSERT_LIBRARIES", "SDKROOT", "CARGO_BUILD_RUSTC_WRAPPER", "RUSTUP_DIST_SERVER"):
                with self.subTest(key=key), patch.object(runner.native, "_build_environment", return_value={
                        **clean, key: "not-a-secret-but-never-export"}):
                    with self.assertRaisesRegex(runner.Refusal, "ambient-build-or-native-injection-override") as caught:
                        runner.build_environment(root)
                    self.assertNotIn("not-a-secret", str(caught.exception))
            config = root / ".cargo/config.toml"
            config.parent.mkdir()
            config.write_text("# mock ambient configuration")
            with patch.object(runner.native, "_build_environment", return_value=clean):
                with self.assertRaisesRegex(runner.Refusal, "ambient-cargo-configuration"):
                    runner.build_environment(root)

    def test_confined_fresh_output_never_mutates_existing_or_source(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            existing = root / runner.DEFAULT_OUTPUT
            existing.mkdir(parents=True)
            witness = existing / "kept.txt"
            witness.write_text("preserved")
            for output in (runner.DEFAULT_OUTPUT, "../unrelated", "/tmp/unrelated",
                           "build/ci-verification", runner.REPORT_PARENT, runner.REPORT_PARENT + "/child"):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    runner.run(root, output)
            self.assertEqual("preserved", witness.read_text())
            self.assertFalse((existing / "receipt.json").exists())


class ProcessControls(unittest.TestCase):
    class Process:
        pid = 4242

        def __init__(self, *, running=False, descendants=False, ignore_term=False):
            self.returncode = None if running else 0
            self.alive = running or descendants
            self.ignore_term = ignore_term
            self.signals = []

        def poll(self):
            return self.returncode

        def wait(self, *, timeout):
            if self.returncode is None:
                raise subprocess.TimeoutExpired("source-model-only", timeout)
            return self.returncode

        def killpg(self, pid, sig):
            if pid != self.pid:
                raise AssertionError("not the owned process group")
            self.signals.append(sig)
            if sig == signal.SIGKILL or not self.ignore_term:
                self.alive = False
                if self.returncode is None:
                    self.returncode = -sig

    class Clock:
        elapsed = 0.0

        def now(self):
            return self.elapsed

        def sleep(self, duration):
            self.elapsed += duration

    def run_process(self, process, *, timeout=1, disk=None, payload=b"", maximum=1024):
        clock = self.Clock()
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr, \
                patch.object(runner.subprocess, "Popen", return_value=process) as spawn, \
                patch.object(runner.shutil, "disk_usage", return_value=type("Disk", (), {
                    "free": runner.DISK_RESERVE if disk is None else disk})()), \
                patch.object(runner, "group_alive", side_effect=lambda pid: process.alive), \
                patch.object(runner.os, "killpg", side_effect=process.killpg), \
                patch.object(runner.time, "monotonic", side_effect=clock.now), \
                patch.object(runner.time, "sleep", side_effect=clock.sleep):
            stdout.write(payload)
            stdout.flush()
            result = runner.execute(Path("/source-model-only"), ["mock-command"], stdout, stderr, {}, timeout, maximum)
            return result, spawn

    def test_clean_exit_requires_reaped_leader_and_empty_owned_group(self):
        process = self.Process()
        result, spawn = self.run_process(process)
        self.assertTrue(result["passed"])
        self.assertTrue(result["cleanup"]["leader_reaped"])
        self.assertTrue(result["cleanup"]["group_empty"])
        self.assertEqual([], process.signals)
        self.assertTrue(spawn.call_args.kwargs["start_new_session"])

    def test_timeout_sends_term_only_to_owned_group_and_stays_red(self):
        process = self.Process(running=True)
        result, _ = self.run_process(process)
        self.assertFalse(result["passed"])
        self.assertEqual("owned-process-timeout", result["stop_reason"])
        self.assertEqual([signal.SIGTERM], process.signals)
        self.assertTrue(result["cleanup"]["leader_reaped"])
        self.assertTrue(result["cleanup"]["group_empty"])
        self.assertFalse(result["cleanup"]["clean"])

    def test_stalled_term_escalates_kill_and_bounded_reap_without_green_recovery(self):
        process = self.Process(running=True, ignore_term=True)
        result, _ = self.run_process(process)
        self.assertFalse(result["passed"])
        self.assertEqual([signal.SIGTERM, signal.SIGKILL], process.signals)
        self.assertTrue(result["cleanup"]["kill_sent"])
        self.assertTrue(result["cleanup"]["leader_reaped"])
        self.assertTrue(result["cleanup"]["group_empty"])

    def test_zero_exit_with_surviving_descendants_is_cleaned_but_not_accepted(self):
        process = self.Process(descendants=True)
        result, _ = self.run_process(process)
        self.assertEqual(0, result["exit_code"])
        self.assertFalse(result["passed"])
        self.assertTrue(result["cleanup"]["forced"])
        self.assertEqual([signal.SIGTERM], process.signals)

    def test_disk_reserve_prevents_any_process_start(self):
        result, spawn = self.run_process(self.Process(), disk=runner.DISK_RESERVE - 1)
        spawn.assert_not_called()
        self.assertFalse(result["started"])
        self.assertEqual("eight-gib-disk-reserve-unavailable", result["stop_reason"])
        self.assertNotIn("pid", result)

    def test_excess_output_terminates_owned_process_and_retains_red_reason(self):
        process = self.Process(running=True)
        result, _ = self.run_process(process, payload=b"X" * 1025)
        self.assertFalse(result["passed"])
        self.assertEqual("process-output-size-bound", result["stop_reason"])
        self.assertEqual([signal.SIGTERM], process.signals)

    def test_cleanup_refusal_is_independent_of_primary_process_cause(self):
        process = self.Process()
        with patch.object(runner, "group_alive", return_value=False), \
                patch.object(process, "wait", side_effect=subprocess.TimeoutExpired("mock", 5)):
            result = runner.cleanup_group(process, force=True)
        self.assertEqual("owned-process-cleanup-refused-or-timed-out", result["cleanup_error"])
        self.assertFalse(result["clean"])
        self.assertFalse(result["leader_reaped"])

    def test_quiet_gui_probe_discards_payload_and_keeps_failure_cleanup_evidence(self):
        failed = {**execution(passed=False), "stop_reason": "owned-process-timeout"}
        with patch.object(runner, "execute", return_value=failed) as execute_mock:
            with self.assertRaises(runner.Refusal) as caught:
                runner.private_capture(Path("/source-model-only"), ["launchctl", "print", "gui/7"], {}, discard=True)
        self.assertTrue(execute_mock.call_args.kwargs["discard"])
        self.assertFalse(caught.exception.evidence["payload_archived"])
        self.assertEqual(failed, caught.exception.evidence["execution"])
        self.assertNotIn("gui/7", str(caught.exception))


class CargoArtifactControls(unittest.TestCase):
    def test_only_exact_fresh_native_executable_is_admitted_and_public_origin_is_relative(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            target = root / "build/ci-verification/new/cargo-target"
            path, value = artifact(root, target)
            admitted, receipt = runner.admit_artifact(root, target, cargo_stdout(value), execution())
            self.assertEqual(path, admitted)
            self.assertEqual("MH_EXECUTE", receipt["macho_file_type"])
            self.assertTrue(receipt["fresh_cargo_artifact"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), receipt["sha256"])
            self.assertNotIn(str(root), json.dumps(receipt))

    def test_duplicate_other_stale_or_unlocked_origin_cannot_select_a_binary(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            target = root / "build/ci-verification/new/cargo-target"
            _, value = artifact(root, target)
            variants = [cargo_stdout(value, value), cargo_stdout({**value, "fresh": True}),
                        cargo_stdout({**value, "package_id": "registry+unrelated"}),
                        cargo_stdout({**value, "features": ["appkit-lifecycle-tests", "unreviewed"]}),
                        cargo_stdout({**value, "target": {**value["target"], "name": "stress_2048"}}),
                        cargo_stdout({**value, "filenames": [value["executable"], "other"]}),
                        cargo_stdout({**value, "profile": {**value["profile"], "test": False}})]
            for payload in variants:
                with self.subTest(payload=payload[:50]), self.assertRaises(ValueError):
                    runner.admit_artifact(root, target, payload, execution())

    def test_compiler_failure_missing_terminal_nonjson_and_duplicate_keys_are_red(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            target = root / "build/ci-verification/new/cargo-target"
            _, value = artifact(root, target)
            for payload in (json.dumps(value).encode(), b"not Cargo JSON\n", cargo_stdout(value).replace(
                    b'"success": true', b'"success": false'), b'{"reason":"build-finished","success":true,"success":true}\n'):
                with self.subTest(payload=payload[:30]), self.assertRaises(ValueError):
                    runner.admit_artifact(root, target, payload, execution())
            with self.assertRaisesRegex(runner.Refusal, "cargo-compilation-not-accepted"):
                runner.admit_artifact(root, target, cargo_stdout(value), execution(passed=False))

    def test_arm64_dylib_or_other_cpu_is_not_an_executable(self):
        for file_type, cpu in ((6, 0x0100000C), (2, 0x01000007)):
            with self.subTest(file_type=file_type, cpu=cpu), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                target = root / "build/ci-verification/new/cargo-target"
                path, value = artifact(root, target, file_type=file_type)
                payload = bytearray(path.read_bytes())
                struct.pack_into("<I", payload, 4, cpu)
                path.write_bytes(payload)
                with self.assertRaises(ValueError):
                    runner.admit_artifact(root, target, cargo_stdout(value), execution())

    def test_symlink_hardlink_outside_target_and_predating_binary_are_refused(self):
        for kind in ("symlink", "hardlink", "outside", "predating"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                target = root / "build/ci-verification/new/cargo-target"
                path, value = artifact(root, target)
                receipt = execution()
                if kind == "symlink":
                    real = path.with_name("real-binary")
                    path.rename(real)
                    path.symlink_to(real)
                elif kind == "hardlink":
                    os.link(path, path.with_name("aliased-binary"))
                elif kind == "outside":
                    value["executable"] = str(root / "outside/appkit_lifecycle-0123abcd")
                    value["filenames"] = [value["executable"]]
                else:
                    receipt["started_at_ns"] = path.stat().st_mtime_ns + runner.FRESHNESS_SLOP_NS + 1
                with self.assertRaises(ValueError):
                    runner.admit_artifact(root, target, cargo_stdout(value), receipt)


class XmlAndPreservationControls(unittest.TestCase):
    def test_exact_native_xml_and_valid_red_xml_have_distinct_actual_outcomes(self):
        for case in runner.CASES:
            with self.subTest(case=case):
                self.assertEqual("passed", runner.read_xml(xml(case), case)["status"])
                self.assertEqual("failed", runner.read_xml(xml(case, failed=True), case)["status"])

    def test_foreign_duplicate_skip_dtd_bad_cleanup_and_missing_counts_are_never_passes(self):
        case = runner.CASES[0]
        good = xml(case)
        variants = [good.replace(case.encode(), b"stress_2048"), good.replace(runner.CLASS.encode(), b"Other"),
                    good.replace(b'errors="0"', b'errors="1"'), good.replace(b' skipped="0"', b""),
                    good.replace(b"<system-out>", b"<skipped/><system-out>"),
                    good.replace(b"cleanup=true", b"cleanup=false"), good.replace(b"live=0", b"live=1"),
                    good.replace(b'time="0.000001"', b'time="NaN"'),
                    good.replace(b'<?xml version="1.0" encoding="UTF-8"?>', b'<!DOCTYPE testsuite [<!ENTITY a "bad">]>')]
        for payload in variants:
            with self.subTest(payload=payload[:70]), self.assertRaises(ValueError):
                runner.read_xml(payload, case)

    def test_complete_default_population_copies_only_exact_original_xml_and_preserves_old(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            make_reports(root, runner.CASES[:1], pid=1111)
            baseline = runner.report_state(root)
            started = time.time_ns()
            folder = make_reports(root)
            raw = {path.name: path.read_bytes() for path in folder.iterdir()}
            out = root / "build/ci-verification/new"
            out.mkdir()
            result = runner.collect_reports(root, out, execution(started=started), baseline, markers())
            self.assertTrue(result["passed"])
            self.assertEqual(8, result["accepted_xml_cases"])
            self.assertFalse(result["raw_control_flag_independently_observed"])
            self.assertEqual(raw, {path.name: path.read_bytes() for path in (out / "fresh-reports").iterdir()})
            current = runner.report_state(root)
            self.assertEqual(baseline, {key: value for key, value in current.items() if "process-4242" not in key})

    def test_failed_first_case_retains_exact_red_xml_and_does_not_invent_missing_cases(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            started = time.time_ns()
            make_reports(root, runner.CASES[:1], failed=runner.CASES[0])
            out = root / "build/ci-verification/new"
            out.mkdir()
            result = runner.collect_reports(root, out, execution(passed=False, started=started), {},
                                            markers(runner.CASES[:1], passed=False))
            self.assertFalse(result["passed"])
            self.assertEqual(1, result["reached_original_xml"])
            self.assertEqual(0, result["accepted_xml_cases"])
            self.assertEqual([{"classname": runner.CLASS, "name": runner.CASES[0], "status": "failed"}], result["testcases"])
            self.assertEqual(xml(runner.CASES[0], failed=True),
                             (out / "fresh-reports" / ("TEST-" + runner.CASES[0] + ".xml")).read_bytes())
            self.assertIn("native-process-not-accepted", result["errors"])

    def test_duplicate_unknown_reordered_or_nonzero_console_witness_is_red(self):
        for console in (markers() + markers(runner.CASES[:1]), markers(tuple(reversed(runner.CASES))),
                        markers() + markers(("stress_2048",)), markers(live=1), markers(cleanup=False)):
            with self.subTest(console=console[:40]), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                make_reports(root)
                out = root / "build/ci-verification/new"
                out.mkdir()
                result = runner.collect_reports(root, out, execution(), {}, console)
                self.assertFalse(result["passed"])
                self.assertEqual(8, result["reached_original_xml"])

    def test_pid_collision_does_not_copy_or_delete_any_preexisting_report(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            folder = make_reports(root)
            baseline = runner.report_state(root)
            out = root / "build/ci-verification/new"
            out.mkdir()
            result = runner.collect_reports(root, out, execution(), baseline, markers())
            self.assertFalse(result["passed"])
            self.assertEqual(0, result["reached_original_xml"])
            self.assertEqual([], list((out / "fresh-reports").iterdir()))
            self.assertEqual(baseline, runner.report_state(root))
            self.assertEqual(8, len(list(folder.iterdir())))

    def test_changed_nonowned_report_or_unknown_owned_file_is_red_but_preserved(self):
        for kind in ("nonowned", "owned"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                old = make_reports(root, runner.CASES[:1], pid=1111)
                baseline = runner.report_state(root)
                folder = make_reports(root)
                unexpected = (old / "TEST-changed.xml") if kind == "nonowned" else (folder / "unexpected.txt")
                unexpected.write_text("preserved unknown input")
                out = root / "build/ci-verification/new"
                out.mkdir()
                result = runner.collect_reports(root, out, execution(), baseline, markers())
                self.assertFalse(result["passed"])
                self.assertEqual("preserved unknown input", unexpected.read_text())
                self.assertFalse((out / "fresh-reports" / unexpected.name).exists())

    def test_report_symlink_hardlink_and_nonfresh_xml_are_refused(self):
        for kind in ("symlink", "hardlink", "predating"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                folder = make_reports(root)
                path = folder / ("TEST-" + runner.CASES[0] + ".xml")
                if kind == "symlink":
                    original = root / "held-original.xml"
                    path.rename(original)
                    path.symlink_to(original)
                elif kind == "hardlink":
                    os.link(path, root / "held-alias.xml")
                out = root / "build/ci-verification/new"
                out.mkdir()
                if kind == "predating":
                    result = runner.collect_reports(root, out, execution(started=time.time_ns() + runner.FRESHNESS_SLOP_NS),
                                                    {}, markers())
                    self.assertFalse(result["passed"])
                    self.assertEqual(0, result["reached_original_xml"])
                else:
                    with self.assertRaises(ValueError):
                        runner.collect_reports(root, out, execution(), {}, markers())


class OrchestrationControls(unittest.TestCase):
    def modeled_run(self, root, *, mode="success"):
        state = {"library": "a" * 64, "native": "b" * 64, "runtime_calls": 0}
        calls = []

        def runtime(*args):
            state["runtime_calls"] += 1
            return {"host": "actual-model-not-native", "epoch": 2 if mode == "runtime-drift" and
                    state["runtime_calls"] == 3 else 1}

        def logged(root, output, role, command, env, timeout, maximum):
            calls.append((role, command))
            started = time.time_ns()
            if role == "cargo":
                _, value = artifact(root, Path(command[-1]))
                if mode == "source-drift":
                    state["library"] = "c" * 64
                return execution(passed=mode != "compile-failure", started=started), cargo_stdout(value)
            if mode == "native-failure":
                make_reports(root, runner.CASES[:1], failed=runner.CASES[0])
                return execution(passed=False, started=started), markers(runner.CASES[:1], passed=False)
            make_reports(root)
            return execution(started=started), markers()

        with patch.object(runner, "build_environment", return_value={"NATIVECMPKIT_NATIVE_UI_TESTS": "true"}), \
                patch.object(runner, "git_identity", return_value={"source_revision": "d" * 40, "source_tree_dirty": False}), \
                patch.object(runner.library, "snapshot_inputs", side_effect=lambda root: {"source-model": state["library"]}), \
                patch.object(runner.native, "expected_source_files", side_effect=lambda root, module: {"native-model": state["native"]}), \
                patch.object(runner, "runtime_identity", side_effect=runtime), \
                patch.object(runner, "source_contract", return_value={"raw_control_flag_exported": False,
                                                                     "raw_control_flag_independently_observed": False}), \
                patch.object(runner, "logged_execution", side_effect=logged):
            result = runner.run(root, "build/ci-verification/new")
        return result, calls

    def test_source_model_success_compiles_once_then_executes_only_exact_binary_without_args(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result, calls = self.modeled_run(root)
            self.assertTrue(result["passed"])
            self.assertEqual(["cargo", "native"], [role for role, command in calls])
            self.assertEqual(1, len(calls[1][1]))
            self.assertNotIn("--case", " ".join(calls[1][1]))
            self.assertTrue(result["inputs_held"])
            self.assertTrue(result["reports_held"])
            self.assertTrue(result["owned_lock_released"])
            self.assertFalse(result["publication_performed"])
            self.assertFalse(result["release_readiness_verified"])
            self.assertEqual(result, json.loads((root / "build/ci-verification/new/receipt.json").read_text()))

    def test_compile_failure_receipt_persists_and_never_launches_native(self):
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), mode="compile-failure")
            self.assertFalse(result["passed"])
            self.assertEqual(["cargo"], [role for role, command in calls])
            self.assertFalse(result["compilation"]["passed"])
            self.assertNotIn("native_execution", result)
            self.assertTrue(result["inputs_held"])
            self.assertTrue(result["owned_lock_released"])

    def test_native_failure_keeps_reached_xml_and_primary_outcome_after_independent_final_custody(self):
        with tempfile.TemporaryDirectory() as name:
            result, calls = self.modeled_run(Path(name), mode="native-failure")
            self.assertFalse(result["passed"])
            self.assertEqual(["cargo", "native"], [role for role, command in calls])
            self.assertEqual(1, result["native_reports"]["reached_original_xml"])
            self.assertEqual("failed", result["native_reports"]["testcases"][0]["status"])
            self.assertTrue(result["artifact_held"])
            self.assertTrue(result["reports_held"])
            self.assertTrue(result["owned_lock_released"])

    def test_source_drift_stops_before_native_and_final_runtime_drift_keeps_job_red(self):
        for mode in ("source-drift", "runtime-drift"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as name:
                result, calls = self.modeled_run(Path(name), mode=mode)
                self.assertFalse(result["passed"])
                if mode == "source-drift":
                    self.assertEqual(["cargo"], [role for role, command in calls])
                    self.assertIn("complete-library-inputs-changed", result["errors"])
                else:
                    self.assertEqual(["cargo", "native"], [role for role, command in calls])
                    self.assertIn("final-runtime-identity-changed-or-missing", result["errors"])

    def test_preflight_failure_retains_sanitized_primary_and_cleanup_without_starting_native(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with patch.object(runner, "build_environment", side_effect=runner.Refusal("modeled-preflight", {
                    "execution": execution(passed=False), "payload_archived": False})), \
                    patch.object(runner.library, "snapshot_inputs", return_value={"source": "a" * 64}), \
                    patch.object(runner.native, "expected_source_files", return_value={"native": "b" * 64}), \
                    patch.object(runner, "logged_execution", side_effect=AssertionError("no compiler/native")):
                result = runner.run(root, "build/ci-verification/new")
            self.assertFalse(result["passed"])
            self.assertEqual("modeled-preflight", result["errors"][0])
            self.assertFalse(result["refusal_evidence"]["payload_archived"])
            self.assertTrue(result["owned_lock_released"])
            self.assertTrue((root / "build/ci-verification/new/receipt.json").is_file())


if __name__ == "__main__":
    unittest.main()
