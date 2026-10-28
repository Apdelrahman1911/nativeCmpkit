"""Finite browser IO/Coil selection guards. Synthetic tooling, not browser executions."""
from collections import Counter
import copy
import os
from pathlib import Path
import tempfile
import time
import unittest
from xml.etree import ElementTree as ET

import library_tests as r
import workflow_matrix as m


class BrowserCoilReadFocusTests(unittest.TestCase):
    def test_coil_bundle_uses_the_actual_compose_resource_plugin_without_production_transformations(self):
        source = (r.ROOT / "calf-file-picker-coil/build.gradle.kts").read_text()
        self.assertIn('id("compose.multiplatform")', source)
        self.assertIn("targetKotlinPlatforms.set(emptySet())", source)
        self.assertNotIn("libs.kotlinx.browser", source)
        self.assertNotIn("os-browserify", source)
        self.assertNotIn("path-browserify", source)
        owning = (r.ROOT / "convention-plugins/src/main/kotlin/compose.multiplatform.gradle.kts").read_text()
        self.assertIn('id("org.jetbrains.compose")', owning)
        self.assertIn("configureBrowserTestBundles()", owning)

    def plan(self, suite="wasm"):
        return r.plan(r.ROOT, suite, only_modules=(r.BROWSER_COIL_READ_MODULE,), focus=r.BROWSER_COIL_READ_FOCUS)

    def cases(self, suite="wasm"):
        target = "js" if suite == "js" else "wasmJs"
        return [{"classname": r.SUITES[suite][0] + "." + c["classname"],
                 "name": c["name"] + "[" + target + ", browser, ChromeHeadless155.0, Linux0.0]"}
                for c in r.browser_coil_read_identities()]

    def collect(self, cases=None, suite="wasm", outcome="", marker=1, stale=False, duplicate=False):
        plan = self.plan(suite)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / plan["expected"][0]["report_directory"]
            reports.mkdir(parents=True)
            document = ET.Element("testsuite")
            for c in self.cases(suite) if cases is None else cases:
                node = ET.SubElement(document, "testcase", **c)
                if outcome:
                    ET.SubElement(node, outcome)
            path = reports / "TEST-synthetic.xml"
            path.write_bytes(ET.tostring(document))
            if duplicate:
                (reports / "TEST-duplicate.xml").write_bytes(path.read_bytes())
            now = time.time_ns()
            if stale:
                os.utime(path, ns=(now - 10_000_000_000, now - 10_000_000_000))
            return r.collect_reports(root, plan, now - 1_000_000_000, now + 1_000_000_000,
                                     Counter({plan["expected"][0]["task"]: marker}), host_system="Linux")

    def test_two_finite_targets_and_failure_only_profiles_do_not_replay_other_modules(self):
        rows = m.matrix("browser-coil-io")["include"]
        self.assertEqual(["browser-js", "browser-wasm"], [row["slot"] for row in rows])
        for row in rows:
            self.assertEqual(r.BROWSER_COIL_READ_MODULE, row["test-modules"])
            self.assertEqual(r.BROWSER_COIL_READ_FOCUS, row["test-focus"])
        for profile, slot in (("browser-coil-io-js", "browser-js"), ("browser-coil-io-wasm", "browser-wasm")):
            self.assertEqual([slot], [row["slot"] for row in m.matrix(profile)["include"]])
        for profile in ("all", "browser", "core", "ios-ui"):
            self.assertTrue(all("test-focus" not in row for row in m.matrix(profile)["include"]))

    def test_only_four_declared_methods_run_and_new_module_is_required_in_full_browser_suites(self):
        for suite in ("js", "wasm"):
            plan = self.plan(suite)
            self.assertFalse(plan["complete_suite_requested"])
            self.assertEqual(r.browser_coil_read_identities(), plan["expected"][0]["required_testcases"])
            self.assertTrue(r.validate_test_focus(plan))
            self.assertIn(r.BROWSER_COIL_READ_MODULE, r.MINIMUM_MODULES[suite])
            self.assertEqual([":calf-file-picker-coil:" + r.SUITES[suite][0], "--tests", r.BROWSER_COIL_READ_CLASS],
                             r.gradle_command(suite, plan)[-3:])
            self.assertEqual([], self.collect(suite=suite)["errors"])
            self.assertEqual(4, self.collect(suite=suite)["totals"]["passed"])

    def test_wrong_scope_task_filter_inputs_and_full_suite_claims_are_rejected(self):
        for suite, modules in (("ios", (r.BROWSER_COIL_READ_MODULE,)), ("desktop", (r.BROWSER_COIL_READ_MODULE,)),
                               ("js", ("calf-io",)), ("wasm", None)):
            with self.subTest(suite=suite, modules=modules), self.assertRaises(ValueError):
                r.plan(r.ROOT, suite, only_modules=modules, focus=r.BROWSER_COIL_READ_FOCUS)
        for key, value in (("task", ":calf-file-picker-coil:publish"), ("test_filter", "*"),
                           ("required_testcases", []), ("test_source_files", [])):
            plan = copy.deepcopy(self.plan())
            plan["expected"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                r.validate_test_focus(plan)
        plan = self.plan()
        plan["complete_suite_requested"] = True
        with self.assertRaises(ValueError):
            r.validate_test_focus(plan)
        with self.assertRaises(ValueError):
            r.gradle_command("js", self.plan("wasm"))

    def test_positive_current_plan_precedes_declaration_drift_and_missing_native_fixture_rejection(self):
        source = (r.ROOT / r.BROWSER_COIL_READ_SOURCE).read_text()
        self.assertTrue(r.validate_test_focus(self.plan()))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "settings.gradle.kts").write_text('include(\n    ":calf-file-picker-coil",\n)\n')
            module = root / r.BROWSER_COIL_READ_MODULE
            module.mkdir()
            (module / "build.gradle.kts").write_text("// synthetic build, never executed\n")
            changed = root / r.BROWSER_COIL_READ_SOURCE
            changed.parent.mkdir(parents=True)
            changed.write_text(source)
            fixture = root / r.browser_coil_read_fixture("wasm")
            fixture.parent.mkdir(parents=True)
            fixture.write_text((r.ROOT / r.browser_coil_read_fixture("wasm")).read_text())

            def temporary_plan():
                return r.plan(root, "wasm", only_modules=(r.BROWSER_COIL_READ_MODULE,),
                              focus=r.BROWSER_COIL_READ_FOCUS)

            # Calibrate a valid checkout first; rejection must come from the
            # mutation/missing real source, not absent settings or build files.
            self.assertTrue(r.validate_test_focus(temporary_plan()))
            for content in (source.replace(r.BROWSER_COIL_READ_METHODS[0], "wrongMethod", 1),
                            source.replace("@Test", "@IgnoredTest", 1), source + "\n@Test fun unrelated() {}\n"):
                changed.write_text(content)
                with self.assertRaises(ValueError):
                    temporary_plan()
            changed.write_text(source)
            self.assertTrue(r.validate_test_focus(temporary_plan()))
            fixture.unlink()
            with self.assertRaises(ValueError):
                temporary_plan()

    def test_missing_extra_duplicate_or_foreign_browser_identities_do_not_pass(self):
        original = self.cases()
        variants = [[], original[:-1], original * 2, [*original, {**original[0], "name": "unrelated[wasmJs, browser, Chrome]"}]]
        for key, value in (("classname", r.BROWSER_COIL_READ_CLASS), ("classname", "jsBrowserTest." + r.BROWSER_COIL_READ_CLASS),
                           ("name", r.BROWSER_COIL_READ_METHODS[0]),
                           ("name", r.BROWSER_COIL_READ_METHODS[0] + "[js, browser, Chrome]")):
            changed = copy.deepcopy(original)
            changed[0][key] = value
            variants.append(changed)
        for cases in variants:
            with self.subTest(cases=cases):
                self.assertTrue(self.collect(cases)["errors"])
        self.assertTrue(self.collect(duplicate=True)["errors"])

    def test_failed_errored_skipped_stale_or_missing_actual_task_is_not_success(self):
        for outcome in ("failure", "error", "skipped"):
            with self.subTest(outcome=outcome):
                self.assertTrue(self.collect(outcome=outcome)["errors"])
        self.assertTrue(self.collect(stale=True)["errors"])
        self.assertTrue(self.collect(marker=0)["errors"])

    def test_real_fixture_forwards_native_read_and_restores_exact_constructor_descriptor(self):
        for suite in ("js", "wasm"):
            text = (r.ROOT / r.browser_coil_read_fixture(suite)).read_text()
            for required in ("new Original()", "originalRead.call(reader, file)", "new DOMException",
                             "globalThis.FileReader !== state.wrapper", "Object.defineProperty(globalThis, 'FileReader', state.descriptor)"):
                self.assertIn(required, text)
        source = (r.ROOT / r.BROWSER_COIL_READ_SOURCE).read_text()
        for required in ("operation.dispose()", "operation.job.join()", "FileReader.LOADING", "assertDetached(reader)",
                         "loader.execute(request)", "loader.enqueue(request)", "8 * 1024 * 1024", "SecurityError"):
            self.assertIn(required, source)

    def test_dependency_repair_belongs_to_the_public_api_owner_not_a_test_classpath_workaround(self):
        for module in ("calf-io", "calf-file-picker"):
            source = (r.ROOT / module / "build.gradle.kts").read_text()
            web = source.split("sourceSets.webMain.dependencies {", 1)[1].split("}", 1)[0]
            self.assertIn("api(libs.kotlinx.browser)", web)
            self.assertNotIn("implementation(libs.kotlinx.browser)", web)
        self.assertNotIn("libs.kotlinx.browser", (r.ROOT / "calf-file-picker-coil/build.gradle.kts").read_text())
