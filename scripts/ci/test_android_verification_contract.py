"""Synthetic CI contract regressions; none executes Android or a library API."""
from collections import Counter
import json
import unittest
from unittest.mock import patch

import library_tests as r
import runtime_context as runtime
import test_library_tests as fixtures


class AndroidVerificationContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.LibraryTestReceipts()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.fixture.write("calf-fixture/src/androidDeviceTest/kotlin/Device.kt", "// synthetic device test")
        self.fixture.write("calf-empty/src/commonTest/kotlin/Common.kt", "// common tests are not a device host")

    def plan(self):
        return r.plan(self.root, "android-device", minimum_modules=("calf-fixture",))

    def test_device_plan_requires_an_actual_authored_device_test_host(self):
        plan = self.plan()
        self.assertEqual(["calf-fixture"], [item["module"] for item in plan["expected"]])
        self.assertEqual(["commonTest", "androidDeviceTest"], plan["expected"][0]["test_source_sets"])
        self.assertEqual("calf-fixture/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest",
                         plan["expected"][0]["report_directory"])
        self.assertEqual(":calf-fixture:connectedAndroidDeviceTest", plan["expected"][0]["task"])
        self.assertIn("calf-empty", {item["module"] for item in plan["uncovered"]})

    def test_deleting_device_sources_cannot_turn_common_tests_into_native_success(self):
        (self.root / "calf-fixture/src/androidDeviceTest/kotlin/Device.kt").unlink()
        with self.assertRaises(ValueError):
            self.plan()

    def test_device_command_is_serial_bound_and_instrumentation_is_sequential(self):
        command = r.gradle_command("android-device", self.plan(), android_serial="emulator-5588")
        self.assertIn("-PnativecmpkitAndroidDeviceSerial=emulator-5588", command)
        self.assertFalse(any(arg.startswith("-Pandroid.injected.device.serial=") for arg in command))
        self.assertIn("--no-parallel", command)
        self.assertIn("--stacktrace", command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.timeout_msec=120000", command)
        self.assertEqual(1, command.count(":calf-fixture:connectedAndroidDeviceTest"))
        self.assertNotIn("--rerun-tasks", command)

    def test_repository_device_tasks_run_data_ownership_before_native_ui(self):
        plan = r.plan(r.ROOT, "android-device")
        self.assertEqual(["calf-io", "calf-file-picker", "calf-webview"],
                         [item["module"] for item in plan["expected"]])

    def test_missing_physical_or_injected_serials_are_rejected_before_execution(self):
        for serial in (None, "", "personal-phone", "emulator-5588 --info", "emulator-5588;echo", "emulator-5589"):
            with self.subTest(serial=serial), self.assertRaises(ValueError):
                r.gradle_command("android-device", self.plan(), android_serial=serial)
        with self.assertRaises(ValueError):
            r.gradle_command("desktop", self.fixture.plan(), android_serial="emulator-5588")

    def test_host_xml_cannot_satisfy_missing_native_report_and_marker(self):
        self.fixture.write("calf-fixture/build/test-results/testAndroidHostTest/TEST-host.xml", self.fixture.report())
        result = self.fixture.collect(test_plan=self.plan())
        self.assertEqual(0, result["totals"]["executed"])
        self.assertTrue(result["errors"])

    def test_utp_output_is_not_mistaken_for_actual_xml_results(self):
        self.fixture.write("calf-fixture/build/outputs/androidTest-results/connected/androidMain/TEST-wrong.xml",
                           self.fixture.report())
        result = self.fixture.collect(test_plan=self.plan())
        self.assertEqual(0, result["totals"]["executed"])
        self.assertTrue(result["errors"])

    def test_executed_agp_inspection_contract_matches_init_script_and_plan(self):
        source = (r.ROOT / "scripts/ci/fresh-tests.init.gradle.kts").read_text()
        expected = "intermediates/android_test_results/androidMain/connectedAndroidDeviceTest"
        self.assertIn(f'layout.buildDirectory.dir("{expected}")', source)
        self.assertIn('javaClass.getMethod("getXmlResultsDirectory")', source)
        self.assertIn('javaClass.getMethod("getResultsDir")', source)
        self.assertIn('layout.buildDirectory.dir("outputs/androidTest-results/connected/androidMain")', source)
        self.assertTrue(all(item["report_directory"].endswith("build/" + expected)
                            for item in self.plan()["expected"]))

    def test_init_requires_supported_environment_and_empty_agp_serial_options(self):
        source = (r.ROOT / "scripts/ci/fresh-tests.init.gradle.kts").read_text()
        self.assertIn('providers.gradleProperty("nativecmpkitAndroidDeviceSerial")', source)
        self.assertIn('providers.environmentVariable("ANDROID_SERIAL").orNull == identifier', source)
        self.assertIn('listOf("getDeviceSerialValues", "getConnectedCheckDeviceSerials")', source)
        self.assertIn('check(options.orNull.orEmpty().isEmpty())', source)
        self.assertNotIn('javaClass.getMethod("setSerialOption"', source)

    def test_environment_is_a_child_copy_without_disclosing_or_changing_the_caller(self):
        with patch.dict(r.os.environ, {"PRIVATE_FIXTURE_VALUE": "synthetic-retain-in-child"}, clear=True):
            result = r.android_device_environment("emulator-5588")
            self.assertEqual("emulator-5588", result["ANDROID_SERIAL"])
            self.assertEqual("synthetic-retain-in-child", result["PRIVATE_FIXTURE_VALUE"])
            self.assertNotIn("ANDROID_SERIAL", r.os.environ)
            result["PRIVATE_FIXTURE_VALUE"] = "child-only"
            self.assertEqual("synthetic-retain-in-child", r.os.environ["PRIVATE_FIXTURE_VALUE"])

    def test_matching_inherited_selector_is_retained_but_other_selectors_fail_closed(self):
        with patch.dict(r.os.environ, {"ANDROID_SERIAL": "emulator-5588"}, clear=True):
            self.assertEqual("emulator-5588", r.android_device_environment("emulator-5588")["ANDROID_SERIAL"])
        for selector in ("", "personal-phone", "emulator-5590", "emulator-5588,emulator-5590"):
            with self.subTest(selector=selector), patch.dict(r.os.environ, {"ANDROID_SERIAL": selector}, clear=True):
                with self.assertRaises(ValueError):
                    r.android_device_environment("emulator-5588")

    def test_conflicting_environment_is_rejected_before_any_report_or_process_mutation(self):
        output = "build/ci-verification/device-environment-conflict"
        prior = self.fixture.write(self.plan()["expected"][0]["report_directory"] + "/TEST-old.xml",
                                   self.fixture.report())
        before = prior.read_bytes()
        with patch.dict(r.os.environ, {"ANDROID_SERIAL": "emulator-5590"}, clear=True), \
                patch.object(r, "plan", return_value=self.plan()), patch.object(r, "execute") as process:
            with self.assertRaises(ValueError):
                r.run(self.root, "android-device", output, None, 60, 1024, android_serial="emulator-5588")
        process.assert_not_called()
        self.assertFalse((self.root / output).exists())
        self.assertEqual(before, prior.read_bytes())

    def test_valid_run_transports_selector_to_child_and_receipt_without_environment_dump(self):
        plan = self.plan()
        emulator = runtime.parse_android_emulator("emulator-5588", {
            "api_level": "35", "release": "15", "abi": "x86_64", "boot_completed": "1", "selinux": "Enforcing"})
        context = {"source_revision": "a" * 40, "source_tree_dirty": True,
                   "host": {"system": "Linux"}, "android_emulator": emulator}

        def execute(root, command, log_path, timeout, reserve_mib, *, env):
            self.assertEqual("emulator-5588", env["ANDROID_SERIAL"])
            self.assertEqual("synthetic-private", env["PRIVATE_FIXTURE_VALUE"])
            self.fixture.write(plan["expected"][0]["report_directory"] + "/TEST-fresh.xml", self.fixture.report())
            log_path.write_text("NATIVECMPKIT_TEST_RUNTIME task=:calf-fixture:connectedAndroidDeviceTest gradle=9.7.1 java=17\n")
            return {"exit_code": 0}

        with patch.dict(r.os.environ, {"PRIVATE_FIXTURE_VALUE": "synthetic-private"}, clear=True), \
                patch.object(r, "plan", return_value=plan), patch.object(r, "git_revision", return_value="a" * 40), \
                patch.object(r.runtime_context, "capture", return_value=context), \
                patch.object(r, "execute", side_effect=execute):
            receipt = r.run(self.root, "android-device", "build/ci-verification/device-env-valid", None,
                            60, 1024, android_serial="emulator-5588")
        self.assertTrue(receipt["passed"])
        self.assertEqual({"mechanism": "ANDROID_SERIAL", "serial": "emulator-5588",
                          "agp_target_serial_options": "empty"}, receipt["android_device_selection"])
        self.assertNotIn("synthetic-private", json.dumps(receipt))

    def test_fresh_nested_agp_reports_are_counted_without_losing_a_failure(self):
        plan = self.plan()
        directory = plan["expected"][0]["report_directory"]
        self.fixture.write(directory + "/TEST-emulator.xml", self.fixture.report())
        self.fixture.write(directory + "/nested/TEST-failed.xml", self.fixture.report("failed", '<failure message="native failure"/>'))
        result = self.fixture.collect(test_plan=plan)
        self.assertEqual(2, result["totals"]["executed"])
        self.assertEqual(1, result["totals"]["failures"])
        self.assertTrue(result["errors"])


class AndroidRuntimeIdentityTests(unittest.TestCase):
    def identity(self, **overrides):
        return {"api_level": "35", "release": "15", "abi": "x86_64", "boot_completed": "1",
                "selinux": "Enforcing", **overrides}

    def test_device_identity_is_explicit_booted_and_enforcing(self):
        result = runtime.parse_android_emulator("emulator-5588", self.identity(private="never export"))
        self.assertEqual("emulator-5588", result["serial"])
        self.assertEqual("35", result["api_level"])
        self.assertEqual("Enforcing", result["selinux"])
        self.assertNotIn("private", result)

    def test_wrong_boot_security_or_malformed_identity_cannot_make_evidence(self):
        for values in (self.identity(api_level="٣٥"), self.identity(api_level="35.0"),
                       self.identity(boot_completed="0"), self.identity(selinux="Permissive"),
                       self.identity(abi="unknown-machine"), self.identity(release="private path")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                runtime.parse_android_emulator("emulator-5588", values)

    def test_personal_device_invalid_or_odd_ports_are_not_accepted(self):
        for serial in ("phone", "emulator-0", "emulator-5589", "emulator-999999", "emulator-5588 --info"):
            with self.subTest(serial=serial), self.assertRaises(ValueError):
                runtime.parse_android_emulator(serial, self.identity())

    def test_different_native_emulator_contexts_partition_fingerprints(self):
        before = {"android_emulator": runtime.parse_android_emulator("emulator-5588", self.identity())}
        after = {"android_emulator": runtime.parse_android_emulator("emulator-5588", self.identity(api_level="37", release="17"))}
        self.assertNotEqual(runtime.compiler_runtime_fingerprint(before), runtime.compiler_runtime_fingerprint(after))


if __name__ == "__main__":
    unittest.main()
