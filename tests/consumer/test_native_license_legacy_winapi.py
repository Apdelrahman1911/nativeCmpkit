"""New legacy material controls, NOT native/consumer authenticity or legal approval.

Catalog/text/proof bytes are genuine reviewed public material copied into owned
temporary fixtures. Deliberately malformed archives/reports are synthetic and
never executed. No real crate payload is scanned, subprocess/network invoked,
or existing accepted test suite replayed here.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import zipfile

import collect_native_licenses as collector
import native_license_legacy_winapi as legacy
import native_license_supplements as supplements
import verify_artifacts as gate

ROOT = Path(__file__).resolve().parents[2]
ORIGINALS = ROOT / "docs/development/evidence/current-platform-recovery-20261101/native-stage-prerequisites20261104"
NAMES = ("winapi-i686-pc-windows-gnu", "winapi-x86_64-pc-windows-gnu")


class LegacyWinapiLicenseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()  # Only our trusted temporary root.
        self.catalog = self.root / "public-catalog"
        self.entry = self.catalog / (NAMES[0] + "-0.4.0")
        shutil.copytree(ROOT / supplements.CATALOG_RELATIVE / self.entry.name, self.entry)
        self.metadata_bytes = (ORIGINALS / "metadata-current606/calf-file-picker.json").read_bytes()
        self.metadata = json.loads(self.metadata_bytes)
        self.packages = {package["name"]: package for package in self.metadata["packages"]}
        self.package = copy.deepcopy(self.packages[NAMES[0]])
        self.data = json.loads((self.entry / "manifest.json").read_bytes())

    def save(self):
        (self.entry / "manifest.json").write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n")

    def load(self):
        return supplements.load_supplement(self.catalog, self.package)

    def refuse(self):
        with self.assertRaises(gate.InvalidArtifact):
            self.load()

    def mutate_rehashed(self, kind, local, payload):
        record = next(record for record in self.data[kind] if record["catalog_path"] == local)
        (self.entry / local).write_bytes(payload)
        record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        if "git_blob_oid" in record:
            record["git_blob_oid"] = supplements.git_blob_oid(payload)
        self.save()

    def test_two_exact_real_catalog_entries_keep_separate_no_vcs_contract(self):
        shutil.copytree(ROOT / supplements.CATALOG_RELATIVE / (NAMES[1] + "-0.4.0"),
                        self.catalog / (NAMES[1] + "-0.4.0"))
        for name, members in zip(NAMES, (1390, 1419)):
            with self.subTest(package=name):
                held = supplements.load_supplement(self.catalog, self.packages[name])
                self.assertIsInstance(held, legacy.LegacyWinapiSupplement)
                self.assertEqual(3, held.manifest["schema_version"])
                self.assertFalse(held.manifest["archive_vcs_metadata_present"])
                self.assertFalse(held.manifest["source_authenticity_certified"])
                self.assertFalse(held.manifest["license_obligations_reviewed"])
                proof = json.loads(held.contents["research/correspondence.json"])
                self.assertEqual(members, proof["matching_members"])
                self.assertEqual(0, proof["mismatching_members"])
                self.assertNotIn(".cargo_vcs_info.json", {row["crate_path"] for row in proof["payload_files"]})
                self.assertEqual(10, len(held.contents))

    def test_held_nested_material_is_immutable_and_exports_detached_records(self):
        held = self.load()
        original = held.material_record("owning/")
        for mapping, key in ((held.manifest, "scope"),
                             (held.manifest["package"], "license"),
                             (held.manifest["license_files"][0], "sha256"),
                             (held.contents, "LICENSE-MIT")):
            with self.subTest(key=key), self.assertRaises(TypeError):
                mapping[key] = "external mutation"
        exported = held.material_record("owning/")
        exported["provenance_files"][0]["sha256"] = "counterfeit"
        exported["license_obligations_reviewed"] = True
        self.assertEqual(original, held.material_record("owning/"))
        with self.assertRaises(TypeError):
            legacy.PACKAGES[NAMES[0]]["checksum"] = "counterfeit"

    def test_unknown_registry_identity_version_checksum_license_or_source_refuses(self):
        for field, value in (("name", "unreviewed"), ("version", "0.4.1"),
                             ("checksum", "0" * 64), ("license", "MIT"),
                             ("source_kind", "git"), ("license_file", "LICENSE")):
            with self.subTest(field=field), self.assertRaises(gate.InvalidArtifact):
                altered = self.package | {field: value}
                legacy.load_legacy(self.entry, altered, self.data, (self.entry / "manifest.json").read_bytes())

    def test_v2_float_boolean_and_extra_schema_fields_do_not_enter_legacy(self):
        for version in (2, 3.0, True):
            with self.subTest(schema=version):
                self.data["schema_version"] = version; self.save(); self.refuse()
        self.data["schema_version"] = 3
        self.data["unknown_policy_waiver"] = True; self.save(); self.refuse()

    def test_repository_revision_root_tree_and_package_path_cannot_be_substituted(self):
        for field, value in (("repository", "https://github.com/other/source"),
                             ("revision", "a" * 40), ("root_tree_oid", "b" * 40),
                             ("path_in_vcs", "x86_64")):
            original = self.data[field]
            with self.subTest(field=field):
                self.data[field] = value; self.save(); self.refuse()
            self.data[field] = original

    def test_no_vcs_authenticity_or_legal_clearance_boolean_can_be_claimed(self):
        for field in ("archive_vcs_metadata_present", "source_authenticity_certified", "license_obligations_reviewed"):
            with self.subTest(field=field):
                self.data[field] = True; self.save(); self.refuse()
            self.data[field] = False

    def test_fabricated_cargo_vcs_proof_is_not_a_legacy_contract(self):
        self.data["crate_files"].append({"path": ".cargo_vcs_info.json",
            "catalog_path": "crate/.cargo_vcs_info.json", "bytes": 2, "sha256": "0" * 64})
        self.save(); self.refuse()

    def test_missing_or_dropped_full_member_correspondence_refuses(self):
        path = self.entry / "research/correspondence.json"
        original = path.read_bytes()
        changed = json.loads(original)
        changed["payload_files"].pop()
        changed["matching_members"] -= 1
        self.mutate_rehashed("provenance_files", "research/correspondence.json", json.dumps(changed).encode())
        self.refuse()
        path.unlink()
        self.refuse()

    def test_altered_member_origin_and_hash_rebinding_cannot_replace_sealed_evidence(self):
        path = self.entry / "research/correspondence.json"
        changed = json.loads(path.read_bytes())
        changed["payload_files"][0].update(source_path="other/Cargo.toml", git_blob_oid="0" * 40,
                                           source_blob_oid="0" * 40, exact_source_match=True)
        self.mutate_rehashed("provenance_files", "research/correspondence.json", json.dumps(changed).encode())
        self.refuse()

    def test_self_rehashed_license_or_later_copyright_bytes_are_not_the_earlier_origin(self):
        for filename in ("LICENSE-MIT", "LICENSE-APACHE"):
            with self.subTest(filename=filename):
                payload = (self.entry / filename).read_bytes() + b"\nCounterfeit producer text.\n"
                self.mutate_rehashed("license_files", filename, payload)
                self.refuse()

    def test_self_rehashed_source_commit_tree_envelope_and_tree_bound_refuse(self):
        path = self.entry / "research/source-commit.json"
        changed = json.loads(path.read_bytes()); changed["tree"]["sha"] = "0" * 40
        self.mutate_rehashed("provenance_files", "research/source-commit.json", json.dumps(changed).encode())
        self.refuse()
        for raw in (b"not gzip", gzip.compress(b" " * (legacy.MAX_TREE_BYTES + 1), mtime=0)):
            with self.subTest(envelope_bytes=len(raw)), self.assertRaises(gate.InvalidArtifact):
                legacy.source_tree(raw)

    def test_paths_symlinks_and_hardlinks_cannot_redirect_public_material(self):
        record = self.data["provenance_files"][0]
        old = record["catalog_path"]
        for path in ("../private", "research/.git/private", "/absolute"):
            with self.subTest(path=path):
                record["catalog_path"] = path; self.save(); self.refuse()
        record["catalog_path"] = old; self.save()
        target = self.entry / old
        target.rename(self.entry / "held-correspondence")
        target.symlink_to(self.entry / "held-correspondence")
        self.refuse()
        target.unlink()
        target.hardlink_to(self.entry / "held-correspondence")
        self.refuse()

    def test_wrong_compressed_archive_cannot_fallback_or_scan_tar_payload(self):
        held = self.load()
        path = self.root / (NAMES[0] + "-0.4.0.crate")
        path.write_bytes(b"\0" * legacy.PACKAGES[NAMES[0]]["archive_bytes"])
        with mock.patch("tarfile.open", side_effect=AssertionError("No tar payload scan")):
            with self.assertRaises(gate.InvalidArtifact):
                supplements.verify_crate_correspondence(path, held)
        with self.assertRaises(gate.InvalidArtifact):
            supplements.verify_crate_correspondence(path.with_name("foreign.crate"), held)

    def test_collector_rejects_synthetic_bad_archive_without_ordinary_payload_fallback(self):
        cache = self.root / "cache"; cache.mkdir()
        (cache / (NAMES[0] + "-0.4.0.crate")).write_bytes(b"synthetic malformed archive; never executed")
        metadata = self.root / "metadata.json"; metadata.write_bytes(self.metadata_bytes)
        with mock.patch.object(collector, "collect_archive", side_effect=AssertionError("No accepted payload replay")):
            report = collector.collect(metadata, [cache], self.root / "notices", vcs_supplements=self.catalog)
        selected = next(package for package in report["packages"] if package["name"] == NAMES[0])
        self.assertEqual([], selected["files"])
        self.assertNotIn("external_vcs_material", selected)
        self.assertFalse(report["complete_material_collection"])
        self.assertFalse(report["license_obligations_reviewed"])
        self.assertTrue(any(gap.get("package") == NAMES[0] + "-0.4.0" for gap in report["gaps"]))

    def notice_fixture(self):
        prefix = "META-INF/nativecmpkit/native-dependencies/calf-file-picker/"
        payloads = {prefix + "metadata.json": self.metadata_bytes}
        report = {"schema_version": 1, "module": "calf-file-picker",
            "metadata_sha256": hashlib.sha256(self.metadata_bytes).hexdigest(),
            "cargo_toml_sha256": self.metadata["cargo_toml_sha256"],
            "cargo_lock_sha256": self.metadata["cargo_lock_sha256"],
            "complete_material_collection": False, "license_obligations_reviewed": False,
            "gaps": [{"scope": "Synthetic inspector wrapper; ordinary dependencies deliberately unexecuted"}],
            "packages": []}
        for package in self.metadata["packages"]:
            record = {key: package[key] for key in ("name", "version", "source_kind", "license", "checksum")}
            record["files"] = []
            if package["name"] in NAMES:
                held = supplements.load_supplement(ROOT / supplements.CATALOG_RELATIVE, package)
                owning = prefix + package["name"] + "-0.4.0/"
                record.update(files=held.license_entries(owning), external_vcs_material=held.material_record(owning))
                payloads.update(held.license_payloads(owning) | held.provenance_payloads(owning))
            report["packages"].append(record)
        return prefix, payloads, report

    def inspect_notices(self, prefix, payloads, report):
        payloads[prefix + "licenses-report.json"] = json.dumps(report).encode()
        container = io.BytesIO()
        with zipfile.ZipFile(container, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, payload in payloads.items():
                archive.writestr(path, payload)
        container.seek(0)
        (self.root / "inert-repository").mkdir(exist_ok=True)
        inspector = gate.ArtifactVerifier(ROOT, self.root / "inert-repository", "0.1.0-preview.1",
            modules=["nativecmpkit-file-picker"], targets=["metadata"], native_platforms=["linux-x64"])
        with zipfile.ZipFile(container) as archive:
            inspector.native_notices(archive, set(archive.namelist()), "calf-file-picker", "legacy-fixture")
        return inspector.checks

    def test_notice_inspector_independently_compares_real_legacy_proofs_not_full_consumer(self):
        checks = self.inspect_notices(*self.notice_fixture())
        owning = [record for record in checks if any(":crate-license:" + name + "@0.4.0:" in record["name"] for name in NAMES)]
        self.assertEqual(42, len(owning))
        self.assertTrue(all(record["passed"] for record in owning), owning)
        self.assertTrue(any(not record["passed"] for record in checks))  # Incomplete by design.

    def test_notice_inspector_rejects_forged_origin_or_self_rehashed_license(self):
        for mode in ("origin", "license"):
            with self.subTest(mode=mode):
                prefix, payloads, report = self.notice_fixture()
                package = next(record for record in report["packages"] if record["name"] == NAMES[0])
                if mode == "origin":
                    package["external_vcs_material"]["root_tree_oid"] = "0" * 40
                else:
                    record = package["files"][0]
                    payload = payloads[record["path"]] + b"\nCounterfeit material.\n"
                    payloads[record["path"]] = payload
                    record.update(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
                checks = self.inspect_notices(prefix, payloads, report)
                owning = [record for record in checks if ":crate-license:" + NAMES[0] + "@" in record["name"]]
                self.assertTrue(any(not record["passed"] for record in owning))
