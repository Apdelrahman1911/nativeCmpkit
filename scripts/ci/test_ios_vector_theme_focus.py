"""Related-batch selection/driver/receipt fixtures, not actual Apple executions."""
from collections import Counter
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest

import ios_ui_application as app
import library_tests as r
import simulator_appearance
import test_ios_application_receipts as receipts
import test_ios_ui_application as owned
import workflow_matrix as matrix


class IosVectorThemeFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "ios", only_modules=("calf-ui",), focus=r.IOS_VECTOR_THEME_FOCUS)

    def fixture(self):
        f = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(f.doCleanups)
        f.setUp()
        f.write(r.IOS_VECTOR_THEME_SOURCE, (r.ROOT / r.IOS_VECTOR_THEME_SOURCE).read_bytes())
        f.plan = self.plan(f.root)
        f.cases = [{"classname": r.IOS_VECTOR_THEME_CLASS, "name": method, "status": "passed"}
                   for method in r.IOS_VECTOR_THEME_METHODS]
        f.document["explicit_test_focus"] = r.IOS_VECTOR_THEME_FOCUS
        f.document["application_protocol"].update(testcases=copy.deepcopy(f.cases), counts=r.case_counts(f.cases))
        f.document["application_protocol"]["vector_scale_observations"] = [
            {"density": 2.0, "native_screen": 2.0, "view": 2.0, "layer": 2.0}]
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()
        return f

    def protocol(self):
        p = app.NativeProtocol()
        p.feed(owned.ACTIVE)
        p.feed(owned.frame("testSuiteStarted", name=app.SYSTEM_APPEARANCE_CASE[0]))
        p.feed(owned.frame("testStarted", name=app.SYSTEM_APPEARANCE_CASE[1]))
        return p

    def marker(self, step):
        phase, index, style = step
        return f"NATIVECMPKIT_SYSTEM_APPEARANCE phase={phase} step={index} style={style}"

    def test_five_exact_new_methods_share_one_ipad_job_real_cli_and_no_accepted_test_replay(self):
        row, = matrix.matrix("ios-vector-theme")["include"]
        self.assertEqual(("ios-ipad", "calf-ui", r.IOS_VECTOR_THEME_FOCUS, "ipad"),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus", "simulator-kind")))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(5, len(plan["expected"][0]["required_testcases"]))
        self.assertTrue(r.validate_test_focus(plan))
        selectors = r.ui_application_focus_filter(r.IOS_VECTOR_THEME_FOCUS).split(",")
        self.assertEqual(5, len(selectors))
        self.assertTrue(all("NativeVectorThemeAcceptanceTest." in value for value in selectors))
        self.assertNotIn("UIImageConversionTest", ",".join(selectors))
        self.assertNotIn("ThemeOwnershipTest", ",".join(selectors))
        result = subprocess.run([r.sys.executable, "-B", str(r.ROOT / "scripts/ci/library_tests.py"), "plan",
                                 "--suite", "ios", "--module", "calf-ui", "--focus", r.IOS_VECTOR_THEME_FOCUS],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(plan, json.loads(result.stdout))
        for values in (selectors, list(reversed(selectors))):
            self.assertEqual(r.IOS_VECTOR_THEME_FOCUS, app.application_test_focus(
                sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + ",".join(values)]))
        self.assertEqual(300, app.application_timeout_seconds(r.IOS_VECTOR_THEME_FOCUS))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertIn(r.IOS_VECTOR_THEME_SOURCE, r.IOS_APPLICATION_SOURCES)
        self.assertIn(("utils.NativeVectorThemeAcceptanceTest", r.IOS_VECTOR_THEME_METHODS[-1]), r.IOS_APPLICATION_CASES)
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-file-picker",)), ("ios", None)):
            with self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.IOS_VECTOR_THEME_FOCUS)

    def test_missing_extra_unexecuted_duplicate_failed_skipped_or_foreign_xml_cannot_pass(self):
        plan = self.plan()
        identities = r.ui_application_focus_identities(r.IOS_VECTOR_THEME_FOCUS)
        def collect(cases, result="", marker=1):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); reports = root / plan["expected"][0]["report_directory"]
                reports.mkdir(parents=True)
                (reports / "TEST-synthetic.xml").write_text("<testsuite>" + "".join(
                    f'<testcase classname="{c["classname"]}" name="{c["name"]}">{result}</testcase>'
                    for c in cases) + "</testsuite>")
                now = time.time_ns()
                return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                         Counter({plan["expected"][0]["task"]: marker}), host_system="Darwin")
        self.assertEqual([], collect(identities)["errors"])
        for cases in ([], identities[:-1], identities * 2,
                      identities + [{**identities[0], "name": "unrelated"}],
                      [{**identities[0], "name": identities[0]["name"].replace("SimulatorArm64", "Arm64")}, *identities[1:]]):
            self.assertTrue(collect(cases)["errors"])
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            self.assertTrue(collect(identities, outcome)["errors"])
        self.assertTrue(collect(identities, marker=0)["errors"])

    def test_native_pass_requires_exact_real_changes_readbacks_restoration_and_all_old_lifecycle_gates(self):
        f = self.fixture()
        self.assertEqual([], f.collect()["errors"])
        original = copy.deepcopy(f.document)
        for transform in (
            lambda d: d["application_protocol"].pop("vector_scale_observations"),
            lambda d: d["application_protocol"]["vector_scale_observations"].append(
                d["application_protocol"]["vector_scale_observations"][0]),
            lambda d: d["application_protocol"]["vector_scale_observations"][0].update(native_screen=3.0),
            lambda d: d["application_protocol"]["vector_scale_observations"][0].update(density=True),
            lambda d: d.pop("system_appearance_driver"),
            lambda d: d["system_appearance_driver"].update(restored=False),
            lambda d: d["system_appearance_driver"]["steps"].pop(),
            lambda d: d["system_appearance_driver"]["controls"].reverse(),
            lambda d: d["system_appearance_driver"]["controls"][0].update(command=["sh", "-c", "anything"]),
            lambda d: d["application_protocol"].pop("system_appearance_observations"),
            lambda d: d["application_protocol"]["system_appearance_observations"].reverse(),
            lambda d: d["application_protocol"]["system_appearance_observations"][0].update(step=True),
            lambda d: d["application_protocol"]["completion"].update(worker_terminated=False),
            lambda d: d["cleanup"].update(owned_local_bundle_removed=False),
            lambda d: d["runtime_after"].update(source_revision="b" * 40),
        ):
            f.document = copy.deepcopy(original); transform(f.document); f.save()
            self.assertTrue(f.collect()["errors"])

    def test_every_native_phase_is_required_and_only_requests_trigger_finite_external_controls(self):
        p = self.protocol(); requests = []
        p.system_appearance_request = lambda step, style: requests.append((step, style))
        for step in app.SYSTEM_APPEARANCE_STEPS:
            p.feed(self.marker(step))
        p.feed(owned.frame("testFinished", name=app.SYSTEM_APPEARANCE_CASE[1]))
        p.feed(owned.frame("testSuiteFinished", name=app.SYSTEM_APPEARANCE_CASE[0]))
        p.feed(owned.COMPLETE)
        result = p.finish(0)
        self.assertEqual(list(simulator_appearance.REQUESTS), requests)
        self.assertEqual(1, result["counts"]["passed"])
        self.assertEqual(app.SYSTEM_APPEARANCE_STEPS, tuple(
            (s["phase"], s["step"], s["style"]) for s in result["system_appearance_observations"]))
        p = self.protocol()
        with self.assertRaises(ValueError):
            p.feed(owned.frame("testFinished", name=app.SYSTEM_APPEARANCE_CASE[1]))
        p = self.protocol(); p.feed(self.marker(app.SYSTEM_APPEARANCE_STEPS[0]))
        partial = p.partial()
        self.assertEqual(0, partial["counts"]["passed"])
        self.assertFalse(partial["complete_native_lifecycle"])
        self.assertIsNone(partial["completion"])

    def test_missing_reordered_duplicate_foreign_or_malformed_native_phase_is_refused(self):
        for invalid in (
            self.marker(app.SYSTEM_APPEARANCE_STEPS[1]),
            "NATIVECMPKIT_SYSTEM_APPEARANCE phase=request step=1 style=light",
            "NATIVECMPKIT_SYSTEM_APPEARANCE phase=request step=3 style=dark",
            "NATIVECMPKIT_SYSTEM_APPEARANCE phase=unknown step=1 style=dark",
            "NATIVECMPKIT_SYSTEM_APPEARANCE phase=request step=1 style=$(command)",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.protocol().feed(invalid)
        first = self.marker(app.SYSTEM_APPEARANCE_STEPS[0])
        with self.assertRaises(ValueError):
            app.NativeProtocol().feed(first)
        p = self.protocol(); p.feed(first)
        with self.assertRaises(ValueError):
            p.feed(first)

    def test_actual_run_caller_binds_focused_deadline_native_requests_and_original_appearance_cleanup(self):
        for initial in ("light", "dark"):
            f = owned.OwnedApplicationTests("test_owned_only_install_launch_readback_uninstall_and_local_cleanup")
            f.setUp()
            try:
                f.system_appearance = initial
                f.expected_timeout = 300
                def launch(argv, protocol, *, timeout):
                    self.assertEqual(300, timeout)
                    protocol.feed(owned.ACTIVE)
                    protocol.feed(owned.frame("testSuiteStarted", name=app.SYSTEM_APPEARANCE_CASE[0]))
                    protocol.feed(owned.frame("testStarted", name=app.SYSTEM_APPEARANCE_CASE[1]))
                    for step in app.SYSTEM_APPEARANCE_STEPS:
                        protocol.feed(self.marker(step))
                    protocol.feed(owned.frame("testFinished", name=app.SYSTEM_APPEARANCE_CASE[1]))
                    protocol.feed(owned.frame("testSuiteFinished", name=app.SYSTEM_APPEARANCE_CASE[0]))
                    protocol.feed(owned.COMPLETE)
                    return {"process_exit": 0, **protocol.finish(0)}
                args = sorted(app.TEST_ARGUMENTS) + ["--ktest_gradle_filter=" + r.ui_application_focus_filter(r.IOS_VECTOR_THEME_FOCUS)]
                result = f.fixture_run(arguments=args, launch=launch)
                self.assertTrue(result["transport_passed"])
                self.assertTrue(simulator_appearance.validate_receipt(result["system_appearance_driver"], owned.DEVICE))
                self.assertEqual(initial, f.system_appearance)
                self.assertTrue(result["cleanup"]["owned_app_absence_verified"])
                self.assertTrue(result["cleanup"]["owned_local_bundle_removed"])
            finally:
                f.doCleanups()

    def test_source_uses_actual_native_rendering_traits_modals_and_never_claims_window_override_as_system(self):
        source = (r.ROOT / r.IOS_VECTOR_THEME_SOURCE).read_text()
        self.assertEqual(5, source.count("@Test fun "))
        for text in ("UIImageView(frame", "UIImageRenderingModeAlwaysOriginal", "UIImageRenderingModeAlwaysTemplate",
                     "listOf(2f, 3f)", "drawViewHierarchyInRect", "CGContextRelease", "CGColorSpaceRelease",
                     "traitCollection.userInterfaceStyle", "calendarHost!!.applyColors(Color.Transparent, dayColor, Color.Cyan)",
                     "CalendarViewHost().also", "Color.Black.copy(alpha = .1f)", "BottomSheetManager(parent",
                     "UIModalPresentationPopover", "UIPopoverPresentationController", "UIUserInterfaceIdiomPad",
                     "NATIVECMPKIT_SYSTEM_APPEARANCE phase=request", "NATIVECMPKIT_SYSTEM_APPEARANCE phase=verified",
                     "driver-established actual initial light", "scope.cancel()"):
            self.assertIn(text, source)
        self.assertNotIn("Assume.", source)
        self.assertNotIn("Thread.sleep", source)
        # Actual Kotlin/UIKit metadata exposes idioms as Long constants, not enums.
        self.assertNotIn("UIUserInterfaceIdiom.UIUserInterfaceIdiomPad", source)
        # UIContentContainerProtocol contributes a read-only property; Kotlin's
        # UIViewController binding supplies the explicit Objective-C setter.
        self.assertIn("controller.setPreferredContentSize(CGSizeMake(380.0, 480.0))", source)
        self.assertNotIn("controller.preferredContentSize =", source)
        system = source.split("@Test fun " + r.IOS_VECTOR_THEME_METHODS[-1], 1)[1].split("private fun snapshot", 1)[0]
        self.assertNotIn("window.overrideUserInterfaceStyle =", system)
        f = self.fixture()
        path = f.root / r.IOS_VECTOR_THEME_SOURCE
        original = path.read_text()
        for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun unrelated() {}\n"):
            path.write_text(changed)
            with self.assertRaises(ValueError):
                self.plan(f.root)


if __name__ == "__main__":
    unittest.main()
