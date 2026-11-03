# SPDX-License-Identifier: Apache-2.0
"""Important NEW/affected controls only; ZERO Kotlin/UIKit/XCTest execution here."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock, patch

import library_tests as library
import workflow_matrix as workflow
import native_ui_input as native
import native_ui_input_startup as startup
import ios_modal_worker_source_projection as history
import ios_worker_completion_source_projection as completion_history
from test_native_ui_input import driver_fixture, TOKEN, AUTH, DEVICE, BUNDLE, HASH, no_native

ROOT = Path(__file__).resolve().parents[2]
HOST = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
COMPILER = "scripts/ci/ios_modal_worker_compile.init.gradle.kts"


class ModalWorkerStartupControls(unittest.TestCase):
    def test_startup_git_revision_is_sha1_not_a_sha256_binary_digest(self):
        self.assertIsNotNone(startup.REVISION.fullmatch("a" * 40))
        for candidate in ("a" * 64, "a" * 39, "g" * 40, "a" * 40 + "\n"):
            self.assertIsNone(startup.REVISION.fullmatch(candidate))
        source = (ROOT / "scripts/ci/native_ui_input_startup.py").read_text()
        self.assertIn("not REVISION.fullmatch(revision)", source)
        self.assertNotIn("native.HASH.fullmatch(revision)", source)

    def test_worker_pool_is_call_owned_without_changing_main_dispatch_or_any_original_lifecycle_body(self):
        self.assertEqual("dd73e1a96b6a7cbf64d67b39ab0f4c62d1f8b7100771409f75336410c6a7d7db",
                         hashlib.sha256((ROOT / library.IOS_MODAL_LIFECYCLE_SOURCE).read_bytes()).hexdigest())
        source = (ROOT / HOST).read_text()
        previous = history.current_source_before_modal_worker(HOST, source.encode()).decode()
        self.assertEqual("4eb8b1c7cc43de5bc39f0d36ec818d7216054e0b6b262b936826b4efe51fbc65", hashlib.sha256(previous.encode()).hexdigest())
        bridge = source.split("internal fun <T> onApplicationMain", 1)[1].split("internal fun requireOwnedApplicationWindow", 1)[0]
        self.assertLess(bridge.index("if (NSThread.isMainThread) return action()"), bridge.index("return autoreleasepool"))
        self.assertIn("dispatch_sync(dispatch_get_main_queue()) { result = runCatching(action) }", bridge)
        self.assertIn("checkNotNull(result).getOrThrow()", bridge)
        prior_stage = completion_history.current_source_before_worker_completion(HOST, source.encode()).decode()
        self.assertEqual(previous.split("internal fun requireOwnedApplicationWindow", 1)[1], prior_stage.split("internal fun requireOwnedApplicationWindow", 1)[1])
        source = (ROOT / library.IOS_WORKER_OWNERSHIP_SOURCE).read_text()
        self.assertEqual(library.IOS_WORKER_OWNERSHIP_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertNotIn("BottomSheetManager", source)
        for marker in ("setContent { }", "waitForIdle()", "repeat(3) { runOnIdle { GC.collect() } }", "assertSame(original, actual)"):
            self.assertIn(marker, source)

    def test_finite_three_method_selection_excludes_both_accepted_lifecycle_methods_and_all_prior_modal_cases(self):
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_WORKER_MEMORY_FOCUS)
        identities = library.ui_application_focus_identities(library.IOS_MODAL_WORKER_MEMORY_FOCUS)
        self.assertEqual(3, len(identities))
        self.assertEqual(identities, plan["expected"][0]["required_testcases"])
        self.assertTrue({item["name"] for item in identities}.isdisjoint(
            {name + "[iosSimulatorArm64]" for name in library.IOS_MODAL_LIFECYCLE_METHODS[1:]}))
        command = library.gradle_command("ios", plan, DEVICE)
        self.assertEqual(1, command.count(COMPILER))
        source = (ROOT / COMPILER).read_text()
        request = source.split("val applicationRequest", 1)[1].split("val permittedTasks", 1)[0]
        authored = re.findall(r'"(com\.mohamedrejeb\.[^"\n]+)"', request)
        expected = [":calf-ui:iosSimulatorArm64ApplicationTest"] + [arg for item in authored for arg in ("--tests", item)]
        self.assertEqual(expected, command[command.index(":calf-ui:iosSimulatorArm64ApplicationTest"):])
        self.assertEqual([library.IOS_MODAL_LIFECYCLE_SOURCE, library.IOS_WORKER_OWNERSHIP_SOURCE,
                          HOST, HOST.replace("NativeUiApplicationHost", "NativeObjectIdentity")],
                         re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', source))
        row = workflow.matrix("ios-modal-worker-memory-recovery")["include"]
        self.assertEqual(1, len(row)); self.assertEqual(library.IOS_MODAL_WORKER_MEMORY_FOCUS, row[0]["test-focus"])
        for mutation in ({"ios-modal-worker-memory-recovery": ("ios-iphone", "ios-ipad")},
                         {"ios-modal-worker-memory-recovery": ("desktop-macos-arm64",)}):
            with patch.dict(workflow.PROFILES, mutation), self.assertRaises(ValueError): workflow.matrix("ios-modal-worker-memory-recovery")
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, library.IOS_MODAL_WORKER_MEMORY_FOCUS))

    def test_scheme_environment_preserves_xcode_testing_paths_and_refuses_existing_credentials_without_mutation(self):
        target = {"IsUITestBundle": True, "BlueprintName": "NativeCmpKitInputTests",
                  "EnvironmentVariables": {"OWNED": "keep"}, "TestingEnvironmentVariables": {"DYLD_LIBRARY_PATH": "__TESTROOT__/Debug"}}
        for key in ("EnvironmentVariables", "TestingEnvironmentVariables"):
            for value in ({"NATIVECMPKIT_INPUT_AUTH": "foreign"}, {"x": 1}, None):
                document = {"NativeCmpKitInputTests": dict(target, **{key: value})}
                prior = copy.deepcopy(document)
                with self.assertRaises(ValueError): native.prepare_xctestrun(document, "http://127.0.0.1:49123", TOKEN, BUNDLE, AUTH)
                self.assertEqual(prior, document)
        document = {"NativeCmpKitInputTests": copy.deepcopy(target)}
        native.prepare_xctestrun(document, "http://127.0.0.1:49123", TOKEN, BUNDLE, AUTH)
        selected = document["NativeCmpKitInputTests"]
        self.assertEqual(target["TestingEnvironmentVariables"], selected["TestingEnvironmentVariables"])
        self.assertEqual("keep", selected["EnvironmentVariables"]["OWNED"])
        self.assertEqual(AUTH, selected["EnvironmentVariables"]["NATIVECMPKIT_INPUT_AUTH"])

    def test_readiness_records_actual_exit_without_conflating_it_with_the_deadline(self):
        with driver_fixture() as driver:
            driver.ready = Mock(); driver.ready.wait.return_value = False
            driver.process = Mock(); driver.process.poll.return_value = 65
            with patch.object(native.time, "monotonic", side_effect=[10.0, 12.25]), self.assertRaises(RuntimeError):
                driver._await_runner_readiness()
            self.assertEqual({"ready": False, "process_exit_code": 65, "deadline_reached": False, "elapsed_seconds": 2.25}, driver.receipt["runner_startup"])
            self.assertNotIn("runner_ready", driver.receipt)

    def test_readiness_records_a_live_timeout_without_inventing_an_exit(self):
        with driver_fixture() as driver:
            driver.ready = Mock(); driver.ready.wait.return_value = False
            driver.process = Mock(); driver.process.poll.return_value = None
            with patch.object(native.time, "monotonic", side_effect=[10.0, 190.0]), self.assertRaises(RuntimeError):
                driver._await_runner_readiness()
            self.assertEqual({"ready": False, "process_exit_code": None, "deadline_reached": True, "elapsed_seconds": 180.0}, driver.receipt["runner_startup"])

    def test_readiness_requires_the_authenticated_event_not_process_success_or_elapsed_sleep(self):
        with driver_fixture() as driver:
            driver.ready.set(); driver.process = Mock(); driver.process.poll.return_value = None
            with patch.object(native.time, "monotonic", side_effect=[10.0, 10.5]): driver._await_runner_readiness()
            self.assertEqual({"ready": True, "process_exit_code": None, "deadline_reached": False, "elapsed_seconds": .5}, driver.receipt["runner_startup"])
            self.assertTrue(driver.receipt["runner_ready"])

    def test_startup_only_handshake_needs_no_aut_container_and_can_never_certify_library_input(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(native.secrets, "token_hex", return_value=AUTH):
            driver = startup.StartupDriver(Path(temporary), DEVICE, BUNDLE, TOKEN, no_native)
            self.assertIsNone(driver.directory)
            self.assertFalse(driver.receipt["verified"])
            self.assertNotIn("signed_application_executable_sha256", driver.receipt)
            self.assertEqual({"ready": True}, driver.handle("POST", "/ready", {}))
            self.assertEqual({"operation": "finish"}, driver.handle("GET", "/next", None))
            self.assertEqual({"finished": True}, driver.handle("POST", "/finished", {"delivered": 0}))
            self.assertEqual([], driver.receipt["operations"])
            for method in (driver.prepare, driver.finish):
                with self.assertRaises(RuntimeError): method()
            self.assertFalse(native.validate_receipt(driver.receipt, ROOT, library.IOS_MODAL_XCUI_METHODS,
                             bundle_id=BUNDLE, device=DEVICE, native_pid=1, signed_hash=HASH, plist_hash=HASH))

    def test_startup_failure_excerpt_exports_only_fixed_phases_and_typed_allowlisted_error_codes(self):
        with driver_fixture() as driver:
            driver.scratch.mkdir(parents=True)
            raw = ("NATIVECMPKIT_XCTEST_STARTUP setup-enter\n"
                   "NATIVECMPKIT_XCTEST_TRANSPORT domain=NSURLErrorDomain code=-1022\n"
                   "NATIVECMPKIT_XCTEST_STARTUP setup-enter " + AUTH + "\n"
                   "NATIVECMPKIT_XCTEST_STARTUP secret-path\n"
                   "NATIVECMPKIT_XCTEST_TRANSPORT domain=secret-domain code=1\n"
                   "NATIVECMPKIT_XCTEST_TRANSPORT domain=other code=9999999999\n" +
                   "NATIVECMPKIT_XCTEST_STARTUP finished\n" * 30).encode()
            driver.log = (driver.scratch / "xcodebuild.log").open("xb"); driver.log.write(raw)
            driver._capture_log()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), driver.receipt["private_log_sha256"])
            self.assertEqual(24, len(driver.receipt["startup_diagnostics"]))
            self.assertEqual({"phase": "transport", "domain": "NSURLErrorDomain", "code": -1022}, driver.receipt["startup_diagnostics"][1])
            self.assertNotIn(AUTH, json.dumps(driver.receipt)); self.assertNotIn("secret", json.dumps(driver.receipt))

    def test_standalone_workflow_has_one_readonly_host_no_library_build_or_private_artifacts(self):
        self.assertEqual({"include": []}, workflow.matrix("ios-xctest-startup"))
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        job = source.split("  apple-xctest-startup:\n", 1)[1].split("  apple-appinfo-shape:\n", 1)[0]
        for token in ("runs-on: macos-26", "persist-credentials: false", "--select-simulator", "--restore-check", "--simulator"):
            self.assertIn(token, job)
        for token in ("gradlew", "setup-java", "setup-android", "rustup", "write", ".xcresult", "native-input/"):
            self.assertNotIn(token, job)
        self.assertIn("permissions:\n  contents: read\n", source)
        swift = (ROOT / native.SWIFT).read_text()
        self.assertIn('startup("setup-refused"); throw error', swift)
        self.assertNotRegex(swift, r"\.(launch|activate|performSelector)\s*\(")

    def test_exact_owning_inverse_restores_all_old_pins_and_refuses_historical_or_mutated_current_sources(self):
        for relative, binding in history._bindings().items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_modal_worker(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_modal_worker(relative, previous))
            for bad in (previous, current + b"\n", current.replace(b"\n", b"\r\n")):
                with self.assertRaisesRegex(ValueError, "exact current"):
                    history.current_source_before_modal_worker(relative, bad)


if __name__ == "__main__":
    unittest.main()
