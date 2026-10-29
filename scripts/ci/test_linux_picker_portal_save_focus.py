"""Finite save-only recovery guards; synthetic tooling, not GTK/JNI executions."""
from pathlib import Path
import subprocess
import unittest

import library_tests as r
import picker_dialog_context as portal
import test_linux_picker_portal_focus as fixtures
import workflow_matrix as matrix


class LinuxPickerPortalSaveFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "desktop", only_modules=("calf-file-picker",), focus=r.LINUX_PICKER_PORTAL_SAVE_FOCUS)

    def collect(self, cases=None, **kwargs):
        helper = fixtures.LinuxPickerPortalFocusTests()
        helper.plan = self.plan
        cases = r.linux_picker_portal_identities(r.LINUX_PICKER_PORTAL_SAVE_FOCUS) if cases is None else cases
        return helper.collect(cases, **kwargs)

    def test_one_failed_method_one_linux_job_never_replays_completed_open_or_cancellation(self):
        row, = matrix.matrix("picker-linux-portal-save")["include"]
        self.assertEqual(("desktop-linux-x64", "calf-file-picker", r.LINUX_PICKER_PORTAL_SAVE_FOCUS),
                         tuple(row[k] for k in ("slot", "test-modules", "test-focus")))
        plan = self.plan(); expected = plan["expected"][0]
        self.assertFalse(plan["complete_suite_requested"])
        self.assertTrue(r.validate_test_focus(plan))
        self.assertEqual(1, len(expected["required_testcases"]))
        self.assertEqual(r.LINUX_PICKER_PORTAL_METHODS[1] + "[desktop]", expected["required_testcases"][0]["name"])
        self.assertEqual([":calf-file-picker:desktopTest", "--tests", r.LINUX_PICKER_PORTAL_CLASS + "." + r.LINUX_PICKER_PORTAL_METHODS[1]], r.gradle_command("desktop", plan)[-3:])
        self.assertTrue(portal.OwnedPickerPortal(r.ROOT, Path("unused"), plan).requested)
        self.assertEqual(3, len(r.linux_picker_portal_identities()))
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        result = subprocess.run([r.sys.executable, "scripts/ci/library_tests.py", "plan", "--suite", "desktop",
                                 "--module", "calf-file-picker", "--focus", r.LINUX_PICKER_PORTAL_SAVE_FOCUS],
                                cwd=r.ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_missing_duplicate_extra_skipped_failed_wrong_host_stale_or_unexecuted_cannot_pass(self):
        cases = r.linux_picker_portal_identities(r.LINUX_PICKER_PORTAL_SAVE_FOCUS)
        self.assertEqual([], self.collect()["errors"])
        self.assertEqual(1, self.collect()["totals"]["passed"])
        for invalid in ([], cases * 2, r.linux_picker_portal_identities(),
                        [{**cases[0], "name": r.LINUX_PICKER_PORTAL_METHODS[0] + "[desktop]"}]):
            self.assertTrue(self.collect(invalid)["errors"])
        for status in ("failed", "error", "skipped"):
            self.assertTrue(self.collect(status=status)["errors"])
        for host in ("Darwin", "Windows"):
            self.assertTrue(self.collect(host=host)["errors"])
            self.assertTrue(self.collect(host=host, status="skipped")["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])

    def test_filter_whole_suite_and_source_minimum_cannot_be_changed_to_reduce_coverage(self):
        for key, value in (("task", ":calf-file-picker:publish"), ("test_filter", r.LINUX_PICKER_PORTAL_CLASS),
                           ("required_testcases", r.linux_picker_portal_identities()), ("test_source_files", [])):
            plan = self.plan(); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        plan = self.plan(); plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError): r.validate_test_focus(plan)
        for focus in ("*", "unknown"):
            with self.assertRaises(ValueError): r.linux_picker_portal_identities(focus)

    def test_save_only_entry_is_explicitly_replaced_and_accepted_path_helper_is_unchanged(self):
        source = (r.ROOT / r.LINUX_PICKER_PORTAL_SOURCE).read_text()
        helper = source.split("private suspend fun selectSavePath", 1)[1].split("private suspend fun selectPath", 1)[0]
        self.assertLess(helper.index('"ctrl+l"'), helper.index('"ctrl+a"'))
        self.assertLess(helper.index('"ctrl+a"'), helper.index('"type"'))
        self.assertIn("}) { selectSavePath(it, destination) }", source)
        self.assertIn("}) { selectPath(it, source) }", source)
        self.assertIn("assertEquals(destination.canonicalFile, saved?.canonicalFile)", source)
        self.assertIn("assertContentEquals(content, destination.readBytes())", source)
        self.assertEqual(3, source.count("@Test fun "))


if __name__ == "__main__": unittest.main()
