"""Finite recovery/source/protocol tooling fixtures; NOT real UIKit/Worker/library passes."""
import copy
from pathlib import Path
import subprocess
import unittest

import ios_ui_application as app
import library_tests as r
import workflow_matrix as m
import test_ios_picker_batch_focus as batch
import test_ios_ui_application as frames


class IosPickerRecoveryTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-file-picker",), focus=r.IOS_PICKER_RECOVERY_FOCUS)

    def helper(self):
        helper = batch.IosPickerBatchTests("test_one_slot_exact_26_methods_no_replay_or_publishing_tasks")
        self.addCleanup(helper.doCleanups)
        return helper

    def test_seven_changed_host_and_runtime_methods_disjoint_from_19_completed_methods(self):
        row, = m.matrix("ios-picker-recovery")["include"]
        self.assertEqual(("ios-iphone", "calf-file-picker", r.IOS_PICKER_RECOVERY_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        selected = self.plan()["expected"][0]
        self.assertEqual(7, len(selected["required_testcases"]))
        self.assertFalse(self.plan()["complete_suite_requested"])
        self.assertEqual(26, len(self.helper().plan()["expected"][0]["required_testcases"]))
        old = {(c["classname"], c["name"]) for c in r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS)}
        recovery = {(c["classname"], c["name"]) for c in selected["required_testcases"]}
        self.assertEqual(19, len(old - recovery))
        self.assertEqual(7, len(recovery & old))
        self.assertEqual({r.IOS_PICKER_BOUNDARY_GROUPS[0]["classname"], r.IOS_PICKER_BOUNDARY_GROUPS[2]["classname"]},
                         {c["classname"].removeprefix(r.IOS_APPLICATION_TASK + ".") for c in selected["required_testcases"]})
        self.assertEqual(r.IOS_PICKER_BOUNDARY_GROUPS[0], r.IOS_PICKER_RECOVERY_GROUPS[0])
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_exact_command_and_cli_keep_native_application_not_standalone_or_unrelated_replay(self):
        plan = self.plan()
        expected = plan["expected"][0]
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, expected["task"])
        self.assertEqual("genuine-uikit-application", expected["native_test_host"])
        selectors = [v for g in r.IOS_PICKER_RECOVERY_GROUPS for method in g["methods"]
                     for v in ("--tests", g["classname"] + "." + method)]
        self.assertEqual(selectors, r.gradle_command("ios", plan, simulator=batch.fixtures.DEVICE)[-14:])
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-file-picker", "--focus", r.IOS_PICKER_RECOVERY_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("FileSaverStagingTest", expected["test_filter"])
        self.assertNotIn("NativePickedCopyBoundaryTest", expected["test_filter"])

    def test_declaration_host_drift_or_wrong_suite_cannot_reduce_recovery_coverage(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PICKER_RECOVERY_FOCUS)
        f, _, _, _ = self.helper().fixture()
        self.assertTrue(r.validate_test_focus(self.plan(f.root)))
        source = f.root / r.IOS_PICKER_RECOVERY_GROUPS[0]["source"]
        original = source.read_text()
        source.write_text(original.replace("@Test", "@IgnoredTest", 1))
        with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original)
        (f.root / r.IOS_PICKER_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)

    def test_recovery_missing_duplicate_wrong_target_failed_skipped_or_old_26_XML_is_not_a_pass(self):
        helper = self.helper()
        helper.plan = self.plan
        identities = r.ui_application_focus_identities(r.IOS_PICKER_RECOVERY_FOCUS)
        self.assertEqual(7, helper.collect(identities)["totals"]["passed"])
        self.assertEqual([], helper.collect(identities)["errors"])
        old = r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS)
        for cases in ([], identities[:-1], identities * 2, old):
            self.assertTrue(helper.collect(cases)["errors"])
        wrong = copy.deepcopy(identities); wrong[0]["name"] = wrong[0]["name"].replace("iosSimulatorArm64", "iosArm64")
        self.assertTrue(helper.collect(wrong)["errors"])
        for result in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(helper.collect(identities, outcome=result)["errors"])
        self.assertTrue(helper.collect(identities, markers=0)["errors"])

    def test_exact_recovery_receipt_still_requires_protocol_Worker_runtime_binary_and_cleanup(self):
        f, _, _, document = self.helper().fixture()
        f.plan = self.plan(f.root)
        cases = [{"classname": g["classname"], "name": name, "status": "passed"}
                 for g in r.IOS_PICKER_RECOVERY_GROUPS for name in g["methods"]]
        document["explicit_test_focus"] = r.IOS_PICKER_RECOVERY_FOCUS
        document["application_protocol"].update(testcases=cases, counts=r.case_counts(cases))
        f.document = document
        f.receipt_path = f.output / "native-picker-application" / batch.fixtures.TOKEN / "receipt.json"
        f.modules = [{"module": "calf-file-picker", "task": document["task"], "testcases": f.xml_cases(cases)}]
        f.save()
        accepted = f.collect()
        self.assertEqual([], accepted["errors"])
        self.assertEqual(7, accepted["ios_applications"][0]["counts"]["passed"])
        for section, key, value in (("cleanup", "owned_app_absence_verified", False),
                                     ("cleanup", "owned_app_stopped_verified", False),
                                     ("runtime_after", "source_revision", "b" * 40)):
            before = f.document[section][key]
            f.document[section][key] = value; f.save()
            self.assertTrue(f.collect()["errors"])
            f.document[section][key] = before
        f.document["application_protocol"]["lifecycle_failure_observation"] = {"stage": "runner_error", "error_type": "IllegalStateException"}
        f.save(); self.assertTrue(f.collect()["errors"])
        del f.document["application_protocol"]["lifecycle_failure_observation"]
        f.document["application_protocol"]["completion"]["worker_terminated"] = False
        f.save(); self.assertTrue(f.collect()["errors"])

    def test_picker_projection_observes_exact_forward_ancestor_and_back_links_on_every_safe_point(self):
        path = r.ROOT / "calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/IosDialogPresentation.kt"
        source = path.read_text()
        observation = source.split("internal fun iosDialogHasNoPresentation", 1)[1].split("private fun dismissOwnedIosDialog", 1)[0]
        for phrase in ("check(NSThread.isMainThread)", "controller.presentingViewController != null",
                       "controller.isBeingPresented()", "controller.isBeingDismissed()",
                       "presented.objcPtr() == controller.objcPtr()", "ancestor = ancestor.parentViewController"):
            self.assertIn(phrase, observation)
        self.assertEqual(2, source.count("iosDialogHasNoPresentation(presenter, controller)"))
        self.assertNotIn(".hasNoPresentation()", source)
        self.assertNotIn("Thread.sleep", source)
        self.assertNotIn("delay(", source)
        self.assertIn("presenter.presentViewController(controller, true, completed)", source)
        self.assertIn("present(controller, session::presentationCompleted)", source)
        self.assertNotIn("session.presentationRejected()", source)
        self.assertIn("controller.dismissViewControllerAnimated(false, completed)", source)

    def test_changed_host_requires_real_appearance_without_replacing_rendering_or_old_ownership_checks(self):
        host = (r.ROOT / r.IOS_PICKER_APPLICATION_SOURCES[0]).read_text()
        self.assertIn("override fun viewDidAppear(animated: Boolean)", host)
        self.assertIn("override fun viewWillDisappear(animated: Boolean)", host)
        self.assertIn("ComposeUIViewController(configure = { delegate = lifecycle })", host)
        self.assertIn("rootHasAppeared && sameNativeObject(controller.view.window, window)", host)
        self.assertIn("committedGeneration == generation.intValue", host)
        self.assertIn("Recomposer.runningRecomposers.value.none { it.hasPendingWork }", host)
        self.assertIn('check(sameNativeObject(window.rootViewController, controller)) { "Refuse cleanup of a foreign root" }', host)
        self.assertIn("owned root disappearance after restoration", host)
        self.assertNotIn("enforceStrictPlistSanityCheck", host)
        self.assertNotIn("parallelRendering", host)
        self.assertIn("BasicText(text.value)", (r.ROOT / r.IOS_PICKER_APPLICATION_SOURCES[1]).read_text())


class NativeFailureAndPickerDiagnosticTests(unittest.TestCase):
    def begun(self, method="cancellationDuringRealExportPresentationWaitsForNativeCompletionBeforeRemovingStaging"):
        protocol = app.NativeProtocol()
        for line in (frames.ACTIVE, frames.frame("testSuiteStarted", name="com.mohamedrejeb.calf.picker.IosPickerRuntimeOwnershipTest"),
                     frames.frame("testStarted", name=method)):
            protocol.feed(line)
        return protocol

    def admission(self, phase="export-initial", iteration=0):
        return (f"NATIVECMPKIT_PICKER_ADMISSION phase={phase} iteration={iteration} "
                "backlink=false presenting=false dismissing=false forward=true noPresentation=false")

    def test_known_runner_termination_timeout_or_nonzero_completion_is_retained_but_never_accepted(self):
        for line, stage in (("NATIVECMPKIT_UIKIT_RUNNER_ERROR type=IllegalStateException", "runner_error"),
                            ("NATIVECMPKIT_UIKIT_TERMINATION_ERROR type=RuntimeException", "termination_error"),
                            ("NATIVECMPKIT_UIKIT_TIMEOUT workerTerminationVerified=false", "timeout"),
                            (frames.COMPLETE.replace("runnerExit=0", "runnerExit=1"), "runner_completion")):
            protocol = self.begun()
            with self.assertRaises(ValueError): protocol.feed(line)
            partial = protocol.partial()
            self.assertEqual(stage, partial["lifecycle_failure_observation"]["stage"])
            self.assertFalse(partial["complete_native_lifecycle"])
            self.assertEqual(0, partial["counts"]["executed"])
            with self.assertRaises(ValueError): protocol.feed(frames.COMPLETE)
            with self.assertRaises(ValueError): protocol.finish(0)

    def test_unknown_private_malformed_or_inactive_failure_marker_is_not_retained(self):
        for line in ("NATIVECMPKIT_UIKIT_RUNNER_ERROR type=IllegalStateException message=private-path",
                     "NATIVECMPKIT_UIKIT_RUNNER_ERROR type=" + "a" * 81,
                     "NATIVECMPKIT_UIKIT_UNKNOWN private-message", "NATIVECMPKIT_UIKIT_RUNNER_ERROR type=/private/file"):
            protocol = self.begun()
            with self.assertRaises(ValueError): protocol.feed(line)
            self.assertIsNone(protocol.lifecycle_failure_observation)
        protocol = app.NativeProtocol()
        with self.assertRaises(ValueError): protocol.feed("NATIVECMPKIT_UIKIT_RUNNER_ERROR type=IllegalStateException")
        self.assertIsNone(protocol.lifecycle_failure_observation)

    def test_exact_finite_admission_observations_are_diagnostics_not_finished_cases(self):
        protocol = self.begun(); protocol.feed(self.admission())
        observation, = protocol.partial()["picker_admission_observations"]
        self.assertEqual({"phase": "export-initial", "iteration": 0, "backlink": False, "presenting": False,
                          "dismissing": False, "forward": True, "no_presentation": False}, observation)
        self.assertEqual(0, protocol.partial()["counts"]["passed"])
        with self.assertRaises(ValueError): protocol.feed(self.admission())
        photo = self.begun("retainedPublicPhotoLauncherUsesFourNativeConfigurationSnapshotsAndCurrentCallback")
        for i in range(1, 5): photo.feed(self.admission("photo-initial", i))
        self.assertEqual(4, len(photo.partial()["picker_admission_observations"]))
        self.assertEqual(0, photo.partial()["counts"]["passed"])
        with self.assertRaises(ValueError): photo.feed(self.admission("photo-initial", 5))

    def test_admission_cannot_cross_case_or_accept_missing_reordered_malformed_or_private_fields(self):
        for line in (self.admission("photo-initial", 1), self.admission(iteration=1),
                     self.admission() + " private=secret", self.admission().replace("forward=true", "forward=1")):
            protocol = self.begun()
            with self.assertRaises(ValueError): protocol.feed(line)
            self.assertEqual([], protocol.picker_admission_observations)
        photo = self.begun("retainedPublicPhotoLauncherUsesFourNativeConfigurationSnapshotsAndCurrentCallback")
        with self.assertRaises(ValueError): photo.feed(self.admission("photo-initial", 2))
        self.assertEqual([], photo.picker_admission_observations)


if __name__ == "__main__":
    unittest.main()
