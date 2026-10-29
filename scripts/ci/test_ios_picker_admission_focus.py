"""Finite selection/transport adversarial fixtures; NOT UIKit/Worker/library executions."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ios_ui_application as app
import library_tests as r
import workflow_matrix as m
import test_ios_picker_batch_focus as batch
import test_ios_ui_application as frames


def host_observations():
    return [{"phase": phase, "iteration": iteration, "main_thread": main_thread}
            for phase, iteration, main_thread in app.PICKER_HOST_STEPS]


def host_line(step):
    return (f'NATIVECMPKIT_PICKER_HOST phase={step["phase"]} iteration={step["iteration"]} '
            f'mainThread={str(step["main_thread"]).lower()}')


class IosPickerAdmissionFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-file-picker",), focus=r.IOS_PICKER_ADMISSION_FOCUS)

    def helper(self):
        helper = batch.IosPickerBatchTests("test_one_slot_exact_26_methods_no_replay_or_publishing_tasks")
        self.addCleanup(helper.doCleanups)
        return helper

    def fixture(self):
        f, binary, _, document = self.helper().fixture()
        f.write(r.IOS_DEFERRED_PRESENTATION_GROUP["source"], (r.ROOT / r.IOS_DEFERRED_PRESENTATION_GROUP["source"]).read_bytes())
        f.plan = self.plan(f.root)
        cases = [{"classname": g["classname"], "name": name, "status": "passed"}
                 for g in r.IOS_PICKER_ADMISSION_GROUPS for name in g["methods"]]
        document["explicit_test_focus"] = r.IOS_PICKER_ADMISSION_FOCUS
        document["application_protocol"].update(testcases=cases, counts=r.case_counts(cases),
                                                picker_host_observations=host_observations())
        f.document = document
        f.receipt_path = f.output / "native-picker-application" / batch.fixtures.TOKEN / "receipt.json"
        f.modules = [{"module": "calf-file-picker", "task": document["task"], "testcases": f.xml_cases(cases)}]
        f.save()
        return f

    def test_nine_changed_new_methods_keep_original26_and7_and_all_host_slots(self):
        row, = m.matrix("ios-picker-admission")["include"]
        self.assertEqual(("ios-iphone", "calf-file-picker", r.IOS_PICKER_ADMISSION_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(9, len(plan["expected"][0]["required_testcases"]))
        self.assertEqual(26, len(self.helper().plan()["expected"][0]["required_testcases"]))
        old = r.plan(r.ROOT, "ios", only_modules=("calf-file-picker",), focus=r.IOS_PICKER_RECOVERY_FOCUS)
        self.assertEqual(7, len(old["expected"][0]["required_testcases"]))
        selected = {(c["classname"], c["name"]) for c in r.ui_application_focus_identities(r.IOS_PICKER_ADMISSION_FOCUS)}
        original = {(c["classname"], c["name"]) for c in r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS)}
        self.assertEqual(19, len(original - selected))
        self.assertEqual(2, len(selected - original))
        self.assertEqual(11, len(m.matrix("all")["include"]))

    def test_exact_task_cli_and_native_filters_never_replay_foundation_or_unrelated_tasks(self):
        plan = self.plan()
        expected = plan["expected"][0]
        self.assertEqual(":calf-file-picker:" + r.IOS_APPLICATION_TASK, expected["task"])
        self.assertEqual("genuine-uikit-application", expected["native_test_host"])
        selectors = [v for g in r.IOS_PICKER_ADMISSION_GROUPS for method in g["methods"]
                     for v in ("--tests", g["classname"] + "." + method)]
        self.assertEqual(selectors, r.gradle_command("ios", plan, simulator=batch.fixtures.DEVICE)[-18:])
        self.assertNotIn("NativePickedCopyBoundaryTest", expected["test_filter"])
        self.assertNotIn("FileSaverStagingTest", expected["test_filter"])
        args = sorted(app.TEST_ARGUMENTS)
        self.assertEqual(r.IOS_PICKER_ADMISSION_FOCUS, app.application_test_focus(
            args + ["--ktest_gradle_filter=" + ",".join(reversed(expected["test_filter"].split(",")))]))
        process = subprocess.run([sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan", "--suite", "ios",
                                  "--module", "calf-file-picker", "--focus", r.IOS_PICKER_ADMISSION_FOCUS],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, process.returncode, process.stderr)

    def test_wrong_suite_module_missing_declaration_or_host_cannot_shrink_coverage(self):
        for suite, modules in (("desktop", ("calf-file-picker",)), ("ios", ("calf-ui",)), ("ios", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_PICKER_ADMISSION_FOCUS)
        f = self.fixture()
        self.assertTrue(r.validate_test_focus(f.plan))
        source = f.root / r.IOS_DEFERRED_PRESENTATION_GROUP["source"]
        original = source.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n"):
            source.write_text(changed)
            with self.assertRaises(ValueError): self.plan(f.root)
        source.write_text(original)
        (f.root / r.IOS_PICKER_APPLICATION_SOURCES[0]).unlink()
        with self.assertRaises(ValueError): self.plan(f.root)

    def test_missing_duplicate_old_selection_wrong_target_failures_skips_or_stale_XML_are_red(self):
        helper = self.helper()
        helper.plan = self.plan
        identities = r.ui_application_focus_identities(r.IOS_PICKER_ADMISSION_FOCUS)
        self.assertEqual([], helper.collect(identities)["errors"])
        self.assertEqual(9, helper.collect(identities)["totals"]["passed"])
        for cases in ([], identities[:-1], identities * 2,
                      r.ui_application_focus_identities(r.IOS_PICKER_RECOVERY_FOCUS),
                      r.ui_application_focus_identities(r.IOS_PICKER_BOUNDARY_FOCUS)):
            self.assertTrue(helper.collect(cases)["errors"])
        wrong = copy.deepcopy(identities)
        wrong[0]["name"] = wrong[0]["name"].replace("iosSimulatorArm64", "iosArm64")
        self.assertTrue(helper.collect(wrong)["errors"])
        for result in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(helper.collect(identities, outcome=result)["errors"])
        self.assertTrue(helper.collect(identities, markers=0)["errors"])

    def test_new_receipt_keeps_Worker_runtime_binary_cleanup_and_exact_host_phases(self):
        f = self.fixture()
        self.assertEqual([], f.collect()["errors"])
        for section, key, bad in (("cleanup", "owned_app_absence_verified", False),
                                   ("runtime_after", "source_revision", "b" * 40),
                                   ("application_protocol", "completion", {"runner_exit": 0, "worker_terminated": False})):
            old = f.document[section][key]
            f.document[section][key] = bad
            f.save()
            self.assertTrue(f.collect()["errors"])
            f.document[section][key] = old
        original = host_observations()
        for changed in ([], original[:-1], original * 2,
                        [{**original[0], "main_thread": True}, *original[1:]],
                        [{**original[0], "iteration": True}, *original[1:]],
                        [{**original[0], "private": "must-not-be-accepted"}, *original[1:]]):
            f.document["application_protocol"]["picker_host_observations"] = changed
            f.save()
            self.assertTrue(f.collect()["errors"])

    def test_owning_source_never_treats_nil_links_or_exception_as_rejection_acknowledgement(self):
        production = (r.ROOT / "calf-file-picker/src/iosMain/kotlin/com.mohamedrejeb.calf.picker/IosDialogPresentation.kt").read_text()
        admission = production.split("internal fun iosDialogHasNoPresentation", 1)[0]
        self.assertNotIn("session.presentationRejected()", admission)
        self.assertNotIn("if (iosDialogHasNoPresentation", admission)
        self.assertIn("present(controller, session::presentationCompleted)", admission)
        self.assertIn("session.finish()", admission)
        self.assertIn("presenter.presentViewController(controller, true, completed)", admission)
        self.assertNotIn("delay(", production)
        self.assertNotIn("Thread.sleep", production)
        test = (r.ROOT / r.IOS_DEFERRED_PRESENTATION_GROUP["source"]).read_text()
        for phrase in ("parent.presentViewController(controller, true, completed)", "assertNotNull(picker.delegate",
                       "assertEquals(0, cleanups)", "session.presentationCompletionObserved", "assertNull(owner.current)",
                       "assertSame(next, owner.current", "Source is never handed to UIKit"):
            self.assertIn(phrase, test)

    def test_real_export_requires_native_callback_and_photo_reports_error_before_weak_delegate_assertion(self):
        source = (r.ROOT / r.IOS_PICKER_BOUNDARY_GROUPS[2]["source"]).read_text()
        export = source.split("@Test fun cancellationDuringRealExport", 1)[1].split("@Test fun retainedPublicPhoto", 1)[0]
        self.assertIn("assertFalse(session.presentationCompletionObserved", export)
        self.assertIn("waitForNative { session.presentationCompletionObserved", export)
        self.assertNotIn("session.presentationCompleted()", export)
        self.assertNotIn("assertFalse(iosDialogHasNoPresentation(parent, picker)", export)
        photo = source.split("@Test fun retainedPublicPhoto", 1)[1]
        self.assertLess(photo.index("Live recomposition must not release"), photo.index("assertNotNull(picker.delegate)"))
        self.assertIn("val limits = listOf(2, 5, null, 1)", photo)
        self.assertIn("Live recomposition must not mutate an already shown native configuration", photo)


class PickerHostAndTransportDiagnosticsTests(unittest.TestCase):
    def begun(self):
        p = app.NativeProtocol()
        for line in (frames.ACTIVE, frames.frame("testSuiteStarted", name=app.PICKER_HOST_CASE[0]),
                     frames.frame("testStarted", name=app.PICKER_HOST_CASE[1])):
            p.feed(line)
        return p

    def test_exact_ten_host_phases_are_not_cases_until_actual_finished_frames_and_Worker_completion(self):
        p = self.begun()
        for step in host_observations(): p.feed(host_line(step))
        self.assertEqual(0, p.partial()["counts"]["passed"])
        self.assertEqual(host_observations(), p.partial()["picker_host_observations"])
        for line in (frames.frame("testFinished", name=app.PICKER_HOST_CASE[1]),
                     frames.frame("testSuiteFinished", name=app.PICKER_HOST_CASE[0]), frames.COMPLETE):
            p.feed(line)
        self.assertEqual(1, p.finish(0)["counts"]["passed"])

    def test_missing_duplicate_wrong_case_thread_order_or_private_host_fields_cannot_pass(self):
        first = host_line(host_observations()[0])
        for line in (first + " private=secret", first.replace("mainThread=false", "mainThread=true"),
                     first.replace("before-host", "restored"), first.replace("iteration=1", "iteration=2")):
            p = self.begun()
            with self.assertRaises(ValueError): p.feed(line)
            self.assertEqual([], p.picker_host_observations)
        p = self.begun(); p.feed(first)
        with self.assertRaises(ValueError): p.feed(first)
        p = self.begun()
        with self.assertRaises(ValueError): p.feed(frames.frame("testFinished", name=app.PICKER_HOST_CASE[1]))
        p = app.NativeProtocol()
        with self.assertRaises(ValueError): p.feed(first)

    def transport_failure(self, lines, protocol=None):
        p = protocol or app.NativeProtocol()
        out = SimpleNamespace(buffer=io.BytesIO())
        code = "import sys\n" + "\n".join("print(" + repr(line) + ",flush=True)" for line in lines)
        with tempfile.TemporaryDirectory() as directory, patch.object(app.lt, "ROOT", Path(directory)), \
                patch.object(app.sys, "stdout", out), \
                patch.object(app.shutil, "disk_usage", return_value=SimpleNamespace(free=10 * 1024**3)), \
                self.assertRaises(ValueError):
            app.forward_application([sys.executable, "-u", "-c", code], p, 5)
        return p.transport_observation

    def test_real_child_distinguishes_failed_feed_from_missing_footer_finalization_without_transcripts(self):
        malformed = self.transport_failure(["##teamcity[testStarted name='unterminated private secret"])
        self.assertEqual(("protocol-feed", "malformed-teamcity-frame"),
                         (malformed["failure_stage"], malformed["failure_reason"]))
        incomplete = self.transport_failure(frames.complete_lines()[:-1])
        self.assertEqual(("protocol-finish", "missing-worker-completion"),
                         (incomplete["failure_stage"], incomplete["failure_reason"]))
        self.assertEqual(0, incomplete["console_process_exit"])
        self.assertNotIn("private", json.dumps(malformed))
        self.assertNotIn("secret", json.dumps(malformed))

    def test_unknown_exception_body_cannot_become_a_retained_reason_or_weaken_failure(self):
        p = app.NativeProtocol()
        with patch.object(p, "feed", side_effect=ValueError("private transcript /private/file secret-token")):
            observed = self.transport_failure(["ignored controlled fixture"], p)
        self.assertEqual("protocol-feed", observed["failure_stage"])
        self.assertEqual("unclassified", observed["failure_reason"])
        self.assertNotIn("private", json.dumps(observed))
        self.assertNotIn("secret", json.dumps(observed))


if __name__ == "__main__":
    unittest.main()
