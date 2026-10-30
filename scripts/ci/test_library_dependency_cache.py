"""Synthetic failure-safe dependency-cache fences, not Actions/native/trust passes."""
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dependency_cache_inputs as d
import library_dependency_cache as c


class LibraryDependencyCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="nativecmpkit-library-cache-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "checkout"
        self.root.mkdir()
        self.home = Path(temporary.name) / "home"
        self.home.mkdir()
        self.write("settings.gradle.kts", 'include(\n ":calf-core", ":calf-io",\n)\n')
        for name in ("build.gradle.kts", "gradle.properties", "calf-core/build.gradle.kts",
                     "calf-io/build.gradle.kts", *d.RECIPE_FILES):
            self.write(name, "synthetic-config-not-executed-" + name)
        inputs = d.selected_inputs(self.root, "libraries")
        selection = d.selection_contract(self.root, "calf-io")
        self.receipt = {"schema_version": 1, "scope": "libraries", "source_revision": "a" * 40,
                        "dependency_input_count": len(inputs), "inputs": inputs,
                        "dependency_inputs_sha256": d.fingerprint("libraries", inputs),
                        "selection_cache_key": selection["cache_key"], "selected_modules": selection["modules"],
                        "compiled_or_test_results_reused": False, "ordinary_dependency_trust_certified": False,
                        "release_readiness_certified": False}

    def write(self, name, body):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
        return path

    def validate(self, record=None, selection="calf-io"):
        with patch.object(c.lt, "git_revision", return_value="a" * 40):
            return c.validate_dependency_observation(self.root, record or self.receipt, selection)

    def test_exact_unchanged_key_and_selection_are_eligible_independent_of_library_failure(self):
        self.assertEqual(self.receipt["dependency_inputs_sha256"], self.validate())
        self.assertNotIn("tests_passed", self.receipt)
        self.write("calf-io/build/test-results/TEST-failed.xml", "not-cached-failed-library-report")
        self.assertEqual(self.receipt["dependency_inputs_sha256"], self.validate())

    def test_changed_recipe_config_or_selection_refuses_save_without_deleting_data(self):
        path = self.root / "calf-io/build.gradle.kts"
        before = path.read_bytes()
        path.write_text("changed-config")
        with self.assertRaises(ValueError):
            self.validate()
        self.assertEqual(b"changed-config", path.read_bytes())
        path.write_bytes(before)
        with self.assertRaises(ValueError):
            self.validate(selection="calf-core")
        path = self.root / "scripts/ci/library_dependency_cache.py"
        path.write_text("changed-owning-validator")
        with self.assertRaises(ValueError):
            self.validate()

    def test_wrong_revision_scope_hash_count_or_success_claims_are_refused(self):
        for update in ({"source_revision": "b" * 40}, {"scope": "core-io"}, {"schema_version": 2},
                       {"dependency_inputs_sha256": "0" * 64}, {"dependency_input_count": 0},
                       {"compiled_or_test_results_reused": True}, {"ordinary_dependency_trust_certified": True},
                       {"release_readiness_certified": True}, {"selected_modules": ["calf-core"]},
                       {"selection_cache_key": "unreviewed"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.validate(self.receipt | update)

    def test_known_candidate_payload_and_all_metadata_versions_forbid_cache_export(self):
        cache = self.home / ".gradle/caches/modules-2"
        for relative in ("files-2.1/" + c.GROUP + "/candidate.jar",
                         "metadata-2.108/descriptors/" + c.GROUP + "/candidate/module.bin",
                         "metadata-2.999/descriptors/" + c.GROUP + "/candidate/module.bin"):
            file = cache / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b"synthetic-candidate-preserved-not-a-package")
            state = c.observe_library_cache(self.home)
            self.assertFalse(state["candidate_group_absent"])
            self.assertEqual(b"synthetic-candidate-preserved-not-a-package", file.read_bytes())
        self.assertEqual(3, sum(c.observe_library_cache(self.home)["candidate_group_paths_present"].values()))

    def test_absent_or_ordinary_registry_cache_is_eligible_not_a_trust_certification(self):
        self.assertTrue(c.observe_library_cache(self.home)["candidate_group_absent"])
        file = self.home / ".gradle/caches/modules-2/files-2.1/org.example/synthetic/dependency.jar"
        file.parent.mkdir(parents=True)
        file.write_bytes(b"untrusted-dependency-not-executed")
        state = c.observe_library_cache(self.home)
        self.assertTrue(state["candidate_group_absent"])
        self.assertFalse(state["ordinary_dependency_trust_certified"])
        self.assertFalse(state["release_readiness_certified"])
        self.assertNotIn(str(self.home), json.dumps(state))

    def test_symlink_unexpected_cache_root_or_unbounded_inventory_refuses_without_cleanup(self):
        cache = self.home / ".gradle/caches/modules-2"
        cache.parent.mkdir(parents=True)
        foreign = self.home / "outside"
        foreign.mkdir()
        cache.symlink_to(foreign, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.observe_library_cache(self.home)
        self.assertTrue(cache.is_symlink())
        cache.unlink(); cache.write_bytes(b"unexpected-file")
        with self.assertRaises(ValueError):
            c.observe_library_cache(self.home)
        self.assertEqual(b"unexpected-file", cache.read_bytes())
        cache.unlink(); cache.mkdir()
        for number in range(3):
            (cache / str(number)).mkdir()
        with patch.object(c, "MAX_CACHE_ROOT_ENTRIES", 2), self.assertRaises(ValueError):
            c.observe_library_cache(self.home)

    def test_linked_candidate_or_metadata_path_is_unknown_not_false_absence(self):
        cache = self.home / ".gradle/caches/modules-2"
        metadata = cache / "metadata-2.108"
        metadata.mkdir(parents=True)
        outside = self.home / "outside"
        outside.mkdir()
        (metadata / "descriptors").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            c.observe_library_cache(self.home)
        self.assertTrue((metadata / "descriptors").is_symlink())

    def invoke(self, phase, env=None):
        with patch.object(c, "ROOT", self.root), patch.object(c.lt, "git_revision", return_value="a" * 40), \
                patch.object(c.Path, "home", return_value=self.home), patch.dict(c.os.environ, env or {}, clear=True), \
                patch("sys.argv", ["library_dependency_cache.py", "--phase", phase, "--selection", "calf-io"]), \
                patch("sys.stdout", new_callable=io.StringIO) as console:
            code = c.main()
        output = self.root / f"build/ci-runtime/library-cache-{phase}.json"
        return code, json.loads(output.read_text()), console.getvalue()

    def observation(self, body=None):
        return self.write("build/ci-runtime/library-dependencies.json", body or json.dumps(self.receipt))

    def test_real_cli_writes_distinct_eligible_restore_and_save_receipts_without_reading_test_outputs(self):
        self.observation()
        for phase in ("restore", "save"):
            code, record, console = self.invoke(phase)
            self.assertEqual(0, code)
            self.assertTrue(record["passed"])
            self.assertEqual(phase, record["phase"])
            self.assertFalse(record["packages_published"])
            self.assertNotIn(str(self.home), json.dumps(record) + console)
        before = (self.root / "build/ci-runtime/library-cache-save.json").read_bytes()
        with self.assertRaises(ValueError):
            self.invoke("save")
        self.assertEqual(before, (self.root / "build/ci-runtime/library-cache-save.json").read_bytes())

    def test_real_cli_candidate_failure_preserves_payload_and_refuses_save_with_safe_receipt(self):
        self.observation()
        candidate = self.home / (".gradle/caches/modules-2/files-2.1/" + c.GROUP + "/candidate.jar")
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(b"PRIVATE_SYNTHETIC_CANDIDATE_NOT_UPLOADED")
        code, record, console = self.invoke("save")
        self.assertEqual(1, code)
        self.assertFalse(record["passed"])
        self.assertFalse(record["cache"]["candidate_group_absent"])
        self.assertEqual("known-candidate-group-absence", record["failure"]["stage"])
        self.assertEqual(b"PRIVATE_SYNTHETIC_CANDIDATE_NOT_UPLOADED", candidate.read_bytes())
        self.assertNotIn("PRIVATE_SYNTHETIC", json.dumps(record) + console)

    def test_real_cli_unknown_input_or_foreign_home_cannot_authorize_export(self):
        self.observation()
        code, record, _ = self.invoke("restore", {"GRADLE_USER_HOME": str(self.home / "other-home")})
        self.assertEqual(1, code)
        self.assertEqual("fixed-library-cache-home", record["failure"]["stage"])
        self.observation('{"schema_version":1,"schema_version":1}')
        code, record, _ = self.invoke("save")
        self.assertEqual(1, code)
        self.assertFalse(record["passed"])
        self.assertEqual("exact-dependency-observation", record["failure"]["stage"])

    def test_real_cli_bounded_observation_refusal_does_not_overwrite_or_slurp_data(self):
        observation = self.observation()
        before = observation.read_bytes()
        with patch.object(c, "MAX_OBSERVATION_BYTES", 1):
            code, record, _ = self.invoke("save")
        self.assertEqual(1, code)
        self.assertFalse(record["passed"])
        self.assertEqual(before, observation.read_bytes())

    def test_unknown_metadata_layout_refuses_instead_of_omitting_candidate_namespace(self):
        path = self.home / ".gradle/caches/modules-2/metadata-unreviewed/descriptors" / c.GROUP
        path.mkdir(parents=True)
        with self.assertRaises(ValueError):
            c.observe_library_cache(self.home)
        self.assertTrue(path.is_dir())

    def test_workflow_saves_only_exact_checked_library_dependencies_even_after_test_failure(self):
        source = (d.ROOT / ".github/workflows/gradle.yml").read_text()
        job = source.split("  library-tests:\n", 1)[1].split("  webview-consumer:\n", 1)[0]
        restore = job.split("- name: Explicit dependency/compiler/runtime/slot-keyed cache", 1)[1].split("- name:", 1)[0]
        self.assertIn("id: dependency-cache", restore)
        self.assertIn("uses: actions/cache/restore@", restore)
        self.assertNotIn("restore-keys:", restore)
        for name in (".gradle/wrapper/dists", ".gradle/caches/modules-2", ".cargo/registry/cache",
                     ".cargo/registry/index", ".konan/dependencies"):
            self.assertIn(name, restore)
        save = job.split("- name: Save checked registry dependencies even when library tests fail", 1)[1].split("- name:", 1)[0]
        self.assertIn("uses: actions/cache/save@", save)
        self.assertIn("!cancelled()", save)
        self.assertIn("steps.dependency-cache-save-check.outcome == 'success'", save)
        self.assertIn("steps.dependency-cache.outputs.cache-hit != 'true'", save)
        self.assertIn("steps.dependency-cache.outputs.cache-primary-key", save)
        self.assertEqual(restore.split("path: |", 1)[1].strip(), save.split("path: |", 1)[1].strip())
        for forbidden in ("build-cache", "test-results", "*.xml", "*.apk", "target/", "packages: write", "continue-on-error"):
            self.assertNotIn(forbidden, save)
        self.assertIn("--phase restore", job)
        self.assertIn("--phase save", job)
        self.assertLess(job.index("--phase restore"), job.index("Source-set-aware expected library tests"))
        self.assertLess(job.index("Fresh actual library suite"), job.index("--phase save"))
        # Packaged consumers deliberately retain their stronger success-only policy.
        consumer = source.split("  consumer-core-io:\n", 1)[1]
        self.assertIn("a failed job cannot save this cache", consumer)
        self.assertNotIn("actions/cache/save@", consumer)


if __name__ == "__main__":
    unittest.main()
