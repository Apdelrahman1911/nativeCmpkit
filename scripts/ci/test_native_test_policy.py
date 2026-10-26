"""Synthetic policy fixtures only; not execution of native JNI/AppKit tests."""
import time
import unittest
from collections import Counter

import library_tests as runner
import native_test_policy as policy
import test_library_tests as fixture_tools


def cases(host="Linux", suffix="[desktop]"):
    not_applicable = policy.NON_MAC if policy.canonical_host(host) == "macos" else policy.MAC_GUI
    return [{"classname": policy.CLASS, "name": method + suffix,
             "status": "skipped" if method == not_applicable else "passed"}
            for method in policy.REQUIRED_CASES]


class NativeScenarioPolicy(unittest.TestCase):
    def test_host_canonicalization_never_confuses_darwin_with_windows(self):
        for value in ("mac", "Darwin", "macOS", "MAC OS X"):
            self.assertEqual("macos", policy.canonical_host(value))
        for value in ("windows", "Windows", "win32"):
            self.assertEqual("windows", policy.canonical_host(value))
        self.assertEqual("linux", policy.canonical_host("Linux"))
        for value in ("", "GNU/Linux", "not-mac", "FreeBSD", "DarwinWindows", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                policy.canonical_host(value)

    def test_exact_host_na_is_not_a_pass(self):
        for host in ("Linux", "windows", "Darwin", "mac"):
            for suffix in ("", "[desktop]"):
                with self.subTest(host=host, suffix=suffix):
                    actual = cases(host, suffix)
                    scenarios, errors = policy.apply(policy.MODULE, "desktop", actual, host, True)
                    self.assertEqual([], errors)
                    self.assertEqual(4, len(scenarios))
                    counts = runner.case_counts(actual)
                    self.assertEqual(3, counts["passed"])
                    self.assertEqual(3, counts["executed"])
                    self.assertEqual(1, counts["not_applicable"])
                    self.assertEqual(1, counts["skipped"])
                    self.assertEqual(0, counts["unexpected_skipped"])

    def test_required_mac_gui_skip_and_missing_optin_fail(self):
        for skip, opt_in in ((True, True), (True, False), (False, False)):
            actual = cases("mac")
            if skip:
                actual[-1]["status"] = "skipped"
            scenarios, errors = policy.apply(policy.MODULE, "desktop", actual, "mac", opt_in)
            self.assertTrue(errors)
            self.assertNotEqual("not-applicable", scenarios[-1]["disposition"])
            self.assertEqual(1, runner.case_counts(actual)["not_applicable"])

    def test_all_host_case_skip_or_failure_is_never_na(self):
        for status in ("failed", "error", "skipped"):
            actual = cases()
            actual[0]["status"] = status
            _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
            self.assertTrue(errors)
            self.assertNotIn("disposition", actual[0])

    def test_missing_or_renamed_scenario_fails_including_na_scenario(self):
        for index in range(4):
            actual = cases()
            actual.pop(index)
            _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
            self.assertTrue(any("exactly once" in error for error in errors))

    def test_duplicate_normalized_case_is_rejected(self):
        actual = cases()
        extra = dict(actual[0])
        extra["name"] = policy.ALL_HOSTS[0]
        actual.append(extra)
        _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
        self.assertTrue(any("exactly once" in error for error in errors))

    def test_na_must_not_be_falsely_counted_as_executed(self):
        actual = cases()
        actual[-1]["status"] = "passed"
        _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
        self.assertTrue(any("not executed or counted passed" in error for error in errors))
        self.assertEqual(0, runner.case_counts(actual)["not_applicable"])

    def test_case_names_cannot_broaden_the_exception(self):
        for altered in (policy.MAC_GUI + "[ios]", "prefix" + policy.MAC_GUI, policy.MAC_GUI + "[desktop][desktop]"):
            actual = cases()
            actual[-1]["name"] = altered
            _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
            self.assertTrue(errors)
            self.assertEqual(1, runner.case_counts(actual)["unexpected_skipped"])

    def test_wrong_class_module_and_suite_never_get_skip_exception(self):
        actual = cases()
        actual[-1]["classname"] = "SomeOtherTest"
        _, errors = policy.apply(policy.MODULE, "desktop", actual, "Linux", False)
        self.assertTrue(errors)
        for module, suite in (("calf-io", "desktop"), (policy.MODULE, "js")):
            actual = cases()
            self.assertEqual(([], []), policy.apply(module, suite, actual, "Linux", False))
            self.assertEqual(1, runner.case_counts(actual)["unexpected_skipped"])


class NativeScenarioReports(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_tools.LibraryTestReceipts()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.write("settings.gradle.kts", 'include(\n    ":calf-share",\n)\n')
        self.fixture.write("calf-share/build.gradle.kts", "// fixture")
        self.fixture.write(policy.SOURCE, "// source-bound synthetic scenario fixture")

    def collect(self, extra_skip=False):
        actual = cases()
        if extra_skip:
            actual.append({"classname": "Unrelated", "name": "skippedCase", "status": "skipped"})
        payload = '<testsuite name="share">' + ''.join(
            f'<testcase classname="{case["classname"]}" name="{case["name"]}">' +
            ('<skipped/>' if case["status"] == "skipped" else '') + '</testcase>' for case in actual) + '</testsuite>'
        self.fixture.write("calf-share/build/test-results/desktopTest/TEST-share.xml", payload)
        plan = runner.plan(self.root, "desktop", minimum_modules=("calf-share",))
        now = time.time_ns()
        return runner.collect_reports(self.root, plan, now-1_000_000_000, now+1_000_000_000,
                                      Counter({":calf-share:desktopTest": 1}), host_system="Linux")

    def test_synthetic_collector_counts_na_separately_per_report_and_total(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(3, result["totals"]["passed"])
        self.assertEqual(1, result["totals"]["not_applicable"])
        self.assertEqual(1, result["modules"][0]["reports"][0]["not_applicable"])
        self.assertEqual(4, len(result["modules"][0]["native_scenarios"]))

    def test_unrelated_skip_still_invalidates_suite(self):
        result = self.collect(extra_skip=True)
        self.assertTrue(result["errors"])
        self.assertEqual(1, result["totals"]["unexpected_skipped"])

    def test_deleting_native_source_cannot_silently_drop_scenarios(self):
        (self.root / policy.SOURCE).unlink()
        self.fixture.write("calf-share/src/commonTest/kotlin/Other.kt", "// unrelated tests")
        with self.assertRaisesRegex(ValueError, "scenario source is missing"):
            runner.plan(self.root, "desktop", minimum_modules=("calf-share",))


if __name__ == "__main__":
    unittest.main()
