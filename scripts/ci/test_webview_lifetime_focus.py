"""Finite native lifetime selection/source/evidence guards; synthetic tooling, not native tests."""
from collections import Counter
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as r
import native_test_policy as policy
import workflow_matrix as matrix


class WebViewLifetimeFocusTests(unittest.TestCase):
    def plan(self, suite="desktop", root=r.ROOT, focus=r.WEBVIEW_LIFETIME_FOCUS):
        return r.plan(root, suite, only_modules=("calf-webview",), focus=focus)

    def collect(self, suite="desktop", cases=None, outcome="", markers=1, stale=False, duplicate=False,
                focus=r.WEBVIEW_LIFETIME_FOCUS):
        plan = self.plan(suite, focus=focus)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / plan["expected"][0]["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in r.webview_lifetime_identities(suite, focus) if cases is None else cases:
                node = ET.SubElement(xml, "testcase", **case)
                if outcome:
                    ET.SubElement(node, outcome)
            file = folder / "TEST-synthetic.xml"
            file.write_bytes(ET.tostring(xml))
            if duplicate:
                (folder / "TEST-duplicate.xml").write_bytes(file.read_bytes())
            now = time.time_ns()
            if stale:
                os.utime(file, ns=(now - 10_000_000_000, now - 10_000_000_000))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: markers}), host_system="Linux")

    def test_five_required_native_hosts_prioritize_android_and_linux_with_failure_only_profiles(self):
        rows = matrix.matrix("webview-lifetime")["include"]
        self.assertEqual(["android-device-api35", "desktop-linux-x64", "desktop-macos-arm64",
                          "desktop-macos-x64", "desktop-windows-x64"], [row["slot"] for row in rows])
        for row in rows:
            self.assertEqual("calf-webview", row["test-modules"])
            self.assertEqual(r.WEBVIEW_LIFETIME_FOCUS, row["test-focus"])
        for profile, slot in (("android", "android-device-api35"), ("linux", "desktop-linux-x64"),
                              ("macos-arm64", "desktop-macos-arm64"), ("macos-x64", "desktop-macos-x64"),
                              ("windows", "desktop-windows-x64")):
            self.assertEqual([slot], [row["slot"] for row in matrix.matrix("webview-lifetime-" + profile)["include"]])
        for profile in ("all", "core", "apple", "android-device", "webview-desktop"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))

    def test_desktop_runs_exactly_five_methods_and_device_one_lossless_class_of_three(self):
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(5, len(plan["expected"][0]["required_testcases"]))
        command = r.gradle_command("desktop", plan)
        self.assertEqual(5, command.count("--tests"))
        self.assertEqual(r.webview_lifetime_filter("desktop").split(","), [command[i + 1] for i, arg in enumerate(command) if arg == "--tests"])
        plan = self.plan("android-device")
        self.assertEqual(3, len(plan["expected"][0]["required_testcases"]))
        command = r.gradle_command("android-device", plan, android_serial="emulator-5588")
        selectors = [arg for arg in command if arg.startswith("-Pandroid.testInstrumentationRunnerArguments.class=")]
        self.assertEqual(["-Pandroid.testInstrumentationRunnerArguments.class=" + r.webview_lifetime_filter("android-device")], selectors)
        self.assertNotIn(",", selectors[0])
        self.assertNotIn("--tests", command)

    def test_intel_media_failure_only_profile_preserves_four_accepted_methods_and_other_hosts(self):
        row, = matrix.matrix("webview-lifetime-macos-media")["include"]
        self.assertEqual("desktop-macos-x64", row["slot"])
        self.assertEqual("calf-webview", row["test-modules"])
        self.assertEqual(r.WEBVIEW_MEDIA_FOCUS, row["test-focus"])
        plan = self.plan(focus=r.WEBVIEW_MEDIA_FOCUS)
        identity, = plan["expected"][0]["required_testcases"]
        self.assertEqual(r.WEBVIEW_LIFETIME_SPECS["desktop"][0]["methods"][2] + "[desktop]", identity["name"])
        command = r.gradle_command("desktop", plan)
        self.assertEqual(1, command.count("--tests"))
        self.assertEqual(r.webview_lifetime_filter("desktop", r.WEBVIEW_MEDIA_FOCUS), command[command.index("--tests") + 1])
        for suite in ("android-device", "android-host", "ios", "js", "wasm"):
            with self.assertRaises(ValueError): self.plan(suite, focus=r.WEBVIEW_MEDIA_FOCUS)
        self.assertEqual(5, len(self.plan()["expected"][0]["required_testcases"]))
        self.assertEqual(3, len(self.plan("android-device")["expected"][0]["required_testcases"]))
        for profile in ("webview-lifetime", "webview-lifetime-macos-x64"):
            self.assertTrue(all(row["test-focus"] == r.WEBVIEW_LIFETIME_FOCUS for row in matrix.matrix(profile)["include"]))

    def test_one_real_media_case_must_be_fresh_exact_nonzero_and_pass_without_missing_native_waivers(self):
        focus = r.WEBVIEW_MEDIA_FOCUS
        result = self.collect(focus=focus)
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["totals"]["passed"])
        for invalid in ({"cases": []}, {"cases": r.webview_lifetime_identities("desktop")},
                        {"cases": [{"classname": "Foreign", "name": "fake[desktop]"}]},
                        {"duplicate": True}, {"stale": True}, {"markers": 0}, {"markers": 2},
                        {"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"}):
            with self.subTest(invalid=invalid): self.assertTrue(self.collect(focus=focus, **invalid)["errors"])
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("task", ":calf-webview:publish")):
            plan = self.plan(focus=focus); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan(focus=focus); plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError): r.validate_test_focus(plan)

    def test_one_media_focus_is_transportable_through_real_cli_not_only_python_planner(self):
        args = ["library_tests.py", "plan", "--suite", "desktop", "--module", "calf-webview", "--focus", r.WEBVIEW_MEDIA_FOCUS]
        stream = io.StringIO()
        with patch("sys.argv", args), patch("sys.stdout", stream): self.assertEqual(0, r.main())
        document = json.loads(stream.getvalue())
        self.assertEqual(r.WEBVIEW_MEDIA_FOCUS, document["explicit_test_focus"])
        self.assertEqual(1, len(document["expected"][0]["required_testcases"]))
        self.assertFalse(document["complete_suite_requested"])
        for changed in (args[:3] + ["android-device"] + args[4:], args[:-1] + ["unreviewed-wildcard"]):
            with patch("sys.argv", changed), patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit) as failure:
                r.main()
            self.assertEqual(2, failure.exception.code)

    def test_android_media_recovery_transports_one_exact_failed_method_and_private_diagnostic_only(self):
        row, = matrix.matrix("webview-lifetime-android-media")["include"]
        self.assertEqual("android-device-api35", row["slot"])
        self.assertEqual(r.WEBVIEW_ANDROID_MEDIA_FOCUS, row["test-focus"])
        focus = r.WEBVIEW_ANDROID_MEDIA_FOCUS
        plan = self.plan("android-device", focus=focus)
        self.assertEqual(1, len(plan["expected"][0]["required_testcases"]))
        expected = r.WEBVIEW_LIFETIME_SPECS["android-device"][0]
        command = r.gradle_command("android-device", plan, android_serial="emulator-5588")
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + expected["classname"] + "#" + expected["methods"][1], command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitWebViewHeapDiagnostic=true", command)
        self.assertNotIn("--tests", command)
        self.assertNotIn("nativecmpkitWebViewHeapDiagnostic", " ".join(r.gradle_command("android-device", self.plan("android-device"), android_serial="emulator-5588")))
        args = ["library_tests.py", "plan", "--suite", "android-device", "--module", "calf-webview", "--focus", focus]
        stream = io.StringIO()
        with patch("sys.argv", args), patch("sys.stdout", stream): self.assertEqual(0, r.main())
        self.assertEqual(focus, json.loads(stream.getvalue())["explicit_test_focus"])
        for suite in ("desktop", "android-host", "ios", "js", "wasm"):
            with self.assertRaises(ValueError): self.plan(suite, focus=focus)
        self.assertEqual([], self.collect("android-device", focus=focus)["errors"])
        for invalid in ({"cases": []}, {"cases": r.webview_lifetime_identities("android-device")},
                        {"outcome": "failure"}, {"outcome": "error"}, {"outcome": "skipped"}, {"stale": True}, {"duplicate": True}):
            self.assertTrue(self.collect("android-device", focus=focus, **invalid)["errors"])
        source = (r.ROOT / expected["source"]).read_text()
        self.assertIn("Debug.dumpHprofData(dump.path)", source)
        self.assertIn("temporary.renameTo(complete)", source)
        self.assertIn("throw failure", source)
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertNotIn("private-webview-heap/**", workflow)
        self.assertNotIn("*.hprof", workflow)
        self.assertNotIn("*.jar", workflow[workflow.index("- name: Keep receipts and actual selected-task XML"):workflow.index("  consumer-core-io:")])

    def test_current_exact_nonzero_xml_is_accepted_in_its_disclosed_native_scope(self):
        for suite, count in (("desktop", 5), ("android-device", 3)):
            result = self.collect(suite)
            self.assertEqual([], result["errors"])
            self.assertEqual(count, result["totals"]["passed"])
            self.assertEqual(count, len(result["modules"][0]["native_scenarios"]))
            self.assertTrue(all(c["required_on_host"] for c in result["modules"][0]["native_scenarios"]))

    def test_empty_missing_extra_duplicate_and_wrong_class_or_target_cannot_pass(self):
        for suite in ("desktop", "android-device"):
            actual = r.webview_lifetime_identities(suite)
            variants = [[], actual[:-1], actual * 2, actual + [{**actual[0], "name": "unrelated"}]]
            for key, value in (("classname", "unrelated.NativeTest"), ("name", "unrelated[desktop]"),
                               ("name", actual[0]["name"] + "[iosSimulatorArm64]")):
                changed = copy.deepcopy(actual); changed[0][key] = value; variants.append(changed)
            for cases in variants:
                with self.subTest(suite=suite, cases=cases):
                    self.assertTrue(self.collect(suite, cases=cases)["errors"])
            self.assertTrue(self.collect(suite, duplicate=True)["errors"])

    def test_failures_errors_skips_stale_xml_and_absent_or_duplicate_actual_task_markers_are_rejected(self):
        for suite in ("desktop", "android-device"):
            for status in ("failure", "error", "skipped"):
                self.assertTrue(self.collect(suite, outcome=status)["errors"])
            self.assertTrue(self.collect(suite, stale=True)["errors"])
            for count in (0, 2):
                self.assertTrue(self.collect(suite, markers=count)["errors"])

    def test_wrong_scope_task_filter_inventory_source_fixture_or_full_suite_claim_is_rejected(self):
        for suite in ("ios", "js", "wasm", "android-host"):
            with self.assertRaises(ValueError):
                self.plan(suite)
        for suite in ("desktop", "android-device"):
            for key, value in (("module", "calf-io"), ("task", ":calf-webview:publish"), ("test_filter", "*"),
                               ("required_testcases", []), ("test_source_files", [])):
                plan = self.plan(suite); plan["expected"][0][key] = value
                with self.subTest(suite=suite, key=key), self.assertRaises(ValueError):
                    r.validate_test_focus(plan)
            plan = self.plan(suite); plan["complete_suite_requested"] = True
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan("android-device"); plan["expected"][0]["native_fixture_paths"] = []
        with self.assertRaises(ValueError): r.validate_test_focus(plan)
        with self.assertRaises(ValueError): r.gradle_command("android-host", self.plan())

    def temporary_root(self, directory, suite):
        root = Path(directory).resolve()
        (root / "settings.gradle.kts").write_text('include(\n    ":calf-webview",\n)\n')
        module = root / "calf-webview"; module.mkdir()
        (module / "build.gradle.kts").write_text("// synthetic build, never executed\n")
        for group in r.WEBVIEW_LIFETIME_SPECS[suite]:
            path = root / group["source"]; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((r.ROOT / group["source"]).read_text())
        if suite == "android-device":
            for relative in r.WEBVIEW_DEVICE_FIXTURES:
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((r.ROOT / relative).read_text())
        return root

    def test_valid_source_calibration_precedes_missing_renamed_ignored_or_extra_method_rejection(self):
        for suite in ("desktop", "android-device"):
            with tempfile.TemporaryDirectory() as directory:
                root = self.temporary_root(directory, suite)
                self.assertTrue(r.validate_test_focus(self.plan(suite, root)))
                group = r.WEBVIEW_LIFETIME_SPECS[suite][0]; path = root / group["source"]; original = path.read_text()
                for changed in (original.replace(group["methods"][0], "wrongMethod", 1),
                                original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun extra() {}\n"):
                    path.write_text(changed)
                    with self.assertRaises(ValueError): self.plan(suite, root)
                path.write_text(original)
                self.assertTrue(r.validate_test_focus(self.plan(suite, root)))
                path.unlink()
                with self.assertRaises(ValueError): self.plan(suite, root)

    def test_exact_test_only_loopback_policy_cannot_become_global_wildcard_subtree_exported_or_entity_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.temporary_root(directory, "android-device")
            self.assertTrue(r.validate_test_focus(self.plan("android-device", root)))
            path = root / r.WEBVIEW_DEVICE_FIXTURES[1]; original = path.read_text()
            for changed in (original.replace('cleartextTrafficPermitted="false"', 'cleartextTrafficPermitted="true"'),
                            original.replace("127.0.0.1", "localhost"), original.replace("127.0.0.1", "*"),
                            original.replace('includeSubdomains="false"', 'includeSubdomains="true"'),
                            original.replace("<network-security-config>", '<!DOCTYPE network-security-config [<!ENTITY host "127.0.0.1">]><network-security-config>')):
                path.write_text(changed)
                with self.assertRaises(ValueError): self.plan("android-device", root)
            path.write_text(original)
            manifest = root / r.WEBVIEW_DEVICE_FIXTURES[0]; initial = manifest.read_text()
            for changed in (initial.replace('android:exported="false"', 'android:exported="true"'),
                            initial.replace('android:usesCleartextTraffic="false"', 'android:usesCleartextTraffic="true"'),
                            initial.replace("android.permission.INTERNET", "unrelated.permission")):
                manifest.write_text(changed)
                with self.assertRaises(ValueError): self.plan("android-device", root)
            manifest.write_text(initial)
            self.assertTrue(r.validate_test_focus(self.plan("android-device", root)))
            path.unlink()
            with self.assertRaises(ValueError): self.plan("android-device", root)

    def test_full_native_suites_still_require_stop_history_and_all_new_lifetime_cases(self):
        desktop = [{"classname": "com.mohamedrejeb.calf.ui.web.JavaFxWebViewTest", "name": m + "[desktop]", "status": "passed"}
                   for m in policy.DESKTOP_WEBVIEW_STOP_CASES]
        desktop += [{"classname": "com.mohamedrejeb.calf.ui.web.DesktopWebViewLifetimeTest", "name": m + "[desktop]", "status": "passed"}
                    for m in policy.DESKTOP_WEBVIEW_LIFETIME_CASES]
        device = [{"classname": "com.mohamedrejeb.calf.ui.web.AndroidWebViewHistoryDeviceTest",
                   "name": "navigatorReplacementReadsRealBrowserHistoryWithoutAnotherPageEvent", "status": "passed"}]
        device += [{"classname": c["classname"], "name": c["name"], "status": "passed"} for c in r.webview_lifetime_identities("android-device")]
        for suite, cases in (("desktop", desktop), ("android-device", device)):
            scenarios, errors = policy.apply("calf-webview", suite, cases, "Linux", False)
            self.assertEqual([], errors); self.assertEqual(len(cases), len(scenarios))
            for index in range(len(cases)):
                changed = copy.deepcopy(cases); changed.pop(index)
                self.assertTrue(policy.apply("calf-webview", suite, changed, "Linux", False)[1])
            for status in ("failed", "error", "skipped"):
                changed = copy.deepcopy(cases); changed[-1]["status"] = status
                self.assertTrue(policy.apply("calf-webview", suite, changed, "Linux", False)[1])
        self.assertTrue(policy.apply("calf-webview", "android-device", device, "Windows", False)[1])
        self.assertEqual(([], []), policy.apply("calf-webview", "js", [], "Linux", False))

    def test_native_storage_and_fixtures_keep_live_handles_observability_real_engines_and_minimum_permissions(self):
        for relative in ("calf-webview/src/androidMain/kotlin/com/mohamedrejeb/calf/ui/web/WebView.android.kt",
                         "calf-webview/src/desktopMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.desktop.kt"):
            source = (r.ROOT / relative).read_text()
            self.assertIn("AtomicReference<WebView?>(null)", source)
            self.assertIn("attachmentVersion by mutableLongStateOf", source)
            self.assertNotIn("webView by mutableStateOf<WebView?>", source)
        desktop = (r.ROOT / r.WEBVIEW_LIFETIME_SPECS["desktop"][0]["source"]).read_text()
        device = (r.ROOT / r.WEBVIEW_LIFETIME_SPECS["android-device"][0]["source"]).read_text()
        for source in (desktop, device):
            for forbidden in ("@Ignore", "assumeTrue(", "assumeFalse(", "Robolectric", "Platform.exit("):
                # The explanatory "no Robolectric" header is not a runtime replacement.
                if forbidden != "Robolectric": self.assertNotIn(forbidden, source)
            self.assertIn("WeakReference", source)
            self.assertIn("observedAttachment", source)
            self.assertIn("currentTime > 0.1", source)
            self.assertIn("disconnected.await", source)
        self.assertIn("host.assertResumed()", device)
        self.assertIn("Parcel.obtain()", device)
        self.assertIn("WebStateSaver.restore", device)
        self.assertIn("ReferenceQueue<Any>()", device)
        self.assertIn("queue.poll() === reference", device)
        self.assertNotIn("it.get()", device)
        self.assertNotIn("reference.get()", device)
        self.assertIn("assertCollected(fixture.nativeReferences)", device)
        self.assertIn("fixture.activityReferences.single().wasCollected()", device)
        self.assertIn("bFixture.nativeReferences.single().wasCollected()", device)
        self.assertIn("Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_MULTIPLE_TASK", device)
        self.assertIn('.setAction("com.mohamedrejeb.calf.ui.web.NATIVE_LIFETIME.$key")', device)
        self.assertIn('it.intent.getStringExtra("nativecmpkit-lifetime") == key', device)
        self.assertIn("assertNotEquals(a.taskId(), activeSecond.taskId()", device)
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("pulseaudio libasound2-plugins", workflow)
        self.assertIn("/desktop-audio/receipt.json", workflow)
        self.assertNotIn("/desktop-audio/**", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)


if __name__ == "__main__": unittest.main()
