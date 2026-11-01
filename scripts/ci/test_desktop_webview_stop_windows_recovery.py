"""One failed Windows Stop route and refusal diagnostics: source/tooling controls, not native acceptance.

Privately authored proposal controls. Authoring/syntax inspection does not execute
these methods; a synthetic XML pass below cannot qualify an actual Windows run.
"""
from collections import Counter
import ast
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

import library_tests as lt
import workflow_matrix as matrix

FOCUS = "webview-desktop-stop-windows-recovery"
CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewStopRedirectAcceptanceTest"
METHOD = "publicStopCancelsOneHeldNativeRequestBeforeAnyResponseAndRecoversOnTheSameOwner"
REDIRECT = "actual302RedirectAndPublicReloadKeepNativeRequestAndTerminalMetadataDistinct"
SOURCE = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewStopRedirectAcceptanceTest.kt"
SOURCE_SHA256 = "5a7db4734c215546d751b702b2b9c92766ec81e54f2eb33a788b0687cdebb4d7"
PREIMAGE_SHA256 = "0a8301aa683b0b5e1f767e8d7928e21a9038b74e3a26c038e612f5a22958ce8b"
ACCEPTED_CLASS = "com.mohamedrejeb.calf.ui.web.DesktopWebViewRequestStateAcceptanceTest"
ACCEPTED_METHOD = "twoHeldNativeTransportFailuresResetOldErrorsAndRecoverOnTheSameOwner"
ACCEPTED_SOURCE = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewRequestStateAcceptanceTest.kt"
CASE = {"classname": CLASS, "name": METHOD + "[desktop]"}
ROW = {"slot": "desktop-windows-x64", "suite": "desktop", "runner": "windows-2025",
       "arch": "x64", "python": "python", "test-modules": "calf-webview", "test-focus": FOCUS}
PREDICATES = (
    "native.engine.loadWorker.state == Worker.State.CANCELLED &&",
    "!native.engine.loadWorker.isRunning && state.loadingState == LoadingState.Finished &&",
    "cancellations.get() == 1 && server.peerEofs(Endpoint.StopHeld) == 1 &&",
    "server.pending(Endpoint.StopHeld) == 0",
)
ORIGINAL_BLOCK = '''                await("public Stop native cancellation and actual pre-header client EOF") {
                    native.engine.loadWorker.state == Worker.State.CANCELLED &&
                        !native.engine.loadWorker.isRunning && state.loadingState == LoadingState.Finished &&
                        cancellations.get() == 1 && server.peerEofs(Endpoint.StopHeld) == 1 &&
                        server.pending(Endpoint.StopHeld) == 0
                }
'''


def digest(source):
    return hashlib.sha256(source.encode()).hexdigest()


def code_only(source):
    return re.sub(r"(?m)//[^\n]*", "", re.sub(r"(?s)/\*.*?\*/", "", source))


class DesktopWebViewStopWindowsRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Source-only planning when the lead later executes controls. No Gradle/native invocation.
        cls.original_plan = lt.plan(lt.ROOT, "desktop", only_modules=("calf-webview",), focus=FOCUS)

    def plan(self):
        return copy.deepcopy(self.original_plan)

    def source_root(self, directory):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        build = root / "calf-webview/build.gradle.kts"
        build.parent.mkdir()
        build.write_text("// Explicitly synthetic discovery root, never compiled.\n")
        for relative in (SOURCE, ACCEPTED_SOURCE):
            file = root / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes((lt.ROOT / relative).read_bytes())
        return root

    def collect(self, reports=None, outcome="", date=None, markers=1):
        plan = self.plan()
        expected, = plan["expected"]
        reports = [[CASE]] if reports is None else reports
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / expected["report_directory"]
            folder.mkdir(parents=True)
            files = []
            for index, cases in enumerate(reports):
                xml = ET.Element("testsuite")
                for case in cases:
                    node = ET.SubElement(xml, "testcase", **case)
                    if outcome:
                        ET.SubElement(node, outcome)
                file = folder / ("TEST-explicitly-synthetic-%s.xml" % index)
                file.write_bytes(ET.tostring(xml))
                files.append(file)
            now = time.time_ns()
            if date and files:
                changed = now + (20_000_000_000 if date == "future" else -20_000_000_000)
                os.utime(files[0], ns=(changed, changed))
            return lt.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                      Counter({expected["task"]: markers}), host_system="Windows")

    def test_one_exact_windows_row_inherits_all_canonical_fields_but_focus_and_full_slots_stay_eleven(self):
        self.assertEqual({"include": [ROW]}, matrix.matrix(FOCUS))
        inherited, = matrix.matrix("webview-desktop-request-state-windows-single")["include"]
        self.assertEqual({**inherited, "test-focus": FOCUS}, ROW)
        self.assertEqual(("desktop-windows-x64",), matrix.PROFILES[FOCUS])
        self.assertEqual("calf-webview", matrix.MODULE_SUBSETS[FOCUS])
        text = (lt.ROOT / "scripts/ci/workflow_matrix.py").read_text()
        tree = ast.parse(text)
        slots = next(node for node in tree.body if isinstance(node, ast.Assign) and
                     any(isinstance(target, ast.Name) and target.id == "SLOTS" for target in node.targets))
        self.assertEqual(11, len(ast.literal_eval(slots.value)))
        self.assertEqual("12305c5b967e1b7ea85420f3827992ea8fdd481247ba469d3161f74c783e3d3d",
                         digest(ast.get_source_segment(text, slots)))

    def test_profile_slot_module_and_every_canonical_field_drift_are_refused(self):
        for slots in ((), ("desktop-linux-x64",), ("desktop-windows-x64", "desktop-linux-arm64"),
                      ("desktop-windows-x64", "desktop-windows-x64")):
            with patch.dict(matrix.PROFILES, {FOCUS: slots}), self.assertRaises(ValueError):
                matrix.matrix(FOCUS)
        for modules in (None, "calf-io", "calf-webview,calf-ui", ""):
            with patch.dict(matrix.MODULE_SUBSETS, {FOCUS: modules}), self.assertRaises(ValueError):
                matrix.matrix(FOCUS)
        for key, value in (("runner", "ubuntu-24.04"), ("arch", "arm64"), ("suite", "ios"),
                           ("python", "python3"), ("native-ui", "true"), ("arbitrary", "field")):
            altered = tuple({**row, key: value} if row["slot"] == ROW["slot"] else dict(row) for row in matrix.SLOTS)
            with patch.object(matrix, "SLOTS", altered), self.assertRaises(ValueError):
                matrix.matrix(FOCUS)

    def test_specs_filter_identity_and_source_are_exactly_one_failed_stop_not_accepted_request_or_redirect(self):
        spec = {"classname": CLASS, "method": METHOD, "source": SOURCE, "sha256": SOURCE_SHA256}
        self.assertEqual([spec], lt.webview_desktop_request_specs(FOCUS))
        self.assertEqual([CASE], lt.webview_desktop_request_identities(FOCUS))
        self.assertEqual(CLASS + "." + METHOD, lt.webview_desktop_request_filter(FOCUS))
        self.assertNotIn(ACCEPTED_CLASS, lt.webview_desktop_request_filter(FOCUS))
        self.assertNotIn(REDIRECT, lt.webview_desktop_request_filter(FOCUS))
        self.assertEqual(frozenset({("Windows", "x64")}), lt.WEBVIEW_DESKTOP_REQUEST_HOSTS_BY_FOCUS[FOCUS])

    def test_exact_one_method_plan_retains_inherited_compilation_and_one_original_xml(self):
        plan = self.plan()
        expected, = plan["expected"]
        self.assertTrue(lt.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(["calf-webview"], plan["explicit_module_subset"])
        self.assertEqual(list(lt.SUITES["desktop"][1]), plan["inherited_test_source_sets"])
        self.assertEqual(FOCUS, plan["explicit_test_focus"])
        self.assertEqual("calf-webview", expected["module"])
        self.assertEqual(":calf-webview", expected["project"])
        self.assertEqual(":calf-webview:desktopTest", expected["task"])
        self.assertEqual("calf-webview/build/test-results/desktopTest", expected["report_directory"])
        self.assertEqual(["desktopTest"], expected["test_source_sets"])
        self.assertEqual([SOURCE], expected["test_source_files"])
        self.assertEqual({SOURCE: SOURCE_SHA256}, expected["test_source_sha256"])
        self.assertEqual(CLASS + "." + METHOD, expected["test_filter"])
        self.assertEqual([CASE], expected["required_testcases"])
        self.assertIs(type(expected["required_original_xml"]), int)
        self.assertEqual(1, expected["required_original_xml"])
        self.assertIn("six", plan["scope"])
        self.assertIn("10s", plan["scope"])
        self.assertIn("not selected or replayed", plan["scope"])

    def test_filter_identity_source_hash_task_report_and_original_count_mutations_cannot_expand_or_turn_green(self):
        for key, value in (("test_filter", "*"), ("test_filter", CLASS), ("test_filter", ACCEPTED_CLASS + "." + ACCEPTED_METHOD),
                           ("required_testcases", []), ("required_testcases", [CASE, CASE]),
                           ("test_source_files", []), ("test_source_files", [SOURCE, ACCEPTED_SOURCE]),
                           ("test_source_sets", ["commonTest"]), ("test_source_sha256", {}),
                           ("test_source_sha256", {SOURCE: PREIMAGE_SHA256}), ("required_original_xml", None),
                           ("required_original_xml", True), ("required_original_xml", 0), ("required_original_xml", 2),
                           ("task", ":calf-webview:publish"), ("project", ":calf-io"), ("module", "calf-io"),
                           ("report_directory", "calf-io/build/test-results/desktopTest")):
            changed = self.plan()
            changed["expected"][0][key] = value
            with self.assertRaises(ValueError):
                lt.validate_test_focus(changed)
        for key, value in (("suite", "ios"), ("complete_suite_requested", True),
                           ("explicit_module_subset", ["calf-webview", "calf-io"]), ("inherited_test_source_sets", ["iosTest"])):
            changed = self.plan()
            changed[key] = value
            with self.assertRaises(ValueError):
                lt.validate_test_focus(changed)

    def test_wrong_suites_modules_unknown_profiles_and_unknown_focuses_have_no_full_suite_fallback(self):
        for suite in ("android-host", "android-device", "js", "wasm", "ios"):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=("calf-webview",), focus=FOCUS)
        for modules in (None, (), ("calf-io",), ("calf-webview", "calf-ui"), ("calf-webview", "calf-webview")):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, "desktop", only_modules=modules, focus=FOCUS)
        for unknown in (FOCUS + "-linux", FOCUS + "*", "unknown-windows-stop"):
            with self.assertRaises(ValueError):
                matrix.matrix(unknown)
            with self.assertRaises(ValueError):
                lt.webview_desktop_request_specs(unknown)

    def test_supported_windows_aliases_form_one_actual_method_selector_with_original_capacity_and_no_publish(self):
        for architecture in ("x64", "AMD64", "x86_64"):
            lt.validate_webview_desktop_request_host("Windows", architecture, FOCUS)
            with patch("library_tests.platform.system", return_value="Windows"), patch("library_tests.platform.machine", return_value=architecture):
                command = lt.gradle_command("desktop", self.plan())
            self.assertEqual([CLASS + "." + METHOD], [command[index + 1] for index, token in enumerate(command) if token == "--tests"])
            self.assertEqual(1, command.count("--tests"))
            self.assertIn(":calf-webview:desktopTest", command)
            self.assertIn("--max-workers=2", command)
            self.assertIn("-Dorg.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8", command)
            self.assertIn("--no-daemon", command)
            self.assertNotRegex(" ".join(command), r"publish|com\.sun\.webkit\.useHTTP2Loader|nativecmpkitDesktopSecurityFocus|--offline")

    def test_other_host_unknown_architecture_and_missing_runtime_identity_are_refused_before_command(self):
        for system, architecture in (("Linux", "x64"), ("Linux", "arm64"), ("Darwin", "arm64"), ("Darwin", "x64"),
                                     ("Windows", "arm64"), ("Windows", "riscv64"), ("FreeBSD", "x64"),
                                     (None, "x64"), ("Windows", None)):
            with self.assertRaises(ValueError):
                lt.validate_webview_desktop_request_host(system, architecture, FOCUS)
            with patch("library_tests.platform.system", return_value=system), patch("library_tests.platform.machine", return_value=architecture):
                with self.assertRaises(ValueError):
                    lt.gradle_command("desktop", self.plan())

    def test_cli_plan_is_source_only_and_unknown_focus_is_refused(self):
        args = ["library_tests.py", "plan", "--suite", "desktop", "--module", "calf-webview", "--focus", FOCUS]
        output = io.StringIO()
        with patch("sys.argv", args), patch("sys.stdout", output):
            self.assertEqual(0, lt.main())
        self.assertEqual(self.plan(), json.loads(output.getvalue()))
        with patch("sys.argv", args[:-1] + ["unknown-windows-stop"]), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as refusal:
            lt.main()
        self.assertEqual(2, refusal.exception.code)

    def test_selected_changed_missing_or_symlink_fixture_is_refused_before_any_native_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.source_root(directory)
            self.assertTrue(lt.validate_test_focus(lt.plan(root, "desktop", only_modules=("calf-webview",), focus=FOCUS)))
            file = root / SOURCE
            original = file.read_bytes()
            for needle in (METHOD, "server.peerEofs(Endpoint.StopHeld) == 1", "withTimeout(10_000)", "stopSnapshot"):
                file.write_bytes(original.replace(needle.encode(), b"unreviewed", 1))
                with self.assertRaises(ValueError):
                    lt.plan(root, "desktop", only_modules=("calf-webview",), focus=FOCUS)
                file.write_bytes(original)
            file.unlink()
            with self.assertRaises(ValueError):
                lt.plan(root, "desktop", only_modules=("calf-webview",), focus=FOCUS)
            file.symlink_to(root / "calf-webview/build.gradle.kts")
            with self.assertRaises(ValueError):
                lt.plan(root, "desktop", only_modules=("calf-webview",), focus=FOCUS)

    def test_one_fresh_exact_synthetic_pass_is_only_collector_calibration_not_windows_acceptance(self):
        result = self.collect()
        self.assertEqual([], result["errors"], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])
        self.assertEqual(0, result["totals"]["not_applicable"])
        scenario, = result["modules"][0]["native_scenarios"]
        self.assertEqual(CASE, {key: scenario[key] for key in CASE})
        self.assertEqual(SOURCE, scenario["source"])
        self.assertTrue(scenario["required_on_host"])
        self.assertEqual("required-executed", scenario["disposition"])

    def test_missing_empty_duplicate_accepted_redirect_foreign_wrong_target_and_mixed_xml_are_refused(self):
        accepted = {"classname": ACCEPTED_CLASS, "name": ACCEPTED_METHOD + "[desktop]"}
        redirect = {"classname": CLASS, "name": REDIRECT + "[desktop]"}
        foreign = {"classname": "Foreign.Test", "name": METHOD + "[desktop]"}
        mutations = ([], [[]], [[CASE], []], [[CASE, CASE]], [[CASE], [CASE]], [[accepted]], [[redirect]],
                     [[foreign]], [[CASE, accepted]], [[CASE, redirect]], [[CASE], [accepted]],
                     [[{**CASE, "name": METHOD}]], [[{**CASE, "name": METHOD + "[iosSimulatorArm64]"}]])
        for reports in mutations:
            self.assertTrue(self.collect(reports=reports)["errors"])

    def test_failed_error_skipped_stale_future_or_nonfresh_task_markers_stay_red(self):
        for changed in ({"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"},
                        {"date": "stale"}, {"date": "future"}, {"markers": 0}, {"markers": 2}):
            self.assertTrue(self.collect(**changed)["errors"])

    def test_original_six_predicates_deadline_public_command_and_no_teardown_before_witness_are_retained(self):
        text = (lt.ROOT / SOURCE).read_text()
        stop = text.split("    @Test fun " + REDIRECT, 1)[0]
        block = stop.split('await("public Stop native cancellation and actual pre-header client EOF") {', 1)[1].split("                } catch (error: AssertionError)", 1)[0]
        tail = block.split('";closing=${server.isClosing()}")', 1)[1]
        self.assertEqual(list(PREDICATES), [line.strip() for line in tail.splitlines() if line.strip() not in ("", "}")])
        self.assertEqual(1, stop.count("navigator.stopLoading()"))
        self.assertLess(stop.index("navigator.stopLoading()"), stop.index("val stopSnapshot"))
        self.assertLess(stop.index("server.peerEofs(Endpoint.StopHeld) == 1"), stop.index("finally"))
        self.assertLess(stop.index("server.peerEofs(Endpoint.StopHeld) == 1"), stop.index("navigator.loadUrl(server.url(Endpoint.Recovery))"))
        self.assertIn("withTimeout(10_000) { while (!onFxThread(condition)) delay(25) }", text)
        for required in ("server.pending(Endpoint.StopHeld) == 1", "Worker.State.RUNNING", "assertEquals(0, server.responses(Endpoint.StopHeld))",
                         "assertEquals(0, server.peerEofs(Endpoint.StopHeld))", "assertEquals(0, cancellations.get())", "assertFalse(server.isClosing()",
                         "assertSame(native, state.webView); assertSame(owner, state.owner)", "removeListener(observer)"):
            self.assertIn(required, stop)
        held = code_only(text).split("Endpoint.StopHeld -> {", 1)[1].split("Endpoint.Redirect -> {", 1)[0]
        self.assertIn("check(input.read() == -1)", held)
        self.assertIn("current.peerEofs.incrementAndGet(); return", held)
        self.assertNotRegex(held, r"respond\(|closeOwnedSocket\(|SocketException")

    def test_diagnostic_is_only_last_poll_fixed_scalars_preserves_failure_cause_and_has_no_competing_owner_or_fabrication(self):
        text = (lt.ROOT / SOURCE).read_text()
        inserted = text.split("                // Scalar-only last FX-poll sample;", 1)[1].split("                assertFalse(server.isClosing())", 1)[0]
        snapshot = inserted.split('stopSnapshot.set("sampled=true" +', 1)[1].split("                        native.engine.loadWorker.state ==", 1)[0]
        scalars = re.findall(r'";([A-Za-z]+)=\$\{([^\n]+)\}"', snapshot)
        self.assertEqual([("worker", "native.engine.loadWorker.state.name"), ("running", "native.engine.loadWorker.isRunning"),
                          ("finished", "state.loadingState == LoadingState.Finished"), ("cancellations", "cancellations.get()"),
                          ("peerEofs", "server.peerEofs(Endpoint.StopHeld)"), ("pending", "server.pending(Endpoint.StopHeld)"),
                          ("arrivals", "server.arrivals(Endpoint.StopHeld)"), ("responses", "server.responses(Endpoint.StopHeld)"),
                          ("closing", "server.isClosing()")], scalars)
        self.assertIn('val stopSnapshot = AtomicReference("sampled=false")', inserted)
        self.assertIn('throw AssertionError("public Stop witness refused; ${stopSnapshot.get()}", error)', inserted)
        self.assertNotRegex(inserted, r"print|Logger|System\.|server\.url|\.message|\.exception|\.port|\.pid|\.nonce|\.getProperty|\.setProperty")
        code = code_only(text)
        self.assertNotRegex(code, r"consumeNavigationEvents\s*\(|\.engine\.(load|loadContent|reload)\s*\(|loadWorker\.cancel\s*\(|"
                           r"state\.(content|requestedUrl|lastLoadedUrl|pageTitle|errorsForCurrentRequest|loadingState)\s*=(?!=)|"
                           r"\.(beginRequest|acceptContent)\s*\(|\bWebViewError\s*\(|@(Ignore|Disabled|IgnoredTest)\b")

    def test_sole_fixture_insertion_accepted_bodies_production_and_evidence_pipeline_are_unchanged(self):
        text = (lt.ROOT / SOURCE).read_text()
        left, inserted_and_rest = text.split("                // Scalar-only last FX-poll sample;", 1)
        _, right = inserted_and_rest.split("                assertFalse(server.isClosing())", 1)
        reconstructed = left + ORIGINAL_BLOCK + "                assertFalse(server.isClosing())" + right
        self.assertEqual(PREIMAGE_SHA256, digest(reconstructed))
        self.assertEqual(SOURCE_SHA256, digest(text))
        suffix = text[text.index("    @Test fun " + REDIRECT):]
        self.assertEqual("1c152af0b6f9015fbd719c8c505fc918742a620e35aff6e8cf4a2b8e5ff914f4", digest(suffix))
        preserved = {
            ACCEPTED_SOURCE: "c08bcdc062d18d24c5a370aaa818a8171c352d06acca35af1202fd4eb2c13f13",
            "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt": "598bd8a18431882e68b96a28ff70f65c641bf2a1d36486aeff0aae12b999ae39",
            "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebViewContracts.kt": "4a87aa4a7a17252f817f8bdc9b8de8fcda62fb6093bfed624db0bc5c6875647f",
            "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt": "36891159184df5bcd03b724b81070698c878022796a5b563994c58591c763791",
            "convention-plugins/src/main/kotlin/DesktopJavaFx.kt": "acf777bd8781de5e8aebb4a8be33b0e2649971696fa2168dc9d1e698fb87c2d5",
            "gradle/libs.versions.toml": "88b87d830087e6f63ebe6211f8f30b85d33e89322f837c27810b9091c1469449",
        }
        for relative, expected in preserved.items():
            self.assertEqual(expected, hashlib.sha256((lt.ROOT / relative).read_bytes()).hexdigest())
        source = (lt.ROOT / "scripts/ci/library_tests.py").read_text()
        # Pin only the owning existing XML branch, not unrelated report/control methods.
        start = '        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_DESKTOP_REQUEST_FOCUSES:\n'
        end = '        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_IDENTITY_FOCUSES:\n'
        fragment = start + source.split(start, 1)[1].split(end, 1)[0]
        self.assertEqual("b3df23f2636d6c1a420294d9ebdc8d37c8f24c0eb455fd1589dcb4e9447e00ad", digest(fragment))
        choices = re.search(r"options: \[([^\n]+)\]", (lt.ROOT / ".github/workflows/gradle.yml").read_text()).group(1).split(",")
        self.assertEqual(1, [choice.strip() for choice in choices].count(FOCUS))
        # Existing literal profiles are preserved; this new route cannot replay their accepted cells.
        self.assertEqual(2, len(lt.webview_desktop_request_specs("webview-desktop-request-state-stop")))
        self.assertEqual(3, len(lt.webview_desktop_request_specs("webview-desktop-request-state-stop-redirect")))


if __name__ == "__main__":
    unittest.main()
