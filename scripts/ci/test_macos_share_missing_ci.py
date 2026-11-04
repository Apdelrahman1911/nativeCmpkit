# SPDX-License-Identifier: Apache-2.0
"""NEW missing-only routing/source/synthetic XML controls; zero AppKit/JNI runs."""
from collections import Counter
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import library_tests as library
import macos_share_missing_ci as share
import macos_share_missing_source_projection as history
import workflow_matrix as workflow

ROOT = Path(__file__).resolve().parents[2]


class MissingShare630CiControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_plan = library.plan(ROOT, "desktop", only_modules=(share.MODULE,), focus=share.FOCUS)

    def plan(self):
        return copy.deepcopy(self.source_plan)

    def command(self, plan=None, *, root=ROOT, host="Darwin", arch="arm64", opt_in="true"):
        with patch.object(library.platform, "system", return_value=host), \
                patch.object(library.platform, "machine", return_value=arch), \
                patch.dict(os.environ, {"NATIVECMPKIT_NATIVE_UI_TESTS": opt_in}):
            return library.gradle_command("desktop", self.plan() if plan is None else plan, root=root)

    def collect(self, *, cases=None, status="", host="Darwin", opted_in=True,
                markers=1, extra=False, stale=False, hardlinked=False):
        plan = self.plan(); expected = plan["expected"][0]
        cases = share.identities() if cases is None else cases
        raw = "<testsuite>" + "".join(
            f'<testcase classname="{case["classname"]}" name="{case["name"]}">{status}</testcase>'
            for case in cases) + "</testsuite>"
        with tempfile.TemporaryDirectory(prefix="share630-synthetic-only-") as temporary:
            root = Path(temporary); folder = root / expected["report_directory"]; folder.mkdir(parents=True)
            target = folder / "TEST-model.xml"; target.write_text(raw)
            if extra: (folder / "TEST-empty-model.xml").write_text("<testsuite/>")
            if hardlinked: target.with_name("private-backing.xml").hardlink_to(target)
            now = time.time_ns()
            if stale: os.utime(target, ns=(now - 10_000_000_000, now - 10_000_000_000))
            return library.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                Counter({expected["task"]: markers}), host_system=host, native_ui_opt_in=opted_in)

    def test_exact_one_missing_jni_plan_command_and_canonical_opted_in_row(self):
        self.assertEqual({"include": [{"slot": "desktop-macos-arm64", "suite": "desktop", "runner": "macos-26",
            "arch": "arm64", "python": "python3", "native-ui": "true", "test-modules": share.MODULE,
            "test-focus": share.FOCUS}]}, workflow.matrix(share.PROFILE))
        plan = self.plan(); expected = plan["expected"][0]
        self.assertIs(False, plan["complete_suite_requested"])
        self.assertEqual([share.MODULE], plan["explicit_module_subset"])
        self.assertEqual(1, len(plan["expected"]))
        self.assertEqual((share.TASK, share.FILTER, share.identities()),
                         (expected["task"], expected["test_filter"], expected["required_testcases"]))
        command = self.command(plan)
        self.assertEqual(["--tests", share.FILTER], command[-2:])
        self.assertEqual(1, command.count(share.TASK))
        self.assertEqual(1, command.count("--tests"))
        self.assertFalse(any("publish" in value or value.endswith(".*") for value in command))
        result = self.collect()
        self.assertEqual([], result["errors"])
        self.assertEqual((1, 0), (result["totals"]["passed"], result["totals"]["not_applicable"]))

    def test_profile_mutations_and_other_suites_or_modules_refuse(self):
        for suite, modules in (("ios", (share.MODULE,)), ("desktop", None),
                               ("desktop", ("calf-ui",)), ("desktop", (share.MODULE, "calf-ui"))):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                library.plan(ROOT, suite, only_modules=modules, focus=share.FOCUS)
        for slots in (("desktop-macos-x64",), ("desktop-macos-arm64", "desktop-linux-x64")):
            with patch.dict(workflow.PROFILES, {share.PROFILE: slots}), self.assertRaises(ValueError):
                workflow.matrix(share.PROFILE)
        with patch.dict(workflow.MODULE_SUBSETS, {share.PROFILE: "calf-ui"}), self.assertRaises(ValueError):
            workflow.matrix(share.PROFILE)
        for key, value in (("arch", "x64"), ("native-ui", "false"), ("runner", "macos-26-intel")):
            slots = copy.deepcopy(workflow.SLOTS)
            next(row for row in slots if row["slot"] == "desktop-macos-arm64")[key] = value
            with patch.object(workflow, "SLOTS", slots), self.assertRaises(ValueError): workflow.matrix(share.PROFILE)

    def test_arbitrary_filters_tasks_populations_and_contract_mutations_refuse(self):
        for key, value in (("test_filter", "*"), ("test_filter", share.CLASS + ".*"),
                ("test_filter_argument", "annotation"), ("test_exclusion_annotation", "Skip"),
                ("task", ":calf-share:publish"), ("report_directory", "foreign/reports"),
                ("required_testcases", []), ("test_source_files", []), (share.CONTRACT_KEY, None)):
            plan = self.plan(); plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): library.validate_test_focus(plan)
        for key, value in (("native_tests_executed", False), ("schema_version", True), ("source_sha256", {}),
                           ("required_testcases", []), ("independent_missing_appkit_cases", [])):
            plan = self.plan(); plan["expected"][0][share.CONTRACT_KEY][key] = value
            with self.subTest(contract=key), self.assertRaises(ValueError): library.validate_test_focus(plan)
        plan = self.plan(); plan["explicit_test_focus"] = "macos-share-coroutine-lifecycle"
        with self.assertRaises(ValueError): library.validate_test_focus(plan)

    def test_actual_arm64_optin_and_exact_inputs_are_required_again_before_command(self):
        for host, arch, opt_in in (("Linux", "aarch64", "true"), ("Windows", "arm64", "true"),
                                  ("Darwin", "x86_64", "true"), ("Darwin", "arm64", "false")):
            with self.subTest(host=host, arch=arch, opt_in=opt_in), self.assertRaises(ValueError):
                self.command(host=host, arch=arch, opt_in=opt_in)
        with tempfile.TemporaryDirectory(prefix="share630-source-only-") as temporary:
            root = Path(temporary)
            for name in share.SOURCE_SHA256:
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertEqual(self.plan()["expected"][0][share.CONTRACT_KEY],
                             share.source_contract(root, self.plan()["expected"][0]["test_source_files"]))
            target = root / share.SOURCE; raw = target.read_bytes()
            target.write_bytes(raw.replace(b"desktopTimeoutMillis = 2_000", b"desktopTimeoutMillis = 20_000", 1))
            with self.assertRaises(ValueError): self.command(root=root)
            target.unlink(); target.symlink_to(ROOT / share.SOURCE)
            with self.assertRaises(ValueError): self.command(root=root)

    def test_missing_duplicate_accepted_foreign_or_wrong_suffix_xml_never_pass(self):
        identity = share.identities()[0]
        cases = [[], [identity, identity], [{**identity, "name": "acceptedCancellation[desktop]"}],
                 [{**identity, "classname": "Foreign"}], [{**identity, "name": share.METHOD + "[iosSimulatorArm64]"}],
                 [identity, {**identity, "name": "independentRealNativeOwnersRejectOverlapWithoutReplacingTheRetainedRequest[desktop]"}]]
        for population in cases:
            with self.subTest(population=population): self.assertTrue(self.collect(cases=population)["errors"])

    def test_red_skipped_stale_empty_nonordinary_and_task_marker_reports_refuse(self):
        for options in ({"status": "<failure/>"}, {"status": "<error/>"}, {"status": "<skipped/>"},
                        {"opted_in": False}, {"host": "Linux"}, {"extra": True}, {"stale": True},
                        {"hardlinked": True}, {"markers": 0}, {"markers": 2}):
            with self.subTest(options=options): self.assertTrue(self.collect(**options)["errors"])

    def test_workflow_keeps_jni_independent_and_only_adds_two_json_xml_artifact_globs(self):
        name = ".github/workflows/gradle.yml"; current = (ROOT / name).read_bytes()
        original = history.source_before_share_missing_ci(name, current).decode(); source = current.decode()
        start = source.index("      - name: Six missing Share630 AppKit cases")
        end = source.index("      - name: Fresh actual library suite with strict nonzero receipts", start)
        appkit = source[start:end]
        self.assertIn("!cancelled() && inputs.profile == 'macos-share-missing-lifecycle' && steps.plan.outcome == 'success'", appkit)
        self.assertIn('macos_share_appkit_lifecycle.py --missing-only-share630 --output "build/ci-verification/$SLOT-appkit"', appkit)
        self.assertNotIn("continue-on-error", appkit)
        following = source[end:source.index("      - name:", end + 1)]
        old_start = original.index("      - name: Fresh actual library suite with strict nonzero receipts")
        old_following = original[old_start:original.index("      - name:", old_start + 1)]
        self.assertEqual(old_following, following)
        self.assertIn("!cancelled() && steps.plan.outcome == 'success'", following)
        self.assertNotIn("success()", following)
        self.assertIn('if [[ -n "$TEST_FOCUS" ]]; then args+=(--focus "$TEST_FOCUS"); fi', following)
        old_paths = {line.strip() for line in original.splitlines() if line.strip().startswith("build/ci-")}
        paths = {line.strip() for line in source.splitlines() if line.strip().startswith("build/ci-")}
        self.assertEqual({"build/ci-verification/${{ matrix.slot }}-appkit/cases/*/*.json",
                          "build/ci-verification/${{ matrix.slot }}-appkit/cases/*/fresh-reports/*.xml"}, paths - old_paths)
        self.assertTrue(old_paths <= paths)
        self.assertEqual(1, source.count("macos-share-missing-lifecycle, "))
        self.assertEqual(1, source.count("--missing-only-share630 --output"))

    def test_carried_assertions_deadlines_accepted_bodies_and_default_eight_runner_are_unchanged(self):
        for name, digest in share.SOURCE_SHA256.items():
            self.assertEqual(digest, hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), name)
        source = (ROOT / share.SOURCE).read_text()
        self.assertEqual(2, source.count("awaitTimeoutRetention(fixture, RetentionPhase."))
        self.assertIn("desktopTimeoutMillis = 2_000, allowClipboardFallback = false", source)
        self.assertIn('awaitCondition("Actual AppKit operation was not retained", 10_000)', source)
        self.assertIn("throw error // Preserve the original assertion and independent owned cleanup.", source)
        self.assertIn("share630_source_contract", (ROOT / "scripts/ci/macos_share_missing_ci.py").read_text())


if __name__ == "__main__":
    unittest.main()
