"""Synthetic finite device-selection guards, not Android library executions."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import android_device_tests as device
import library_tests as r
import workflow_matrix as matrix


class AndroidIoOversizeFocus(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-io",\n)\n')
        self.write("calf-io/build.gradle.kts", "// synthetic build, never executed\n")
        self.write("calf-io/src/commonTest/kotlin/Unrelated.kt", "// retained, not requested\n")
        self.source = "package com.mohamedrejeb.calf.io\nclass KmpFileDeviceTest {\n" + \
            "\n".join("@Test fun " + method + "() {}" for method in r.ANDROID_IO_DEVICE_METHODS) + "\n}\n"
        self.write(r.ANDROID_IO_DEVICE_SOURCE, self.source)

    def write(self, name, payload):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload)

    def plan(self):
        return r.plan(self.root, "android-device", only_modules=("calf-io",),
                      focus=r.ANDROID_IO_OVERSIZE_FOCUS)

    def collect(self, cases=None, marker=1, age=0):
        cases = r.android_io_oversize_identities() if cases is None else cases
        plan = self.plan()
        body = ""
        for case in cases:
            status = {"passed": "", "failure": "<failure/>", "error": "<error/>", "skipped": "<skipped/>"}[
                case.get("status", "passed")]
            body += '<testcase classname="' + case["classname"] + '" name="' + case["name"] + '">' + status + '</testcase>'
        name = plan["expected"][0]["report_directory"] + "/TEST-io.xml"
        self.write(name, "<testsuite>" + body + "</testsuite>")
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000 + age, now + 1_000_000_000 + age,
                                 Counter({plan["expected"][0]["task"]: marker}))

    def test_exact_failed_method_preserves_the_full_declared_inputs_and_incomplete_scope(self):
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(r.ANDROID_IO_DEVICE_CLASS + "#" + r.ANDROID_IO_OVERSIZE_METHOD, item["test_filter"])
        self.assertEqual(r.android_io_oversize_identities(), item["required_testcases"])
        self.assertIn("calf-io/src/commonTest/kotlin/Unrelated.kt", item["test_source_files"])
        self.assertIn(r.ANDROID_IO_DEVICE_SOURCE, item["test_source_files"])
        self.assertEqual("calf-io/build/outputs/androidTest-results/connected/androidMain", item["report_directory"])

    def test_real_profile_and_cli_select_one_method_not_the_twelve_method_class_or_other_modules(self):
        row, = matrix.matrix("android-io-oversize")["include"]
        self.assertEqual(("android-device-api35", "calf-io", r.ANDROID_IO_OVERSIZE_FOCUS),
                         (row["slot"], row["test-modules"], row["test-focus"]))
        result = subprocess.run([sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "android-device", "--module", "calf-io", "--focus", r.ANDROID_IO_OVERSIZE_FOCUS],
                                cwd=r.ROOT, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertIn(r.ANDROID_IO_DEVICE_CLASS + "#" + r.ANDROID_IO_OVERSIZE_METHOD, result.stdout.decode())
        self.assertEqual(1, len(r.plan(r.ROOT, "android-device", only_modules=("calf-io",),
                                     focus=r.ANDROID_IO_OVERSIZE_FOCUS)["expected"][0]["required_testcases"]))

    def test_supported_instrumentation_class_method_argument_has_no_KGP_filter(self):
        command = r.gradle_command("android-device", self.plan(), root=self.root, android_serial="emulator-5554")
        arguments = [arg for arg in command if arg.startswith("-Pandroid.testInstrumentationRunnerArguments.class=")]
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.class=" + r.ANDROID_IO_DEVICE_CLASS + "#" +
                          r.ANDROID_IO_OVERSIZE_METHOD], arguments)
        self.assertNotIn("--tests", command)
        self.assertEqual(":calf-io:connectedAndroidDeviceTest", command[-1])
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.timeout_msec=120000", command)

    def test_unreviewed_module_suite_wildcard_and_duplicate_selection_are_rejected(self):
        for suite, modules, focus in (("desktop", ("calf-io",), r.ANDROID_IO_OVERSIZE_FOCUS),
                                     ("android-device", ("calf-ui",), r.ANDROID_IO_OVERSIZE_FOCUS),
                                     ("android-device", ("calf-io", "calf-ui"), r.ANDROID_IO_OVERSIZE_FOCUS),
                                     ("android-device", ("calf-io", "calf-io"), r.ANDROID_IO_OVERSIZE_FOCUS),
                                     ("android-device", ("calf-io",), "io-device-*")):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)
        with self.assertRaises(ValueError):
            r.gradle_command("android-host", self.plan(), root=self.root)

    def test_changed_declared_inventory_requires_review_without_replaying_passed_cases(self):
        for source in (self.source.replace(r.ANDROID_IO_DEVICE_METHODS[0], "different"),
                       self.source.replace("\n}", "\n@Test fun extra() {}\n}"),
                       self.source.replace(r.ANDROID_IO_OVERSIZE_METHOD, "different")):
            self.write(r.ANDROID_IO_DEVICE_SOURCE, source)
            with self.assertRaises(ValueError):
                self.plan()

    def test_tampered_plan_cannot_execute_an_unrelated_or_full_device_suite(self):
        plan = self.plan()
        for key, value in (("test_filter", r.ANDROID_IO_DEVICE_CLASS), ("required_testcases", []),
                           ("test_source_files", []), ("module", "calf-ui"), ("task", ":calf-io:testAndroidHostTest")):
            changed = deepcopy(plan)
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(changed)
        changed = deepcopy(plan)
        changed["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            r.validate_test_focus(changed)

    def test_exact_one_pass_requires_fresh_XML_and_actual_task_execution(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])
        self.assertEqual(1, result["totals"]["executed"])
        scenario, = result["modules"][0]["native_scenarios"]
        self.assertEqual(r.ANDROID_IO_DEVICE_SOURCE, scenario["source"])
        self.assertEqual("required-executed", scenario["disposition"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(age=10_000_000_000)["errors"])

    def test_missing_extra_duplicate_wrong_target_failure_error_and_skip_do_not_pass(self):
        case, = r.android_io_oversize_identities()
        for cases in ([], [case, case], [case, dict(case, name=r.ANDROID_IO_DEVICE_METHODS[0])],
                      [dict(case, classname="foreign.KmpFileDeviceTest")], [dict(case, name=case["name"] + "[android]")],
                      *([dict(case, status=status)] for status in ("failure", "error", "skipped"))):
            with self.subTest(cases=cases):
                self.assertTrue(self.collect(cases)["errors"])

    def test_controller_requires_the_reviewed_module_before_touching_an_emulator(self):
        with patch.object(device, "require_host", side_effect=RuntimeError("synthetic stop before runtime")) as guard:
            with self.assertRaises(ValueError):
                device.run(self.root, "build/ci-verification/synthetic", only_modules=("calf-ui",),
                           focus=r.ANDROID_IO_OVERSIZE_FOCUS)
            guard.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, "synthetic stop"):
                device.run(self.root, "build/ci-verification/synthetic", only_modules=("calf-io",),
                           focus=r.ANDROID_IO_OVERSIZE_FOCUS)
            guard.assert_called_once()
        result = subprocess.run([sys.executable, str(r.ROOT / "scripts/ci/android_device_tests.py"),
                                 "--output", "build/ci-verification/synthetic", "--api-level", "35",
                                 "--module", "calf-ui", "--focus", r.ANDROID_IO_OVERSIZE_FOCUS], capture_output=True)
        self.assertEqual(2, result.returncode)
        self.assertIn(b"--focus requires its exact reviewed single --module", result.stderr)

    def test_existing_full_profiles_and_original_native_assertions_are_not_weakened(self):
        for profile in ("all", "android-device", "android-webview"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))
        plan = r.plan(self.root, "android-device", only_modules=("calf-io",))
        command = r.gradle_command("android-device", plan, root=self.root, android_serial="emulator-5554")
        self.assertFalse(r.validate_test_focus(plan))
        self.assertFalse(any(arg.startswith("-Pandroid.testInstrumentationRunnerArguments.class=") for arg in command))
        source = (r.ROOT / r.ANDROID_IO_DEVICE_SOURCE).read_text()
        self.assertIn("assertEquals(64L, KmpFile(uri).getSize(context))", source)
        self.assertIn("assertFailsWith<IOException> { KmpFile(uri).readByteArray(context, maxBytes = 63) }", source)
        self.assertIn('assertEquals(0, stats(uri).getInt("opens"))', source)
        self.assertIn("assertEquals(0, openDeviceDescriptorsFor(DeviceDescriptorIdentity.of(file)))", source)


if __name__ == "__main__":
    unittest.main()
