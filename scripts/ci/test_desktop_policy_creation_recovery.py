# SPDX-License-Identifier: Apache-2.0
"""Only NEW source/selection/receipt regressions; zero native/build executions.

The two original macOS methods remain the required runtime witness. No accepted
TLS/cookie/media/request/Stop method is selected by this failed-only recovery.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import android_external328_source_projection as external
import arm64_stop_candidate_source_projection as arm
import desktop_policy_creation_source_projection as history
import desktop_security_plan as security
import library_tests as library
import workflow_matrix as matrix

ROOT = library.ROOT
FOCUS = security.POLICY_RECOVERY_FOCUS
PROFILE = security.POLICY_RECOVERY_PROFILE
POLICY = security.SOURCE_PATHS["policy"]
READY = ('            // A fresh isolated worker must await genuine public onCreated, not test order.\n'
         '            host.awaitCreation(owner)\n')


class DesktopPolicyCreationRecoveryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = library.snapshot_inputs(ROOT)
        cls.bindings = history._bindings()
        cls.current = {path: (ROOT / path).read_bytes() for path in cls.bindings}

    @classmethod
    def tearDownClass(cls):
        if cls.inputs != library.snapshot_inputs(ROOT):
            raise AssertionError("The held source inputs changed during NEW controls")

    def plan(self):
        return library.plan(ROOT, "desktop", only_modules=("calf-webview",), focus=FOCUS)

    def test_only_missing_creation_wait_changes_the_original_native_policy_body(self):
        source = self.current[POLICY].decode()
        previous = history.source_before_policy_creation(POLICY, self.current[POLICY]).decode()
        self.assertEqual(previous, source.replace(READY, "", 1))
        self.assertEqual(1, source.count(READY))
        body = source.split("@Test fun " + security.POLICY_METHOD, 1)[1].split("private suspend fun evaluate", 1)[0]
        self.assertLess(body.index("        try {"), body.index("host.awaitCreation(owner)"))
        self.assertLess(body.index("host.awaitCreation(owner)"), body.index('host.awaitDocument(owner, "javascript")'))
        self.assertIn("while (created.none { it.state === state })", source)
        self.assertIn("failure.get()?.let { throw it }; delay(10)", source)
        self.assertIn("suspend fun awaitCreation(state: WebViewState) = withTimeout(20_000)", source)
        self.assertNotIn("Platform.startup(", source)
        self.assertEqual(hashlib.sha256(self.current[POLICY]).hexdigest(), security.SOURCE_SHA256[POLICY])

    def test_seven_exact_source_inverses_restore_every_old_pin_and_forward_byte(self):
        self.assertEqual(7, len(self.bindings))
        self.assertEqual(18, sum(len(b["fragments"]) for b in self.bindings.values()))
        for path, binding in self.bindings.items():
            with self.subTest(path=path):
                current = self.current[path]
                previous = history.current_source_before_policy_creation(path, current)
                self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
                self.assertEqual(binding["after_sha256"], hashlib.sha256(current).hexdigest())
                self.assertEqual(previous, history.source_before_policy_creation(path, previous))
                forward = previous
                for fragment in binding["fragments"]:
                    before, after = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(1, forward.count(before))
                    forward = forward.replace(before, after, 1)
                self.assertEqual(current, forward)

    def test_current_admission_never_accepts_old_changed_truncated_or_foreign_bytes(self):
        for path, current in self.current.items():
            previous = history.source_before_policy_creation(path, current)
            for candidate in (previous, current[:-1], current + b"\n", b"foreign", b""):
                with self.subTest(path=path, bytes=len(candidate)), self.assertRaises(ValueError):
                    history.current_source_before_policy_creation(path, candidate)
            for candidate in (current[:-1], current + b"\n", b"foreign", b""):
                with self.subTest(path=path, bytes=len(candidate)), self.assertRaises(ValueError):
                    history.source_before_policy_creation(path, candidate)
        for value in (None, bytearray(self.current[POLICY]), [], "text"):
            with self.subTest(kind=type(value).__name__), self.assertRaises(ValueError):
                history.current_source_before_policy_creation(POLICY, value)
        with self.assertRaises(ValueError):
            history.source_before_policy_creation(POLICY, b"x" * (history.MAX_SOURCE_BYTES + 1))

    def test_existing_arm_external_and_tls_history_readers_compose_without_repinning(self):
        for path, binding in external._bindings().items():
            raw = (ROOT / path).read_bytes()
            prior = external.current_source_for_history(path, raw)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(prior).hexdigest())
        for path, binding in arm._bindings().items():
            before = external.current_source_for_history(path, (ROOT / path).read_bytes())
            # The older complete ARM preimage must retain its original idempotence.
            pre_arm = arm.source_before_arm64_stop_candidate(
                path, history.current_source_before_policy_creation(path, (ROOT / path).read_bytes()))
            self.assertEqual(binding["before_sha256"], hashlib.sha256(pre_arm).hexdigest())
            self.assertEqual(pre_arm, arm.source_before_arm64_stop_candidate(path, pre_arm))
            self.assertTrue(before)
        from test_desktop_tls_finished_write_recovery import source_contract
        self.assertEqual(3, len(source_contract()))  # Changed owning default reader only, no old test method.
        from test_ci224_shared_source_composition import CI224SharedSourceCompositionTests
        CI224SharedSourceCompositionTests.setUpClass()  # Source boundary only, no accepted method replay.
        CI224SharedSourceCompositionTests.tearDownClass()

    def test_failed_only_plan_has_one_original_policy_method_and_no_tls_helper(self):
        plan = self.plan()
        item, = plan["expected"]
        self.assertEqual("desktop", plan["suite"])
        self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual([{"classname": security.POLICY_CLASS, "name": security.POLICY_METHOD + "[desktop]"}], item["required_testcases"])
        self.assertEqual(1, item["required_original_xml"])
        self.assertEqual([POLICY], item["test_source_files"])
        self.assertEqual({POLICY: security.SOURCE_SHA256[POLICY]}, item["test_source_sha256"])
        self.assertTrue(library.validate_test_focus(plan))

    def test_command_and_host_admission_select_only_the_two_failed_mac_os_methods(self):
        for system, arch in (("Darwin", "arm64"), ("Darwin", "x86_64")):
            with self.subTest(system=system, arch=arch), patch("library_tests.platform.system", return_value=system), patch("library_tests.platform.machine", return_value=arch):
                security.validate_host(system, arch, FOCUS)
                command = library.gradle_command("desktop", self.plan(), root=ROOT)
                selectors = [command[i + 1] for i, arg in enumerate(command) if arg == "--tests"]
                self.assertEqual([security.POLICY_CLASS + "." + security.POLICY_METHOD], selectors)
                self.assertEqual(1, command.count(security.INIT_SCRIPT))
                self.assertEqual(1, command.count("-PnativecmpkitDesktopSecurityFocus=" + FOCUS))
                self.assertEqual(1, command.count(":calf-webview:desktopTest"))
                self.assertIn("scripts/ci/fresh-tests.init.gradle.kts", command)
        for system, arch in (("Linux", "x86_64"), ("Linux", "aarch64"), ("Windows", "AMD64"), ("Darwin", "other"), (None, "arm64")):
            with self.subTest(system=system, arch=arch), self.assertRaises(ValueError):
                security.validate_host(system, arch, FOCUS)

    def test_matrix_inherits_only_original_mac_rows_and_graph_capture_is_not_replayed(self):
        original = matrix.matrix("webview-desktop-security-macos-pair")["include"]
        recovery = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["desktop-macos-arm64", "desktop-macos-x64"], [r["slot"] for r in recovery])
        self.assertEqual([dict(r, **{"test-focus": FOCUS}) for r in original], recovery)
        before = history.current_source_before_policy_creation(".github/workflows/gradle.yml", self.current[".github/workflows/gradle.yml"]).decode()
        after = self.current[".github/workflows/gradle.yml"].decode()
        self.assertEqual(before, after.replace("webview-desktop-policy-macos-recovery, ", "", 1))
        capture_if = next(line for line in after.splitlines() if "steps.plan.outcome == 'success'" in line and "webview-desktop-security-regressions" in line)
        self.assertNotIn(PROFILE, capture_if)
        self.assertIn("permissions:\n  contents: read", after)

    def test_recovery_rejects_host_module_plan_and_source_broadening(self):
        for changed in (("desktop-windows-x64",), ("desktop-macos-arm64",), ("desktop-macos-arm64", "desktop-macos-x64", "desktop-linux-x64")):
            with self.subTest(slots=changed), patch.dict(matrix.PROFILES, {PROFILE: changed}), self.assertRaises(ValueError):
                matrix.matrix(PROFILE)
        with patch.dict(matrix.MODULE_SUBSETS, {PROFILE: "calf-io"}), self.assertRaises(ValueError):
            matrix.matrix(PROFILE)
        for key, value in (("module", "calf-io"), ("task", ":calf-webview:publish"), ("test_filter", "*"), ("required_original_xml", 2), ("test_source_sha256", {})):
            plan = copy.deepcopy(self.plan()); plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                library.validate_test_focus(plan)

    def collect(self, outcome="", classname=None, method=None, extra=False, markers=1, stale=False):
        plan = self.plan()
        with tempfile.TemporaryDirectory(prefix="explicitly-synthetic-policy-recovery-") as folder:
            root = Path(folder)
            file = root / plan["expected"][0]["report_directory"] / "TEST-explicitly-synthetic-policy.xml"
            file.parent.mkdir(parents=True)
            suite = ET.Element("testsuite")
            case = ET.SubElement(suite, "testcase", classname=classname or security.POLICY_CLASS, name=method or security.POLICY_METHOD + "[desktop]")
            if outcome:
                ET.SubElement(case, outcome)
            if extra:
                ET.SubElement(suite, "testcase", classname=security.COOKIE_CLASS, name=security.COOKIE_METHOD + "[desktop]")
            file.write_bytes(ET.tostring(suite))
            now = time.time_ns()
            if stale:
                import os
                os.utime(file, ns=(now - 20_000_000_000, now - 20_000_000_000))
            return library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                           Counter({":calf-webview:desktopTest": markers}), host_system="Darwin")

    def test_fresh_exact_one_policy_xml_is_required_and_failures_remain_red(self):
        good = self.collect()
        self.assertFalse(good["errors"])
        self.assertEqual(1, good["totals"]["passed"])
        for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                        {"classname": "Foreign.Test"}, {"method": "acceptedDifferentMethod[desktop]"},
                        {"extra": True}, {"markers": 0}, {"markers": 2}, {"stale": True}):
            with self.subTest(changed=changed):
                self.assertTrue(self.collect(**changed)["errors"])

    def test_original_strict_public_worker_parser_is_retained_for_policy_recovery(self):
        prefix = "NATIVECMPKIT_DESKTOP_SECURITY_"
        lines = [prefix + "SETUP task=:calf-webview:desktopTest focus=" + FOCUS + " forks=1 forkEvery=1 classes=1",
                 prefix + "WORKER phase=start worker=7",
                 prefix + "CASE phase=start worker=7 classname=" + security.POLICY_CLASS,
                 prefix + "CASE phase=finish worker=7 classname=" + security.POLICY_CLASS + " tests=1 passed=1 failed=0 skipped=0 result=SUCCESS",
                 prefix + "WORKER phase=finish worker=7 tests=1 passed=1 failed=0 skipped=0 result=SUCCESS"]
        with tempfile.TemporaryDirectory(prefix="explicitly-synthetic-policy-worker-") as folder:
            file = Path(folder) / "synthetic-events.log"
            file.write_text("\n".join(lines) + "\n")
            observed = security.worker_observation(file, FOCUS)
            self.assertEqual(1, len(observed["selected_class_workers"]))
            self.assertFalse(observed["os_worker_pid_observed"])
            for bad in (lines[:-1], lines + [lines[-1]], [l.replace("passed=1 failed=0", "passed=0 failed=1") for l in lines],
                        [l.replace("forkEvery=1", "forkEvery=0") for l in lines], [lines[0], lines[2], lines[1], *lines[3:]]):
                file.write_text("\n".join(bad) + "\n")
                with self.assertRaises(ValueError):
                    security.worker_observation(file, FOCUS)

    def test_unchanged_windows_linux_security_sources_admit_the_same_readiness_repair(self):
        for system, arch, focus, count in (("Windows", "AMD64", "tls-rendering-cookies-policy", 3),
                                         ("Linux", "aarch64", "tls-rendering-cookies-policy-media", 4)):
            security.validate_host(system, arch, focus)
            plan = library.plan(ROOT, "desktop", only_modules=("calf-webview",), focus=focus)
            self.assertEqual(count, len(plan["expected"][0]["required_testcases"]))
            self.assertEqual(security.SOURCE_SHA256[POLICY], plan["expected"][0]["test_source_sha256"][POLICY])
            self.assertEqual(1, plan["desktop_security_fixture"]["max_parallel_forks"])
            self.assertEqual(1, plan["desktop_security_fixture"]["fork_every"])

    def test_tls_class_source_setup_admits_current_bytes_and_restores_all_old_pins(self):
        import test_desktop_tls_finished_write_recovery as tls
        tls.DesktopTlsFinishedWriteRecoveryModels.setUpClass()
        sources = tls.DesktopTlsFinishedWriteRecoveryModels.sources
        self.assertEqual(set(tls.FILE_HASHES), set(sources))
        for path, value in sources.items():
            self.assertEqual(tls.FILE_HASHES[path]["after_sha256"], hashlib.sha256(value.encode()).hexdigest())
        self.assertEqual(3, len(tls.DesktopTlsFinishedWriteRecoveryModels.originals))

    def test_tls_class_source_setup_refuses_old_foreign_truncated_and_appended_plans(self):
        import test_desktop_tls_finished_write_recovery as tls
        current = self.current[tls.PLAN]
        old = history.source_before_policy_creation(tls.PLAN, current)
        for candidate in (old, current[:-1], current + b"\n", b"foreign", b""):
            with self.subTest(bytes=len(candidate)), tempfile.TemporaryDirectory(prefix="explicitly-synthetic-tls-boundary-") as folder:
                root = Path(folder)
                for path in tls.FILE_HASHES:
                    target = root / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((ROOT / path).read_bytes())
                (root / tls.PLAN).write_bytes(candidate)
                with patch.object(tls, "ROOT", root), self.assertRaises(ValueError):
                    tls.DesktopTlsFinishedWriteRecoveryModels.setUpClass()


if __name__ == "__main__":
    unittest.main()
