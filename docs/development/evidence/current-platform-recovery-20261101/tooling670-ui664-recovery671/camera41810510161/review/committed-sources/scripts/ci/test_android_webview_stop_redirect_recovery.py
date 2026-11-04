# SPDX-License-Identifier: Apache-2.0
"""New Stop1-only source/selector/XML controls. Never Gradle, emulator or native acceptance."""
from collections import Counter
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import android_device_tests as controller
import library_tests as r
import test_android_webview_request_selector as selector_guard
import test_android_webview_request_state as source_guard
from test_ios_io_profile import profile_options
import workflow_matrix as matrix


FOCUS = "android-webview-stop-redirect-recovery"
STOP = "publicNavigatorStopClosesHeldTransportAndActual302RedirectReloadUsesCurrentOwner"
ACCEPTED = "twoHeldNativeTransportFailuresResetErrorsAndNativeReloadUsesCurrentOwnerUrl"
ACCEPTED_BODY_SHA256 = "78c76a5cb63279131fb1736fbdf32e2bcb7591a698f676520f03209437fa277e"
OUTSIDE_FAILED_BODY_SHA256 = "fb745e96dc3686b515d7a814de3f5d870c53d39af9e3c247c514e8eeb5b05fce"


class AndroidWebViewStopRedirectRecoveryControls(unittest.TestCase):
    def source(self):
        return (r.ROOT / r.ANDROID_WEBVIEW_REQUEST_SOURCE).read_text(encoding="utf-8")

    def temporary_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        module = root / "calf-webview"
        module.mkdir()
        (module / "build.gradle.kts").write_text("// Synthetic source discovery only; never compiled or executed\n")
        for relative in [r.ANDROID_WEBVIEW_REQUEST_SOURCE, *r.android_webview_request_fixtures()]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((r.ROOT / relative).read_bytes())
        return root

    def plan(self, root):
        return r.plan(root, "android-device", only_modules=("calf-webview",), focus=FOCUS)

    def command(self, root, plan=None):
        return r.gradle_command("android-device", self.plan(root) if plan is None else plan,
                                root=root, android_serial="emulator-5588")

    def collect(self, *, cases=None, outcome=None, reports=1, extra_empty=False,
                stale=False, future=False, marker=1, host="Linux"):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            plan = self.plan(root)
            item, = plan["expected"]
            folder = root / item["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in r.android_webview_stop_redirect_recovery_identities() if cases is None else cases:
                element = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(element, outcome)
            paths = []
            for index in range(reports):
                path = folder / ("TEST-synthetic-stop-only-" + str(index) + ".xml")
                path.write_bytes(ET.tostring(xml))
                paths.append(path)
            if extra_empty:
                path = folder / "TEST-unrelated-empty.xml"
                path.write_bytes(ET.tostring(ET.Element("testsuite")))
                paths.append(path)
            now = time.time_ns()
            if stale or future:
                modified = now + (10_000_000_000 if future else -10_000_000_000)
                for path in paths:
                    os.utime(path, ns=(modified, modified))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({item["task"]: marker}), host_system=host)

    def test_four_seed_expectations_and_exact_original_inverse_preserve_all_helpers_and_accepted_body(self):
        source = self.source()
        stop = source_guard.body_after(source, "@Test fun " + STOP)
        accepted = source_guard.body_after(source, "@Test fun " + ACCEPTED)
        self.assertEqual(["server.seed.url"] * 4, re.findall(
            r"assertEquals\(WebContent\.Url\(([^)\n]+)\), state\.content\)", stop))
        self.assertEqual(ACCEPTED_BODY_SHA256, hashlib.sha256(accepted.encode()).hexdigest())
        self.assertEqual(1, source.count(stop))
        outside = source.replace(stop, "<ONLY-FAILED-STOP-BODY-EXCLUDED>", 1)
        self.assertEqual(OUTSIDE_FAILED_BODY_SHA256, hashlib.sha256(outside.encode()).hexdigest())
        original = selector_guard.request_source_before_stop_content(source)
        self.assertEqual(selector_guard.HELD_REQUEST_SEQUENCE_SELECTED_SOURCE_SHA256,
                         hashlib.sha256(original.encode()).hexdigest())
        self.assertEqual(accepted, source_guard.body_after(original, "@Test fun " + ACCEPTED))
        self.assertEqual(source_guard.COMPILED_ANDROID_REQUEST_SOURCE_SHA256,
                         hashlib.sha256(source_guard.compiled_request_source(source).encode()).hexdigest())
        self.assertEqual(source_guard.compiled_request_source(original), source_guard.compiled_request_source(source))

    def test_each_content_assertion_refuses_old_url_or_manual_declarative_rewrite(self):
        source = self.source()
        for name, before, after in selector_guard.STOP_DECLARATIVE_CONTENT_FRAGMENT_IMAGES:
            self.assertEqual(1, source.count(after))
            changed = source.replace(after, before, 1)
            with self.subTest(assertion=name), self.assertRaises(ValueError):
                source_guard.require_stop_redirect_witnesses(changed)
        current = "assertEquals(WebContent.Url(server.seed.url), state.content)"
        stop = source_guard.body_after(source, "@Test fun " + STOP)
        rewritten = stop.replace(current, "state.content = WebContent.Url(server.stopped.url)", 1)
        with self.assertRaises(ValueError):
            source_guard.require_stop_redirect_witnesses(source.replace(stop, rewritten, 1))

    def test_inverse_barrier_refuses_old_partial_duplicate_unknown_native_changes(self):
        source = self.source()
        original = selector_guard.request_source_before_stop_content(source)
        _, before, after = selector_guard.STOP_DECLARATIVE_CONTENT_FRAGMENT_IMAGES[0]
        variants = (original, source.replace(after, before, 1), source.replace(after, after + after, 1),
                    source + "\nprivate fun unknownNativeAction() { native.destroy() }\n",
                    source.replace("fixture.navigator.stopLoading()", "native.stopLoading()", 1))
        for index, changed in enumerate(variants):
            with self.subTest(variant=index), self.assertRaises(ValueError):
                selector_guard.request_source_before_stop_content(changed)

    def test_public_source_keeps_requested_navigation_independent_of_declarative_content(self):
        shared = (r.ROOT / "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt").read_text()
        android = (r.ROOT / "calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt").read_text()
        contracts = (r.ROOT / "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt").read_text()
        load_url = source_guard.body_after(shared, "public fun loadUrl(")
        self.assertIn("enqueue(NavigationEvent.LoadUrl(url, additionalHttpHeaders.toMap()))", load_url)
        load = source_guard.body_after(android, "internal fun loadAndroidContent(")
        self.assertIn("state.acceptContent(content, WebContentPlatform.Android)", load)
        self.assertIn("view.loadUrl(content.url, content.additionalHttpHeaders)", load)
        navigation = source_guard.body_after(android, "internal suspend fun WebViewNavigator.handleNavigationEvents(")
        self.assertIn("val content = event.contentOrNull()", navigation)
        self.assertIn("loadAndroidContent(webView, state, content)", navigation)
        self.assertIn("WebViewNavigator.NavigationEvent.Reload -> webView.reload()", navigation)
        self.assertIn("WebViewNavigator.NavigationEvent.StopLoading -> webView.stopLoading()", navigation)
        begin = source_guard.body_after(contracts, "internal fun WebViewState.beginRequest(")
        accept = source_guard.body_after(contracts, "internal fun WebViewState.acceptContent(")
        self.assertIn("requestedUrl = url", begin)
        self.assertIn("beginRequest((content as? WebContent.Url)?.url)", accept)
        for block in (load_url, load, navigation):
            self.assertFalse(re.search(r"\bstate\.content\s*=", block))
        for block in (begin, accept):
            self.assertFalse(re.search(r"(?m)^\s*(?:this\.)?content\s*=", block))
        self.assertIn("that content may still contain a previous URL", contracts)

    def test_stop1_plan_retains_both_declarations_but_requires_only_unaccepted_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            plan = self.plan(root)
            item, = plan["expected"]
            self.assertEqual(FOCUS, plan["explicit_test_focus"])
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
            self.assertEqual([{"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": STOP}], item["required_testcases"])
            self.assertEqual("class", item["test_filter_argument"])
            self.assertEqual(35, item["verification_api_level"])
            self.assertEqual(r.android_webview_request_fixtures(), item["native_fixture_paths"])
            self.assertEqual([ACCEPTED, STOP], re.findall(r"@Test\s+fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)", self.source()))
            self.assertNotIn(ACCEPTED, [case["name"] for case in item["required_testcases"]])
            self.assertFalse(r.android_io_documents_required(plan))
            self.assertFalse(r.android_permission_demo_required(plan))
            self.assertFalse(r.android_storage_probe_required(plan))

    def test_single_class_method_selector_is_lossless_not_annotation_or_unowned_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            command = self.command(root)
            prefix = "-Pandroid.testInstrumentationRunnerArguments."
            selectors = dict(argument[len(prefix):].split("=", 1) for argument in command if argument.startswith(prefix))
            exact = r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + STOP
            self.assertEqual({"class": exact, "timeout_msec": "120000"}, selectors)
            _, decoded = selector_guard.agp_ate_map_round_trip(selectors)
            self.assertEqual(selectors, decoded)
            self.assertNotIn(",", selectors["class"])
            self.assertNotIn(ACCEPTED, selectors["class"])
            self.assertNotIn("--tests", command)
            self.assertEqual(":calf-webview:connectedAndroidDeviceTest", command[-1])
            self.assertNotIn("nativecmpkitWebViewHeapDiagnostic", " ".join(command))

    def test_wrong_suite_module_and_api_refuse_before_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            for suite in ("android-host", "desktop", "ios", "js", "wasm"):
                with self.subTest(suite=suite), self.assertRaises(ValueError):
                    r.plan(root, suite, only_modules=("calf-webview",), focus=FOCUS)
            for modules in (None, (), ("calf-io",), ("calf-webview", "calf-io"), ("calf-webview", "calf-webview")):
                with self.subTest(modules=modules), self.assertRaises(ValueError):
                    r.plan(root, "android-device", only_modules=modules, focus=FOCUS)
                with self.subTest(api_modules=modules), self.assertRaises(ValueError):
                    controller.validate_api_selection(35, modules, FOCUS)
            controller.validate_api_selection(35, ("calf-webview",), FOCUS)
            for api in (True, 35.0, "35", 23, 28, 29, 30, 33, 34, 36):
                with self.subTest(api=api), self.assertRaises(ValueError):
                    controller.validate_api_selection(api, ("calf-webview",), FOCUS)
            self.assertFalse((root / "build").exists())

    def test_original_annotations_missing_extra_skip_or_wrong_runtime_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            path = root / r.ANDROID_WEBVIEW_REQUEST_SOURCE
            original = path.read_text()
            variants = (original.replace("@Test fun " + ACCEPTED, "fun " + ACCEPTED, 1),
                        original.replace("@Test fun " + STOP, "fun " + STOP, 1),
                        original.replace("    @AndroidWebViewRequestVerification\n", "", 1),
                        original.replace("AnnotationRetention.RUNTIME", "AnnotationRetention.SOURCE", 1),
                        original.replace("@Test fun " + ACCEPTED, "@Ignore @Test fun " + ACCEPTED, 1),
                        original + "\n@Test fun extraAcceptedReplay() {}\n")
            for index, source in enumerate(variants):
                path.write_text(source)
                with self.subTest(variant=index), self.assertRaises(ValueError):
                    self.plan(root)
            path.write_text(original)
            foreign = root / "calf-webview/src/commonTest/kotlin/ForeignAnnotation.kt"
            foreign.parent.mkdir(parents=True)
            foreign.write_text("@AndroidWebViewRequestVerification @Test fun foreign() {}\n")
            with self.assertRaises(ValueError):
                self.plan(root)

    def test_plan_tampering_refuses_selector_scope_reports_helpers_and_api_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            valid = self.plan(root)
            item, = valid["expected"]
            mutations = (("test_filter", r.ANDROID_WEBVIEW_REQUEST_ANNOTATION),
                         ("test_filter", r.ANDROID_WEBVIEW_REQUEST_CLASS),
                         ("test_filter", item["test_filter"] + "," + r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + ACCEPTED),
                         ("test_filter", item["test_filter"] + "%2CForeign"),
                         ("test_filter_argument", None), ("test_filter_argument", "annotation"),
                         ("test_filter_argument", "notAnnotation"), ("test_exclusion_annotation", "Foreign"),
                         ("required_testcases", []), ("required_testcases", r.android_webview_request_identities()),
                         ("required_testcases", [{"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": ACCEPTED}]),
                         ("module", "calf-io"), ("project", ":calf-io"), ("task", ":calf-webview:publish"),
                         ("report_directory", "foreign/build/test-results/desktopTest"),
                         ("utp_results_directory", "foreign/build/outputs"),
                         ("agp_declared_xml_directory", "foreign/build/intermediates"),
                         ("test_source_files", [r.ANDROID_WEBVIEW_REQUEST_SOURCE]),
                         ("native_fixture_paths", []), ("verification_api_level", True),
                         ("verification_api_level", 35.0), ("verification_api_level", 34))
            for key, value in mutations:
                changed = copy.deepcopy(valid)
                changed["expected"][0][key] = value
                with self.subTest(field=key, variant=repr(value)), self.assertRaises(ValueError):
                    self.command(root, changed)
            changed = copy.deepcopy(valid)
            del changed["expected"][0]["test_filter_argument"]
            with self.assertRaises(ValueError):
                self.command(root, changed)
            for mutate in (lambda plan: plan.update(complete_suite_requested=True),
                           lambda plan: plan["expected"].extend(copy.deepcopy(plan["expected"]))):
                changed = copy.deepcopy(valid)
                mutate(changed)
                with self.assertRaises(ValueError):
                    self.command(root, changed)

    def test_plan_cli_is_source_only_and_requires_exact_single_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            entries = ((r.main, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-webview", "--focus", FOCUS]),
                       (controller.main, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-webview", "--focus", FOCUS,
                                          "--output", "build/ci-verification/synthetic-never-created"]))
            for entry, argv in entries:
                stream = io.StringIO()
                with patch.object(r, "ROOT", root), patch("sys.argv", argv), patch("sys.stdout", stream), \
                     patch("subprocess.run", side_effect=AssertionError("No external command in source-only CLI")), \
                     patch.object(controller, "require_host", side_effect=AssertionError("No host/native admission in source-only CLI")):
                    self.assertEqual(0, entry())
                plan = json.loads(stream.getvalue())
                self.assertEqual(FOCUS, plan["explicit_test_focus"])
                self.assertEqual([STOP], [case["name"] for case in plan["expected"][0]["required_testcases"]])
                self.assertFalse((root / "build").exists())

    def test_one_synthetic_stop_case_in_one_fresh_xml_is_only_a_tooling_model(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["executed"])
        self.assertEqual(1, result["totals"]["passed"])
        scenario, = result["modules"][0]["native_scenarios"]
        self.assertEqual(STOP, scenario["name"])
        self.assertEqual(35, scenario["verification_api_level"])
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_SOURCE, scenario["source"])

    def test_xml_missing_accepted_extra_foreign_duplicate_or_parameterized_cases_refuse(self):
        exact = r.android_webview_stop_redirect_recovery_identities()
        accepted = [{"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": ACCEPTED}]
        variants = ([], accepted, r.android_webview_request_identities(), exact * 2,
                    exact + [{"classname": "Foreign", "name": "unrelated"}],
                    [{"classname": "Foreign", "name": STOP}],
                    [{"classname": r.ANDROID_WEBVIEW_REQUEST_CLASS, "name": STOP + "[android]"}])
        for index, cases in enumerate(variants):
            with self.subTest(variant=index):
                self.assertTrue(self.collect(cases=cases)["errors"])

    def test_extra_duplicate_empty_stale_future_xml_refuse(self):
        for values in ({"reports": 0}, {"reports": 2}, {"extra_empty": True}, {"stale": True}, {"future": True}):
            with self.subTest(variant=values):
                self.assertTrue(self.collect(**values)["errors"])

    def test_failed_error_skipped_wrong_host_and_marker_xml_refuse(self):
        for values in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                       {"host": "Darwin"}, {"host": "Windows"}, {"marker": 0}, {"marker": 2}):
            with self.subTest(variant=values):
                self.assertTrue(self.collect(**values)["errors"])

    def test_original_two_method_route_and_complete11_slots_stay_authored_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            original = r.plan(root, "android-device", only_modules=("calf-webview",), focus=r.ANDROID_WEBVIEW_REQUEST_FOCUS)
            item, = original["expected"]
            self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_ANNOTATION, item["test_filter"])
            self.assertEqual("annotation", item["test_filter_argument"])
            self.assertEqual([ACCEPTED, STOP], [case["name"] for case in item["required_testcases"]])
            self.assertEqual(FOCUS, r.ANDROID_WEBVIEW_STOP_REDIRECT_RECOVERY_FOCUS)
            self.assertNotEqual(FOCUS, r.ANDROID_WEBVIEW_REQUEST_FOCUS)
            self.assertEqual([ACCEPTED, STOP], list(r.ANDROID_WEBVIEW_REQUEST_METHODS))
            self.assertEqual(1, self.source().count(source_guard.ANDROID_REQUEST_SELECTOR_DECLARATION))
            self.assertEqual(3, self.source().count(source_guard.ANDROID_REQUEST_SELECTOR_NAME))
        all_rows = matrix.matrix("all")["include"]
        self.assertEqual(11, len(all_rows))
        self.assertEqual([slot["slot"] for slot in matrix.SLOTS], [row["slot"] for row in all_rows])
        self.assertTrue(all("test-focus" not in row for row in all_rows))
        original_row, = matrix.matrix(r.ANDROID_WEBVIEW_REQUEST_FOCUS)["include"]
        self.assertEqual("android-device-api35", original_row["slot"])
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_FOCUS, original_row["test-focus"])

    def test_workflow_choice_is_fixed_read_only_without_hidden_serial_or_batch_route(self):
        row, = matrix.matrix(FOCUS)["include"]
        self.assertEqual(("android-device-api35", "android-device", "35", "calf-webview", FOCUS),
                         (row["slot"], row["suite"], row["emulator-api"], row["test-modules"], row["test-focus"]))
        self.assertFalse(any(key.startswith("serial-") or "batch" in key for key in row))
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        options = profile_options(workflow)
        self.assertEqual(1, options.count(FOCUS))
        self.assertEqual(set(matrix.PROFILES), set(options))
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn(FOCUS, workflow[workflow.index("permissions:"):])
        init = (r.ROOT / "scripts/ci/fresh-tests.init.gradle.kts").read_text()
        self.assertIn("requestedSelectors.values.none { ',' in it }", init)
        self.assertIn("runnerArguments.filterKeys { it in selectorKeys } == requestedSelectors", init)

    def test_retained_native_witnesses_refuse_eof302_reload_or_cleanup_shortcuts(self):
        source = self.source()
        source_guard.require_stop_redirect_witnesses(source)
        replacements = (("fixture.navigator.stopLoading()", "native.stopLoading()"),
                        ("check(eof == -1)", "check(true)"),
                        ('if (redirecting) "302 Found" else "200 OK"', 'if (redirecting) "200 OK" else "200 OK"'),
                        ("assertEquals(redirectRequests, server.redirect.requests.get()", "assertEquals(redirectRequests, redirectRequests"),
                        ("socket.soTimeout = 15_000", "socket.soTimeout = 30_000"),
                        ("assertNull(state.webView)", "Unit"))
        for before, after in replacements:
            if before == "assertNull(state.webView)":
                stop = source_guard.body_after(source, "@Test fun " + STOP)
                self.assertEqual(1, stop.count(before))
                changed = source.replace(stop, stop.replace(before, after, 1), 1)
            else:
                self.assertEqual(1, source.count(before))
                changed = source.replace(before, after, 1)
            with self.subTest(witness=before), self.assertRaises(ValueError):
                source_guard.require_stop_redirect_witnesses(changed)


if __name__ == "__main__":
    unittest.main()
