# SPDX-License-Identifier: Apache-2.0
"""New focused source/planner/XML models only. Never native WebView/transport acceptance."""
from collections import Counter
import copy
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
import workflow_matrix as matrix


def body_after(source, anchor):
    """Bound one source block without interpreting braces inside quoted Kotlin strings."""
    start = source.index("{", source.index(anchor))
    depth, quoted, escaped, comment = 0, None, False, False
    index = start
    while index < len(source):
        char = source[index]
        if comment:
            if char == "\n": comment = False
        elif quoted:
            if escaped: escaped = False
            elif char == "\\": escaped = True
            elif char == quoted: quoted = None
        elif source[index:index + 2] == "//":
            comment = True; index += 1
        elif char in "\"'": quoted = char
        elif char == "{": depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0: return source[start + 1:index]
        index += 1
    raise ValueError("Unclosed private source block")


def require_native_witnesses(source):
    for name, invocation in (("onPageStarted", "super.onPageStarted(view, url, favicon)"),
                             ("onReceivedError", "super.onReceivedError(view, request, error)"),
                             ("onPageFinished", "super.onPageFinished(view, url)")):
        body = body_after(source, "override fun " + name)
        if body.index(invocation) > body.index("observe(view)"):
            raise ValueError("Observation cannot bypass or precede production forwarding")
    numeric_bounds = ((r"bytes\.size\(\)\s*<\s*([0-9_]+)\s*\)", 8192),
                      (r"admitted\.incrementAndGet\(\)\s*<=\s*([0-9_]+)\s*\)", 64),
                      (r"candidate\.attempts\.incrementAndGet\(\)\s*<=\s*([0-9_]+)\s*\)", 16))
    for expression, expected in numeric_bounds:
        literals = re.findall(expression, source)
        if len(literals) != 1 or int(literals[0].replace("_", "")) != expected:
            raise ValueError("Exact finite integer bound changed; numeric-prefix text is not proof")
    error = body_after(source, "override fun onReceivedError")
    if re.search(r"isForMainFrame[^\n]*\breturn\b", error):
        raise ValueError("Resource errors must not be silently filtered from native forwarding/observation")
    refusal = body_after(source, "if (owned.title == null)")
    if ("writeResponse(" in refusal or ".write(" in refusal or
            refusal.index("socket.close()") > refusal.index("owned.refused.incrementAndGet()")):
        raise ValueError("Zero-response refusal must close its owned socket before counting")
    close = body_after(source, "override fun close()")
    if close.index("acceptor.join(5_000)") > close.index("sockets.toList()"):
        raise ValueError("Acceptor join precedes final owned socket snapshot")
    required = ("assertEquals(35, Build.VERSION.SDK_INT", "ActivityLease(fixture).use", "AndroidLifetimeFixture(state, probe)",
                "assertSame(probe, it.webViewClient)", "assertIs<AccompanistWebChromeClient>(it.webChromeClient)",
                "native.loadUrl(stage.url)", "native.loadUrl(server.recovery.url)", "fixture.navigator.reload()",
                "assertEquals(server.recovery.url, native.url)", "assertEquals(WebContent.Url(server.seed.url), state.content)",
                "owner.webView !== view", "observed.errors += AndroidRequestError", "observed.generation",
                "assertEquals(nativeErrors, snapshot().errors)", "assertEquals(LoadingState.Loading(0f), it.loading)",
                "if (closing.get()) return", "acquiredStage = owned", "acquiredStage?.let { owned ->",
                "owned.pending.decrementAndGet()", "owned.gate.await(15, TimeUnit.SECONDS)",
                "checkNotNull(routes[path])", 'headers["host"] == "127.0.0.1:${listener.localPort}"',
                "remaining > 0 && bytes.size() < 8_192", "SystemClock.elapsedRealtime() + 5_000",
                "candidate.attempts.incrementAndGet() <= 16", "admitted.incrementAndGet() <= 64",
                "ThreadPoolExecutor(4, 4", "ArrayBlockingQueue<Runnable>(8)", "Cache-Control: no-store",
                "stages.forEach { it.gate.countDown() }", "workers.shutdown()", "workers.shutdownNow()",
                "runWebViewCleanup(stages = arrayOf(", "stage.responseBytes.get()", "stage.testReleased.get()",
                "JavascriptResult.Value(\"true\")", "data-nativecmpkit", "data-stage", "host.unmount()", "host.assertResumed()")
    if any(item not in source for item in required):
        raise ValueError("Missing exact native owner/start/error/loading/Reload/DOM/lease/bounds/cleanup witness")
    for forbidden in (r"\bshouldInterceptRequest\s*\(", r"\bWebResourceResponse\b", r"\bWebViewError\s*\(",
                      r"\.errorsForCurrentRequest\s*=", r"\.beginRequest\s*\(", r"\bacceptContent\s*\(",
                      r"\b(?:assumeTrue|assumeFalse|stopLoading|setWebViewClient|onReceivedHttpError)\s*\(",
                      r"@(Ignore|Disabled|IgnoredTest)\b", r"import[^\n]*(?:Robolectric|mockk|Mockito)"):
        if re.search(forbidden, source):
            raise ValueError("No mock/intercepted/synthetic reset/skip/HTTP-error or manual client replacement")


class AndroidWebViewRequestStateGuards(unittest.TestCase):
    def temporary_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        module = root / "calf-webview"; module.mkdir()
        (module / "build.gradle.kts").write_text("// Synthetic discovery only; never executed\n")
        for relative in [r.ANDROID_WEBVIEW_REQUEST_SOURCE, *r.android_webview_request_fixtures()]:
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((r.ROOT / relative).read_bytes())
        return root

    def plan(self, root, suite="android-device", modules=("calf-webview",)):
        return r.plan(root, suite, only_modules=modules, focus=r.ANDROID_WEBVIEW_REQUEST_FOCUS)

    def collect(self, cases=None, outcome=None, markers=1, duplicate=False, stale=False, host="Linux", extra_empty=False):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory); plan = self.plan(root)
            folder = root / plan["expected"][0]["report_directory"]; folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in r.android_webview_request_identities() if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome: ET.SubElement(node, outcome)
            path = folder / "TEST-synthetic-only.xml"; path.write_bytes(ET.tostring(xml))
            if duplicate: (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            if extra_empty: (folder / "TEST-unrelated-empty.xml").write_bytes(ET.tostring(ET.Element("testsuite")))
            now = time.time_ns()
            if stale: os.utime(path, ns=(now - 10_000_000_000, now - 10_000_000_000))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: markers}), host_system=host)

    def test_one_api35_profile_preserves_full_slots_and_has_no_batch_or_serial_expansion(self):
        row, = matrix.matrix("android-webview-request-state")["include"]
        self.assertEqual("android-device-api35", row["slot"])
        self.assertEqual("android-device", row["suite"])
        self.assertEqual("35", row["emulator-api"])
        self.assertEqual("calf-webview", row["test-modules"])
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_FOCUS, row["test-focus"])
        self.assertFalse(row.get("serial-test-focus"))
        self.assertEqual(11, len(matrix.SLOTS))
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        choices = re.search(r"(?m)^        options: (\[[^\n]+\])$", workflow).group(1)
        self.assertEqual(1, choices.count("android-webview-request-state"))
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("android-webview-request-state", workflow[workflow.index("permissions:"):])

    def test_source_plan_and_command_select_only_the_one_new_method_with_exact_helper_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory); plan = self.plan(root)
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(1, len(plan["expected"]))
            item = plan["expected"][0]
            self.assertEqual(r.android_webview_request_identities(), item["required_testcases"])
            self.assertEqual(r.android_webview_request_fixtures(), item["native_fixture_paths"])
            self.assertEqual(35, item["verification_api_level"])
            command = r.gradle_command("android-device", plan, android_serial="emulator-5588")
            selected = [arg for arg in command if arg.startswith("-Pandroid.testInstrumentationRunnerArguments.class=")]
            self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.class=" + r.ANDROID_WEBVIEW_REQUEST_CLASS + "#" + r.ANDROID_WEBVIEW_REQUEST_METHOD], selected)
            self.assertNotIn("--tests", command)
            self.assertEqual(":calf-webview:connectedAndroidDeviceTest", command[-1])
            self.assertFalse(r.android_io_documents_required(plan))
            self.assertNotIn("nativecmpkitWebViewHeapDiagnostic", " ".join(command))

    def test_wrong_suite_module_scope_or_api_never_reaches_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            for suite in ("desktop", "android-host", "ios", "js", "wasm"):
                with self.subTest(suite=suite), self.assertRaises(ValueError): self.plan(root, suite)
            for modules in (None, (), ("calf-io",), ("calf-webview", "calf-io"), ("calf-webview", "calf-webview")):
                with self.subTest(modules=modules), self.assertRaises(ValueError): self.plan(root, modules=modules)
        controller.validate_api_selection(35, ("calf-webview",), r.ANDROID_WEBVIEW_REQUEST_FOCUS)
        for api in (True, 35.0, "35", 23, 28, 29, 30, 33, 34):
            with self.subTest(api=api), self.assertRaises(ValueError):
                controller.validate_api_selection(api, ("calf-webview",), r.ANDROID_WEBVIEW_REQUEST_FOCUS)

    def test_real_plan_cli_transports_the_exact_focus_without_sdk_or_external_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory)
            for entry, arguments in ((r.main, ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-webview", "--focus", r.ANDROID_WEBVIEW_REQUEST_FOCUS]),
                                     (controller.main, ["android_device_tests.py", "plan", "--api-level", "35", "--module", "calf-webview", "--focus", r.ANDROID_WEBVIEW_REQUEST_FOCUS, "--output", "build/ci-verification/synthetic-unused"])):
                stream = io.StringIO()
                with patch.object(r, "ROOT", root), patch("sys.argv", arguments), patch("sys.stdout", stream):
                    self.assertEqual(0, entry())
                plan = json.loads(stream.getvalue())
                self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_FOCUS, plan["explicit_test_focus"])
                self.assertEqual(1, len(plan["expected"][0]["required_testcases"]))

    def test_plan_tampering_cannot_switch_task_inventory_reports_helper_api_or_whole_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory); valid = self.plan(root)
            for key, value in (("task", ":calf-webview:publish"), ("module", "calf-io"), ("test_filter", "*"),
                               ("required_testcases", []), ("test_source_files", [r.ANDROID_WEBVIEW_REQUEST_SOURCE]),
                               ("native_fixture_paths", []), ("verification_api_level", 35.0),
                               ("report_directory", "foreign/build/test-results/desktopTest")):
                candidate = copy.deepcopy(valid); candidate["expected"][0][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError): r.validate_test_focus(candidate)
            candidate = copy.deepcopy(valid); candidate["complete_suite_requested"] = True
            with self.assertRaises(ValueError): r.validate_test_focus(candidate)
            candidate = copy.deepcopy(valid); candidate["expected"] *= 2
            with self.assertRaises(ValueError): r.validate_test_focus(candidate)

    def test_source_declaration_and_existing_loopback_policy_mutations_refuse_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory); self.plan(root)
            path = root / r.ANDROID_WEBVIEW_REQUEST_SOURCE; original = path.read_text()
            for changed in (original.replace(r.ANDROID_WEBVIEW_REQUEST_METHOD, "wrongMethod", 1), original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun extra() {}\n"):
                path.write_text(changed)
                with self.assertRaises(ValueError): self.plan(root)
            path.write_text(original)
            for relative, pairs in ((r.WEBVIEW_DEVICE_FIXTURES[1], [("127.0.0.1", "localhost"), ('includeSubdomains="false"', 'includeSubdomains="true"')]),
                                    (r.WEBVIEW_DEVICE_FIXTURES[0], [('android:exported="false"', 'android:exported="true"'), ('android:usesCleartextTraffic="false"', 'android:usesCleartextTraffic="true"')])):
                target = root / relative; initial = target.read_text()
                for before, after in pairs:
                    target.write_text(initial.replace(before, after))
                    with self.assertRaises(ValueError): self.plan(root)
                target.write_text(initial)
            (root / r.ANDROID_WEBVIEW_REQUEST_HELPER).unlink()
            with self.assertRaises(ValueError): self.plan(root)

    def test_one_fresh_synthetic_case_is_accepted_only_as_a_tooling_model(self):
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])
        scenario, = result["modules"][0]["native_scenarios"]
        self.assertEqual(35, scenario["verification_api_level"])
        self.assertEqual(r.ANDROID_WEBVIEW_REQUEST_SOURCE, scenario["source"])

    def test_one_original_xml_cannot_be_substituted_by_an_extra_empty_fresh_report(self):
        self.assertTrue(self.collect(extra_empty=True)["errors"])

    def test_missing_foreign_extra_duplicate_stale_failed_skipped_wrong_host_or_marker_xml_refuses(self):
        exact = r.android_webview_request_identities()
        variants = [{"cases": []}, {"cases": exact * 2}, {"cases": exact + [{"classname": "Foreign", "name": "other"}]},
                    {"cases": [{**exact[0], "classname": "Foreign"}]}, {"cases": [{**exact[0], "name": exact[0]["name"] + "[desktop]"}]},
                    {"duplicate": True}, {"stale": True}, {"markers": 0}, {"markers": 2}, {"host": "Windows"}, {"host": "Darwin"},
                    {"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"}]
        for invalid in variants:
            with self.subTest(invalid=invalid): self.assertTrue(self.collect(**invalid)["errors"])

    def test_normal_native_source_has_exact_forwarded_owned_start_error_loading_reload_dom_and_cleanup_witnesses(self):
        require_native_witnesses((r.ROOT / r.ANDROID_WEBVIEW_REQUEST_SOURCE).read_text())

    def test_partial_server_creation_uses_the_acquired_nonnull_pool_and_preserves_owned_cleanup(self):
        source = (r.ROOT / r.ANDROID_WEBVIEW_REQUEST_SOURCE).read_text()
        body = body_after(source, "fun create(): AndroidRequestHttpServer")
        for required in ("val acquiredWorkers = ThreadPoolExecutor(4, 4", "workers = acquiredWorkers",
                         "AndroidRequestHttpServer(listener, acquiredWorkers)", "acquired = it; it.acceptor.start()",
                         "runWebViewCleanup(error, { owned.close() })", "listener.close()", "workers?.shutdownNow()",
                         "workers?.let { check(it.awaitTermination(5, TimeUnit.SECONDS)) }"):
            self.assertIn(required, body)
        self.assertNotIn("AndroidRequestHttpServer(listener, workers)", body)
        self.assertLess(body.index("workers = acquiredWorkers"), body.index("it.acceptor.start()"))

    def test_source_models_reject_reset_masking_filtering_early_cleanup_or_unbounded_fixture_shortcuts(self):
        source = (r.ROOT / r.ANDROID_WEBVIEW_REQUEST_SOURCE).read_text()
        replacements = [("super.onPageStarted(view, url, favicon)", "Unit"),
                        ("super.onReceivedError(view, request, error)", "super.onReceivedError(view, request, error)\n        if (request?.isForMainFrame != true) return"),
                        ("native.loadUrl(stage.url)", "fixture.navigator.loadUrl(stage.url)"),
                        ("fixture.navigator.reload()", "native.loadUrl(server.seed.url)"),
                        ("if (closing.get()) return", "Unit"),
                        ("owned.pending.decrementAndGet()", "recovery.pending.decrementAndGet()"),
                        ("bytes.size() < 8_192", "bytes.size() < 8_192_000"),
                        ("admitted.incrementAndGet() <= 64", "true"),
                        ("ArrayBlockingQueue<Runnable>(8)", "ArrayBlockingQueue<Runnable>(8000)"),
                        ("checkNotNull(routes[path])", "(routes[path] ?: recovery)")]
        for before, after in replacements:
            with self.subTest(before=before), self.assertRaises((ValueError, IndexError)):
                require_native_witnesses(source.replace(before, after, 1))
        with self.assertRaises(ValueError): require_native_witnesses(source + "\nfun masked() { state.errorsForCurrentRequest = emptyList() }\n")
        with self.assertRaises(ValueError): require_native_witnesses(source.replace("socket.close() // No status/header/body", "writeResponse(socket, byteArrayOf(), \"text/plain\", owned)\n                socket.close() // No status/header/body", 1))
        with self.assertRaises(ValueError): require_native_witnesses(source.replace("acceptor.join(5_000)", "Unit", 1))


if __name__ == "__main__":
    unittest.main()
