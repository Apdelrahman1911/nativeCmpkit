"""Important finite selection/fresh XML controls; no EventKit/native execution."""
from collections import Counter
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import ios_calendar_native_focus as calendar
import library_tests as runner
import workflow_matrix as matrix


class CalendarNativeFocusTests(unittest.TestCase):
    def plan(self):
        return runner.plan(runner.ROOT, "ios", only_modules=(calendar.MODULE,), focus=calendar.FOCUS)

    def collect(self, identities=None, outcome="", markers=1, duplicate=False, stale=False,
                host="Darwin", extra_empty=False, split=False):
        plan = self.plan()
        expected = plan["expected"][0]
        identities = calendar.identities() if identities is None else identities
        payload = "<testsuite>" + "".join(
            f'<testcase classname="{item["classname"]}" name="{item["name"]}">{outcome}</testcase>'
            for item in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            path = reports / "TEST-synthetic.xml"
            path.write_text(payload)
            if duplicate:
                (reports / "TEST-synthetic-duplicate.xml").write_text(payload)
            if extra_empty:
                (reports / "TEST-synthetic-empty.xml").write_text("<testsuite/>")
            if split:
                def part(items):
                    return "<testsuite>" + "".join(
                        f'<testcase classname="{item["classname"]}" name="{item["name"]}"/>'
                        for item in items) + "</testsuite>"
                path.write_text(part(identities[:2]))
                (reports / "TEST-synthetic-rest.xml").write_text(part(identities[2:]))
            now = time.time_ns()
            if stale:
                # Outside the collector's unchanged two-second filesystem-clock
                # tolerance, while preserving a legitimate start <= finish.
                os.utime(path, ns=(now - 4_000_000_000, now - 4_000_000_000))
            lower = now - 1_000_000_000
            return runner.collect_reports(root, plan, lower, now + 2_000_000_000,
                Counter({expected["task"]: markers}), host_system=host)

    def test_five_new_native_methods_only_use_the_exact_calendar_task_filter_and_iphone_row(self):
        rows = matrix.matrix(calendar.PROFILE)["include"]
        self.assertEqual([{"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
            "python": "python3", "simulator-kind": "iphone", "test-modules": calendar.MODULE,
            "test-focus": calendar.FOCUS}], rows)
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual([calendar.MODULE], plan["explicit_module_subset"])
        self.assertEqual(1, len(plan["expected"]))
        self.assertEqual(calendar.TASK, plan["expected"][0]["task"])
        self.assertEqual(calendar.identities(), plan["expected"][0]["required_testcases"])
        self.assertEqual(["--tests", calendar.CLASS], runner.gradle_command("ios", plan,
            simulator="00000000-0000-4000-8000-000000000001")[-2:])
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(5, result["totals"]["passed"])
        self.assertEqual(0, result["totals"]["not_applicable"])

    def test_other_modules_targets_broad_filters_and_publish_tasks_are_refused(self):
        for suite, modules in (("desktop", (calendar.MODULE,)), ("ios", ("calf-permissions/core",)),
                               ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                runner.plan(runner.ROOT, suite, only_modules=modules, focus=calendar.FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []),
                           ("task", ":calf-permissions:calf-permissions-calendar:publish")):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.gradle_command("ios", plan)

    def test_changed_missing_extra_or_ignored_native_methods_cannot_be_filtered_away(self):
        source = (runner.ROOT / calendar.SOURCE).read_text()
        calendar.validate_source(source, [calendar.SOURCE])
        variants = (source.replace(calendar.METHODS[0], "foreignMethod", 1),
            source.replace("@Test", "@Ignore @Test", 1), source + "\n@Test fun extraTest() {}\n",
            source.replace("PermissionDelegateRegistry.getDelegate(", "replacementDelegate("))
        for changed in variants:
            with self.subTest(change=changed[-70:]), self.assertRaises(ValueError):
                calendar.validate_source(changed, [calendar.SOURCE])
        with self.assertRaises(ValueError):
            calendar.validate_source(source, [])

    def test_missing_extra_foreign_targets_or_duplicate_xml_never_pass(self):
        expected = calendar.identities()
        variants = [expected[:-1], [*expected, expected[0]],
            [*expected, {"classname": expected[0]["classname"], "name": "foreign[iosSimulatorArm64]"}]]
        for key, value in (("classname", calendar.CLASS), ("classname", "iosSimulatorArm64Test.Foreign"),
                           ("name", calendar.METHODS[0]), ("name", calendar.METHODS[0] + "[iosArm64]")):
            changed = copy.deepcopy(expected)
            changed[0][key] = value
            variants.append(changed)
        for items in variants:
            with self.subTest(items=items):
                self.assertTrue(self.collect(items)["errors"])
        self.assertTrue(self.collect(duplicate=True)["errors"])

    def test_extra_empty_or_split_originals_cannot_supply_one_native_class_execution(self):
        for options in ({"extra_empty": True}, {"split": True}):
            with self.subTest(options=options):
                self.assertTrue(self.collect(**options)["errors"])

    def test_failed_skipped_stale_missing_execution_and_non_apple_results_never_pass(self):
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        self.assertTrue(self.collect(host="Linux")["errors"])

    def test_new_cli_and_source_preflight_select_only_the_compiled_native_class(self):
        result = subprocess.run([sys.executable, str(runner.ROOT / "scripts/ci/library_tests.py"), "plan",
            "--suite", "ios", "--module", calendar.MODULE, "--focus", calendar.FOCUS],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        import json
        self.assertEqual(calendar.identities(), json.loads(result.stdout)["expected"][0]["required_testcases"])
        planned = matrix.preflight_plans(calendar.PROFILE)
        self.assertEqual(1, len(planned["slots"]))


if __name__ == "__main__":
    unittest.main()
