"""Synthetic finite-recovery/source/readback guards; no Android or native outcomes."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import re
import tempfile
import time
import unittest

import android_camera_receiver as receiver
import android_device_tests as device
import library_tests as l
import workflow_matrix as w


HELPER = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedAlwaysFinish.kt"
FOCUS = "android-camera-real-restoration-dont-keep"
PROFILE = "android-camera-restoration-dont-keep"


def helper_source():
    return (l.ROOT / HELPER).read_text(encoding="utf-8")


def constant(source, name):
    matches = re.findall(r"const val " + re.escape(name) + r' = "([^"\r\n]*)"', source)
    if len(matches) != 1:
        raise ValueError("Missing or duplicate source-bound dump constant")
    return matches[0]


def native_dump(source, enabled=False):
    rows = [constant(source, "PROCESS_HEADER"), "  All known processes:"]
    if enabled:
        rows.append(constant(source, "ALWAYS_FINISH_ROW"))
    rows += [constant(source, "READINESS_ROW"), "  ServiceManager statistics:", "  mForceBackgroundCheck=false"]
    return "\n".join(rows)


def modeled_native_readback(source, text):
    """Source-bound ASCII boundary model, not execution of the Kotlin/native reader."""
    if len(text.encode("utf-8")) > 1_048_576 or any(c in text for c in "\r\x00\x1b"):
        raise ValueError("Unbounded or malformed query")
    rows = text.split("\n")
    header = constant(source, "PROCESS_HEADER")
    if not rows or rows[0] != header or rows.count(header) != 1:
        raise ValueError("Incomplete exact processes query")
    readiness = [i for i, row in enumerate(rows) if "mProcessesReady" in row]
    footers = [i for i, row in enumerate(rows) if "mForceBackgroundCheck" in row]
    if (len(readiness) != 1 or rows[readiness[0]] != constant(source, "READINESS_ROW") or
            len(footers) != 1 or footers[0] != len(rows) - 1 or readiness[0] >= footers[0] or
            not re.fullmatch(r"  mForceBackgroundCheck=(true|false)", rows[footers[0]])):
        raise ValueError("Missing or ambiguous complete-query boundary")
    fields = [i for i, row in enumerate(rows) if "mAlwaysFinishActivities" in row]
    if fields:
        if (len(fields) != 1 or rows[fields[0]] != constant(source, "ALWAYS_FINISH_ROW") or
                not 0 < fields[0] < readiness[0]):
            raise ValueError("Unknown or ambiguous native mode")
        return True
    return False


class CameraDontKeepFocusTests(unittest.TestCase):
    def plan(self):
        return l.plan(l.ROOT, "android-device", only_modules=("calf-camera-picker",), focus=FOCUS)

    def report(self, cases, *, marked=True, stale=False):
        plan = self.plan(); expected, = plan["expected"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / expected["report_directory"] / "TEST-modeled-dont-keep.xml"
            report.parent.mkdir(parents=True)
            report.write_text("<testsuite>" + "".join(
                '<testcase classname="' + c["classname"] + '" name="' + c["name"] + '">' +
                c.get("outcome", "") + "</testcase>" for c in cases) + "</testsuite>")
            now = time.time_ns()
            return l.collect_reports(root, plan, now + (10_000_000_000 if stale else -1_000_000_000),
                                     now + (11_000_000_000 if stale else 1_000_000_000),
                                     Counter({expected["task"]: 1}) if marked else Counter())

    def test_only_one_failed_method_is_selected_without_replaying_three_accepted_methods(self):
        plan = self.plan(); expected, = plan["expected"]
        self.assertEqual(FOCUS, l.ANDROID_CAMERA_DONT_KEEP_FOCUS)
        self.assertEqual(l.android_camera_restoration_identities(FOCUS), expected["required_testcases"])
        self.assertEqual([{"classname": l.ANDROID_CAMERA_RESTORATION_CLASS,
                           "name": "nativeDontKeepActivitiesRestoresOneReadableCapturedFile"}], expected["required_testcases"])
        self.assertEqual(l.ANDROID_CAMERA_RESTORATION_CLASS + "#" + expected["required_testcases"][0]["name"], expected["test_filter"])
        self.assertIn(HELPER, expected["test_source_files"])
        self.assertTrue(l.validate_test_focus(plan)); self.assertTrue(l.android_camera_receiver_required(plan))
        self.assertEqual(1, len(expected["required_testcases"])); self.assertFalse(plan["complete_suite_requested"])

    def test_original_four_method_focus_and_inventory_remain_available(self):
        self.assertEqual(4, len(l.android_camera_restoration_identities()))
        self.assertEqual(l.ANDROID_CAMERA_RESTORATION_CLASS, l.android_camera_restoration_filter(l.ANDROID_CAMERA_RESTORATION_FOCUS))
        self.assertEqual(11, len(w.matrix("all")["include"]))
        self.assertEqual(8, len(l.MINIMUM_MODULES["android-device"]))
        source = (l.ROOT / l.ANDROID_CAMERA_RESTORATION_SOURCE).read_text()
        self.assertEqual(list(l.ANDROID_CAMERA_RESTORATION_METHODS), re.findall(r"@Test\s+fun\s+(\w+)\s*\(\s*\)", source))

    def test_profile_is_one_owned_api35_camera_slot_and_preserves_diagnostics(self):
        row, = w.matrix(PROFILE)["include"]
        self.assertEqual(("android-device-api35", "35", "calf-camera-picker", FOCUS),
                         tuple(row[k] for k in ("slot", "emulator-api", "test-modules", "test-focus")))
        self.assertNotIn("serial-emulator-api", row)
        self.assertIn(FOCUS, l.ANDROID_CAMERA_FOCUSES)
        self.assertIn("focus in lt.ANDROID_CAMERA_FOCUSES", (l.ROOT / "scripts/ci/android_device_tests.py").read_text())
        self.assertIn("plan.get(\"explicit_test_focus\") not in lt.ANDROID_CAMERA_FOCUSES", (l.ROOT / "scripts/ci/android_camera_receiver.py").read_text())
        workflow = (l.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn(PROFILE, workflow.split("options: [", 1)[1].split("]", 1)[0].split(", "))
        with self.assertRaises(ValueError): device.validate_api_selection(23, ("calf-camera-picker",), FOCUS)

    def test_unknown_focus_wrong_suite_and_module_escape_are_refused(self):
        for suite, modules, focus in (("android-host", ("calf-camera-picker",), FOCUS),
                                      ("android-device", ("calf-io",), FOCUS),
                                      ("android-device", ("calf-camera-picker", "calf-io"), FOCUS),
                                      ("android-device", ("calf-camera-picker",), FOCUS + "-foreign")):
            with self.subTest(suite=suite, modules=modules, focus=focus):
                with self.assertRaises(ValueError): l.plan(l.ROOT, suite, only_modules=modules, focus=focus)
        with self.assertRaises(ValueError): l.android_camera_restoration_identities("foreign")
        with self.assertRaises(ValueError): l.android_camera_restoration_filter("foreign")

    def test_broad_filter_missing_helper_and_accepted_case_substitution_are_refused(self):
        plan = self.plan()
        variants = []
        bad = deepcopy(plan); bad["expected"][0]["test_filter"] = l.ANDROID_CAMERA_RESTORATION_CLASS; variants.append(bad)
        bad = deepcopy(plan); bad["expected"][0]["required_testcases"] = l.android_camera_restoration_identities()[1:]; variants.append(bad)
        bad = deepcopy(plan); bad["expected"][0]["test_source_files"].remove(HELPER); variants.append(bad)
        bad = deepcopy(plan); bad["complete_suite_requested"] = True; variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError): l.validate_test_focus(bad)

    def test_exact_fresh_one_case_xml_with_actual_task_marker_is_required(self):
        cases = self.plan()["expected"][0]["required_testcases"]
        self.assertFalse(self.report(cases)["errors"])
        self.assertTrue(self.report(cases, marked=False)["errors"])
        self.assertTrue(self.report(cases, stale=True)["errors"])

    def test_missing_extra_duplicate_and_accepted_only_xml_cannot_pass(self):
        cases = self.plan()["expected"][0]["required_testcases"]
        for variant in ([], cases * 2, l.android_camera_restoration_identities(),
                        l.android_camera_restoration_identities()[1:], cases + l.android_camera_provider_identities()):
            with self.subTest(variant=variant): self.assertTrue(self.report(variant)["errors"])

    def test_native_failure_and_skip_remain_failed_not_accepted(self):
        cases = self.plan()["expected"][0]["required_testcases"]
        for outcome in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(outcome=outcome): self.assertTrue(self.report([cases[0] | {"outcome": outcome}])["errors"])

    def test_gradle_plan_retains_owned_receiver_timeout_and_exact_class_method_filter(self):
        plan = self.plan(); expected, = plan["expected"]
        command = l.gradle_command("android-device", plan, android_serial=device.SERIAL)
        self.assertIn(expected["task"], command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.class=" + expected["test_filter"], command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.nativecmpkitOwnedCameraReceiver=true", command)
        self.assertIn("-Pandroid.testInstrumentationRunnerArguments.timeout_msec=120000", command)
        self.assertNotIn("-Pandroid.testInstrumentationRunnerArguments.class=" + l.ANDROID_CAMERA_RESTORATION_CLASS, command)


class CameraAlwaysFinishSourceTests(unittest.TestCase):
    def test_scalar_only_toggle_is_replaced_only_inside_the_dont_keep_branch(self):
        source = (l.ROOT / l.ANDROID_CAMERA_RESTORATION_SOURCE).read_text()
        branch = source.split("if (dontKeep) {", 1)[1].split("// The reporter", 1)[0]
        self.assertIn("OwnedAlwaysFinish(pm, originalFinish)", branch)
        self.assertIn("alwaysFinish = finishOwner", branch)
        self.assertLess(branch.index("alwaysFinish = finishOwner"), branch.index("finishOwner.arm()"))
        self.assertNotIn("settings put global always_finish_activities 1", source)
        self.assertIn('waitUntil { snapshot(prefName).integer("destroys") > 0 }', source)
        self.assertIn('assertEquals(true, snapshot(prefName)["nonFinishingDestroyed"])', source)

    def test_shell_identity_permission_and_api_are_checked_without_permission_or_policy_bypass(self):
        source = helper_source()
        for token in ("Build.VERSION.SDK_INT == 35", 'setOf("ranchu", "goldfish")',
                      "Process.myUid() / 100_000 == 0", 'getApplicationInfo("com.android.shell", 0).uid == 2000',
                      'checkPermission("android.permission.SET_ALWAYS_FINISH", "com.android.shell")'):
            self.assertIn(token, source)
        for forbidden in ("adoptShellPermissionIdentity", "setHiddenApiExemptions", "hidden_api_policy", "su ", "setprop "):
            self.assertNotIn(forbidden, source)

    def test_running_binder_signature_transaction_name_and_descriptor_are_verified_before_mutation(self):
        source = helper_source()
        for token in ('Class.forName("android.app.IActivityManager")',
                      'getDeclaredMethod("setAlwaysFinish", Boolean::class.javaPrimitiveType)',
                      "method.returnType == Void.TYPE", 'Class.forName("android.app.IActivityManager\\$Stub")',
                      'getDeclaredField("TRANSACTION_setAlwaysFinish")', "Modifier.isStatic(field.modifiers)",
                      "Modifier.isFinal(field.modifiers)", 'getDeclaredMethod("getDefaultTransactionName", Int::class.javaPrimitiveType)',
                      'name.invoke(null, transaction) == "setAlwaysFinish"', 'shell("service list", CONTROL_BYTES)',
                      "entries.single { it.second == \"activity\" }.third == SERVICE_DESCRIPTOR"):
            self.assertIn(token, source)
        self.assertIn('shell("service call activity $transaction i32 ${if (enabled) 1 else 0}", CONTROL_BYTES)', source)
        self.assertNotRegex(source, r"service call activity [0-9]")

    def test_complete_bounded_native_query_refuses_unknown_rows_without_exporting_process_bodies(self):
        source = helper_source()
        self.assertIn('shell("dumpsys activity processes", DUMP_BYTES)', source)
        self.assertIn("const val DUMP_BYTES = 1_048_576", source)
        self.assertIn("text.none { it == '\\r' || it == '\\u0000' || it == '\\u001b' }", source)
        for name in ("PROCESS_HEADER", "READINESS_ROW", "ALWAYS_FINISH_ROW"):
            self.assertIn(constant(source, name), source)
        self.assertIn("footer.single().index == lines.lastIndex", source)
        self.assertIn("readiness.single().index < footer.single().index", source)
        self.assertIn("check(fields.size <= 1)", source)
        self.assertIn("fields.single().value == ALWAYS_FINISH_ROW", source)
        self.assertNotIn("println(", source); self.assertNotIn("Log.", source)
        reader = (l.ROOT / l.ANDROID_CAMERA_RESTORATION_SOURCE).read_text()
        self.assertIn("result.size() + n <= maximumBytes", reader)
        self.assertIn('command == "dumpsys activity processes" && maximumBytes == 1_048_576', reader)

    def test_uncertain_arm_and_restoration_attempts_are_owned_before_their_ipcs(self):
        source = helper_source()
        arm = source.split("fun arm()", 1)[1].split("fun restore()", 1)[0]
        restore = source.split("fun restore()", 1)[1].split("private fun", 1)[0]
        self.assertLess(arm.index("mutationAttempted = true"), arm.index("setNative(true)"))
        self.assertLess(restore.index("restorationStarted = true"), restore.index("setNative(original.native)"))
        self.assertIn("check(!closed && !restorationStarted)", restore)
        self.assertIn("if (armCompleted) setOf(target)", restore)
        self.assertIn('setOf(original, State(original.native, "1"), target)', restore)
        self.assertIn("check(current in permitted)", restore)
        self.assertNotIn("catch (", source)

    def test_native_and_original_null_zero_or_one_are_restored_exactly_with_stable_readback(self):
        source = helper_source()
        restore = source.split("fun restore()", 1)[1].split("private fun", 1)[0]
        self.assertLess(restore.index("setNative(original.native)"), restore.index("settings delete global always_finish_activities"))
        self.assertIn('if (original.scalar == "null")', restore)
        self.assertIn('== "Deleted 1 rows"', restore)
        self.assertIn("check(readStableState() == original)", restore)
        self.assertIn('check(value in setOf("null", "0", "1"))', source)
        self.assertIn("check(first == second)", source)
        self.assertIn('check(original.native == (original.scalar == "1"))', source)
        self.assertIn("original.scalar == expectedOriginalScalar", source)
        self.assertNotIn("settings put global always_finish_activities", source)

    def test_exact_no_exception_reply_is_required_and_primary_cleanup_failures_are_preserved(self):
        source = helper_source()
        self.assertIn('Regex("""Result: Parcel\\(\\s*00000000\\s+\'\\.\\.\\.\\.\'\\s*\\)""").matches(reply)', source)
        caller = (l.ROOT / l.ANDROID_CAMERA_RESTORATION_SOURCE).read_text()
        self.assertIn("alwaysFinish?.let { owner -> cleanup { owner.restore() } }", caller)
        self.assertIn("primary.addSuppressed(failure)", caller)
        self.assertIn("cleanupFailure?.let { throw it }", caller)
        for forbidden in ("recreate()", "dispatchResult(", "grantUriPermission(", "performDestroy", "callActivityOnDestroy"):
            self.assertNotIn(forbidden, source)


class CameraAlwaysFinishBoundaryModelTests(unittest.TestCase):
    def test_source_bound_complete_true_and_false_queries_are_distinguished(self):
        source = helper_source()
        self.assertTrue(modeled_native_readback(source, native_dump(source, True)))
        self.assertFalse(modeled_native_readback(source, native_dump(source, False)))

    def test_missing_truncated_or_reordered_boundaries_cannot_be_false_by_omission(self):
        source = helper_source(); text = native_dump(source); rows = text.splitlines()
        for candidate in ("", "\n".join(rows[1:]), "\n".join(rows[:-1]), "\n".join(rows[:2] + rows[3:]),
                          "\n".join([rows[0], rows[-1], *rows[1:-1]]), text + "\ntrailing unknown output"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError): modeled_native_readback(source, candidate)

    def test_duplicate_or_unknown_native_field_and_boundary_rows_are_refused(self):
        source = helper_source(); text = native_dump(source, True)
        for candidate in (text.replace(constant(source, "ALWAYS_FINISH_ROW"), "  mAlwaysFinishActivities=false"),
                          text.replace(constant(source, "ALWAYS_FINISH_ROW"), "  mAlwaysFinishActivities=unknown"),
                          text.replace(constant(source, "ALWAYS_FINISH_ROW"), (constant(source, "ALWAYS_FINISH_ROW") + "\n") * 2),
                          text.replace(constant(source, "READINESS_ROW"), (constant(source, "READINESS_ROW") + "\n") * 2),
                          text.replace("mBooted=true", "mBooted=false"), text + "\n  mForceBackgroundCheck=false",
                          text.replace("mForceBackgroundCheck=false", "mForceBackgroundCheck=unknown")):
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValueError): modeled_native_readback(source, candidate)

    def test_unbounded_control_encoded_and_foreign_header_queries_are_refused(self):
        source = helper_source(); text = native_dump(source)
        for candidate in (text + "x" * 1_048_577, text.replace("processes)", "processes calf-camera-picker)"),
                          text.replace("\n", "\r\n"), text + "\x00", text + "\x1b"):
            with self.subTest(kind=len(candidate)):
                with self.assertRaises(ValueError): modeled_native_readback(source, candidate)


if __name__ == "__main__":
    unittest.main()
