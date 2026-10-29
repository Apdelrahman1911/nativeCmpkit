"""Finite real GTK selection/outcome guards; synthetic tooling, NOT JNI tests."""
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest

import library_tests as r
import native_test_policy as policy
import picker_dialog_context as portal
import test_desktop_saver_state_focus as fixture
import workflow_matrix as matrix


class LinuxPickerPortalFocusTests(unittest.TestCase):
    def plan(self, root=r.ROOT):
        return r.plan(root, "desktop", only_modules=("calf-file-picker",), focus=r.LINUX_PICKER_PORTAL_FOCUS)

    def collect(self, cases=None, **kwargs):
        helper = fixture.DesktopSaverStateFocusTests()
        helper.plan = self.plan
        return helper.collect(r.linux_picker_portal_identities() if cases is None else cases, **kwargs)

    def test_three_actual_methods_share_one_linux_job_without_accepted_native_replay(self):
        row, = matrix.matrix("picker-linux-portal")["include"]
        self.assertEqual(("desktop-linux-x64", "desktop", "calf-file-picker", r.LINUX_PICKER_PORTAL_FOCUS),
                         tuple(row[k] for k in ("slot", "suite", "test-modules", "test-focus")))
        plan = self.plan()
        self.assertTrue(r.validate_test_focus(plan))
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual(r.linux_picker_portal_identities(), plan["expected"][0]["required_testcases"])
        self.assertEqual([":calf-file-picker:desktopTest", "--tests", r.LINUX_PICKER_PORTAL_CLASS], r.gradle_command("desktop", plan)[-3:])
        self.assertTrue(portal.OwnedPickerPortal(r.ROOT, Path("unused"), plan).requested)
        self.assertEqual(11, len(matrix.matrix("all")["include"]))
        self.assertTrue(all(c["classname"] != r.PICKER_LIFETIME_CLASS for c in r.linux_picker_portal_identities()))
        result = subprocess.run([r.sys.executable, "scripts/ci/library_tests.py", "plan", "--suite", "desktop",
                                 "--module", "calf-file-picker", "--focus", r.LINUX_PICKER_PORTAL_FOCUS],
                                cwd=r.ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_focus_requires_all_fresh_exact_nonzero_linux_XML_without_native_skips(self):
        self.assertEqual([], self.collect()["errors"])
        self.assertEqual(3, self.collect()["totals"]["passed"])
        for status in ("failed", "error", "skipped"):
            self.assertTrue(self.collect(status=status)["errors"])
        for host in ("Darwin", "Windows"):
            self.assertTrue(self.collect(host=host)["errors"])
            self.assertTrue(self.collect(host=host, status="skipped")["errors"])
        cases = r.linux_picker_portal_identities()
        for invalid in ([], cases[:-1], cases * 2, r.picker_lifetime_identities(),
                        [{**c, "name": c["name"].removesuffix("[desktop]")} for c in cases]):
            self.assertTrue(self.collect(invalid)["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])

    def test_full_desktop_NA_is_exactly_new_linux_methods_not_a_focused_skip_waiver(self):
        for host in ("Linux", "Darwin", "Windows"):
            cases = [{**c, "status": "passed" if host == "Linux" or i < 3 else "skipped"}
                     for i, c in enumerate(r.picker_lifetime_identities())]
            cases += [{**c, "status": "passed" if host == "Linux" else "skipped"} for c in r.linux_picker_portal_identities()]
            scenarios, errors = policy.apply("calf-file-picker", "desktop", cases, host, False)
            self.assertEqual([], errors)
            self.assertEqual(9, len(scenarios))
            self.assertEqual(0 if host == "Linux" else 6, sum(c.get("disposition") == "not-applicable" for c in cases))
            for invalid in (cases[:-1], cases + [copy.deepcopy(cases[-1])]):
                self.assertTrue(policy.apply("calf-file-picker", "desktop", invalid, host, False)[1])

    def test_scope_filter_source_and_exact_method_declarations_cannot_drift(self):
        for suite, modules in (("js", ("calf-file-picker",)), ("ios", ("calf-file-picker",)),
                               ("desktop", ("calf-io",)), ("desktop", None)):
            with self.assertRaises(ValueError): r.plan(r.ROOT, suite, only_modules=modules, focus=r.LINUX_PICKER_PORTAL_FOCUS)
        for key, value in (("task", ":calf-file-picker:publish"), ("test_filter", "*"),
                           ("required_testcases", []), ("test_source_files", [])):
            plan = self.plan(); plan["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(plan)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-file-picker",\n)\n')
            source = root / r.LINUX_PICKER_PORTAL_SOURCE; source.parent.mkdir(parents=True)
            (root / "calf-file-picker/build.gradle.kts").write_text("// synthetic, never compiled\n")
            original = (r.ROOT / r.LINUX_PICKER_PORTAL_SOURCE).read_text(); source.write_text(original)
            old_scenarios = root / r.PICKER_LIFETIME_SOURCE
            old_scenarios.write_bytes((r.ROOT / r.PICKER_LIFETIME_SOURCE).read_bytes())
            self.assertTrue(r.validate_test_focus(self.plan(root)))
            for changed in (original.replace("@Test", "@IgnoredTest", 1), original + "\n@Test fun extra() {}\n"):
                source.write_text(changed)
                with self.assertRaises(ValueError): self.plan(root)

    def test_real_owning_operations_exact_PID_title_binary_empty_cancel_and_join_are_retained(self):
        source = (r.ROOT / r.LINUX_PICKER_PORTAL_SOURCE).read_text()
        for value in ("PlatformFilePicker.pick(", "PlatformFilePicker.save(", "FilePickerSelectionMode.Multiple()",
                      "FilePickerFileType.Folder", '"empty" to byteArrayOf()', '"binary" to byteArrayOf(0, 1, 127, -128, -1)',
                      '"ctrl+a"', '"search", "--all", "--onlyvisible", "--pid"', '"^$title$"',
                      "withContext(NonCancellable)", "owner.join()", "assertContentEquals(bytes, source.readBytes())"):
            self.assertIn(value, source)
        self.assertEqual(3, source.count("@Test fun "))
        self.assertNotIn("ComposeWindow()", source)
        self.assertNotIn("Thread.sleep", source)
        self.assertNotIn("mock", source.lower())


if __name__ == "__main__": unittest.main()
