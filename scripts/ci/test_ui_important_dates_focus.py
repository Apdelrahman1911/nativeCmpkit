"""Four failed + three new finite date guards. Synthetic tooling, not native tests."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as r
import test_ios_application_receipts as receipts
import test_ui_date_bounds_focus as bounds
import workflow_matrix as matrix


class ImportantDateFocus(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_IMPORTANT_FOCUS)

    def collect(self, cases=None, **kwargs):
        fixture = bounds.DateBoundsFocus()
        fixture.plan = self.plan
        return fixture.collect(r.ui_application_focus_identities(r.UI_DATE_IMPORTANT_FOCUS)
                               if cases is None else cases, **kwargs)

    def test_one_real_iphone_application_replays_only_four_failed_plus_three_new_methods(self):
        row, = matrix.matrix("ios-dates-important")["include"]
        self.assertEqual("ios-iphone", row["slot"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(r.UI_DATE_IMPORTANT_FOCUS, row["test-focus"])
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(":calf-ui:" + r.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(7, len(item["required_testcases"]))
        groups = r.ui_application_focus_groups(r.UI_DATE_IMPORTANT_FOCUS)
        self.assertEqual([4, 3], [len(g["methods"]) for g in groups])
        self.assertEqual(r.UI_DATE_BOUNDS_METHODS[2:], groups[0]["methods"])
        for passed in r.UI_DATE_BOUNDS_METHODS[:2]:
            self.assertNotIn(passed, item["test_filter"])

    def test_each_exact_method_has_its_own_gradle_include_pattern(self):
        command = r.gradle_command("ios", self.plan(), simulator="00000000-0000-4000-8000-000000000001")
        selectors = r.ui_application_focus_filter(r.UI_DATE_IMPORTANT_FOCUS).split(",")
        self.assertEqual(7, command.count("--tests"))
        self.assertEqual([part for value in selectors for part in ("--tests", value)], command[-14:])
        self.assertEqual([":calf-ui:" + r.IOS_APPLICATION_TASK], [v for v in command if v.startswith(":")])

    def test_transport_accepts_the_exact_method_set_in_kgp_set_order(self):
        full = sorted(app.TEST_ARGUMENTS)
        selectors = r.ui_application_focus_filter(r.UI_DATE_IMPORTANT_FOCUS).split(",")
        for ordered in (selectors, list(reversed(selectors)), sorted(selectors)):
            argument = "--ktest_gradle_filter=" + ",".join(ordered)
            self.assertEqual(r.UI_DATE_IMPORTANT_FOCUS, app.application_test_focus(full + [argument]))

    def test_missing_duplicate_unreviewed_wildcard_or_accepted_method_is_rejected(self):
        full = sorted(app.TEST_ARGUMENTS)
        selectors = r.ui_application_focus_filter(r.UI_DATE_IMPORTANT_FOCUS).split(",")
        invalid = (selectors[:-1], selectors + [selectors[0]], selectors + ["other"],
                   ["*", *selectors[1:]],
                   [r.UI_DATE_BOUNDS_CLASS + "." + r.UI_DATE_BOUNDS_METHODS[0], *selectors[1:]],
                   [r.UI_DATE_BOUNDS_CLASS, r.UI_DATE_REPLACEMENT_CLASS])
        for patterns in invalid:
            with self.subTest(patterns=patterns), self.assertRaises(ValueError):
                app.application_test_focus(full + ["--ktest_gradle_filter=" + ",".join(patterns)])
        with self.assertRaises(ValueError):
            app.application_test_focus(full + [app.APPLICATION_FOCUS_ARGUMENTS[r.UI_DATE_IMPORTANT_FOCUS],
                                               app.DATE_BOUNDS_ARGUMENT])

    def test_both_full_declaration_inventories_are_guarded_even_for_excluded_passed_methods(self):
        for group in r.ui_application_focus_groups(r.UI_DATE_IMPORTANT_FOCUS):
            source = (r.ROOT / group["source"]).read_text()
            declared = group.get("declared_methods", group["methods"])
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "changed.kt"
                real = r.safe_path
                for changed in (source.replace(declared[0], "differentMethod", 1),
                                source.replace("@Test fun", "fun", 1),
                                source + "\n@Test fun anotherMethod() {}\n"):
                    path.write_text(changed)
                    with patch.object(r, "safe_path", side_effect=lambda root, name:
                                      path if name == group["source"] else real(root, name)), self.assertRaises(ValueError):
                        self.plan()

    def test_wrong_task_host_scope_filter_source_or_inventory_is_rejected(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-io",)), ("ios", None)):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.UI_DATE_IMPORTANT_FOCUS)
        for section, key, value in (("plan", "complete_suite_requested", True),
                                    ("item", "native_test_host", "skiko-only"),
                                    ("item", "task", ":calf-ui:iosSimulatorArm64Test"),
                                    ("item", "test_filter", r.UI_DATE_BOUNDS_CLASS),
                                    ("item", "required_testcases", r.ui_date_bounds_identities()),
                                    ("item", "test_source_files", [])):
            plan = copy.deepcopy(self.plan())
            (plan if section == "plan" else plan["expected"][0])[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(plan)

    def test_exact_seven_xml_cases_match_their_two_owning_sources(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(7, result["totals"]["passed"])
        self.assertEqual({r.UI_DATE_BOUNDS_SOURCE, r.UI_DATE_REPLACEMENT_SOURCE},
                         {case["source"] for case in result["modules"][0]["native_scenarios"]})

    def test_failed_skipped_stale_missing_duplicate_foreign_or_extra_xml_never_passes(self):
        cases = r.ui_application_focus_identities(r.UI_DATE_IMPORTANT_FOCUS)
        for changed in (cases[:-1], [*cases, cases[0]], [*cases, r.ui_date_bounds_identities()[0]],
                        [{**cases[0], "classname": "foreign"}, *cases[1:]]):
            self.assertTrue(self.collect(changed)["errors"])
        for status in ("failure", "error", "skipped"):
            self.assertTrue(self.collect([{**cases[0], "status": status}, *cases[1:]])["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(age=10_000_000_000)["errors"])

    def test_successful_and_complete_profiles_have_not_been_silently_narrowed(self):
        for focus, count in ((r.UI_DATE_BOUNDS_FOCUS, 6), (r.UI_DATE_REPLACEMENT_FOCUS, 3)):
            plan = r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            self.assertEqual(count, len(plan["expected"][0]["required_testcases"]))
        for profile in ("all", "ios", "ios-ui", "extended"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))


class ImportantDateApplicationEvidence(unittest.TestCase):
    def setUp(self):
        self.fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        for group in r.ui_application_focus_groups(r.UI_DATE_IMPORTANT_FOCUS):
            f.write(group["source"], (r.ROOT / group["source"]).read_bytes())
        f.plan = r.plan(f.root, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_IMPORTANT_FOCUS)
        f.cases = [{"classname": group["classname"], "name": method, "status": "passed"}
                   for group in r.ui_application_focus_groups(r.UI_DATE_IMPORTANT_FOCUS) for method in group["methods"]]
        f.document["explicit_test_focus"] = r.UI_DATE_IMPORTANT_FOCUS
        self.sync()

    def sync(self):
        f = self.fixture
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()

    def test_seven_real_application_cases_retain_worker_cleanup_and_runtime_gates(self):
        result = self.fixture.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(7, result["ios_applications"][0]["counts"]["passed"])
        for key in ("owned_app_stopped_verified", "owned_local_bundle_removed", "owned_app_absence_verified"):
            self.fixture.document["cleanup"][key] = False
            self.fixture.save()
            self.assertTrue(self.fixture.collect()["errors"])
            self.fixture.document["cleanup"][key] = True

    def test_matching_green_protocol_xml_cannot_omit_or_add_methods(self):
        original = copy.deepcopy(self.fixture.cases)
        passed = {"classname": r.UI_DATE_BOUNDS_CLASS, "name": r.UI_DATE_BOUNDS_METHODS[0], "status": "passed"}
        for changed in (original[:-1], [*original, passed], [*original, original[0]]):
            self.fixture.cases = changed
            self.sync()
            self.assertTrue(self.fixture.collect()["errors"])

    def test_transport_selection_and_full_suite_claims_cannot_be_substituted(self):
        self.fixture.document["explicit_test_focus"] = r.UI_DATE_BOUNDS_FOCUS
        self.fixture.save()
        self.assertTrue(self.fixture.collect()["errors"])
        self.fixture.document["explicit_test_focus"] = None
        self.fixture.save()
        self.assertTrue(self.fixture.collect()["errors"])
        self.fixture.plan.pop("explicit_test_focus")
        for item in self.fixture.plan["expected"]:
            item.pop("test_filter")
            item.pop("required_testcases")
        self.assertTrue(self.fixture.collect()["errors"], "Seven date methods are not the full native UI suite")


if __name__ == "__main__":
    unittest.main()
