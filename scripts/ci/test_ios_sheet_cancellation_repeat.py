# SPDX-License-Identifier: Apache-2.0
"""Important NEW C2 selection/history controls only; ZERO UIKit executions."""
import hashlib
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow
import ios_modal_worker_source_projection as worker
import ios_sheet_repeat_source_projection as history
import ios_worker_completion_source_projection as completion_history

ROOT = Path(__file__).resolve().parents[2]
COMPILER = "scripts/ci/ios_sheet_repeat_compile.init.gradle.kts"
DEVICE = "11111111-2222-3333-4444-555555555555"


class SheetCancellationRepeatControls(unittest.TestCase):
    def test_both_same_operation_cases_observe_the_cancelled_animation_reset_and_fresh_await(self):
        source = (ROOT / library.IOS_SHEET_REPEAT_SOURCE).read_text()
        self.assertEqual(library.IOS_SHEET_REPEAT_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        show, hide = source.split("    @Test fun ")[1:]
        for body in (show, hide):
            for marker in ("assertFalse(cancelled.isCompleted)", "cancelled.cancel()",
                           "cancelled.isCompleted && cancelled.isCancelled",
                           "assertTrue(noOp.isCompleted)", "assertFalse(noOp.isCancelled)",
                           "reset.isCompleted", "assertFalse(reset.isCancelled)",
                           "assertFalse(repeated.isCompleted)", "repeated.isCompleted",
                           "assertFalse(repeated.isCancelled)", "sameNativeObject(originalController",
                           "runOnIdle { owner.dispose() }", "waitForNative { parent.presentedViewController == null }"):
                self.assertIn(marker, body)
            self.assertLess(body.index("cancelled.isCompleted && cancelled.isCancelled"), body.index("reset ="))
            self.assertLess(body.index("reset.isCompleted"), body.index("repeated ="))
            self.assertLess(body.index("assertFalse(repeated.isCompleted)"), body.index("waitForNative { repeated.isCompleted"))
        self.assertIn("repeated = owner.scope.launch { owner.state.show() }", show)
        self.assertIn("repeated = owner.scope.launch { owner.state.hide() }", hide)
        self.assertIn("parent.presentedViewController?.isBeingPresented() == true", show)
        self.assertIn("assertTrue(originalController.isBeingDismissed())", hide)
        for marker in ("!it.isBeingPresented() && !it.isBeingDismissed()", "state.detach(manager)",
                       "manager.dispose()", "scope.cancel()", "assertNull(state.iosSheetManager)"):
            self.assertIn(marker, source)
        self.assertNotRegex(source, r"@(Ignore|Disabled|IgnoredTest)\b|Thread\.sleep|delay\(|usleep\(|performSelector")

    def test_exact_two_method_plan_and_three_source_compiler_exclude_all_accepted_populations(self):
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_SHEET_REPEAT_FOCUS)
        required = library.ui_application_focus_identities(library.IOS_SHEET_REPEAT_FOCUS)
        self.assertEqual(2, len(required))
        self.assertEqual(required, plan["expected"][0]["required_testcases"])
        self.assertEqual(["iosSimulatorArm64ApplicationTest." + library.IOS_SHEET_REPEAT_CLASS],
                         list({item["classname"] for item in required}))
        self.assertTrue({item["name"] for item in required}.isdisjoint(
            {name + "[iosSimulatorArm64]" for name in (*library.IOS_MODAL_OWNERSHIP_METHODS,
             *library.IOS_MODAL_LIFECYCLE_METHODS, *library.IOS_WORKER_OWNERSHIP_METHODS, *library.IOS_MODAL_XCUI_METHODS)}))
        command = library.gradle_command("ios", plan, DEVICE)
        self.assertEqual(1, command.count(COMPILER))
        self.assertEqual([":calf-ui:iosSimulatorArm64ApplicationTest"] + [arg
            for name in library.IOS_SHEET_REPEAT_METHODS for arg in ("--tests", library.IOS_SHEET_REPEAT_CLASS + "." + name)],
            command[command.index(":calf-ui:iosSimulatorArm64ApplicationTest"):])
        compiler = (ROOT / COMPILER).read_text()
        paths = re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', compiler)
        self.assertEqual([library.IOS_SHEET_REPEAT_SOURCE,
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt"], paths)
        request = compiler.split("val applicationRequest", 1)[1].split("val permittedTasks", 1)[0]
        self.assertEqual(list(library.IOS_SHEET_REPEAT_METHODS), re.findall(r'"(cancelled\w+)"', request))
        for marker in ("common.setFrom(emptyList<Any>())", "actual.files.map { it.canonicalFile }.toSet() == files.toSet()",
                       '"native_tests_executed" to 0', '"production_source_sets_changed" to false'):
            self.assertIn(marker, compiler)
        self.assertNotIn("*", request)
        # A synthetic declaration mutation must be rejected before any compiler.
        real_safe = library.safe_path
        with tempfile.TemporaryDirectory(prefix="explicitly-synthetic-repeat-declaration-") as folder:
            mutated = Path(folder) / "case.kt"
            original = (ROOT / library.IOS_SHEET_REPEAT_SOURCE).read_text()
            for body in (original.replace("@Test fun", "@Ignore @Test fun", 1),
                         original.replace(library.IOS_SHEET_REPEAT_METHODS[0], "foreignCase", 1)):
                mutated.write_text(body)
                with patch.object(library, "safe_path", side_effect=lambda root, relative:
                        mutated if relative == library.IOS_SHEET_REPEAT_SOURCE else real_safe(root, relative)), self.assertRaises(ValueError):
                    library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_SHEET_REPEAT_FOCUS)

    def test_profile_reserves_one_real_iphone_and_refuses_other_hosts_or_modules(self):
        profile = "ios-sheet-cancellation-repeat"
        self.assertEqual({"include": [{"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
            "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-ui",
            "test-focus": library.IOS_SHEET_REPEAT_FOCUS}]}, workflow.matrix(profile))
        for slots in (("ios-ipad",), ("desktop-macos-arm64",), ("ios-iphone", "ios-ipad")):
            with patch.dict(workflow.PROFILES, {profile: slots}), self.assertRaises(ValueError):
                workflow.matrix(profile)
        with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError):
            workflow.matrix(profile)
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, library.IOS_SHEET_REPEAT_FOCUS))
        source = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("ios-sheet-cancellation-repeat", source)
        self.assertIn("permissions:\n  contents: read\n", source)
        self.assertIn("persist-credentials: false", source)

    def test_seven_exact_additive_fragments_preserve_every_old_worker_pin_and_refuse_mutation(self):
        bindings = history._bindings()
        self.assertEqual({".github/workflows/gradle.yml", "scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py"}, set(bindings))
        self.assertEqual(7, sum(len(binding["fragments"]) for binding in bindings.values()))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            stage = completion_history.current_source_before_worker_completion(relative, current)
            previous = history.current_source_before_sheet_repeat(relative, stage)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_sheet_repeat(relative, previous))
            forward = previous
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(stage, forward)
            self.assertEqual(worker.source_before_modal_worker(relative, previous),
                             worker.current_source_before_modal_worker(relative, current))
            for changed in (previous, stage + b"\n", stage[:-1], stage.replace(b"\n", b"\r\n"),
                            b"", None, bytearray(stage)):
                with self.assertRaises(ValueError): history.current_source_before_sheet_repeat(relative, changed)
            for changed in (stage, current + b"\n", current[:-1], current.replace(b"\n", b"\r\n"),
                            b"", None, bytearray(current)):
                with self.assertRaises(ValueError): completion_history.current_source_before_worker_completion(relative, changed)
        self.assertEqual("8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48",
                         hashlib.sha256(worker.SPEC_PATH.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory(prefix="explicitly-synthetic-repeat-manifest-") as folder:
            changed = Path(folder) / "changed.json"; changed.write_bytes(history.SPEC_PATH.read_bytes() + b"\n")
            with patch.object(history, "SPEC_PATH", changed), self.assertRaises(ValueError): history._bindings()
            linked = Path(folder) / "linked.json"; linked.symlink_to(changed)
            with patch.object(history, "SPEC_PATH", linked), self.assertRaises(ValueError): history._bindings()


if __name__ == "__main__":
    unittest.main()
