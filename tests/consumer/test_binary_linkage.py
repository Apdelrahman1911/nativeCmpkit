"""Receipt/classpath helper tests only; these do NOT execute javac or Java."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import binary_linkage as linkage
from verify_artifacts import InvalidArtifact, sha256


class _FileFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def jar(self, name="dependency.jar", entry="thirdparty/Fixture.class"):
        path = self.root / name
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(entry, b"synthetic, never executed")
        return path

    def record(self, path):
        return {"path": path.relative_to(self.root).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}


class BinaryLinkageHelpersTest(_FileFixture):
    def test_hash_inventory_matches_actual_bytes(self):
        path = self.jar()
        self.assertEqual({path.name: path}, linkage.verified_files(self.root, [self.record(path)]))

    def test_hash_inventory_rejects_tampering(self):
        path = self.jar()
        record = self.record(path)
        path.write_bytes(b"changed")
        with self.assertRaises(InvalidArtifact):
            linkage.verified_files(self.root, [record])

    def test_hash_inventory_rejects_duplicate_file(self):
        path = self.jar()
        record = self.record(path)
        with self.assertRaises(InvalidArtifact):
            linkage.verified_files(self.root, [record, record])

    def test_hash_inventory_rejects_escape(self):
        with self.assertRaises(InvalidArtifact):
            linkage.verified_files(self.root, [{"path": "../outside.jar", "bytes": 0, "sha256": "0" * 64}])

    def test_declared_third_party_jar_has_no_hidden_calf_fallback(self):
        path = self.jar()
        self.assertEqual([("public-dependency", path)], linkage.third_party_jars(["public-dependency=" + str(path)]))

    def test_hidden_calf_classes_in_third_party_jar_rejected(self):
        path = self.jar(entry="com/mohamedrejeb/calf/io/KmpFile.class")
        with self.assertRaises(InvalidArtifact):
            linkage.third_party_jars(["masquerading-dependency=" + str(path)])

    def test_missing_dependencies_rejected(self):
        with self.assertRaises(InvalidArtifact):
            linkage.third_party_jars([])

    def test_duplicate_dependency_id_rejected(self):
        path = self.jar()
        with self.assertRaises(InvalidArtifact):
            linkage.third_party_jars(["same=" + str(path), "same=" + str(path)])

    def test_zero_or_unexpected_case_counts_are_not_success(self):
        valid = {"completed_cases": 6, "assertions": 31, "kmp_abi_certified": False, "native_ui_exercised": False}
        self.assertEqual(valid, linkage.parse_execution(json.dumps(valid)))
        for key, value in (("completed_cases", 0), ("assertions", 0), ("completed_cases", True), ("kmp_abi_certified", True)):
            with self.subTest(key=key, value=value), self.assertRaises(InvalidArtifact):
                linkage.parse_execution(json.dumps(valid | {key: value}))

    def test_compiled_classes_inventory_rejects_extra_class(self):
        directory = self.root / "classes"
        path = directory / "nativecmpkit/consumer"
        path.mkdir(parents=True)
        (path / "LegacyBinaryConsumer.class").write_bytes(b"synthetic-main")
        (path / "LegacyBinaryConsumer$1.class").write_bytes(b"synthetic-implementor")
        self.assertEqual(2, len(linkage.class_inventory(directory)))
        (path / "Unapproved.class").write_bytes(b"unexpected")
        with self.assertRaises(InvalidArtifact):
            linkage.class_inventory(directory)


class LocalJarDiagnosticTest(_FileFixture):
    def fixture(self):
        jar = self.jar()
        source = self.root / "source.kt"
        source.write_text("// synthetic source input, never compiled")
        build = self.root / "build-result.json"
        build.write_text(json.dumps({"exit_code": 0, "command": ["./gradlew", ":fixture:desktopJar"]}))
        inputs = self.root / "inputs.json"
        inputs.write_text(json.dumps({"base_commit": "a" * 40, "files": {"source.kt": sha256(source)}}))
        verification = self.root / "verification.json"
        verification.write_text(json.dumps({"exit_code": 0, "input_hashes_unchanged": True, "changed_inputs": []}))
        manifest = {"schema_version": 1, "mode": "local-jar-diagnostic", "distribution_verified": False,
                    "source_revision": "a" * 40, "source_tree_dirty": True, "build_receipt": self.record(build),
                    "source_input_receipt": self.record(inputs), "source_verification_receipt": self.record(verification),
                    "jars": [self.record(jar) | {"artifact": "fixture-desktop", "published_module": True}]}
        path = self.root / "diagnostic.json"
        path.write_text(json.dumps(manifest))
        return path, manifest

    def inspect(self, path):
        with mock.patch.object(linkage, "git_state", return_value=("a" * 40, True)):
            return linkage.diagnostic_candidates(self.root, path, {"fixture-desktop"})

    def test_explicit_diagnostic_never_claims_distribution_or_static_artifact_pass(self):
        path, _ = self.fixture()
        jars, report, files = self.inspect(path)
        self.assertEqual([self.root / "dependency.jar"], jars)
        self.assertEqual("local-jar-diagnostic", report["mode"])
        self.assertFalse(report["distribution_verified"])
        self.assertFalse(report["maven_artifact_inspection_passed"])
        self.assertTrue(report["candidate_source_tree_dirty"])
        self.assertEqual(1, report["candidate_source_files_rechecked"])
        self.assertIn(self.root / "source.kt", files)

    def test_diagnostic_cannot_claim_verified_distribution(self):
        path, manifest = self.fixture()
        manifest["distribution_verified"] = True
        path.write_text(json.dumps(manifest))
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_rejects_missing_or_unknown_schema_fields(self):
        path, manifest = self.fixture()
        for data in (manifest | {"waive_licenses": True}, {k: v for k, v in manifest.items() if k != "mode"}):
            path.write_text(json.dumps(data))
            with self.assertRaises(InvalidArtifact):
                self.inspect(path)

    def test_diagnostic_requires_successful_build_not_a_failed_combined_command(self):
        path, manifest = self.fixture()
        build = self.root / "build-result.json"
        build.write_text(json.dumps({"exit_code": 1, "command": ["./gradlew", ":fixture:desktopJar"]}))
        manifest["build_receipt"] = self.record(build)
        path.write_text(json.dumps(manifest))
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_requires_unchanged_inputs_during_producer_build(self):
        path, manifest = self.fixture()
        verification = self.root / "verification.json"
        verification.write_text(json.dumps({"exit_code": 0, "input_hashes_unchanged": False, "changed_inputs": ["source.kt"]}))
        manifest["source_verification_receipt"] = self.record(verification)
        path.write_text(json.dumps(manifest))
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_checks_actual_current_source_bytes(self):
        path, _ = self.fixture()
        (self.root / "source.kt").write_text("changed input")
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_checks_actual_current_jar_bytes(self):
        path, _ = self.fixture()
        (self.root / "dependency.jar").write_bytes(b"changed jar")
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_checks_actual_receipt_bytes(self):
        path, _ = self.fixture()
        (self.root / "build-result.json").write_text("{}")
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_diagnostic_rejects_wrong_source_base_or_dirtiness(self):
        path, _ = self.fixture()
        for observed in (("b" * 40, True), ("a" * 40, False)):
            with mock.patch.object(linkage, "git_state", return_value=observed), self.assertRaises(InvalidArtifact):
                linkage.diagnostic_candidates(self.root, path, {"fixture-desktop"})

    def test_diagnostic_requires_every_named_module_once(self):
        path, manifest = self.fixture()
        manifest["jars"] += manifest["jars"]
        path.write_text(json.dumps(manifest))
        with self.assertRaises(InvalidArtifact):
            self.inspect(path)

    def test_unchanged_runtime_inputs_reject_mutation(self):
        path = self.jar()
        files = {path: sha256(path)}
        linkage.ensure_unchanged(files)
        path.write_bytes(b"changed runtime")
        with self.assertRaises(InvalidArtifact):
            linkage.ensure_unchanged(files)


if __name__ == "__main__":
    unittest.main()
