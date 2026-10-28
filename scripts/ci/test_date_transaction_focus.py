"""Synthetic finite-selection fixtures, not Material/native library test passes."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import tempfile
import time
import unittest

import library_tests as r


class DateTransactionFocusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-ui",\n)\n')
        self.write("calf-ui/build.gradle.kts", "// synthetic build, never executed\n")
        self.write("calf-ui/src/commonTest/kotlin/Unrelated.kt", "// retained, not requested\n")
        self.write(r.DATE_TRANSACTION_SCENARIOS_SOURCE, "// synthetic scenario declarations\n")
        self.source = "package com.mohamedrejeb.calf.ui.datepicker\nclass CompactDateTransactionAcceptanceTest {\n" + \
            "\n".join("@Test fun " + method + "(): TestResult = fake()" for method in r.DATE_TRANSACTION_METHODS) + "\n}\n"
        for source in set(r.date_transaction_source(suite) for suite in r.DATE_TRANSACTION_SOURCE_SETS):
            self.write(source, self.source)

    def write(self, name, payload):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload)

    def plan(self, suite):
        return r.plan(self.root, suite, only_modules=("calf-ui",), focus=r.DATE_TRANSACTION_FOCUS)

    def cases(self, suite):
        prefix = r.SUITES[suite][0] + "." if suite in {"js", "wasm"} else ""
        suffix = {"desktop": "[desktop]", "android-host": "", "android-device": "",
                  "js": "[js, browser, ChromeHeadless155.0.0.0, Linux0.0.0]",
                  "wasm": "[wasmJs, browser, ChromeHeadless155.0.0.0, Linux0.0.0]"}[suite]
        return [{"classname": prefix + r.DATE_TRANSACTION_CLASS, "name": method + suffix, "status": "passed"}
                for method in r.DATE_TRANSACTION_METHODS]

    def collect(self, suite, cases):
        plan = self.plan(suite)
        body = ""
        for case in cases:
            status = {"passed": "", "skipped": "<skipped/>", "failed": "<failure/>"}[case["status"]]
            body += '<testcase classname="' + case["classname"] + '" name="' + case["name"] + '">' + status + '</testcase>'
        self.write(plan["expected"][0]["report_directory"] + "/TEST-date.xml", "<testsuite>" + body + "</testsuite>")
        now = time.time_ns()
        return r.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                 Counter({plan["expected"][0]["task"]: 1}))

    def test_five_plans_retain_inputs_but_request_only_four_methods(self):
        for suite in r.DATE_TRANSACTION_SOURCE_SETS:
            with self.subTest(suite=suite):
                plan = self.plan(suite)
                self.assertTrue(r.validate_test_focus(plan))
                self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(r.date_transaction_identities(), plan["expected"][0]["required_testcases"])
                self.assertIn("calf-ui/src/commonTest/kotlin/Unrelated.kt", plan["expected"][0]["test_source_files"])

    def test_host_and_browser_use_KGP_filters_and_device_uses_instrumentation_argument(self):
        for suite in ("desktop", "android-host", "js", "wasm"):
            with self.subTest(suite=suite):
                command = r.gradle_command(suite, self.plan(suite), root=self.root)
                self.assertEqual([":calf-ui:" + r.SUITES[suite][0], "--tests", r.DATE_TRANSACTION_CLASS], command[-3:])
                self.assertEqual(1, command.count("--tests"))
        command = r.gradle_command("android-device", self.plan("android-device"), root=self.root,
                                   android_serial="emulator-5554")
        self.assertNotIn("--tests", command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + r.DATE_TRANSACTION_CLASS, command)
        self.assertEqual(":calf-ui:connectedAndroidDeviceTest", command[-1])

    def test_unreviewed_suite_module_and_freeform_filters_are_rejected(self):
        for suite, modules, focus in (("ios", ("calf-ui",), r.DATE_TRANSACTION_FOCUS),
                                     ("desktop", ("calf-share",), r.DATE_TRANSACTION_FOCUS),
                                     ("desktop", ("calf-ui", "calf-io"), r.DATE_TRANSACTION_FOCUS),
                                     ("js", ("calf-ui",), "arbitrary.*")):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)

    def test_changed_or_added_authored_methods_require_selection_review(self):
        for source in (self.source.replace(r.DATE_TRANSACTION_METHODS[0], "different"),
                       self.source.replace("\n}", "\n@Test fun extra() {}\n}")):
            self.write(r.date_transaction_source("js"), source)
            with self.assertRaises(ValueError):
                self.plan("js")

    def test_tampered_plans_and_cross_suite_execution_are_rejected(self):
        plan = self.plan("js")
        for key, value in (("test_filter", "arbitrary"), ("required_testcases", []), ("test_source_files", [])):
            changed = deepcopy(plan)
            changed["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(changed)
        with self.assertRaises(ValueError):
            r.gradle_command("wasm", plan, root=self.root)
        changed = deepcopy(plan)
        changed["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            r.validate_test_focus(changed)

    def test_five_actual_target_naming_contracts_are_accepted(self):
        for suite in r.DATE_TRANSACTION_SOURCE_SETS:
            with self.subTest(suite=suite):
                result = self.collect(suite, self.cases(suite))
                self.assertEqual([], result["errors"])
                self.assertEqual(4, result["totals"]["passed"])

    def test_missing_extra_failed_skipped_duplicate_or_wrong_target_cases_fail(self):
        good = self.cases("wasm")
        for cases in (good[:-1], good + [dict(good[0], name="unrelated[wasmJs, browser, Chrome]")],
                      [dict(good[0], status="failed"), *good[1:]], [dict(good[0], status="skipped"), *good[1:]],
                      [dict(good[0], classname="jsBrowserTest." + r.DATE_TRANSACTION_CLASS), *good[1:]],
                      [dict(good[0], name=good[0]["name"].replace("[wasmJs,", "[js,")), *good[1:]],
                      [good[0], good[0], *good[2:]]):
            with self.subTest(cases=cases):
                self.assertTrue(self.collect("wasm", cases)["errors"])

    def test_full_suite_requests_remain_unfiltered(self):
        plan = r.plan(self.root, "desktop", only_modules=("calf-ui",))
        self.assertFalse(r.validate_test_focus(plan))
        self.assertNotIn("--tests", r.gradle_command("desktop", plan, root=self.root))


if __name__ == "__main__":
    unittest.main()
