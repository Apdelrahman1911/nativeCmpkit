"""Finite native lifetime selection/source/evidence guards; synthetic tooling, not native tests."""
from collections import Counter
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as r
import native_test_policy as policy
import workflow_matrix as matrix


class WebViewLifetimeFocusTests(unittest.TestCase):
    def plan(self, suite="desktop", root=r.ROOT):
        return r.plan(root, suite, only_modules=("calf-webview",), focus=r.WEBVIEW_LIFETIME_FOCUS)

    def collect(self, suite="desktop", cases=None, outcome="", markers=1, stale=False, duplicate=False):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / plan["expected"][0]["report_directory"]
            folder.mkdir(parents=True)
            xml = ET.Element("testsuite")
            for case in r.webview_lifetime_identities(suite) if cases is None else cases:
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
        self.assertIn("assertNotEquals(a.taskId(), activeSecond.taskId()", device)
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("pulseaudio libasound2-plugins", workflow)
        self.assertIn("/desktop-audio/receipt.json", workflow)
        self.assertNotIn("/desktop-audio/**", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)


if __name__ == "__main__": unittest.main()
