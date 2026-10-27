"""Adversarial exact native IO JUnit policy fixtures; zero Apple executions."""
from collections import Counter
from pathlib import Path
import tempfile
import time
import unittest

import library_tests as runner
import native_test_policy as policy


class IosIoPolicyTests(unittest.TestCase):
    def cases(self, module):
        return [{"classname": "iosSimulatorArm64Test." + classname,
                 "name": method + "[iosSimulatorArm64]", "status": "passed"}
                for classname, method, _ in policy.IOS_IO_CASES[module]]

    def test_every_required_native_case_must_execute_once_on_apple(self):
        for module in policy.IOS_IO_CASES:
            cases = self.cases(module)
            scenarios, errors = policy.apply(module, "ios", cases, "Darwin", False)
            self.assertFalse(errors)
            self.assertEqual(len(cases), len(scenarios))
            self.assertTrue(all(row["required_on_host"] and row["disposition"] == "required-executed" for row in scenarios))
            self.assertTrue(all(row["status"] == "passed" for row in cases))

    def test_missing_duplicate_skipped_failed_or_error_case_cannot_be_accepted(self):
        for module in policy.IOS_IO_CASES:
            for disposition in ("missing", "duplicate", "skipped", "failed", "error"):
                with self.subTest(module=module, disposition=disposition):
                    cases = self.cases(module)
                    if disposition == "missing":
                        cases.pop()
                    elif disposition == "duplicate":
                        cases.append(dict(cases[-1]))
                    else:
                        cases[-1]["status"] = disposition
                    original = [dict(row) for row in cases]
                    _, errors = policy.apply(module, "ios", cases, "Darwin", False)
                    self.assertTrue(errors)
                    self.assertEqual(original, cases, "Never promote or rewrite a native outcome")

    def test_wrong_task_target_or_class_identity_cannot_be_normalized_to_success(self):
        for module in policy.IOS_IO_CASES:
            for field, replacement in (("name", "[desktop]"), ("classname", "otherTask.")):
                with self.subTest(module=module, field=field):
                    cases = self.cases(module)
                    if field == "name":
                        cases[-1][field] = cases[-1][field].replace("[iosSimulatorArm64]", replacement)
                    else:
                        cases[-1][field] = cases[-1][field].replace("iosSimulatorArm64Test.", replacement)
                    _, errors = policy.apply(module, "ios", cases, "Darwin", False)
                    self.assertTrue(errors)

    def test_non_apple_host_and_unrelated_suites_cannot_claim_native_io_acceptance(self):
        for module in policy.IOS_IO_CASES:
            _, errors = policy.apply(module, "ios", self.cases(module), "Linux", False)
            self.assertTrue(errors)
            self.assertEqual(([], []), policy.apply(module, "desktop", [], "Linux", False))
        self.assertEqual(([], []), policy.apply("calf-ui", "ios", [], "Darwin", False))

    def test_real_sources_and_report_collector_enforce_required_cases(self):
        for module, requirements in policy.IOS_IO_CASES.items():
            for classname, method, source in requirements:
                self.assertTrue((runner.ROOT / source).is_file(), source)
                self.assertIn("fun " + method + "(", (runner.ROOT / source).read_text(), method)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                report = module + "/build/test-results/iosSimulatorArm64Test"
                folder = root / report
                folder.mkdir(parents=True)
                payload = ('<testsuite name="unrelated" tests="1" failures="0" errors="0" skipped="0">'
                           '<testcase classname="unrelated" name="unrelated"/></testsuite>')
                (folder / "TEST-unrelated.xml").write_text(payload)
                task = ":" + module + ":iosSimulatorArm64Test"
                plan = {"suite": "ios", "expected": [{"module": module, "task": task, "report_directory": report}]}
                now = time.time_ns()
                receipt = runner.collect_reports(root, plan, now, now, Counter({task: 1}), host_system="Darwin")
                self.assertTrue(receipt["errors"], "Nonzero unrelated XML must not replace mandatory native regressions")
                self.assertEqual(len(requirements), len(receipt["modules"][0]["native_scenarios"]))


if __name__ == "__main__":
    unittest.main()
