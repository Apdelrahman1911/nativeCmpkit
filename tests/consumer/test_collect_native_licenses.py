import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

import collect_native_licenses as licenses
from _native_test_fixtures import metadata_fixture
from verify_artifacts import InvalidArtifact, sha256


class NativeLicensesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cache = self.root / "public-crates-cache"
        self.cache.mkdir()
        self.archive = self.cache / "example-1.0.0.crate"

    def tearDown(self):
        self.temp.cleanup()

    def make_archive(self, entries=None):
        entries = entries if entries is not None else {"example-1.0.0/LICENSE-MIT": b"Copyright Example\nPermission is granted.\n"}
        with tarfile.open(self.archive, "w:gz") as archive:
            for name, content in entries.items():
                entry = tarfile.TarInfo(name)
                entry.size = len(content)
                archive.addfile(entry, io.BytesIO(content))
        return sha256(self.archive)

    def metadata(self, checksum):
        path = self.root / "metadata.json"
        path.write_text(json.dumps(metadata_fixture(checksum=checksum)))
        return path

    def test_exact_verified_license_bytes_collected(self):
        checksum = self.make_archive()
        texts = licenses.collect_archive(self.archive, "example", "1.0.0", checksum)
        self.assertEqual(b"Copyright Example\nPermission is granted.\n", texts["LICENSE-MIT"])

    def test_wrong_archive_checksum_rejected(self):
        self.make_archive()
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", "0" * 64)

    def test_traversal_member_rejected_without_extracting(self):
        checksum = self.make_archive({"example-1.0.0/../../LICENSE": b"bad"})
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)
        self.assertFalse((self.root / "LICENSE").exists())

    def test_spdx_alone_is_not_notice_text(self):
        checksum = self.make_archive({"example-1.0.0/Cargo.toml": b'license="MIT"'})
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)

    def test_copying_source_implementation_is_not_copyright_material(self):
        checksum = self.make_archive({"example-1.0.0/src/copying.rs": b"pub trait CopyingHelper {}"})
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)

    def test_source_looking_file_only_allowed_when_explicitly_declared(self):
        checksum = self.make_archive({"example-1.0.0/src/terms.rs": b"// Copyright; full declared permission text fixture"})
        self.assertIn("src/terms.rs", licenses.collect_archive(self.archive, "example", "1.0.0", checksum, "src/terms.rs"))

    def test_explicit_license_file_collected(self):
        checksum = self.make_archive({"example-1.0.0/legal/terms.txt": b"Copyright and permission"})
        texts = licenses.collect_archive(self.archive, "example", "1.0.0", checksum, "legal/terms.txt")
        self.assertEqual(["legal/terms.txt"], list(texts))

    def test_missing_declared_license_file_fails(self):
        checksum = self.make_archive()
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum, "OTHER-LICENSE")

    def test_empty_license_fails(self):
        checksum = self.make_archive({"example-1.0.0/LICENSE": b""})
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)

    def test_symlink_license_rejected(self):
        with tarfile.open(self.archive, "w:gz") as archive:
            entry = tarfile.TarInfo("example-1.0.0/LICENSE")
            entry.type = tarfile.SYMTYPE
            entry.linkname = "/outside"
            archive.addfile(entry)
        with self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", sha256(self.archive))

    def test_collection_reports_hashes_but_not_legal_certification(self):
        checksum = self.make_archive()
        report = licenses.collect(self.metadata(checksum), [self.cache], self.root / "output")
        self.assertTrue(report["complete_material_collection"])
        self.assertFalse(report["license_obligations_reviewed"])
        self.assertEqual(1, len(report["packages"][0]["files"]))
        self.assertNotIn(str(self.cache), json.dumps(report))
        copied = self.root / "output/META-INF/nativecmpkit/native-dependencies/calf-file-picker/metadata.json"
        self.assertEqual((self.root / "metadata.json").read_bytes(), copied.read_bytes())
        self.assertEqual(report["metadata_sha256"], sha256(copied))

    def test_missing_archive_is_recorded_gap(self):
        report = licenses.collect(self.metadata("0" * 64), [self.cache], self.root / "output")
        self.assertFalse(report["complete_material_collection"])
        self.assertEqual(1, len(report["gaps"]))

    def test_nonempty_output_not_silently_mixed(self):
        checksum = self.make_archive()
        output = self.root / "output"
        output.mkdir()
        (output / "stale.txt").write_text("must not be deleted")
        with self.assertRaises(InvalidArtifact):
            licenses.collect(self.metadata(checksum), [self.cache], output)
        self.assertTrue((output / "stale.txt").is_file())

    def test_unreviewed_source_kind_fails_closed(self):
        path = self.metadata("0" * 64)
        data = json.loads(path.read_text())
        data["packages"][0]["source_kind"] = "private-git"
        path.write_text(json.dumps(data))
        with self.assertRaises(InvalidArtifact):
            licenses.collect(path, [self.cache], self.root / "output")
        self.assertFalse((self.root / "output").exists())

    def test_unsanitized_machine_fields_rejected_before_any_output(self):
        for scope in ("root", "package", "node"):
            with self.subTest(scope=scope):
                path = self.metadata("0" * 64)
                data = json.loads(path.read_text())
                target = data if scope == "root" else data["packages"][0] if scope == "package" else data["resolve"][0]
                target["manifest_path"] = "never-redistribute-a-private-machine-field"
                path.write_text(json.dumps(data))
                with self.assertRaises(InvalidArtifact):
                    licenses.collect(path, [self.cache], self.root / "output")
                self.assertFalse((self.root / "output").exists())

    def test_non_object_metadata_rejected(self):
        path = self.root / "metadata.json"
        path.write_text("[]")
        with self.assertRaises(InvalidArtifact):
            licenses.collect(path, [self.cache], self.root / "output")

    def test_filtered_graph_rejected(self):
        path = self.metadata("0" * 64)
        data = json.loads(path.read_text())
        data["target_filter"] = "x86_64-unknown-linux-gnu"
        path.write_text(json.dumps(data))
        with self.assertRaises(InvalidArtifact):
            licenses.collect(path, [self.cache], self.root / "output")

    def test_unknown_or_missing_graph_nodes_rejected(self):
        for mode in ("unknown", "missing", "duplicate"):
            with self.subTest(mode=mode):
                path = self.metadata("0" * 64)
                data = json.loads(path.read_text())
                if mode == "unknown":
                    data["resolve"][0]["dependencies"].append("unknown@1.0.0")
                elif mode == "missing":
                    data["resolve"].pop()
                else:
                    data["resolve"].append(data["resolve"][0])
                path.write_text(json.dumps(data))
                with self.assertRaises(InvalidArtifact):
                    licenses.collect(path, [self.cache], self.root / "output")

    def test_non_owning_local_root_rejected(self):
        path = self.metadata("0" * 64)
        data = json.loads(path.read_text())
        data["packages"][1]["name"] = "unreviewed-path-crate"
        data["packages"][1]["id"] = "unreviewed-path-crate@0.1.0"
        path.write_text(json.dumps(data))
        with self.assertRaises(InvalidArtifact):
            licenses.collect(path, [self.cache], self.root / "output")

    def test_license_file_escape_rejected_before_any_output(self):
        for name in ("../LICENSE", "C:\\outside", "/outside", "./LICENSE", ""):
            with self.subTest(name=name):
                path = self.metadata("0" * 64)
                data = json.loads(path.read_text())
                data["packages"][0]["license_file"] = name
                path.write_text(json.dumps(data))
                with self.assertRaises(InvalidArtifact):
                    licenses.collect(path, [self.cache], self.root / "output")
                self.assertFalse((self.root / "output").exists())

    def test_entry_bound_enforced_while_reading(self):
        checksum = self.make_archive({"example-1.0.0/LICENSE": b"permission", "example-1.0.0/NOTICE": b"attribution"})
        with mock.patch.object(licenses, "MAX_MEMBERS", 1), self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)

    def test_total_collected_bound_enforced(self):
        checksum = self.make_archive({"example-1.0.0/LICENSE": b"permission", "example-1.0.0/NOTICE": b"attribution"})
        with mock.patch.object(licenses, "MAX_COLLECTED_BYTES", 10), self.assertRaises(InvalidArtifact):
            licenses.collect_archive(self.archive, "example", "1.0.0", checksum)

    def test_prerelease_build_metadata_crate_version_is_safe(self):
        version = "1.0.0-rc.1+meta.2"
        self.archive = self.cache / ("example-" + version + ".crate")
        checksum = self.make_archive({"example-" + version + "/LICENSE": b"permission"})
        self.assertEqual({"LICENSE": b"permission"}, licenses.collect_archive(self.archive, "example", version, checksum))


if __name__ == "__main__":
    unittest.main()
