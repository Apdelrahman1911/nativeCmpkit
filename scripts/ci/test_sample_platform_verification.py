"""Sample-specific verification contracts, never library or device substitutes."""
import hashlib
import json
import ast
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import subprocess
import sys
import xml.etree.ElementTree as ET

import library_tests as libraries
import workflow_matrix as libraries_matrix

ROOT = Path(__file__).resolve().parents[2]
CODEC = "sample/common/src/nonAndroidTest/kotlin/com/mohamedrejeb/calf/sample/utils/SampleImageCodecTest.kt"


class SamplePlatformVerificationTests(unittest.TestCase):
    def _built_target_fixture(self, root, *, missing_wasm=False,
                              jvm_output="sample/desktop/build/libs/sample-jvm.jar"):
        import sample_platform_verification as sample
        paths = {"android": "sample/android/build/outputs/apk/debug/app-debug.apk",
                 "jvm": jvm_output,
                 "js": "sample/web-js/build/dist/js/productionExecutable/web.js",
                 "wasm": "sample/web-wasm/build/dist/wasmJs/productionExecutable/web.js"}
        for target, relative in paths.items():
            if target == "wasm" and missing_wasm:
                continue
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("synthetic-output-" + target).encode())
        output = root / "build/ci-verification/sample-platforms-linux"
        output.mkdir(parents=True)
        for index, task in enumerate(sample.BUILD_TASKS["linux"]):
            failed = missing_wasm and task == ":sample:web-wasm:wasmJsBrowserProductionWebpack"
            if missing_wasm and task == ":sample:web-wasm:wasmJsBrowserDistribution":
                continue
            archive = {"archive_file": jvm_output} if task == ":sample:desktop:jvmJar" else {}
            (output / f"task-build-{index}.json").write_text(json.dumps({
                "schema_version": 1, "task": task, "executed": True, "failed": failed,
                "skipped": False, "skip_message": None, "up_to_date": False, "no_source": False,
                "observed_epoch_ms": 1, "test_success_inferred": False, **archive}))

    def test_versioned_jvm_output_is_bound_to_the_actual_archive_task_not_a_guessed_suffix(self):
        import sample_platform_verification as sample
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = "sample/desktop/build/libs/desktop-jvm-0.1.0-SNAPSHOT.jar"
            self._built_target_fixture(root, jvm_output=relative)
            # A neighbouring source/old archive is not the jvmJar producer's output.
            (root / "sample/desktop/build/libs/old-jvm.jar").write_bytes(b"not the producer")
            result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
            self.assertTrue(result["targets"]["jvm"]["passed"])
            self.assertEqual(relative, result["targets"]["jvm"]["output"]["path"])
            self.assertEqual(hashlib.sha256((root / relative).read_bytes()).hexdigest(),
                             result["targets"]["jvm"]["output"]["sha256"])

    def test_missing_foreign_or_aliased_archive_property_never_selects_a_neighbouring_jar(self):
        import sample_platform_verification as sample
        for mutation in (None, True, "../foreign.jar", "foreign/producer.jar",
                         "sample/desktop/build/libs/missing.jar", "sample/desktop/build/libs/not-a-jar.txt"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._built_target_fixture(root)
                path = root / "build/ci-verification/sample-platforms-linux/task-build-1.json"
                row = json.loads(path.read_text())
                row["archive_file"] = mutation
                path.write_text(json.dumps(row))
                result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
                self.assertFalse(result["targets"]["jvm"]["passed"])
                self.assertIsNone(result["targets"]["jvm"]["output"])
                self.assertTrue(all(result["targets"][other]["passed"] for other in ("android", "js", "wasm")))
        source = (ROOT / "scripts/ci/sample-platforms.init.gradle.kts").read_text()
        self.assertIn("(task as AbstractArchiveTask).archiveFile.get().asFile", source)
        self.assertIn('mapOf("archive_file"', source)

    def test_declared_archive_symlink_or_hardlink_cannot_certify_the_task_output(self):
        import os
        import sample_platform_verification as sample
        for link in ("symlink", "hardlink"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._built_target_fixture(root)
                path = root / "sample/desktop/build/libs/sample-jvm.jar"
                original = root / "unrelated.bin"
                path.rename(original)
                if link == "symlink":
                    path.symlink_to(original)
                else:
                    os.link(original, path)
                result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
                self.assertFalse(result["targets"]["jvm"]["passed"])

    def test_missing_wasm_does_not_erase_three_independent_target_outputs_or_task_results(self):
        import sample_platform_verification as sample
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._built_target_fixture(root, missing_wasm=True)
            result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
            self.assertEqual({"android", "jvm", "js", "wasm"}, set(result["targets"]))
            self.assertTrue(all(result["targets"][name]["passed"] for name in ("android", "jvm", "js")))
            self.assertFalse(result["targets"]["wasm"]["passed"])
            self.assertTrue(result["errors"])
            self.assertTrue(all(result["targets"][name]["output"]["sha256"] for name in ("android", "jvm", "js")))
            self.assertTrue(result["targets"]["wasm"]["tasks"][0]["failed"])

    def test_file_alone_cannot_substitute_for_missing_failed_skipped_foreign_or_stale_task_evidence(self):
        import sample_platform_verification as sample
        for mutation in ("missing", "failed", "skipped", "foreign", "stale", "no-source", "duplicate"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._built_target_fixture(root)
                path = root / "build/ci-verification/sample-platforms-linux/task-build-0.json"
                data = json.loads(path.read_text())
                if mutation == "missing":
                    path.unlink()
                else:
                    changes = {"failed": {"failed": True}, "skipped": {"skipped": True, "skip_message": "SKIPPED"},
                               "foreign": {"task": ":foreign:assembleDebug"}, "stale": {"observed_epoch_ms": 0},
                               "no-source": {"no_source": True}, "duplicate": {"executed": "true"}}
                    path.write_text(json.dumps({**data, **changes[mutation]}))
                result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
                self.assertFalse(result["targets"]["android"]["passed"])
                self.assertTrue(result["errors"])
                self.assertTrue(all(result["targets"][name]["passed"] for name in ("jvm", "js", "wasm")))

    def test_actual_up_to_date_and_cache_task_states_require_real_output_but_are_not_fresh_tests(self):
        import sample_platform_verification as sample
        for skip in ("UP-TO-DATE", "FROM-CACHE"):
            with self.subTest(skip=skip), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self._built_target_fixture(root)
                path = root / "build/ci-verification/sample-platforms-linux/task-build-0.json"
                data = json.loads(path.read_text())
                path.write_text(json.dumps({**data, "skipped": True, "skip_message": skip,
                                           "up_to_date": skip == "UP-TO-DATE"}))
                result = sample.build_outputs(root, {"mode": "linux"}, started_ns=1_000_000, ended_ns=2_000_000)
                self.assertEqual([], result["errors"])
                self.assertTrue(result["targets"]["android"]["passed"])
                self.assertFalse(result["targets"]["android"]["tasks"][0]["test_success_inferred"])

    def _sample_run_fixture(self, root, *, parser_error=False, build_only=False, observer_error=None):
        """Synthetic process/runtime only; use the REAL report parser/policy.

        This checks the orchestration boundary that the source-only guards
        missed. It is not execution of a Gradle/native/sample test method.
        """
        import sample_platform_verification as sample
        source = root / "sample/common/src/commonTest/kotlin/T.kt"
        source.parent.mkdir(parents=True)
        source.write_text("package example\nclass T { @Test fun actual() {} }\n")
        context = {"source_revision": "1" * 40, "source_tree_dirty": False,
                   "host": {"system": "Linux"}}

        def execute(unused_root, command, log_path, timeout, reserve_mib):
            log = []
            for item in sample.plan(root, "linux")["tests"]:
                if item["task"] not in command:
                    continue
                task_name = libraries.SUITES[item["suite"]][0]
                suite = ET.Element("testsuite", tests="1", failures="0", errors="0", skipped="0")
                classname, name = "example.T", "actual"
                if item["suite"] in {"js", "wasm"}:
                    classname = task_name + "." + classname
                    target = "js" if item["suite"] == "js" else "wasmJs"
                    name += f"[{target}, browser, ChromeHeadless156.0.0.0, Linux0.0.0]"
                ET.SubElement(suite, "testcase", classname=classname, name=name, time="0.1")
                folder = root / item["report_directory"]
                folder.mkdir(parents=True)
                (folder / "TEST-example.T.xml").write_bytes(ET.tostring(suite))
                log.append("NATIVECMPKIT_TEST_RUNTIME task=" + item["task"] + " gradle=9.7.1")
            log_path.write_text("\n".join(log))
            return {"exit_code": 0, "elapsed_seconds": 0.01}

        with mock.patch.object(sample, "inputs", return_value={"fixture": "0" * 64}), \
             mock.patch.object(sample.runtime_context, "capture", return_value=context), \
             mock.patch.object(libraries, "execute", side_effect=execute), \
             mock.patch.object(libraries, "git_revision", return_value=context["source_revision"]), \
             mock.patch.object(sample.daemon_jvm, "observation", return_value={"major": 17},
                               side_effect=ValueError("synthetic refusal") if observer_error == "gradle_daemon" else None), \
             mock.patch.object(sample, "inspect_graph", return_value={"synthetic": True},
                               side_effect=ValueError("synthetic refusal") if observer_error == "compile_dependency_graph" else None), \
             mock.patch.object(sample, "build_outputs", return_value={"synthetic": True, "errors": []}), \
             mock.patch.object(sample, "inspect_web_node_environments", return_value={"synthetic": True},
                               side_effect=ValueError("synthetic refusal") if observer_error == "web_node_environments" else None):
            if parser_error:
                with mock.patch.object(libraries, "collect_reports", side_effect=ValueError("synthetic parser refusal")):
                    return sample.run(root, "linux", None, 1)
            if build_only:
                return sample.run(root, "linux", None, 1, build_only=True)
            return sample.run(root, "linux", None, 1)

    def test_observer_failure_preserves_every_other_observation_process_and_final_inputs(self):
        for key in ("gradle_daemon", "compile_dependency_graph", "web_node_environments"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                receipt = self._sample_run_fixture(root, build_only=True, observer_error=key)
                self.assertFalse(receipt["passed"])
                self.assertNotIn(key, receipt)
                self.assertEqual([key], [error["observer"] for error in receipt["errors"]])
                self.assertIn("actual_built_outputs", receipt)
                for other in {"gradle_daemon", "compile_dependency_graph", "web_node_environments"} - {key}:
                    self.assertIn(other, receipt)
                self.assertEqual(0, receipt["execution"]["exit_code"])
                self.assertEqual(receipt["inputs_before_sha256"], receipt["inputs_after_sha256"])
                self.assertTrue((root / "build/ci-verification/sample-platforms-linux/execution.json").is_file())
                self.assertFalse((root / "build/ci-verification/.library-tests.lock").exists())

    def test_actual_shared_collector_policy_accepts_the_owning_exact_sample_boundary(self):
        # Real40963671526 passed16+17+17 cases, then its owning collector
        # illegally passed required_testcases to the library's unfiltered policy.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self._sample_run_fixture(root)
            self.assertTrue(receipt["passed"])
            self.assertEqual(3, sum(item["passed"] for item in receipt["sample_suites"]))
            self.assertEqual([], receipt["errors"])
            self.assertTrue((root / "build/ci-verification/sample-platforms-linux/inputs-after.json").is_file())
            self.assertFalse((root / "build/ci-verification/.library-tests.lock").exists())

    def test_report_parser_refusal_keeps_a_failed_receipt_after_inputs_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self._sample_run_fixture(root, parser_error=True)
            self.assertFalse(receipt["passed"])
            self.assertEqual(0, sum(item["passed"] for item in receipt["sample_suites"]))
            self.assertTrue(any(error.get("reason") == "ValueError" for error in receipt["errors"]))
            self.assertEqual(receipt["inputs_before_sha256"], receipt["inputs_after_sha256"])
            self.assertTrue((root / "build/ci-verification/sample-platforms-linux/receipt.json").is_file())
            self.assertTrue((root / "build/ci-verification/sample-platforms-linux/execution.json").is_file())
            self.assertFalse((root / "build/ci-verification/.library-tests.lock").exists())

    def test_sample_adapter_preserves_library_filter_rejection_and_owning_exact_selection(self):
        import sample_platform_verification as sample
        item = sample.plan(ROOT, "linux")["tests"][0]
        with self.assertRaises(ValueError):
            libraries.validate_test_focus({"explicit_test_focus": None, "expected": [item]})
        mutated = {**item, "required_testcases": item["required_testcases"][:-1]}
        with mock.patch.object(libraries, "collect_reports", side_effect=AssertionError("must refuse before parsing")):
            with self.assertRaises(ValueError):
                sample.collect_sample_reports(ROOT, mutated, 0, 1, {}, "Linux")

    def test_build_only_recovery_has_zero_test_replay_and_retains_every_actual_app_build(self):
        import sample_platform_verification as sample
        for mode in ("linux", "apple"):
            full = sample.plan(ROOT, mode)
            recovery = sample.plan(ROOT, mode, build_only=True)
            self.assertEqual(full["build_tasks"], recovery["build_tasks"])
            self.assertEqual(full["dependency_task"], recovery["dependency_task"])
            self.assertEqual([], recovery["tests"])
            self.assertTrue(recovery["build_only"])
            self.assertFalse(recovery["library_verification"])
            self.assertFalse(recovery["release_readiness_certified"])
            device = "11111111-1111-1111-1111-111111111111" if mode == "apple" else None
            command = sample.gradle_command(ROOT, recovery, device)
            self.assertNotIn("--tests", command)
            self.assertFalse(any(task.endswith("Test") for task in command))
            row, = sample.workflow_matrix("sample-builds-" + mode)["include"]
            self.assertTrue(row["build_only"])
            self.assertEqual([], libraries_matrix.matrix("sample-builds-" + mode)["include"])
        self.assertEqual(11, len(libraries_matrix.matrix("all")["include"]))
        with tempfile.TemporaryDirectory() as tmp:
            receipt = self._sample_run_fixture(Path(tmp), build_only=True)
            self.assertTrue(receipt["passed"])
            self.assertEqual([], receipt["sample_suites"])
            self.assertEqual({}, receipt["task_execution_markers"])
            self.assertTrue(receipt["build_only"])

    def test_fixed_build_only_cli_and_workflow_preflight_propagate_the_same_explicit_scope(self):
        text = (ROOT / ".github/workflows/gradle.yml").read_text()
        call = text.split("sample_plan = ", 1)[1].split("\n", 1)[0]
        node = ast.parse(call, mode="eval").body
        keyword, = node.keywords
        self.assertEqual("build_only", keyword.arg)
        self.assertEqual('row["build_only"]', ast.unparse(keyword.value).replace("'", '"'))
        job = text.split("\n  sample-platforms:\n", 1)[1].split("\n  library-tests:\n", 1)[0]
        self.assertIn("SAMPLE_BUILD_ONLY: ${{ matrix.build_only }}", job)
        self.assertIn('if [[ "$SAMPLE_BUILD_ONLY" == true ]]; then args+=(--build-only); fi', job)
        for mode in ("linux", "apple"):
            result = subprocess.run([sys.executable, "-B", "scripts/ci/sample_platform_verification.py",
                                     "plan", "--mode", mode, "--build-only"],
                                    cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            import json
            selected = json.loads(result.stdout)
            self.assertTrue(selected["build_only"])
            self.assertEqual([], selected["tests"])

    def test_actual_workflow_preflight_passes_the_sample_helpers_existing_root(self):
        import sample_platform_verification as sample
        text = (ROOT / ".github/workflows/gradle.yml").read_text()
        call = text.split("sample_plan = ", 1)[1].split("\n", 1)[0]
        node = ast.parse(call, mode="eval").body
        self.assertEqual("sample_platform_verification", node.func.value.id)
        self.assertEqual("plan", node.func.attr)
        self.assertIsInstance(node.args[0], ast.Attribute)
        self.assertEqual("ROOT", node.args[0].attr)
        owners = {"sample_platform_verification": sample, "workflow_matrix": libraries_matrix}
        owner = owners[node.args[0].value.id]
        self.assertEqual(ROOT, getattr(owner, node.args[0].attr))
        for row in sample.workflow_matrix("sample-platforms-linux")["include"]:
            self.assertEqual("linux", sample.plan(getattr(owner, node.args[0].attr), row["mode"])["mode"])

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
                    actual = [{**c, "classname": libraries.SUITES[suite][0] + "." + c["classname"],
                               "name": c["name"] + "[iosSimulatorArm64]"} for c in cases]
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

    def test_native_identity_has_the_actual_kgp_task_prefix_instead_of_a_flat_fixture_class(self):
        import sample_platform_verification as sample
        item = sample.plan(ROOT, "apple")["tests"][0]
        # The independently collected real KGP Native XML uses this task prefix
        # (see permission-ios-important-20261028/fixed001-attempt2/reports), not
        # merely a target suffix on a synthetic JVM-style class name.
        actual = [{"classname": libraries.SUITES["ios"][0] + "." + case["classname"],
                   "name": case["name"] + "[iosSimulatorArm64]", "status": "passed"}
                  for case in item["required_testcases"]]
        self.assertTrue(sample.exact_case_inventory(item, actual, require_runtime_suffix=True))
        self.assertFalse(sample.exact_case_inventory(item,
            [{**case, "classname": case["classname"].removeprefix("iosSimulatorArm64Test.")} for case in actual],
            require_runtime_suffix=True))

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

    def test_failed_shared_sample_build_captures_bounded_diagnostics_before_reports_upload(self):
        text = (ROOT / ".github/workflows/gradle.yml").read_text()
        job = text.split("\n  sample-platforms:\n", 1)[1].split("\n  library-tests:\n", 1)[0]
        capture = job.split("- name: Bounded owning sample failure diagnostics", 1)[1].split("- name: Keep sample receipts", 1)[0]
        self.assertIn("if: failure()", capture)
        self.assertIn('output="build/ci-verification/sample-platforms-$SAMPLE_MODE"', capture)
        self.assertIn('if [[ -d "$output" ]]', capture)
        self.assertIn('scripts/ci/failure_diagnostics.py --output "$output"', capture)
        self.assertNotIn("|| true", capture)
        self.assertNotIn("cat ", capture)
        self.assertNotIn("tail ", capture)
        self.assertIn("scripts/ci/sample_platform_verification.py", job)

    def test_actual_apple_navigationevent_groups_are_distinct_from_the_removed_navigation_library(self):
        # Actual40967168162 has navigationevent (not navigation) in both Apple
        # graphs. Prefix matching falsely rejected these unrelated group IDs.
        import sample_platform_verification as sample
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gradle").mkdir()
            (root / "gradle/libs.versions.toml").write_text('[versions]\nandroid-sample-minSdk = "24"\n')
            (root / "sample/android").mkdir(parents=True)
            (root / "sample/android/build.gradle.kts").write_text(
                "minSdk = libs.versions.android.sample.minSdk.get().toInt()\n")
            (root / "sample/common/src/commonMain/kotlin").mkdir(parents=True)
            graph = {"mode": "apple", "project": ":sample:common", "sample_minSdk_lowered": False,
                     "compilations": [{"target": target, "unresolved_dependencies": 0,
                        "resolved_modules": [
                            {"group": "androidx.navigationevent", "name": "navigationevent", "version": "1.1.1"},
                            {"group": "org.jetbrains.androidx.navigationevent", "name": "navigationevent-compose", "version": "1.1.0"},
                        ]} for target in ("iosArm64", "iosSimulatorArm64")]}
            output = root / "build/ci-verification/sample-platforms-apple/compile-dependencies.json"
            output.parent.mkdir(parents=True)
            output.write_text(json.dumps(graph))
            result = sample.inspect_graph(root, "apple")
            self.assertTrue(result["unused_second_navigation_group_absent"])
            self.assertTrue(result["all_selected_compile_graphs_reviewed"])
            self.assertEqual(24, result["sample_app_declared_minSdk"])
            self.assertFalse(result["minimum_platform_certified"])
            for group in ("org.jetbrains.androidx.navigation", "androidx.navigation"):
                with self.subTest(actual_unused_navigation_group=group):
                    graph["compilations"][0]["resolved_modules"].append(
                        {"group": group, "name": "navigation-compose", "version": "2.10.0-alpha05"})
                    output.write_text(json.dumps(graph))
                    with self.assertRaisesRegex(ValueError, "Unused second navigation library"):
                        sample.inspect_graph(root, "apple")
                    graph["compilations"][0]["resolved_modules"].pop()

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
