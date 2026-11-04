# SPDX-License-Identifier: Apache-2.0
"""Five finite NEW source/routing/report controls; zero Android/native acceptance.

Synthetic XML/context fixtures below are named synthetic and never substitute
for the later one-method actual API35 capture, compiler or native source maps.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import android_camera_callback_native_focus as callback
import android_camera_receiver as receiver
import android_device_tests as device
import library_tests as library
import workflow_matrix as workflow


class AndroidCameraCallbackSourceRoutingTests(unittest.TestCase):
    def plan(self):
        return library.plan(library.ROOT, "android-device", only_modules=(callback.MODULE,), focus=callback.FOCUS)

    def test_leaf668_exact_three_fragments_and_native_hold_recomposition_cleanup_without_injection(self):
        self.assertTrue(callback.validate_current_sources(callback.ROOT))
        document = callback._document()
        self.assertEqual(callback.SEALED_LEAF_SHA256, document["sealed_leaf_sha256"])
        provider = (callback.ROOT / callback.PROVIDER_SOURCE).read_bytes()
        original = callback.source_before_callback672(callback.PROVIDER_SOURCE, provider)
        self.assertEqual("e222639ed728465798aa0be937f13dc181c36dfd566db0b2fa9bbdbe67f18532", callback.sha(original))
        self.assertEqual(3, len(document["bindings"][callback.PROVIDER_SOURCE]["fragments"]))
        marker = b"/**\n * Actual API23/35 Activity/Compose consumer"
        self.assertEqual(original[original.index(marker):], provider[provider.index(marker):])
        for relative, row in document["bindings"].items():
            after = (callback.ROOT / relative).read_bytes()
            before = callback.current_source_before_callback672(relative, after)
            self.assertEqual(row["before_sha256"], callback.sha(before))
            self.assertEqual(before, callback.source_before_callback672(relative, before))
            with self.assertRaises(ValueError): callback.current_source_before_callback672(relative, before)
            with self.assertRaises(ValueError): callback.source_before_callback672(relative, after + b"\nunknown-drift")
        for variant in ({**document, "schema_version": True}, {**document, "added_inputs": {}},
                        {**document, "sealed_leaf_sha256": "0" * 64}):
            with self.assertRaises(ValueError): callback._shape(variant)
        with self.assertRaises(ValueError): callback._json(b'{"scope":1,"scope":1}')
        read = callback._ordinary_bytes
        def changed(root, relative):
            raw = read(root, relative)
            return raw + b"\n// unknown callback source" if relative == callback.SOURCE else raw
        with patch.object(callback, "_ordinary_bytes", side_effect=changed):
            with self.assertRaises(ValueError): callback.validate_current_sources(callback.ROOT)
        native = (callback.ROOT / callback.SOURCE).read_text()
        self.assertEqual([callback.METHOD], re.findall(r"@Test\s+fun\s+(\w+)\s*\(", native))
        self.assertNotRegex(native, r"@(Ignore|Disabled|IgnoredTest)\b|\b(?:assumeTrue|assumeFalse|Assume)\b")
        restoration = (callback.ROOT / "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/AndroidCameraRestorationTest.kt").read_text()
        helpers = [
            ("    private fun assertDelayedControl(", "\n    private fun clientTaskSnapshots", restoration),
            ("    private fun clientTaskSnapshots()", "\n    private fun tasks(nonce:", restoration),
            ("    private fun delayedIntent()", "\n    private fun assertDelayedRecipient", restoration),
            ("    private fun assertDelayedRecipient(", "\n    private fun outputs()", restoration),
            ("    private fun outputs()", "\n    private fun outputFor", restoration),
            ("    private fun outputFor(", "\n    private fun Map<String, Any>.integer", restoration),
            ("    private fun <T> onMain(", "\n}", original.decode()),
        ]
        for start, end, owner in helpers:
            fragment = owner[owner.index(start):owner.index(end, owner.index(start))].strip()
            self.assertEqual(1, native.count(fragment))
        for token in ("assertEquals(35, Build.VERSION.SDK_INT)", 'getString("nativecmpkitOwnedCameraReceiver")',
                      "activity.resultCallback = callbackA", "activity.resultCallback = callbackB", "for (tick in 2..5)",
                      "awaitAppliedCallback(activity, callbackB, 2)", "assertSame(publicOwner, activity.launcher)",
                      "Intent.FLAG_ACTIVITY_REORDER_TO_FRONT", "currentScenario.onActivity { assertSame(activity, it)",
                      "capture?.let { assertEquals(it, joined) }", "cleared.getString(\"generation\")", "cleared.getInt(\"pid\")",
                      "ownerReceiver.complete(held.packet, cancel = false)", "owner.complete(joined.packet, cancel = true)",
                      "assertEquals(held.uri, captured.file.uri)", "assertTrue(delivery.second", "deliveredB.size <= 1",
                      "primary.addSuppressed(failure)", "check(externalTerminated)", "check(tasksGone && externalTerminated)",
                      "task.finishAndRemoveTask()", "finally { root.recycle() }"):
            self.assertIn(token, native)
        self.assertEqual(1, native.count("publicOwner.launch()"))
        self.assertLess(native.index("awaitAppliedCallback(activity, callbackB, 2)"), native.index("ownerReceiver.complete(held.packet"))
        self.assertLess(native.index("owner.restoreDelayed(lease)"), native.index("cleanup { receiver?.close() }"))
        for forbidden in ("grantUriPermission(", "handleResult(", "dispatchResult(", "setAlwaysFinish(",
                          "force-stop", "killProcess(", "recreate()", "received(activity.packet)", "complete(activity.packet"):
            self.assertNotIn(forbidden, native)

    def test_exact_api35_one_method_profile_requires_explicit_receiver_and_delayed_focus(self):
        row, = workflow.matrix(callback.PROFILE)["include"]
        self.assertEqual(("android-device-api35", "android-device", "35", callback.MODULE, callback.FOCUS),
                         tuple(row[key] for key in ("slot", "suite", "emulator-api", "test-modules", "test-focus")))
        self.assertNotIn("serial-emulator-api", row)
        plan = self.plan(); self.assertTrue(library.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(callback.CLASS + "#" + callback.METHOD, item["test_filter"])
        self.assertEqual(callback.identities(), item["required_testcases"])
        self.assertEqual(sorted(callback.TEST_SOURCES), item["test_source_files"])
        self.assertEqual(callback.TEST_SOURCE_SETS, item["test_source_sets"])
        self.assertEqual(35, item[callback.CONTRACT_KEY]["verification_api_level"])
        self.assertEqual(callback.DELAYED_COMPONENT, item[callback.CONTRACT_KEY]["delayed_component"])
        self.assertFalse(item[callback.CONTRACT_KEY]["compiler_or_native_success_inferred"])
        command = library.gradle_command("android-device", plan, android_serial="emulator-5588")
        self.assertEqual(callback.TASK, command[-1]); self.assertNotIn("--tests", command)
        self.assertEqual(1, command.count("-P" + callback.GRADLE_PROPERTY + "=" + callback.FOCUS))
        for token in ("-Pandroid.testInstrumentationRunnerArguments.class=" + callback.CLASS + "#" + callback.METHOD,
                      "-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedCameraReceiver=true",
                      "-Pandroid.testInstrumentationRunnerArguments.timeout_msec=120000",
                      "-PnativecmpkitAndroidDeviceSerial=emulator-5588"):
            self.assertEqual(1, command.count(token))
        self.assertFalse(any("," in token or "notAnnotation=" in token or "annotation=" in token
                             for token in command if token.startswith("-Pandroid.testInstrumentationRunnerArguments.")))
        assembly = library.gradle_command("android-device", plan, android_serial="emulator-5588", for_assembly=True)
        self.assertEqual(callback.PROJECT + ":assembleAndroidDeviceTest", assembly[-1]); self.assertNotIn(callback.TASK, assembly)
        for serial in (None, "personal-device", "emulator-5589", "emulator-5700"):
            with self.assertRaises(ValueError): library.gradle_command("android-device", plan, android_serial=serial)
        mutations = [
            ("test_filter", callback.CLASS), ("test_filter", callback.CLASS + "#" + callback.METHOD + ",Foreign#method"),
            ("required_testcases", library.android_camera_provider_identities()), ("test_exclusion_annotation", "skip.Foreign"),
            ("test_filter_argument", "annotation"), ("task", callback.PROJECT + ":testAndroidHostTest"),
            ("required_original_xml", True), ("test_source_files", [callback.SOURCE]),
            ("report_directory", callback.DECLARED_XML_DIRECTORY), ("utp_results_directory", "other/build/results"),
        ]
        for field, value in mutations:
            changed = deepcopy(plan); changed["expected"][0][field] = value
            with self.assertRaises(ValueError): library.validate_test_focus(changed)
        for field, value in (("schema_version", True), ("source_policy_verified", 1),
                             ("compiler_or_native_success_inferred", 0), ("delayed_opt_in", "unfiltered-default")):
            contract = deepcopy(item[callback.CONTRACT_KEY]); contract[field] = value
            with self.assertRaises(ValueError): callback.validate_source_contract(contract)
        cli = workflow.preflight_plans(callback.PROFILE)
        self.assertEqual(1, len(cli["slots"])); self.assertTrue(cli["source_only"])
        self.assertEqual(0, cli["Gradle_builds_executed"]); self.assertEqual(0, cli["slots"][0]["exit_code"])

    def test_unfiltered_wrong_api_and_foreign_contract_refuse_before_host_output_or_source_pruning(self):
        for modules in (None, (), (callback.MODULE,)):
            with patch.object(library, "projects") as projects, patch.object(library, "source_files") as sources:
                with self.assertRaises(ValueError): library.plan(library.ROOT, "android-device", only_modules=modules)
                projects.assert_not_called(); sources.assert_not_called()
        with tempfile.TemporaryDirectory(prefix="synthetic-callback-refusal-") as directory:
            root = Path(directory)
            invalid = [(35, None, None), (35, (callback.MODULE,), None), (23, (callback.MODULE,), callback.FOCUS),
                       (34, (callback.MODULE,), callback.FOCUS), (True, (callback.MODULE,), callback.FOCUS),
                       (35, None, callback.FOCUS), (35, (callback.MODULE, "calf-io"), callback.FOCUS),
                       (35, ("calf-io",), callback.FOCUS)]
            for api, modules, focus in invalid:
                with patch.object(device, "require_host") as host, patch.object(device, "_run") as native:
                    with self.assertRaises(ValueError):
                        device.run(root, "build/ci-verification/refused", only_modules=modules, focus=focus, api_level=api)
                    host.assert_not_called(); native.assert_not_called()
                self.assertFalse((root / "build").exists())
            with patch.object(library.runtime_context, "capture") as host:
                with self.assertRaises(ValueError): library.run(root, "android-device", "build/ci-verification/refused", None, 1, 8192)
                host.assert_not_called()
            self.assertFalse((root / "build").exists())
        device.validate_api_selection(23, (callback.MODULE,), library.ANDROID_CAMERA_PROVIDER_FOCUS)
        device.validate_api_selection(35, (callback.MODULE,), library.ANDROID_CAMERA_DONT_KEEP_FOCUS)
        device.validate_api_selection(35, ("calf-io",), None)
        plan = self.plan()
        changed = deepcopy(plan); changed["explicit_test_focus"] = library.ANDROID_CAMERA_PROVIDER_FOCUS
        with self.assertRaises(ValueError): library.validate_test_focus(changed)
        changed = deepcopy(plan); changed["expected"][0][library.camera_ios.CONTRACT_KEY] = {}
        with self.assertRaises(ValueError): library.validate_test_focus(changed)
        changed = deepcopy(plan); changed["expected"][0][library.content_policy.CONTRACT_FIELD] = {}
        with self.assertRaises(ValueError): library.validate_test_focus(changed)
        init = (callback.ROOT / "scripts/ci/fresh-tests.init.gradle.kts").read_text()
        for token in ('check((callbackFocus != null) == callbackSelected)', 'requestedSelectors == mapOf("class" to callbackSelector)',
                      'runnerArguments["nativecmpkitOwnedCameraReceiver"] == "true"',
                      'providers.environmentVariable("ANDROID_SERIAL").orNull == identifier', 'outputs.upToDateWhen { false }'):
            self.assertIn(token, init)
        library_job = (callback.ROOT / ".github/workflows/gradle.yml").read_text().split("  library-tests:\n", 1)[1]
        admission = library_job.index("Admit finite Android discovery before host setup")
        for host_step in ("actions/setup-java@", "Install the exact compiler", "Provision SDK", "Record actual architecture"):
            self.assertLess(admission, library_job.index(host_step))
        self.assertIn('scripts/ci/android_device_tests.py "${args[@]}" > /dev/null', library_job)

    def test_only_complete_declared_non_camera_fixture_minimum_admits_source_discovery_never_default_or_deleted_camera(self):
        self.assertTrue(callback.validate_current_sources(callback.ROOT))
        relative = "scripts/ci/library_tests.py"
        raw = (callback.ROOT / relative).read_bytes()
        restored = callback.current_source_before_callback672(relative, raw)
        self.assertEqual(callback._document()["bindings"][relative]["before_sha256"], callback.sha(restored))
        self.assertEqual(restored, callback.source_before_callback672(relative, restored))
        with self.assertRaises(ValueError): callback.current_source_before_callback672(relative, restored)
        with tempfile.TemporaryDirectory(prefix="synthetic-callback-declarations-") as directory:
            root = Path(directory)
            def write(relative, text):
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
                return path
            def includes(*modules):
                write("settings.gradle.kts", "include(\n" + "".join('    ":' + module + '",\n' for module in modules) + ")\n")
            includes("calf-fixture", "calf-empty")
            write("calf-fixture/build.gradle.kts", "// synthetic build declaration\n")
            write("calf-empty/build.gradle.kts", "// synthetic uncovered declaration\n")
            write("calf-fixture/src/commonTest/kotlin/Common.kt", "// synthetic common input, not native evidence\n")
            host_source = write("calf-fixture/src/androidDeviceTest/kotlin/Device.kt", "// synthetic authored device-host input, not execution\n")
            with patch.object(library, "projects", wraps=library.projects) as declarations:
                source_plan = library.plan(root, "android-device", minimum_modules=("calf-fixture",))
                declarations.assert_called_once_with(root)
            self.assertEqual(["calf-fixture"], [item["module"] for item in source_plan["expected"]])
            self.assertEqual(["commonTest", "androidDeviceTest"], source_plan["expected"][0]["test_source_sets"])
            self.assertEqual({"calf-empty"}, {item["module"] for item in source_plan["uncovered"]})
            self.assertNotIn(callback.SOURCE, source_plan["expected"][0]["test_source_files"])
            self.assertFalse((root / "build").exists())
            host_source.unlink()
            with self.assertRaises(ValueError): library.plan(root, "android-device", minimum_modules=("calf-fixture",))
            host_source.write_text("// restored synthetic device input\n")
            for minimum in (None, (), ("calf-missing",), ("calf-fixture", "calf-fixture"),
                            (callback.MODULE,), ["calf-fixture"]):
                with self.subTest(minimum=minimum), patch.object(library, "source_files") as sources:
                    with self.assertRaises(ValueError): library.plan(root, "android-device", minimum_modules=minimum)
                    sources.assert_not_called()
            for declared in (None, (), ["calf-fixture"], ("calf-fixture", "calf-fixture"), ("calf-fixture", object())):
                with self.assertRaises(ValueError):
                    callback.validate_discovery("android-device", None, None, library.ANDROID_CAMERA_FOCUSES,
                                                declared_modules=declared, minimum_modules=("calf-fixture",))
            includes("calf-fixture", "calf-empty", callback.MODULE)
            camera_build = write(callback.MODULE + "/build.gradle.kts", "// synthetic declared Camera with no callback class\n")
            self.assertFalse((root / callback.SOURCE).exists())
            with patch.object(library, "source_files") as sources:
                with self.assertRaises(ValueError): library.plan(root, "android-device", minimum_modules=("calf-fixture",))
                sources.assert_not_called()
            subset = library.plan(root, "android-device", only_modules=("calf-fixture",))
            self.assertFalse(subset["complete_suite_requested"])
            self.assertEqual(["calf-fixture"], subset["explicit_module_subset"])
            self.assertEqual(["calf-fixture"], [item["module"] for item in subset["expected"]])
            camera_build.unlink()
            with patch.object(library, "source_files") as sources:
                with self.assertRaisesRegex(ValueError, "Included library build file is missing"):
                    library.plan(root, "android-device", minimum_modules=("calf-fixture",))
                sources.assert_not_called()
            includes("calf-fixture", "calf-empty")  # Deleting Camera declaration never admits the actual/default minimum.
            with patch.object(library, "source_files") as sources:
                with self.assertRaises(ValueError): library.plan(root, "android-device")
                sources.assert_not_called()
            for settings in ('include(\n    libraryProjects.map { it.name }\n)\n',
                             'include(\n    ":calf-fixture",\n    ":calf-fixture",\n)\n'):
                write("settings.gradle.kts", settings)
                with patch.object(library, "source_files") as sources:
                    with self.assertRaises(ValueError): library.plan(root, "android-device", minimum_modules=("calf-fixture",))
                    sources.assert_not_called()
            for api in (23, 35):
                with self.assertRaises(ValueError): device.validate_api_selection(api, None, None)
            self.assertFalse((root / "build").exists())

    def test_one_fresh_callback_xml_task_and_context_reject_missing_duplicate_skip_failure_stale_or_old_substitution(self):
        plan = self.plan(); item, = plan["expected"]
        positive_context = {"source_tree_dirty": False, "source_revision": "a" * 40,
                            "host": {"system": "Linux", "architecture": "x64"},
                            "android_emulator": {"serial": "emulator-5588", "api_level": "35", "abi": "x86_64",
                                                 "boot_completed": "1", "selinux": "Enforcing"}}
        self.assertTrue(callback.validate_context(positive_context, "emulator-5588"))
        for category, key, value in (("android_emulator", "api_level", "23"), ("android_emulator", "api_level", 35),
                                     ("android_emulator", "serial", "emulator-5554"), ("android_emulator", "selinux", "Permissive"),
                                     ("android_emulator", "boot_completed", "0"), ("host", "system", "Darwin")):
            changed = deepcopy(positive_context); changed[category][key] = value
            with self.assertRaises(ValueError): callback.validate_context(changed, "emulator-5588")
        with tempfile.TemporaryDirectory(prefix="synthetic-callback-xml-") as directory:
            root = Path(directory); report = root / item["report_directory"] / "TEST-synthetic-callback.xml"
            report.parent.mkdir(parents=True)
            required = [{**case, "status": "passed"} for case in callback.identities()]
            def write(cases):
                suite = ET.Element("testsuite")
                for case in cases:
                    child = ET.SubElement(suite, "testcase", classname=case["classname"], name=case["name"])
                    if case["status"] != "passed": ET.SubElement(child, {"failed": "failure", "skipped": "skipped", "error": "error"}[case["status"]])
                ET.SubElement(suite, "system-out").text = "synthetic-console-not-native"
                report.write_bytes(ET.tostring(suite))
            variants = [required, [], required * 2, [{**required[0], "status": "failed"}], [{**required[0], "status": "skipped"}],
                        [{**required[0], "status": "error"}], [{**library.android_camera_provider_identities()[0], "status": "passed"}],
                        [{**library.android_camera_restoration_identities()[0], "status": "passed"}],
                        required + [{**library.android_camera_provider_identities()[0], "status": "passed"}]]
            for index, cases in enumerate(variants):
                write(cases); now = time.time_ns()
                observed = library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({callback.TASK: 1}), host_system="Linux")
                self.assertEqual(index != 0, bool(observed["errors"]))
            write(required); now = time.time_ns()
            for markers in (Counter(), Counter({callback.TASK: 2})):
                self.assertTrue(library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, markers, host_system="Linux")["errors"])
            self.assertTrue(library.collect_reports(root, plan, now + 10_000_000_000, now + 11_000_000_000, Counter({callback.TASK: 1}), host_system="Linux")["errors"])
            self.assertTrue(library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({callback.TASK: 1}), host_system="Darwin")["errors"])
            empty = report.with_name("TEST-synthetic-extra-empty.xml"); empty.write_text("<testsuite/>")
            self.assertTrue(library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000, Counter({callback.TASK: 1}), host_system="Linux")["errors"])
            empty.unlink()
            write([{**required[0], "status": "failed"}]); cases = library.junit_cases(report.read_bytes())
            output = root / "build/ci-verification/synthetic-failed-callback"; output.mkdir(parents=True)
            receipt = {"suite": "android-device", "explicit_test_focus": callback.FOCUS, "source_tree_dirty": False,
                       "source_revision": "a" * 40, "source_revision_after": "a" * 40, "changed_inputs": [], "passed": False,
                       "task_execution_markers": {callback.TASK: 1}, "totals": library.case_counts(cases),
                       "modules": [{"module": callback.MODULE, "testcases": cases,
                                    "reports": [{"path": report.relative_to(root).as_posix(), "sha256": library.sha256(report)}]}]}
            archived = receiver.archive_focused_reports(root, output, receipt, plan)
            self.assertFalse(archived["original_passed"]); self.assertFalse(archived["native_success_inferred_from_archival"])
            self.assertEqual("failed", archived["actual_testcases"][0]["status"])


if __name__ == "__main__":
    unittest.main()
