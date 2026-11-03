"""Finite source/routing controls only, never native behavior evidence."""
from pathlib import Path
import hashlib
import json
import re
import tempfile
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow
import ios_modal_lifecycle_source_projection as lifecycle
import ios_modal_ownership_source_projection as modal
import ios_popover_anchor_source_projection as anchor_history

ROOT = Path(__file__).resolve().parents[2]
PROFILES = (("ios-modal-lifecycle-replacement", "iphone"),
            ("ios-modal-lifecycle-replacement-ipad", "ipad"))


class IosModalLifecycleReplacementTests(unittest.TestCase):
    def test_only_this_new_focus_uses_the_narrow_compiler_without_changing_old_commands(self):
        simulator = "726D52AF-426A-408A-974D-CA8B9BE8A479"
        script = "scripts/ci/ios_modal_focused_compile.init.gradle.kts"
        for focus, present in ((library.IOS_MODAL_LIFECYCLE_FOCUS, True),
                               (library.IOS_MODAL_OWNERSHIP_FOCUS, False)):
            plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=focus)
            command = library.gradle_command("ios", plan, simulator)
            self.assertEqual(present, script in command)
            self.assertEqual(1 if present else 0, command.count(script))
            self.assertEqual(1, command.count(":calf-ui:iosSimulatorArm64ApplicationTest"))
            self.assertIn("scripts/ci/fresh-tests.init.gradle.kts", command)

    def test_focused_compiler_holds_the_exact_three_sources_and_ignores_unrelated_included_builds(self):
        source = (ROOT / "scripts/ci/ios_modal_focused_compile.init.gradle.kts").read_text()
        paths = re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', source)
        self.assertEqual([library.IOS_MODAL_LIFECYCLE_SOURCE,
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt"], paths)
        self.assertLess(source.index('rootProject.findProject(":calf-ui") ?: return@projectsEvaluated'),
                        source.index("check(gradle.startParameter.taskNames in permittedTasks)"))
        for required in ('getMethod("setSource", Array<Any>::class.java)',
                         'getMethod("getSources")', 'common.setFrom(emptyList<Any>())',
                         'files.toSet() && common.files.isEmpty()',
                         'listOf(":calf-ui:compileTestKotlinIosSimulatorArm64")',
                         'listOf(":calf-ui:iosSimulatorArm64ApplicationTest")'):
            self.assertIn(required, source)
        self.assertNotIn("ignoreFailures", source)
        self.assertNotIn("sourceSets", source)
        self.assertNotIn("UP-TO-DATE", source)

    def test_only_the_three_new_methods_are_selected_on_each_single_actual_host(self):
        source = (ROOT / library.IOS_MODAL_LIFECYCLE_SOURCE).read_text()
        self.assertEqual(library.IOS_MODAL_LIFECYCLE_METHODS,
                         tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertEqual(4, source.count("runApplicationUiTest {"))
        for profile, kind in PROFILES:
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios",
                "runner": "macos-26", "arch": "arm64", "python": "python3",
                "simulator-kind": kind, "test-modules": "calf-ui",
                "test-focus": library.IOS_MODAL_LIFECYCLE_FOCUS}]}, workflow.matrix(profile))
        identities = library.ui_application_focus_identities(library.IOS_MODAL_LIFECYCLE_FOCUS)
        self.assertEqual(3, len(identities))
        self.assertEqual({name + "[iosSimulatorArm64]" for name in library.IOS_MODAL_LIFECYCLE_METHODS},
                         {item["name"] for item in identities})
        old = library.ui_application_focus_identities(library.IOS_MODAL_OWNERSHIP_FOCUS)
        self.assertEqual(9, len(old))
        self.assertTrue({item["name"] for item in old}.isdisjoint(item["name"] for item in identities))

    def test_wrong_host_module_or_suite_is_refused_before_native_setup(self):
        for profile, _ in PROFILES:
            for mutation in ({profile: ("desktop-macos-arm64",)}, {profile: ("ios-iphone", "ios-ipad")}):
                with patch.dict(workflow.PROFILES, mutation):
                    with self.assertRaises(ValueError):
                        workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}):
                with self.assertRaises(ValueError):
                    workflow.matrix(profile)
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, library.IOS_MODAL_LIFECYCLE_FOCUS))

    def test_live_plan_requires_three_enabled_native_declarations(self):
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_LIFECYCLE_FOCUS)
        self.assertEqual(library.ui_application_focus_identities(library.IOS_MODAL_LIFECYCLE_FOCUS),
                         plan["expected"][0]["required_testcases"])
        source = (ROOT / library.IOS_MODAL_LIFECYCLE_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            ignored = Path(temporary) / "Ignored.kt"
            ignored.write_text(source.replace("class NativeModalLifecycleReplacementTest", "@Ignore\nclass NativeModalLifecycleReplacementTest", 1))
            actual_safe_path = library.safe_path
            def selected_source(root, relative):
                return ignored if relative == library.IOS_MODAL_LIFECYCLE_SOURCE else actual_safe_path(root, relative)
            with patch.object(library, "safe_path", selected_source):
                with self.assertRaisesRegex(ValueError, "enabled native declarations"):
                    library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_LIFECYCLE_FOCUS)

    def test_history_restores_every_routing_byte_without_refreshing_original_modal_pins(self):
        bindings = json.loads(lifecycle.SPEC_PATH.read_text())["bindings"]
        self.assertEqual(3, len(bindings))
        self.assertEqual(8, sum(len(item["fragments"]) for item in bindings.values()))
        old_bindings = json.loads(modal.SPEC_PATH.read_text())["bindings"]
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = lifecycle.current_source_before_modal_lifecycle(relative,
                anchor_history.current_source_before_popover_anchor(relative, current))
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(old_bindings[relative]["after_sha256"], hashlib.sha256(previous).hexdigest())
            historical = modal.current_source_before_modal_ownership(relative, current)
            self.assertEqual(old_bindings[relative]["before_sha256"], hashlib.sha256(historical).hexdigest())
            self.assertEqual(historical, modal.source_before_modal_ownership(relative, historical))
            for wrong in (previous, current + b"\n", current.replace(b"\n", b"\r\n")):
                with self.assertRaisesRegex(ValueError, "exact current"):
                    lifecycle.current_source_before_modal_lifecycle(relative, wrong)
        from android_external328_source_projection import current_source_for_history
        for relative in bindings:
            self.assertIsInstance(current_source_for_history(relative, (ROOT / relative).read_bytes()), bytes)

    def test_new_lifecycle_cases_require_real_animation_ownership_and_main_thread_collection(self):
        source = (ROOT / library.IOS_MODAL_LIFECYCLE_SOURCE).read_text()
        for required in ("isBeingPresented()", "isBeingDismissed()", "hiding.isCancelled",
                         "assertNull(state.iosSheetManager)", "held.detach(assertNotNull(firstManager))",
                         "assertNull(assertNotNull(firstParent).view.window)", "current = replacement",
                         "assertFalse(sameNativeObject(priorController, secondParent?.presentedViewController))",
                         "repeat(4) { cycle", "repeat(3) { runOnIdle { GC.collect() } }"):
            self.assertIn(required, source)
        self.assertNotRegex(source, r"@(Ignore|Disabled|IgnoredTest)\b")
        self.assertNotIn("LocalUIViewController provides", source)
        self.assertNotIn("dismissViewControllerAnimated", source)
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", "scripts/ci/ios_ui_application.py"):
            self.assertNotIn("ios_modal_lifecycle_source_projection", (ROOT / relative).read_text())


if __name__ == "__main__":
    unittest.main()
