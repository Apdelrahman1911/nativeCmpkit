"""Finite related saver-state guards. Synthetic tooling, not native library passes."""
from collections import Counter
import copy
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

import library_tests as r
import picker_dialog_context as portal
import workflow_matrix as matrix


class DesktopSaverStateFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "desktop", only_modules=("calf-file-picker",), focus=r.DESKTOP_SAVER_STATE_FOCUS)

    def collect(self, cases=None, status="passed", stale=False, marker=1, host="Linux"):
        plan = self.plan()
        cases = r.desktop_saver_state_identities() if cases is None else cases
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / plan["expected"][0]["report_directory"] / "TEST-synthetic.xml"
            report.parent.mkdir(parents=True)
            document = ET.Element("testsuite")
            for case in cases:
                item = ET.SubElement(document, "testcase", classname=case["classname"], name=case["name"])
                if status != "passed": ET.SubElement(item, {"failed": "failure", "error": "error", "skipped": "skipped"}[status])
            report.write_bytes(ET.tostring(document))
            now = time.time_ns()
            if stale: os.utime(report, ns=(now - 10_000_000_000,) * 2)
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({":calf-file-picker:desktopTest": marker}), host_system=host)

    def test_exact_one_method_runs_on_three_desktop_hosts_without_accepted_picker_replay(self):
        rows = matrix.matrix("picker-saver-state")["include"]
        self.assertEqual(["desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64"], [row["slot"] for row in rows])
        self.assertTrue(all(row["suite"] == "desktop" and row["test-modules"] == "calf-file-picker" and
                            row["test-focus"] == r.DESKTOP_SAVER_STATE_FOCUS for row in rows))
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(r.desktop_saver_state_identities(), plan["expected"][0]["required_testcases"])
        self.assertEqual([":calf-file-picker:desktopTest", "--tests", r.DESKTOP_SAVER_STATE_CLASS], r.gradle_command("desktop", plan)[-3:])
        self.assertTrue(all(case["classname"] != r.PICKER_LIFETIME_CLASS for case in plan["expected"][0]["required_testcases"]))
        rows[0]["test-focus"] = "arbitrary"
        self.assertEqual(r.DESKTOP_SAVER_STATE_FOCUS, matrix.matrix("picker-saver-state")["include"][0]["test-focus"])
        self.assertEqual(11, len(matrix.matrix("all")["include"]))

    def test_one_nonzero_exact_XML_is_required_on_every_host_without_native_skip_waiver(self):
        for host in ("Linux", "Darwin", "Windows"):
            result = self.collect(host=host)
            self.assertEqual([], result["errors"])
            self.assertEqual(1, result["totals"]["passed"])
            self.assertEqual(0, result["totals"]["not_applicable"])
            for status in ("failed", "error", "skipped"):
                self.assertTrue(self.collect(status=status, host=host)["errors"])

    def test_missing_duplicate_foreign_wrong_target_stale_or_absent_task_fails(self):
        original = r.desktop_saver_state_identities()
        for cases in ([], original * 2, r.picker_lifetime_identities(),
                      [{**original[0], "name": original[0]["name"].removesuffix("[desktop]")}],
                      [{**original[0], "classname": "foreign.Class"}]):
            self.assertTrue(self.collect(cases)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])

    def test_wrong_scope_filter_source_count_or_complete_claim_is_rejected(self):
        for suite, modules in (("js", ("calf-file-picker",)), ("ios", ("calf-file-picker",)),
                               ("desktop", ("calf-io",)), ("desktop", None),
                               ("desktop", ("calf-file-picker", "calf-io"))):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.DESKTOP_SAVER_STATE_FOCUS)
        for key, value in (("task", ":calf-file-picker:publish"), ("test_filter", "*"),
                           ("required_testcases", []), ("test_source_files", [])):
            plan = copy.deepcopy(self.plan()); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan(); plan["expected"] *= 2
        with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan(); plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError): r.validate_test_focus(plan)

    def test_original_valid_declarations_precede_drift_and_missing_source_rejections(self):
        source = (r.ROOT / r.DESKTOP_SAVER_STATE_SOURCE).read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-file-picker",\n)\n')
            module = root / "calf-file-picker"; module.mkdir()
            (module / "build.gradle.kts").write_text("// synthetic fixture, never compiled\n")
            path = root / r.DESKTOP_SAVER_STATE_SOURCE; path.parent.mkdir(parents=True); path.write_text(source)
            # The owning module still requires its original six-method native
            # source even when this finite focus selects only the new saver case.
            (root / r.PICKER_LIFETIME_SOURCE).write_text((r.ROOT / r.PICKER_LIFETIME_SOURCE).read_text())
            self.assertTrue(r.validate_test_focus(self.plan(root)))
            for changed in (source.replace(r.DESKTOP_SAVER_STATE_METHOD, "wrongMethod", 1),
                            source.replace("@Test", "@IgnoredTest", 1),
                            source.replace("class NativeDesktopSaverStateTest", "class ForeignTest", 1),
                            source + "\n@Test fun extra() {}\n"):
                path.write_text(changed)
                with self.assertRaises(ValueError): self.plan(root)
            path.write_text(source); self.assertTrue(r.validate_test_focus(self.plan(root)))
            path.unlink()
            (module / "src/commonTest").mkdir(parents=True)
            (module / "src/commonTest/Other.kt").write_text("// unrelated source")
            with self.assertRaises((ValueError, FileNotFoundError)): self.plan(root)

    def test_only_exact_nonchooser_focus_avoids_unused_portal_original_full_unknown_keep_it(self):
        with patch.object(portal.platform, "system", return_value="Linux"), patch.object(portal.subprocess, "Popen") as spawn:
            plan = self.plan()
            self.assertIn(portal.SOURCE, plan["expected"][0]["test_source_files"])
            context = portal.OwnedPickerPortal(r.ROOT, Path("unused"), plan).start()
            self.assertFalse(context.requested); self.assertIsNone(context.environment); self.assertIsNone(context.receipt)
            context.close(); spawn.assert_not_called()
            for focus in (None, r.PICKER_LIFETIME_FOCUS, "arbitrary-nonchooser"):
                changed = copy.deepcopy(plan)
                if focus is None: changed.pop("explicit_test_focus")
                else: changed["explicit_test_focus"] = focus
                self.assertTrue(portal.OwnedPickerPortal(r.ROOT, Path("unused"), changed).requested)

    def test_public_factory_keeps_actual_operation_current_state_and_per_launch_snapshot(self):
        source = (r.ROOT / "calf-file-picker/src/desktopMain/kotlin/com/mohamedrejeb/calf/picker/FileSaverLauncher.desktop.kt").read_text()
        self.assertIn("rememberDesktopFileSaverLauncher(settings, onError, onResult, PlatformFilePicker::save)", source)
        self.assertEqual(2, source.count("actual fun rememberFileSaverLauncher("))
        for phrase in ("internal fun rememberDesktopFileSaverLauncher", "val currentSaveFile by rememberUpdatedState(saveFile)",
                       "val currentSettings by rememberUpdatedState(settings)",
                       "val currentParent by rememberUpdatedState(settings.parentWindow ?: LocalFilePickerParentWindow.current)",
                       "val launchParent = currentParent", "val launchSettings = currentSettings", "val launchSaveFile = currentSaveFile",
                       "launchSettings.title, launchParent, source, bytes", "busy.compareAndSet(false, true)",
                       "currentCoroutineContext().ensureActive()", "currentOnResult(", "currentOnError("):
            self.assertIn(phrase, source)

    def test_real_fixture_keeps_visible_Compose_JNI_writer_disposal_and_disclosed_parent_boundary(self):
        source = (r.ROOT / r.DESKTOP_SAVER_STATE_SOURCE).read_text()
        for phrase in ("isVisible = true", "DisposableEffect(Unit)", "awaitLatch(host.disposed)",
                       "withActiveDialogHandle(coroutineContext", "NativeFilePickerBridge.createSaveDialog",
                       "NativeFilePickerBridge.destroyDialog", "NativeFilePickerBridge.showFileDialog(handles.last())",
                       "saveSelectedDesktopFile(", "assertSame(retained, host.launcher.get())",
                       "assertNotSame(local, explicit", "host.errors.last().first", "source.readBytes()",
                       "assertNotNull(host.window.renderApi)", "assertNotNull(other.renderApi)",
                       "assertEquals(GraphicsApi.SOFTWARE_FAST, renderer)",
                       "assertEquals(GraphicsApi.SOFTWARE_FAST, parentRenderer)",
                       "native modality/focus", "0).also"):
            self.assertIn(phrase, source)
        self.assertNotIn("PlatformFilePicker.save(", source)
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertIn("inputs.profile == 'picker-saver-state') && 1 || 2", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("packages: write", workflow)

    def test_software_renderer_request_is_exact_Linux_nonchooser_profile_not_a_native_or_full_suite_waiver(self):
        workflow = (r.ROOT / ".github/workflows/gradle.yml").read_text()
        self.assertEqual(1, workflow.count("SKIKO_RENDER_API:"))
        self.assertIn("SKIKO_RENDER_API: " + chr(36) +
                      "{{ inputs.profile == 'picker-saver-state' && runner.os == 'Linux' && 'SOFTWARE_FAST' || '' }}", workflow)
        source = (r.ROOT / r.DESKTOP_SAVER_STATE_SOURCE).read_text()
        self.assertIn('if (System.getenv("SKIKO_RENDER_API") == "SOFTWARE_FAST")', source)
        self.assertNotIn('assumeTrue(', source)
        self.assertNotIn('GraphicsEnvironment.isHeadless', source)
        self.assertIn("no GPU certification", source)

    def test_cli_selects_exact_finite_focus(self):
        result = subprocess.run([r.sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan", "--suite", "desktop",
                                 "--module", "calf-file-picker", "--focus", r.DESKTOP_SAVER_STATE_FOCUS],
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__": unittest.main()
