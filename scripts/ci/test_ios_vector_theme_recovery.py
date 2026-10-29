"""Finite serial recovery/unchanged-assertion guards; zero native executions."""
from pathlib import Path
import json
import subprocess
import unittest

import library_tests as tests
import workflow_matrix as matrix
import ios_ui_application as app
import test_ios_application_receipts as receipts


class IosVectorThemeRecoveryTests(unittest.TestCase):
    def test_rendering_only_recovery_never_replays_accepted_theme_methods(self):
        row, = matrix.matrix("ios-vector-rendering-recovery")["include"]
        self.assertEqual("ios-ipad", row["slot"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(tests.IOS_VECTOR_RENDERING_FOCUS, row["test-focus"])
        self.assertNotIn("serial-test-focus", row)
        preflight = matrix.preflight_plans("ios-vector-rendering-recovery")
        self.assertEqual(1, len(preflight["slots"]))
        self.assertEqual(1, len(tests.ui_application_focus_identities(row["test-focus"])))
        self.assertNotIn("Appearance", tests.ui_application_focus_filter(row["test-focus"]))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def test_requested_snapshot_density_is_bound_to_actual_attached_view_backing(self):
        source = (tests.ROOT / tests.IOS_VECTOR_THEME_SOURCE).read_text()
        method = source.split("@Test fun " + tests.IOS_VECTOR_THEME_METHODS[0], 1)[1].split("@Test fun ", 1)[0]
        attach = method.index("parent.view.addSubview(view)")
        configure = method.index("view.setContentScaleFactor(density.toDouble())")
        capture = method.index("snapshot(view, density)")
        self.assertLess(attach, configure)
        self.assertLess(configure, capture)
        self.assertIn("assertEquals(density.toDouble(), view.contentScaleFactor", method)
        self.assertIn("assertEquals(density.toDouble(), view.layer.contentsScale", method)
        self.assertIn("listOf(2f, 3f)", method)
        self.assertIn("original[channel].toInt() and 255)) <= 3", method)
        self.assertIn("actual[offset + channel].toInt() and 255)) <= 3", method)
        self.assertNotIn("kCAFilterNearest", method)
        self.assertNotIn("return@", method)

    def test_one_host_preflights_two_exact_independent_methods_not_accepted_replay(self):
        row, = matrix.matrix("ios-vector-theme-recovery")["include"]
        self.assertEqual("ios-ipad", row["slot"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(tests.IOS_VECTOR_RENDERING_FOCUS, row["test-focus"])
        self.assertEqual(tests.IOS_SYSTEM_APPEARANCE_FOCUS, row["serial-test-focus"])
        preflight = matrix.preflight_plans("ios-vector-theme-recovery")
        self.assertEqual(2, len(preflight["slots"]))
        self.assertEqual({"ios-ipad"}, {slot["slot"] for slot in preflight["slots"]})
        for slot, focus in zip(preflight["slots"], (tests.IOS_VECTOR_RENDERING_FOCUS, tests.IOS_SYSTEM_APPEARANCE_FOCUS)):
            self.assertEqual(focus, slot["command"][slot["command"].index("--focus") + 1])
            plan = tests.plan(tests.ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            self.assertEqual(1, len(plan["expected"][0]["required_testcases"]))
            self.assertTrue(tests.validate_test_focus(plan))
            self.assertEqual(300, app.application_timeout_seconds(focus))
            self.assertEqual(focus, app.application_test_focus(sorted(app.TEST_ARGUMENTS) +
                ["--ktest_gradle_filter=" + tests.ui_application_focus_filter(focus)]))
            self.assertNotIn("ThemeOwnershipTest", tests.ui_application_focus_filter(focus))
            self.assertNotIn("UIImageConversionTest", tests.ui_application_focus_filter(focus))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertTrue(all("serial-test-focus" not in r for r in matrix.matrix("all")["include"]))

    def test_each_new_focus_still_requires_native_runtime_worker_binary_xml_and_cleanup(self):
        for focus in (tests.IOS_VECTOR_RENDERING_FOCUS, tests.IOS_SYSTEM_APPEARANCE_FOCUS):
            fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
            fixture.setUp()
            try:
                fixture.write(tests.IOS_VECTOR_THEME_SOURCE, (tests.ROOT / tests.IOS_VECTOR_THEME_SOURCE).read_bytes())
                fixture.plan = tests.plan(fixture.root, "ios", only_modules=("calf-ui",), focus=focus)
                method = tests.IOS_VECTOR_THEME_METHODS[0 if focus == tests.IOS_VECTOR_RENDERING_FOCUS else -1]
                cases = [{"classname": tests.IOS_VECTOR_THEME_CLASS, "name": method, "status": "passed"}]
                fixture.document["explicit_test_focus"] = focus
                fixture.document["application_protocol"].update(testcases=cases, counts=tests.case_counts(cases))
                fixture.modules[0]["testcases"] = fixture.xml_cases(cases)
                fixture.save()
                self.assertEqual([], fixture.collect()["errors"])
                fixture.document["application_protocol"]["completion"]["worker_terminated"] = False
                fixture.save()
                self.assertTrue(fixture.collect()["errors"])
            finally:
                fixture.doCleanups()

    def test_failed_first_check_does_not_skip_second_but_missing_xml_or_cleanup_does(self):
        workflow = (tests.ROOT / ".github/workflows/gradle.yml").read_text()
        first = workflow.index("name: Preserve first fresh XML")
        second = workflow.index("name: Independent related native subset")
        last = workflow.index("name: Preserve second fresh XML")
        self.assertLess(first, second); self.assertLess(second, last)
        block = workflow[second:last]
        self.assertIn("!cancelled() && steps.serial_archive.outcome == 'success'", block)
        self.assertNotIn("success()", block)
        self.assertIn('"build/ci-verification/$SLOT-related-recovery"', block)
        self.assertIn("--reserve-mib 8192", block)
        self.assertIn("/fresh-reports/*.xml", workflow)
        self.assertIn("-related-recovery/native-ui-application/*/receipt.json", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("packages: write", workflow)

    def test_pixel_failure_diagnostics_preserve_every_original_hierarchy_and_template_assertion(self):
        source = (tests.ROOT / tests.IOS_VECTOR_THEME_SOURCE).read_text()
        self.assertEqual(5, source.count("@Test fun "))
        self.assertIn("source.indices.forEach { channel ->", source)
        self.assertIn("original[channel].toInt() and 255)) <= 3", source)
        self.assertIn("for (offset in source.indices step 4)", source)
        self.assertIn("actual[offset + channel].toInt() and 255)) <= 3", source)
        self.assertIn("view.drawViewHierarchyInRect(view.bounds, afterScreenUpdates = false)", source)
        self.assertIn("view.layer.renderInContext", source)
        self.assertIn("hierarchy=${original[channel].toInt() and 255}, layer=${isolated[channel].toInt() and 255}", source)
        self.assertIn("listOf(2f, 3f)", source)
        self.assertNotIn("Assume.", source)
        self.assertNotIn("return@forEach", source)


if __name__ == "__main__":
    unittest.main()
