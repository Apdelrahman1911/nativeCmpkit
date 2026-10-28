"""Two-SDK completion guardrails, not Android runtime verification."""
import copy
import unittest

import library_tests as r
import workflow_matrix as m


class AndroidCompletionFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "android-host", only_modules=(r.IOS_PERMISSION_MODULE,),
                      focus=r.ANDROID_PERMISSION_COMPLETION_FOCUS)

    def test_all_three_methods_must_run_on_both_sdks_not_unrelated_suites(self):
        rows = m.matrix("permissions-completion-android")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("android-host", rows[0]["suite"])
        self.assertEqual(r.ANDROID_PERMISSION_COMPLETION_FOCUS, rows[0]["test-focus"])
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(6, len(plan["expected"][0]["required_testcases"]))
        command = r.gradle_command("android-host", plan)
        self.assertEqual(["--tests", r.ANDROID_PERMISSION_COMPLETION_CLASS], command[-2:])
        self.assertFalse(plan["complete_suite_requested"])

    def test_missing_sdk_changed_class_or_wrong_platform_is_rejected(self):
        for suite in ("desktop", "ios", "android-device"):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=(r.IOS_PERMISSION_MODULE,),
                       focus=r.ANDROID_PERMISSION_COMPLETION_FOCUS)
        for change in (lambda p: p["expected"][0]["required_testcases"].pop(),
                       lambda p: p["expected"][0].update(test_filter="arbitrary")):
            plan = copy.deepcopy(self.plan())
            change(plan)
            with self.assertRaises(ValueError):
                r.validate_test_focus(plan)
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_native_callback_boundaries_are_real_contracts_with_zero_retained_observers(self):
        source = (r.ROOT / r.ANDROID_PERMISSION_COMPLETION_SOURCE).read_text()
        self.assertIn("@Config(sdk = [29, 33], manifest = Config.NONE)", source)
        self.assertIn("Permission.Notification", source)
        self.assertIn("Permission.RemoteNotification", source)
        self.assertIn("host.registry.deliver(0, emptySet())", source)
        self.assertIn("assertEquals(0, old.owner.registry.observerCount)", source)
        self.assertIn("assertEquals(0, replacement.owner.registry.observerCount)", source)


if __name__ == "__main__":
    unittest.main()
