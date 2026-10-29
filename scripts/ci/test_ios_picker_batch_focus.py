"""Finite related-picker tooling guards. Every fixture below is synthetic, not UIKit verification."""
from collections import Counter
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import workflow_matrix as m
import test_ios_application_receipts as fixtures


class IosPickerBatchTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-file-picker",), focus=r.IOS_PICKER_BOUNDARY_FOCUS)

    def collect(self, identities=None, outcome="", markers=1, duplicate=False):
        plan = self.plan()
        selected = plan["expected"][0]
        identities = r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS) if identities is None else identities
        xml = "<testsuite>" + "".join(
            f'<testcase classname="{c["classname"]}" name="{c["name"]}">{outcome}</testcase>' for c in identities) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / selected["report_directory"]
            reports.mkdir(parents=True)
            (reports / "TEST-explicitly-synthetic.xml").write_text(xml)
            if duplicate:
                (reports / "TEST-duplicate.xml").write_text(xml)
            now = time.time_ns()
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({selected["task"]: markers}), host_system="Darwin")

    def fixture(self):
        f = fixtures.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        f.write("settings.gradle.kts", 'include(\n    ":calf-ui",\n    ":calf-io",\n    ":calf-file-picker",\n)\n')
        f.write("calf-file-picker/build.gradle.kts", "// synthetic model input; never executed")
        for source in {*r.IOS_PICKER_APPLICATION_SOURCES, *(g["source"] for g in r.IOS_PICKER_BOUNDARY_GROUPS)}:
            f.write(source, (r.ROOT / source).read_bytes())
        binary = f.write(app.APPLICATION_HOSTS["calf-file-picker"]["binary_directory"] + "/test.kexe", f.binary.read_bytes())
        binary.chmod(0o700)
        cases = [{"classname": g["classname"], "name": name, "status": "passed"}
                 for g in r.IOS_PICKER_BOUNDARY_GROUPS for name in g["methods"]]
        document = copy.deepcopy(f.document)
        document.update(task=app.APPLICATION_HOSTS["calf-file-picker"]["task"],
                        explicit_test_focus=r.IOS_PICKER_BOUNDARY_FOCUS,
                        binary_path=binary.relative_to(f.root).as_posix(), binary_sha256=r.sha256(binary),
                        binary_sha256_after=r.sha256(binary), macho=app.macho_simulator_identity(binary))
        document["application_protocol"].update(testcases=cases, counts=r.case_counts(cases))
        document["application_protocol"].pop("image_lifetime_observation", None)
        return f, binary, cases, document

    def test_one_slot_exact_26_methods_no_replay_or_publishing_tasks(self):
        rows = m.matrix("ios-picker-batch")["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual(("ios-iphone", "calf-file-picker", r.IOS_PICKER_BOUNDARY_FOCUS),
                         tuple(rows[0][k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        expected = plan["expected"][0]
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, expected["task"])
        self.assertEqual("genuine-uikit-application", expected["native_test_host"])
        self.assertEqual(26, len(expected["required_testcases"]))
        selectors = [value for g in r.IOS_PICKER_BOUNDARY_GROUPS for method in g["methods"]
                     for value in ("--tests", g["classname"] + "." + method)]
        self.assertEqual(selectors, r.gradle_command("ios", plan, simulator=fixtures.DEVICE)[-52:])
        self.assertNotIn(r.IOS_SAVE_WRITE_METHOD, expected["test_filter"])
        self.assertNotIn("calf.io.", expected["test_filter"])
        self.assertEqual([], self.collect()["errors"])
        self.assertEqual(26, self.collect()["totals"]["passed"])
        process = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                  "--suite", "ios", "--module", "calf-file-picker", "--focus", r.IOS_PICKER_BOUNDARY_FOCUS],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, process.returncode, process.stderr)

    def test_original_ui_and_standalone_foundation_profiles_keep_their_own_tasks(self):
        ui = r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=r.IOS_SLIDER_NUMERIC_FOCUS)
        self.assertEqual(":calf-ui:" + r.IOS_APPLICATION_TASK, ui["expected"][0]["task"])
        foundation = r.plan(r.ROOT, "ios", only_modules=("calf-file-picker",), focus=r.IOS_SAVE_WRITE_FOCUS)
        self.assertEqual(":calf-file-picker:iosSimulatorArm64Test", foundation["expected"][0]["task"])
        self.assertNotIn("native_test_host", foundation["expected"][0])
        full_picker = r.plan(r.ROOT, "ios", only_modules=("calf-file-picker",))
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, full_picker["expected"][0]["task"])

    def test_other_suites_modules_missing_hosts_and_declaration_drift_cannot_run(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PICKER_BOUNDARY_FOCUS)
        f, _, _, _ = self.fixture()
        self.assertTrue(r.validate_test_focus(self.plan(f.root)))
        source = f.root / r.IOS_PICKER_BOUNDARY_GROUPS[1]["source"]
        original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n"):
            source.write_text(changed)
            with self.assertRaises(ValueError):
                self.plan(f.root)
        source.write_text(original)
        self.assertTrue(r.validate_test_focus(self.plan(f.root)))
        (f.root / r.IOS_PICKER_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError):
            self.plan(f.root)

    def test_exact_module_directory_and_filters_reject_cross_application_reuse(self):
        picker_binary = app.APPLICATION_HOSTS["calf-file-picker"]["binary_directory"] + "/test.kexe"
        ui_binary = app.EXPECTED_BINARY_DIRECTORY + "/test.kexe"
        self.assertEqual("calf-file-picker", app.application_host(picker_binary, r.IOS_PICKER_BOUNDARY_FOCUS)["module"])
        self.assertEqual("calf-ui", app.application_host(ui_binary, r.IOS_SLIDER_NUMERIC_FOCUS)["module"])
        for binary, focus in ((picker_binary, r.IOS_SLIDER_NUMERIC_FOCUS), (ui_binary, r.IOS_PICKER_BOUNDARY_FOCUS),
                              ("calf-file-picker/build/bin/iosArm64/applicationDebugTest/test.kexe", None),
                              ("other/applicationDebugTest/test.kexe", None)):
            with self.subTest(binary=binary, focus=focus), self.assertRaises(ValueError):
                app.application_host(binary, focus)
        selectors = r.ui_application_focus_filter(r.IOS_PICKER_BOUNDARY_FOCUS).split(",")
        arguments = sorted(app.TEST_ARGUMENTS)
        self.assertEqual(r.IOS_PICKER_BOUNDARY_FOCUS,
                         app.application_test_focus(arguments + ["--ktest_gradle_filter=" + ",".join(reversed(selectors))]))
        for changed in (selectors[:-1], selectors * 2, [*selectors, "*"], [*selectors[:-1], "foreign"]):
            with self.assertRaises(ValueError):
                app.application_test_focus(arguments + ["--ktest_gradle_filter=" + ",".join(changed)])

    def test_missing_duplicate_foreign_target_failure_skip_and_zero_task_are_not_success(self):
        original = r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS)
        for changed in ([], original[:-1], original * 2,
                        [*original, {"classname": original[0]["classname"], "name": "unrelated"}]):
            self.assertTrue(self.collect(changed)["errors"])
        for key, value in (("classname", r.IOS_PICKER_BOUNDARY_GROUPS[0]["classname"]),
                           ("name", original[0]["name"].replace("iosSimulatorArm64", "iosArm64"))):
            changed = copy.deepcopy(original)
            changed[0][key] = value
            self.assertTrue(self.collect(changed)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(markers=0)["errors"])
        self.assertTrue(self.collect(duplicate=True)["errors"])

    def test_picker_still_requires_native_protocol_xml_sdk_workers_and_owned_cleanup(self):
        f, _, cases, document = self.fixture()
        f.plan = self.plan(f.root)
        f.receipt_path = f.output / "native-picker-application" / fixtures.TOKEN / "receipt.json"
        f.document = document
        f.modules = [{"module": "calf-file-picker", "task": document["task"], "testcases": f.xml_cases(cases)}]
        f.save()
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual("calf-file-picker", accepted["ios_applications"][0]["module"])
        self.assertEqual(26, accepted["ios_applications"][0]["counts"]["passed"])
        for section, key, value in (("cleanup", "owned_app_absence_verified", False),
                                    ("cleanup", "owned_app_stopped_verified", False),
                                    ("cleanup", "owned_local_bundle_removed", False),
                                    ("runtime_after", "source_revision", "b" * 40)):
            before = f.document[section][key]
            f.document[section][key] = value
            f.save()
            self.assertTrue(f.collect()["errors"])
            f.document[section][key] = before
        f.document["application_protocol"]["activation"]["owned_worker"] = 1
        f.save()
        self.assertTrue(f.collect()["errors"])

    def test_full_plans_keep_two_independent_app_receipts_and_do_not_silently_drop_a_removed_host_tag(self):
        f, _, picker_cases, picker_document = self.fixture()
        f.plan = r.plan(f.root, "ios", only_modules=("calf-ui", "calf-file-picker"))
        picker_document.pop("explicit_test_focus")
        picker_path = f.output / "native-picker-application" / fixtures.TOKEN / "receipt.json"
        picker_path.parent.mkdir(parents=True)
        picker_path.write_text(json.dumps(picker_document))
        f.modules.append({"module": "calf-file-picker", "task": picker_document["task"], "testcases": f.xml_cases(picker_cases)})
        review = f.collect()
        self.assertEqual([], review["errors"])
        self.assertEqual({"calf-ui", "calf-file-picker"}, {item["module"] for item in review["ios_applications"]})
        self.assertEqual({"calf-ui": 16, "calf-file-picker": 26},
                         {item["module"]: item["counts"]["passed"] for item in review["ios_applications"]})
        expected = next(e for e in f.plan["expected"] if e["module"] == "calf-file-picker")
        expected.pop("native_test_host")
        rejected = f.collect()
        self.assertEqual(1, len(rejected["ios_applications"]))
        self.assertEqual("calf-file-picker", rejected["errors"][0]["module"])
