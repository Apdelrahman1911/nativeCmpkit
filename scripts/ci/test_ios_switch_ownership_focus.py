"""Synthetic finite-selection/receipt guards, not native switch executions."""
from collections import Counter
import copy
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_application_receipts as receipts
import workflow_matrix as m


class IOSSwitchOwnershipFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_SWITCH_OWNERSHIP_FOCUS)

    def collect(self, identities=None, outcome="", markers=1):
        plan = self.plan()
        identities = r.ui_application_focus_identities(r.IOS_SWITCH_OWNERSHIP_FOCUS) if identities is None else identities
        xml = "<testsuite>" + "".join(
            f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>'
            for c in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / plan["expected"][0]["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-synthetic.xml").write_text(xml)
            now = time.time_ns()
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: markers}), host_system="Darwin")

    def test_finite_profile_real_application_and_cli_select_only_three_new_methods(self):
        rows = m.matrix("ios-switch-ownership")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual("ios-iphone", rows[0]["slot"])
        self.assertEqual("calf-ui", rows[0]["test-modules"])
        self.assertEqual(r.IOS_SWITCH_OWNERSHIP_FOCUS, rows[0]["test-focus"])
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual("genuine-uikit-application", plan["expected"][0]["native_test_host"])
        selectors = [value for name in r.IOS_SWITCH_OWNERSHIP_METHODS
                     for value in ("--tests", r.IOS_SWITCH_OWNERSHIP_CLASS + "." + name)]
        self.assertEqual(selectors, r.gradle_command(
            "ios", plan, simulator="00000000-0000-4000-8000-000000000001")[-6:])
        process = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                  "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_SWITCH_OWNERSHIP_FOCUS],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(3, self.collect()["totals"]["passed"])
        self.assertEqual([], self.collect()["errors"])
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_SWITCH_OWNERSHIP_FOCUS)

    def test_valid_temporary_host_precedes_declaration_drift_and_missing_host_rejection(self):
        source = (r.ROOT / r.IOS_SWITCH_OWNERSHIP_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-ui",\n)\n')
            (root / "calf-ui").mkdir()
            (root / "calf-ui/build.gradle.kts").write_text("// synthetic build, never executed\n")
            for relative in r.IOS_APPLICATION_SOURCES:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((r.ROOT / relative).read_bytes())
            target = root / r.IOS_SWITCH_OWNERSHIP_SOURCE
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
            self.assertTrue(r.validate_test_focus(self.plan(root)))
            for changed in (source.replace(r.IOS_SWITCH_OWNERSHIP_METHODS[0], "wrongMethod", 1),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun unrelated() {}\n"):
                target.write_text(changed)
                with self.assertRaises(ValueError):
                    self.plan(root)
            target.write_text(source)
            self.assertTrue(r.validate_test_focus(self.plan(root)))
            (root / r.IOS_APPLICATION_SOURCES[0]).unlink()
            with self.assertRaises(ValueError):
                self.plan(root)

    def test_exact_kgp_filters_and_xml_reject_missing_duplicate_foreign_failed_or_skipped_cases(self):
        args = sorted(app.TEST_ARGUMENTS)
        prefix = "--ktest_gradle_filter="
        methods = r.ui_application_focus_filter(r.IOS_SWITCH_OWNERSHIP_FOCUS).split(",")
        for selected in (methods, list(reversed(methods))):
            self.assertEqual(r.IOS_SWITCH_OWNERSHIP_FOCUS,
                             app.application_test_focus(args + [prefix + ",".join(selected)]))
        for selected in (methods[:-1], methods * 2, [*methods, "other"], [*methods[:-1], "*"]):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                app.application_test_focus(args + [prefix + ",".join(selected)])
        original = r.ui_application_focus_identities(r.IOS_SWITCH_OWNERSHIP_FOCUS)
        for identities in ([], original[:-1], original * 2,
                           [*original, {"classname": original[0]["classname"], "name": "unrelated"}]):
            self.assertTrue(self.collect(identities)["errors"])
        for key, value in (("classname", r.IOS_SWITCH_OWNERSHIP_CLASS), ("name", r.IOS_SWITCH_OWNERSHIP_METHODS[0]),
                           ("name", r.IOS_SWITCH_OWNERSHIP_METHODS[0] + "[iosArm64]")):
            changed = copy.deepcopy(original)
            changed[0][key] = value
            self.assertTrue(self.collect(changed)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])

    def test_three_cases_still_require_original_application_protocol_worker_and_owned_cleanup(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        f.write(r.IOS_SWITCH_OWNERSHIP_SOURCE, (r.ROOT / r.IOS_SWITCH_OWNERSHIP_SOURCE).read_bytes())
        f.plan = self.plan(f.root)
        f.cases = [{"classname": r.IOS_SWITCH_OWNERSHIP_CLASS, "name": name, "status": "passed"}
                   for name in r.IOS_SWITCH_OWNERSHIP_METHODS]
        f.document["explicit_test_focus"] = r.IOS_SWITCH_OWNERSHIP_FOCUS
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(3, accepted["ios_applications"][0]["counts"]["passed"])
        for key in ("owned_app_stopped_verified", "owned_local_bundle_removed", "owned_app_absence_verified"):
            f.document["cleanup"][key] = False
            f.save()
            self.assertTrue(f.collect()["errors"])
            f.document["cleanup"][key] = True
        f.document["application_protocol"]["completion"]["worker_terminated"] = False
        f.save()
        self.assertTrue(f.collect()["errors"])
