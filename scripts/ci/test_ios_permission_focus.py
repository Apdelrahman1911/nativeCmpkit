"""Focused native factory selection only; these fixtures are not iOS execution."""
import copy
import unittest

import library_tests as r
import workflow_matrix as m


class IOSPermissionFocusTests(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=(r.IOS_PERMISSION_MODULE,), focus=r.IOS_PERMISSION_FOCUS)

    def test_only_seven_owning_methods_on_one_native_target_are_requested(self):
        rows = m.matrix("permissions-ios")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual(r.IOS_PERMISSION_FOCUS, rows[0]["test-focus"])
        self.assertEqual(r.IOS_PERMISSION_MODULE, rows[0]["test-modules"])
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(r.ios_permission_identities(), plan["expected"][0]["required_testcases"])
        command = r.gradle_command("ios", plan, simulator="00000000-0000-4000-8000-000000000001")
        self.assertEqual(["--tests", r.IOS_PERMISSION_CLASS], command[-2:])
        self.assertFalse(plan["complete_suite_requested"])

    def test_filters_cannot_escape_the_reviewed_native_scope_or_drop_a_method(self):
        for suite, modules in (("desktop", (r.IOS_PERMISSION_MODULE,)), ("ios", ("calf-ui",))):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PERMISSION_FOCUS)
        plan = copy.deepcopy(self.plan())
        plan["expected"][0]["required_testcases"].pop()
        with self.assertRaises(ValueError):
            r.validate_test_focus(plan)
        for profile in ("all", "ios", "ios-ui", "permissions-unsupported"):
            self.assertTrue(all(row.get("test-focus") != r.IOS_PERMISSION_FOCUS for row in m.matrix(profile)["include"]))

    def test_tests_use_the_real_darwin_main_queue_and_acknowledge_late_callbacks(self):
        source = (r.ROOT / r.IOS_PERMISSION_SOURCE).read_text()
        self.assertNotIn("Dispatchers.setMain(", source)
        self.assertIn("Dispatchers.Main.immediate", source)
        self.assertIn("NSRunLoop.mainRunLoop.runUntilDate", source)
        self.assertIn("dispatch_async(dispatch_get_global_queue", source)
        self.assertIn("dispatch_async(dispatch_get_main_queue()) { mainDeliveries++ }", source)
        self.assertIn("secondHelper.mainDeliveries == 2", source)
        self.assertIn("registry.observerCount", source)


if __name__ == "__main__":
    unittest.main()
