"""Supported-tool attempt admission, not Apple runtime/memory/profile passes."""
import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as lt
import test_ios_application_receipts as receipts
import test_ios_ui_application as frames
import workflow_matrix as matrix


class IosImageDarwinFocusTests(unittest.TestCase):
    def test_supported_darwin_tool_attempt_is_separate_from_the_failed_strict_profile(self):
        self.assertIn("ios-image-memory-darwin", matrix.PROFILES,
                      "Instruments cannot start when the unrelated strict ObjC startup assertion aborts")
        row, = matrix.matrix("ios-image-memory-darwin")["include"]
        self.assertEqual(("ios-iphone", "calf-ui", lt.IOS_IMAGE_DARWIN_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        strict, = matrix.matrix("ios-image-memory")["include"]
        self.assertEqual(lt.IOS_IMAGE_MEMORY_FOCUS, strict["test-focus"])
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def plan(self, root=lt.ROOT):
        return lt.plan(root, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_DARWIN_FOCUS)

    def arguments(self):
        return sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + lt.ui_application_focus_filter(lt.IOS_IMAGE_DARWIN_FOCUS)]

    def test_native_methods_are_identical_but_diagnostic_commands_and_scope_are_distinct(self):
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(3, len(plan["expected"][0]["required_testcases"]))
        self.assertEqual(lt.ui_application_focus_filter(lt.IOS_IMAGE_MEMORY_FOCUS), plan["expected"][0]["test_filter"])
        self.assertEqual(lt.ui_application_focus_groups(lt.IOS_IMAGE_MEMORY_FOCUS),
                         lt.ui_application_focus_groups(lt.IOS_IMAGE_DARWIN_FOCUS))
        command = lt.gradle_command("ios", plan, frames.DEVICE)
        self.assertIn("-PnativecmpkitImageMemoryDiagnostics=darwin-tools", command)
        self.assertNotIn("-PnativecmpkitImageMemoryDiagnostics=true", command)
        self.assertEqual(3, command.count("--tests"))
        self.assertNotIn("UIImageConversionTest", " ".join(command))
        strict = lt.plan(lt.ROOT, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        self.assertIn("-PnativecmpkitImageMemoryDiagnostics=true", lt.gradle_command("ios", strict, frames.DEVICE))
        self.assertNotEqual(plan["scope"], strict["scope"])

    def test_transport_flag_not_identical_filter_order_binds_the_independent_request(self):
        arguments = self.arguments()
        for patterns in (arguments[-1].split("=", 1)[1].split(","),
                         list(reversed(arguments[-1].split("=", 1)[1].split(",")))):
            changed = arguments[:2] + ["--ktest_gradle_filter=" + ",".join(patterns)]
            self.assertEqual(lt.IOS_IMAGE_MEMORY_FOCUS, app.application_test_focus(changed))
            self.assertEqual(lt.IOS_IMAGE_DARWIN_FOCUS, app.application_test_focus(changed, "darwin-tools"))
        self.assertEqual(360, app.application_timeout_seconds(lt.IOS_IMAGE_DARWIN_FOCUS))

    def test_unknown_mode_unfiltered_other_focus_missing_duplicate_or_arbitrary_selectors_are_rejected(self):
        for mode in ("true", "false", "disable", "asan", "darwin", ""):
            with self.assertRaises(ValueError):
                app.application_test_focus(self.arguments(), mode)
        for arguments in (sorted(app.TEST_ARGUMENTS), self.arguments() + ["--extra"],
                          sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=*"],
                          sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + lt.ui_application_focus_filter(lt.IOS_WEBVIEW_LIFECYCLE_FOCUS)],
                          sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + lt.IOS_IMAGE_MEMORY_CLASS + "." + lt.IOS_IMAGE_MEMORY_METHODS[0]],
                          sorted(app.TEST_ARGUMENTS) + [self.arguments()[-1] + "," + lt.IOS_IMAGE_MEMORY_CLASS + "." + lt.IOS_IMAGE_MEMORY_METHODS[0]]):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                app.application_test_focus(arguments, "darwin-tools")

    def test_real_cli_strips_only_the_finite_transport_flag_before_generated_native_arguments(self):
        binary = lt.ROOT / "calf-ui/build/bin/iosSimulatorArm64/applicationDebugTest/test.kexe"
        arguments = self.arguments()
        argv = [str(lt.ROOT / "scripts/ci/ios_ui_application.py"), "--binary", str(binary),
                "--image-diagnostics", "darwin-tools", *arguments]
        with patch.object(app.sys, "argv", argv), patch.object(app, "run", return_value={"transport_passed": True}) as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, app.main())
        run.assert_called_once_with(binary.relative_to(lt.ROOT).as_posix(), arguments, image_diagnostics="darwin-tools")

    def fixture(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups); f.setUp()
        f.write(lt.IOS_IMAGE_MEMORY_SOURCE, (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_bytes())
        f.plan = self.plan(f.root)
        cases = [{"classname": lt.IOS_IMAGE_MEMORY_CLASS, "name": name, "status": "passed"}
                 for name in lt.IOS_IMAGE_MEMORY_METHODS]
        f.document.update(explicit_test_focus=lt.IOS_IMAGE_DARWIN_FOCUS, image_diagnostics_mode="darwin-tools",
                          strict_runtime_assertions_attested=False)
        f.document["application_protocol"].update(testcases=cases, counts=lt.case_counts(cases))
        f.modules[0]["testcases"] = f.xml_cases(cases); f.save()
        return f

    def test_mode_receipt_and_all_actual_worker_binary_runtime_xml_cleanup_gates_remain_required(self):
        f = self.fixture()
        self.assertEqual([], f.collect()["errors"])
        self.assertFalse(f.document["image_memory_profile"]["profile_passed"], "A native result is not a profile result")
        original = copy.deepcopy(f.document)
        for change in (lambda d: d.pop("image_diagnostics_mode"),
                       lambda d: d.update(image_diagnostics_mode="strict-runtime"),
                       lambda d: d.update(strict_runtime_assertions_attested=True),
                       lambda d: d.pop("image_memory_profile"),
                       lambda d: d["image_memory_profile"].update(owned_private_tree_removed=False),
                       lambda d: d["image_memory_profile"].update(signed_application_executable_sha256="f" * 64),
                       lambda d: d["application_protocol"].update(completion={"runner_exit": 0, "worker_terminated": False}),
                       lambda d: d.update(binary_sha256_after="f" * 64),
                       lambda d: d["cleanup"].update(owned_app_absence_verified=False)):
            f.document = copy.deepcopy(original); change(f.document); f.save()
            self.assertTrue(f.collect()["errors"])

    def test_independent_mode_cannot_launder_an_old_strict_receipt_or_other_module(self):
        f = self.fixture()
        f.document["explicit_test_focus"] = lt.IOS_IMAGE_MEMORY_FOCUS; f.save()
        self.assertTrue(f.collect()["errors"])
        f.plan = lt.plan(f.root, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        self.assertTrue(f.collect()["errors"], "Strict evidence must not contain a Darwin-only mode claim")
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-webview",)),
                               ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError): lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.IOS_IMAGE_DARWIN_FOCUS)

    def test_linked_test_only_mode_retains_both_strict_options_and_does_not_override_defaults(self):
        build = (lt.ROOT / "calf-ui/build.gradle.kts").read_text()
        self.assertIn('if (imageMemoryMode == "true") {\n                binaryOption("runtimeAssertionsMode", "panic")', build)
        self.assertIn('binaryOption("checkStateAtExternalCalls", "true")', build)
        self.assertIn('if (imageMemoryMode == "darwin-tools") listOf("--image-diagnostics", "darwin-tools")', build)
        self.assertIn('setOf("true", "darwin-tools")', build)
        self.assertNotIn('binaryOption("runtimeAssertionsMode", "ignore")', build)
        self.assertNotIn('binaryOption("checkStateAtExternalCalls", "false")', build)
        self.assertNotIn('binaryOption("sanitizer"', build)
        self.assertEqual(3, (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_text().count("@Test"))

    def test_synthetic_owned_launch_observes_mode_and_keeps_unsupported_profile_explicit(self):
        f = frames.OwnedApplicationTests("test_owned_only_install_launch_readback_uninstall_and_local_cleanup")
        self.addCleanup(f.doCleanups); f.setUp()
        child = {"SIMCTL_CHILD_MallocScribble": "1"}  # Explicitly synthetic process environment.
        def launch(argv, protocol, *, timeout, environment):
            self.assertEqual(360, timeout); self.assertEqual(child, environment)
            self.assertNotIn("--image-diagnostics", argv)
            protocol.feed(frames.ACTIVE)
            protocol.feed(protocol.expected_bundle + ": 12345")
            protocol.feed(frames.frame("testSuiteStarted", name=lt.IOS_IMAGE_MEMORY_CLASS))
            for method in lt.IOS_IMAGE_MEMORY_METHODS:
                protocol.feed(frames.frame("testStarted", name=method))
                if method == app.IMAGE_PROFILE_CASE[1]:
                    protocol.feed("NATIVECMPKIT_IMAGE_PROFILE phase=ready")
                    protocol.feed("NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=23")
                protocol.feed(frames.frame("testFinished", name=method))
            protocol.feed(frames.frame("testSuiteFinished", name=lt.IOS_IMAGE_MEMORY_CLASS))
            protocol.feed(frames.COMPLETE)
            return {"process_exit": 0, **protocol.finish(0)}
        with patch("apple_image_profile.ImageProfileDriver") as driver, \
                patch.object(app.runtime, "capture", side_effect=[f.before, f.before]), \
                patch.object(app, "execute_control", side_effect=f.control), \
                patch.object(app, "forward_application", side_effect=launch), \
                patch.object(app.shutil, "disk_usage", return_value=frames.SimpleNamespace(free=10 * 1024**3)):
            driver.return_value.prepare.return_value = child
            driver.return_value.receipt = {"owned_ack_removed": True, "owned_private_tree_removed": True,
                                          "supported": False, "profile_passed": False}
            result = app.run(f.binary.relative_to(f.root).as_posix(), self.arguments(), image_diagnostics="darwin-tools")
            self.assertTrue(result["transport_passed"])
            self.assertEqual(3, result["application_protocol"]["counts"]["passed"])
            self.assertEqual("darwin-tools", result["image_diagnostics_mode"])
            self.assertFalse(result["strict_runtime_assertions_attested"])
            self.assertFalse(result["image_memory_profile"]["profile_passed"])
            driver.return_value.request.assert_called_once_with(12345)
            driver.return_value.close.assert_called_once()
        self.assertNotIn("SIMCTL_CHILD", json.dumps(result))

    def test_workflow_is_a_finite_reports_only_request_with_no_new_permissions_or_publication(self):
        workflow = (lt.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("ios-image-memory, ios-image-memory-darwin, ios-webview-lifecycle", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("id-token: write", workflow)
        self.assertTrue(matrix.preflight_plans("ios-image-memory-darwin", lt.ROOT))


if __name__ == "__main__":
    unittest.main()
