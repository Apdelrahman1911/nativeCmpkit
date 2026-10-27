"""Adversarial public-material fixtures, NOT Kotlin, JNI, consumer or legal clearance."""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

import collect_native_licenses as collector
import native_license_supplements as supplements
import verify_artifacts as gate
from _native_test_fixtures import metadata_fixture


class VcsLicenseSupplementTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        # Canonicalize only this trusted, freshly created fixture root. macOS
        # exposes tempfile's /var or /tmp through system symlinks; material
        # readers still reject every symlink in the supplied catalog/cache path.
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source"
        self.cache = self.root / "public-cache"
        self.cache.mkdir()
        self.catalog = self.source / supplements.CATALOG_RELATIVE
        self.entry = self.catalog / "example-1.0.0"
        self.entry.mkdir(parents=True)
        self.repository = "https://github.com/example/native-sys"
        self.revision = "a" * 40
        self.vcs_path = "crates/example"
        fields = ('[package]\nname="example"\nversion="1.0.0"\nlicense="MIT"\n'
                  'repository="' + self.repository + '"\n').encode()
        self.crate_payloads = {
            "Cargo.toml": b"# Normalized manifest fixture\n" + fields,
            "Cargo.toml.orig": fields,
            ".cargo_vcs_info.json": json.dumps({"git": {"sha1": self.revision}, "path_in_vcs": self.vcs_path}).encode(),
            "src/lib.rs": b"// Synthetic code fixture; never executed.\n",
        }
        self.archive = self.cache / "example-1.0.0.crate"
        self.archive_bytes()
        self.license = b"Copyright Example\nPermission is granted.\nSynthetic test material, not a real legal approval.\n"
        self.data = {
            "schema_version": 1,
            "package": {"name": "example", "version": "1.0.0", "checksum": gate.sha256(self.archive), "license": "MIT"},
            "repository": self.repository, "revision": self.revision, "path_in_vcs": self.vcs_path,
            "crate_files": [], "vcs_files": [], "license_files": [],
            "scope": supplements.SCOPE, "license_obligations_reviewed": False,
        }
        for name in (".cargo_vcs_info.json", "Cargo.toml", "Cargo.toml.orig"):
            self.add_file("crate_files", name, "crate/" + name, self.crate_payloads[name])
        root_manifest = ('[package]\nname="native-sys"\nversion="0.1.0"\nlicense="MIT"\n'
                         'repository="' + self.repository + '"\n').encode()
        self.add_file("vcs_files", "Cargo.toml", "vcs/root-Cargo.toml", root_manifest)
        self.add_file("vcs_files", self.vcs_path + "/Cargo.toml", "vcs/package-Cargo.toml", fields)
        self.add_file("license_files", "LICENSE-MIT", "LICENSE-MIT", self.license)
        self.save_catalog()
        (self.source / "docs/migration").mkdir(parents=True)
        (self.source / "docs/migration/identity.json").write_text(json.dumps({"modules": [{"new_artifact": "nativecmpkit-file-picker"}]}))
        for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
            (self.source / name).write_text("Project notice synthetic fixture " + name)
        native = self.source / "calf-file-picker/native"
        native.mkdir(parents=True)
        (native / "Cargo.toml").write_text('[package]\nname="calf-filepicker-native"\nversion="0.1.0"\n')
        self.metadata_path = self.root / "metadata.json"
        self.save_metadata()

    def tearDown(self):
        self.temp.cleanup()

    def archive_bytes(self, extra=None, links=None):
        entries = self.crate_payloads | (extra or {})
        with tarfile.open(self.archive, "w:gz") as archive:
            for name, payload in entries.items():
                member = tarfile.TarInfo("example-1.0.0/" + name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            for name, destination in (links or {}).items():
                member = tarfile.TarInfo("example-1.0.0/" + name)
                member.type = tarfile.SYMTYPE
                member.linkname = destination
                archive.addfile(member)

    def add_file(self, kind, path, local, payload):
        target = self.entry / local
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        record = {"path": path, "catalog_path": local, "bytes": len(payload), "sha256": supplements.digest(payload)}
        if kind != "crate_files":
            record["git_blob_oid"] = supplements.git_blob_oid(payload)
        self.data[kind].append(record)

    def save_catalog(self):
        (self.entry / "manifest.json").write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")

    def save_metadata(self):
        native = self.source / "calf-file-picker/native"
        lock = native / "Cargo.lock"
        checksum = gate.sha256(self.archive)
        lock.write_text('version = 4\n[[package]]\nname="calf-filepicker-native"\nversion="0.1.0"\n'
                        '[[package]]\nname="example"\nversion="1.0.0"\n'
                        'source="registry+https://github.com/rust-lang/crates.io-index"\nchecksum="' + checksum + '"\n')
        self.metadata = metadata_fixture(checksum=checksum, manifest_hash=gate.sha256(native / "Cargo.toml"), lock_hash=gate.sha256(lock))
        self.metadata_path.write_text(json.dumps(self.metadata))

    def rebind_archive_fixture(self):
        # Synthetic fixtures may deliberately construct another checksum-bound
        # archive. This is not permission to change a real approved catalog.
        self.data["package"]["checksum"] = gate.sha256(self.archive)
        self.save_catalog()
        self.save_metadata()

    def collect(self, explicit=True, output="output"):
        return collector.collect(self.metadata_path, [self.cache], self.root / output,
                                 vcs_supplements=self.catalog if explicit else None)

    def rejected_catalog(self):
        with self.assertRaises(gate.InvalidArtifact):
            self.collect()
        self.assertFalse((self.root / "output").exists())

    def assert_gap(self, report):
        self.assertFalse(report["complete_material_collection"])
        self.assertFalse(report["license_obligations_reviewed"])
        self.assertEqual(1, len(report["gaps"]))
        self.assertEqual([], report["packages"][0]["files"])
        self.assertNotIn("external_vcs_material", report["packages"][0])

    def actual_entries(self):
        self.collect()
        output = self.root / "output"
        return {path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*") if path.is_file()}

    def notice_checks(self, entries):
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
            for path, payload in entries.items():
                archive.writestr(path, payload)
        repository = self.root / "staged-fixture"
        repository.mkdir(exist_ok=True)
        verifier = gate.ArtifactVerifier(self.source, repository, "0.1.0-preview.1", targets=["desktop"], native_platforms=["linux-x64"])
        with zipfile.ZipFile(io.BytesIO(memory.getvalue())) as archive:
            verifier.native_notices(archive, gate.archive_names(archive), "calf-file-picker", "fixture")
        return verifier.checks

    def report_entry(self, entries):
        name = "META-INF/nativecmpkit/native-dependencies/calf-file-picker/licenses-report.json"
        return name, json.loads(entries[name])

    def assert_gate_fails(self, entries, part):
        checks = self.notice_checks(entries)
        self.assertTrue(any(not check["passed"] and part in check["name"] for check in checks), checks)

    def test_default_archive_only_preserves_missing_text_gap(self):
        self.assert_gap(self.collect(explicit=False))

    def test_explicit_empty_catalog_does_not_invent_material(self):
        empty = self.root / "empty-public-catalog"
        empty.mkdir()
        self.assert_gap(collector.collect(self.metadata_path, [self.cache], self.root / "output", vcs_supplements=empty))

    def test_explicit_exact_supplement_retains_full_text_and_provenance(self):
        report = self.collect()
        self.assertTrue(report["complete_material_collection"])
        self.assertFalse(report["license_obligations_reviewed"])
        record = report["packages"][0]
        self.assertEqual(1, len(record["files"]))
        self.assertEqual("pinned-vcs", record["files"][0]["origin"]["kind"])
        self.assertEqual(self.revision, record["external_vcs_material"]["revision"])
        self.assertEqual(6, len(record["external_vcs_material"]["provenance_files"]))
        self.assertEqual(self.license, (self.root / "output" / record["files"][0]["path"]).read_bytes())
        self.assertNotIn(str(self.root), json.dumps(report))

    def test_read_checked_bytes_are_not_reread_during_material_copy(self):
        package = self.metadata["packages"][0]
        loaded = supplements.load_supplement(self.catalog, package)
        (self.entry / "LICENSE-MIT").write_bytes(b"Changed after held read")
        self.assertEqual({"scope/LICENSE-MIT": self.license}, loaded.license_payloads("scope/"))

    def test_missing_archive_cannot_be_replaced_by_vcs_text(self):
        self.archive.unlink()
        self.assert_gap(self.collect())

    def test_wrong_archive_checksum_cannot_use_supplement(self):
        self.archive.write_bytes(self.archive.read_bytes() + b"tampered")
        self.assert_gap(self.collect())

    def test_archive_symlink_cannot_use_supplement(self):
        original = self.cache / "original.crate"
        self.archive.rename(original)
        self.archive.symlink_to(original.name)
        self.assert_gap(self.collect())

    def test_archive_hardlink_rejected_at_supplement_correspondence(self):
        os.link(self.archive, self.cache / "shared.crate")
        self.assert_gap(self.collect())

    def test_traversal_archive_error_is_not_missing_text_fallback(self):
        self.archive_bytes(extra={"../../outside": b"never written"})
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())
        self.assertFalse((self.root / "outside").exists())

    def test_linked_license_archive_error_is_not_missing_text_fallback(self):
        self.archive_bytes(links={"LICENSE": "/outside"})
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_binary_archive_license_is_not_missing_text_fallback(self):
        self.archive_bytes(extra={"LICENSE": b"\xff\x00"})
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_real_archive_license_is_not_overwritten_by_missing_text_catalog(self):
        self.archive_bytes(extra={"LICENSE": b"Archive owns this synthetic complete text"})
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_missing_actual_original_manifest_proof_fails_closed(self):
        self.crate_payloads.pop("Cargo.toml.orig")
        self.archive_bytes()
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_actual_original_manifest_proof_must_match_catalog_bytes(self):
        self.crate_payloads["Cargo.toml.orig"] += b"# Different locked archive source\n"
        self.archive_bytes()
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_actual_crate_vcs_commit_proof_must_match_catalog_bytes(self):
        self.crate_payloads[".cargo_vcs_info.json"] = b'{"git":{"sha1":"' + b"b" * 40 + b'"},"path_in_vcs":"crates/example"}'
        self.archive_bytes()
        self.rebind_archive_fixture()
        self.assert_gap(self.collect())

    def test_tampered_catalog_text_is_rejected_before_output(self):
        (self.entry / "LICENSE-MIT").write_bytes(self.license + b"changed")
        self.rejected_catalog()

    def test_hardlinked_catalog_text_is_rejected_before_output(self):
        os.link(self.entry / "LICENSE-MIT", self.root / "shared-license")
        self.rejected_catalog()

    def test_catalog_text_parent_symlink_is_rejected(self):
        (self.entry / "vcs").rename(self.entry / "real-vcs")
        (self.entry / "vcs").symlink_to("real-vcs", target_is_directory=True)
        self.rejected_catalog()

    def test_catalog_root_symlink_is_rejected(self):
        self.catalog.rename(self.catalog.with_name("real-catalog"))
        self.catalog.symlink_to("real-catalog", target_is_directory=True)
        self.rejected_catalog()

    def test_unknown_catalog_fields_cannot_export_machine_data(self):
        self.data["manifest_path"] = "untrusted-machine-field-never-copy"
        self.save_catalog()
        self.rejected_catalog()

    def test_duplicate_catalog_json_keys_are_rejected(self):
        (self.entry / "manifest.json").write_text('{"schema_version":1,"schema_version":1}')
        self.rejected_catalog()

    def test_boolean_catalog_schema_is_not_integer_version(self):
        self.data["schema_version"] = True
        self.save_catalog()
        self.rejected_catalog()

    def test_boolean_text_byte_count_is_not_integer_size(self):
        self.data["license_files"][0]["bytes"] = True
        self.save_catalog()
        self.rejected_catalog()

    def test_rehashed_text_without_correct_git_blob_is_rejected(self):
        record = self.data["license_files"][0]
        record["git_blob_oid"] = "b" * 40
        self.save_catalog()
        self.rejected_catalog()

    def test_mutable_revision_name_is_not_a_pinned_commit(self):
        self.data["revision"] = "main"
        self.save_catalog()
        self.rejected_catalog()

    def test_foreign_or_credential_origin_is_not_a_public_catalog_source(self):
        for value in ("https://example.invalid/native", "https://secret@example.invalid/native", "https://github.com/example/native?token=never-use"):
            with self.subTest(value=value):
                self.data["repository"] = value
                self.save_catalog()
                self.rejected_catalog()

    def test_foreign_package_checksum_cannot_reuse_catalog(self):
        self.data["package"]["checksum"] = "0" * 64
        self.save_catalog()
        self.rejected_catalog()

    def test_traversal_catalog_proof_is_rejected_before_output(self):
        self.data["crate_files"][0]["catalog_path"] = "../outside"
        self.save_catalog()
        self.rejected_catalog()

    def test_source_implementation_is_not_supplemental_permission_text(self):
        self.data["license_files"][0]["path"] = "src/copying.rs"
        self.save_catalog()
        self.rejected_catalog()

    def test_catalog_cannot_assert_legal_clearance(self):
        self.data["license_obligations_reviewed"] = True
        self.save_catalog()
        self.rejected_catalog()

    def test_catalog_requires_both_manifest_and_exact_vcs_proofs(self):
        self.data["vcs_files"].pop()
        self.save_catalog()
        self.rejected_catalog()

    def test_duplicate_proof_record_is_rejected(self):
        self.data["crate_files"].append(copy.deepcopy(self.data["crate_files"][0]))
        self.save_catalog()
        self.rejected_catalog()

    def test_aggregate_supplement_byte_bound_is_fail_closed(self):
        with mock.patch.object(collector, "MAX_ALL_SUPPLEMENT_BYTES", 1):
            self.rejected_catalog()

    def test_supplement_package_count_bound_is_fail_closed(self):
        with mock.patch.object(collector, "MAX_SUPPLEMENT_PACKAGES", 0):
            self.rejected_catalog()

    def test_nonempty_output_is_preserved_not_silently_merged(self):
        output = self.root / "output"
        output.mkdir()
        (output / "stale.txt").write_bytes(b"Preserve this failed-output witness")
        with self.assertRaises(gate.InvalidArtifact):
            self.collect()
        self.assertEqual(b"Preserve this failed-output witness", (output / "stale.txt").read_bytes())

    def test_catalog_read_descriptors_close_after_success_and_failure(self):
        opened = []
        original = os.fdopen
        def observed(*args, **kwargs):
            stream = original(*args, **kwargs)
            opened.append(stream)
            return stream
        with mock.patch.object(supplements.os, "fdopen", side_effect=observed):
            for _ in range(4):
                self.assertIsNotNone(supplements.load_supplement(self.catalog, self.metadata["packages"][0]))
            (self.entry / "LICENSE-MIT").write_bytes(b"Incorrect bytes force a post-read failure")
            with self.assertRaises(gate.InvalidArtifact):
                supplements.load_supplement(self.catalog, self.metadata["packages"][0])
        self.assertGreater(len(opened), 4)
        self.assertTrue(all(stream.closed for stream in opened))

    def test_catalog_descriptor_closes_if_stream_construction_fails(self):
        descriptors = []
        original = os.open
        def observed(*args, **kwargs):
            descriptor = original(*args, **kwargs)
            descriptors.append(descriptor)
            return descriptor
        try:
            with mock.patch.object(supplements.os, "open", side_effect=observed), \
                    mock.patch.object(supplements.os, "fdopen", side_effect=OSError("Synthetic stream construction failure")):
                with self.assertRaises(gate.InvalidArtifact):
                    supplements.regular_bytes(self.entry, "LICENSE-MIT")
            alive = []
            for descriptor in descriptors:
                try:
                    os.fstat(descriptor)
                    alive.append(descriptor)
                except OSError:
                    pass
            self.assertEqual(1, len(descriptors))
            self.assertEqual([], alive, "Reader must release its raw descriptor when fdopen fails")
        finally:
            # Preserve host resources even when this regression detects a leak.
            for descriptor in descriptors:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def test_replaced_catalog_file_is_rejected_and_opened_stream_closes(self):
        target = self.entry / "LICENSE-MIT"
        original_open, original_fdopen = os.open, os.fdopen
        streams = []
        def replace_before_open(path, *args, **kwargs):
            replacement = target.with_name("replacement-license")
            replacement.write_bytes(self.license)
            os.replace(replacement, target)
            return original_open(path, *args, **kwargs)
        def observed(*args, **kwargs):
            stream = original_fdopen(*args, **kwargs)
            streams.append(stream)
            return stream
        with mock.patch.object(supplements.os, "open", side_effect=replace_before_open), \
                mock.patch.object(supplements.os, "fdopen", side_effect=observed):
            with self.assertRaisesRegex(gate.InvalidArtifact, "replaced before opening"):
                supplements.regular_bytes(self.entry, "LICENSE-MIT")
        self.assertEqual(1, len(streams))
        self.assertTrue(streams[0].closed)

    def test_mutated_catalog_file_is_rejected_and_opened_stream_closes(self):
        target = self.entry / "LICENSE-MIT"
        mutation = self.license + b"Mutation during held read"
        original_fdopen = os.fdopen
        streams = []
        class MutatingStream:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                self.stream.__enter__()
                return self
            def __exit__(self, *args):
                return self.stream.__exit__(*args)
            def fileno(self):
                return self.stream.fileno()
            def read(self, maximum):
                payload = self.stream.read(maximum)
                target.write_bytes(mutation)
                return payload
        def observed(*args, **kwargs):
            stream = original_fdopen(*args, **kwargs)
            streams.append(stream)
            return MutatingStream(stream)
        with mock.patch.object(supplements.os, "fdopen", side_effect=observed):
            with self.assertRaisesRegex(gate.InvalidArtifact, "changed or exceeded"):
                supplements.regular_bytes(self.entry, "LICENSE-MIT")
        self.assertEqual(1, len(streams))
        self.assertTrue(streams[0].closed)

    def test_supplement_collection_never_fetches_or_executes(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("No subprocess authorized")), \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("No network authorized")):
            self.assertTrue(self.collect()["complete_material_collection"])

    def test_independent_notice_gate_accepts_exact_source_bound_material_only(self):
        checks = self.notice_checks(self.actual_entries())
        self.assertTrue(checks)
        self.assertTrue(all(check["passed"] for check in checks), [check for check in checks if not check["passed"]])

    def test_notice_gate_rejects_changed_external_repository(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        report["packages"][0]["external_vcs_material"]["repository"] = "https://github.com/foreign/repository"
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "external-origin")

    def test_notice_gate_rejects_missing_external_origin_record(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        report["packages"][0].pop("external_vcs_material")
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "external-origin")

    def test_notice_gate_rejects_external_text_reclassified_as_archive_material(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        report["packages"][0]["files"][0].pop("origin")
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "external-license-records")

    def test_notice_gate_rejects_self_rehashed_license_text_substitute(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        record = report["packages"][0]["files"][0]
        changed = self.license + b"Altered but rehashed by producer"
        entries[record["path"]] = changed
        record["bytes"], record["sha256"] = len(changed), hashlib.sha256(changed).hexdigest()
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "external-text")

    def test_notice_gate_rejects_missing_original_manifest_proof(self):
        entries = self.actual_entries()
        proof = next(path for path in entries if path.endswith("provenance/crate/Cargo.toml.orig"))
        entries.pop(proof)
        self.assert_gate_fails(entries, "external-proof")

    def test_notice_gate_rejects_self_rehashed_catalog_provenance(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        record = report["packages"][0]["external_vcs_material"]
        proof = next(item for item in record["provenance_files"] if item["path"].endswith("provenance/manifest.json"))
        changed = entries[proof["path"]] + b" \n"
        entries[proof["path"]] = changed
        proof["bytes"], proof["sha256"] = len(changed), hashlib.sha256(changed).hexdigest()
        record["manifest_sha256"] = proof["sha256"]
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "external-origin")
        self.assert_gate_fails(entries, "external-proof")

    def test_notice_gate_rejects_external_material_without_approved_catalog(self):
        entries = self.actual_entries()
        self.entry.rename(self.entry.with_name("not-the-requested-identity"))
        self.assert_gate_fails(entries, "native-license-parse")

    def test_notice_gate_rejects_unrecorded_stale_provenance_material(self):
        entries = self.actual_entries()
        entries["META-INF/nativecmpkit/native-dependencies/calf-file-picker/example-1.0.0/provenance/stale.json"] = b"{}"
        self.assert_gate_fails(entries, "native-license-no-stale-material")

    def test_notice_gate_retains_fail_closed_missing_text_requirement(self):
        entries = self.actual_entries()
        name, report = self.report_entry(entries)
        entries.pop(report["packages"][0]["files"][0]["path"])
        report["packages"][0]["files"] = []
        report["complete_material_collection"] = False
        report["gaps"] = [{"package": "example-1.0.0", "reason": "No complete text"}]
        entries[name] = json.dumps(report).encode()
        self.assert_gate_fails(entries, "text-present")
        self.assert_gate_fails(entries, "native-license-collection-complete")


if __name__ == "__main__":
    unittest.main()
