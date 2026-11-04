"""NEW synthetic classifier/source controls only: zero AppKit/JNI/native execution."""
import re
import json
import os
import subprocess
import tomllib
import unittest
from pathlib import Path

import native_test_policy as policy

ROOT = Path(__file__).resolve().parents[2]


def lifecycle_cases(status="passed", suffix="[desktop]"):
    return [{"classname": policy.MAC_LIFECYCLE_CLASS, "name": method + suffix, "status": status}
            for method in policy.MAC_LIFECYCLE_METHODS]


class MacOsShareLifecyclePolicy(unittest.TestCase):
    def test_exact_new_mac_population_requires_all_three_real_outcomes(self):
        for host in ("Darwin", "macos", "MAC OS X"):
            for suffix in ("", "[desktop]"):
                actual = lifecycle_cases(suffix=suffix)
                scenarios, errors = policy.macos_lifecycle_cases(actual, host, True)
                self.assertEqual([], errors)
                self.assertEqual(3, len(scenarios))
                self.assertTrue(all(row["required_on_host"] and row["disposition"] == "required-executed" for row in scenarios))
                self.assertTrue(all("disposition" not in row for row in actual))

    def test_only_exact_opposite_host_skips_are_na_never_passes(self):
        for host in ("Linux", "windows", "win32"):
            actual = lifecycle_cases("skipped")
            scenarios, errors = policy.macos_lifecycle_cases(actual, host, False)
            self.assertEqual([], errors)
            self.assertTrue(all(not row["required_on_host"] and row["disposition"] == "not-applicable" for row in scenarios))
            self.assertTrue(all(row["status"] == "skipped" and row["disposition"] == "not-applicable" for row in actual))
            _, errors = policy.macos_lifecycle_cases(lifecycle_cases(), host, False)
            self.assertEqual(3, len(errors))

    def test_mac_skip_failure_unknown_and_missing_optin_remain_red(self):
        for status in ("skipped", "failed", "error", "unknown", None):
            scenarios, errors = policy.macos_lifecycle_cases(lifecycle_cases(status), "Darwin", True)
            self.assertEqual(3, len(errors))
            self.assertTrue(all(row["disposition"] == "required-not-passed" for row in scenarios))
        for optin in (False, None, "true", 1):
            _, errors = policy.macos_lifecycle_cases(lifecycle_cases(), "Darwin", optin)
            self.assertEqual(3, len(errors))

    def test_missing_and_duplicate_new_methods_cannot_pass(self):
        for index in range(3):
            missing = lifecycle_cases()
            missing.pop(index)
            _, errors = policy.macos_lifecycle_cases(missing, "Darwin", True)
            self.assertEqual(1, len(errors))
            duplicate = lifecycle_cases()
            duplicate.append({**duplicate[index], "name": policy.MAC_LIFECYCLE_METHODS[index]})
            _, errors = policy.macos_lifecycle_cases(duplicate, "Darwin", True)
            self.assertEqual(1, len(errors))
        _, errors = policy.macos_lifecycle_cases([], "Darwin", True)
        self.assertEqual(3, len(errors))

    def test_altered_names_classes_or_target_suffixes_never_get_na(self):
        for altered in ("prefix" + policy.MAC_LIFECYCLE_METHODS[0], policy.MAC_LIFECYCLE_METHODS[0] + "[ios]",
                        policy.MAC_LIFECYCLE_METHODS[0] + "[desktop][desktop]"):
            actual = lifecycle_cases("skipped")
            actual[0]["name"] = altered
            _, errors = policy.macos_lifecycle_cases(actual, "Linux", False)
            self.assertTrue(errors)
            self.assertNotIn("disposition", actual[0])
        actual = lifecycle_cases("skipped")
        actual[0]["classname"] += "Other"
        _, errors = policy.macos_lifecycle_cases(actual, "Linux", False)
        self.assertTrue(errors)
        self.assertNotIn("disposition", actual[0])

    def test_unknown_host_is_refused_instead_of_guessed(self):
        for host in (None, "FreeBSD", "DarwinWindows", ""):
            with self.assertRaises(ValueError):
                policy.macos_lifecycle_cases(lifecycle_cases(), host, True)

    def test_complete_suite_classifies_new_na_without_changing_original_registry(self):
        original = [{"classname": policy.CLASS, "name": method + "[desktop]",
                     "status": "skipped" if method == policy.MAC_GUI else "passed"}
                    for method in policy.REQUIRED_CASES]
        old, errors = policy.apply("calf-share", "desktop", original, "Linux", False)
        self.assertEqual([], errors)
        self.assertEqual(4, len(old))
        complete = original + lifecycle_cases("skipped")
        scenarios, errors = policy.apply("calf-share", "desktop", complete, "Linux", False)
        self.assertEqual([], errors)
        self.assertEqual(7, len(scenarios))
        self.assertEqual(4, sum(row.get("disposition") == "not-applicable" for row in complete))
        self.assertEqual(4, len(policy.REQUIRED_CASES))

    def test_unrelated_modules_suites_and_classes_receive_no_new_skip_exception(self):
        for module, suite in (("calf-io", "desktop"), ("calf-share", "ios"), ("calf-share", "js")):
            actual = lifecycle_cases("skipped")
            self.assertEqual(([], []), policy.apply(module, suite, actual, "Linux", False))
            self.assertTrue(all("disposition" not in row for row in actual))
        actual = lifecycle_cases("skipped") + [{"classname": "Other", "name": "skip", "status": "skipped"}]
        _, errors = policy.macos_lifecycle_cases(actual, "Linux", False)
        self.assertEqual([], errors)
        self.assertNotIn("disposition", actual[-1])

    def test_new_kotlin_declarations_bind_real_owner_jni_and_nonvirtual_worker(self):
        source = (ROOT / policy.MAC_LIFECYCLE_SOURCE).read_text()
        self.assertEqual(list(policy.MAC_LIFECYCLE_METHODS), re.findall(r"@Test\s+fun\s+(\w+)\s*\(", source))
        self.assertIn("DesktopShareOwner(scope, { options.get() }, { results += it })", source)
        self.assertIn("Executors.newSingleThreadExecutor().asCoroutineDispatcher()", source)
        self.assertIn("fixture.scope.async { true }.await()", source)
        self.assertIn("NativeShareBridge.beginShareSheet", source)
        self.assertIn("fixture.job.join()", source)
        self.assertIn("ShareFailureReason.TimedOut", source)
        self.assertNotRegex(source, r"@(?:Ignore|Disabled)|TestDispatcher|runTest\(")

    def test_optin_native_harness_compiles_actual_source_without_new_release_dependency(self):
        manifest = tomllib.loads((ROOT / "calf-share/native/Cargo.toml").read_text())
        target = manifest["test"]
        self.assertEqual(1, len(target))
        self.assertEqual("appkit_lifecycle", target[0]["name"])
        self.assertIs(False, target[0]["harness"])
        self.assertEqual(["appkit-lifecycle-tests"], target[0]["required-features"])
        self.assertEqual([], manifest["features"]["appkit-lifecycle-tests"])
        self.assertEqual('include!("../src/lib.rs");', (ROOT / "calf-share/native/tests/appkit_lifecycle_main.rs").read_text().splitlines()[1])
        self.assertIn('#[cfg(all(test, feature = "appkit-lifecycle-tests"))]', (ROOT / "calf-share/native/src/macos.rs").read_text())

    def test_native_control_failure_and_weak_lifetime_are_independent_of_result_cleanup(self):
        source = (ROOT / "calf-share/native/tests/appkit_lifecycle/cases.rs").read_text()
        self.assertIn("CONTROL_FAILED.store(true", source)
        self.assertIn("!CONTROL_FAILED.load(", source)
        self.assertIn("Weak::from_retained(&operation.delegate)", source)
        self.assertIn("Arc::downgrade(&operation._completion)", source)
        self.assertIn("w.delegate.load().is_none() && w.completion.upgrade().is_none()", source)
        self.assertIn("for _ in 0..2048", source)
        self.assertNotIn("unsafe impl Send", source)
        self.assertNotIn("finish_on_main(", source)
        self.assertNotIn("performWithItems", source.replace("// A real OS service object is retained, but never performWithItems/opened.", ""))


class MacOsShareLifecycleFinalHarnessControls(unittest.TestCase):
    """NEW final harness controls; earlier accepted eleven controls are not replayed."""

    def test_actual_cargo_target_discovery_has_only_one_explicit_feature_gated_harness(self):
        result = subprocess.run(["cargo", "metadata", "--offline", "--locked", "--no-deps",
                                 "--format-version", "1", "--manifest-path",
                                 "calf-share/native/Cargo.toml"], cwd=ROOT, check=True,
                                capture_output=True, text=True, timeout=30,
                                env={**os.environ, "PATH": str(Path.home() / ".cargo/bin") + os.pathsep + os.environ["PATH"]})
        package = next(item for item in json.loads(result.stdout)["packages"] if item["name"] == "calf-share-native")
        targets = [item for item in package["targets"] if "test" in item["kind"]]
        self.assertEqual(1, len(targets), "No root helper may become an ungated auto-discovered integration target")
        self.assertEqual("appkit_lifecycle", targets[0]["name"])
        self.assertEqual(["appkit-lifecycle-tests"], targets[0]["required-features"])
        self.assertTrue(targets[0]["src_path"].endswith("/tests/appkit_lifecycle_main.rs"))

    def test_finite_native_catalogue_has_exact_eight_cases_and_stress_is_separate(self):
        source = (ROOT / "calf-share/native/tests/appkit_lifecycle/cases.rs").read_text()
        catalogue = source.split("const FINITE:", 1)[1].split("];", 1)[0]
        names = re.findall(r'"([a-z_]+)"', catalogue)
        self.assertEqual([
            "cancel_before_dispatch", "no_key_window", "missing_content_view", "real_picker_cancel",
            "controlled_picker_dismissal", "controlled_success_duplicate_late", "controlled_service_failure",
            "bounded_concurrent_requests",
        ], names)
        for name in names:
            self.assertEqual(1, len(re.findall(r"^fn " + name + r"\(\)", source, re.MULTILINE)))
        self.assertNotIn("stress_2048", catalogue)
        self.assertIn('selector == "--case=stress_2048"', source)
        self.assertIn('selector == &format!("--case={name}")', source)
        self.assertIn('assert!(!selected.is_empty()', source)

    def test_actual_native_reports_are_exclusively_fresh_reached_cases_with_red_cleanup(self):
        source = (ROOT / "calf-share/native/tests/appkit_lifecycle/cases.rs").read_text()
        report = source.split("pub(crate) fn run()", 1)[1]
        self.assertIn('format!("process-{}", std::process::id())', report)
        self.assertIn('std::fs::create_dir(&output)', report)
        self.assertNotIn('remove_dir_all', report)
        self.assertIn('for (name, case) in selected', report)
        self.assertIn('result.is_ok() && cleanup.is_ok() && !CONTROL_FAILED.load(', report)
        self.assertIn('usize::from(!passed)', report)
        self.assertIn('TEST-{name}.xml', report)
        self.assertIn('actual-native=true live={}', report)
        self.assertIn('controlled-callbacks-not-recipient=true', report)
        self.assertIn('if failed {\n            break;', report)
        self.assertIn('std::process::exit(1)', report)
        self.assertNotRegex(report, r"<skipped|read_to_string|junit_cases|copy\(")

    def test_controlled_native_dismissal_calls_actual_receiver_and_terminal_result(self):
        source = (ROOT / "calf-share/native/tests/appkit_lifecycle/cases.rs").read_text()
        body = source.split("fn controlled_picker_dismissal()", 1)[1].split("fn controlled_service_failure()", 1)[0]
        self.assertIn('let id = begin()', body)
        self.assertIn('let observer = when_live(id,', body)
        self.assertIn('operations.borrow()[&id].delegate.clone()', body)
        self.assertIn('msg_send![&*delegate, sharingServicePicker:', body)
        self.assertIn('didChooseSharingService: std::ptr::null::<AnyObject>()]', body)
        self.assertIn('wait_result(id, DISMISSED)', body)
        self.assertIn('observer.join()', body)
        self.assertIn('assert_released()', body)
        self.assertNotRegex(body, r"registry\(\)\.finish|finish_on_main|finish_later|cancel_share\(")


if __name__ == "__main__":
    unittest.main()
