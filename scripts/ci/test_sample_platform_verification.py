"""Sample-specific verification contracts, never library or device substitutes."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import library_tests as libraries
import workflow_matrix as libraries_matrix

ROOT = Path(__file__).resolve().parents[2]
CODEC = "sample/common/src/nonAndroidTest/kotlin/com/mohamedrejeb/calf/sample/utils/SampleImageCodecTest.kt"


class SamplePlatformVerificationTests(unittest.TestCase):
    def test_actual_codec_cases_are_shared_with_web_and_native_without_replaying_desktop(self):
        self.assertTrue((ROOT / CODEC).is_file(), "Actual codec cases must belong to nonAndroidTest, not desktop only")
        old = ROOT / CODEC.replace("nonAndroidTest", "desktopTest")
        self.assertFalse(old.exists())
        source = (ROOT / CODEC).read_text()
        self.assertEqual("08ce40901f75b935aaae8d25568c55851985b6c7d0d8858a5c18dd5eebe6391c",
                         hashlib.sha256((ROOT / CODEC).read_bytes()).hexdigest())
        self.assertEqual(4, source.count("@Test"))
        self.assertIn("input.toByteArray()", source)
        self.assertIn("circleCropSampleImage(bytes).decodeSampleImage()", source)
        hierarchy = (ROOT / "convention-plugins/src/main/kotlin/Hirearchy.kt").read_text()
        group = hierarchy.split('group("nonAndroid")', 1)[1].split('group("web")', 1)[0]
        for target in ("withJvm()", "withIos()", "withJs()", "withWasmJs()"):
            self.assertIn(target, group)

    def test_sample_profiles_cannot_narrow_any_library_or_device_matrix(self):
        import sample_platform_verification as sample
        for profile, mode in (("sample-platforms-linux", "linux"), ("sample-platforms-apple", "apple")):
            self.assertEqual([], libraries_matrix.matrix(profile)["include"])
            row, = sample.workflow_matrix(profile)["include"]
            self.assertEqual(mode, row["mode"])
        self.assertEqual(11, len(libraries_matrix.matrix("all")["include"]))
        self.assertEqual(0, sample.workflow_matrix("core")["include"].__len__())
        with self.assertRaises(ValueError): sample.plan(ROOT, "arbitrary")

    def test_actual_target_plan_builds_apps_and_frameworks_and_runs_only_unaccepted_sample_methods(self):
        import sample_platform_verification as sample
        linux, apple = sample.plan(ROOT, "linux"), sample.plan(ROOT, "apple")
        self.assertIn(":sample:android:assembleDebug", linux["build_tasks"])
        self.assertIn(":sample:desktop:jvmJar", linux["build_tasks"])
        self.assertIn(":sample:web-js:jsBrowserProductionWebpack", linux["build_tasks"])
        self.assertIn(":sample:web-js:jsBrowserDistribution", linux["build_tasks"])
        self.assertIn(":sample:web-wasm:wasmJsBrowserProductionWebpack", linux["build_tasks"])
        self.assertIn(":sample:web-wasm:wasmJsBrowserDistribution", linux["build_tasks"])
        self.assertEqual({"android-host", "js", "wasm"}, {row["suite"] for row in linux["tests"]})
        self.assertNotIn(":sample:common:desktopTest", [row["task"] for row in linux["tests"]])
        self.assertIn(":sample:common:linkDebugFrameworkIosArm64", apple["build_tasks"])
        self.assertIn(":sample:common:linkDebugFrameworkIosSimulatorArm64", apple["build_tasks"])
        self.assertEqual("ios", apple["tests"][0]["suite"])
        for plan in (linux, apple):
            self.assertFalse(plan["library_verification"])
            self.assertFalse(plan["release_readiness_certified"])
            self.assertTrue(all(row["required_testcases"] for row in plan["tests"]))

    def test_compile_test_filters_and_simulator_are_exact_and_have_no_publish_or_signing_authority(self):
        import sample_platform_verification as sample
        linux = sample.gradle_command(ROOT, sample.plan(ROOT, "linux"))
        self.assertIn("scripts/ci/fresh-tests.init.gradle.kts", linux)
        self.assertIn("scripts/ci/sample-platforms.init.gradle.kts", linux)
        self.assertIn("--max-workers=1", linux)
        self.assertNotIn("--rerun-tasks", linux)
        self.assertFalse(any("publish" in item.lower() for item in linux))
        with self.assertRaises(ValueError): sample.gradle_command(ROOT, sample.plan(ROOT, "apple"))
        command = sample.gradle_command(ROOT, sample.plan(ROOT, "apple"), "1" * 8 + "-" + "1" * 4 + "-" + "1" * 4 + "-" + "1" * 4 + "-" + "1" * 12)
        self.assertTrue(any(item.startswith("-PnativecmpkitSimulatorDevice=") for item in command))
        xcode = sample.xcode_command(ROOT, "11111111-1111-1111-1111-111111111111")
        self.assertIn("CODE_SIGNING_ALLOWED=NO", xcode)
        self.assertNotIn("-allowProvisioningUpdates", xcode)
        self.assertNotIn("archive", xcode)

    def test_fresh_expected_sample_cases_reject_missing_failed_skipped_duplicate_or_foreign_xml(self):
        import sample_platform_verification as sample
        item = sample.plan(ROOT, "linux")["tests"][0]
        cases = [{**c, "status": "passed"} for c in item["required_testcases"]]
        self.assertTrue(sample.exact_case_inventory(item, cases))
        for bad in (cases[:-1], cases + cases[:1], [{**c, "status": "skipped"} for c in cases],
                    [{**cases[0], "name": "foreign"}, *cases[1:]], [{**cases[0], "status": "failed"}, *cases[1:]]):
            with self.subTest(cases=bad): self.assertFalse(sample.exact_case_inventory(item, bad))

    def test_extra_unreviewed_source_sets_or_complex_test_declarations_cannot_disappear(self):
        import sample_platform_verification as sample
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "sample/common/src/commonTest/kotlin/T.kt"
            path.parent.mkdir(parents=True)
            path.write_text("package example\nclass T { @Test fun actual() {} }\n")
            self.assertEqual([{"classname": "example.T", "name": "actual"}], sample.source_testcases(root, "commonTest"))
            path.write_text("package example\nclass T { @Test fun `changed syntax`() {} }\n")
            with self.assertRaises(ValueError): sample.source_testcases(root, "commonTest")

    def test_runtime_case_identity_requires_actual_browser_and_native_target_suffixes(self):
        import sample_platform_verification as sample
        for mode in ("linux", "apple"):
            for item in sample.plan(ROOT, mode)["tests"]:
                cases = [{**case, "status": "passed"} for case in item["required_testcases"]]
                suite = item["suite"]
                if suite == "ios":
                    actual = [{**c, "name": c["name"] + "[iosSimulatorArm64]"} for c in cases]
                elif suite in {"js", "wasm"}:
                    target = "js" if suite == "js" else "wasmJs"
                    actual = [{**c, "classname": libraries.SUITES[suite][0] + "." + c["classname"],
                               "name": c["name"] + f"[{target}, browser, ChromeHeadless153.0.0.0, Linux0.0.0]"} for c in cases]
                else:
                    actual = cases
                self.assertTrue(sample.exact_case_inventory(item, actual, require_runtime_suffix=True))
                if suite != "android-host":
                    self.assertFalse(sample.exact_case_inventory(item, cases, require_runtime_suffix=True))
                bad = [{**actual[0], "name": actual[0]["name"] + "[foreign]"}, *actual[1:]]
                self.assertFalse(sample.exact_case_inventory(item, bad, require_runtime_suffix=True))

    def test_new_native_graphics_host_is_explicit_and_does_not_claim_physical_encoding_verification(self):
        source = (ROOT / "sample/common/src/androidHostTest/kotlin/com/mohamedrejeb/calf/sample/utils/SampleImageCodecAndroidHostTest.kt").read_text()
        self.assertIn("@GraphicsMode(GraphicsMode.Mode.NATIVE)", source)
        self.assertIn("@Config(sdk = [35], manifest = Config.NONE)", source)
        self.assertIn("assertFailsWith<IllegalStateException> { input.toByteArray() }", source)
        self.assertEqual(3, source.count("@Test"))
        self.assertGreaterEqual(source.count("isRecycled"), 4)

    def test_sample_workflow_uses_one_read_only_host_and_uploads_no_artifacts_or_cache_results(self):
        text = (ROOT / ".github/workflows/gradle.yml").read_text()
        job = text.split("\n  sample-platforms:\n", 1)[1].split("\n  library-tests:\n", 1)[0]
        self.assertIn("max-parallel: 1", job)
        self.assertIn("persist-credentials: false", job)
        self.assertNotIn("permissions:", job)
        self.assertNotIn("restore-keys:", job)
        self.assertNotIn("github.sha", job)
        self.assertIn("inputs.profile", text)
        upload = job.split("- name: Keep sample receipts", 1)[1]
        for forbidden in (".apk", ".aar", ".jar", ".app", ".klib", "Common.framework", "*.log"):
            self.assertNotIn(forbidden, upload)
        self.assertIn("scripts/ci/sample_platform_verification.py", job)

    def test_sample_init_script_ignores_inherited_builds_and_records_actual_public_compilation_graphs(self):
        source = (ROOT / "scripts/ci/sample-platforms.init.gradle.kts").read_text()
        self.assertIn("sampleRootFile.isAbsolute && sampleRootFile.isDirectory", source)
        self.assertLess(source.index("canonicalFile != sampleRoot"), source.index('rootProject.project(":sample:common")'))
        for api in ("getCompileDependencyConfigurationName", "getCompileKotlinTaskName", "incoming.resolutionResult"):
            self.assertIn(api, source)
        self.assertIn("UnresolvedDependencyResult", source)
        self.assertIn("check(!output.exists())", source)
        self.assertNotIn("PublishToMavenRepository", source)


if __name__ == "__main__":
    unittest.main()
