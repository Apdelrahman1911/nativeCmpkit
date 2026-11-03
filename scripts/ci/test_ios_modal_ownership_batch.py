"""Focused routing/refusal checks, not native UIKit results."""
from pathlib import Path
import hashlib
import json
import re
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow
import ios_modal_ownership_source_projection as history

ROOT = Path(__file__).resolve().parents[2]


class IosModalOwnershipBatchTests(unittest.TestCase):
    def test_each_fixed_host_selects_only_the_nine_new_native_cases(self):
        names = library.IOS_MODAL_OWNERSHIP_METHODS
        source = (ROOT / library.IOS_MODAL_OWNERSHIP_SOURCE).read_text()
        self.assertEqual(names, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertEqual(9, source.count("= runApplicationUiTest {"))
        for profile, kind in (("ios-modal-ownership-batch", "iphone"), ("ios-modal-ownership-ipad", "ipad")):
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26",
                "arch": "arm64", "python": "python3", "simulator-kind": kind,
                "test-modules": "calf-ui", "test-focus": library.IOS_MODAL_OWNERSHIP_FOCUS}]}, workflow.matrix(profile))
        identities = library.ui_application_focus_identities(library.IOS_MODAL_OWNERSHIP_FOCUS)
        self.assertEqual(9, len(identities))
        self.assertEqual({name + "[iosSimulatorArm64]" for name in names}, {item["name"] for item in identities})
        self.assertTrue(library.allowed_test_focus("ios", ("calf-ui",), library.IOS_MODAL_OWNERSHIP_FOCUS))

    def test_wrong_host_module_and_suite_are_refused_without_changing_old_alert_selection(self):
        old = library.ui_application_focus_filter(library.UI_ALERT_RECOVERY_FOCUS)
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, library.IOS_MODAL_OWNERSHIP_FOCUS))
        for profile in ("ios-modal-ownership-batch", "ios-modal-ownership-ipad"):
            with patch.dict(workflow.PROFILES, {profile: ("desktop-macos-arm64",)}):
                with self.assertRaises(ValueError):
                    workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}):
                with self.assertRaises(ValueError):
                    workflow.matrix(profile)
        self.assertEqual(old, library.ui_application_focus_filter(library.UI_ALERT_RECOVERY_FOCUS))
        self.assertNotIn(library.UI_ALERT_IMPORTANT_CLASS, library.ui_application_focus_filter(library.IOS_MODAL_OWNERSHIP_FOCUS))

    def test_current_modal_sources_restore_exact_history_without_admitting_old_or_mutated_sources(self):
        bindings = json.loads(history.SPEC_PATH.read_text())["bindings"]
        self.assertEqual(7, len(bindings))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_modal_ownership(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_modal_ownership(relative, previous))
            with self.assertRaisesRegex(ValueError, "historical image"):
                history.current_source_before_modal_ownership(relative, previous)
            for changed in (current + b"\n", current.replace(b"\n", b"\r\n")):
                with self.assertRaisesRegex(ValueError, "exact current"):
                    history.current_source_before_modal_ownership(relative, changed)
        from android_external328_source_projection import current_source_for_history
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            self.assertIsInstance(current_source_for_history(relative, (ROOT / relative).read_bytes()), bytes)

    def test_live_native_planning_does_not_use_offline_modal_history(self):
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", "scripts/ci/ios_ui_application.py"):
            self.assertNotIn("ios_modal_ownership_source_projection", (ROOT / relative).read_text())
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_OWNERSHIP_FOCUS)
        self.assertEqual(9, len(plan["expected"][0]["required_testcases"]))


if __name__ == "__main__":
    unittest.main()
