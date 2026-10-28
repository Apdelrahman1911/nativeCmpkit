"""Failed compact selection/diagnostic guards; synthetic tooling, not native tests."""
import copy
from pathlib import Path
import subprocess
import sys
import unittest

import ios_ui_application as app
import library_tests as r
import test_ios_application_receipts as receipts
import test_ios_ui_application as transport
import test_ui_date_bounds_focus as bounds
import workflow_matrix as matrix


def diagnostic(index, **changes):
    values = dict(phase=app.COMPACT_APPEARANCE_PHASES[index],
                  backgroundMatches="false", tintMatches="true",
                  attached=str(index in range(2, 7)).lower(), enabled="false",
                  rtl="true", dark="true", mainThread="true")
    values.update(changes)
    return "NATIVECMPKIT_COMPACT_APPEARANCE " + " ".join(f"{k}={v}" for k, v in values.items())


def observations():
    return [{"phase": phase, "background_matches": False, "tint_matches": True,
             "attached": index in range(2, 7), "enabled": False,
             "rtl": True, "dark": True, "main_thread": True}
            for index, phase in enumerate(app.COMPACT_APPEARANCE_PHASES)]


class CompactDateFocus(unittest.TestCase):
    def plan(self):
        return r.plan(r.ROOT, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_COMPACT_FOCUS)

    def collect(self, cases=None, **kwargs):
        fixture = bounds.DateBoundsFocus()
        fixture.plan = self.plan
        return fixture.collect(r.ui_application_focus_identities(r.UI_DATE_COMPACT_FOCUS)
                               if cases is None else cases, **kwargs)

    def test_one_failed_method_only_retains_the_real_application_and_full_declared_inventory(self):
        row, = matrix.matrix("ios-date-compact")["include"]
        self.assertEqual(("ios-iphone", "calf-ui", r.UI_DATE_COMPACT_FOCUS),
                         (row["slot"], row["test-modules"], row["test-focus"]))
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        item, = plan["expected"]
        self.assertEqual(":calf-ui:" + r.IOS_APPLICATION_TASK, item["task"])
        self.assertEqual("genuine-uikit-application", item["native_test_host"])
        self.assertEqual(1, len(item["required_testcases"]))
        self.assertEqual(r.UI_DATE_REPLACEMENT_CLASS + "." + r.UI_DATE_REPLACEMENT_METHODS[1], item["test_filter"])
        group, = r.ui_application_focus_groups(r.UI_DATE_COMPACT_FOCUS)
        self.assertEqual(r.UI_DATE_REPLACEMENT_METHODS, group["declared_methods"])
        self.assertEqual((r.UI_DATE_REPLACEMENT_METHODS[1],), group["methods"])

    def test_real_cli_gradle_and_transport_only_accept_the_exact_single_method(self):
        result = subprocess.run([sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"),
                                 "plan", "--suite", "ios", "--module", "calf-ui", "--focus", r.UI_DATE_COMPACT_FOCUS],
                                cwd=r.ROOT, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        command = r.gradle_command("ios", self.plan(), simulator=transport.DEVICE)
        self.assertEqual(1, command.count("--tests"))
        self.assertEqual(["--tests", self.plan()["expected"][0]["test_filter"]], command[-2:])
        exact = app.APPLICATION_FOCUS_ARGUMENTS[r.UI_DATE_COMPACT_FOCUS]
        full = sorted(app.TEST_ARGUMENTS)
        self.assertEqual(r.UI_DATE_COMPACT_FOCUS, app.application_test_focus(full + [exact]))
        for invalid in (exact + ".*", exact + ",foreign", exact.replace("gradle_filter", "filter")):
            with self.assertRaises(ValueError):
                app.application_test_focus(full + [invalid])

    def test_accepted_profiles_and_methods_are_not_silently_replayed_or_narrowed(self):
        for focus, count in ((r.UI_DATE_BOUNDS_FOCUS, 6), (r.UI_DATE_REPLACEMENT_FOCUS, 3),
                             (r.UI_DATE_IMPORTANT_FOCUS, 7)):
            self.assertEqual(count, len(r.plan(r.ROOT, "ios", only_modules=("calf-ui",),
                                              focus=focus)["expected"][0]["required_testcases"]))
        for profile in ("all", "ios", "ios-ui", "extended"):
            self.assertTrue(all("test-focus" not in row for row in matrix.matrix(profile)["include"]))
        self.assertEqual(1, self.collect()["totals"]["passed"])
        selected = r.ui_application_focus_identities(r.UI_DATE_COMPACT_FOCUS)
        accepted_other = r.ui_application_focus_identities(r.UI_DATE_REPLACEMENT_FOCUS)[0]
        for invalid in ([], [*selected, accepted_other], [*selected, *selected], [accepted_other]):
            self.assertTrue(self.collect(invalid)["errors"])

    def test_failure_skip_stale_and_missing_execution_remain_failures(self):
        case, = r.ui_application_focus_identities(r.UI_DATE_COMPACT_FOCUS)
        for status in ("failure", "error", "skipped"):
            self.assertTrue(self.collect([{**case, "status": status}])["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(age=10_000_000_000)["errors"])

    def test_raw_probe_does_not_change_the_existing_public_assertion_or_shared_replacement_body(self):
        source = (r.ROOT / r.UI_DATE_REPLACEMENT_SOURCE).read_text()
        self.assertIn("traceCompactNativeAppearance()\n        replacement(\"compact\")", source)
        self.assertIn("assertEquals(colors.containerColor.toUIColor(), view.backgroundColor)", source)
        self.assertIn("assertInitialized(first, colors, enabled = kind != \"compact\")", source)
        helper = (r.ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/datepicker/CompactNativeAppearanceDiagnostic.kt").read_text()
        self.assertIn("UIDatePickerBackend(", helper)
        self.assertIn("requireOwnedApplicationWindow()", helper)
        self.assertIn("finally {", helper)
        self.assertIn("picker.removeFromSuperview()", helper)
        self.assertIn("assertNull(picker.window", helper)
        self.assertNotIn("@Test", helper)


class CompactAppearanceProtocol(unittest.TestCase):
    def start(self, suite=app.COMPACT_APPEARANCE_CASE[0], method=app.COMPACT_APPEARANCE_CASE[1]):
        protocol = app.NativeProtocol()
        for line in (transport.ACTIVE, transport.frame("testSuiteStarted", name=suite),
                     transport.frame("testStarted", name=method)):
            protocol.feed(line)
        return protocol

    def finish(self, protocol, failed=False):
        suite, method = app.COMPACT_APPEARANCE_CASE
        if failed:
            protocol.feed(transport.frame("testFailed", name=method, message="synthetic failed assertion"))
        for line in (transport.frame("testFinished", name=method, duration="1"),
                     transport.frame("testSuiteFinished", name=suite), transport.COMPLETE):
            protocol.feed(line)
        return protocol.finish(0)

    def test_real_boolean_observations_are_retained_without_turning_a_failed_case_green(self):
        protocol = self.start()
        for index in range(len(app.COMPACT_APPEARANCE_PHASES)):
            protocol.feed(diagnostic(index))
        result = self.finish(protocol, failed=True)
        self.assertEqual(observations(), result["compact_appearance_observation"])
        self.assertEqual(1, result["counts"]["failures"])
        self.assertEqual(0, result["counts"]["passed"])

    def test_off_case_off_main_missing_attachment_and_unknown_fields_are_rejected(self):
        for protocol in (app.NativeProtocol(), self.start(method="inlineStateReplacementInitializesAllEqualSettings")):
            with self.assertRaises(ValueError):
                protocol.feed(diagnostic(0))
        for changes in ({"mainThread": "false"}, {"mainThread": "1"}, {"attached": "true"},
                        {"phase": "unknown"}, {"backgroundMatches": "private-value"}):
            with self.assertRaises(ValueError):
                self.start().feed(diagnostic(0, **changes))

    def test_duplicate_reordered_missing_and_unfinished_markers_cannot_certify_execution(self):
        for sequence in ((0, 0), (1,), (0, 2)):
            protocol = self.start()
            with self.assertRaises(ValueError):
                for index in sequence:
                    protocol.feed(diagnostic(index))
        protocol = self.start()
        protocol.feed(diagnostic(0))
        partial = protocol.partial()
        self.assertFalse(partial["complete_native_lifecycle"])
        self.assertEqual(0, partial["counts"]["executed"])
        with self.assertRaises(ValueError):
            self.finish(protocol)


class CompactDateApplicationEvidence(unittest.TestCase):
    def setUp(self):
        self.fixture = receipts.IosApplicationReceipts("test_exact_app_protocol_xml_runtime_binary_and_cleanup_are_required")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        f.write(r.UI_DATE_REPLACEMENT_SOURCE, (r.ROOT / r.UI_DATE_REPLACEMENT_SOURCE).read_bytes())
        f.plan = r.plan(f.root, "ios", only_modules=("calf-ui",), focus=r.UI_DATE_COMPACT_FOCUS)
        f.cases = [{"classname": app.COMPACT_APPEARANCE_CASE[0], "name": app.COMPACT_APPEARANCE_CASE[1], "status": "passed"}]
        f.document["explicit_test_focus"] = r.UI_DATE_COMPACT_FOCUS
        f.document["application_protocol"]["testcases"] = copy.deepcopy(f.cases)
        f.document["application_protocol"]["counts"] = r.case_counts(f.cases)
        f.document["application_protocol"].pop("image_lifetime_observation", None)
        f.document["application_protocol"]["compact_appearance_observation"] = observations()
        f.modules[0]["testcases"] = f.xml_cases(f.cases)
        f.save()

    def test_complete_native_diagnostics_retain_application_worker_runtime_and_cleanup_requirements(self):
        result = self.fixture.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual(observations(), result["ios_applications"][0]["compact_appearance_observation"])
        self.fixture.document["cleanup"]["owned_app_absence_verified"] = False
        self.fixture.save()
        self.assertTrue(self.fixture.collect()["errors"])

    def test_green_protocol_xml_without_exact_finite_main_thread_diagnostics_is_rejected(self):
        original = observations()
        for invalid in (None, [], original[:-1], original + [original[0]],
                        [{**original[0], "main_thread": False}, *original[1:]],
                        [{**original[0], "background_matches": 0}, *original[1:]],
                        [{**original[0], "attached": True}, *original[1:]],
                        [{**original[0], "phase": "private"}, *original[1:]]):
            self.fixture.document["application_protocol"]["compact_appearance_observation"] = invalid
            self.fixture.save()
            self.assertTrue(self.fixture.collect()["errors"])


if __name__ == "__main__":
    unittest.main()
