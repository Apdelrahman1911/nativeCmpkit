# SPDX-License-Identifier: Apache-2.0
"""Important new source/admission controls, NOT UIKit/native or rotation tests."""
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

import ios_popover_anchor_plan as compiler
import ios_popover_anchor_source_projection as history
import ios_popover_bar_recovery_source_projection as bar_history
import library_tests as library
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]
SIMULATOR = "726D52AF-426A-408A-974D-CA8B9BE8A479"
INIT = "scripts/ci/ios_popover_anchor_compile.init.gradle.kts"
MANAGER = "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AlertDialogManager.kt"
ANCHOR = "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/uikit/AlertDialogIosPopoverAnchor.kt"


class PopoverAnchorSourceControls(unittest.TestCase):
    def test_exact_five_enabled_cases_and_each_fixed_real_host_are_selected(self):
        source = (ROOT / library.IOS_POPOVER_ANCHOR_SOURCE).read_text()
        self.assertEqual(library.IOS_POPOVER_ANCHOR_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertEqual(5, source.count("= runApplicationUiTest {"))
        self.assertNotRegex(source, r"@(Ignore|Disabled|IgnoredTest)\b")
        for profile, kind in (("ios-popover-anchor", "iphone"), ("ios-popover-anchor-ipad", "ipad")):
            self.assertEqual({"include": [{"slot": "ios-" + kind, "suite": "ios", "runner": "macos-26",
                "arch": "arm64", "python": "python3", "simulator-kind": kind,
                "test-modules": "calf-ui", "test-focus": compiler.FOCUS}]}, workflow.matrix(profile))
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=compiler.FOCUS)
        self.assertEqual(library.ui_application_focus_identities(compiler.FOCUS), plan["expected"][0]["required_testcases"])
        self.assertEqual(5, len(plan["expected"][0]["required_testcases"]))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertIn("NOT actual OS", plan["scope"])

    def test_only_new_focus_uses_the_exact_four_source_compiler_and_five_filters(self):
        source = (ROOT / INIT).read_text()
        self.assertEqual(list(compiler.SOURCES), re.findall(r'"(calf-ui/src/iosTest/[^"\n]+\.kt)"', source))
        self.assertIn('common.setFrom(emptyList<Any>())', source)
        self.assertIn('actual.files.map { it.canonicalFile }.toSet() == files.toSet()', source)
        self.assertIn('compilation.doFirst {', source)
        self.assertIn('"native_tests_executed" to 0', source)
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=compiler.FOCUS)
        command = library.gradle_command("ios", plan, SIMULATOR)
        self.assertEqual(1, command.count(INIT))
        selectors = [command[i + 1] for i, value in enumerate(command) if value == "--tests"]
        self.assertEqual([library.IOS_POPOVER_ANCHOR_CLASS + "." + name for name in library.IOS_POPOVER_ANCHOR_METHODS], selectors)
        old = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_XCUI_FOCUS)
        self.assertNotIn(INIT, library.gradle_command("ios", old, SIMULATOR))
        live = (ROOT / "scripts/ci/ios_ui_application.py").read_text()
        self.assertIn('focus == lt.IOS_MODAL_XCUI_FOCUS:', live)
        self.assertNotIn("lt.IOS_POPOVER_ANCHOR_FOCUS", live)  # No claimed independent OS input for controlled cases.

    def test_wrong_suite_modules_host_and_disabled_native_source_fail_closed(self):
        for suite, modules in (("desktop", ("calf-ui",)), ("ios", ("calf-share",)), ("ios", None)):
            self.assertFalse(library.allowed_test_focus(suite, modules, compiler.FOCUS))
        for profile in ("ios-popover-anchor", "ios-popover-anchor-ipad"):
            with patch.dict(workflow.PROFILES, {profile: ("desktop-macos-arm64",)}), self.assertRaises(ValueError):
                workflow.matrix(profile)
            with patch.dict(workflow.MODULE_SUBSETS, {profile: "calf-share"}), self.assertRaises(ValueError):
                workflow.matrix(profile)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "ignored.kt"
            target.write_text((ROOT / library.IOS_POPOVER_ANCHOR_SOURCE).read_text().replace(
                "class NativePopoverAnchorTest", "@Ignore\nclass NativePopoverAnchorTest", 1))
            ordinary = library.safe_path
            def controlled_path(root, relative):
                return target if relative == library.IOS_POPOVER_ANCHOR_SOURCE else ordinary(root, relative)
            with patch.object(library, "safe_path", controlled_path), self.assertRaisesRegex(ValueError, "enabled native declarations"):
                library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=compiler.FOCUS)

    def test_supported_view_local_api_finite_geometry_and_native_owner_cleanup_are_retained(self):
        anchor = (ROOT / ANCHOR).read_text()
        for token in ("staticCompositionLocalOf<AlertDialogIosPopoverAnchor?> { null }", "LOCAL coordinates",
                      "val rect = sourceRect ?: bounds", "view.window?.objcPtr() == window.objcPtr()",
                      "validRectInBounds(rect, bounds)", "item.customView?.let(::inCurrentWindow)",
                      "source view's current bounds", "NSThread.isMainThread", "origin.x.isFinite()"):
            self.assertIn(token, anchor)
        source = (ROOT / MANAGER).read_text()
        pump = source.split("    private fun pump()", 1)[1].split("    private fun clearController", 1)[0]
        admitted = pump.split("NativePresentationQueue.acquire(parentUIViewController, this) {", 1)[1]
        self.assertLess(admitted.index("refreshPopoverAnchor()"), admitted.index("presentViewController"))
        delegate = source.split("override fun popoverPresentationController(\n", 1)[1].split("    private fun requireMain", 1)[0]
        for token in ("requireMain()", "!ownsPopover", "presentation.disposed", "Phase.Dismissing",
                      "if (willRepositionPopoverToRect == null || inView == null) return", "inView.pointed.value = anchor.view"):
            self.assertIn(token, delegate)
        cleanup = source.split("    private fun clearController()", 1)[1].split("    private fun ownsPopover", 1)[0]
        for token in ("ownedAnchorView?.objcPtr() == popover.sourceView?.objcPtr()",
                      "ownedAnchorBarButton?.objcPtr() == popover.barButtonItem?.objcPtr()",
                      "delegate.objcPtr() == presentationDelegate.objcPtr()", "ownedAnchorView = null", "ownedAnchorBarButton = null"):
            self.assertIn(token, cleanup)
        self.assertNotIn("presentationController?.delegate =", source)
        adapter = (ROOT / "calf-ui/src/iosMain/kotlin/com/mohamedrejeb/calf/ui/dialog/AdaptiveAlertDialog.ios.kt").read_text()
        self.assertEqual(2, adapter.count("val popoverAnchor = LocalAlertDialogIosPopoverAnchor.current"))
        self.assertEqual(2, adapter.count("alertDialogManager.popoverAnchor = popoverAnchor"))

    def test_all_eight_complete_paths_and_twenty_nine_fragments_roundtrip(self):
        bindings = history._bindings()
        self.assertEqual(8, len(bindings))
        self.assertEqual(29, sum(len(row["fragments"]) for row in bindings.values()))
        for relative, row in bindings.items():
            current = (ROOT / relative).read_bytes()
            old = history.current_source_before_popover_anchor(relative, current)
            self.assertEqual(row["before_sha256"], hashlib.sha256(old).hexdigest())
            self.assertEqual(old, history.source_before_popover_anchor(relative, old))
            self.assertIs(old, history.peel_current_popover_for_older_history(relative, old))
            self.assertEqual(old, history.peel_current_popover_for_older_history(relative, current))
            forward = old
            for fragment in row["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()))
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(bar_history.source_before_bar_recovery(relative, current), forward)

    def test_current_admission_rejects_historical_unknown_drift_types_and_identity_guessing(self):
        bindings = history._bindings()
        for relative in bindings:
            live = (ROOT / relative).read_bytes()
            old = history.source_before_popover_anchor(relative, live)
            for payload in (old, live[:-1], live + b"\n", live.replace(b"\n", b"\r\n"), b"unknown", b""):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    history.current_source_before_popover_anchor(relative, payload)
            for payload in (None, bytearray(live), live.decode()):
                with self.assertRaises(ValueError): history.source_before_popover_anchor(relative, payload)
        with self.assertRaises(ValueError):
            history.source_before_popover_anchor(MANAGER, b"x" * (history.MAX_SOURCE_BYTES + 1))
        raw = (ROOT / MANAGER).read_bytes()
        self.assertIs(raw, history.source_before_popover_anchor("unlisted", raw))
        with self.assertRaises(ValueError):
            history.current_source_before_popover_anchor("scripts/ci/library_tests.py", raw)

    def test_fragment_bytes_hashes_unique_sites_and_manifest_aliases_are_mandatory(self):
        live = (ROOT / MANAGER).read_bytes()
        for field in ("before", "after", "before_fragment_sha256", "after_fragment_sha256"):
            rows = copy.deepcopy(history._bindings())
            rows[MANAGER]["fragments"][0][field] += "unreviewed"
            with patch.object(history, "_bindings", return_value=rows), self.assertRaises(ValueError):
                history.source_before_popover_anchor(MANAGER, live)
        rows = copy.deepcopy(history._bindings()); rows[MANAGER]["before_sha256"] = "0" * 64
        with patch.object(history, "_bindings", return_value=rows), self.assertRaises(ValueError):
            history.source_before_popover_anchor(MANAGER, live)
        with tempfile.TemporaryDirectory() as temporary:
            file = Path(temporary) / "manifest.json"
            original = history.SPEC_PATH.read_bytes()
            for raw in (original + b"\n", b"{}", b"", b"x" * (history.MAX_SPEC_BYTES + 1)):
                file.write_bytes(raw)
                with patch.object(history, "SPEC_PATH", file), self.assertRaises(ValueError): history._bindings()
            file.write_bytes(original)
            alias = file.with_name("symbolic"); alias.symlink_to(file)
            with patch.object(history, "SPEC_PATH", alias), self.assertRaises(ValueError): history._bindings()
            alias.unlink(); alias.hardlink_to(file)
            with patch.object(history, "SPEC_PATH", file), self.assertRaises(ValueError): history._bindings()

    def test_all_old_modal_pins_and_exact_current_ancestor_admission_remain(self):
        from android_external328_source_projection import current_source_for_history
        import ios_modal_ownership_source_projection as modal
        import ios_modal_lifecycle_source_projection as lifecycle
        self.assertEqual("541e0e1f5d08dc699a8a450361ef00780de2e5c92607b0a141c487fd1156c72f", hashlib.sha256(modal.SPEC_PATH.read_bytes()).hexdigest())
        self.assertEqual("d911d4c08c649f81e68f869b9b15fd8a6194697fb073fd011a18a05d2299dfff", hashlib.sha256(lifecycle.SPEC_PATH.read_bytes()).hexdigest())
        for relative in (MANAGER, "scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            raw = (ROOT / relative).read_bytes()
            prior = modal.current_source_before_modal_ownership(relative, raw)
            self.assertEqual(modal._bindings()[relative]["before_sha256"], hashlib.sha256(prior).hexdigest())
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml"):
            self.assertIsInstance(current_source_for_history(relative, (ROOT / relative).read_bytes()), bytes)
        for relative in ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", "scripts/ci/ios_ui_application.py"):
            self.assertNotIn("ios_popover_anchor_source_projection", (ROOT / relative).read_text())

    def test_application_collector_cannot_accept_focused_native_results_without_compiler_admission(self):
        # Existing explicitly synthetic setup only; do NOT invoke any old test body.
        import test_ios_application_receipts as synthetic
        fixture = synthetic.IosApplicationReceipts(methodName="runTest")
        fixture.setUp()
        try:
            fixture.write(library.IOS_POPOVER_ANCHOR_SOURCE, (ROOT / library.IOS_POPOVER_ANCHOR_SOURCE).read_bytes())
            fixture.plan = library.plan(fixture.root, "ios", only_modules=("calf-ui",), focus=compiler.FOCUS)
            fixture.document["explicit_test_focus"] = compiler.FOCUS
            fixture.cases = [{"classname": library.IOS_POPOVER_ANCHOR_CLASS, "name": method, "status": "passed"}
                             for method in library.IOS_POPOVER_ANCHOR_METHODS]
            fixture.document["application_protocol"]["testcases"] = fixture.cases
            fixture.document["application_protocol"]["counts"] = library.case_counts(fixture.cases)
            fixture.modules[0]["testcases"] = fixture.xml_cases(fixture.cases)
            fixture.save()
            with patch.object(compiler, "validate_compilation", return_value=False) as admission:
                result = fixture.collect()
                admission.assert_called_once()
                self.assertIn("fresh exact four-source compiler receipt", str(result["errors"]))
        finally:
            fixture.doCleanups()


class PopoverCompilerReceiptControls(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for relative in compiler.SOURCES:
            target = self.root / relative; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        self.path = self.root / compiler.RECEIPT; self.path.parent.mkdir(parents=True)
        self.document = {"task": ":calf-ui:compileTestKotlinIosSimulatorArm64", "focus": compiler.FOCUS,
            "source_sha256": {name: hashlib.sha256((self.root / name).read_bytes()).hexdigest() for name in compiler.SOURCES},
            "effective_sources": list(compiler.SOURCES), "excluded_unrelated_test_sources": True,
            "production_source_sets_changed": False, "native_tests_executed": 0,
            "scope": "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes"}
        self.save()

    def save(self): self.path.write_text(json.dumps(self.document))
    def valid(self):
        now = time.time_ns()
        return compiler.validate_compilation(self.root, now - 1_000_000_000, now + 1_000_000_000)

    def test_exact_fresh_four_file_receipt_admits_compilation_only(self):
        self.assertTrue(self.valid())
        self.assertFalse(compiler.validate_compilation(self.root, True, time.time_ns()))
        self.assertFalse(compiler.validate_compilation(self.root, 0, time.time_ns()))
        self.assertFalse(compiler.validate_compilation(self.root, time.time_ns(), 1))

    def test_wrong_sources_hashes_target_scope_native_claims_and_extra_fields_refuse(self):
        original = copy.deepcopy(self.document)
        mutations = (lambda d: d.update(task=":calf-ui:iosSimulatorArm64Test"), lambda d: d.update(focus="ui-native-modal-xcui-batch"),
            lambda d: d.update(native_tests_executed=True), lambda d: d.update(native_tests_executed=0.0),
            lambda d: d.update(native_tests_executed=5), lambda d: d.update(excluded_unrelated_test_sources=1),
            lambda d: d.update(production_source_sets_changed=0), lambda d: d.update(production_source_sets_changed=True),
            lambda d: d.update(scope="Native passed"), lambda d: d.update(extra="unknown"),
            lambda d: d["effective_sources"].pop(), lambda d: d["effective_sources"].reverse(),
            lambda d: d["source_sha256"].update({compiler.SOURCES[0]: "0" * 64}))
        for change in mutations:
            self.document = copy.deepcopy(original); change(self.document); self.save()
            self.assertFalse(self.valid())

    def test_stale_future_missing_malformed_duplicate_and_nonfinite_receipts_refuse(self):
        now = time.time_ns()
        for stamp in (now - 10_000_000_000, now + 10_000_000_000):
            os.utime(self.path, ns=(stamp, stamp)); self.assertFalse(self.valid())
        for raw in (b"{}", b"", b"\xff", b"[", b'{"native_tests_executed":0,"native_tests_executed":0}', b'{"value":NaN}', b"x" * (compiler.MAX_BYTES + 1)):
            self.path.write_bytes(raw); self.assertFalse(self.valid())
        self.path.unlink(); self.assertFalse(self.valid())

    def test_receipt_and_source_aliases_or_after_compile_source_drift_refuse(self):
        self.assertTrue(self.valid())
        original = self.path.read_bytes(); external = self.root / "external.json"; external.write_bytes(original)
        self.path.unlink(); self.path.symlink_to(external); self.assertFalse(self.valid())
        self.path.unlink(); self.path.write_bytes(original)
        link = self.root / "hard.json"; link.hardlink_to(self.path); self.assertFalse(self.valid()); link.unlink()
        target = self.root / compiler.SOURCES[0]; raw = target.read_bytes()
        target.write_bytes(raw + b"\n"); self.assertFalse(self.valid()); target.write_bytes(raw)
        link = self.root / "hard.kt"; link.hardlink_to(target); self.assertFalse(self.valid()); link.unlink()
        target.unlink(); link.write_bytes(raw); target.symlink_to(link); self.assertFalse(self.valid())


if __name__ == "__main__":
    unittest.main()
