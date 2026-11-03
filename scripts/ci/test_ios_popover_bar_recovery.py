# SPDX-License-Identifier: Apache-2.0
"""Important failed-case source/receipt controls; ZERO UIKit/native executions."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]
FOCUS = "ui-native-popover-bar-recovery"
METHOD = "nativeBarButtonAndDetachedOrMissingViewUseTheDocumentedFallback"
CLASS = "com.mohamedrejeb.calf.ui.dialog.NativePopoverAnchorTest"
NATIVE = "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativePopoverAnchorTest.kt"
INIT = "scripts/ci/ios_popover_bar_compile.init.gradle.kts"
SIMULATOR = "726D52AF-426A-408A-974D-CA8B9BE8A479"


class PopoverBarRecoveryControls(unittest.TestCase):
    def test_each_real_host_selects_only_the_failed_case_not_four_accepted_methods(self):
        for profile, kind in (("ios-popover-bar-recovery", "iphone"), ("ios-popover-bar-ipad-recovery", "ipad")):
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26", "arch": "arm64",
                                           "python": "python3", "simulator-kind": kind,
                                           "test-modules": "calf-ui", "test-focus": FOCUS}]}, workflow.matrix(profile))
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=FOCUS)
        self.assertEqual([{"classname": "iosSimulatorArm64ApplicationTest." + CLASS,
                           "name": METHOD + "[iosSimulatorArm64]"}], plan["expected"][0]["required_testcases"])
        self.assertFalse(plan["complete_suite_requested"])
        self.assertIn("NOT actual OS", plan["scope"])

    def test_exact_four_source_compiler_and_one_filter_leave_full_old_routes_intact(self):
        import ios_popover_anchor_plan as old
        import ios_popover_bar_recovery_plan as compiler
        self.assertEqual(old.SOURCES, compiler.SOURCES)
        source = (ROOT / INIT).read_text()
        self.assertEqual(list(old.SOURCES), re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', source))
        self.assertIn('common.setFrom(emptyList<Any>())', source)
        self.assertIn('"native_tests_executed" to 0', source)
        self.assertEqual(1, source.count('"' + METHOD + '"'))
        for name in library.IOS_POPOVER_ANCHOR_METHODS:
            if name != METHOD:
                self.assertNotIn('"' + name + '"', source)
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=FOCUS)
        command = library.gradle_command("ios", plan, SIMULATOR)
        self.assertEqual(1, command.count(INIT))
        self.assertEqual([CLASS + "." + METHOD], [command[i + 1] for i, value in enumerate(command) if value == "--tests"])
        group = library.ui_application_focus_groups(FOCUS)[0]
        self.assertEqual(library.IOS_POPOVER_ANCHOR_METHODS, group["declared_methods"])
        self.assertEqual((METHOD,), group["methods"])
        for profile in ("ios-popover-anchor", "ios-popover-anchor-ipad"):
            self.assertEqual(old.FOCUS, workflow.matrix(profile)["include"][0]["test-focus"])
        self.assertEqual(5, len(library.ui_application_focus_identities(old.FOCUS)))

    def test_disabled_foreign_suite_modules_host_and_extra_case_refuse(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, FOCUS))
        for profile in ("ios-popover-bar-recovery", "ios-popover-bar-ipad-recovery"):
            with patch.dict(workflow.PROFILES, {profile: ("desktop-macos-arm64",)}), self.assertRaises(ValueError):
                workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError):
                workflow.matrix(profile)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "native.kt"
            ordinary = library.safe_path
            def controlled(root, relative):
                return target if relative == NATIVE else ordinary(root, relative)
            for mutation in ("@Ignore\nclass NativePopoverAnchorTest", "@Disabled\nclass NativePopoverAnchorTest"):
                target.write_text((ROOT / NATIVE).read_text().replace("class NativePopoverAnchorTest", mutation, 1))
                with patch.object(library, "safe_path", controlled), self.assertRaisesRegex(ValueError, "enabled native declarations"):
                    library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=FOCUS)

    def test_bar_identity_and_window_ownership_replace_only_unsupported_nil_postcondition(self):
        source = (ROOT / NATIVE).read_text()
        body = source.split("@Test fun " + METHOD, 1)[1].split("    @Test fun", 1)[0]
        head, tail = body.split("toolbar.removeFromSuperview()", 1)
        self.assertNotIn("assertNull(popover.sourceView)", head)
        for token in ("sameNativeObject(bar, popover.barButtonItem)", "val nativeSource = popover.sourceView",
                      "nativeSource == null || sameNativeObject(parent.view, nativeSource)",
                      "sameNativeObject(parent.view.window, bar.customView?.window)",
                      "assertEquals(UIPopoverArrowDirectionAny, popover.permittedArrowDirections)"):
            self.assertIn(token, head)
        self.assertIn("alternative", head)
        self.assertEqual(3, tail.count("manager.updateDialogProperties()"))
        self.assertIn("assertNull(popover.barButtonItem)", tail)
        self.assertIn("assertEquals(0uL, popover.permittedArrowDirections)", tail)
        self.assertIn("if (managerReady) manager.dispose()", tail)
        self.assertIn("waitForNative { parent.presentedViewController == null }", tail)

    def test_new_fresh_receipt_admits_only_exact_compiler_not_native_acceptance(self):
        import ios_popover_bar_recovery_plan as compiler
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in compiler.SOURCES:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())
            target = root / compiler.RECEIPT; target.parent.mkdir(parents=True, exist_ok=True)
            document = {"task": ":calf-ui:compileTestKotlinIosSimulatorArm64", "focus": FOCUS,
                        "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in compiler.SOURCES},
                        "effective_sources": list(compiler.SOURCES), "excluded_unrelated_test_sources": True,
                        "production_source_sets_changed": False, "native_tests_executed": 0,
                        "scope": "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes"}
            now = time.time_ns(); target.write_text(json.dumps(document)); os.utime(target, ns=(now, now))
            self.assertTrue(compiler.validate_compilation(root, now - 1000000000, now + 1000000000))
            for key, value in (("focus", library.IOS_POPOVER_ANCHOR_FOCUS), ("native_tests_executed", False),
                               ("native_tests_executed", 1), ("production_source_sets_changed", True),
                               ("effective_sources", list(compiler.SOURCES) + [NATIVE]), ("unexpected", 0)):
                changed = copy.deepcopy(document); changed[key] = value; target.write_text(json.dumps(changed)); os.utime(target, ns=(now, now))
                self.assertFalse(compiler.validate_compilation(root, now - 1000000000, now + 1000000000), (key, value))
            target.write_text(json.dumps(document)); os.utime(target, ns=(now - 3000000000, now - 3000000000))
            self.assertFalse(compiler.validate_compilation(root, now, now + 1000000000))

    def test_collector_cannot_promote_bar_results_without_new_exact_receipt(self):
        source = (ROOT / "scripts/ci/library_tests.py").read_text()
        body = source.split("if test_plan.get(\"explicit_test_focus\") == IOS_POPOVER_BAR_RECOVERY_FOCUS:", 2)[-1]
        self.assertIn("ios_popover_bar_recovery_plan.validate_compilation(root, started_ns, ended_ns)", body)
        self.assertIn("failed bar-anchor case requires its fresh exact four-source compiler receipt", body)
        self.assertNotIn("ios_popover_bar_recovery_source_projection", source)
        self.assertNotIn("ios_popover_bar_recovery_plan", (ROOT / "scripts/ci/ios_ui_application.py").read_text())

    def test_exact_new_fragments_roundtrip_keep_all_four_accepted_method_bodies_and_old_pins(self):
        import ios_popover_bar_recovery_source_projection as recovery
        import ios_popover_anchor_source_projection as old
        bindings = recovery._bindings()
        self.assertEqual(6, len(bindings))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = recovery.current_source_before_bar_recovery(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertIs(previous, recovery.source_before_bar_recovery(relative, previous))
            forward = previous
            for fragment in binding["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, forward)
        previous = recovery.current_source_before_bar_recovery(NATIVE, (ROOT / NATIVE).read_bytes()).decode()
        current = (ROOT / NATIVE).read_text()
        for method in library.IOS_POPOVER_ANCHOR_METHODS:
            if method != METHOD:
                def body(source): return source.split("@Test fun " + method, 1)[1].split("    @Test fun", 1)[0]
                self.assertEqual(body(previous), body(current), method)
        self.assertEqual("145287111a3c12354efa3b30c2df93ee3a8120f3a42a37f2193a02d17065544f", hashlib.sha256(old.SPEC_PATH.read_bytes()).hexdigest())
        self.assertEqual(29, sum(len(b["fragments"]) for b in old._bindings().values()))

    def test_ancestor_peeling_is_nonrecursive_and_latest_partial_foreign_or_historical_refuse(self):
        import ios_popover_bar_recovery_source_projection as recovery
        import ios_popover_anchor_source_projection as old
        import ios_worker_completion_source_projection as worker
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            live = (ROOT / relative).read_bytes()
            previous = recovery.current_source_before_bar_recovery(relative, live)
            expected = old.source_before_popover_anchor(relative, previous)
            self.assertEqual(expected, old.current_source_before_popover_anchor(relative, live))
            self.assertEqual(worker.current_source_before_worker_completion(relative, live), worker.current_source_before_worker_completion(relative, previous))
            for bad in (previous, live[:-1], live + b"\n", live.replace(b"\n", b"\r\n"), b"", None, bytearray(live)):
                with self.assertRaises(ValueError): recovery.current_source_before_bar_recovery(relative, bad)
                with self.assertRaises(ValueError): old.current_source_before_popover_anchor(relative, bad)
        reader = (ROOT / "scripts/ci/ios_popover_anchor_source_projection.py").read_text()
        self.assertEqual(2, reader.count("bar_history.peel_current_bar_for_older_history(relative, payload)"))
        self.assertEqual(1, reader.count("bar_history.current_source_before_bar_recovery(relative, payload)"))
        helper = (ROOT / "scripts/ci/ios_popover_bar_recovery_source_projection.py").read_text()
        self.assertNotIn("ios_popover_anchor_source_projection", helper)


if __name__ == "__main__":
    unittest.main()
