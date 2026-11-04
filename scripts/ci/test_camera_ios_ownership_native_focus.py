# SPDX-License-Identifier: Apache-2.0
"""NEW finite Camera selection/source/XML models; no compiler or native execution."""
import ast
from collections import Counter
import copy
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import camera_ios_ownership_native_focus as camera
import library_tests as library
import workflow_matrix as matrix

ROOT = Path(__file__).resolve().parents[2]
DEVICE = "11111111-1111-1111-1111-111111111111"


def copy_model_checkout(root):
    """Only the Camera compiler companions and authored discovery sources."""
    (root / "settings.gradle.kts").write_text('include(\n    ":calf-camera-picker",\n)\n')
    names = set(camera.SOURCE_SHA256) | set(camera.OTHER_SOURCE_SHA256)
    names.update(path.relative_to(ROOT).as_posix() for path in library.source_files(ROOT, "calf-camera-picker/src/commonTest"))
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


def native_plan(root):
    return library.plan(root, "ios", only_modules=(camera.MODULE,), focus=camera.FOCUS)


class CameraIosOwnershipNativeFocusControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        copy_model_checkout(self.root)

    def test_exact_enabled_new5_three_source_hashes_and_zero_test_helpers_require_common0(self):
        self.assertTrue(camera.validate_sources(self.root, sorted(camera.SOURCES)))
        self.assertEqual(5, len(camera.METHODS))
        self.assertEqual(5, len(set(camera.selectors())))
        self.assertEqual(list(camera.METHODS), re.findall(r"@Test\s+fun\s+(\w+)\s*\(\s*\)",
                         (self.root / camera.TEST_SOURCE).read_text()))
        self.assertEqual([], camera.source_contract(self.root)["common_sources"])
        for sources in (list(camera.SOURCES), sorted(camera.SOURCES)[:-1], sorted(camera.SOURCES) + ["foreign.kt"],
                        tuple(sorted(camera.SOURCES)), sorted(camera.SOURCES) * 2):
            if sources == sorted(camera.SOURCES):
                continue
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                camera.validate_sources(self.root, sources)

    def test_only_one_exact_manual_iphone_arm64_row_and_literal_choice_refuse_host_or_module_drift(self):
        wanted = {"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
                  "python": "python3", "simulator-kind": "iphone", "test-modules": camera.MODULE,
                  "test-focus": camera.FOCUS}
        self.assertEqual([wanted], matrix.matrix(camera.PROFILE)["include"])
        workflow = (ROOT / ".github/workflows/gradle.yml").read_text()
        options = re.search(r"options: \[([^\n]+)\]", workflow).group(1).split(", ")
        self.assertEqual(1, options.count(camera.PROFILE))
        for slots in (("ios-ipad",), ("ios-iphone", "ios-ipad"), ("ios-iphone", "ios-iphone")):
            with patch.dict(matrix.PROFILES, {camera.PROFILE: slots}), self.assertRaises(ValueError):
                matrix.matrix(camera.PROFILE)
        with patch.dict(matrix.MODULE_SUBSETS, {camera.PROFILE: "calf-file-picker"}), self.assertRaises(ValueError):
            matrix.matrix(camera.PROFILE)
        for field, value in (("runner", "macos-26-intel"), ("arch", "x64"), ("suite", "desktop"),
                             ("python", "python"), ("simulator-kind", "ipad"), ("extra", "foreign")):
            slots = copy.deepcopy(matrix.SLOTS)
            next(row for row in slots if row["slot"] == "ios-iphone")[field] = value
            with patch.object(matrix, "SLOTS", slots), self.assertRaises(ValueError):
                matrix.matrix(camera.PROFILE)

    def test_no_focus_camera_keeps_original_task_and_global_application_host_inheritance(self):
        ordinary = library.plan(self.root, "ios", only_modules=(camera.MODULE,))
        item = ordinary["expected"][0]
        self.assertEqual(":calf-camera-picker:iosSimulatorArm64Test", item["task"])
        self.assertNotIn("native_test_host", item)
        self.assertNotIn(camera.MODULE, library.IOS_APPLICATION_HOST_SOURCES)
        self.assertFalse(library.validate_test_focus(ordinary))
        self.assertEqual(camera.focus_spec(), library.UI_APPLICATION_FOCUS_SPECS[camera.FOCUS])
        for suite, modules, focus in (("desktop", (camera.MODULE,), camera.FOCUS),
                                     ("ios", ("calf-ui",), camera.FOCUS),
                                     ("ios", (camera.MODULE, "calf-ui"), camera.FOCUS),
                                     ("ios", (camera.MODULE,), camera.FOCUS + "-all")):
            with self.assertRaises(ValueError):
                library.plan(self.root, suite, only_modules=modules, focus=focus)

    def test_exact_module_task_report_filters_required5_contract_refuses_aliases_omissions_and_booleans(self):
        plan = native_plan(self.root)
        self.assertTrue(library.validate_test_focus(plan))
        item = plan["expected"][0]
        self.assertEqual((camera.TASK, ["iosTest"], sorted(camera.SOURCES), 1),
                         (item["task"], item["test_source_sets"], item["test_source_files"], item["required_original_xml"]))
        self.assertEqual(camera.identities(), item["required_testcases"])
        mutations = (
            lambda p: p.update(complete_suite_requested=0),
            lambda p: p.update(explicit_module_subset=[camera.MODULE, "calf-ui"]),
            lambda p: p["expected"][0].update(task=":calf-camera-picker:iosSimulatorArm64Test"),
            lambda p: p["expected"][0].update(project=":calf-ui"),
            lambda p: p["expected"][0].update(required_original_xml=True),
            lambda p: p["expected"][0].update(test_source_sets=["commonTest", "iosTest"]),
            lambda p: p["expected"][0].update(test_filter_argument="foreign"),
            lambda p: p["expected"][0][camera.CONTRACT_KEY].update(schema_version=True),
            lambda p: p["expected"][0][camera.CONTRACT_KEY].update(native_tests_executed=False),
            lambda p: p["expected"][0][camera.CONTRACT_KEY]["source_sha256"].update({camera.HOST_SOURCE: "a" * 64}),
            lambda p: p["expected"][0].pop("required_testcases"),
        )
        for mutate in mutations:
            bad = copy.deepcopy(plan)
            mutate(bad)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                library.validate_test_focus(bad)
        ordinary = library.plan(self.root, "ios", only_modules=(camera.MODULE,))
        ordinary["expected"][0][camera.CONTRACT_KEY] = camera.source_contract(self.root)
        with self.assertRaisesRegex(ValueError, "No Camera"):
            library.validate_test_focus(ordinary)

    def test_actual_current_source_init_privacy_and_api_inputs_are_ordinary_exact_before_command(self):
        for name in camera.SOURCE_SHA256 | camera.OTHER_SOURCE_SHA256:
            target = self.root / name
            raw = target.read_bytes()
            with self.subTest(input=name):
                target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError):
                    camera.source_contract(self.root)
                target.unlink()
                with self.assertRaises(FileNotFoundError):
                    camera.source_contract(self.root)
                target.symlink_to(ROOT / name)
                with self.assertRaises(ValueError):
                    camera.source_contract(self.root)
                target.unlink()
                backing = target.with_name(target.name + ".backing")
                backing.write_bytes(raw)
                target.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    camera.source_contract(self.root)
                target.unlink()
                backing.unlink()
                target.write_bytes(raw)
        self.assertTrue(camera.validate_sources(self.root))

    def test_separate_compiler_or_ordered_new5_request_uses_public_kgp_three_sources_and_apple_native_host(self):
        init = (ROOT / camera.INIT_SCRIPT).read_text()
        self.assertIn("gradle.startParameter.taskNames in setOf(compilerRequest, applicationRequest)", init)
        self.assertIn('getMethod("setSource", Array<Any>::class.java)', init)
        self.assertIn("common.setFrom(emptyList<Any>())", init)
        self.assertIn("actual.files.map { it.canonicalFile }.toSet() == files.toSet()", init)
        self.assertIn('getByName("iosSimulatorArm64ApplicationTest").doFirst', init)
        self.assertIn("compiler_executions_attested\" to 0", init)
        plan = native_plan(self.root)
        with patch.object(library.platform, "system", return_value="Darwin"), patch.object(library.platform, "machine", return_value="arm64"):
            command = library.gradle_command("ios", plan, simulator=DEVICE, root=self.root)
        self.assertIn(camera.INIT_SCRIPT, command)
        self.assertIn("-P" + camera.FOCUS_PROPERTY + "=" + camera.FOCUS, command)
        self.assertEqual(camera.native_request(), command[-len(camera.native_request()):])
        for system, arch in (("Linux", "x86_64"), ("Windows", "arm64"), ("Darwin", "x86_64")):
            with patch.object(library.platform, "system", return_value=system), patch.object(library.platform, "machine", return_value=arch), self.assertRaises(ValueError):
                library.gradle_command("ios", plan, simulator=DEVICE, root=self.root)

    def test_one_fresh_original_five_case_xml_refuses_missing_duplicate_extra_skip_failure_and_stale_reports(self):
        plan = native_plan(self.root)
        item = plan["expected"][0]
        folder = self.root / item["report_directory"]
        folder.mkdir(parents=True)
        report = folder / "TEST-camera-source-model.xml"
        cases = camera.identities()

        def write(rows, outcome=None):
            suite = ET.Element("testsuite", tests=str(len(rows)))
            for index, row in enumerate(rows):
                case = ET.SubElement(suite, "testcase", **row)
                if outcome and index == 0:
                    ET.SubElement(case, outcome)
            report.write_bytes(ET.tostring(suite))

        def collect():
            now = time.time_ns()
            return library.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                           Counter({camera.TASK: 1}), host_system="Darwin")

        write(cases)
        accepted = collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(5, accepted["totals"]["passed"])
        for rows in ([], cases[:-1], cases + cases[:1], cases + [{"classname": "foreign", "name": "foreign"}]):
            write(rows)
            self.assertTrue(collect()["errors"])
        for outcome in ("skipped", "failure", "error"):
            write(cases, outcome)
            self.assertTrue(collect()["errors"])
        write(cases)
        extra = folder / "TEST-extra-empty-model.xml"
        extra.write_text('<testsuite tests="0"/>')
        self.assertTrue(collect()["errors"])
        extra.unlink()
        os.utime(report, ns=(1, 1))
        self.assertTrue(collect()["errors"])
        outcomes, errors = camera.outcomes([{**row, "status": "passed"} for row in cases], "Linux",
                                           cases_by_report=[[{**row, "status": "passed"} for row in cases]])
        self.assertTrue(errors)
        self.assertTrue(all(row["disposition"] == "required-not-passed" for row in outcomes))

    def test_fresh_native_admission_is_required_even_when_compiler_and_link_are_unchanged(self):
        now = time.time_ns()
        self.assertFalse(camera.validate_admission(self.root, now - 1_000_000_000, now + 1_000_000_000))
        target = self.root / camera.ADMISSION
        target.parent.mkdir(parents=True)
        document = camera.admission_document(native_task=True)
        target.write_text(json.dumps(document))
        self.assertTrue(camera.validate_admission(self.root, now - 1_000_000_000, now + 1_000_000_000))
        for key, value in (("schema_version", True), ("compiler_executions_attested", False),
                           ("excluded_unrelated_test_sources", 1), ("native_tests_executed", 5),
                           ("common_sources", ["accepted.kt"]), ("task", camera.COMPILER_TASK)):
            bad = copy.deepcopy(document)
            bad[key] = value
            target.write_text(json.dumps(bad))
            self.assertFalse(camera.validate_admission(self.root, now - 1_000_000_000, now + 1_000_000_000))
        target.write_text(json.dumps(document))
        os.utime(target, ns=(1, 1))
        self.assertFalse(camera.validate_admission(self.root, now - 1_000_000_000, now + 1_000_000_000))
        compiler = camera.admission_document(native_task=False)
        self.assertEqual(camera.COMPILER_TASK, compiler["task"])
        self.assertEqual((0, 0, 0), tuple(compiler[key] for key in
                         ("compiler_executions_attested", "apple_links_attested", "native_tests_executed")))


if __name__ == "__main__":
    unittest.main()
