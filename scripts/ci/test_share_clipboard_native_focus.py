"""New #82 routing/source guards. Synthetic XML is never native/browser evidence."""
from collections import Counter
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as lt
import workflow_matrix as matrix

PROFILE = "share-clipboard-native"
FOCUS = "web-share-clipboard-native-contexts"
CLASS = "com.mohamedrejeb.calf.share.WebClipboardEnvironmentAcceptanceTest"
SOURCE = "calf-share/src/webTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardEnvironmentAcceptanceTest.kt"
JS_HELPER = "calf-share/src/jsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.js.kt"
WASM_HELPER = "calf-share/src/wasmJsTest/kotlin/com/mohamedrejeb/calf/share/WebClipboardNativeHarness.wasmJs.kt"
FIXTURE = "calf-share/karma.config.d/nativecmpkit-clipboard-fixture.js"
METHODS = (
    "secureContextWithAbsentClipboardApiReportsUnavailableWithoutPlatformCalls",
    "genuinelyInsecureHttpContextHasNoClipboardApiAndReportsUnavailable",
    "actualDeniedClipboardPermissionRejectsOneTrustedGestureWriteWithoutSuccess",
    "directTrustedGesturePreservesActivationAndCompletesOneActualOwnedTextWrite",
)


class ShareClipboardNativeFocusTests(unittest.TestCase):
    def source_root(self, directory):
        root = Path(directory)
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-share",\n)\n')
        build = root / "calf-share/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicitly synthetic discovery root; never built\n")
        for relative in (SOURCE, JS_HELPER, WASM_HELPER, FIXTURE):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def plan(self, root, suite="js"):
        return lt.plan(root, suite, only_modules=("calf-share",), focus=FOCUS)

    def cases(self, suite="js"):
        target = "js" if suite == "js" else "wasmJs"
        return [{"classname": lt.SUITES[suite][0] + "." + CLASS,
                 "name": method + "[" + target + ", browser, OwnedClipboardHeadless synthetic-tooling]"}
                for method in METHODS]

    def collect(self, plan, cases=None, outcome="", stale=False, duplicate=False, markers=1):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selected, = plan["expected"]
            folder = root / selected["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in self.cases(plan["suite"]) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            path = folder / "TEST-explicitly-synthetic.xml"
            path.write_bytes(ET.tostring(xml))
            if duplicate:
                (folder / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale:
                os.utime(path, ns=(now - 20_000_000_000,) * 2)
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({selected["task"]: markers}), host_system="Linux")

    def test_finite_profile_and_commands_select_only_four_new_cases(self):
        rows = matrix.matrix(PROFILE)["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        self.assertTrue(all(row["test-modules"] == "calf-share" and row["test-focus"] == FOCUS for row in rows))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        accepted = matrix.matrix("share-browser")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in accepted])
        self.assertTrue(all(row["test-modules"] == "calf-share" and "test-focus" not in row for row in accepted))
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("js", "wasm"):
                plan = self.plan(root, suite)
                selected, = plan["expected"]
                sources = lt.share_clipboard_native_sources(suite)
                self.assertTrue(lt.validate_test_focus(plan))
                self.assertFalse(plan["complete_suite_requested"])
                self.assertEqual(CLASS, selected["test_filter"])
                self.assertEqual([{"classname": CLASS, "name": method} for method in METHODS], selected["required_testcases"])
                self.assertEqual(1, selected["required_original_xml"])
                self.assertEqual(list(sources), selected["test_source_files"])
                self.assertEqual({p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in sources},
                                 selected["test_source_sha256"])
                self.assertEqual(list(lt.SUITES[suite][1]), plan["inherited_test_source_sets"])
                command = lt.gradle_command(suite, plan)
                self.assertEqual(1, command.count("--tests"))
                self.assertEqual(CLASS, command[command.index("--tests") + 1])
                self.assertFalse(any("WebSharePromiseTest" in argument or "ShareContractsTest" in argument for argument in command))

    def test_wrong_scope_or_changed_selected_source_bytes_refuses_before_any_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("ios", "desktop", "android-host", "android-device"):
                with self.subTest(suite=suite), self.assertRaises(ValueError):
                    self.plan(root, suite)
            for suite in ("js", "wasm"):
                for modules in (None, ("calf-ui",), ("calf-share", "calf-ui")):
                    with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                        lt.plan(root, suite, only_modules=modules, focus=FOCUS)
                for relative in lt.share_clipboard_native_sources(suite):
                    path = root / relative
                    original = path.read_bytes()
                    try:
                        path.write_bytes(original + b"\n// unreviewed synthetic change\n")
                        with self.subTest(suite=suite, source=relative), self.assertRaises(ValueError):
                            self.plan(root, suite)
                    finally:
                        path.write_bytes(original)

    def test_changed_plan_fields_cannot_widen_or_relabel_finite_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("js", "wasm"):
                for key, value in (
                    ("module", "calf-ui"), ("project", ":calf-ui"), ("task", ":calf-share:publish"),
                    ("report_directory", "calf-share/build/test-results/foreign"),
                    ("test_filter", "com.mohamedrejeb.calf.share.*"), ("required_testcases", []),
                    ("required_original_xml", True), ("required_original_xml", 2),
                    ("test_source_files", []), ("test_source_sets", ["commonTest"]),
                    ("test_source_sha256", {}), ("browser_http_fixture", "foreign.js"),
                ):
                    plan = self.plan(root, suite)
                    plan["expected"][0][key] = value
                    with self.subTest(suite=suite, field=key, value=value), self.assertRaises(ValueError):
                        lt.validate_test_focus(plan)
                for key, value in (("complete_suite_requested", True),
                                   ("explicit_module_subset", ["calf-share", "calf-ui"]),
                                   ("inherited_test_source_sets", ["webTest"])):
                    plan = self.plan(root, suite)
                    plan[key] = value
                    with self.subTest(suite=suite, field=key), self.assertRaises(ValueError):
                        lt.validate_test_focus(plan)

    def test_actual_target_case_inventory_refuses_missing_foreign_and_duplicate_identities(self):
        for suite in ("js", "wasm"):
            cases = self.cases(suite)
            self.assertTrue(lt.share_clipboard_native_case_inventory(suite, cases))
            malformed = [[], cases[:-1], cases + [cases[0]], [cases[0]] * 4]
            for field, value in (("classname", CLASS), ("classname", lt.SUITES[suite][0] + ".foreign"),
                                 ("name", METHODS[0]), ("name", "WebSharePromiseTest.accepted"),
                                 ("name", METHODS[0] + "[foreign, browser, synthetic]")):
                changed = copy.deepcopy(cases)
                changed[0][field] = value
                malformed.append(changed)
            for changed in malformed:
                with self.subTest(suite=suite, malformed=changed):
                    self.assertFalse(lt.share_clipboard_native_case_inventory(suite, changed))
            opposite = "wasm" if suite == "js" else "js"
            self.assertFalse(lt.share_clipboard_native_case_inventory(opposite, cases))

    def test_fresh_single_original_synthetic_xml_has_exact_coverage_and_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            for suite in ("js", "wasm"):
                plan = self.plan(root, suite)
                receipt = self.collect(plan)
                self.assertFalse(receipt["errors"])
                self.assertEqual(4, receipt["totals"]["tests"])
                self.assertEqual(4, receipt["totals"]["passed"])
                for options in (
                    {"cases": []}, {"cases": self.cases(suite)[:-1]}, {"duplicate": True},
                    {"stale": True}, {"markers": 0}, {"markers": 2},
                    {"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                ):
                    with self.subTest(suite=suite, options=options):
                        rejected = self.collect(plan, **options)
                        self.assertTrue(rejected["errors"])

    def test_literal_native_environment_and_completion_observation_is_source_locked(self):
        source = (lt.ROOT / SOURCE).read_text()
        fixture = (lt.ROOT / FIXTURE).read_text()
        self.assertIn('assertEquals("denied", permissionState()', source)
        self.assertIn('assertEquals("NotAllowedError", clipboardFixtureValue("errorName"))', source)
        self.assertIn('assertEquals("DOMException", clipboardFixtureValue("errorType"))', source)
        self.assertIn('assertFalse(clipboardFixtureSecureContext(), "Actual HTTP', source)
        self.assertIn('assertTrue(event.isTrusted', source)
        self.assertIn('assertTrue(clipboardFixtureActivation()', source)
        self.assertIn('assertTrue(document.hasFocus()', source)
        self.assertIn('assertTrue(results.isEmpty()', source)
        self.assertIn('owner.launch(ShareContent.Text(ownedText())) // No dispatch/suspension', source)
        self.assertIn("Reflect.apply(nativeWrite, clipboard, [text])", fixture)
        self.assertIn("return promise; // EXACT native Promise", fixture)
        self.assertIn("headers['Permissions-Policy'] = 'clipboard-read=(), clipboard-write=()'", fixture)
        self.assertIn("nativecmpkit-clipboard-insecure.invalid", fixture)
        self.assertIn("await selected(); // Real compiled library-level method", fixture)
        self.assertIn("'|passed|' + h.unhandled + '|' + invocations", fixture)
        self.assertNotIn("|passed|0|1", fixture)
        self.assertNotIn("sameNativePromise", fixture + source)
        for forbidden in ("readText(", "readClipboard(", "userGesture: true", "Browser.grantPermissions",
                          "--disable-web-security", "--unsafely-treat-insecure-origin-as-secure",
                          "--ignore-certificate-errors", "window.isSecureContext ="):
            self.assertNotIn(forbidden, fixture + source)
        for helper in (JS_HELPER, WASM_HELPER):
            text = (lt.ROOT / helper).read_text()
            self.assertIn("navigator.permissions.query({name:'clipboard-write'})", text)
            self.assertIn("p.state", text)

    def test_owning_open_input_and_close_are_reserved_and_cleanup_is_coalesced(self):
        fixture = (lt.ROOT / FIXTURE).read_text()
        source = (lt.ROOT / SOURCE).read_text()
        opened = fixture[fixture.index("if (action === 'open')"):fixture.index("const session = sessions.get(token);")]
        self.assertLess(opened.index("sessions.set(token, session)"), opened.index("await bounded(scriptUrls"))
        click = fixture[fixture.index("const click = session =>"):fixture.index("const jsValue = value =>")]
        self.assertLess(click.index("session.clickStarted = true"), click.index("await connect(session)"))
        closed = fixture[fixture.index("const close = session =>"):fixture.index("const middleware =")]
        self.assertIn("if (session.closeOperation) return session.closeOperation", closed)
        self.assertLess(closed.index("session.closing = true"), closed.index("await session.clickOperation"))
        self.assertLess(closed.index("await session.clickOperation"), closed.index("await stopConnection(session)"))
        self.assertIn("if (primary) throw primary", closed)
        self.assertIn("fs.constants.O_NOFOLLOW", fixture)
        self.assertIn("owner.launcher._process !== owner.child", fixture)
        self.assertIn("owner.launcher.STATE_CAPTURED", fixture)
        self.assertIn("targetInfos.filter(info => info.type === 'page' && info.url === session.owner.url)", fixture)
        self.assertIn("--remote-debugging-port=0", fixture)
        self.assertIn("fs.mkdtempSync(path.join(karmaRoot,", fixture)
        self.assertIn("fs.chmodSync(directory, 0o700)", fixture)
        self.assertIn("Exact inherited Chrome profile option changed", fixture)
        self.assertIn("connection.closeObserved", fixture)
        self.assertIn("openAttempted = true // The exact token also owns cleanup", source)
        self.assertIn("if (openAttempted)", source)
        self.assertIn('window.removeEventListener("message", received)', source)
        self.assertIn("native.remove()", source)


if __name__ == "__main__":
    unittest.main()
