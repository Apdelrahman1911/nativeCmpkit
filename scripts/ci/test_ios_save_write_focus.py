"""Finite Foundation failure selection/receipt guards; these are not native executions."""
from collections import Counter
import copy
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import library_tests as r
import workflow_matrix as m


class IOSSaveWriteFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=("calf-file-picker",), focus=r.IOS_SAVE_WRITE_FOCUS)

    def collect(self, identities=None, outcome="", markers=1, duplicate=False):
        expected = self.plan()["expected"][0]
        identities = r.ios_save_write_identities() if identities is None else identities
        xml = "<testsuite>" + "".join(
            f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-synthetic.xml").write_text(xml)
            if duplicate:
                (reports / "TEST-duplicate.xml").write_text(xml)
            now = time.time_ns()
            return r.collect_reports(root, self.plan(), now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({expected["task"]: markers}), host_system="Darwin")

    def test_finite_profile_cli_and_command_select_only_the_new_native_method(self):
        rows = m.matrix("ios-saver-write-failure")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual("calf-file-picker", rows[0]["test-modules"])
        self.assertEqual(r.IOS_SAVE_WRITE_FOCUS, rows[0]["test-focus"])
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        selector = r.IOS_SAVE_WRITE_CLASS + "." + r.IOS_SAVE_WRITE_METHOD
        self.assertEqual(["--tests", selector], r.gradle_command(
            "ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-2:])
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-file-picker", "--focus", r.IOS_SAVE_WRITE_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        report = self.collect()
        self.assertFalse(report["errors"])
        self.assertEqual(1, report["totals"]["passed"])
        self.assertEqual(r.IOS_SAVE_WRITE_SOURCE, report["modules"][0]["native_scenarios"][0]["source"])

    def test_wrong_scope_or_weakened_filter_cannot_run(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_SAVE_WRITE_FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("task", ":calf-file-picker:publish")):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")

    def test_all_original_declarations_remain_and_cannot_be_filtered_away(self):
        source = (r.ROOT / r.IOS_SAVE_WRITE_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text('include(":calf-file-picker")\n')
            path = root / r.IOS_SAVE_WRITE_SOURCE
            path.parent.mkdir(parents=True)
            for changed in (source.replace(r.IOS_SAVE_WRITE_METHOD, "wrongMethod"),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun unrelated() {}\n"):
                path.write_text(changed)
                with self.subTest(change=changed[-70:]), self.assertRaises(ValueError):
                    r.plan(root, "ios", only_modules=("calf-file-picker",), focus=r.IOS_SAVE_WRITE_FOCUS)

    def test_missing_extra_duplicate_or_foreign_target_xml_is_not_success(self):
        original = r.ios_save_write_identities()
        variants = [[], original * 2, [*original, {"classname": original[0]["classname"], "name": "unrelated"}]]
        for key, value in (("classname", r.IOS_SAVE_WRITE_CLASS), ("classname", "iosSimulatorArm64Test.Foreign"),
                           ("name", r.IOS_SAVE_WRITE_METHOD), ("name", r.IOS_SAVE_WRITE_METHOD + "[iosArm64]")):
            changed = copy.deepcopy(original)
            changed[0][key] = value
            variants.append(changed)
        for identities in variants:
            with self.subTest(identities=identities):
                self.assertTrue(self.collect(identities)["errors"])
        self.assertTrue(self.collect(duplicate=True)["errors"])

    def test_failed_skipped_or_no_actual_task_marker_never_passes(self):
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])
