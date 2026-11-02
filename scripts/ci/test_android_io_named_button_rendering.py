"""Important rendering/finite-selection controls; no device/library passes.

The genuine selected library test remains the Android execution gate. XML below
is synthetic and tests missing/duplicate/foreign/failure admission only.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

import android_device_tests as device
import android_io_named_button_rendering as render
import android_io_named_system_documents as source
import android_io_named_gate_details as detail
import library_tests as lt
import workflow_matrix as matrix

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL_UI_SHA256 = "5f247f185c2703c04d1664657ee43b75ff19d919eb5cb2b10c16396736d9826e"  # Filled from the retained 8bfe511c source, not a current derivative.


class NamedSystemButtonRenderingControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-button-rendering-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for relative in source.SOURCE_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.path = self.root / source.UI
        self.current = self.path.read_text()

    def test_exact_four_deltas_roundtrip_retains_original_observers_actions_and_source(self):
        original = render.rendering_preimage(self.current)
        self.assertEqual(ORIGINAL_UI_SHA256, hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(self.current, render.rendering_postimage(original))
        self.assertEqual(self.current, render.rendering_fixture_postimage(original))
        self.assertEqual(1, original.count("val deadline = SystemClock.elapsedRealtime() + 20_000"))
        self.assertEqual(2, original.count("val deadline = SystemClock.elapsedRealtime() + 1_000"))
        source.validate_source_receipt(source.source_contract(self.root))

    def test_partial_duplicate_and_nonexact_rendering_refuse_not_silently_repair(self):
        mutations = [(after, before) for before, after in render.DELTAS]
        mutations += [
            (render.DELTAS[0][1], render.DELTAS[0][1] * 2),
            ("java.util.Locale.ENGLISH", "java.util.Locale.getDefault()"),
            ("it.text?.toString() == renderedPickLabel", "it.text?.toString()?.contains(renderedPickLabel) == true"),
        ]
        for before, after in mutations:
            with self.subTest(fragment=before[:65]):
                # Locale occurs twice: change just the pick conversion; no ambiguous mutation.
                value = self.current.replace(before, after, 1)
                self.path.write_text(value)
                with self.assertRaisesRegex(ValueError, "^" + re.escape(render.REFUSAL) + "$"):
                    source.source_contract(self.root)

    def test_raw_only_original_cannot_obtain_current_source_receipt(self):
        self.path.write_text(render.rendering_preimage(self.current))
        with self.assertRaisesRegex(ValueError, "^" + re.escape(render.REFUSAL) + "$"):
            source.source_contract(self.root)

    def test_en_locale_and_enabled_clickable_guards_remain_mandatory(self):
        for before, after in [
            ('assertEquals("en", context.resources.configuration.locales[0].language)', 'assertTrue(true)'),
            ('                it.isEnabled && it.isClickable', '                it.isClickable'),
        ]:
            with self.subTest(boundary=before):
                path = self.root / (source.TEST if "assertEquals" in before else source.UI)
                original = path.read_text()
                self.assertIn(before, original)
                path.write_text(original.replace(before, after, 1))
                with self.assertRaises(ValueError):
                    source.source_contract(self.root)
                path.write_text(original)

    def test_historical_fixture_preserves_broken_native_predicate_and_refuses_it(self):
        original = render.rendering_preimage(self.current)
        before = render.DELTAS[1][0]
        mutant = original.replace(before, '            it.isClickable\n', 1)
        overlay = render.rendering_fixture_postimage(mutant)
        self.assertIn('            it.isClickable\n', overlay)
        self.path.write_text(overlay)
        with self.assertRaisesRegex(ValueError, "^" + re.escape(render.REFUSAL) + "$"):
            source.source_contract(self.root)

    def test_historical_resource_and_detail_bridges_return_exact_current_and_old_hashes(self):
        historical = source.resource_admission_preimage(self.current)
        self.assertEqual("03a0ebc37215c4b86043f253f4e83b7db39c7fd52652d9ea735e6e7c106ea1dc",
                         hashlib.sha256(historical.encode()).hexdigest())
        self.assertEqual(self.current, source.resource_admission_postimage(historical))
        self.assertEqual("3f7288affcc1e52b8262a7c3c07fabeb2941c40fff36aa1c456ffd34419ece6e",
                         hashlib.sha256(detail.detail_preimage(self.current).encode()).hexdigest())
        for function in (render.rendering_preimage, render.rendering_postimage, render.rendering_fixture_postimage):
            for value in (None, b"not source", []):
                with self.subTest(function=function.__name__, type=type(value).__name__):
                    with self.assertRaises(ValueError):
                        function(value)


class NamedExternalFiniteSelectionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = lt.plan(ROOT, "android-device", only_modules=("calf-io",), focus=lt.ANDROID_IO_NAMED_EXTERNAL_FOCUS)

    def test_single_original_external_method_and_canonical_pair_remain_distinct(self):
        row = self.plan["expected"][0]
        self.assertFalse(self.plan["complete_suite_requested"])
        self.assertTrue(lt.validate_test_focus(self.plan))
        self.assertEqual(1, len(row["required_testcases"]))
        self.assertEqual(lt.ANDROID_IO_NAMED_SYSTEM_METHODS[0], row["required_testcases"][0]["name"])
        self.assertEqual(lt.ANDROID_IO_NAMED_SYSTEM_CLASS + "#" + lt.ANDROID_IO_NAMED_SYSTEM_METHODS[0], row["test_filter"])
        self.assertEqual(2, len(lt.android_io_named_system_identities()))
        self.assertEqual(lt.ANDROID_IO_NAMED_SYSTEM_CLASS, lt.android_io_named_system_filter())
        self.assertIn("Downloads", self.plan["scope"])

    def test_plan_refuses_broad_pair_downloads_substitution_missing_or_duplicate_case(self):
        row = self.plan["expected"][0]
        for name, value in [
            ("test_filter", lt.ANDROID_IO_NAMED_SYSTEM_CLASS),
            ("test_filter", lt.ANDROID_IO_NAMED_SYSTEM_CLASS + "#" + lt.ANDROID_IO_NAMED_SYSTEM_METHODS[1]),
            ("required_testcases", []),
            ("required_testcases", row["required_testcases"] * 2),
            ("required_testcases", lt.android_io_named_system_identities()),
        ]:
            with self.subTest(field=name, value=value):
                plan = copy.deepcopy(self.plan)
                plan["expected"][0][name] = value
                with self.assertRaises(ValueError):
                    lt.validate_test_focus(plan)

    def test_controller_enforces_API35_only_calf_io_without_helper_or_grant_bootstrap(self):
        device.validate_api_selection(35, ("calf-io",), lt.ANDROID_IO_NAMED_EXTERNAL_FOCUS)
        for api, modules in [(34, ("calf-io",)), (35, None), (35, ("calf-io", "calf-share")), (True, ("calf-io",))]:
            with self.subTest(api=api, modules=modules):
                with self.assertRaises(ValueError):
                    device.validate_api_selection(api, modules, lt.ANDROID_IO_NAMED_EXTERNAL_FOCUS)
        self.assertFalse(lt.android_io_documents_required(self.plan))
        self.assertIsNone(self.plan.get("android_io_documents"))

    def test_actual_Gradle_argv_has_one_method_not_class_and_one_original_task(self):
        argv = lt.gradle_command("android-device", self.plan, android_serial="emulator-5588")
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + self.plan["expected"][0]["test_filter"], argv)
        self.assertEqual(1, argv.count(":calf-io:connectedAndroidDeviceTest"))
        self.assertNotIn("--tests", argv)
        with self.assertRaises(ValueError):
            lt.android_io_named_system_identities("unknown-or-broad")

    def test_workflow_is_exact_one_host_with_API35_sdk_profile_and_readonly_permissions(self):
        rows = matrix.matrix(lt.ANDROID_IO_NAMED_EXTERNAL_FOCUS)["include"]
        self.assertEqual(1, len(rows))
        self.assertEqual({"slot": "android-device-api35", "suite": "android-device", "runner": "ubuntu-24.04",
                          "arch": "x64", "emulator-api": "35", "test-modules": "calf-io",
                          "test-focus": lt.ANDROID_IO_NAMED_EXTERNAL_FOCUS},
                         {key: rows[0][key] for key in ["slot", "suite", "runner", "arch", "emulator-api", "test-modules", "test-focus"]})
        workflow = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("inputs.profile == 'android-io-named-external-storage'", workflow)
        self.assertIn("android-io-named-system-providers, android-io-named-external-storage,", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)

    def test_synthetic_XML_requires_one_exact_nonzero_fresh_external_result(self):
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-external-XML-") as temporary:
            root = Path(temporary)
            path = root / self.plan["expected"][0]["report_directory"] / "TEST-external.xml"
            path.parent.mkdir(parents=True)
            def report(names, failure=False):
                suite = ET.Element("testsuite")
                for name in names:
                    case = ET.SubElement(suite, "testcase", classname=lt.ANDROID_IO_NAMED_SYSTEM_CLASS, name=name)
                    if failure:
                        ET.SubElement(case, "failure").text = "synthetic failure"
                path.write_bytes(ET.tostring(suite))
                now = time.time_ns()
                return lt.collect_reports(root, self.plan, now - 1_000_000_000, now + 1_000_000_000,
                                          Counter({":calf-io:connectedAndroidDeviceTest": 1}), host_system="Linux")
            accepted = report(lt.ANDROID_IO_NAMED_SYSTEM_METHODS[:1])
            self.assertEqual(1, accepted["modules"][0]["passed"])
            self.assertFalse(accepted["errors"])
            for names, failure in [((), False), (lt.ANDROID_IO_NAMED_SYSTEM_METHODS, False),
                                   (lt.ANDROID_IO_NAMED_SYSTEM_METHODS[:1] * 2, False),
                                   (lt.ANDROID_IO_NAMED_SYSTEM_METHODS[1:], False),
                                   (lt.ANDROID_IO_NAMED_SYSTEM_METHODS[:1], True)]:
                with self.subTest(names=names, failure=failure):
                    refused = report(names, failure)
                    self.assertTrue(refused["errors"])


if __name__ == "__main__":
    unittest.main()
