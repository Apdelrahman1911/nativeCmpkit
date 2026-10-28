"""Exact public-permission selection fixtures; no native/browser authorization execution."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

import library_tests as r
import workflow_matrix as m


class UnsupportedPermissionFocusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.write("settings.gradle.kts", 'include(\n    ":calf-permissions:core",\n)\nproject(":calf-permissions:core").name = "calf-permissions-core"\n')
        self.write("calf-permissions/core/build.gradle.kts", "// synthetic fixture\n")
        self.write(r.UNSUPPORTED_PERMISSION_FIXTURE, "// synthetic shared fixture\n")
        self.source = "package com.mohamedrejeb.calf.permissions\nclass UnsupportedPublicFactoryTest {\n" + \
            "\n".join("@Test fun " + name + "(): TestResult = fake()" for name in r.UNSUPPORTED_PERMISSION_METHODS) + "\n}\n"
        for suite in r.UNSUPPORTED_PERMISSION_SOURCE_SETS:
            self.write(r.unsupported_permission_source(suite), self.source)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def plan(self, suite):
        return r.plan(self.root, suite, only_modules=(r.UNSUPPORTED_PERMISSION_MODULE,), focus=r.UNSUPPORTED_PERMISSION_FOCUS)

    def cases(self, suite):
        prefix = r.SUITES[suite][0] + "." if suite != "desktop" else ""
        suffix = "[desktop]" if suite == "desktop" else "[" + ("js" if suite == "js" else "wasmJs") + ", browser, ChromeHeadless156.0.0.0, Linux0.0.0]"
        return [{"classname": prefix + r.UNSUPPORTED_PERMISSION_CLASS, "name": method + suffix, "status": "passed"}
                for method in r.UNSUPPORTED_PERMISSION_METHODS]

    def test_five_host_jobs_request_only_six_public_factory_methods(self):
        rows = m.matrix("permissions-unsupported")["include"]
        self.assertEqual({"desktop-linux-x64", "desktop-macos-arm64", "desktop-windows-x64", "browser-js", "browser-wasm"}, {x["slot"] for x in rows})
        for row in rows:
            self.assertEqual(r.UNSUPPORTED_PERMISSION_MODULE, row["test-modules"])
            self.assertEqual(r.UNSUPPORTED_PERMISSION_FOCUS, row["test-focus"])
        for suite in r.UNSUPPORTED_PERMISSION_SOURCE_SETS:
            plan = self.plan(suite)
            self.assertTrue(r.validate_test_focus(plan))
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(r.unsupported_permission_identities(), plan["expected"][0]["required_testcases"])
            command = r.gradle_command(suite, plan, root=self.root)
            self.assertEqual(["--tests", r.UNSUPPORTED_PERMISSION_CLASS], command[-2:])

    def test_actual_source_fragments_and_default_full_profiles_remain_present(self):
        for suite in r.UNSUPPORTED_PERMISSION_SOURCE_SETS:
            self.assertTrue((r.ROOT / r.unsupported_permission_source(suite)).is_file())
            p = r.plan(r.ROOT, suite, only_modules=(r.UNSUPPORTED_PERMISSION_MODULE,), focus=r.UNSUPPORTED_PERMISSION_FOCUS)
            self.assertIn(r.UNSUPPORTED_PERMISSION_FIXTURE, p["expected"][0]["test_source_files"])
        for profile in ("core", "browser", "apple", "all"):
            self.assertTrue(all("test-focus" not in row for row in m.matrix(profile)["include"]))

    def test_real_workflow_cli_accepts_the_reviewed_focus_for_all_three_suites(self):
        for suite in r.UNSUPPORTED_PERMISSION_SOURCE_SETS:
            result = subprocess.run(
                [sys.executable, str(r.ROOT / "scripts/ci/library_tests.py"), "plan", "--suite", suite,
                 "--module", r.UNSUPPORTED_PERMISSION_MODULE, "--focus", r.UNSUPPORTED_PERMISSION_FOCUS],
                cwd=r.ROOT, capture_output=True, text=True, timeout=30, check=True,
            )
            plan = json.loads(result.stdout)
            self.assertEqual(r.UNSUPPORTED_PERMISSION_FOCUS, plan["explicit_test_focus"])
            self.assertEqual(r.unsupported_permission_identities(), plan["expected"][0]["required_testcases"])

    def test_wrong_suite_module_or_freeform_focus_is_rejected(self):
        for suite, modules, focus in (("ios", (r.UNSUPPORTED_PERMISSION_MODULE,), r.UNSUPPORTED_PERMISSION_FOCUS),
                                     ("android-host", (r.UNSUPPORTED_PERMISSION_MODULE,), r.UNSUPPORTED_PERMISSION_FOCUS),
                                     ("js", ("calf-ui",), r.UNSUPPORTED_PERMISSION_FOCUS),
                                     ("js", (r.UNSUPPORTED_PERMISSION_MODULE,), "arbitrary.*")):
            with self.assertRaises(ValueError):
                r.plan(self.root, suite, only_modules=modules, focus=focus)

    def test_changed_or_extra_authored_method_requires_selection_review(self):
        for source in (self.source.replace(r.UNSUPPORTED_PERMISSION_METHODS[0], "different"),
                       self.source.replace("\n}", "\n@Test fun extra() {}\n}")):
            self.write(r.unsupported_permission_source("js"), source)
            with self.assertRaises(ValueError): self.plan("js")

    def test_tampered_plan_cannot_escape_its_class_sources_or_scope(self):
        plan = self.plan("js")
        for key, value in (("test_filter", "arbitrary"), ("required_testcases", []), ("test_source_files", [])):
            bad = deepcopy(plan)
            bad["expected"][0][key] = value
            with self.assertRaises(ValueError): r.validate_test_focus(bad)
        with self.assertRaises(ValueError): r.gradle_command("wasm", plan, root=self.root)

    def test_three_actual_task_target_naming_contracts_and_all_six_identities_are_required(self):
        for suite in r.UNSUPPORTED_PERMISSION_SOURCE_SETS:
            good = self.cases(suite)
            self.assertTrue(r.unsupported_permission_case_inventory(suite, good))
            for cases in (good[:-1], good + [good[0]], [good[0], good[0], *good[2:]],
                          [dict(good[0], classname="otherTask." + r.UNSUPPORTED_PERMISSION_CLASS), *good[1:]],
                          [dict(good[0], name="different"), *good[1:]]):
                self.assertFalse(r.unsupported_permission_case_inventory(suite, cases))

    def test_nonzero_unrelated_skipped_or_failed_xml_is_not_a_public_factory_pass(self):
        for disposition in ("unrelated", "failed", "skipped"):
            plan = self.plan("desktop")
            cases = self.cases("desktop")
            if disposition == "unrelated": cases[0]["name"] = "unrelated[desktop]"
            else: cases[0]["status"] = disposition
            body = "".join('<testcase classname="' + x["classname"] + '" name="' + x["name"] + '">' +
                           {"passed": "", "failed": "<failure/>", "skipped": "<skipped/>"}[x["status"]] + '</testcase>' for x in cases)
            self.write(plan["expected"][0]["report_directory"] + "/TEST-permission.xml", "<testsuite>" + body + "</testsuite>")
            now = time.time_ns()
            result = r.collect_reports(self.root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                       Counter({plan["expected"][0]["task"]: 1}))
            self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
