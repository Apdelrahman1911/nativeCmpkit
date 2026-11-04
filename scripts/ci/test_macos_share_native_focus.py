"""NEW finite selector/host/fresh XML controls; zero AppKit/JNI executions."""
from collections import Counter
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as runner
import macos_share_native_focus as share
import workflow_matrix as matrix


class MacOsShareNativeFocusTests(unittest.TestCase):
    def plan(self):
        return runner.plan(runner.ROOT, "desktop", only_modules=(share.MODULE,), focus=share.FOCUS)

    def collect(self, identities=None, status="", host="Darwin", opted_in=True, markers=1,
                extra_empty=False, split=False, stale=False):
        plan = self.plan()
        identities = share.identities() if identities is None else identities
        def document(items):
            return "<testsuite>" + "".join(
                f'<testcase classname="{item["classname"]}" name="{item["name"]}">{status}</testcase>'
                for item in items) + "</testsuite>"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = plan["expected"][0]
            reports = root / expected["report_directory"]
            reports.mkdir(parents=True)
            path = reports / "TEST-synthetic.xml"
            path.write_text(document(identities))
            if extra_empty:
                (reports / "TEST-synthetic-empty.xml").write_text("<testsuite/>")
            if split:
                path.write_text(document(identities[:1]))
                (reports / "TEST-synthetic-rest.xml").write_text(document(identities[1:]))
            now = time.time_ns()
            if stale:
                os.utime(path, ns=(now - 4_000_000_000, now - 4_000_000_000))
            return runner.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                Counter({expected["task"]: markers}), host_system=host, native_ui_opt_in=opted_in)

    def test_only_three_new_methods_and_one_fixed_opted_in_mac_host_are_selected(self):
        rows = matrix.matrix(share.PROFILE)["include"]
        self.assertEqual([{"slot": "desktop-macos-arm64", "suite": "desktop", "runner": "macos-26",
            "arch": "arm64", "python": "python3", "native-ui": "true", "test-modules": share.MODULE,
            "test-focus": share.FOCUS}], rows)
        plan = self.plan()
        self.assertFalse(plan["complete_suite_requested"])
        self.assertEqual([share.MODULE], plan["explicit_module_subset"])
        self.assertEqual(1, len(plan["expected"]))
        self.assertEqual(share.TASK, plan["expected"][0]["task"])
        self.assertEqual(share.identities(), plan["expected"][0]["required_testcases"])
        with patch.object(runner.platform, "system", return_value="Darwin"), \
             patch.object(runner.platform, "machine", return_value="arm64"):
            self.assertEqual(["--tests", share.CLASS + ".*"], runner.gradle_command("desktop", plan)[-2:])
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual((3, 0), (result["totals"]["passed"], result["totals"]["not_applicable"]))

    def test_other_modules_suites_filters_and_publish_tasks_are_refused(self):
        for suite, modules in (("ios", (share.MODULE,)), ("desktop", ("calf-file-picker",)),
                               ("desktop", ("calf-ui",)), ("desktop", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                runner.plan(runner.ROOT, suite, only_modules=modules, focus=share.FOCUS)
        for key, value in (("test_filter", "*"), ("required_testcases", []), ("task", ":calf-share:publish")):
            plan = copy.deepcopy(self.plan()); plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.gradle_command("desktop", plan)

    def test_current_methods_default_native_owner_and_real_lifetime_checks_are_required(self):
        source = (runner.ROOT / share.SOURCE).read_text()
        share.validate_source(source, [share.SOURCE])
        variants = (source.replace(share.METHODS[0], "foreignMethod", 1),
            source.replace("@Test", "@Ignore @Test", 1), source + "\n@Test fun extraMethod() {}\n",
            source.replace("DesktopShareOwner(scope,", "FakeShareOwner(scope,"),
            source.replace("NativeShareBridge.liveUiOperationCount()", "0"))
        for changed in variants:
            with self.subTest(change=changed[-50:]), self.assertRaises(ValueError):
                share.validate_source(changed, [share.SOURCE])
        with self.assertRaises(ValueError): share.validate_source(source, [])

    def test_command_execution_refuses_other_hosts_and_intel_substitution(self):
        for host, arch in (("Linux", "aarch64"), ("Windows", "arm64"), ("Darwin", "x86_64")):
            with self.subTest(host=host, arch=arch), \
                 patch.object(runner.platform, "system", return_value=host), \
                 patch.object(runner.platform, "machine", return_value=arch), self.assertRaises(ValueError):
                runner.gradle_command("desktop", self.plan())
        share.validate_host("Darwin", "arm64")

    def test_missing_duplicate_accepted_foreign_or_target_suffix_methods_never_pass(self):
        expected = share.identities()
        variants = [expected[:-1], [*expected, expected[0]], [*expected,
            {"classname": "com.mohamedrejeb.calf.share.platform.NativeShareBridgeTest", "name": "accepted[desktop]"}]]
        for key, value in (("classname", "Foreign"), ("name", share.METHODS[0] + "[iosSimulatorArm64]")):
            changed = copy.deepcopy(expected); changed[0][key] = value; variants.append(changed)
        for identities in variants:
            with self.subTest(identities=identities): self.assertTrue(self.collect(identities)["errors"])

    def test_failures_skips_opt_out_and_opposite_host_na_cannot_be_native_green(self):
        for status in ("<failure/>", "<error/>", "<skipped/>"):
            with self.subTest(status=status): self.assertTrue(self.collect(status=status)["errors"])
        self.assertTrue(self.collect(opted_in=False)["errors"])
        self.assertTrue(self.collect(host="Linux", status="<skipped/>")["errors"])
        self.assertTrue(self.collect(host="Windows")["errors"])

    def test_one_fresh_original_and_exactly_one_real_task_marker_are_required(self):
        for options in ({"extra_empty": True}, {"split": True}, {"stale": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(options=options): self.assertTrue(self.collect(**options)["errors"])

    def test_cli_preflight_and_same_host_rust_step_preserve_independent_library_failure(self):
        result = subprocess.run([sys.executable, str(runner.ROOT / "scripts/ci/library_tests.py"), "plan",
            "--suite", "desktop", "--module", share.MODULE, "--focus", share.FOCUS],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(share.identities(), json.loads(result.stdout)["expected"][0]["required_testcases"])
        self.assertEqual(1, len(matrix.preflight_plans(share.PROFILE)["slots"]))
        workflow = (runner.ROOT / ".github/workflows/gradle.yml").read_text()
        rust = workflow.index("scripts/ci/macos_share_appkit_lifecycle.py --output")
        native = workflow.index("      - name: Fresh actual library suite with strict nonzero receipts")
        self.assertLess(rust, native)
        self.assertIn("!cancelled() && inputs.profile == 'macos-share-lifecycle' && steps.plan.outcome == 'success'", workflow)
        following = workflow[native:workflow.index("        env:", native)]
        self.assertIn("!cancelled() && steps.plan.outcome == 'success'", following)
        self.assertNotIn("continue-on-error", workflow[:native])


if __name__ == "__main__":
    unittest.main()
