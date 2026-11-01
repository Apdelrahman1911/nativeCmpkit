# SPDX-License-Identifier: Apache-2.0
"""New source/selector/XML models only; never Gradle or native WebView acceptance."""
from collections import Counter
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as r
import test_android_webview_request_state as source_guard
from test_ios_io_profile import profile_options
import workflow_matrix as matrix


ANNOTATION = "com.mohamedrejeb.calf.ui.web.AndroidWebViewRequestVerification"
ANNOTATION_NAME = ANNOTATION.rsplit(".", 1)[1]
ORIGINAL_TWO_METHOD_SOURCE_SHA256 = "84018856aee7c6e223d32465d2eef76a9b705ebbaf6f232513fd34c8b152b326"
ORIGINAL_METHOD_BODY_SHA256 = {
    "twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl":
        "6e07ff036d902271ad1b5347b556611dc3b978aae5945fb201e4048e02aa65d1",
    "publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner":
        "c6a1cc9662b38f6fd74d1d8f1a93c59e65825ea231ac6e227e8078a2ddce700a",
}


def agp_ate_map_round_trip(arguments):
    """Literal model of AGP9.4.0 joinToString and ATE1.0.1 split/mapNotNull, not their execution."""
    encoded = ",".join(key + "=" + value for key, value in arguments.items())
    decoded = {}
    for token in encoded.split(","):
        parts = token.split("=", 1)
        if len(parts) == 2:
            decoded[parts[0].strip()] = parts[1].strip()
    return encoded, decoded


class AndroidWebViewRequestSelectorModels(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        module = self.root / "calf-webview"
        module.mkdir()
        (module / "build.gradle.kts").write_text("// Synthetic discovery only; never built\n")
        for source_set in r.SUITES["android-device"][1]:
            for original in r.source_files(r.ROOT, "calf-webview/src/" + source_set):
                relative = original.relative_to(r.ROOT)
                target = self.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(original.read_bytes())
        self.source_path = self.root / r.ANDROID_WEBVIEW_REQUEST_SOURCE
        self.source = self.source_path.read_text()

    def plan(self):
        return r.plan(self.root, "android-device", only_modules=("calf-webview",),
                      focus=r.ANDROID_WEBVIEW_REQUEST_FOCUS)

    def command(self, plan=None):
        return r.gradle_command("android-device", self.plan() if plan is None else plan,
                                root=self.root, android_serial="emulator-5588")

    def selectors(self, command):
        prefix = "-Pandroid.testInstrumentationRunnerArguments."
        return dict(argument[len(prefix):].split("=", 1) for argument in command
                    if argument.startswith(prefix))

    def reject_source_variants(self, candidates):
        for label, source in candidates:
            with self.subTest(variant=label):
                self.source_path.write_text(source)
                with self.assertRaises(ValueError):
                    self.plan()
        self.source_path.write_text(self.source)

    def test_new_command_is_one_lossless_annotation_with_original_two_identities(self):
        plan = self.plan()
        item, = plan["expected"]
        self.assertEqual("annotation", item["test_filter_argument"])
        self.assertEqual(ANNOTATION, item["test_filter"])
        self.assertEqual(r.android_webview_request_identities(), item["required_testcases"])
        self.assertEqual({"annotation": ANNOTATION, "timeout_msec": "120000"},
                         self.selectors(self.command(plan)))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(2, len(item["required_testcases"]))
        self.assertNotIn("--tests", self.command(plan))
        self.assertEqual(":calf-webview:connectedAndroidDeviceTest", self.command(plan)[-1])

    def test_exact_agp_ate_map_model_drops_old_second_class_method_but_retains_annotation(self):
        legacy = ",".join(r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + method
                          for method in r.ANDROID_WEBVIEW_REQUEST_METHODS)
        encoded, lost = agp_ate_map_round_trip({"class": legacy, "timeout_msec": "120000"})
        self.assertIn("," + r.ANDROID_WEBVIEW_REQUEST_CLASS + "#", encoded)
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + r.ANDROID_WEBVIEW_REQUEST_METHODS[0],
                         lost["class"])
        requested = self.selectors(self.command())
        encoded, decoded = agp_ate_map_round_trip(requested)
        self.assertEqual(requested, decoded)
        self.assertEqual(2, len(encoded.split(",")))
        self.assertNotIn("class", decoded)

    def test_runner_annotation_model_includes_only_exact_two_methods_not_other_classes(self):
        # Runner1.7.0 evaluates the method annotation or the test-class annotation.
        # FUNCTION target prohibits class grouping; the source guard binds every use.
        methods = re.findall(r"@" + ANNOTATION_NAME + r"\s+@Test\s+fun\s+"
                             r"([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", self.source)
        descriptions = [({"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": method},
                         {ANNOTATION}, set()) for method in methods]
        descriptions += [({"classname": "Unrelated", "name": "mustNotRun"}, set(), set()),
                         ({"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": "unannotatedHelper"},
                          set(), set())]
        selected = [identity for identity, method_annotations, class_annotations in descriptions
                    if ANNOTATION in method_annotations or ANNOTATION in class_annotations]
        self.assertEqual(r.android_webview_request_identities(), selected)
        self.assertFalse(re.search(r"@" + ANNOTATION_NAME + r"\s+(?:@RunWith[^\n]*\s+)?class\b",
                                   self.source))

    def test_source_selector_is_top_level_function_runtime_and_exact_two_uses(self):
        item, = self.plan()["expected"]
        r.validate_android_webview_request_annotation(self.root, item["test_source_files"])
        declaration = source_guard.ANDROID_REQUEST_SELECTOR_DECLARATION
        self.assertEqual(1, self.source.count(declaration))
        self.assertEqual(3, self.source.count(ANNOTATION_NAME))
        before = self.source[:self.source.index(declaration)]
        self.assertNotIn("{", before)
        self.assertNotIn("}", before)
        for method in r.ANDROID_WEBVIEW_REQUEST_METHODS:
            self.assertEqual(1, self.source.count("    @" + ANNOTATION_NAME + "\n    @Test fun " + method + "()"))

    def test_stripping_only_selection_metadata_restores_both_original_bodies_and_all_helpers(self):
        unselected = source_guard.request_source_without_selection_annotation(self.source)
        self.assertEqual(ORIGINAL_TWO_METHOD_SOURCE_SHA256, hashlib.sha256(unselected.encode()).hexdigest())
        for method, expected in ORIGINAL_METHOD_BODY_SHA256.items():
            with self.subTest(method=method):
                self.assertEqual(expected, hashlib.sha256(
                    source_guard.body_after(self.source, "@Test fun " + method).encode()).hexdigest())
        self.assertEqual(list(r.ANDROID_WEBVIEW_REQUEST_METHODS),
                         re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", unselected))

    def test_compiled_projection_keeps_old_hash_and_refuses_partial_metadata_or_body_changes(self):
        projected = source_guard.compiled_request_source(self.source)
        self.assertEqual(source_guard.COMPILED_ANDROID_REQUEST_SOURCE_SHA256,
                         hashlib.sha256(projected.encode()).hexdigest())
        partial = self.source.replace("    @" + ANNOTATION_NAME + "\n", "", 1)
        extra = self.source + "\n// " + ANNOTATION_NAME + " must not be projected away\n"
        for candidate in (partial, extra):
            with self.subTest(partial_or_extra=candidate is partial), self.assertRaises(ValueError):
                source_guard.request_source_without_selection_annotation(candidate)
        changed = self.source.replace("assertEquals(35, Build.VERSION.SDK_INT", "assertEquals(34, Build.VERSION.SDK_INT", 1)
        with self.assertRaises(ValueError):
            source_guard.compiled_request_source(changed)
        second = self.source.replace("fixture.navigator.stopLoading()", "native.stopLoading()", 1)
        self.assertNotEqual(ORIGINAL_TWO_METHOD_SOURCE_SHA256,
                            hashlib.sha256(source_guard.request_source_without_selection_annotation(second).encode()).hexdigest())

    def test_missing_duplicate_moved_or_fully_qualified_method_annotations_refuse(self):
        marker = "    @" + ANNOTATION_NAME + "\n"
        first, second = r.ANDROID_WEBVIEW_REQUEST_METHODS
        self.reject_source_variants([
            ("first-missing", self.source.replace(marker + "    @Test fun " + first, "    @Test fun " + first, 1)),
            ("second-missing", self.source.replace(marker + "    @Test fun " + second, "    @Test fun " + second, 1)),
            ("both-missing", self.source.replace(marker, "")),
            ("duplicate", self.source.replace(marker, marker + marker, 1)),
            ("moved-after-Test", self.source.replace(marker + "    @Test", "    @Test\n" + marker.strip(), 1)),
            ("qualified-instead-of-reviewed-short-use", self.source.replace(marker, "    @" + ANNOTATION + "\n", 1)),
        ])

    def test_source_binary_retention_wrong_target_or_duplicate_declaration_refuses(self):
        declaration = source_guard.ANDROID_REQUEST_SELECTOR_DECLARATION
        self.reject_source_variants([
            ("source-retention", self.source.replace("AnnotationRetention.RUNTIME", "AnnotationRetention.SOURCE", 1)),
            ("binary-retention", self.source.replace("AnnotationRetention.RUNTIME", "AnnotationRetention.BINARY", 1)),
            ("class-target", self.source.replace("AnnotationTarget.FUNCTION", "AnnotationTarget.CLASS", 1)),
            ("function-plus-class", self.source.replace("AnnotationTarget.FUNCTION", "AnnotationTarget.FUNCTION, AnnotationTarget.CLASS", 1)),
            ("duplicate-declaration", self.source.replace(declaration, declaration + declaration, 1)),
            ("renamed-declaration", self.source.replace("annotation class " + ANNOTATION_NAME, "annotation class WrongSelection", 1)),
        ])

    def test_nested_declaration_refuses_instead_of_an_unloadable_broad_annotation_filter(self):
        declaration = source_guard.ANDROID_REQUEST_SELECTOR_DECLARATION
        nested = self.source.replace(declaration, "class ForeignContainer {\n" + declaration + "}\n\n", 1)
        self.reject_source_variants([("nested-FQCN-would-change", nested)])

    def test_class_helper_alias_or_extra_same_source_uses_cannot_broaden_selection(self):
        marker = "@" + ANNOTATION_NAME
        self.reject_source_variants([
            ("class-use", self.source.replace("@RunWith(AndroidJUnit4::class)", marker + "\n@RunWith(AndroidJUnit4::class)", 1)),
            ("helper-use", self.source + "\n" + marker + "\nfun unrelatedHelper() {}\n"),
            ("alias-import", self.source.replace("import org.junit.Test", "import " + ANNOTATION + " as ExtraSelection\nimport org.junit.Test", 1)),
            ("extra-qualified-use", self.source + "\n@" + ANNOTATION + "\n@Test fun unrelated() {}\n"),
        ])

    def test_foreign_common_or_device_annotation_uses_imports_or_declarations_refuse(self):
        for source_set in ("commonTest", "androidDeviceTest"):
            relative = "calf-webview/src/" + source_set + "/kotlin/ForeignSelection.kt"
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            for label, text in (
                ("short-method", "@" + ANNOTATION_NAME + "\n@Test fun foreign() {}\n"),
                ("qualified-method", "@" + ANNOTATION + "\n@Test fun foreign() {}\n"),
                ("alias-import", "import " + ANNOTATION + " as Another\n@Another @Test fun foreign() {}\n"),
                ("duplicate-declaration", source_guard.ANDROID_REQUEST_SELECTOR_DECLARATION),
            ):
                with self.subTest(source_set=source_set, variant=label):
                    path.write_text(text)
                    with self.assertRaises(ValueError):
                        self.plan()
            path.unlink()

    def test_annotation_inventory_missing_duplicate_symlink_or_escaping_paths_refuse(self):
        files = self.plan()["expected"][0]["test_source_files"]
        variants = [[], [name for name in files if name != r.ANDROID_WEBVIEW_REQUEST_SOURCE],
                    files + [r.ANDROID_WEBVIEW_REQUEST_SOURCE], files + ["../foreign.kt"]]
        for inventory in variants:
            with self.subTest(inventory=inventory), self.assertRaises(ValueError):
                r.validate_android_webview_request_annotation(self.root, inventory)
        saved = self.source_path.with_name("private-original-selection.txt")
        self.source_path.rename(saved)
        self.source_path.symlink_to(saved.name)
        with self.assertRaises(ValueError):
            self.plan()
        with self.assertRaises(ValueError):
            r.validate_android_webview_request_annotation(self.root, files)

    def test_plan_cannot_omit_or_replace_annotation_argument_with_class_or_compound_values(self):
        valid = self.plan()
        legacy = ",".join(r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + method
                          for method in r.ANDROID_WEBVIEW_REQUEST_METHODS)
        for key, value in (("test_filter_argument", None), ("test_filter_argument", "class"),
                           ("test_filter_argument", "notAnnotation"), ("test_filter", legacy),
                           ("test_filter", ANNOTATION + ",Foreign"), ("test_filter", ANNOTATION + "%2CForeign"),
                           ("test_filter", r.ANDROID_WEBVIEW_REQUEST_CLASS), ("test_filter", "*")):
            candidate = copy.deepcopy(valid)
            candidate["expected"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.command(candidate)
        candidate = copy.deepcopy(valid)
        del candidate["expected"][0]["test_filter_argument"]
        with self.assertRaises(ValueError):
            self.command(candidate)

    def test_annotation_plan_cli_is_pure_and_keeps_exact_two_source_bound_cases(self):
        stream = io.StringIO()
        argv = ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-webview",
                "--focus", r.ANDROID_WEBVIEW_REQUEST_FOCUS]
        with patch.object(r, "ROOT", self.root), patch("sys.argv", argv), patch("sys.stdout", stream), \
                patch.object(r.subprocess, "Popen", side_effect=AssertionError("No external command is allowed")):
            self.assertEqual(0, r.main())
        item, = json.loads(stream.getvalue())["expected"]
        self.assertEqual("annotation", item["test_filter_argument"])
        self.assertEqual(ANNOTATION, item["test_filter"])
        self.assertEqual(r.android_webview_request_identities(), item["required_testcases"])
        self.assertIn(r.ANDROID_WEBVIEW_REQUEST_SOURCE, item["test_source_files"])
        self.assertEqual(r.android_webview_request_fixtures(), item["native_fixture_paths"])

    def test_lossless_command_preserves_unchanged_comma_and_effective_argument_guards_before_markers(self):
        init = (r.ROOT / "scripts/ci/fresh-tests.init.gradle.kts").read_text()
        connected = init[init.index('tasks.matching { it.name == "connectedAndroidDeviceTest"'):]
        comma_guard = "check(requestedSelectors.values.none { ',' in it })"
        effective_guard = "check(runnerArguments.filterKeys { it in selectorKeys } == requestedSelectors)"
        marker = 'logger.lifecycle("NATIVECMPKIT_TEST_RUNTIME task=$path'
        self.assertEqual(1, connected.count(comma_guard))
        self.assertEqual(1, connected.count(effective_guard))
        self.assertLess(connected.index(comma_guard), connected.index(marker))
        self.assertLess(connected.index(effective_guard), connected.index(marker))
        selected = {key: value for key, value in self.selectors(self.command()).items()
                    if key in {"class", "annotation", "notAnnotation"}}
        self.assertEqual({"annotation": ANNOTATION}, selected)
        self.assertTrue(all("," not in value for value in selected.values()))
        self.assertEqual(selected, agp_ate_map_round_trip(selected)[1])

    def test_annotation_plan_still_requires_two_cases_one_xml_and_exact_single_runtime_marker(self):
        plan = self.plan()
        folder = self.root / plan["expected"][0]["report_directory"]
        folder.mkdir(parents=True)
        path = folder / "TEST-synthetic-selection-only.xml"
        exact = r.android_webview_request_identities()
        for cases, markers, duplicate in ((exact, 1, False), (exact[:1], 1, False),
                                          (exact[1:], 1, False), (exact, 0, False),
                                          (exact, 2, False), (exact, 1, True)):
            xml = ET.Element("testsuite")
            for identity in cases:
                ET.SubElement(xml, "testcase", **identity)
            path.write_bytes(ET.tostring(xml))
            extra = folder / "TEST-extra-synthetic.xml"
            if duplicate:
                extra.write_bytes(path.read_bytes())
            now = time.time_ns()
            result = r.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                       Counter({plan["expected"][0]["task"]: markers}), host_system="Linux")
            with self.subTest(cases=len(cases), markers=markers, duplicate=duplicate):
                if cases == exact and markers == 1 and not duplicate:
                    self.assertEqual([], result["errors"])
                    self.assertEqual(2, result["totals"]["passed"])
                else:
                    self.assertTrue(result["errors"])
            if extra.exists():
                extra.unlink()

    def test_annotation_profile_stays_existing_api35_slot_and_does_not_change_all_full_slots(self):
        row, = matrix.matrix(r.ANDROID_WEBVIEW_REQUEST_FOCUS)["include"]
        self.assertEqual(("android-device-api35", "android-device", "35", "calf-webview"),
                         (row["slot"], row["suite"], row["emulator-api"], row["test-modules"]))
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_FOCUS, row["test-focus"])
        self.assertFalse(any(key.startswith("serial-") for key in row))
        all_rows = matrix.matrix("all")["include"]
        self.assertEqual([slot["slot"] for slot in matrix.SLOTS], [row["slot"] for row in all_rows])
        self.assertEqual(11, len(all_rows))
        self.assertTrue(all("test-focus" not in row for row in all_rows))
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        options = profile_options(workflow)
        self.assertEqual(1, options.count(r.ANDROID_WEBVIEW_REQUEST_FOCUS))
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)


if __name__ == "__main__":
    unittest.main()
