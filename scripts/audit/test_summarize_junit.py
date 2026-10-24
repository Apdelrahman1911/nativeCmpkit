#!/usr/bin/env python3
"""Small local fixture tests for the log-only CI JUnit summarizer."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("summarize_junit", Path(__file__).with_name("summarize_junit.py"))
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class JUnitSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-junit-fixture-")
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def report(self, module, task, name, text):
        path = self.root / module / "build/test-results" / task / ("TEST-" + name + ".xml")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_empty_is_not_inferred_successful_tests(self):
        result = summary.summarize(self.root)
        self.assertEqual(result["report_files"], 0)
        self.assertEqual(result["totals"]["tests"], 0)

    def test_totals_per_task_and_aggregate_exclusion(self):
        self.report("a", "desktopTest", "a", '<testsuite tests="3" failures="1" errors="0" skipped="1"/>')
        self.report("b", "desktopTest", "b", '<testsuite tests="2" failures="0" errors="0" skipped="0"/>')
        self.report("a", "allTests", "aggregate", '<testsuite tests="5" failures="1" skipped="1"/>')
        self.report("a", "jsBrowserTest", "web", '<testsuites><testsuite tests="1"/></testsuites>')
        result = summary.summarize(self.root)
        self.assertEqual(result["report_files"], 3)
        self.assertEqual(result["totals"], dict(tests=6, failures=1, errors=0, skipped=1))
        self.assertEqual(result["by_task"]["desktopTest"]["tests"], 5)

    def test_failure_and_stdout_contents_are_not_copied(self):
        self.report("a", "desktopTest", "a", '<testsuite tests="1" failures="1"><testcase><failure>private-example</failure></testcase><system-out>private-example</system-out></testsuite>')
        self.assertNotIn("private-example", json.dumps(summary.summarize(self.root)))

    def test_malformed_or_unknown_xml_is_reported(self):
        self.report("a", "desktopTest", "broken", "<invalid")
        self.report("a", "desktopTest", "unknown", "<notJUnit/>")
        result = summary.summarize(self.root)
        self.assertEqual(result["report_files"], 0)
        self.assertEqual(len(result["parse_errors"]), 2)

    def test_external_entity_declaration_is_rejected(self):
        declaration = '<!DOCTYPE testsuite [<!ENTITY e SYSTEM "file:///not-read-by-this-test">]><testsuite tests="1">&e;</testsuite>'
        self.report("a", "desktopTest", "entity", declaration)
        encoded = self.root / "a/build/test-results/desktopTest/TEST-utf16.xml"
        encoded.write_bytes(('<?xml version="1.0" encoding="UTF-16"?>' + declaration).encode("utf-16"))
        result = summary.summarize(self.root)
        self.assertEqual(result["report_files"], 0)
        self.assertEqual(len(result["parse_errors"]), 2)
        self.assertEqual(result["parse_errors"][0]["error"], "ValueError")

    def test_output_is_deterministic(self):
        self.report("z", "wasmJsBrowserTest", "z", '<testsuite tests="2"/>')
        self.report("a", "desktopTest", "a", '<testsuite tests="1"/>')
        self.assertEqual(json.dumps(summary.summarize(self.root)), json.dumps(summary.summarize(self.root)))

    def test_fresh_run_excludes_archives_and_caches(self):
        self.report("calf-ui", "desktopTest", "current", '<testsuite tests="1"/>')
        for directory in ["docs/testing/evidence/old/calf-ui", "site/evidence/calf-ui",
                          ".git/fixture", ".gradle/fixture", "node_modules/dependency",
                          "calf-ui/node_modules/dependency"]:
            self.report(directory, "desktopTest", "archived", '<testsuite tests="20"/>')
        result = summary.summarize(self.root)
        self.assertEqual(result["report_files"], 1)
        self.assertEqual(result["totals"]["tests"], 1)
        self.assertEqual(result["reports"][0]["module"], "calf-ui")

    def test_explicit_artifact_root_can_inspect_archived_reports(self):
        self.report("docs/testing/evidence/old/calf-ui", "desktopTest", "archived", '<testsuite tests="20"/>')
        artifact_root = self.root / "docs/testing/evidence/old"
        result = summary.summarize(artifact_root)
        self.assertEqual(result["report_files"], 1)
        self.assertEqual(result["totals"]["tests"], 20)
        self.assertEqual(result["reports"][0]["module"], "calf-ui")


if __name__ == "__main__":
    unittest.main()
