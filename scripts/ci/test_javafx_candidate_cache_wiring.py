"""Workflow-to-real-CLI cache wiring regressions; no hosted/native execution."""
from __future__ import annotations

import fnmatch
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import dependency_cache_inputs as dependencies
import library_dependency_cache as cache


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ".github/workflows/javafx-library-candidate.yml"


class JavaFxCandidateCacheWiringTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-javafx-cache-wiring-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "checkout"
        self.root.mkdir()
        self.home = Path(temporary.name) / "home"
        self.home.mkdir()
        self.workflow = (ROOT / WORKFLOW).read_text(encoding="utf-8")
        self.write("settings.gradle.kts", 'include(\n ":calf-core", ":calf-webview",\n)\n')
        for name in ("build.gradle.kts", "gradle.properties", "calf-core/build.gradle.kts",
                     "calf-webview/build.gradle.kts", *dependencies.RECIPE_FILES):
            self.write(name, "synthetic-config-not-executed-" + name)

    def write(self, relative, body):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def producer_output(self):
        step = self.workflow.split("- name: Exact configured dependency and runtime cache identity\n", 1)[1]
        step = step.split("- name: Restore only the exact established dependency cache", 1)[0]
        matches = re.findall(
            r"scripts/ci/dependency_cache_inputs\.py --scope libraries --selection calf-webview "
            r"\\\n\s*--output (build/ci-runtime/[a-z-]+\.json)", step)
        self.assertEqual(len(matches), 1)
        self.assertIn("--scope libraries --selection calf-webview", step)
        self.assertIn("json.load(open('" + matches[0] + "'))", step)
        return matches[0]

    def produce(self):
        relative = self.producer_output()
        with patch.object(dependencies, "ROOT", self.root), \
                patch.object(dependencies.lt, "git_revision", return_value="a" * 40), \
                patch("sys.argv", ["dependency_cache_inputs.py", "--scope", "libraries",
                                   "--selection", "calf-webview", "--output", relative]), \
                patch("sys.stdout", new_callable=io.StringIO) as console:
            code = dependencies.main()
        self.assertEqual(code, 0)
        record = json.loads((self.root / relative).read_bytes())
        self.assertEqual(console.getvalue().strip(), record["dependency_inputs_sha256"])
        return relative, record

    def restore(self, selection="calf-webview"):
        with patch.object(cache, "ROOT", self.root), \
                patch.object(cache.lt, "git_revision", return_value="a" * 40), \
                patch.object(cache.Path, "home", return_value=self.home), \
                patch.dict(cache.os.environ, {}, clear=True), \
                patch("sys.argv", ["library_dependency_cache.py", "--phase", "restore",
                                   "--selection", selection]), \
                patch("sys.stdout", new_callable=io.StringIO) as console:
            code = cache.main()
        receipt = self.root / "build/ci-runtime/library-cache-restore.json"
        return code, json.loads(receipt.read_bytes()), console.getvalue()

    def test_workflow_producer_observation_reaches_the_real_fixed_path_validator(self):
        relative, dependencies_record = self.produce()
        original = (self.root / relative).read_bytes()
        code, record, console = self.restore()
        self.assertEqual(code, 0, record)
        self.assertTrue(record["passed"])
        self.assertEqual(record["dependency_inputs_sha256"], dependencies_record["dependency_inputs_sha256"])
        self.assertEqual(original, (self.root / relative).read_bytes())
        self.assertTrue(record["cache"]["candidate_group_absent"])
        self.assertFalse(record["compiled_or_test_results_reused"])
        self.assertFalse(record["ordinary_dependency_trust_certified"])
        self.assertFalse(record["release_readiness_certified"])
        self.assertNotIn(str(self.home), json.dumps(record) + console)

    def test_mismatched_selection_still_refuses_without_repairing_the_observation(self):
        relative, _ = self.produce()
        original = (self.root / relative).read_bytes()
        code, record, _ = self.restore("calf-core")
        self.assertEqual(code, 1)
        self.assertFalse(record["passed"])
        self.assertEqual(record["failure"]["stage"], "exact-dependency-observation")
        self.assertEqual(original, (self.root / relative).read_bytes())

    def test_receipt_upload_covers_both_producer_and_failed_cache_observation(self):
        relative = self.producer_output()
        upload = self.workflow.split("- name: Preserve verification receipts only", 1)[1]
        self.assertIn("if: always()", upload)
        paths = upload.split("path: |\n", 1)[1].splitlines()
        patterns = [line.strip() for line in paths if line.strip()]
        for target in (relative, "build/ci-runtime/library-cache-restore.json"):
            with self.subTest(target=target):
                self.assertTrue(any(fnmatch.fnmatchcase(target, pattern) for pattern in patterns))
        self.assertFalse(any(pattern.endswith(("*.jar", "*.class", "*.zip")) for pattern in patterns))

    def test_cache_gate_is_before_the_one_failed_native_case_with_no_fallback_or_save(self):
        step = self.workflow.split("- name: Validate restored cache without deleting or trusting changed bytes\n", 1)[1]
        step = step.split("- name: Full-JAR candidate", 1)[0]
        self.assertIn("library_dependency_cache.py --phase restore --selection calf-webview", step)
        self.assertNotIn("continue-on-error", step)
        self.assertNotIn("||", step)
        self.assertNotIn("restore-keys:", self.workflow)
        self.assertNotIn("actions/cache/save", self.workflow)
        self.assertNotIn("packages: write", self.workflow)
        self.assertEqual(self.workflow.count("run_library_candidate.py"), 1)


if __name__ == "__main__":
    unittest.main()
