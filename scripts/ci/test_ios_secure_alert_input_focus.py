"""New finite profile/protocol/JUnit/lifecycle controls, NOT actual UIKit tests.

All native application records, XML and Mach-O objects here are explicitly
synthetic. Ten finite real native methods remain UNEXECUTED: one combined
input/keyboard/masking/no-log method, three original console methods and six
additional console-control methods. This is not physical-device/full-log proof.
"""
from collections import Counter
import copy
from pathlib import Path
import re
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import secure_alert_input_plan as s
import test_ios_application_receipts as receipts
import test_secure_alert_input_plan as bindings
import workflow_matrix as matrix


def _secure_alert_profile_options(workflow):
    """Require literal, unique choices, not adjacency to unrelated profiles."""
    declaration, = [line for line in workflow.splitlines()
                    if line.startswith("        options: [") and line.endswith("]")]
    choices = [value.strip() for value in declaration.split("[", 1)[1][:-1].split(",")]
    if (any(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None for value in choices)
            or len(choices) != len(set(choices))
            or any(choices.count(profile) != 1
                   for profile in ("ios-ui", "ios-secure-alert-input", "ios-date-bounds"))):
        raise ValueError("Secure alert requires its three distinct literal workflow profile choices")
    return choices


class SecureAlertProfileOptionsTests(unittest.TestCase):
    def test_related_profile_insertions_and_reordering_do_not_change_secure_alert_admission(self):
        for choices in (
            "ios-ui, ios-secure-alert-input, ios-date-bounds",
            "ios-ui, ios-ui-adaptive-pre26, ios-ui-adaptive-drag-shader-ios26plus, ios-secure-alert-input, ios-date-bounds",
            "ios-date-bounds, ios-ui-adaptive-pre26, ios-secure-alert-input, ios-ui",
        ):
            self.assertIn("ios-secure-alert-input", _secure_alert_profile_options("        options: [" + choices + "]"))

    def test_missing_duplicate_ambiguous_or_nonliteral_profile_choices_refuse(self):
        required = ["ios-ui", "ios-secure-alert-input", "ios-date-bounds"]
        valid = "        options: [" + ", ".join(required) + "]"
        malformed = [valid + "\n" + valid, valid.replace("ios-ui", '"ios-ui"', 1), "        options: []"]
        malformed += ["        options: [" + ", ".join(required[:index] + required[index + 1:]) + "]" for index in range(3)]
        malformed += ["        options: [" + ", ".join(required + [profile]) + "]" for profile in required]
        for workflow in malformed:
            with self.subTest(workflow=workflow), self.assertRaises(ValueError):
                _secure_alert_profile_options(workflow)


class IosSecureAlertInputFocusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        bindings.populate_bound_source_root(self.root)
        self.plan = r.plan(self.root, "ios", only_modules=(s.MODULE,), focus=s.FOCUS)

    def collect_xml(self, identities=None, outcome="", marker=1):
        identities = r.ui_application_focus_identities(s.FOCUS) if identities is None else identities
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / self.plan["expected"][0]["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-explicitly-synthetic.xml").write_text("<testsuite>" + "".join(
                f'<testcase classname="{case["classname"]}" name="{case["name"]}">{outcome}</testcase>'
                for case in identities) + "</testsuite>")
            now = time.time_ns()
            return r.collect_reports(root, self.plan, now - 1_000_000_000, now + 1_000_000_000,
                Counter({self.plan["expected"][0]["task"]: marker}), host_system="Darwin")

    def application_fixture(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        for relative in (*s.QUALIFIED_SOURCE_SHA256, s.SCREEN, s.BUILD):
            f.write(relative, (r.ROOT / relative).read_bytes())
        f.plan = r.plan(f.root, "ios", only_modules=(s.MODULE,), focus=s.FOCUS)
        f.cases = [{"classname": group["classname"], "name": method, "status": "passed"}
                   for group in r.ui_application_focus_groups(s.FOCUS) for method in group["methods"]]
        f.document["explicit_test_focus"] = s.FOCUS
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        return f

    def test_one_new_iphone_profile_exact_ten_methods_no_old_ui_or_sample_tests_or_write_permissions(self):
        row, = matrix.matrix(s.PROFILE)["include"]
        self.assertEqual(("ios-iphone", s.MODULE, s.FOCUS), tuple(row[key] for key in ("slot", "test-modules", "test-focus")))
        self.assertFalse(self.plan["complete_suite_requested"])
        self.assertEqual("genuine-uikit-application", self.plan["expected"][0]["native_test_host"])
        self.assertTrue(r.validate_test_focus(self.plan))
        self.assertEqual(10, len(self.plan["expected"][0]["required_testcases"]))
        filters = r.ui_application_focus_filter(s.FOCUS).split(",")
        self.assertEqual([s.NATIVE_CLASS + "." + s.NATIVE_METHODS[0]] + [s.CAPTURE_CLASS + "." + name for name in s.CAPTURE_METHODS], filters)
        self.assertNotIn("NativeAlertLifecycleTest", ",".join(filters))
        self.assertNotIn("sample", ",".join(filters))
        command = r.gradle_command("ios", self.plan, simulator="11111111-1111-1111-1111-111111111111")
        self.assertEqual([part for value in filters for part in ("--tests", value)], command[-2 * len(filters):])
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(s.PROFILE, _secure_alert_profile_options(workflow))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        for suite, modules in (("desktop", (s.MODULE,)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): r.plan(self.root, suite, only_modules=modules, focus=s.FOCUS)

    def test_actual_source_only_cli_preflight_has_exact_focus_and_does_not_run_gradle(self):
        result = subprocess.run([r.sys.executable, "-B", str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
            "--suite", "ios", "--module", s.MODULE, "--focus", s.FOCUS],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, "The exact source-only CLI prerequisite refused")
        preflight = matrix.preflight_plans(s.PROFILE)
        self.assertTrue(preflight["source_only"])
        self.assertEqual(0, preflight["Gradle_builds_executed"])
        self.assertEqual(0, preflight["library_tests_executed"])
        slot, = preflight["slots"]
        self.assertEqual(0, slot["exit_code"])
        self.assertEqual(s.FOCUS, slot["command"][slot["command"].index("--focus") + 1])
        self.assertEqual("plan", slot["command"][3])

    def test_exact_native_filters_accept_only_ten_unique_methods_and_keep_full_protocol_unchanged(self):
        filters = r.ui_application_focus_filter(s.FOCUS).split(",")
        for selected in (filters, list(reversed(filters))):
            self.assertEqual(s.FOCUS, app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selected)]))
        self.assertIsNone(app.application_test_focus(sorted(app.TEST_ARGUMENTS)))
        for selected in (filters[:-1], filters * 2, [*filters, "other"], [*filters[:-1], "*"]):
            with self.assertRaises(ValueError): app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(selected)])
        with self.assertRaises(ValueError): app.application_test_focus(sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(filters), "--ktest_gradle_filter=*"])
        self.assertEqual(app.APP_TIMEOUT_SECONDS, app.application_timeout_seconds(s.FOCUS))

    def test_green_xml_cannot_omit_duplicate_add_foreign_target_fail_skip_or_avoid_real_task_marker(self):
        identities = r.ui_application_focus_identities(s.FOCUS)
        accepted = self.collect_xml(identities)
        self.assertEqual([], accepted["errors"])
        self.assertEqual(10, accepted["totals"]["passed"])
        for selected in ([], identities[:-1], identities * 2,
            [*identities, {**identities[0], "name": "public-foreign-case"}],
            [{**identities[0], "name": identities[0]["name"].replace("[iosSimulatorArm64]", "[iosArm64]")}, *identities[1:]],
            [{**identities[0], "classname": s.NATIVE_CLASS}, *identities[1:]]):
            self.assertTrue(self.collect_xml(selected)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(self.collect_xml(outcome=outcome)["errors"])
        self.assertTrue(self.collect_xml(marker=0)["errors"])

    def test_ten_synthetic_cases_still_require_original_owned_worker_transport_runtime_and_cleanup_gates(self):
        f = self.application_fixture()
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(10, accepted["ios_applications"][0]["counts"]["passed"])
        original = copy.deepcopy(f.document)
        for key in ("owned_app_stopped_verified", "owned_app_absence_verified", "owned_local_bundle_removed"):
            f.document = copy.deepcopy(original)
            f.document["cleanup"][key] = False
            f.save(); self.assertTrue(f.collect()["errors"])
        for field, value in (("worker_terminated", False), ("runner_exit", 1)):
            f.document = copy.deepcopy(original)
            f.document["application_protocol"]["completion"][field] = value
            f.save(); self.assertTrue(f.collect()["errors"])
        f.document = copy.deepcopy(original)
        f.document["runtime_after"]["source_revision"] = "0" * 40
        f.save(); self.assertTrue(f.collect()["errors"])
        f.document = copy.deepcopy(original)
        f.document["packages_published"] = True
        f.save(); self.assertTrue(f.collect()["errors"])

    def test_matching_synthetic_protocol_and_xml_cannot_relabel_scope_or_drop_any_capture_control(self):
        f = self.application_fixture()
        self.assertEqual([], f.collect()["errors"])
        original = copy.deepcopy(f.document)
        original_cases = copy.deepcopy(f.cases)
        for index in range(10):
            cases = original_cases[:index] + original_cases[index + 1:]
            f.document = copy.deepcopy(original)
            f.document["application_protocol"]["testcases"] = cases
            f.document["application_protocol"]["counts"] = r.case_counts(cases)
            f.modules[0]["testcases"] = f.xml_cases(cases)
            f.save(); self.assertTrue(f.collect()["errors"])
        f.document = copy.deepcopy(original)
        f.modules[0]["testcases"] = f.xml_cases(original_cases)
        f.document["explicit_test_focus"] = r.UI_DATE_BOUNDS_FOCUS
        f.save(); self.assertTrue(f.collect()["errors"])
