"""Synthetic driver refusal/restoration checks, not UIKit or simulator executions."""
import copy
import subprocess
import unittest

import simulator_appearance as s

DEVICE = "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"


class AppearanceDriverTests(unittest.TestCase):
    def fake(self, initial="light"):
        self.actual = initial
        self.commands = []

        def control(argv, timeout):
            self.assertEqual(30, timeout)
            self.assertEqual(["/usr/bin/xcrun", "simctl", "ui", DEVICE, "appearance"], argv[:5])
            self.commands.append(argv)
            if len(argv) == 6:
                self.actual = argv[5]
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            return subprocess.CompletedProcess(argv, 0, (self.actual + "\n").encode(), b"")

        self.control = control
        return s.AppearanceDriver(DEVICE, control)

    def complete(self, initial="light"):
        driver = self.fake(initial)
        driver.start()
        for step, style in s.REQUESTS:
            driver.request(step, style)
        driver.restore()
        return driver

    def test_two_genuine_state_changes_and_original_light_or_dark_restoration_are_exactly_recorded(self):
        for initial, count in (("light", 10), ("dark", 14)):
            with self.subTest(initial=initial):
                driver = self.complete(initial)
                self.assertEqual(initial, self.actual)
                self.assertEqual(count, len(self.commands))
                self.assertTrue(s.validate_receipt(driver.receipt, DEVICE))
                self.assertFalse(driver.receipt["uses_window_override"])
                self.assertFalse(driver.receipt["physical_settings_verified"])
                self.assertNotIn("stdout", repr(driver.receipt))

    def test_preparation_requests_and_cleanup_cannot_be_replayed_or_reordered(self):
        driver = self.fake()
        with self.assertRaises(ValueError):
            driver.request(1, "dark")
        driver.start()
        with self.assertRaises(ValueError):
            driver.start()
        for step, style in ((2, "light"), (True, "dark"), (1, "light"), (1, "$(command)")):
            with self.subTest(step=step, style=style), self.assertRaises(ValueError):
                driver.request(step, style)
        driver.request(1, "dark")
        with self.assertRaises(ValueError):
            driver.request(1, "dark")
        driver.request(2, "light")
        driver.restore()
        count = len(self.commands)
        driver.restore()
        self.assertEqual(count, len(self.commands))
        with self.assertRaises(ValueError):
            driver.request(1, "dark")

    def test_bad_device_unknown_nonbytes_unbounded_query_or_failed_exit_does_not_authorize_change(self):
        for device in ("booted", "", DEVICE + ";command"):
            with self.subTest(device=device), self.assertRaises(ValueError):
                s.AppearanceDriver(device, lambda *_: self.fail("Must not execute"))
        for code, stdout, exception in ((1, b"light", RuntimeError), (0, b"unknown", ValueError),
                                       (0, b"light\ndark", ValueError), (0, "light", ValueError),
                                       (0, b"x" * 129, ValueError), (False, b"light", ValueError)):
            calls = []
            def control(argv, timeout):
                calls.append(argv)
                return subprocess.CompletedProcess(argv, code, stdout, b"")
            driver = s.AppearanceDriver(DEVICE, control)
            with self.subTest(code=code, stdout=type(stdout).__name__), self.assertRaises(exception):
                driver.start()
            driver.restore()
            self.assertEqual(1, len(calls))
            self.assertTrue(all(len(c) == 5 for c in calls))
            self.assertFalse(driver.receipt["restored"])
            self.assertFalse(s.validate_receipt(driver.receipt, DEVICE))

    def test_wrong_readback_or_absent_transition_stays_failed_and_original_style_is_restored(self):
        driver = self.fake("dark")
        driver.start()
        self.actual = "dark"  # Unexpected external state change before first request.
        with self.assertRaises(ValueError):
            driver.request(1, "dark")
        driver.restore()
        self.assertEqual("dark", self.actual)
        self.assertFalse(s.validate_receipt(driver.receipt, DEVICE))
        driver = self.fake()
        driver.start()
        original = driver.control
        def do_not_apply(argv, timeout):
            if len(argv) == 6 and argv[5] == "dark":
                return subprocess.CompletedProcess(argv, 0, b"", b"")
            return original(argv, timeout)
        driver.control = do_not_apply
        with self.assertRaises(ValueError):
            driver.request(1, "dark")
        driver.restore()
        self.assertFalse(s.validate_receipt(driver.receipt, DEVICE))

    def test_uncertain_failed_native_set_is_reconciled_for_cleanup_not_retried_as_success(self):
        driver = self.fake("light")
        driver.start()
        original = driver.control
        count = 0
        def fail_after_change(argv, timeout):
            nonlocal count
            result = original(argv, timeout)
            if len(argv) == 6 and argv[5] == "dark":
                count += 1
                return subprocess.CompletedProcess(argv, 1, b"", b"")
            return result
        driver.control = fail_after_change
        with self.assertRaises(RuntimeError):
            driver.request(1, "dark")
        self.assertEqual("dark", self.actual)
        driver.restore()
        self.assertEqual("light", self.actual)
        self.assertEqual(1, count)
        self.assertFalse(s.validate_receipt(driver.receipt, DEVICE))

    def test_missing_corrupted_boolean_foreign_or_reordered_receipt_evidence_cannot_pass(self):
        document = self.complete("dark").receipt
        variants = []
        for key, value in (("restored", False), ("prepared_light", False), ("uses_window_override", True),
                           ("physical_settings_verified", True), ("initial_style", "unknown"),
                           ("restored_style", "light"), ("schema_version", True), ("error_type", "TimeoutError")):
            bad = copy.deepcopy(document); bad[key] = value; variants.append(bad)
        for transform in (
            lambda d: d["steps"].pop(),
            lambda d: d["steps"].reverse(),
            lambda d: d["steps"][0].update(step=True),
            lambda d: d["steps"][0].update(set_exit_code=False),
            lambda d: d["controls"].pop(),
            lambda d: d["controls"].reverse(),
            lambda d: d["controls"][0].update(exit_code=True),
            lambda d: d["controls"][0].update(observed_style="light"),
            lambda d: d["controls"][1].update(command=["sh", "-c", "anything"]),
            lambda d: d["controls"][1].update(observed_style="light"),
        ):
            bad = copy.deepcopy(document); transform(bad); variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(index=index):
                self.assertFalse(s.validate_receipt(bad, DEVICE))
        self.assertFalse(s.validate_receipt(document, "booted"))
        self.assertFalse(s.validate_receipt(document, DEVICE.replace("AAAA", "BBBB")))


if __name__ == "__main__":
    unittest.main()
