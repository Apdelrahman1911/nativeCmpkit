"""PRIVATE source proposal. New synthetic guards only; no fixture has run.

These prospective tooling methods never execute Kotlin, UIKit, Gradle, native
input, target controllers, CI reacquisition or an accepted test body.
"""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import ios_ui_application as app
import library_tests as r
import workflow_matrix as matrix


class AlertYearImportantFocus(unittest.TestCase):
    def plan(self, suite="ios", red=False):
        focus = (r.UI_DATE_YEAR_MATERIAL_FOCUS if suite == "desktop" else
                 r.UI_DATE_YEAR_PREDICATE_RED_FOCUS if red else r.UI_ALERT_DATE_IMPORTANT_FOCUS)
        return r.plan(r.ROOT, suite, only_modules=("calf-ui",), focus=focus)

    def test_exact_new_ten_native_two_material_and_optional_red_one_are_finite(self):
        for suite, red, count, task in (
            ("ios", False, 10, ":calf-ui:iosSimulatorArm64ApplicationTest"),
            ("desktop", False, 2, ":calf-ui:desktopTest"),
            ("ios", True, 1, ":calf-ui:iosSimulatorArm64ApplicationTest"),
        ):
            plan = self.plan(suite, red)
            self.assertTrue(r.validate_test_focus(plan))
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(["calf-ui"], plan["explicit_module_subset"])
            item, = plan["expected"]
            self.assertEqual(task, item["task"])
            self.assertEqual(count, len(item["required_testcases"]))
            self.assertIn(r.UI_DATE_YEAR_SHARED_SOURCE, item["test_source_files"])
            if suite == "ios":
                self.assertEqual("genuine-uikit-application", item["native_test_host"])
            self.assertTrue(all("NativeAlertLifecycleTest" not in case["classname"] and
                                "NativeDateBoundsAcceptanceTest" not in case["classname"] and
                                "NativeDropDownLifecycleTest" not in case["classname"]
                                for case in item["required_testcases"]))

    def test_one_fixed_host_preflights_both_real_suite_selectors_without_new_runner(self):
        row, = matrix.matrix("ios-alert-date-important")["include"]
        self.assertEqual(("ios-iphone", "macos-26", "arm64", "calf-ui"),
                         (row["slot"], row["runner"], row["arch"], row["test-modules"]))
        self.assertEqual(r.UI_ALERT_DATE_IMPORTANT_FOCUS, row["test-focus"])
        self.assertNotIn("serial-test-focus", row) # Not a second UIKit application.
        red_row, = matrix.matrix("ios-date-year-predicate-red")["include"]
        self.assertEqual(r.UI_DATE_YEAR_PREDICATE_RED_FOCUS, red_row["test-focus"])
        self.assertEqual(("ios-iphone", "macos-26", "arm64", "calf-ui"),
                         (red_row["slot"], red_row["runner"], red_row["arch"], red_row["test-modules"]))
        commands = []
        def fake_run(command, **kwargs):
            commands.append(command)
            suite = command[command.index("--suite") + 1]
            focus = command[command.index("--focus") + 1]
            return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps(
                r.plan(r.ROOT, suite, only_modules=("calf-ui",), focus=focus)))
        with patch.object(matrix.subprocess, "run", side_effect=fake_run):
            matrix.preflight_plans("ios-alert-date-important", r.ROOT)
        self.assertEqual([("ios", r.UI_ALERT_DATE_IMPORTANT_FOCUS),
                          ("desktop", r.UI_DATE_YEAR_MATERIAL_FOCUS)],
                         [(command[command.index("--suite") + 1], command[command.index("--focus") + 1])
                          for command in commands])
        for profile in ("all", "ios", "ios-ui", "extended"):
            self.assertTrue(all("test-focus" not in item for item in matrix.matrix(profile)["include"]))
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        material = workflow.split("      - name: Plan two new Material year-policy companions on the same host", 1)[1]
        material = material.split("      - name: Preserve first fresh XML before the related same-host recovery", 1)[0]
        for literal in ("steps.plan.outcome == 'success'", "inputs.profile == 'ios-alert-date-important'",
                        "steps.material_year_plan.outcome == 'success'", "--suite desktop --module calf-ui",
                        "--focus ui-material-year-policy-important", "$SLOT-material-year", "--reserve-mib 8192"):
            self.assertIn(literal, material)
        self.assertNotIn("--simulator", material)
        self.assertNotIn("continue-on-error", material)
        self.assertIn("${{ steps.material_year_plan.outputs.reports }}", workflow)

    def test_gradle_and_native_arguments_cannot_select_old_or_arbitrary_methods(self):
        for suite in ("ios", "desktop"):
            plan = self.plan(suite)
            command = r.gradle_command(suite, plan,
                "11111111-1111-1111-1111-111111111111" if suite == "ios" else None)
            actual = [command[index + 1] for index, value in enumerate(command) if value == "--tests"]
            item, = plan["expected"]
            expected = item["test_filter"].split(",") if suite == "ios" else [item["test_filter"]]
            self.assertEqual(expected, actual)
            self.assertEqual([item["task"]], [value for value in command if value.startswith(":")])
        full = sorted(app.TEST_ARGUMENTS)
        selector = r.ui_application_focus_filter(r.UI_ALERT_DATE_IMPORTANT_FOCUS)
        self.assertEqual(r.UI_ALERT_DATE_IMPORTANT_FOCUS,
                         app.application_test_focus(full + ["--ktest_gradle_filter=" + selector]))
        # Old reviewed focuses remain valid globally; the new Gradle plan
        # cannot reinterpret them as this new ten-method application selector.
        self.assertEqual(r.UI_DATE_BOUNDS_FOCUS, app.application_test_focus(
            full + ["--ktest_gradle_filter=" + r.UI_DATE_BOUNDS_CLASS]))
        for value in ("*", selector + ",unrelated",
                      selector.replace(r.UI_ALERT_IMPORTANT_METHODS[0], "unknown", 1)):
            with self.assertRaises(ValueError):
                app.application_test_focus(full + ["--ktest_gradle_filter=" + value])

    def test_wrong_module_scope_task_host_filter_or_inventory_is_refused(self):
        for suite, focus in (("desktop", r.UI_ALERT_DATE_IMPORTANT_FOCUS),
                             ("ios", r.UI_DATE_YEAR_MATERIAL_FOCUS)):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=("calf-ui",), focus=focus)
        for suite in ("ios", "desktop"):
            focus = self.plan(suite)["explicit_test_focus"]
            for modules in (None, ("calf-io",), ("calf-ui", "calf-io")):
                with self.assertRaises(ValueError):
                    r.plan(r.ROOT, suite, only_modules=modules, focus=focus)
            for section, key, value in (("plan", "complete_suite_requested", True),
                                        ("item", "test_filter", "*"),
                                        ("item", "required_testcases", []),
                                        ("item", "test_source_files", []),
                                        ("item", "task", ":calf-ui:iosSimulatorArm64Test")):
                plan = copy.deepcopy(self.plan(suite))
                (plan if section == "plan" else plan["expected"][0])[key] = value
                with self.assertRaises(ValueError):
                    r.validate_test_focus(plan)

    def test_new_source_drift_or_disabled_native_declarations_cannot_reduce_selection(self):
        groups = r.ui_application_focus_groups(r.UI_ALERT_DATE_IMPORTANT_FOCUS)
        groups += ({"source": r.UI_DATE_YEAR_MATERIAL_SOURCE, "methods": r.UI_DATE_YEAR_MATERIAL_METHODS},)
        for group in groups:
            source = (r.ROOT / group["source"]).read_text()
            real_read = Path.read_text
            for value in (source.replace(group["methods"][0], "differentMethod", 1),
                          source.replace("@Test fun", "fun", 1),
                          source + "\n@Test fun extraMethod() {}\n",
                          source.replace("@Test fun", "@Ignore @Test fun", 1)):
                # Keep every discovered source path real and owned. Substituting
                # an outside temporary path would test relative_to(root) instead
                # of the actual owning declaration/refusal boundary.
                def changed_read(path, *args, **kwargs):
                    return value if path == r.ROOT / group["source"] else real_read(path, *args, **kwargs)
                with patch.object(Path, "read_text", new=changed_read), self.assertRaisesRegex(ValueError,
                        "Native date declarations changed|New important alert/year source|New important Material year declarations changed"):
                    self.plan("desktop" if group["source"] == r.UI_DATE_YEAR_MATERIAL_SOURCE else "ios")

    def test_owned_accessibility_helper_has_no_dismiss_or_private_handler_fallback(self):
        source = (r.ROOT / r.UI_ALERT_IMPORTANT_SOURCE).read_text()
        body = source.split("private fun NativeApplicationUiTest.activateImportantNativeAction", 1)[1]
        for required in ("requireOwnedApplicationWindow()", "sameNativeObject(alert.view.window, window)",
                         "assertTrue(action.enabled", "UIAccessibilityTraitButton",
                         "assertEquals(1, eligible.size", "accessibilityActivate()"):
            self.assertIn(required, body)
        for forbidden in (".activateAction(", ".dismiss(", "performSelector", "valueForKey", "setValue(",
                          "UITouch(", "UIEvent(", "NSClassFromString"):
            self.assertNotIn(forbidden, body)
        owner = (r.ROOT / "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/datepicker/AdaptiveDatePicker.ios.kt").read_text()
        resolver = owner.split("resolveSelection = { pickedMillis ->", 1)[1].split("},", 1)[0]
        self.assertIn(".takeIf { state.isDaySelectable(it) } ?: state.selectedDateMillis", resolver)
        self.assertNotIn(".takeIf { utcYearOf(it) in state.yearRange }", resolver)

    def collect(self, suite, cases, marker=1, age=0, extra_empty=False):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            report = root / plan["expected"][0]["report_directory"]
            report.mkdir(parents=True)
            grouped = {}
            for case in cases:
                grouped.setdefault(case["classname"], []).append(case)
            for index, group in enumerate(grouped.values()):
                # These are prospective XML node names. The actual parser maps
                # <failure> to status="failed"; never guess case_counts keys.
                totals = Counter(case.get("status", "passed") for case in group)
                xml = ET.Element("testsuite", tests=str(len(group)), failures=str(totals["failure"]),
                                 errors=str(totals["error"]), skipped=str(totals["skipped"]))
                for case in group:
                    node = ET.SubElement(xml, "testcase", classname=case["classname"], name=case["name"])
                    if case.get("status") in ("failure", "error", "skipped"):
                        ET.SubElement(node, case["status"])
                path = report / ("TEST-synthetic-" + str(index) + ".xml")
                path.write_bytes(ET.tostring(xml))
                now = time.time_ns()
                os.utime(path, ns=(now - age, now - age))
            if extra_empty:
                (report / "TEST-synthetic-empty.xml").write_bytes(ET.tostring(
                    ET.Element("testsuite", tests="0", failures="0", errors="0", skipped="0")))
            now = time.time_ns()
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: marker}), host_system="Darwin")

    def test_exact_fresh_xml_has_each_new_case_and_its_owning_source(self):
        for suite, count in (("ios", 10), ("desktop", 2)):
            cases = [{**case, "status": "passed"} for case in self.plan(suite)["expected"][0]["required_testcases"]]
            result = self.collect(suite, cases)
            self.assertEqual([], result["errors"])
            self.assertEqual(count, result["totals"]["passed"])
            expected_sources = ({r.UI_ALERT_IMPORTANT_SOURCE, r.UI_DATE_YEAR_NATIVE_SOURCE} if suite == "ios"
                                else {r.UI_DATE_YEAR_MATERIAL_SOURCE})
            self.assertEqual(expected_sources, {case["source"] for case in result["modules"][0]["native_scenarios"]})

    def test_missing_duplicate_foreign_failed_skipped_stale_or_zero_xml_never_passes(self):
        for suite in ("ios", "desktop"):
            cases = [{**case, "status": "passed"} for case in self.plan(suite)["expected"][0]["required_testcases"]]
            for changed in (cases[:-1], cases + [cases[0]],
                            [{**cases[0], "classname": "foreign"}, *cases[1:]],
                            [{**cases[0], "status": "failure"}, *cases[1:]],
                            [{**cases[0], "status": "error"}, *cases[1:]],
                            [{**cases[0], "status": "skipped"}, *cases[1:]]):
                self.assertTrue(self.collect(suite, changed)["errors"])
            self.assertTrue(self.collect(suite, cases, marker=0)["errors"])
            self.assertTrue(self.collect(suite, cases, marker=2)["errors"])
            self.assertTrue(self.collect(suite, cases, age=10_000_000_000)["errors"])
            self.assertTrue(self.collect(suite, cases, age=-10_000_000_000)["errors"])
            self.assertTrue(self.collect(suite, cases, extra_empty=True)["errors"])


if __name__ == "__main__":
    unittest.main()
