"""Synthetic finite-selection guards; these do not execute Android library tests."""
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


class AndroidSaveIdentityFocus(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-file-picker",\n)\n')
        self.write("calf-file-picker/build.gradle.kts", "// synthetic, never built\n")
        self.write("calf-file-picker/src/commonTest/Unrelated.kt", "// retained, not selected\n")
        for group in r.ANDROID_SAVE_IDENTITY_GROUPS:
            package, name = group["classname"].rsplit(".", 1)
            self.write(group["source"], "package " + package + "\nclass " + name + " {\n" +
                       "\n".join("@Test fun " + method + "() {}" for method in group["declared_methods"]) + "\n}\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def plan(self):
        return r.plan(self.root, "android-device", only_modules=("calf-file-picker",),
                      focus=r.ANDROID_SAVE_IDENTITY_FOCUS)

    def collect(self, cases=None, marker=1, age=0):
        cases = r.android_save_identity_identities() if cases is None else cases
        plan = self.plan()
        body = ""
        for case in cases:
            status = {"passed": "", "failure": "<failure/>", "error": "<error/>", "skipped": "<skipped/>"}[
                case.get("status", "passed")]
            body += '<testcase classname="' + case["classname"] + '" name="' + case["name"] + '">' + status + '</testcase>'
        self.write(plan["expected"][0]["report_directory"] + "/TEST-identity.xml", "<testsuite>" + body + "</testsuite>")
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000 + age, now + 1_000_000_000 + age,
                                 Counter({plan["expected"][0]["task"]: marker}))

    def test_exact_ten_native_methods_retain_all_twenty_one_declarations_and_incomplete_scope(self):
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(10, len(item["required_testcases"]))
        self.assertEqual(21, sum(len(g["declared_methods"]) for g in r.ANDROID_SAVE_IDENTITY_GROUPS))
        self.assertEqual(r.android_save_identity_filter(), item["test_filter"])
        self.assertIn("original hardlink", plan["scope"])
        for group in r.ANDROID_SAVE_IDENTITY_GROUPS:
            self.assertIn(group["source"], item["test_source_files"])

    def test_profile_cli_and_runner_use_only_the_supported_canonical_class_method_list(self):
        row, = matrix.matrix("android-saver-identity")["include"]
        self.assertEqual(("android-device-api35", "calf-file-picker", r.ANDROID_SAVE_IDENTITY_FOCUS),
                         (row["slot"], row["test-modules"], row["test-focus"]))
        result = subprocess.run([sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "android-device", "--module", "calf-file-picker", "--focus", r.ANDROID_SAVE_IDENTITY_FOCUS],
                                cwd=r.ROOT, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        command = r.gradle_command("android-device", self.plan(), root=self.root, android_serial="emulator-5554")
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.class=" + r.android_save_identity_filter()],
                         [a for a in command if a.startswith("-Pandroid.testInstrumentationRunnerArguments.class=")])
        self.assertNotIn("--tests", command)
        self.assertNotIn("*", r.android_save_identity_filter())
        self.assertEqual(":calf-file-picker:connectedAndroidDeviceTest", command[-1])

    def test_foreign_suite_module_wildcard_and_duplicate_module_are_rejected(self):
        for suite, modules, focus in (("desktop", ("calf-file-picker",), r.ANDROID_SAVE_IDENTITY_FOCUS),
                                     ("android-device", ("calf-io",), r.ANDROID_SAVE_IDENTITY_FOCUS),
                                     ("android-device", ("calf-file-picker", "calf-io"), r.ANDROID_SAVE_IDENTITY_FOCUS),
                                     ("android-device", ("calf-file-picker", "calf-file-picker"), r.ANDROID_SAVE_IDENTITY_FOCUS),
                                     ("android-device", ("calf-file-picker",), "save-device-*")):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)

    def test_changed_deleted_or_extra_declared_native_method_requires_review(self):
        group = r.ANDROID_SAVE_IDENTITY_GROUPS[0]
        original = (self.root / group["source"]).read_text()
        for changed in (original.replace("actualHardLinkIsNotTruncatedOrDeleted", "different"),
                        original.replace("\n}", "\n@Test fun extra() {}\n}"),
                        original.replace(group["methods"][0], "different")):
            self.write(group["source"], changed)
            with self.assertRaises(ValueError):
                self.plan()
        self.write(group["source"], original)

    def test_tampered_plan_cannot_broaden_narrow_or_escape_the_native_module(self):
        plan = self.plan()
        for key, value in (("required_testcases", []), ("test_filter", "com.mohamedrejeb.calf.picker.*"),
                           ("test_source_files", []), ("module", "calf-io"), ("task", ":calf-file-picker:testAndroidHostTest")):
            changed = deepcopy(plan)
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(changed)
        changed = deepcopy(plan)
        changed["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            r.validate_test_focus(changed)

    def test_exact_fresh_nonzero_execution_and_both_native_source_identities_are_required(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(10, result["totals"]["passed"])
        self.assertEqual({g["source"] for g in r.ANDROID_SAVE_IDENTITY_GROUPS},
                         {c["source"] for c in result["modules"][0]["native_scenarios"]})
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(age=10_000_000_000)["errors"])

    def test_missing_extra_duplicate_foreign_failed_and_skipped_xml_never_pass(self):
        cases = r.android_save_identity_identities()
        group = r.ANDROID_SAVE_IDENTITY_GROUPS[0]
        extra = {"classname": group["classname"], "name": "actualHardLinkIsNotTruncatedOrDeleted"}
        for changed in ([], cases[:-1], cases + [cases[0]], cases + [extra],
                        [dict(cases[0], classname="foreign.IdentityTest"), *cases[1:]],
                        *([dict(cases[0], status=s), *cases[1:]] for s in ("failure", "error", "skipped"))):
            with self.subTest(cases=changed):
                self.assertTrue(self.collect(changed)["errors"])

    def test_controller_preflight_and_full_profiles_keep_enforcing_hardlink_gate(self):
        with patch.object(device, "require_host", side_effect=RuntimeError("synthetic stop")) as guard:
            with self.assertRaises(ValueError):
                device.run(self.root, "build/ci-verification/synthetic", only_modules=("calf-io",), focus=r.ANDROID_SAVE_IDENTITY_FOCUS)
            guard.assert_not_called()
            with self.assertRaisesRegex(RuntimeError, "synthetic stop"):
                device.run(self.root, "build/ci-verification/synthetic", only_modules=("calf-file-picker",), focus=r.ANDROID_SAVE_IDENTITY_FOCUS)
            guard.assert_called_once()
        for profile in ("all", "android-device", "android-webview"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))
        full = r.plan(self.root, "android-device", only_modules=("calf-file-picker",))
        self.assertFalse(r.validate_test_focus(full))
        source = (r.ROOT / r.ANDROID_SAVE_IDENTITY_GROUPS[0]["source"]).read_text()
        self.assertIn("Os.link(source.path, alias.path)", source)
        self.assertIn("assertTrue(first.st_nlink >= 2)", source)
        controller = (r.ROOT / "scripts/ci/android_device_tests.py").read_text()
        self.assertNotIn("setenforce", controller)
        self.assertIn('"getenforce"', controller)


if __name__ == "__main__":
    unittest.main()
