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
HELD_START_DIAGNOSTIC_TWO_METHOD_SOURCE_SHA256 = "0afe3cdee0d353bb8a531606c892ac2b317f1ebf848bb84bef8bc212e6790a3f"
ORIGINAL_SELECTED_SOURCE_SHA256 = "8b22586f28d0c228c3837c9660e47ecfb15e5a3534b3f587e533add1d82235a4"
HELD_START_DIAGNOSTIC_SELECTED_SOURCE_SHA256 = "4f92af5333784a8c79cfcd6c2f0192bb8517feba886f116d6c0813b0fbda9e1a"
ORIGINAL_METHOD_BODY_SHA256 = {
    "twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl":
        "6e07ff036d902271ad1b5347b556611dc3b978aae5945fb201e4048e02aa65d1",
    "publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner":
        "c6a1cc9662b38f6fd74d1d8f1a93c59e65825ea231ac6e227e8078a2ddce700a",
}


# Exact held-sequence historical identities. Current assertion-only identities below retain their inverse.
HELD_REQUEST_SEQUENCE_TWO_METHOD_SOURCE_SHA256 = "9e20cfa28b59157229f343838acdb9b8067a3ed3643f5b5aaf93aaf73e418ad8"
HELD_REQUEST_SEQUENCE_SELECTED_SOURCE_SHA256 = "d94c268cc1a1c3712a11d7e2b5b6350f6003057e64fc53af77155522b4ae3d98"
HELD_REQUEST_SEQUENCE_METHOD_BODY_SHA256 = {'twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl': '78c76a5cb63279131fb1736fbdf32e2bcb7591a698f676520f03209437fa277e', 'publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner': '0e2e3b3843f4b8c30950fe17dfffa3ef9c68c442f0b8e7e0e62f36276d7061f5'}


# Four assertion-only expectations on the original failed method. No helper/native criterion changes.
STOP_DECLARATIVE_CONTENT_SELECTED_SOURCE_SHA256 = 'a9512c990faade65b6a57b3045e4c0651ecd18380485164c44b8f59cf4fe5aa4'
STOP_DECLARATIVE_CONTENT_TWO_METHOD_SOURCE_SHA256 = '3fb923b293dec529b3b874285a4a998d7946d0c07d8db6a7fa7fdcc575216316'
STOP_DECLARATIVE_CONTENT_METHOD_BODY_SHA256 = {'twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl': '78c76a5cb63279131fb1736fbdf32e2bcb7591a698f676520f03209437fa277e', 'publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner': '684a194b4edf9fd1fc7bb036bf750dc473bc4e105f1f8c9688fe8378de85ee91'}
STOP_DECLARATIVE_CONTENT_FRAGMENT_IMAGES = (
    ('stop-before-public-invocation', '                    assertTrue(native.isAttachedToWindow)\n                    assertEquals(WebContent.Url(server.stopped.url), state.content)\n                    assertTrue(server.stopped.stopInvoked.compareAndSet(false, true))\n', '                    assertTrue(native.isAttachedToWindow)\n                    assertEquals(WebContent.Url(server.seed.url), state.content)\n                    assertTrue(server.stopped.stopInvoked.compareAndSet(false, true))\n'),
    ('redirect-terminal-document', '                    assertEquals(WebContent.Url(server.redirect.url), state.content)\n                    assertEquals(server.landing.url, native.url)\n                    assertEquals(server.landing.url, state.lastLoadedUrl)\n', '                    assertEquals(WebContent.Url(server.seed.url), state.content)\n                    assertEquals(server.landing.url, native.url)\n                    assertEquals(server.landing.url, state.lastLoadedUrl)\n'),
    ('reload-before-public-invocation', '                    assertSame(native, state.webView)\n                    assertEquals(WebContent.Url(server.redirect.url), state.content)\n                    assertEquals(server.landing.url, native.url)\n', '                    assertSame(native, state.webView)\n                    assertEquals(WebContent.Url(server.seed.url), state.content)\n                    assertEquals(server.landing.url, native.url)\n'),
    ('reload-terminal-requested-url', '                    assertEquals(WebContent.Url(server.redirect.url), state.content)\n                    assertEquals(reload.url, state.requestedUrl)\n', '                    assertEquals(WebContent.Url(server.seed.url), state.content)\n                    assertEquals(reload.url, state.requestedUrl)\n'),
)


def request_source_before_stop_content(source):
    """Evidence-only exact inverse; never a source exemption or compiler/native claim."""
    if hashlib.sha256(source.encode()).hexdigest() != STOP_DECLARATIVE_CONTENT_SELECTED_SOURCE_SHA256:
        raise ValueError("Only the exact four-assertion corrected Stop source image may be reversed")
    restored = source
    for name, before, after in STOP_DECLARATIVE_CONTENT_FRAGMENT_IMAGES:
        if restored.count(after) != 1:
            raise ValueError("Missing or duplicate exact Stop content assertion context: " + name)
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored.encode()).hexdigest() != HELD_REQUEST_SEQUENCE_SELECTED_SOURCE_SHA256:
        raise ValueError("Exact Stop content inverse did not restore the original failed-run source image")
    return restored


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

    def test_stripping_only_selection_metadata_preserves_both_original_bodies_and_exact_diagnostic_helpers(self):
        unselected = source_guard.request_source_without_selection_annotation(self.source)
        self.assertEqual(STOP_DECLARATIVE_CONTENT_TWO_METHOD_SOURCE_SHA256, hashlib.sha256(unselected.encode()).hexdigest())
        for method, expected in STOP_DECLARATIVE_CONTENT_METHOD_BODY_SHA256.items():
            with self.subTest(method=method):
                self.assertEqual(expected, hashlib.sha256(
                    source_guard.body_after(self.source, "@Test fun " + method).encode()).hexdigest())
        self.assertEqual(list(r.ANDROID_WEBVIEW_REQUEST_METHODS),
                         re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", unselected))

    def test_compiled_projection_keeps_exact_diagnostic_hash_and_refuses_partial_metadata_or_body_changes(self):
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
        self.assertNotEqual(STOP_DECLARATIVE_CONTENT_TWO_METHOD_SOURCE_SHA256,
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


# Exact reversible diagnostic-only fragments; never a regex or arbitrary-helper exemption.
DIAGNOSTIC_SOURCE_FRAGMENTS = (
    ('stop-held-helper',
     r'''    private fun awaitStopRedirectHeld(server: AndroidStopRedirectHttpServer, probe: AndroidStopRedirectProbe,
                                      native: AndroidWebView, stage: AndroidStopRedirectStage,
                                      expected: AndroidStopRedirectStage = stage) {
        waitFor("A forwarded native start and the exact still-held owned request", server, probe) {
            onMain { probe.hasStart(expected) && probe.ownerIs(native) } && stage.requests.get() > 0 && stage.pending.get() > 0
        }
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.replies.get())
        assertEquals(0, stage.peerEof.get())
        if (stage.reply != AndroidStopRedirectReply.WaitForStop) {
            assertFalse(stage.testReleased.get())
            assertEquals(1L, stage.permit.count)
        }
        onMain {
            probe.assertStarts(expected)
            val snapshot = probe.snapshot()
            assertNull(snapshot.loaded)
            assertNull(snapshot.title)
            assertTrue(snapshot.errors.isEmpty())
            assertIs<LoadingState.Loading>(snapshot.loading)
        }
    }

''',
     r'''    private fun awaitStopRedirectHeld(server: AndroidStopRedirectHttpServer, probe: AndroidStopRedirectProbe,
                                      native: AndroidWebView, stage: AndroidStopRedirectStage,
                                      expected: AndroidStopRedirectStage = stage) {
        var lastSample = "not sampled"
        observeHeldStartFailure({ lastSample }) {
            waitFor("A forwarded native start and the exact still-held owned request", server, probe) {
                val start = onMain {
                    Triple(probe.hasStart(expected), probe.ownerIs(native),
                        runCatching { probe.heldStartFacts(expected) }.getOrDefault("probeFacts=unavailable"))
                }
                val requests = stage.requests.get()
                val pending = stage.pending.get()
                lastSample = "stage=${stage.name} expected=${expected.name} hasStart=${start.first} " +
                    "sameOwner=${start.second} requests=$requests pending=$pending ${start.third} " +
                    "released=${stage.testReleased.get()} permit=${stage.permit.count} " +
                    "bytes=${stage.responseBytes.get()} replies=${stage.replies.get()} " +
                    "stopInvoked=${stage.stopInvoked.get()} peerEof=${stage.peerEof.get()}"
                start.first && start.second && requests > 0 && pending > 0
            }
        }
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.replies.get())
        assertEquals(0, stage.peerEof.get())
        if (stage.reply != AndroidStopRedirectReply.WaitForStop) {
            assertFalse(stage.testReleased.get())
            assertEquals(1L, stage.permit.count)
        }
        onMain {
            probe.assertStarts(expected)
            val snapshot = probe.snapshot()
            assertNull(snapshot.loaded)
            assertNull(snapshot.title)
            assertTrue(snapshot.errors.isEmpty())
            assertIs<LoadingState.Loading>(snapshot.loading)
        }
    }

'''),
    ('request-held-helper',
     r'''    private fun awaitHeldStart(server: AndroidRequestHttpServer, probe: AndroidRequestProbe, stage: AndroidRequestStage) {
        waitFor("A real onPageStarted and still-held exact owned HTTP request", server, probe) {
            onMain { probe.hasStart(stage) } && stage.attempts.get() > 0 && stage.pending.get() > 0
        }
        assertFalse(stage.testReleased.get(), "A pre-disconnected endpoint cannot prove the loading interval")
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.refused.get())
        assertEquals(0, stage.completed.get())
        onMain {
            probe.assertStarts(stage)
            val snapshot = probe.snapshot()
            assertEquals(stage.url, snapshot.requested)
            assertNull(snapshot.loaded)
            assertNull(snapshot.title)
            assertTrue(snapshot.errors.isEmpty())
            assertIs<LoadingState.Loading>(snapshot.loading)
        }
    }

''',
     r'''    private fun awaitHeldStart(server: AndroidRequestHttpServer, probe: AndroidRequestProbe, stage: AndroidRequestStage) {
        var lastSample = "not sampled"
        observeHeldStartFailure({ lastSample }) {
            waitFor("A real onPageStarted and still-held exact owned HTTP request", server, probe) {
                val start = onMain {
                    probe.hasStart(stage) to runCatching { probe.heldStartFacts(stage) }.getOrDefault("probeFacts=unavailable")
                }
                val attempts = stage.attempts.get()
                val pending = stage.pending.get()
                lastSample = "stage=${stage.name} hasStart=${start.first} attempts=$attempts pending=$pending ${start.second} " +
                    "released=${stage.testReleased.get()} gate=${stage.gate.count} " +
                    "bytes=${stage.responseBytes.get()} refused=${stage.refused.get()} completed=${stage.completed.get()}"
                start.first && attempts > 0 && pending > 0
            }
        }
        assertFalse(stage.testReleased.get(), "A pre-disconnected endpoint cannot prove the loading interval")
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.refused.get())
        assertEquals(0, stage.completed.get())
        onMain {
            probe.assertStarts(stage)
            val snapshot = probe.snapshot()
            assertEquals(stage.url, snapshot.requested)
            assertNull(snapshot.loaded)
            assertNull(snapshot.title)
            assertTrue(snapshot.errors.isEmpty())
            assertIs<LoadingState.Loading>(snapshot.loading)
        }
    }

'''),
    ('failure-attachment-helper',
     "",
     r'''/** Only already-sampled bounded facts; no new UI work, native action, or cause claim during unwind. */
private fun observeHeldStartFailure(lastSample: () -> String, wait: () -> Unit) {
    try { wait() } catch (primary: Throwable) {
        runCatching {
            primary.addSuppressed(AssertionError("Last held-start sample before unwind (not a cause): ${lastSample().take(768)}"))
        }
        throw primary // Preserve the original timeout/fixture/callback failure and its boundary.
    }
}

'''),
    ('AndroidRequestStage-probe-facts',
     "",
     r'''    fun heldStartFacts(stage: AndroidRequestStage) = "current=${isCurrent(stage)} ownerPresent=${owner.webView != null} " +
        "generation=${active?.generation ?: 0} starts=${active?.starts?.size ?: 0} " +
        "finishes=${active?.finishes?.size ?: 0} nativeErrors=${active?.errors?.size ?: 0}"
'''),
    ('AndroidStopRedirectStage-probe-facts',
     "",
     r'''    fun heldStartFacts(stage: AndroidStopRedirectStage) = "current=${isCurrent(stage)} ownerPresent=${owner.webView != null} " +
        "generation=${active?.generation ?: 0} starts=${active?.starts?.size ?: 0} " +
        "finishes=${active?.finishes?.size ?: 0} nativeErrors=${active?.errors?.size ?: 0}"
'''),
)


# The historical diagnostic-only fragment tuple above is intentionally unchanged.
# Reverse only ONE exact current whole after image, then ONE exact historical diagnostic
# image. No broad regex, helper stripping, unrecognized source or planner execution.
HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES = {name: (before, after)
                                       for name, before, after in DIAGNOSTIC_SOURCE_FRAGMENTS}
HELD_REQUEST_SEQUENCE_SOURCE_FRAGMENTS = (
    ('request-failure-held-call',
     r'''awaitHeldStart(server, probe, stage)''',
     r'''awaitHeldRequest(server, probe, native, stage)'''),
    ('request-recovery-held-call',
     r'''awaitHeldStart(server, probe, server.recovery)''',
     r'''awaitHeldRequest(server, probe, native, server.recovery)'''),
    ('request-reload-held-call',
     r'''awaitHeldStart(server, probe, reload)''',
     r'''awaitHeldRequest(server, probe, native, reload)'''),
    ('stop-redirect-marker',
     r'''    // New #64 Stop/redirect fixture; the compiled fail/fail method above remains unchanged.
''',
     r'''    // #64 Stop/redirect fixture retains genuine native callbacks and exact owned HTTP.
'''),
    ('stop-held-call',
     r'''awaitStopRedirectHeld(server, probe, native, server.stopped)''',
     r'''awaitStopRedirectHeldRequest(server, probe, native, server.stopped)'''),
    ('redirect-held-call',
     r'''awaitStopRedirectHeld(server, probe, native, server.redirect, expected = server.landing)''',
     r'''awaitStopRedirectHeldRequest(server, probe, native, server.redirect, expected = server.landing)'''),
    ('landing-held-call',
     r'''awaitStopRedirectHeld(server, probe, native, server.landing)''',
     r'''awaitStopRedirectHeldRequest(server, probe, native, server.landing)'''),
    ('stop-reload-held-call',
     r'''awaitStopRedirectHeld(server, probe, native, reload)''',
     r'''awaitStopRedirectHeldRequest(server, probe, native, reload)'''),
    ('stop-held-helper',
     HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES["stop-held-helper"][1],
     r'''    private fun awaitStopRedirectHeldRequest(server: AndroidStopRedirectHttpServer, probe: AndroidStopRedirectProbe,
                                      native: AndroidWebView, stage: AndroidStopRedirectStage,
                                      expected: AndroidStopRedirectStage = stage) {
        var lastSample = "not sampled"
        observeHeldStartFailure({ lastSample }) {
            waitFor("The current native owner and exact still-held owned request", server, probe) {
                val lease = onMain {
                    Triple(probe.isCurrent(expected), probe.ownerIs(native),
                        runCatching { probe.heldStartFacts(expected) }.getOrDefault("probeFacts=unavailable"))
                }
                val requests = stage.requests.get()
                val pending = stage.pending.get()
                lastSample = "stage=${stage.name} expected=${expected.name} current=${lease.first} " +
                    "sameOwner=${lease.second} requests=$requests pending=$pending ${lease.third} " +
                    "released=${stage.testReleased.get()} permit=${stage.permit.count} " +
                    "bytes=${stage.responseBytes.get()} replies=${stage.replies.get()} " +
                    "stopInvoked=${stage.stopInvoked.get()} peerEof=${stage.peerEof.get()}"
                lease.first && lease.second && requests > 0 && pending > 0
            }
        }
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.replies.get())
        assertEquals(0, stage.peerEof.get())
        if (stage.reply != AndroidStopRedirectReply.WaitForStop) {
            assertFalse(stage.testReleased.get())
            assertEquals(1L, stage.permit.count)
        }
        onMain {
            assertTrue(probe.isCurrent(expected))
            assertTrue(probe.ownerIs(native))
            if (stage.reply == AndroidStopRedirectReply.WaitForStop) {
                // This is the real public LoadUrl acceptance, not a manufactured native start.
                val snapshot = probe.snapshot()
                assertEquals(stage.url, snapshot.requested)
                assertNull(snapshot.loaded)
                assertNull(snapshot.title)
                assertTrue(snapshot.errors.isEmpty())
                assertIs<LoadingState.Loading>(snapshot.loading)
            }
        }
    }

'''),
    ('request-held-helper',
     HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES["request-held-helper"][1],
     r'''    private fun awaitHeldRequest(server: AndroidRequestHttpServer, probe: AndroidRequestProbe,
                                 native: AndroidWebView, stage: AndroidRequestStage) {
        var lastSample = "not sampled"
        observeHeldStartFailure({ lastSample }) {
            waitFor("The current native owner and still-held exact owned HTTP request", server, probe) {
                val lease = onMain {
                    Triple(probe.isCurrent(stage), probe.ownerIs(native),
                        runCatching { probe.heldStartFacts(stage) }.getOrDefault("probeFacts=unavailable"))
                }
                val attempts = stage.attempts.get()
                val pending = stage.pending.get()
                lastSample = "stage=${stage.name} current=${lease.first} sameOwner=${lease.second} " +
                    "attempts=$attempts pending=$pending ${lease.third} " +
                    "released=${stage.testReleased.get()} gate=${stage.gate.count} " +
                    "bytes=${stage.responseBytes.get()} refused=${stage.refused.get()} completed=${stage.completed.get()}"
                lease.first && lease.second && attempts > 0 && pending > 0
            }
        }
        assertFalse(stage.testReleased.get(), "A pre-disconnected endpoint cannot prove the loading interval")
        assertEquals(1L, stage.gate.count)
        assertEquals(0, stage.responseBytes.get())
        assertEquals(0, stage.refused.get())
        assertEquals(0, stage.completed.get())
        onMain {
            assertTrue(probe.isCurrent(stage))
            assertTrue(probe.ownerIs(native))
        }
        // The native load intentionally bypasses acceptContent. Do not reset or demand reset
        // before Chromium can emit its genuine onPageStarted after the held response/refusal.
        // That forwarded callback records and asserts the reset at its own actual boundary.
    }

'''),
    ('request-owner-readback',
     r'''    fun isCurrent(stage: AndroidRequestStage) = active?.stage === stage
''',
     r'''    fun isCurrent(stage: AndroidRequestStage) = active?.stage === stage
    fun ownerIs(native: AndroidWebView) = owner.webView === native
'''),
    ('AndroidRequestStage-probe-facts',
     HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES['AndroidRequestStage-probe-facts'][1],
     r'''    fun heldStartFacts(stage: AndroidRequestStage) = "current=${isCurrent(stage)} ownerPresent=${owner.webView != null} " +
        "hasStart=${hasStart(stage)} generation=${active?.generation ?: 0} starts=${active?.starts?.size ?: 0} " +
        "finishes=${active?.finishes?.size ?: 0} nativeErrors=${active?.errors?.size ?: 0}"
'''),
    ('AndroidStopRedirectStage-probe-facts',
     HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES['AndroidStopRedirectStage-probe-facts'][1],
     r'''    fun heldStartFacts(stage: AndroidStopRedirectStage) = "current=${isCurrent(stage)} ownerPresent=${owner.webView != null} " +
        "hasStart=${hasStart(stage)} generation=${active?.generation ?: 0} starts=${active?.starts?.size ?: 0} " +
        "finishes=${active?.finishes?.size ?: 0} nativeErrors=${active?.errors?.size ?: 0}"
'''),
    ('request-start-callback',
     r'''    override fun onPageStarted(view: AndroidWebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        observe(view) {
            val observed = checkNotNull(active)
            check(url == observed.stage.url && ++serial <= 32)
            observed.generation = serial
            observed.starts += snapshot()
        }
    }
''',
     r'''    override fun onPageStarted(view: AndroidWebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        observe(view) {
            val observed = checkNotNull(active)
            check(url == observed.stage.url && ++serial <= 32)
            observed.generation = serial
            observed.starts += snapshot()
            assertStarts(observed.stage) // Assert only after this genuine forwarded native start.
        }
    }
'''),
    ('stop-finish-predicate',
     r'''    fun finished(stage: AndroidStopRedirectStage) = hasStart(stage) && active!!.finishes.any { it.first == active!!.generation }
''',
     r'''    fun finished(stage: AndroidStopRedirectStage) = isCurrent(stage) &&
        (hasStart(stage) || (stage.reply == AndroidStopRedirectReply.WaitForStop && stage.stopInvoked.get())) &&
        active!!.finishes.any { it.first == active!!.generation }
'''),
    ('stop-terminal-shape',
     r'''    fun assertTerminal(stage: AndroidStopRedirectStage, native: AndroidWebView, stopped: Boolean) {
        assertSame(native, owner.webView); assertTrue(native.isAttachedToWindow)
        assertStarts(stage); assertTrue(finished(stage))
        val observed = active!!
        val nativeErrors = observed.errors.filter { it.generation == observed.generation && it.code != null }
            .map { it.code!! to (it.description ?: "Unknown error") }
        assertEquals(nativeErrors, snapshot().errors) // No resource-error filtering or invented cancellation error.
        assertTrue(nativeErrors.isEmpty())
        assertEquals(stage.url, snapshot().loaded)
        assertEquals(LoadingState.Finished, snapshot().loading)
        assertFalse(owner.isLoading)
        if (stopped) {
            assertNull(snapshot().title) // No response/document title was received for the stopped request.
        } else {
            assertEquals(stage.title, snapshot().title)
            assertEquals(stage.url, native.url)
            assertEquals(stage.title, native.title)
        }
    }
''',
     r'''    fun assertTerminal(stage: AndroidStopRedirectStage, native: AndroidWebView, stopped: Boolean) {
        assertSame(native, owner.webView); assertTrue(native.isAttachedToWindow)
        assertEquals(stopped, stage.reply == AndroidStopRedirectReply.WaitForStop)
        assertTrue(finished(stage))
        val observed = active!!
        if (stopped && !hasStart(stage)) {
            assertTrue(stage.stopInvoked.get())
            assertEquals(0, observed.generation) // No start generation was fabricated for a precommit abort.
            assertTrue(observed.starts.isEmpty())
        } else assertStarts(stage)
        val nativeErrors = observed.errors.filter { it.generation == observed.generation && it.code != null }
            .map { it.code!! to (it.description ?: "Unknown error") }
        assertEquals(nativeErrors, snapshot().errors) // No resource-error filtering or invented cancellation error.
        assertEquals(stage.url, snapshot().requested)
        assertTrue(nativeErrors.isEmpty())
        assertEquals(stage.url, snapshot().loaded)
        assertEquals(LoadingState.Finished, snapshot().loading)
        assertFalse(owner.isLoading)
        if (stopped) {
            assertNull(snapshot().title) // No response/document title was received for the stopped request.
        } else {
            assertEquals(stage.title, snapshot().title)
            assertEquals(stage.url, native.url)
            assertEquals(stage.title, native.title)
        }
    }
'''),
    ('stop-start-callback',
     r'''    override fun onPageStarted(view: AndroidWebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        watch(view) {
            val observed = checkNotNull(active)
            val started = checkNotNull(url)
            check(started in observed.startUrls && ++serial <= 32)
            observed.generation = serial
            observed.starts += started to snapshot()
        }
    }
''',
     r'''    override fun onPageStarted(view: AndroidWebView, url: String?, favicon: Bitmap?) {
        super.onPageStarted(view, url, favicon)
        watch(view) {
            val observed = checkNotNull(active)
            val started = checkNotNull(url)
            check(started in observed.startUrls && ++serial <= 32)
            observed.generation = serial
            observed.starts += started to snapshot()
            assertStarts(observed.stage) // A real start still must reset state at this callback boundary.
        }
    }
'''),
    ('stop-finish-callback',
     r'''    override fun onPageFinished(view: AndroidWebView, url: String?) {
        super.onPageFinished(view, url)
        watch(view) {
            val observed = checkNotNull(active)
            if (url == observed.stage.url) {
                check(observed.generation > 0 && observed.finishes.size < 32)
                observed.finishes += observed.generation to snapshot()
            }
        }
    }
''',
     r'''    override fun onPageFinished(view: AndroidWebView, url: String?) {
        super.onPageFinished(view, url)
        watch(view) {
            val observed = checkNotNull(active)
            if (url == observed.stage.url) {
                check(observed.finishes.size < 32)
                check(observed.generation > 0 ||
                    (observed.stage.reply == AndroidStopRedirectReply.WaitForStop && observed.stage.stopInvoked.get()))
                // Only this real matching finish may witness an unchanged generation-zero Stop.
                observed.finishes += observed.generation to snapshot()
            }
        }
    }
'''),
)


class AndroidHeldStartDiagnosticGuardControls(unittest.TestCase):
    """New diagnostic-specific source refusals only; never native or selector-suite acceptance."""
    def setUp(self):
        self.source = (r.ROOT / r.ANDROID_WEBVIEW_REQUEST_SOURCE).read_text()
        self.fragments = dict(HISTORICAL_DIAGNOSTIC_FRAGMENT_IMAGES)
        self.fragments.update({name: (before, after)
                               for name, before, after in HELD_REQUEST_SEQUENCE_SOURCE_FRAGMENTS})

    def changed_fragment(self, name, before, after):
        fragment = self.fragments[name][1]
        self.assertEqual(1, self.source.count(fragment), "Mutation must target the current exact source fragment")
        self.assertEqual(1, fragment.count(before))
        return self.source.replace(fragment, fragment.replace(before, after, 1), 1)

    def reject(self, candidates, validator=source_guard.compiled_request_source):
        for label, candidate in candidates:
            with self.subTest(rejection=label), self.assertRaises((ValueError, AssertionError)):
                validator(candidate)

    def original_source_before_sequencing(self, source):
        # Bind and reverse only the four exact current assertions before the unchanged historical barriers.
        restored = request_source_before_stop_content(source)
        if hashlib.sha256(restored.encode()).hexdigest() != HELD_REQUEST_SEQUENCE_SELECTED_SOURCE_SHA256:
            raise ValueError("Only the exact sealed owning sequence after image may be reversed")
        for name, before, after in HELD_REQUEST_SEQUENCE_SOURCE_FRAGMENTS:
            if restored.count(after) != 1:
                raise ValueError("Missing or duplicate exact owning sequence fragment: " + name)
            restored = restored.replace(after, before, 1)
        if hashlib.sha256(restored.encode()).hexdigest() != HELD_START_DIAGNOSTIC_SELECTED_SOURCE_SHA256:
            raise ValueError("Exact sequence reversal did not restore the frozen f984 diagnostic image")
        return restored

    def original_source_before_diagnostics(self, source):
        # The current and then historical exact after-image barriers precede all reversal.
        # compiled_request_source never calls this evidence helper or strips diagnostic bytes.
        restored = self.original_source_before_sequencing(source)
        if hashlib.sha256(restored.encode()).hexdigest() != HELD_START_DIAGNOSTIC_SELECTED_SOURCE_SHA256:
            raise ValueError("Only the exact frozen diagnostic image may be reversed")
        for name, before, after in DIAGNOSTIC_SOURCE_FRAGMENTS:
            if restored.count(after) != 1:
                raise ValueError("Missing or duplicate exact diagnostic fragment: " + name)
            restored = restored.replace(after, before, 1)
        if hashlib.sha256(restored.encode()).hexdigest() != ORIGINAL_SELECTED_SOURCE_SHA256:
            raise ValueError("Exact diagnostic reversal did not restore the frozen original file")
        return restored

    def whole_selector_guard(self, source):
        # Exercise only the owning adapted whole-helper guard, not the other accepted selector models.
        case = AndroidWebViewRequestSelectorModels()
        case.source = source
        case.test_stripping_only_selection_metadata_preserves_both_original_bodies_and_exact_diagnostic_helpers()

    def complete_native_guards(self, source):
        source_guard.require_native_witnesses(source)
        source_guard.require_stop_redirect_witnesses(source)

    def test_exact_fragments_restore_original_file_bodies_and_both_precise_hash_advances(self):
        before = self.original_source_before_diagnostics(self.source)
        self.assertEqual(ORIGINAL_SELECTED_SOURCE_SHA256, hashlib.sha256(before.encode()).hexdigest())
        unselected_before = source_guard.request_source_without_selection_annotation(before)
        self.assertEqual(ORIGINAL_TWO_METHOD_SOURCE_SHA256, hashlib.sha256(unselected_before.encode()).hexdigest())
        start = unselected_before.index(source_guard.HISTORICAL_STOP_REDIRECT_MEMBER_MARKER)
        end = unselected_before.index(source_guard.HISTORICAL_REQUEST_HELD_HELPER_ANCHOR, start)
        helper = unselected_before.index(source_guard.STOP_REDIRECT_HELPER_MARKER, end)
        original_projection = unselected_before[:start] + unselected_before[end:helper]
        self.assertEqual(source_guard.ORIGINAL_COMPILED_ANDROID_REQUEST_SOURCE_SHA256,
                         hashlib.sha256(original_projection.encode()).hexdigest())
        diagnostic = self.original_source_before_sequencing(self.source)
        self.assertEqual(HELD_START_DIAGNOSTIC_SELECTED_SOURCE_SHA256, hashlib.sha256(diagnostic.encode()).hexdigest())
        self.assertEqual(HELD_START_DIAGNOSTIC_TWO_METHOD_SOURCE_SHA256, hashlib.sha256(
            source_guard.request_source_without_selection_annotation(diagnostic).encode()).hexdigest())
        historical_unselected = source_guard.request_source_without_selection_annotation(diagnostic)
        historical_start = historical_unselected.index(source_guard.HISTORICAL_STOP_REDIRECT_MEMBER_MARKER)
        historical_end = historical_unselected.index(source_guard.HISTORICAL_REQUEST_HELD_HELPER_ANCHOR, historical_start)
        historical_helper = historical_unselected.index(source_guard.STOP_REDIRECT_HELPER_MARKER, historical_end)
        historical_projection = historical_unselected[:historical_start] + historical_unselected[historical_end:historical_helper]
        self.assertEqual(source_guard.HELD_START_DIAGNOSTIC_COMPILED_SOURCE_SHA256,
                         hashlib.sha256(historical_projection.encode()).hexdigest())
        self.assertEqual(STOP_DECLARATIVE_CONTENT_TWO_METHOD_SOURCE_SHA256, hashlib.sha256(
            source_guard.request_source_without_selection_annotation(self.source).encode()).hexdigest())
        self.assertEqual(source_guard.COMPILED_ANDROID_REQUEST_SOURCE_SHA256, hashlib.sha256(
            source_guard.compiled_request_source(self.source).encode()).hexdigest())
        self.assertNotEqual(source_guard.ORIGINAL_COMPILED_ANDROID_REQUEST_SOURCE_SHA256,
                            source_guard.COMPILED_ANDROID_REQUEST_SOURCE_SHA256)
        for method, digest in ORIGINAL_METHOD_BODY_SHA256.items():
            for image in (before, diagnostic):
                with self.subTest(method=method, before=image is before):
                    self.assertEqual(digest, hashlib.sha256(
                        source_guard.body_after(image, "@Test fun " + method).encode()).hexdigest())
        self.whole_selector_guard(self.source)  # Current exact body hashes include only reviewed helper call changes.
        self.complete_native_guards(self.source)

    def test_literal_reversal_refuses_old_partial_mutated_or_unknown_after_images(self):
        before = self.original_source_before_diagnostics(self.source)
        observer = self.fragments["failure-attachment-helper"][1]
        request = self.fragments["AndroidRequestStage-probe-facts"][1]
        self.reject([
            ("unchanged-original-is-not-the-current-after-image", before),
            ("previous-diagnostic-image-is-not-the-current-after-image", self.original_source_before_sequencing(self.source)),
            ("partial-request-facts", self.source.replace(request, "", 1)),
            ("duplicate-attachment", self.source.replace(observer, observer + observer, 1)),
            ("changed-sample-bound", self.changed_fragment("failure-attachment-helper", "lastSample().take(768)", "lastSample().take(767)")),
            ("unknown-native-helper", self.source + "\nprivate fun unknownNative() { native.destroy() }\n"),
            ("partial-selector-metadata", self.source.replace("    @" + ANNOTATION_NAME + "\n", "", 1)),
        ], self.original_source_before_diagnostics)

    def test_partial_duplicate_moved_or_extra_excluded_diagnostic_helpers_refuse(self):
        stop = self.fragments["AndroidStopRedirectStage-probe-facts"][1]
        request = self.fragments["AndroidRequestStage-probe-facts"][1]
        observer = self.fragments["failure-attachment-helper"][1]
        self.reject([
            ("missing-stop-facts", self.source.replace(stop, "", 1)),
            ("duplicate-stop-facts", self.source.replace(stop, stop + stop, 1)),
            ("moved-stop-facts", self.source.replace(stop, "", 1) + stop),
            ("stop-held-signature-change", self.source.replace("native: AndroidWebView, stage: AndroidStopRedirectStage,", "native: Any, stage: AndroidStopRedirectStage,", 1)),
            ("missing-stop-held-call", self.changed_fragment("stop-held-helper", "observeHeldStartFailure({ lastSample })", "run")),
            ("extra-hidden-fact-helper", self.source + "\n" + request),
            ("extra-hidden-observer-call", self.source + "\nfun hidden() { observeHeldStartFailure({ \"hidden\" }) {} }\n"),
            ("missing-attachment-helper", self.source.replace(observer, "", 1)),
            ("missing-request-facts", self.source.replace(request, "", 1)),
        ])

    def test_exact_current_owner_and_acquired_held_request_operands_remain_required(self):
        # Original acceptance deadlines and genuine callback resets remain; no pre-header start gate.
        self.reject([
            ("request-current-removed", self.changed_fragment("request-held-helper", "lease.first && lease.second && attempts > 0 && pending > 0", "lease.second && attempts > 0 && pending > 0")),
            ("request-owner-removed", self.changed_fragment("request-held-helper", "lease.first && lease.second && attempts > 0 && pending > 0", "lease.first && attempts > 0 && pending > 0")),
            ("request-attempt-zero", self.changed_fragment("request-held-helper", "lease.first && lease.second && attempts > 0 && pending > 0", "lease.first && lease.second && attempts >= 0 && pending > 0")),
            ("request-pending-zero", self.changed_fragment("request-held-helper", "lease.first && lease.second && attempts > 0 && pending > 0", "lease.first && lease.second && attempts > 0 && pending >= 0")),
            ("stop-current-or-owner", self.changed_fragment("stop-held-helper", "lease.first && lease.second && requests > 0 && pending > 0", "lease.first || lease.second && requests > 0 && pending > 0")),
            ("stop-request-zero", self.changed_fragment("stop-held-helper", "lease.first && lease.second && requests > 0 && pending > 0", "lease.first && lease.second && requests >= 0 && pending > 0")),
            ("stop-pending-zero", self.changed_fragment("stop-held-helper", "lease.first && lease.second && requests > 0 && pending > 0", "lease.first && lease.second && requests > 0 && pending >= 0")),
            ("stop-owner-guessed", self.changed_fragment("stop-held-helper", "Triple(probe.isCurrent(expected), probe.ownerIs(native),", "Triple(probe.isCurrent(expected), true,")),
            ("stop-current-guessed", self.changed_fragment("stop-held-helper", "Triple(probe.isCurrent(expected), probe.ownerIs(native),", "Triple(true, probe.ownerIs(native),")),
            ("request-owner-guessed", self.changed_fragment("request-held-helper", "Triple(probe.isCurrent(stage), probe.ownerIs(native),", "Triple(probe.isCurrent(stage), true,")),
            ("request-current-guessed", self.changed_fragment("request-held-helper", "Triple(probe.isCurrent(stage), probe.ownerIs(native),", "Triple(true, probe.ownerIs(native),")),
        ])

    def test_optional_probe_facts_cannot_emit_private_values_or_mutate_native_owner(self):
        self.reject([
            ("request-native-url", self.changed_fragment("AndroidRequestStage-probe-facts", "ownerPresent=${owner.webView != null}", "ownerUrl=${owner.webView?.url}")),
            ("stop-native-title", self.changed_fragment("AndroidStopRedirectStage-probe-facts", "ownerPresent=${owner.webView != null}", "ownerTitle=${owner.webView?.title}")),
            ("request-error-body", self.changed_fragment("AndroidRequestStage-probe-facts", "nativeErrors=${active?.errors?.size ?: 0}", "nativeErrors=${active?.errors}")),
            ("stop-native-action", self.changed_fragment("stop-held-helper", "runCatching { probe.heldStartFacts(expected) }", "runCatching { native.stopLoading(); probe.heldStartFacts(expected) }")),
            ("request-diagnostic-read-can-throw", self.changed_fragment("request-held-helper", 'runCatching { probe.heldStartFacts(stage) }.getOrDefault("probeFacts=unavailable")', "probe.heldStartFacts(stage)")),
            ("stop-diagnostic-read-can-throw", self.changed_fragment("stop-held-helper", 'getOrDefault("probeFacts=unavailable")', "getOrThrow()")),
            ("stop-stage-url-output", self.changed_fragment("stop-held-helper", '"stage=${stage.name} expected=${expected.name}', '"url=${stage.url} expected=${expected.name}')),
        ])

    def test_primary_throwable_bounded_last_sample_and_no_unwind_ui_work_stay_exact(self):
        self.reject([
            ("primary-swallowed", self.changed_fragment("failure-attachment-helper", "throw primary //", "return //")),
            ("primary-replaced", self.changed_fragment("failure-attachment-helper", "primary.addSuppressed(AssertionError(", "throw AssertionError(")),
            ("sample-cap-expanded", self.changed_fragment("failure-attachment-helper", "lastSample().take(768)", "lastSample().take(4096)")),
            ("attachment-can-mask-primary", self.changed_fragment("failure-attachment-helper", "runCatching {", "run {")),
            ("new-main-work-during-unwind", self.changed_fragment("failure-attachment-helper", "primary.addSuppressed(", "onMain { native.reload() }; primary.addSuppressed(")),
            ("false-cause-claim", self.changed_fragment("failure-attachment-helper", "before unwind (not a cause)", "before unwind (proved cause)")),
        ])

    def test_diagnostics_cannot_release_respond_reset_start_or_supply_public_stop(self):
        self.reject([
            ("stop-release-in-wait", self.changed_fragment("stop-held-helper", "val requests = stage.requests.get()", "stage.releaseForTest(); val requests = stage.requests.get()")),
            ("response-write-in-wait", self.changed_fragment("request-held-helper", "val attempts = stage.attempts.get()", "socket.getOutputStream().write(1); val attempts = stage.attempts.get()")),
            ("request-helper-reset", self.changed_fragment("request-held-helper", "Triple(probe.isCurrent(stage), probe.ownerIs(native),", "probe.arm(stage); Triple(probe.isCurrent(stage), probe.ownerIs(native),")),
            ("synthetic-start", self.changed_fragment("stop-held-helper", "Triple(probe.isCurrent(expected), probe.ownerIs(native),", "probe.onPageStarted(native, stage.url, null); Triple(probe.isCurrent(expected), probe.ownerIs(native),")),
            ("early-stop-mark", self.changed_fragment("stop-held-helper", "val pending = stage.pending.get()", "stage.stopInvoked.set(true); val pending = stage.pending.get()")),
            ("zero-byte-assertion-weakened", self.changed_fragment("stop-held-helper", "assertEquals(0, stage.responseBytes.get())", "assertTrue(stage.responseBytes.get() >= 0)")),
        ])

    def test_full_source_manual_reset_still_refuses_before_any_diagnostic_projection(self):
        candidates = [
            ("attachment-body-reset", self.changed_fragment("failure-attachment-helper", "runCatching {", "runCatching { state.errorsForCurrentRequest = emptyList();")),
            ("separate-stop-wait-reset", self.changed_fragment("stop-held-helper", "val requests = stage.requests.get()", "state.errorsForCurrentRequest = emptyList(); val requests = stage.requests.get()")),
            ("separate-stop-fact-reset", self.changed_fragment("AndroidStopRedirectStage-probe-facts", "    fun heldStartFacts(", "    fun masked() { state.errorsForCurrentRequest = emptyList() }\n    fun heldStartFacts(")),
        ]
        for label, candidate in candidates:
            with self.subTest(rejection=label), self.assertRaisesRegex(ValueError, "Manual request resets are forbidden anywhere in the full native fixture"):
                source_guard.require_native_witnesses(candidate)

    def test_retained_diagnostic_bytes_cannot_hide_unknown_helpers_with_a_broad_projection(self):
        observer = self.fragments["failure-attachment-helper"][1]
        marker = source_guard.STOP_REDIRECT_HELPER_MARKER
        self.reject([
            ("unknown-helper-after-attachment", self.source.replace(observer, observer + "private fun unrelatedNativeAction() { native.destroy() }\n\n", 1)),
            ("unknown-helper-before-separate-layer", self.source.replace(marker, "\nprivate fun alternateStartWitness() = true\n" + marker, 1)),
            ("diagnostic-like-unrecognized-helper", self.source.replace(observer, observer + "private fun heldStartFactsFallback() = true\n\n", 1)),
        ])

    def test_whole_selector_hash_advance_still_refuses_unrelated_native_body_and_helper_changes(self):
        second = source_guard.body_after(self.source, "@Test fun " + source_guard.STOP_REDIRECT_METHOD)
        changed_second = second.replace("assertEquals(0, server.stopped.peerEof.get()", "assertEquals(1, server.stopped.peerEof.get()", 1)
        self.assertNotEqual(second, changed_second)
        members_start = self.source.index(source_guard.STOP_REDIRECT_MEMBER_MARKER)
        members_end = self.source.index(source_guard.REQUEST_HELD_HELPER_ANCHOR, members_start)
        members = self.source[members_start:members_end]
        changed_members = members.replace("SystemClock.elapsedRealtime() + 10_000", "SystemClock.elapsedRealtime() + 1_000", 1)
        self.assertNotEqual(members, changed_members)
        self.reject([
            ("second-method-pre-stop-eof-weakened", self.source.replace(second, changed_second, 1)),
            ("separate-wait-deadline-changed", self.source[:members_start] + changed_members + self.source[members_end:]),
            ("unknown-separate-native-helper", self.source + "\nprivate fun unrelatedNativeAction() { native.destroy() }\n"),
            ("separate-probe-generation-guessed", self.source.replace("observed.generation = serial", "observed.generation = 1")),
            ("native-owner-disposal-assertion-removed", self.source.replace("assertEquals(0, fixture.disposed.get())", "assertTrue(fixture.disposed.get() >= 0)")),
            ("arbitrary-new-helper", self.source + "\nprivate fun arbitrary() = true\n"),
        ], self.whole_selector_guard)

    def test_new_diagnostics_cannot_waive_original_forwarding_eof_or_finite_native_bounds(self):
        marker = source_guard.STOP_REDIRECT_HELPER_MARKER
        start = self.source.index(marker)
        prefix, separate = self.source[:start], self.source[start:]
        self.reject([
            ("stop-forwarded-finish-removed", prefix + separate.replace("super.onPageFinished(view, url)", "Unit", 1)),
            ("stop-peer-reader-deadline-expanded", prefix + separate.replace("socket.soTimeout = 15_000", "socket.soTimeout = 30_000", 1)),
            ("stop-route-limit-expanded", prefix + separate.replace("owned.requests.incrementAndGet() <= 16", "owned.requests.incrementAndGet() <= 17", 1)),
            ("stop-header-limit-expanded", prefix + separate.replace("buffer.size() < 8_192", "buffer.size() < 8_193", 1)),
            ("request-held-gate-deadline-expanded", self.source.replace("owned.gate.await(15, TimeUnit.SECONDS)", "owned.gate.await(30, TimeUnit.SECONDS)", 1)),
            ("stop-mark-check-inverted", prefix + separate.replace("check(route.stopInvoked.get())", "check(!route.stopInvoked.get())", 1)),
        ], self.complete_native_guards)


    def test_only_wait_for_stop_can_finish_without_start_after_public_latch_and_actual_matching_callback(self):
        self.complete_native_guards(self.source)
        self.reject([
            ("no-start-for-non-stop", self.changed_fragment("stop-finish-predicate", "(hasStart(stage) || (stage.reply == AndroidStopRedirectReply.WaitForStop && stage.stopInvoked.get()))", "(hasStart(stage) || stage.stopInvoked.get())")),
            ("zero-finish-before-public-stop", self.changed_fragment("stop-finish-predicate", "&& stage.stopInvoked.get()", "&& true")),
            ("foreign-stage-finish", self.changed_fragment("stop-finish-predicate", "= isCurrent(stage) &&", "= true &&")),
            ("missing-real-finish-record", self.changed_fragment("stop-finish-predicate", "active!!.finishes.any { it.first == active!!.generation }", "true")),
            ("unmatched-native-finish-url", self.changed_fragment("stop-finish-callback", "if (url == observed.stage.url)", "if (true)")),
            ("zero-callback-before-public-stop", self.changed_fragment("stop-finish-callback", "&& observed.stage.stopInvoked.get()", "&& true")),
            ("zero-record-fabricated-for-positive-start", self.changed_fragment("stop-finish-callback", "observed.finishes += observed.generation to snapshot()", "observed.finishes += 0 to snapshot()")),
            ("zero-terminal-for-document", self.changed_fragment("stop-terminal-shape", "if (stopped && !hasStart(stage))", "if (!hasStart(stage))")),
            ("zero-terminal-kind-unchecked", self.changed_fragment("stop-terminal-shape", "assertEquals(stopped, stage.reply == AndroidStopRedirectReply.WaitForStop)", "Unit")),
            ("zero-generation-manufactured", self.changed_fragment("stop-terminal-shape", "assertEquals(0, observed.generation)", "observed.generation = 0")),
            ("zero-terminal-starts-not-empty", self.changed_fragment("stop-terminal-shape", "assertTrue(observed.starts.isEmpty())", "Unit")),
        ], self.complete_native_guards)

    def test_real_start_reset_assertions_and_nonstop_positive_generation_cannot_be_waived(self):
        request_finish = "fun finished(stage: AndroidRequestStage) = hasStart(stage) &&"
        self.assertEqual(1, self.source.count(request_finish))
        self.reject([
            ("request-reset-observation-removed", self.changed_fragment("request-start-callback", "assertStarts(observed.stage)", "Unit")),
            ("stop-reset-observation-removed", self.changed_fragment("stop-start-callback", "assertStarts(observed.stage)", "Unit")),
            ("request-helper-reset-instead-of-callback-assertion", self.changed_fragment("request-start-callback", "assertStarts(observed.stage)", "owner.beginRequest(observed.stage.url)")),
            ("nonstop-finish-without-positive-start", self.source.replace(request_finish, "fun finished(stage: AndroidRequestStage) = isCurrent(stage) &&", 1)),
            ("error-without-positive-start", self.source.replace("check(observed.generation > 0 && observed.errors.size < 64)", "check(observed.generation >= 0 && observed.errors.size < 64)")),
        ], self.complete_native_guards)

if __name__ == "__main__":
    unittest.main()
