# SPDX-License-Identifier: Apache-2.0
"""New shared modal source/routing controls; not native touch or heap evidence."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import library_tests as library
import workflow_matrix as workflow
import native_ui_input as input_driver
import ios_modal_xcui_source_projection as history

ROOT = Path(__file__).resolve().parents[2]
SIMULATOR = "726D52AF-426A-408A-974D-CA8B9BE8A479"
COMPILER = "scripts/ci/ios_modal_xcui_compile.init.gradle.kts"
LIFECYCLE_SHA256 = "dd73e1a96b6a7cbf64d67b39ab0f4c62d1f8b7100771409f75336410c6a7d7db"
HOST_SHA256 = "4eb8b1c7cc43de5bc39f0d36ec818d7216054e0b6b262b936826b4efe51fbc65"


def native_request(source, variable):
    match = re.search(r'val ' + variable + r' = listOf\("([^"\n]+)"\) \+ listOf\(\n(.*?)\n'
        r'    \)\.flatMap \{ method -> listOf\("--tests", "([^"\n]+)\.\$method"\) \}', source, re.S)
    if match is None: raise ValueError("One authored finite native request required")
    task, body, classname = match.groups()
    methods = re.findall(r'^        "([A-Za-z][A-Za-z0-9]+)",$', body, re.M)
    return [task] + [argument for method in methods for argument in ("--tests", classname + "." + method)]


class IosModalXcuiBatchControls(unittest.TestCase):
    def test_seven_enabled_methods_use_only_one_actual_host_and_the_exact_four_source_compiler(self):
        source = (ROOT / library.IOS_MODAL_XCUI_SOURCE).read_text()
        self.assertEqual(library.IOS_MODAL_XCUI_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertNotRegex(source, r"@(Ignore|Disabled|IgnoredTest)\b")
        compiler = (ROOT / COMPILER).read_text()
        self.assertEqual([library.IOS_MODAL_XCUI_SOURCE, input_driver.NATIVE,
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
            "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt"],
            re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', compiler))
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_XCUI_FOCUS)
        command = library.gradle_command("ios", plan, SIMULATOR)
        self.assertEqual(native_request(compiler, "applicationRequest"), command[command.index(":calf-ui:iosSimulatorArm64ApplicationTest"):])
        self.assertEqual(1, command.count(COMPILER))
        self.assertEqual(7, len(plan["expected"][0]["required_testcases"]))
        self.assertTrue(input_driver.validate_sources(ROOT))
        for profile, kind in (("ios-modal-xcui-batch", "iphone"), ("ios-modal-xcui-batch-ipad", "ipad")):
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26", "arch": "arm64",
                "python": "python3", "simulator-kind": kind, "test-modules": "calf-ui", "test-focus": library.IOS_MODAL_XCUI_FOCUS}]},
                workflow.matrix(profile))
            for module in ("calf-share", "calf-io"):
                with patch.dict(workflow.MODULE_SUBSETS, {profile: module}), self.assertRaises(ValueError): workflow.matrix(profile)
            with patch.dict(workflow.PROFILES, {profile: ("ios-iphone", "ios-ipad")}), self.assertRaises(ValueError): workflow.matrix(profile)

    def test_failed_only_memory_request_keeps_original_three_bodies_and_excludes_every_accepted_method(self):
        self.assertEqual(LIFECYCLE_SHA256, hashlib.sha256((ROOT / library.IOS_MODAL_LIFECYCLE_SOURCE).read_bytes()).hexdigest())
        host = ROOT / "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt"
        from ios_modal_worker_source_projection import current_source_before_modal_worker
        self.assertEqual(HOST_SHA256, hashlib.sha256(current_source_before_modal_worker(host.relative_to(ROOT).as_posix(), host.read_bytes())).hexdigest())
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_LIFECYCLE_MEMORY_FOCUS)
        required = plan["expected"][0]["required_testcases"]
        self.assertEqual({method + "[iosSimulatorArm64]" for method in library.IOS_MODAL_LIFECYCLE_MEMORY_METHODS}, {c["name"] for c in required})
        self.assertNotIn(library.IOS_MODAL_LIFECYCLE_METHODS[1] + "[iosSimulatorArm64]", {c["name"] for c in required})
        self.assertTrue({c["name"] for c in required}.isdisjoint(c["name"] for c in library.ui_application_focus_identities(library.IOS_MODAL_OWNERSHIP_FOCUS)))
        script = "scripts/ci/ios_modal_focused_compile.init.gradle.kts"
        source = (ROOT / script).read_text(); expected = native_request(source, "memoryRecoveryRequest")
        command = library.gradle_command("ios", plan, SIMULATOR)
        self.assertEqual(expected, command[command.index(":calf-ui:iosSimulatorArm64ApplicationTest"):])
        self.assertEqual(5, len(expected)); self.assertIn("        memoryRecoveryRequest,\n", source)
        self.assertIn("check(gradle.startParameter.taskNames in permittedTasks)", source)
        self.assertEqual({"include": [{"slot": "ios-iphone", "suite": "ios", "runner": "macos-26", "arch": "arm64",
            "python": "python3", "simulator-kind": "iphone", "test-modules": "calf-ui", "test-focus": library.IOS_MODAL_LIFECYCLE_MEMORY_FOCUS}]},
            workflow.matrix("ios-modal-lifecycle-memory-recovery"))

    def test_source_planning_refuses_disabled_declarations_and_a_missing_or_test_bearing_input_helper(self):
        source = (ROOT / library.IOS_MODAL_XCUI_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as temporary:
            altered = Path(temporary) / "Ignored.kt"
            altered.write_text(source.replace("class NativeModalXcuiBatchTest", "@Ignore\nclass NativeModalXcuiBatchTest", 1))
            original = library.safe_path
            def selected(root, relative): return altered if relative == library.IOS_MODAL_XCUI_SOURCE else original(root, relative)
            with patch.object(library, "safe_path", selected), self.assertRaisesRegex(ValueError, "enabled native declarations"):
                library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_XCUI_FOCUS)
        read = input_driver.read_ordinary
        def annotated(path, limit=input_driver.MAX_BYTES):
            raw = read(path, limit)
            return raw + b"\n@Ignore\n" if path == ROOT / input_driver.NATIVE else raw
        with patch.object(input_driver, "read_ordinary", side_effect=annotated), self.assertRaisesRegex(ValueError, "zero-test"):
            library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_XCUI_FOCUS)
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(OSError): input_driver.validate_sources(Path(temporary))

    def test_public_input_has_no_launch_private_activation_callback_fallback_or_sample_substitution(self):
        swift = (ROOT / input_driver.SWIFT).read_text()
        for token in ("XCUIApplication(bundleIdentifier: bundle)", "application.state == .runningForeground", "field.typeText(text)",
                      "button.tap()", "thenDragTo: to", "query.count == 1", "URLSessionConfiguration.ephemeral",
                      "session?.invalidateAndCancel()", 'request.setValue("Bearer " + token', "token != sessionToken"):
            self.assertIn(token, swift)
        self.assertNotRegex(swift, r"\.(launch|activate|performSelector)\s*\(")
        self.assertNotRegex(swift, r"\.setValue\([^\n]*forKey:")
        self.assertNotIn("screenshot", swift.split("private func deliver", 1)[1].split("private func coordinate", 1)[0])
        native = (ROOT / library.IOS_MODAL_XCUI_SOURCE).read_text()
        for token in ("newEdits.last()", "oldEdits.isEmpty()", 'listOf("Save B")', "outside = true",
                      "outsideHiddenBefore", "SheetValue.PartiallyExpanded", "SheetValue.Expanded", "SheetValue.Hidden",
                      "saver.restore(value)", "UIUserInterfaceSizeClassRegular"):
            self.assertIn(token, native)
        self.assertNotRegex(native, r"(activateAction|accessibilityActivate|sendActionsForControlEvents|dismissViewControllerAnimated)\s*\(")
        self.assertNotIn("sample/", native)
        app = (ROOT / "scripts/ci/ios_ui_application.py").read_text()
        self.assertIn('if host["module"] == "calf-ui" and focus == lt.IOS_MODAL_XCUI_FOCUS:', app)
        self.assertIn("except Exception as error:\n                receipt[\"native_xctest_input\"]", app)
        collector = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn("native_ui_input.validate_receipt(document.get(\"native_xctest_input\")", collector)

    def test_terminal_sheet_release_invalidates_content_and_breaks_native_delegate_edges_without_changing_intent_or_animation_waiters(self):
        relative = "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/sheet/BottomSheetManager.kt"
        source = (ROOT / relative).read_text(); old = history.current_source_before_modal_xcui(relative, source.encode()).decode()
        for start, end in (("    private suspend fun awaitVisibility", "    private fun publishState"),
                           ("    private fun finishWaiters", "    private fun pump")):
            self.assertEqual(old.split(start, 1)[1].split(end, 1)[0], source.split(start, 1)[1].split(end, 1)[0])
        self.assertIn("val lease = contentState\n        ComposeUIViewController { lease.value?.invoke() }", source)
        disposal = source.split("    fun dispose()", 1)[1].split("    private fun releaseIfDisposed", 1)[0]
        self.assertLess(disposal.index("contentState.value = null"), disposal.index("pump()"))
        self.assertIn("confirmValueChange = { false }", disposal)
        release = source.split("    private fun releaseIfDisposed", 1)[1].split("@OptIn", 1)[0]
        self.assertIn("presentation.phase != NativePresentationState.Phase.Hidden", release)
        self.assertIn("delegate.releaseCallbacks()", release)
        callbacks = source.split("    internal fun releaseCallbacks()", 1)[1].split("    override fun", 1)[0]
        for token in ("check(NSThread.isMainThread)", "onDismiss = {}", "confirmValueChange = { false }", "onDetentChanged = {}"):
            self.assertIn(token, callbacks)

    def test_exact_six_path_history_restores_prior_bytes_preserves_old_pins_and_refuses_tampering(self):
        bindings = history._bindings(); self.assertEqual(6, len(bindings))
        self.assertEqual(22, sum(len(binding["fragments"]) for binding in bindings.values()))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_modal_xcui(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_modal_xcui(relative, previous))
            for changed in (previous, current + b"\n", current.replace(b"\n", b"\r\n")):
                with self.assertRaisesRegex(ValueError, "exact current"): history.current_source_before_modal_xcui(relative, changed)
        for name, pin in (("ios-modal-lifecycle-source-inverse.json", "d911d4c08c649f81e68f869b9b15fd8a6194697fb073fd011a18a05d2299dfff"),
                          ("ios-modal-ownership-source-inverse.json", "541e0e1f5d08dc699a8a450361ef00780de2e5c92607b0a141c487fd1156c72f")):
            self.assertEqual(pin, hashlib.sha256((ROOT / "scripts/ci/fixtures" / name).read_bytes()).hexdigest())
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", "scripts/ci/ios_ui_application.py"):
            source = (ROOT / relative).read_text()
            self.assertNotIn("ios_modal_xcui_source_projection", source)
            self.assertNotIn("ios_modal_lifecycle_source_projection", source)
        workflow_text = (ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertNotIn("build/ci-runtime/native-input", workflow_text)
        self.assertNotIn(".xcresult", workflow_text)


if __name__ == "__main__":
    unittest.main()
