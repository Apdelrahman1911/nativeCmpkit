"""Related picker batch selection/outcome guardrails. Synthetic tooling, not UI tests."""
from collections import Counter
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as r
import native_test_policy as policy
import workflow_matrix as matrix


class PickerBatchFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "desktop", only_modules=("calf-file-picker",), focus=r.PICKER_LIFETIME_FOCUS)

    def cases(self, host="Linux"):
        return [{**case, "status": "passed" if host == "Linux" or index < 3 else "skipped"}
                for index, case in enumerate(r.picker_lifetime_identities())]

    def collect(self, cases=None, host="Linux", stale=False, marker=1):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / plan["expected"][0]["report_directory"] / "TEST-synthetic.xml"
            report.parent.mkdir(parents=True)
            doc = ET.Element("testsuite")
            for case in self.cases(host) if cases is None else cases:
                node = ET.SubElement(doc, "testcase", classname=case["classname"], name=case["name"])
                if case["status"] != "passed":
                    ET.SubElement(node, {"failed": "failure", "error": "error", "skipped": "skipped"}[case["status"]])
            report.write_bytes(ET.tostring(doc))
            now = time.time_ns()
            if stale: os.utime(report, ns=(now - 10_000_000_000,) * 2)
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({":calf-file-picker:desktopTest": marker}), host_system=host)

    def test_related_three_host_batch_and_failed_host_recoveries_do_not_replay_other_modules(self):
        slots = ["desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"]
        rows = matrix.matrix("picker-batch")["include"]
        self.assertEqual(slots, [row["slot"] for row in rows])
        for row in rows:
            self.assertEqual("calf-file-picker", row["test-modules"])
            self.assertEqual(r.PICKER_LIFETIME_FOCUS, row["test-focus"])
            self.assertEqual("desktop", row["suite"])
        for profile, slot in zip(("picker-batch-linux", "picker-batch-macos", "picker-batch-windows"), slots):
            self.assertEqual([slot], [row["slot"] for row in matrix.matrix(profile)["include"]])
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertTrue(all("test-focus" not in row for row in matrix.matrix("all")["include"]))

    def test_six_exact_declared_methods_use_one_owned_library_filter_and_no_complete_suite_claim(self):
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(r.picker_lifetime_identities(), plan["expected"][0]["required_testcases"])
        self.assertEqual([":calf-file-picker:desktopTest", "--tests", r.PICKER_LIFETIME_CLASS],
                         r.gradle_command("desktop", plan)[-3:])
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(6, result["totals"]["executed"])

    def test_native_host_na_is_exactly_three_portal_methods_not_missing_renderer_or_general_ui_skips(self):
        for host in ("Darwin", "Windows"):
            result = self.collect(host=host)
            self.assertEqual([], result["errors"])
            self.assertEqual(3, result["totals"]["passed"])
            self.assertEqual(3, result["totals"]["not_applicable"])
            self.assertEqual(0, result["totals"]["unexpected_skipped"])
            self.assertTrue(self.collect(self.cases("Linux"), host=host)["errors"])
        for host in ("Linux", "Darwin", "Windows"):
            for status in ("failed", "error", "skipped"):
                cases = self.cases(host); cases[0]["status"] = status
                self.assertTrue(self.collect(cases, host=host)["errors"])
        cases = self.cases(); cases[3]["status"] = "skipped"
        self.assertTrue(self.collect(cases)["errors"])

    def test_missing_duplicate_foreign_stale_and_no_actual_task_are_not_success(self):
        original = self.cases()
        for cases in ([], original[:-1], original * 2, original + [{**original[0], "name": "foreign[desktop]"}],
                      [{**case, "name": case["name"].removesuffix("[desktop]")} for case in original]):
            self.assertTrue(self.collect(cases)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])

    def test_wrong_scope_mutated_filters_and_complete_claims_are_rejected(self):
        for suite, modules in (("js", ("calf-file-picker",)), ("ios", ("calf-file-picker",)),
                               ("desktop", ("calf-io",)), ("desktop", None)):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.PICKER_LIFETIME_FOCUS)
        for key, value in (("task", ":calf-file-picker:publish"), ("test_filter", "*"),
                           ("required_testcases", []), ("test_source_files", [])):
            plan = copy.deepcopy(self.plan()); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan(); plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError): r.validate_test_focus(plan)

    def test_valid_owning_declarations_precede_mutation_and_missing_source_rejection(self):
        source = (r.ROOT / r.PICKER_LIFETIME_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-file-picker",\n)\n')
            module = root / "calf-file-picker"; module.mkdir()
            (module / "build.gradle.kts").write_text("// synthetic, never compiled\n")
            path = root / r.PICKER_LIFETIME_SOURCE; path.parent.mkdir(parents=True); path.write_text(source)
            def plan(): return r.plan(root, "desktop", only_modules=("calf-file-picker",), focus=r.PICKER_LIFETIME_FOCUS)
            self.assertTrue(r.validate_test_focus(plan()))
            for changed in (source.replace(r.PICKER_LIFETIME_METHODS[0], "wrongMethod", 1),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun extra() {}\n"):
                path.write_text(changed)
                with self.assertRaises(ValueError): plan()
            path.write_text(source); self.assertTrue(r.validate_test_focus(plan()))
            path.unlink()
            (module / "src/commonTest").mkdir(parents=True)
            (module / "src/commonTest/Other.kt").write_text("// unrelated tests")
            with self.assertRaisesRegex(ValueError, "scenario source is missing"): plan()

    def test_renderer_is_test_only_public_factory_uses_actual_native_operation_and_window_worker_is_joined(self):
        source = (r.ROOT / "calf-file-picker/build.gradle.kts").read_text()
        test_section = source.split("sourceSets.desktopTest.dependencies {", 1)[1].split("}", 1)[0]
        self.assertIn("implementation(compose.desktop.currentOs)", test_section)
        self.assertEqual(1, source.count("compose.desktop.currentOs"))
        production = (r.ROOT / "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FilePickerLauncher.desktop.kt").read_text()
        self.assertIn("onError, onResult, PlatformFilePicker::pick", production)
        self.assertIn("internal fun rememberDesktopFilePickerLauncher", production)
        self.assertIn("val launchPickFiles = currentPickFiles", production)
        tests = (r.ROOT / r.PICKER_LIFETIME_SOURCE).read_text()
        for required in ("awaitLatch(finished)", "PlatformFilePicker.pick(directory, type, mode, title, parent)",
                         "NATIVECMPKIT_PICKER_OWNED_DISPLAY", '"--pid"', '"^$title$"', "NativeFilePickerBridge.destroyDialog(handle.get())"):
            self.assertIn(required, tests)

    def test_batch_workflow_uploads_only_sanitized_jni_and_portal_receipts(self):
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("if: matrix.test-focus == 'picker-native-lifetime'", workflow)
        self.assertIn('scripts/ci/picker_jni_paths.py --output "build/ci-verification/$SLOT-jni-paths"', workflow)
        upload = workflow.split("- name: Keep receipts and actual selected-task XML only; never packages", 1)[1].split("\n  webview-consumer:", 1)[0]
        self.assertIn("-jni-paths/*.json", upload)
        self.assertIn("/desktop-picker-portal/receipt.json", upload)
        for excluded in ("cargo.private.log", "*.log", "target/", ".so", ".dll", ".dylib", "nck-picker-", "/desktop-picker-portal/**"):
            self.assertNotIn(excluded, upload)


if __name__ == "__main__": unittest.main()
