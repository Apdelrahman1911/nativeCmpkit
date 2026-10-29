"""Finite native-cache controller regressions; adapters execute ZERO native builds/tests.

The genuine five-host workflow separately invokes real Cargo and validates real
native payloads. Synthetic orchestration receipts here must never replace it.
"""
from contextlib import ExitStack, redirect_stdout
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import native_lock_reproducibility as controller


class NativeLockReproducibilityTest(unittest.TestCase):
    def test_finite_plan_keeps_both_crates_two_empty_caches_and_no_UI_replay(self):
        for platform in controller.native.SUPPORTED_PLATFORMS:
            with self.subTest(platform=platform):
                plan = controller.plan(controller.ROOT, platform)
                self.assertEqual(["calf-file-picker", "calf-share"], plan["modules"])
                self.assertEqual(2, plan["attempts_per_module"])
                self.assertEqual("1.98.0", plan["rust_toolchain"])
                self.assertEqual(controller.native.SUPPORTED_PLATFORMS[platform]["rustTarget"], plan["rust_target"])
                self.assertTrue(plan["cargo_home_and_target_begin_empty_each_attempt"])
                self.assertTrue(plan["cargo_locked"])
                self.assertFalse(plan["accepted_native_UI_suites_replayed"])
                self.assertEqual(0, plan["native_runtime_test_count"])

    def test_nonadvertised_windows_arm64_cannot_substitute_a_target(self):
        with self.assertRaises(ValueError):
            controller.plan(controller.ROOT, "windows-arm64")

    def test_exact_cargo_198_and_historical_refusal_diagnostics_are_recognized(self):
        for text in ("error: cannot update the lock file /private/fixture/Cargo.lock because --locked was passed",
                     "the lock file needs to be updated but --locked was passed"):
            self.assertTrue(controller.lock_refusal(101, text))

    def test_network_manifest_success_and_other_errors_are_not_lock_proof(self):
        for code, text in ((0, "cannot update the lock file because --locked was passed"),
                           (1, "cannot update the lock file because --locked was passed"),
                           (101, "manifest parsing failed"), (101, "network unavailable --locked"),
                           (101, "cannot update cache permissions")):
            self.assertFalse(controller.lock_refusal(code, text))

    def test_root_dependency_fixture_removes_only_its_exact_existing_line(self):
        for module, dependency in controller.DEPENDENCY_PROBES.items():
            text = (controller.ROOT / module / "native/Cargo.toml").read_text()
            changed = controller.remove_root_dependency(text, module)
            removed = [line for line in text.splitlines(keepends=True) if line.startswith(dependency + " =")]
            self.assertEqual(1, len(removed))
            self.assertEqual(text.replace(removed[0], ""), changed)
            self.assertIn("publish = false", changed)
            self.assertIn("[profile.release]", changed)

    def test_no_missing_or_duplicate_dependency_line_can_fake_the_negative_fixture(self):
        for text in ("[dependencies]\nother = '1'\n", "jni = '0.21'\njni = '0.21'\n"):
            with self.assertRaises(ValueError):
                controller.remove_root_dependency(text, "calf-share")

    def test_full_graph_features_are_sorted_and_native_cache_paths_not_exported(self):
        raw = {"packages": [{"id": "/private/cache/root", "name": "root", "version": "1"},
                             {"id": "registry/source/a", "name": "a", "version": "2"}],
               "resolve": {"nodes": [{"id": "registry/source/a", "features": ["b", "a"]},
                                       {"id": "/private/cache/root", "features": []}]}}
        graph = controller.feature_graph(raw)
        self.assertEqual([{"id": "a@2", "features": ["a", "b"]}, {"id": "root@1", "features": []}], graph)
        self.assertNotIn("/private", json.dumps(graph))

    def test_ambiguous_packages_duplicate_nodes_and_malformed_features_are_rejected(self):
        raw = {"packages": [{"id": "root", "name": "root", "version": "1"}],
               "resolve": {"nodes": [{"id": "root", "features": []}]}}
        variants = []
        duplicate_package = copy.deepcopy(raw); duplicate_package["packages"].append({"id": "other", "name": "root", "version": "1"})
        variants.append(duplicate_package)
        duplicate_node = copy.deepcopy(raw); duplicate_node["resolve"]["nodes"].append(copy.deepcopy(raw["resolve"]["nodes"][0]))
        variants.append(duplicate_node)
        for value in (False, [True], ["a", "a"]):
            invalid = copy.deepcopy(raw); invalid["resolve"]["nodes"][0]["features"] = value; variants.append(invalid)
        for invalid in variants:
            with self.assertRaises(ValueError):
                controller.feature_graph(invalid)

    def test_graph_and_metadata_drift_fail_without_claiming_binary_reproducibility(self):
        first = {"graph": {"packages": ["a"]}, "manifest": {"module": "picker", "sha256": "a", "size": 1, "rustToolchain": "1.98.0"}}
        second = copy.deepcopy(first); second["manifest"].update(sha256="b", size=2)
        observed = controller.compare_attempts(first, second)
        self.assertFalse(observed["native_binary_bytes_identical"])
        self.assertFalse(observed["native_binary_sizes_identical"])
        for kind in ("graph", "metadata"):
            changed = copy.deepcopy(first)
            if kind == "graph": changed["graph"]["packages"] = ["b"]
            else: changed["manifest"]["rustToolchain"] = "stable"
            with self.assertRaises(ValueError): controller.compare_attempts(first, changed)

    def test_dependency_controls_are_offline_restored_and_do_not_edit_production(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); crate = root / "calf-share/native"; crate.mkdir(parents=True)
            original = b'[package]\nname="fixture"\nversion="1.0.0"\n[dependencies]\njni = "0.21"\n'
            (crate / "Cargo.toml").write_bytes(original); (crate / "Cargo.lock").write_text("unchanged lock")
            (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel="1.98.0"\n')
            private = root / "private"; private.mkdir()
            graph = {"packages": ["fixture"]}
            refusal = subprocess.CompletedProcess([], 101, b"", b"cannot update the lock file because --locked was passed")
            with patch.object(controller, "capture_metadata", return_value=graph) as metadata, \
                    patch.object(controller.subprocess, "run", return_value=refusal) as command:
                receipt = controller.dependency_refusal(root, "calf-share", ["rustup", "run", "1.98.0"], {}, private, graph)
            self.assertEqual(original, (crate / "Cargo.toml").read_bytes())
            self.assertTrue(receipt["production_manifest_never_modified"])
            self.assertTrue(receipt["lock_bytes_unchanged"])
            self.assertTrue(receipt["restored_control_passed"])
            self.assertEqual(2, metadata.call_count)
            self.assertTrue(all(call.kwargs.get("offline") is True for call in metadata.call_args_list))
            self.assertIn("--locked", command.call_args.args[0]); self.assertIn("--offline", command.call_args.args[0])

    def test_wrong_host_or_dirty_revision_cannot_start_any_build(self):
        with patch.object(controller.native, "current_platform", return_value="macos-arm64"), \
                patch.object(controller.library, "execute") as execute:
            with self.assertRaises(ValueError): controller.run(controller.ROOT, "linux-x64", "build/ci-verification/unused", 8192)
            execute.assert_not_called()
        with patch.object(controller.native, "current_platform", return_value="linux-x64"), \
                patch.object(controller.native, "git_provenance", return_value=("a" * 40, True)), \
                patch.object(controller.library, "execute") as execute:
            with self.assertRaises(ValueError): controller.run(controller.ROOT, "linux-x64", "build/ci-verification/unused", 8192)
            execute.assert_not_called()

    def test_output_cannot_replace_source_previous_evidence_or_other_projects(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(controller.native, "current_platform", return_value="linux-x64"):
            root = Path(tmp); prior = root / "build/ci-verification/prior"; prior.mkdir(parents=True)
            for relative in ("build/ci-verification", "build/ci-verification/prior", "calf-share/native", "../other-project"):
                with self.assertRaises(ValueError): controller.run(root, "linux-x64", relative, 8192)

    def orchestration(self, *, failed=False, changed=False):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); root = Path(tmp.name)
        (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel="1.98.0"\n')
        homes = []; identity = ("a" * 40, False); manifest = {"sha256": "b" * 64, "size": 1, "rustToolchain": "1.98.0"}
        def execute(cwd, command, log, timeout, reserve, *, env):
            home = Path(env["CARGO_HOME"]); target = root / command[command.index("--cargo-target-dir") + 1]
            self.assertFalse(list(home.iterdir())); self.assertFalse(list(target.iterdir()))
            self.assertEqual("2", env["CARGO_BUILD_JOBS"]); self.assertEqual(8192, reserve)
            self.assertEqual("build", command[2]); self.assertIn("0.1.0-SNAPSHOT", command)
            (home / "cached-marker").write_text("new"); (target / "binary-marker").write_text("new")
            homes.append(home); log.write_text("controlled orchestration log, not a native build")
            return {"exit_code": 1 if failed else 0, "elapsed_seconds": 0.01}
        with ExitStack() as stack, redirect_stdout(io.StringIO()):
            stack.enter_context(patch.object(controller.native, "current_platform", return_value="linux-x64"))
            stack.enter_context(patch.object(controller.native, "git_provenance", return_value=identity))
            capture = stack.enter_context(patch.object(controller, "inputs", return_value={"input": "a" * 64}))
            if changed: capture.side_effect = [{"input": "a" * 64}, {"input": "b" * 64}, {"input": "b" * 64}]
            stack.enter_context(patch.object(controller.library, "execute", side_effect=execute))
            stack.enter_context(patch.object(controller.native, "validate_bundle", return_value=[manifest]))
            stack.enter_context(patch.object(controller, "capture_metadata", return_value={"packages": ["controlled"]}))
            stack.enter_context(patch.object(controller, "dependency_refusal", return_value={"lock_bytes_unchanged": True}))
            receipt = controller.run(root, "linux-x64", "build/ci-verification/mock-only", 8192)
        self.assertTrue(all(not path.exists() for path in homes))
        self.assertEqual(0, receipt["native_runtime_tests_executed"])
        self.assertFalse(receipt["release_readiness_certified"])
        self.assertFalse(receipt["packages_releases_deployments_or_Pages_created"])
        self.assertTrue((root / "build/ci-verification/mock-only/receipt.json").is_file())
        return receipt, homes

    def test_orchestration_uses_four_distinct_empty_homes_and_removes_owned_outputs(self):
        receipt, homes = self.orchestration()
        self.assertEqual(4, len(set(homes))); self.assertTrue(receipt["passed"])
        self.assertEqual(2, len(receipt["modules"]))
        self.assertTrue(all(module["completed_empty_cache_builds"] == 2 for module in receipt["modules"]))

    def test_failed_or_changed_input_attempt_keeps_failure_and_never_counts_missing_builds(self):
        failed, homes = self.orchestration(failed=True)
        self.assertFalse(failed["passed"]); self.assertEqual(1, len(homes)); self.assertEqual([], failed["modules"])
        self.assertEqual("empty-cache-native-build", failed["failure_stage"])
        changed, homes = self.orchestration(changed=True)
        self.assertFalse(changed["passed"]); self.assertFalse(changed["input_hashes_before_after_match"])
        self.assertEqual(1, len(homes)); self.assertEqual([], changed["modules"])

    def test_workflow_has_five_actual_hosts_read_only_reports_no_cache_or_UI_replay(self):
        text = (controller.ROOT / ".github/workflows/build-native-libs.yml").read_text()
        block = text.split("\n  native-lock-reproducibility:\n", 1)[1].split("\n  picker-jni-macos-domain:", 1)[0]
        for platform, runner in (("linux-x64", "ubuntu-24.04"), ("linux-arm64", "ubuntu-24.04-arm"),
                                 ("macos-arm64", "macos-26"), ("macos-x64", "macos-26-intel"),
                                 ("windows-x64", "windows-2025")):
            self.assertIn("platform: " + platform, block); self.assertIn("runner: " + runner, block)
        for required in ("max-parallel: 2", "persist-credentials: false", "toolchain: '1.98.0'",
                         "native_lock_reproducibility.py", "*.json", "needs: native-lock-tooling"):
            self.assertIn(required, block)
        for forbidden in ("actions/cache", "setup-gradle", "setup-java", "cargo test", "gradlew", "packages: write", ".private.log"):
            self.assertNotIn(forbidden, block)
        self.assertIn("contents: read", text)


if __name__ == "__main__":
    unittest.main()
