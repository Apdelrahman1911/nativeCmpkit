"""Focused JavaFX stop/window CI guards; these are not native runtime tests."""
from pathlib import Path
import unittest

import library_tests as runner
import native_test_policy as policy
import workflow_matrix as matrix


class DesktopWebViewStopTests(unittest.TestCase):
    def cases(self):
        return [{"classname": "com.mohamedrejeb.calf.ui.web.JavaFxWebViewTest",
                 "name": name + "[desktop]", "status": "passed"}
                for name in ("stopCancelsRealSlowLoadWithoutFeedbackLoop",
                             "repeatedStopsAfterDetachAndReattachCancelOnlyTheCurrentRealLoad")]

    def test_one_desktop_webview_slot_without_replaying_other_suites(self):
        rows = matrix.matrix("webview-desktop")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("desktop-linux-x64", rows[0]["slot"])
        self.assertEqual("desktop", rows[0]["suite"])
        self.assertEqual("ubuntu-24.04", rows[0]["runner"])
        self.assertEqual("calf-webview", rows[0]["test-modules"])
        for profile in ("core", "browser", "apple", "windows", "all"):
            self.assertTrue(all("test-modules" not in row for row in matrix.matrix(profile)["include"]))
        plan = runner.plan(runner.ROOT, "desktop", only_modules=("calf-webview",))
        self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
        self.assertEqual(["calf-webview"], [item["module"] for item in plan["expected"]])
        self.assertFalse(plan["complete_suite_requested"])

    def test_both_actual_native_cases_are_required_on_each_desktop_host(self):
        for system in ("Linux", "Darwin", "Windows"):
            scenarios, errors = policy.apply("calf-webview", "desktop", self.cases(), system, False)
            self.assertEqual([], errors)
            self.assertEqual(2, len(scenarios))
            self.assertTrue(all(row["required_on_host"] and row["disposition"] == "required-executed"
                                for row in scenarios))

    def test_missing_duplicate_skipped_failed_or_wrong_identity_cannot_be_green(self):
        for defect in ("missing", "duplicate", "skipped", "failure", "error", "wrong-class", "wrong-target"):
            with self.subTest(defect=defect):
                cases = self.cases()
                if defect == "missing":
                    cases.pop()
                elif defect == "duplicate":
                    cases.append(dict(cases[-1]))
                elif defect == "wrong-class":
                    cases[-1]["classname"] = "unrelated.NativeWindowTest"
                elif defect == "wrong-target":
                    cases[-1]["name"] = cases[-1]["name"].replace("[desktop]", "[iosSimulatorArm64]")
                else:
                    cases[-1]["status"] = defect
                before = [dict(row) for row in cases]
                _, errors = policy.apply("calf-webview", "desktop", cases, "Linux", False)
                self.assertTrue(errors)
                self.assertEqual(before, cases, "Never promote or rewrite actual outcomes")

    def test_source_bound_profile_and_cases_cannot_become_a_compile_or_other_platform_pass(self):
        self.assertEqual(([], []), policy.apply("calf-webview", "js", [], "Linux", False))
        source = runner.ROOT / "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/JavaFxWebViewTest.kt"
        for case in self.cases():
            self.assertIn("fun " + case["name"].removesuffix("[desktop]") + "(", source.read_text())
        workflow = (runner.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("webview-desktop", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)


if __name__ == "__main__":
    unittest.main()
