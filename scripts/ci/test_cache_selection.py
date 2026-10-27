"""Synthetic selection/key contracts, not Actions cache or library runtime passes."""
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import dependency_cache_inputs as d
import workflow_matrix as m


class CacheSelectionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-selection-key-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "settings.gradle.kts").write_text(
            'include(\n ":calf-core", ":calf-io", ":calf-ui",\n)\n')
        for module in ("calf-core", "calf-io", "calf-ui"):
            directory = self.root / module
            directory.mkdir()
            (directory / "build.gradle.kts").write_text("// Synthetic configured library build\n")

    def selection(self, value):
        return d.selection_contract(self.root, value)

    def test_multi_module_workflow_never_embeds_the_raw_comma_separated_selector_in_a_cache_key(self):
        source = (Path(__file__).resolve().parents[2] / ".github/workflows/gradle.yml").read_text()
        keys = re.findall(r"(?m)^\s*key: ([^\n]+)$", source)
        self.assertEqual(2, len(keys))
        self.assertNotIn("matrix.test-modules", keys[0])
        self.assertIn("steps.cache-inputs.outputs.selection", keys[0])

    def test_complete_selection_has_an_explicit_safe_all_token(self):
        self.assertEqual({"cache_key": "all", "modules": []}, self.selection(""))

    def test_one_module_is_content_bound_not_a_raw_path_token(self):
        result = self.selection("calf-core")
        self.assertEqual(["calf-core"], result["modules"])
        self.assertRegex(result["cache_key"], r"\Asubset-[0-9a-f]{64}\Z")
        self.assertNotIn("calf-core", result["cache_key"])

    def test_permuted_identical_module_sets_can_reuse_the_same_selection_key(self):
        left = self.selection("calf-core,calf-io")
        right = self.selection("calf-io,calf-core")
        self.assertEqual(left, right)
        self.assertEqual(["calf-core", "calf-io"], left["modules"])
        self.assertNotIn(",", left["cache_key"])

    def test_different_cardinality_and_module_identity_are_not_silently_shared(self):
        values = ["", "calf-core", "calf-io", "calf-core,calf-io", "calf-core,calf-ui"]
        keys = [self.selection(value)["cache_key"] for value in values]
        self.assertEqual(len(keys), len(set(keys)))

    def test_duplicate_modules_are_rejected_not_deduplicated_without_disclosure(self):
        for value in ["calf-core,calf-core", "calf-core,calf-io,calf-core"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.selection(value)

    def test_spaces_empty_elements_controls_and_shell_shapes_are_rejected(self):
        for value in [" ", "calf-core,", ",calf-core", "calf-core,,calf-io", " calf-core",
                      "calf-core ", "calf-core,\ncalf-io", "calf-core\r", "calf-core\t",
                      "calf-core;echo unsafe", "calf-core/../calf-io", "../calf-core", "calf-core\0"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.selection(value)

    def test_unknown_excluded_and_noncanonical_gradle_aliases_are_rejected(self):
        for value in ["all", "calf-media", "calf-missing", ":calf-core", "calf-permissions:core", "calf-core/"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.selection(value)

    def test_nonstring_and_unbounded_selection_never_become_keys(self):
        for value in [None, True, ["calf-core"], 7, "a" * 4097]:
            with self.subTest(type=type(value).__name__), self.assertRaises(ValueError):
                self.selection(value)

    def test_configured_nested_project_is_preserved_but_not_inserted_raw_in_the_key(self):
        root = Path(__file__).resolve().parents[2]
        result = d.selection_contract(root, "calf-permissions/core")
        self.assertEqual(["calf-permissions/core"], result["modules"])
        self.assertRegex(result["cache_key"], r"\Asubset-[0-9a-f]{64}\Z")
        self.assertNotIn("/", result["cache_key"])

    def test_every_finite_profile_produces_distinct_slot_bound_action_compatible_keys(self):
        root = Path(__file__).resolve().parents[2]
        runner_os = {
            "ubuntu-24.04": "Linux", "ubuntu-24.04-arm": "Linux",
            "macos-26": "macOS", "macos-26-intel": "macOS", "windows-2025": "Windows",
        }
        for profile in m.PROFILES:
            rows = m.matrix(profile)["include"]
            keys = []
            for row in rows:
                selection = d.selection_contract(root, row.get("test-modules", ""))
                # Actual runner.os value, not the runs-on label, plus fixed
                # architecture/slot/suite and two real-shaped
                # fingerprints. This executes no cache action or native suite.
                key = "nativecmpkit-deps-v2-" + "-".join(
                    [runner_os[row["runner"]], row["arch"], row["slot"], row["suite"],
                     selection["cache_key"], "a" * 64, "b" * 64])
                self.assertNotIn(",", key, profile)
                self.assertLessEqual(len(key), 512, profile)
                self.assertRegex(key, r"\A[A-Za-z0-9_-]+\Z")
                keys.append(key)
            self.assertEqual(len(keys), len(set(keys)), profile)

    def test_selection_is_revision_root_and_documentation_independent(self):
        before = self.selection("calf-core,calf-io")
        (self.root / "AGENTS.md").write_text("synthetic unrelated documentation")
        with patch.object(d.lt, "git_revision", side_effect=AssertionError("No revision in selection identity")):
            self.assertEqual(before, self.selection("calf-io,calf-core"))

    def test_cli_retains_the_64_hex_dependency_digest_and_records_canonical_selection(self):
        output = "build/ci-runtime/selection.json"
        configured = {"settings.gradle.kts": "a" * 64}
        with patch.object(d, "ROOT", self.root), patch.object(d, "selected_inputs", return_value=configured), \
                patch.object(d.lt, "git_revision", return_value="b" * 40), \
                patch.object(sys, "argv", ["dependency_cache_inputs.py", "--scope", "libraries",
                    "--selection", "calf-io,calf-core", "--output", output]), \
                patch.object(sys, "stdout", io.StringIO()) as stdout:
            self.assertEqual(0, d.main())
            self.assertEqual(d.fingerprint("libraries", configured) + "\n", stdout.getvalue())
        receipt = json.loads((self.root / output).read_bytes())
        self.assertEqual(["calf-core", "calf-io"], receipt["selected_modules"])
        self.assertEqual(self.selection("calf-core,calf-io")["cache_key"], receipt["selection_cache_key"])
        self.assertFalse(receipt["compiled_or_test_results_reused"])
        self.assertFalse(receipt["ordinary_dependency_trust_certified"])

    def test_core_io_scope_does_not_claim_a_caller_selected_library_subset(self):
        with patch.object(d, "ROOT", self.root), patch.object(sys, "argv",
                ["dependency_cache_inputs.py", "--scope", "core-io", "--selection", "calf-core",
                 "--output", "build/ci-runtime/rejected.json"]), self.assertRaises(ValueError):
            d.main()
        self.assertFalse((self.root / "build/ci-runtime/rejected.json").exists())

    def test_invalid_selector_cannot_emit_a_receipt_or_cache_output(self):
        with patch.object(d, "ROOT", self.root), patch.object(d, "selected_inputs", return_value={"x": "a" * 64}), \
                patch.object(sys, "argv", ["dependency_cache_inputs.py", "--scope", "libraries",
                    "--selection", "calf-core,", "--output", "build/ci-runtime/rejected.json"]), \
                patch.object(sys, "stdout", io.StringIO()) as stdout, self.assertRaises(ValueError):
            d.main()
        self.assertFalse((self.root / "build/ci-runtime/rejected.json").exists())
        self.assertEqual("", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
