"""Synthetic pending-v2 ownership/path tests, NOT authenticity or legal approval.

No real license/catalog, filesystem, network, archive or native fixture is used.
The constructor fixtures are deliberately not valid provenance. The bounded fake
reader reaches only malformed crate-path validation, before provenance checking.
"""
from __future__ import annotations

import json
import operator
import unittest

import native_license_material_v2 as material
from verify_artifacts import InvalidArtifact


def snapshot_inputs():
    manifest = {
        "package": {"name": "synthetic-unit-only"},
        "source_origin": {"revision": "synthetic-source", "git_trees": [{"git_oid": "synthetic-tree"}]},
        "text_origin": {"revision": "synthetic-text"},
        "relationship": {"source_is_ancestor_reported": False},
        "license_resolution": {"resolved_license": "synthetic-not-a-license"},
        "attribution_lead": {"applicability": "unreviewed"},
    }
    contents = {"synthetic-unit-only/manifest.json": b"synthetic constructor bytes\n"}
    observations = {"source": {"revision": "synthetic-source"}}
    return manifest, contents, observations


class BoundedSyntheticReader:
    """No disk or provenance access: capture only predetermined synthetic bytes."""
    def __init__(self, payloads):
        self.payloads, self.contents, self.reads = payloads, {}, []

    def file(self, record, extra=frozenset()):
        material.exact(record, material.FILE_FIELDS | extra)
        path = material.canonical_path(record["catalog_path"])
        if path not in self.payloads:
            raise AssertionError("Synthetic path control must not read provenance")
        raw = self.payloads[path]
        material.require(0 < len(raw) <= material.MAX_MANIFEST_BYTES
                         and type(record["bytes"]) is int and record["bytes"] == len(raw)
                         and record["sha256"] == material.digest(raw), "Invalid synthetic binding")
        self.contents[path] = raw
        self.reads.append(path)
        return raw


class PendingMaterialSyntheticTest(unittest.TestCase):
    def test_synthetic_snapshot_owns_nested_state_and_is_read_only(self):
        manifest, contents, observations = snapshot_inputs()
        held = material.PendingMaterial("synthetic-unit-only", manifest, contents, observations)
        before = json.loads(json.dumps(held.evidence_record()))
        payloads = dict(held.contents)
        manifest["source_origin"]["git_trees"][0]["git_oid"] = "external mutation"
        contents["synthetic-unit-only/manifest.json"] = b"external mutation"
        observations["source"]["revision"] = "external mutation"
        with self.subTest(boundary="defensive manifest snapshot"):
            self.assertEqual(before, held.evidence_record())
        with self.subTest(boundary="defensive payload snapshot"):
            self.assertEqual(payloads, held.contents)
        with self.subTest(boundary="defensive observation snapshot"):
            self.assertEqual("synthetic-source", held.git_observations["source"]["revision"])
        for mapping, key in ((held.manifest["text_origin"], "revision"),
                             (held.manifest["source_origin"]["git_trees"], 0),
                             (held.contents, "synthetic-unit-only/manifest.json"),
                             (held.git_observations["source"], "revision")):
            with self.subTest(boundary=key):
                with self.assertRaises(TypeError):
                    operator.setitem(mapping, key, "mutation")

    def test_synthetic_export_is_plain_detached_json_and_edited_origin_is_rejected(self):
        held = material.PendingMaterial("synthetic-unit-only", *snapshot_inputs())
        before = json.loads(json.dumps(held.evidence_record()))
        emitted = held.evidence_record()
        self.assertEqual(before, emitted)
        material.inspect_evidence(held, emitted, dict(held.contents))
        emitted["text_origin"]["revision"] = "synthetic forged origin"
        with self.assertRaises(InvalidArtifact):
            material.inspect_evidence(held, emitted, dict(held.contents))
        self.assertEqual(before, held.evidence_record())

    def test_synthetic_bad_crate_path_refuses_before_provenance_or_proof_read(self):
        # Selected name only to reach the owning path boundary; zero checksum and
        # nonexistent version are synthetic, not an authenticated registry identity.
        package = {"id": "objc2@0.0.0", "name": "objc2", "version": "0.0.0", "checksum": "0" * 64,
                   "license": "MIT", "source_kind": "crates.io", "license_file": None}
        fields = ("source_origin", "source_files", "text_origin", "policy_file", "license_files",
                  "license_resolution", "relationship", "attribution_lead", "research_files")
        for bad in ([], {}, None, 42, "../Cargo.toml", ".cargo_vcs_info.json/../Cargo.toml"):
            with self.subTest(path_type=type(bad).__name__):
                payloads, records = {}, []
                for index, name in enumerate((bad, "Cargo.toml", "Cargo.toml.orig")):
                    path, raw = "synthetic-proof-" + str(index), b"synthetic proof bytes"
                    payloads[path] = raw
                    records.append({"catalog_path": path, "path": name, "bytes": len(raw), "sha256": material.digest(raw)})
                data = {field: None for field in fields}
                data.update(schema_version=2, kind=material.KIND, scope=material.SCOPE, package=package,
                            crate_files=records, path_in_vcs="crates/synthetic", obligations=dict(material.OBLIGATIONS))
                raw = json.dumps(data).encode()
                path = "objc2-0.0.0/manifest.json"
                payloads[path] = raw
                reader = BoundedSyntheticReader(payloads)
                record = {"catalog_path": path, "package": package, "bytes": len(raw), "sha256": material.digest(raw)}
                with self.assertRaises(InvalidArtifact):
                    material.load_material(reader, record)
                self.assertEqual([path], reader.reads)


if __name__ == "__main__":
    unittest.main()
