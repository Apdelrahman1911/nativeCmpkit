"""Adversarial tooling fixtures, not Apple/UIKit/Worker or library execution.

Small subprocess tests exercise Python's real transport, with explicit simulated
native frames. They do not replace the immutable actual simulator/KGP run.
"""
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ios_ui_application as a

DEVICE = "11111111-1111-1111-1111-111111111111"
ACTIVE = "NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2"
COMPLETE = "NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true"
STARTUP_TIMEOUT = ("NATIVECMPKIT_UIKIT_STARTUP_TIMEOUT active=true key=true hidden=false "
                   "rootAttached=false rootNativeEqual=true workerStarted=false")
SUITE = "com.mohamedrejeb.calf.ui.internal.SyntheticFixture"


def frame(event, **fields):
    def escape(s):
        return s.replace("|", "||").replace("'", "|'").replace("\n", "|n").replace("\r", "|r").replace("[", "|[").replace("]", "|]")
    return "##teamcity[" + event + "".join(" " + k + "='" + escape(v) + "'" for k, v in fields.items()) + "]"


def complete_lines(failed=False):
    lines = [ACTIVE, frame("testSuiteStarted", name=SUITE), frame("testStarted", name="fixture")]
    if failed:
        lines.append(frame("testFailed", name="fixture", message="intentional fixture failure"))
    return lines + [frame("testFinished", name="fixture", duration="1"), frame("testSuiteFinished", name=SUITE), COMPLETE]


def macho(platform=7, cpu=0x0100000C, kind=2):
    command = struct.pack("<6I", 0x32, 24, platform, 15 << 16, 26 << 16, 0)
    return struct.pack("<8I", 0xFEEDFACF, cpu, 0, kind, 1, len(command), 0, 0) + command


class LinkedIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "test.kexe"
        self.path.write_bytes(macho())

    def test_real_header_values_are_read_not_inferred_from_kexe_name(self):
        self.assertEqual({"architecture": "arm64", "file_type": "executable", "platform": 7,
                          "minimum_os": "15.0.0", "sdk": "26.0.0"}, a.macho_simulator_identity(self.path))

    def test_device_macos_wrong_arch_and_framework_headers_are_rejected(self):
        for content in [macho(platform=2), macho(platform=1), macho(cpu=0x01000007), macho(kind=6), b"not an executable" * 3]:
            with self.subTest(content=content[:16]):
                self.path.write_bytes(content)
                with self.assertRaises(ValueError): a.macho_simulator_identity(self.path)

    def test_unbounded_truncated_or_misaligned_load_commands_are_rejected(self):
        for content in [macho()[:40], struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 4097, 24, 0, 0) + macho()[32:],
                        macho()[:36] + struct.pack("<I", 23) + macho()[40:],
                        struct.pack("<8I", 0xFEEDFACF, 0x0100000C, 0, 2, 0, 24, 0, 0) + macho()[32:]]:
            with self.subTest(content=content[:32]):
                self.path.write_bytes(content)
                with self.assertRaises(ValueError): a.macho_simulator_identity(self.path)

    def test_unshared_regular_binary_is_required(self):
        linked = self.path.with_name("hardlink.kexe")
        os.link(self.path, linked)
        with self.assertRaises(ValueError): a.macho_simulator_identity(self.path)
        linked.unlink()
        linked.symlink_to(self.path)
        with self.assertRaises(ValueError): a.macho_simulator_identity(linked)

    def test_minimum_manifest_uses_observed_macho_and_owned_identity(self):
        bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
        info = a.app_information(bundle, "15.0.0")
        self.assertEqual("15.0.0", info["MinimumOSVersion"])
        self.assertEqual([1, 2], info["UIDeviceFamily"])
        self.assertEqual(["iPhoneSimulator"], info["CFBundleSupportedPlatforms"])
        for invalid, minimum in [("foreign.app", "15.0.0"), (bundle, "15.0"), (bundle, "15; unsafe")]:
            with self.assertRaises(ValueError): a.app_information(invalid, minimum)


class ProtocolTests(unittest.TestCase):
    def protocol(self, lines):
        protocol = a.NativeProtocol()
        for line in lines: protocol.feed(line)
        return protocol

    def test_nonzero_actual_case_and_unique_workers_are_required(self):
        result = self.protocol(complete_lines()).finish(0)
        self.assertEqual(1, result["counts"]["executed"])
        self.assertEqual(1, result["counts"]["passed"])
        self.assertEqual({"main_worker": 1, "owned_worker": 2}, result["activation"])

    def test_exact_failed_startup_predicates_are_retained_without_becoming_transport(self):
        protocol = a.NativeProtocol()
        with self.assertRaises(ValueError): protocol.feed(STARTUP_TIMEOUT)
        self.assertEqual({"active": True, "key": True, "hidden": False, "root_attached": False,
                          "root_native_equal": True, "worker_started": False},
                         getattr(protocol, "startup_failure_observation", None))
        self.assertIsNone(protocol.active)
        self.assertEqual({}, protocol.cases)
        with self.assertRaises(ValueError): protocol.feed(ACTIVE)
        with self.assertRaises(ValueError): protocol.finish(0)

    def test_malformed_late_or_untrusted_startup_fields_are_not_retained(self):
        for value in [STARTUP_TIMEOUT + " secret=private", STARTUP_TIMEOUT.replace("active=true", "active=1"),
                      STARTUP_TIMEOUT.replace("workerStarted=false", "workerStarted=true"),
                      STARTUP_TIMEOUT.replace("rootAttached=false", "rootAttached=unknown")]:
            with self.subTest(value=value):
                protocol = a.NativeProtocol()
                with self.assertRaises(ValueError): protocol.feed(value)
                self.assertIsNone(getattr(protocol, "startup_failure_observation", None))
        protocol = a.NativeProtocol(); protocol.feed(ACTIVE)
        with self.assertRaises(ValueError): protocol.feed(STARTUP_TIMEOUT)
        self.assertIsNone(getattr(protocol, "startup_failure_observation", None))

    def test_failed_case_is_preserved_under_kgp_no_exit_code_protocol(self):
        result = self.protocol(complete_lines(True)).finish(0)
        self.assertEqual(1, result["counts"]["failures"])
        self.assertEqual(0, result["counts"]["passed"])
        self.assertEqual("failed", result["testcases"][0]["status"])

    def test_activation_completion_or_worker_identity_is_never_invented(self):
        for lines in [complete_lines()[1:], complete_lines()[:-1], [ACTIVE, COMPLETE],
                      [ACTIVE, ACTIVE], [ACTIVE.replace("ownedWorker=2", "ownedWorker=1")],
                      [ACTIVE, "NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false"]]:
            with self.subTest(lines=lines), self.assertRaises(ValueError):
                self.protocol(lines).finish(0)

    def test_crash_or_nonzero_native_runner_invalidates_completed_cases(self):
        for exit_code in [1, -9, 2]:
            with self.assertRaises(ValueError): self.protocol(complete_lines()).finish(exit_code)
        with self.assertRaises(ValueError):
            self.protocol(complete_lines()[:-1] + [COMPLETE.replace("runnerExit=0", "runnerExit=1")])

    def test_unbalanced_overlapping_duplicate_or_late_cases_are_rejected(self):
        good = complete_lines()
        for lines in [good[:3] + [frame("testStarted", name="other")],
                      good[:4] + [frame("testSuiteFinished", name="wrong")],
                      good[:-2] + [frame("testStarted", name="fixture")],
                      good + [frame("testStarted", name="afterCompletion")],
                      good[:2] + [frame("testFailed", name="noStartedCase")]]:
            with self.subTest(lines=lines), self.assertRaises(ValueError): self.protocol(lines).finish(0)

    def test_ignored_case_is_not_execution_or_an_all_skipped_success(self):
        ignored = [ACTIVE, frame("testSuiteStarted", name=SUITE), frame("testIgnored", name="ignored"),
                   frame("testSuiteFinished", name=SUITE), COMPLETE]
        with self.assertRaises(ValueError): self.protocol(ignored).finish(0)
        mixed = complete_lines()[:-2] + [frame("testIgnored", name="ignored"), *complete_lines()[-2:]]
        result = self.protocol(mixed).finish(0)
        self.assertEqual(1, result["counts"]["skipped"])
        self.assertEqual(1, result["counts"]["executed"])
        self.assertEqual(1, result["counts"]["unexpected_skipped"])

    def test_valid_teamcity_escapes_survive_and_malformed_frames_fail_closed(self):
        kind, values = a.teamcity_fields(frame("message", text="quoted ' pipe | [bracket]\n"))
        self.assertEqual("message", kind)
        self.assertEqual("quoted ' pipe | [bracket]\n", values["text"])
        for line in ["##teamcity[testStarted name='a' name='b']", "##teamcity[testStarted name='bad|x']",
                     "##teamcity[testStarted name='unterminated]", "##teamcity[unknown value=unsafe]"]:
            with self.assertRaises(ValueError): a.teamcity_fields(line)

    def test_stream_and_individual_line_bounds_are_enforced(self):
        with patch.object(a, "MAX_LINE_BYTES", 8), self.assertRaises(ValueError): self.protocol([ACTIVE])
        with patch.object(a, "MAX_STREAM_BYTES", 8), self.assertRaises(ValueError): self.protocol(["ordinary output"])


class OwnedApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binary = self.root / a.EXPECTED_BINARY_DIRECTORY / "test.kexe"
        self.binary.parent.mkdir(parents=True)
        self.binary.write_bytes(macho()); self.binary.chmod(0o700)
        self.installed = self.root / "simulator-container/NativeCmpkitLibraryTests.app"
        self.commands = []
        self.before = {"source_revision": "a" * 40, "source_tree_dirty": False,
                       "simulator": {"udid": DEVICE, "state": "Booted", "runtime_version": "26.0"}}
        for obj, name, value in [(a.lt, "ROOT", self.root), (a.platform, "system", lambda: "Darwin"),
                                 (a.platform, "machine", lambda: "arm64")]:
            patcher = patch.object(obj, name, value); patcher.start(); self.addCleanup(patcher.stop)
        patcher = patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_SIMULATOR": DEVICE,
                                         "NATIVECMPKIT_UIKIT_RESULT_ROOT": "build/ci-verification/fixture/native-application"})
        patcher.start(); self.addCleanup(patcher.stop)

    def control(self, argv, timeout=90):
        self.commands.append(argv)
        if "get_app_container" in argv:
            if self.installed.exists(): return subprocess.CompletedProcess(argv, 0, str(self.installed).encode(), b"")
            return subprocess.CompletedProcess(argv, 2, b"", b"An error (domain=NSPOSIXErrorDomain, code=2): No such file or directory")
        if argv[0] == "/usr/bin/codesign":
            executable = Path(argv[-1]) / a.APP_EXECUTABLE
            executable.write_bytes(executable.read_bytes() + b"synthetic-signature")
        if "install" in argv:
            self.installed.parent.mkdir(parents=True)
            shutil.copytree(Path(argv[-1]), self.installed)
        if "uninstall" in argv: shutil.rmtree(self.installed)
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    def launch(self, argv, protocol):
        self.commands.append(argv)
        for line in complete_lines(): protocol.feed(line)
        return {"process_exit": 0, **protocol.finish(0)}

    def fixture_run(self, control=None, contexts=None, launch=None, arguments=None):
        with patch.object(a.runtime, "capture", side_effect=contexts or [self.before, self.before]), \
                patch.object(a, "execute_control", side_effect=control or self.control), \
                patch.object(a, "forward_application", side_effect=launch or self.launch), \
                patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)):
            # Explicit synthetic capacity isolates these ownership contracts from
            # the host's shared /tmp reserve. The production reserve is tested
            # independently below; no real app/build is staged by these fixtures.
            return a.run(self.binary.relative_to(self.root).as_posix(), arguments or list(a.TEST_ARGUMENTS))

    def test_owned_staging_reserve_guard_still_refuses_install(self):
        with patch.object(a.runtime, "capture", return_value=self.before), \
                patch.object(a, "execute_control", side_effect=self.control), \
                patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=0)):
            result = a.run(self.binary.relative_to(self.root).as_posix(), list(a.TEST_ARGUMENTS))
        self.assertFalse(result["transport_passed"])
        self.assertEqual("local-bundle", result["error"]["phase"])
        self.assertFalse(any("install" in cmd or "launch" in cmd for cmd in self.commands))

    def test_owned_only_install_launch_readback_uninstall_and_local_cleanup(self):
        result = self.fixture_run()
        self.assertTrue(result["transport_passed"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
        self.assertTrue(result["cleanup"]["owned_app_identity_reverified"])
        self.assertFalse(self.installed.exists())
        self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
        self.assertFalse(result["packages_published"])
        self.assertEqual(self.binary.read_bytes(), macho())
        self.assertEqual({DEVICE}, {cmd[3] for cmd in self.commands if len(cmd) > 3 and cmd[2] in {"install", "uninstall", "terminate", "get_app_container"}})

    def test_foreign_or_unknown_absence_check_is_never_overwritten_or_cleaned(self):
        for code, stderr in [(0, b""), (2, b"unknown domain"), (149, b"service unavailable")]:
            with self.subTest(code=code):
                self.commands.clear()
                def control(argv, timeout=90):
                    self.commands.append(argv); return subprocess.CompletedProcess(argv, code, b"", stderr)
                result = self.fixture_run(control=control, contexts=[self.before])
                self.assertFalse(result["transport_passed"])
                self.assertEqual("foreign-app-preflight", result["error"]["phase"])
                self.assertEqual(1, len(self.commands))

    def test_control_diagnostics_keep_only_bounded_error_domain_code_not_transcripts(self):
        result = subprocess.CompletedProcess([], 149, b"private stdout", b"secret transcript\nAn error (domain=NSPOSIXErrorDomain, code=2)\nprivate path")
        status = a.control_status(result)
        self.assertEqual(149, status["exit_code"])
        self.assertEqual([{ "domain": "NSPOSIXErrorDomain", "code": 2}], status["error_identities"])
        self.assertNotIn("private", json.dumps(status)); self.assertNotIn("secret", json.dumps(status))

    def test_completed_app_known_not_running_error_is_observed_not_ignored(self):
        def control(argv, timeout=90):
            result = self.control(argv, timeout)
            if "terminate" in argv:
                return subprocess.CompletedProcess(argv, 3, b"", b"An error (domain=NSPOSIXErrorDomain, code=3): Application not running")
            return result
        result = self.fixture_run(control=control)
        self.assertTrue(result["transport_passed"])
        self.assertTrue(result["cleanup"]["owned_app_stopped_verified"])
        self.assertEqual(3, result["cleanup"]["terminate_exit_code"])

    def test_unknown_terminate_error_fails_but_still_uninstalls_only_our_owned_app(self):
        def control(argv, timeout=90):
            result = self.control(argv, timeout)
            if "terminate" in argv:
                return subprocess.CompletedProcess(argv, 149, b"", b"service unavailable")
            return result
        result = self.fixture_run(control=control)
        self.assertFalse(result["transport_passed"])
        self.assertFalse(result["cleanup"]["owned_app_stopped_verified"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
        self.assertFalse(self.installed.exists())

    def test_unknown_install_failure_is_reconciled_without_blind_retry(self):
        def control(argv, timeout=90):
            result = self.control(argv, timeout)
            return subprocess.CompletedProcess(argv, 1, b"", b"uncertain installation") if "install" in argv else result
        result = self.fixture_run(control=control, contexts=[self.before])
        self.assertFalse(result["transport_passed"])
        self.assertTrue(result["steps"]["install-owned-app"]["installed_owned_bytes_verified"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
        self.assertEqual(1, sum("install" in cmd for cmd in self.commands))
        self.assertFalse(any("launch" in cmd for cmd in self.commands))

    def test_changed_installed_bytes_are_not_treated_as_owned_cleanup(self):
        def launch(argv, protocol):
            result = self.launch(argv, protocol)
            (self.installed / a.APP_EXECUTABLE).write_bytes(b"foreign replacement")
            return result
        result = self.fixture_run(launch=launch)
        self.assertFalse(result["transport_passed"])
        self.assertFalse(result["cleanup"]["owned_app_identity_reverified"])
        self.assertTrue(self.installed.exists())
        self.assertFalse(any("uninstall" in cmd or "terminate" in cmd for cmd in self.commands))

    def test_application_or_source_identity_change_invalidates_otherwise_valid_cases(self):
        changed = {**self.before, "source_revision": "b" * 40}
        result = self.fixture_run(contexts=[self.before, changed])
        self.assertFalse(result["transport_passed"])
        self.assertEqual("post-runtime-and-binary", result["error"]["phase"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])

    def test_crash_timeout_and_transport_error_still_clean_only_the_owned_app(self):
        def launch(argv, protocol): raise TimeoutError("synthetic transport hang")
        result = self.fixture_run(contexts=[self.before], launch=launch)
        self.assertFalse(result["transport_passed"])
        self.assertEqual("TimeoutError", result["error"]["type"])
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])

    def test_startup_failure_receipt_retains_only_booleans_and_owned_cleanup(self):
        def launch(argv, protocol): protocol.feed(STARTUP_TIMEOUT)
        result = self.fixture_run(contexts=[self.before], launch=launch)
        self.assertFalse(result["transport_passed"])
        self.assertIsNone(result["application_protocol"])
        self.assertEqual("launch-and-real-test-transport", result["error"]["phase"])
        self.assertEqual({"active": True, "key": True, "hidden": False, "root_attached": False,
                          "root_native_equal": True, "worker_started": False},
                         result.get("startup_failure_observation"))
        self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
        self.assertFalse(self.installed.exists())

    def test_non_apple_or_wrong_arch_filtered_args_and_guessed_device_are_refused(self):
        with patch.object(a.platform, "system", return_value="Linux"), self.assertRaises(ValueError): self.fixture_run()
        with patch.object(a.platform, "machine", return_value="x86_64"), self.assertRaises(ValueError): self.fixture_run()
        for arguments in [list(a.TEST_ARGUMENTS) + ["--ktest_filter=someCase"], ["--ktest_no_exit_code"]]:
            with self.assertRaises(ValueError): self.fixture_run(arguments=arguments)
        with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_SIMULATOR": "booted"}), self.assertRaises(ValueError): self.fixture_run()
        self.assertEqual([], self.commands)

    def test_receipt_path_binary_traversal_and_symlink_interlock_precede_install(self):
        with patch.dict(os.environ, {"NATIVECMPKIT_UIKIT_RESULT_ROOT": "../foreign"}), self.assertRaises(ValueError): self.fixture_run()
        with self.assertRaises(ValueError): a.run("../outside/test.kexe", list(a.TEST_ARGUMENTS))
        original = self.binary.with_suffix(".original"); self.binary.rename(original); self.binary.symlink_to(original)
        with self.assertRaises(ValueError): self.fixture_run()
        self.assertEqual([], self.commands)


class RealPythonTransportTests(unittest.TestCase):
    """Actual owned Python child/pipes, but *simulated* native lifecycle frames."""
    def transport(self, lines, suffix="", timeout=5):
        out = SimpleNamespace(buffer=io.BytesIO())
        code = "import sys,time\n" + "\n".join("print(" + repr(line) + ",flush=True)" for line in lines) + "\n" + suffix
        with tempfile.TemporaryDirectory() as directory, patch.object(a.lt, "ROOT", Path(directory)), \
                patch.object(a.sys, "stdout", out), patch.object(a.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)):
            result = a.forward_application([sys.executable, "-u", "-c", code], a.NativeProtocol(), timeout)
        return result, out.buffer.getvalue()

    def test_real_pipe_preserves_teamcity_frames_and_failure_with_exit_zero(self):
        for failed in [False, True]:
            result, payload = self.transport(complete_lines(failed))
            self.assertEqual(1, result["counts"]["executed"])
            self.assertEqual(int(failed), result["counts"]["failures"])
            self.assertEqual(("\n".join(complete_lines(failed)) + "\n").encode(), payload)

    def test_real_nonzero_child_missing_completion_and_timeout_fail_closed(self):
        for lines, suffix, timeout in [(complete_lines(), "sys.exit(3)", 5),
                                      (complete_lines()[:-1], "", 5), ([ACTIVE], "time.sleep(60)", 1)]:
            with self.subTest(suffix=suffix), self.assertRaises((ValueError, TimeoutError)):
                self.transport(lines, suffix, timeout)


if __name__ == "__main__":
    unittest.main()
