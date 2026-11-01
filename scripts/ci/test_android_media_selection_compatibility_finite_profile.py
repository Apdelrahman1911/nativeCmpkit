"""New media-only compatibility routing models; never SDK/build/native acceptance."""
import ast
import copy
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch
import android_device_batch as batch
import android_device_batch_plan as fixed
import android_device_tests as device
import library_tests as lt
import workflow_matrix as workflow

ROOT = lt.ROOT
PROFILE = "android-media-selection-compatibility"
MODULE = "calf-permissions/core"
CLASS = "com.mohamedrejeb.calf.permissions.AndroidMediaSelectionDeviceTest"
METHOD = "realPlatformMediaSelectionIsReflectedByPublicLibraryStates"
SOURCE = "calf-permissions/core/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/permissions/AndroidMediaSelectionDeviceTest.kt"
ROUTES = ("android-media-selection-api33", "android-media-selection-api34")
SDK = "cmdline-tools;23.0 platforms;android-37.0 build-tools;36.0.0 emulator system-images;android-33;google_apis;x86_64 system-images;android-34;google_apis;x86_64"
ORIGINAL_BATCHES = {'android-io-permission-storage-api35': ('android-io-reference-regressions',
                                         'android-permission-demo',
                                         'android-storage-api35-normal',
                                         'android-storage-api35-all-files'),
 'android-permission-storage-compatibility': ('android-media-selection-api33',
                                              'android-media-selection-api34',
                                              'android-storage-api28',
                                              'android-storage-api29-target28',
                                              'android-storage-api29-legacy',
                                              'android-storage-api29-scoped',
                                              'android-storage-api30-normal',
                                              'android-storage-api30-all-files'),
 'android-storage-compatibility': ('android-storage-api28',
                                   'android-storage-api29-target28',
                                   'android-storage-api29-legacy',
                                   'android-storage-api29-scoped',
                                   'android-storage-api30-normal',
                                   'android-storage-api30-all-files')}

class AndroidMediaSelectionCompatibilityFiniteProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Selected-core copied discovery only, not full root-input/native evidence.
        cls.selection = batch.plan(ROOT, PROFILE)

    def test_only_two_existing_media_routes_request_two_executions_of_one_native_method(self):
        self.assertEqual(ROUTES, fixed.BATCHES[PROFILE])
        self.assertEqual(list(ROUTES), [r["profile"] for r in self.selection["routes"]])
        self.assertEqual([33, 34], [r["api_level"] for r in self.selection["routes"]])
        self.assertEqual(2, self.selection["requested_target_executions"])
        self.assertEqual(1, self.selection["requested_distinct_methods"])
        self.assertIs(self.selection["source_only"], True)
        self.assertIs(self.selection["same_workspace_serial_only"], True)
        self.assertEqual(0, self.selection["Gradle_builds_executed"])
        self.assertEqual(0, self.selection["native_tests_executed"])
        self.assertIs(self.selection["compilation_or_native_acceptance_inferred"], False)
        for route, api in zip(self.selection["routes"], (33, 34)):
            self.assertEqual((api, MODULE, "android-media-selection"), fixed.SELECTIONS[route["profile"]])
            self.assertEqual((MODULE, "android-media-selection", "android-device-api" + str(api) + "-media"),
                (route["module"], route["focus"], route["original_slot"]))
            device.validate_api_selection(api, (MODULE,), route["focus"])
            source = route["source_suite"]
            self.assertTrue(lt.validate_test_focus(source))
            self.assertIs(source["complete_suite_requested"], False)
            self.assertEqual([MODULE], source["explicit_module_subset"])
            item, = source["expected"]
            self.assertEqual(":calf-permissions:calf-permissions-core:connectedAndroidDeviceTest", item["task"])
            self.assertEqual(MODULE + "/build/outputs/androidTest-results/connected/androidMain", item["report_directory"])
            self.assertEqual(CLASS, item["test_filter"])
            self.assertEqual([{"classname": CLASS, "name": METHOD}], item["required_testcases"])
            self.assertIn(SOURCE, item["test_source_files"])
            self.assertNotIn("android_storage_probe", source)
            self.assertNotIn("android_io_documents", source)
            self.assertIs(source["android_permission_demo"]["source_contract"]["native_or_compile_success_inferred"], False)

    def test_one_existing_host_and_all_original_batches_eleven_full_slots_survive(self):
        for name, routes in ORIGINAL_BATCHES.items():
            self.assertEqual(routes, fixed.BATCHES[name])
            self.assertIn(name, workflow.PROFILES)
        self.assertEqual(MODULE, fixed.MODULES[PROFILE])
        self.assertEqual(("android-device-api35",), workflow.PROFILES[PROFILE])
        self.assertEqual({"slot": "android-device-batch-media-compatibility", "suite": "android-device",
            "runner": "ubuntu-24.04", "arch": "x64", "python": "python3",
            "test-modules": MODULE, "android-batch": PROFILE}, workflow.matrix(PROFILE)["include"][0])
        self.assertEqual(1, len(workflow.matrix(PROFILE)["include"]))
        self.assertEqual(["desktop-linux-x64", "android-host", "browser-js", "browser-wasm", "desktop-macos-arm64",
            "ios-iphone", "desktop-windows-x64", "desktop-linux-arm64", "desktop-macos-x64", "ios-ipad",
            "android-device-api35"], [r["slot"] for r in workflow.matrix("all")["include"]])
        self.assertEqual(11, len(workflow.SLOTS))

    def test_dispatch_membership_and_sdk_branch_are_exactly_existing_tools_and_api33_api34(self):
        text = (ROOT / ".github/workflows/gradle.yml").read_text()
        choices = re.search(r"options: \[([^\n]+)\]", text).group(1)
        options = [v.strip() for v in choices.split(",")]
        self.assertEqual(len(options), len(set(options)))
        self.assertEqual(set(workflow.PROFILES), set(options))
        self.assertEqual(1, options.count(PROFILE))
        self.assertTrue(set(ORIGINAL_BATCHES) <= set(options))
        self.assertTrue(set(ROUTES) <= set(options))
        self.assertEqual(SDK, fixed.SDK_PACKAGES[PROFILE])
        self.assertEqual(["cmdline-tools;23.0", "platforms;android-37.0", "build-tools;36.0.0", "emulator",
            "system-images;android-33;google_apis;x86_64", "system-images;android-34;google_apis;x86_64"], SDK.split())
        self.assertEqual([SDK], re.findall(r"inputs\.profile == '" + PROFILE + r"' && '([^']+)'", text))
        self.assertIn('ANDROID_BATCH: ${{ matrix.android-batch }}', text)
        self.assertIn('scripts/ci/android_device_batch.py plan --batch "$ANDROID_BATCH"', text)
        self.assertIn('scripts/ci/android_device_batch.py run --batch "$ANDROID_BATCH"', text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("persist-credentials: false", text)
        library_job = text.split("\n  library-tests:\n", 1)[1].split("\n  webview-consumer:\n", 1)[0]
        capacity = re.search(r"(?m)^      max-parallel: (.+)$", library_job).group(1)
        self.assertNotIn(PROFILE, capacity)
        self.assertTrue(capacity.endswith("&& 1 || 2 }}"))

    def test_new_readonly_batch_cli_and_preflight_use_only_the_finite_media_union(self):
        with patch.object(sys, "argv", ["android_device_batch.py", "plan", "--batch", PROFILE]), \
                patch.object(batch, "run", side_effect=AssertionError("No runtime from plan")), \
                patch.object(sys, "stdout", io.StringIO()) as output:
            self.assertEqual(0, batch.main())
        self.assertEqual(self.selection, json.loads(output.getvalue()))
        completed = subprocess.CompletedProcess([], 0, stdout=json.dumps(self.selection), stderr="")
        with patch.object(workflow.subprocess, "run", return_value=completed) as mocked:
            receipt = workflow.preflight_plans(PROFILE, root=ROOT)
        mocked.assert_called_once_with([sys.executable, "-B", str(ROOT / "scripts/ci/android_device_batch.py"),
            "plan", "--batch", PROFILE], cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(1, len(receipt["slots"]))
        self.assertEqual(2, receipt["slots"][0]["expected_modules"])
        self.assertEqual(0, receipt["Gradle_builds_executed"])
        self.assertEqual(0, receipt["library_tests_executed"])
        for routes in (self.selection["routes"][:1], list(reversed(self.selection["routes"])),
                       [self.selection["routes"][0]] * 2, []):
            altered = {**self.selection, "routes": routes}
            with patch.object(workflow.subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(altered), stderr="")), self.assertRaises(ValueError):
                workflow.preflight_plans(PROFILE, root=ROOT)

    def test_media_api_module_focus_or_host_overrides_refuse_before_source_or_process_work(self):
        first = ROUTES[0]
        for index, value in ((0, 35), (0, "33"), (0, True), (1, "calf-io"), (2, "android-storage-api28")):
            changed = list(fixed.SELECTIONS[first]); changed[index] = value
            with patch.dict(fixed.SELECTIONS, {first: tuple(changed)}), \
                    patch.object(lt, "plan", side_effect=AssertionError("No source plan after refusal")), self.assertRaises(ValueError):
                batch.plan(ROOT, PROFILE)
        matrix_function = workflow.matrix
        for key, value in (("suite", "android-host"), ("runner", "self-hosted"), ("arch", "arm64"),
            ("python", "python"), ("emulator-api", "35"), ("test-modules", "calf-io"),
            ("test-focus", "android-storage-api28"), ("serial-emulator-api", "35")):
            def changed_matrix(name, key=key, value=value):
                document = matrix_function(name)
                if name == first: document["include"][0][key] = value
                return document
            with patch.object(workflow, "matrix", side_effect=changed_matrix), \
                    patch.object(lt, "plan", side_effect=AssertionError("No source plan after refusal")), self.assertRaises(ValueError):
                batch.plan(ROOT, PROFILE)
        for name in (PROFILE + ";all", PROFILE + "-api35", PROFILE + " --module calf-io"):
            with patch.object(lt, "execute") as execute, self.assertRaises(ValueError): batch.plan(ROOT, name)
            execute.assert_not_called()

    def test_media_source_case_task_report_refusals_and_unchanged_serial_cleanup_are_retained(self):
        for route in self.selection["routes"]:
            for mutation in ("task", "report", "filter", "extra-case", "missing-case", "module", "suite"):
                source = copy.deepcopy(route["source_suite"]);item = source["expected"][0]
                if mutation == "task":item["task"] = ":calf-permissions:calf-permissions-core:test"
                elif mutation == "report":item["report_directory"] = MODULE + "/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest"
                elif mutation == "filter":item["test_filter"] = CLASS + "#unrelated"
                elif mutation == "extra-case":item["required_testcases"].append({"classname": CLASS, "name": "unrelated"})
                elif mutation == "missing-case":item["required_testcases"] = []
                elif mutation == "module":item["module"] = "calf-io"
                else:source["suite"] = "android-host"
                with self.assertRaises(ValueError):lt.validate_test_focus(source)
            relative = "build/ci-verification/symbolic-media/routes/" + route["profile"]
            self.assertEqual([sys.executable, "-B", str(ROOT / "scripts/ci/android_device_tests.py"), "run",
                "--api-level", str(route["api_level"]), "--module", MODULE, "--focus", "android-media-selection",
                "--output", relative], batch.command(ROOT, relative, route))
        self.assertEqual(8192, batch.RESERVE_MIB)
        self.assertEqual(8192, device.RESERVE_MIB)
        self.assertEqual(4200, batch.ROUTE_TIMEOUT_SECONDS)
        tree = ast.parse(Path(batch.__file__).read_text())
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
        calls = [n for n in ast.walk(run) if isinstance(n, ast.Call)]
        def line(name):
            nodes = [n for n in calls if (isinstance(n.func, ast.Name) and n.func.id == name)
                or (isinstance(n.func, ast.Attribute) and n.func.attr == name)]
            self.assertEqual(1, len(nodes)); return nodes[0].lineno
        self.assertLess(line("execute"), line("cleanup_certified"))
        self.assertLess(line("cleanup_certified"), line("archive_route"))
        self.assertLess(line("archive_route"), line("reclaim_owned_state"))

if __name__ == "__main__":
    unittest.main()
