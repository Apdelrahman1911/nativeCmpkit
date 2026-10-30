"""Owning memory-batch contracts only; fixtures execute no UIKit or library code."""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as lt
import test_ios_ui_application as frames
import workflow_matrix as matrix
import test_ios_application_receipts as receipts


class IosImageMemoryFocusTests(unittest.TestCase):
    def test_exact_owned_child_receives_native_diagnostics_without_exporting_or_mutating_environment(self):
        import os
        f = frames.OwnedApplicationTests("test_owned_only_install_launch_readback_uninstall_and_local_cleanup")
        self.addCleanup(f.doCleanups); f.setUp()
        f.expected_timeout = 360
        original = os.environ.copy()
        child = {**original, "SIMCTL_CHILD_MallocScribble": "1"}
        def launch(argv, protocol, *, timeout, environment):
            self.assertEqual(360, timeout)
            self.assertEqual(child, environment)
            self.assertEqual(original, os.environ)
            for line in frames.complete_lines(): protocol.feed(line)
            return {"process_exit": 0, **protocol.finish(0)}
        with patch("apple_image_profile.ImageProfileDriver") as driver, \
                patch.object(app.runtime, "capture", side_effect=[f.before, f.before]), \
                patch.object(app, "execute_control", side_effect=f.control), \
                patch.object(app, "forward_application", side_effect=launch), \
                patch.object(app.shutil, "disk_usage", return_value=frames.SimpleNamespace(free=10 * 1024**3)):
            driver.return_value.prepare.return_value = child
            driver.return_value.receipt = {"owned_ack_removed": True, "owned_private_tree_removed": True,
                                            "supported": False, "profile_passed": False}
            arguments = sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + lt.ui_application_focus_filter(lt.IOS_IMAGE_MEMORY_FOCUS)]
            result = app.run(f.binary.relative_to(f.root).as_posix(), arguments)
            self.assertTrue(result["transport_passed"])
            driver.return_value.close.assert_called_once()
        self.assertEqual(original, os.environ)
        self.assertNotIn("SIMCTL_CHILD_MallocScribble", json.dumps(result))

    def test_native_workload_receipts_keep_all_old_gates_and_distinguish_unsupported_profile(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups); f.setUp()
        f.write(lt.IOS_IMAGE_MEMORY_SOURCE, (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_bytes())
        f.plan = lt.plan(f.root, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        f.cases = [{"classname": lt.IOS_IMAGE_MEMORY_CLASS, "name": name, "status": "passed"}
                   for name in lt.IOS_IMAGE_MEMORY_METHODS]
        f.document["explicit_test_focus"] = lt.IOS_IMAGE_MEMORY_FOCUS
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=lt.case_counts(f.cases))
        f.modules[0]["testcases"] = f.xml_cases(f.cases); f.save()
        self.assertEqual([], f.collect()["errors"])
        self.assertFalse(f.document["image_memory_profile"]["profile_passed"])
        original = copy.deepcopy(f.document)
        for change in (
            lambda d: d.pop("image_memory_profile"),
            lambda d: d["image_memory_profile"].update(owned_ack_removed=False),
            lambda d: d["image_memory_profile"].update(signed_application_executable_sha256="f" * 64),
            lambda d: d["image_memory_profile"].update(simulator_udid="foreign"),
            lambda d: d["application_protocol"].pop("image_profile_observations"),
            lambda d: d["application_protocol"]["image_profile_observations"][1].update(rounds=True),
            lambda d: d["application_protocol"].update(completion={"runner_exit": 0, "worker_terminated": False}),
            lambda d: d["cleanup"].update(owned_app_absence_verified=False),
        ):
            f.document = copy.deepcopy(original); change(f.document); f.save()
            self.assertTrue(f.collect()["errors"])

    def test_one_host_selects_only_new_memory_cases_not_the_nine_accepted_cases(self):
        row, = matrix.matrix("ios-image-memory")["include"]
        self.assertEqual("ios-iphone", row["slot"])
        self.assertEqual("calf-ui", row["test-modules"])
        self.assertEqual(lt.IOS_IMAGE_MEMORY_FOCUS, row["test-focus"])
        plan = lt.plan(lt.ROOT, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        self.assertEqual(3, len(plan["expected"][0]["required_testcases"]))
        self.assertFalse(plan["complete_suite_requested"])
        selectors = lt.ui_application_focus_filter(lt.IOS_IMAGE_MEMORY_FOCUS).split(",")
        self.assertEqual(3, len(selectors))
        self.assertNotIn("UIImageConversionTest", ",".join(selectors))
        for values in (selectors, list(reversed(selectors))):
            self.assertEqual(lt.IOS_IMAGE_MEMORY_FOCUS, app.application_test_focus(
                sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(values)]))
        result = subprocess.run([lt.sys.executable, "-B", str(lt.ROOT / "scripts/ci/library_tests.py"),
                                 "plan", "--suite", "ios", "--module", "calf-ui",
                                 "--focus", lt.IOS_IMAGE_MEMORY_FOCUS], capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(plan, json.loads(result.stdout))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertEqual(360, app.application_timeout_seconds(lt.IOS_IMAGE_MEMORY_FOCUS))

    def test_real_memory_plan_owns_diagnostics_without_changing_other_commands(self):
        plan = lt.plan(lt.ROOT, "ios", only_modules=("calf-ui",), focus=lt.IOS_IMAGE_MEMORY_FOCUS)
        command = lt.gradle_command("ios", plan, "11111111-1111-1111-1111-111111111111")
        self.assertIn("-PnativecmpkitImageMemoryDiagnostics=true", command)
        self.assertEqual(3, command.count("--tests"))
        other = lt.plan(lt.ROOT, "ios", only_modules=("calf-ui",), focus=lt.IOS_SLIDER_TAP_FOCUS)
        self.assertNotIn("-PnativecmpkitImageMemoryDiagnostics=true", lt.gradle_command(
            "ios", other, "11111111-1111-1111-1111-111111111111"))
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError):
                lt.plan(lt.ROOT, suite, only_modules=modules, focus=lt.IOS_IMAGE_MEMORY_FOCUS)

    def test_profile_markers_require_exact_case_order_and_defer_until_real_pid(self):
        bundle = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
        p = app.NativeProtocol(bundle)
        p.feed(frames.ACTIVE)
        p.feed(frames.frame("testSuiteStarted", name=app.IMAGE_PROFILE_CASE[0]))
        p.feed(frames.frame("testStarted", name=app.IMAGE_PROFILE_CASE[1]))
        requests = []
        p.image_profile_request = requests.append
        p.feed("NATIVECMPKIT_IMAGE_PROFILE phase=ready")
        self.assertEqual([], requests)
        p.feed(bundle + ": 12345")
        self.assertEqual([12345], requests)
        p.feed("NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=23")
        p.feed(frames.frame("testFinished", name=app.IMAGE_PROFILE_CASE[1]))
        p.feed(frames.frame("testSuiteFinished", name=app.IMAGE_PROFILE_CASE[0]))
        p.feed(frames.COMPLETE)
        summary = p.finish(0)
        self.assertEqual(1, summary["counts"]["passed"])
        self.assertEqual([{"phase": "ready"}, {"phase": "complete", "rounds": 23}],
                         summary["image_profile_observations"])

    def test_missing_malformed_foreign_or_duplicate_profile_marker_never_passes(self):
        def protocol():
            p = app.NativeProtocol()
            p.feed(frames.ACTIVE)
            p.feed(frames.frame("testSuiteStarted", name=app.IMAGE_PROFILE_CASE[0]))
            p.feed(frames.frame("testStarted", name=app.IMAGE_PROFILE_CASE[1]))
            return p
        for marker in ("NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=0",
                       "NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=4097",
                       "NATIVECMPKIT_IMAGE_PROFILE phase=complete rounds=1",
                       "NATIVECMPKIT_IMAGE_PROFILE phase=anything"):
            with self.assertRaises(ValueError): protocol().feed(marker)
        p = protocol()
        with self.assertRaises(ValueError):
            p.feed(frames.frame("testFinished", name=app.IMAGE_PROFILE_CASE[1]))
        p = protocol(); p.feed("NATIVECMPKIT_IMAGE_PROFILE phase=ready")
        with self.assertRaises(ValueError): p.feed("NATIVECMPKIT_IMAGE_PROFILE phase=ready")
        with self.assertRaises(ValueError): app.NativeProtocol().feed("NATIVECMPKIT_IMAGE_PROFILE phase=ready")

    def test_new_native_fixture_uses_real_owned_objects_finite_workers_and_gc(self):
        source = (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_text()
        self.assertEqual(3, source.count("@Test"))
        for required in ("1024", "Worker.start", "requestTermination", "FutureState.COMPUTED",
                         "GC.collect()", "override fun createSnapshot", "super.createSnapshot(context)",
                         "CFStringCompare", "CGColorSpaceGetName", "asSkiaBitmap().close()",
                         "assertBalanced()", "4096", "NATIVECMPKIT_IMAGE_PROFILE"):
            self.assertIn(required, source)
        build = (lt.ROOT / "calf-ui/build.gradle.kts").read_text()
        self.assertIn('binaryOption("runtimeAssertionsMode", "panic")', build)
        self.assertIn('binaryOption("checkStateAtExternalCalls", "true")', build)
        self.assertIn('nativecmpkitImageMemoryDiagnostics', build)

    def test_native_srgb_name_check_uses_importable_typed_content_comparison(self):
        source = (lt.ROOT / lt.IOS_IMAGE_MEMORY_SOURCE).read_text()
        # Kotlin/Native 2.4.20's real CoreFoundationBase KLIB marks CFEqual
        # ERROR/"Unable to import this declaration". Compare the two actual
        # CFString contents, never pointer identity or just non-null presence.
        self.assertNotIn("CFEqual", source)
        self.assertIn("import platform.CoreFoundation.CFStringCompare", source)
        self.assertIn("import platform.CoreFoundation.kCFCompareEqualTo", source)
        self.assertIn("CFStringCompare(assertNotNull(CGColorSpaceGetName(space)), kCGColorSpaceSRGB, 0uL)", source)
        self.assertIn("kCFCompareEqualTo", source)


if __name__ == "__main__": unittest.main()
