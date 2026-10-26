from collections import Counter
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as r


class LibraryTestReceipts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-fixture",\n    ":calf-empty",\n    ":calf-permissions:core",\n    ":sample:common",\n)\nproject(":calf-permissions:core").name = "calf-permissions-core"\n')
        for module in ("calf-fixture", "calf-empty", "calf-permissions/core", "sample/common"):
            self.write(module + "/build.gradle.kts", "// build fixture\n")
        self.write("calf-fixture/src/commonTest/kotlin/Fixture.kt", "// synthetic test input\n")

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode())
        return path

    def plan(self, suite="desktop"):
        return r.plan(self.root, suite, minimum_modules=("calf-fixture",))

    def report(self, name="a", status="", **attributes):
        extra = " ".join(f'{key}="{value}"' for key, value in attributes.items())
        return f'<testsuite name="fixture" {extra}><testcase classname="Fixture" name="{name}">{status}</testcase></testsuite>'.encode()

    def collect(self, test_plan=None, markers=True):
        test_plan = test_plan or self.plan()
        now = time.time_ns()
        return r.collect_reports(self.root, test_plan, now - 1_000_000_000, now + 1_000_000_000,
                                 Counter(item["task"] for item in test_plan["expected"]) if markers else Counter())

    def test_literal_project_renames_and_sample_exclusion(self):
        projects = r.projects(self.root)
        self.assertEqual(":calf-permissions:calf-permissions-core", projects["calf-permissions/core"])
        self.assertNotIn("sample/common", projects)

    def test_source_set_inheritance_is_target_specific(self):
        for source_set in ("materialTest", "nonAndroidTest", "iosTest", "androidHostTest", "webTest"):
            self.write(f"calf-fixture/src/{source_set}/kotlin/{source_set}.kt", "// fixture")
        desktop = self.plan()["expected"][0]["test_source_sets"]
        android = self.plan("android-host")["expected"][0]["test_source_sets"]
        ios = self.plan("ios")["expected"][0]["test_source_sets"]
        web = self.plan("wasm")["expected"][0]["test_source_sets"]
        self.assertEqual(["commonTest", "materialTest", "nonAndroidTest"], desktop)
        self.assertEqual(["commonTest", "materialTest", "androidHostTest"], android)
        self.assertEqual(["commonTest", "nonAndroidTest", "iosTest"], ios)
        self.assertEqual(["commonTest", "materialTest", "nonAndroidTest", "webTest"], web)
        self.assertEqual(2, len(self.plan()["uncovered"]))

    def test_removing_last_required_source_is_failure(self):
        (self.root / "calf-fixture/src/commonTest/kotlin/Fixture.kt").unlink()
        with self.assertRaises(ValueError):
            self.plan()

    def test_explicit_diagnostic_subset_is_not_full_ci_coverage(self):
        self.write("calf-empty/src/commonTest/kotlin/A.kt", "// extra module tests")
        plan = r.plan(self.root, "desktop", only_modules=("calf-fixture",))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-fixture"], plan["explicit_module_subset"])
        self.assertEqual(["calf-empty"], plan["test_bearing_modules_not_requested"])
        self.assertEqual(1, len(plan["expected"]))
        for modules in (("calf-fixture", "calf-fixture"), ("../../outside",), ("calf-permissions/core",)):
            with self.assertRaises(ValueError):
                r.plan(self.root, "desktop", only_modules=modules)

    def test_unknown_hierarchy_cannot_silently_drop_sources(self):
        self.write("calf-fixture/src/mysteryTest/kotlin/A.kt", "// fixture")
        with self.assertRaises(ValueError):
            self.plan()

    def test_dynamic_settings_include_requires_review(self):
        self.write("settings.gradle.kts", 'include(\n    libraryProjects.map { it.name }\n)\n')
        with self.assertRaises(ValueError):
            r.projects(self.root)

    def test_snapshot_covers_new_changed_sources_and_build_configuration(self):
        before = r.snapshot_inputs(self.root)
        self.write("calf-fixture/src/commonTest/kotlin/Added.kt", "// new input")
        self.write("calf-fixture/build/ignored.kt", "// generated, not source")
        self.write("sample/common/src/commonTest/kotlin/Sample.kt", "// never substitute sample tests")
        self.write("sample/common/build.gradle.kts", "// evaluated configuration changed")
        after = r.snapshot_inputs(self.root)
        self.assertIn("calf-fixture/src/commonTest/kotlin/Added.kt", after)
        self.assertNotIn("calf-fixture/build/ignored.kt", after)
        self.assertNotIn("sample/common/src/commonTest/kotlin/Sample.kt", after)
        self.assertNotEqual(before["sample/common/build.gradle.kts"], after["sample/common/build.gradle.kts"])
        self.assertNotEqual(r.input_digest(before), r.input_digest(after))

    def test_traversal_and_symlink_sources_refused(self):
        with self.assertRaises(ValueError):
            r.safe_path(self.root, "../external")
        (self.root / "calf-fixture/src/commonTest/link.kt").symlink_to(self.root / "settings.gradle.kts")
        with self.assertRaises(ValueError):
            self.plan()

    def test_actual_case_elements_not_trusted_summary_attributes(self):
        cases = r.junit_cases(self.report(tests="1", failures="0", errors="0", skipped="0"))
        self.assertEqual({"tests": 1, "failures": 0, "errors": 0, "skipped": 0, "passed": 1, "executed": 1,
                          "not_applicable": 0, "unexpected_skipped": 0}, r.case_counts(cases))
        for payload in (self.report(tests="300"), b'<testsuite name="fake" tests="300"/>', self.report(tests="-1")):
            with self.assertRaises(ValueError):
                r.junit_cases(payload)

    def test_duplicate_case_identity_is_not_double_counted(self):
        payload = b'<testsuite name="fixture"><testcase classname="A" name="a"/><testcase classname="A" name="a"/></testsuite>'
        with self.assertRaises(ValueError):
            r.junit_cases(payload)

    def test_dtd_and_entity_payloads_rejected_even_utf16(self):
        payload = '<!DOCTYPE testsuite [<!ENTITY x "entity">]><testsuite name="fixture"><testcase classname="A" name="&x;"/></testsuite>'
        for encoding in ("utf-8", "utf-16"):
            with self.assertRaises(ValueError):
                r.junit_cases(payload.encode(encoding))

    def test_nested_suites_count_once_and_validate_totals(self):
        payload = b'<testsuites tests="1"><testsuite name="fixture" tests="1"><testcase classname="A" name="a"/></testsuite></testsuites>'
        self.assertEqual(1, r.case_counts(r.junit_cases(payload))["tests"])
        with self.assertRaises(ValueError):
            r.junit_cases(payload.replace(b'tests="1"', b'tests="2"', 1))

    def test_test_failure_and_output_bodies_not_exported(self):
        cases = r.junit_cases(self.report(status='<failure message="private message">private body</failure><system-out>secret data</system-out>'))
        self.assertEqual("failed", cases[0]["status"])
        self.assertNotIn("private", json.dumps(cases))
        self.assertNotIn("secret", json.dumps(cases))

    def test_conflicting_skipped_and_failed_case_is_invalid(self):
        with self.assertRaises(ValueError):
            r.junit_cases(self.report(status="<skipped/><failure/>"))

    def test_empty_and_all_skipped_modules_are_not_passing(self):
        directory = self.plan()["expected"][0]["report_directory"]
        self.assertTrue(self.collect()["errors"])
        self.write(directory + "/TEST-empty.xml", b'<testsuite name="fixture" tests="0"/>')
        self.assertTrue(self.collect()["errors"])
        self.write(directory + "/TEST-empty.xml", self.report(status="<skipped/>"))
        result = self.collect()
        self.assertTrue(result["errors"])
        self.assertEqual(0, result["totals"]["executed"])

    def test_fresh_reports_require_actual_task_execution_marker(self):
        self.write(self.plan()["expected"][0]["report_directory"] + "/TEST-a.xml", self.report())
        self.assertFalse(self.collect()["errors"])
        self.assertTrue(self.collect(markers=False)["errors"])

    def test_stale_and_future_dated_reports_are_rejected(self):
        path = self.write(self.plan()["expected"][0]["report_directory"] + "/TEST-a.xml", self.report())
        for delta in (-60, 60):
            timestamp = time.time() + delta
            os.utime(path, (timestamp, timestamp))
            self.assertTrue(self.collect()["errors"])

    def test_one_missing_module_is_failure_despite_other_passing_module(self):
        self.write("calf-empty/src/commonTest/kotlin/A.kt", "// added tests")
        plan = self.plan()
        populated = next(item for item in plan["expected"] if item["module"] == "calf-fixture")
        self.write(populated["report_directory"] + "/TEST-a.xml", self.report())
        result = self.collect(plan)
        self.assertEqual(1, result["totals"]["passed"])
        self.assertTrue(any(error["module"] == "calf-empty" for error in result["errors"]))

    def test_duplicate_case_across_report_files_is_failure(self):
        directory = self.plan()["expected"][0]["report_directory"]
        self.write(directory + "/TEST-a.xml", self.report())
        self.write(directory + "/TEST-b.xml", self.report())
        self.assertTrue(self.collect()["errors"])

    def test_hardlinked_and_symlinked_reports_not_accepted(self):
        directory = self.plan()["expected"][0]["report_directory"]
        original = self.write("build/unrelated/old.xml", self.report())
        report = self.root / directory / "TEST-a.xml"
        report.parent.mkdir(parents=True)
        os.link(original, report)
        self.assertTrue(self.collect()["errors"])
        report.unlink()
        report.symlink_to(original)
        with self.assertRaises(ValueError):
            self.collect()

    def test_quarantine_moves_only_selected_task_reports(self):
        directory = self.plan()["expected"][0]["report_directory"]
        selected = self.write(directory + "/TEST-old.xml", self.report())
        unrelated = self.write("calf-fixture/build/test-results/allTests/TEST-old.xml", self.report())
        output = self.root / "build/ci-verification/run"
        output.mkdir(parents=True)
        moved = r.quarantine_reports(self.root, output, self.plan())
        self.assertEqual([directory], moved)
        self.assertFalse(selected.exists())
        self.assertTrue(unrelated.is_file())
        self.assertTrue((output / "previous-reports" / directory / "TEST-old.xml").is_file())

    def test_quarantine_validates_all_entries_before_mutation(self):
        directory = self.plan()["expected"][0]["report_directory"]
        selected = self.write(directory + "/TEST-old.xml", self.report())
        (selected.parent / "link").symlink_to(self.root / "settings.gradle.kts")
        output = self.root / "build/ci-verification/run"
        output.mkdir(parents=True)
        with self.assertRaises(ValueError):
            r.quarantine_reports(self.root, output, self.plan())
        self.assertTrue(selected.exists())

    def test_command_is_narrow_and_ios_device_is_explicit(self):
        command = r.gradle_command("desktop", self.plan())
        self.assertIn("--init-script", command)
        self.assertIn(":calf-fixture:desktopTest", command)
        self.assertNotIn("--rerun-tasks", command)
        for simulator in (None, "$(untrusted)"):
            with self.assertRaises(ValueError):
                r.gradle_command("ios", self.plan("ios"), simulator)
        with self.assertRaises(ValueError):
            r.gradle_command("desktop", self.plan(), "11111111-1111-1111-1111-111111111111")

    def test_runtime_markers_ignore_cached_task_lines(self):
        log = self.write("build/run.log", "> Task :calf-fixture:desktopTest FROM-CACHE\nNATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:desktopTest gradle=9.7.1 java=17\n")
        self.assertEqual(Counter({":calf-fixture:desktopTest": 1}), r.execution_markers(log))

    def test_bounded_execution_does_not_start_without_disk_reserve(self):
        with patch.object(r.shutil, "disk_usage") as usage, patch.object(r.subprocess, "Popen") as process:
            usage.return_value.free = 0
            result = r.execute(self.root, [sys.executable, "-c", "pass"], self.root / "run.log", 60, 1024)
            self.assertEqual(75, result["exit_code"])
            process.assert_not_called()

    def fake_run(self, *, exit_code=0, mutate_source=False, revision_after=None):
        def execute(root, command, log_path, timeout, reserve_mib):
            self.write("calf-fixture/build/test-results/desktopTest/TEST-a.xml", self.report())
            log_path.write_text("NATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:desktopTest gradle=9.7.1 java=17\n")
            if mutate_source:
                self.write("calf-fixture/src/commonTest/kotlin/Fixture.kt", "// changed during simulated execution")
            return {"exit_code": exit_code}
        with patch.dict(r.MINIMUM_MODULES, {"desktop": ("calf-fixture",)}), \
                patch.object(r.runtime_context, "capture", return_value={"source_revision": "a" * 40, "source_tree_dirty": True, "host": {"system": "Linux"}}), \
                patch.object(r, "git_revision", side_effect=["a" * 40, revision_after or "a" * 40]), \
                patch.object(r, "execute", side_effect=execute):
            return r.run(self.root, "desktop", "build/ci-verification/synthetic", None, 60, 1024)

    def test_simulated_complete_fresh_run_creates_source_bound_receipt(self):
        receipt = self.fake_run()
        self.assertTrue(receipt["passed"])
        self.assertEqual(receipt["inputs_before_sha256"], receipt["inputs_after_sha256"])
        self.assertFalse((self.root / "build/ci-verification/.library-tests.lock").exists())
        with self.assertRaises(ValueError):
            self.fake_run()

    def test_exit_failure_is_not_masked_by_another_passing_suite(self):
        receipt = self.fake_run(exit_code=1)
        self.assertEqual(1, receipt["totals"]["passed"])
        self.assertFalse(receipt["passed"])

    def test_source_change_invalidates_otherwise_passing_simulated_run(self):
        receipt = self.fake_run(mutate_source=True)
        self.assertFalse(receipt["passed"])
        self.assertEqual(["calf-fixture/src/commonTest/kotlin/Fixture.kt"], receipt["changed_inputs"])

    def test_git_revision_change_invalidates_same_bytes(self):
        receipt = self.fake_run(revision_after="b" * 40)
        self.assertFalse(receipt["passed"])
        self.assertEqual("Git source revision changed during test invocation", receipt["input_capture_error"])

    def test_report_nesting_has_a_bound(self):
        payload = b"<testsuites>" * 34 + self.report() + b"</testsuites>" * 34
        with self.assertRaises(ValueError):
            r.junit_cases(payload)


if __name__ == "__main__":
    unittest.main()
