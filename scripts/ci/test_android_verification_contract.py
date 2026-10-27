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
        self.assertIn("-Pandroid.injected.device.serial=emulator-5588", command)
        self.assertIn("--no-parallel", command)
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
