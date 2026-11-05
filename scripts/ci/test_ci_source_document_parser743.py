# SPDX-License-Identifier: Apache-2.0
"""NEW743 document-parser wiring only; no timing, admission or native claims."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ci_source_domain740 as domain
import ci_source_recovery740_742 as recovery
import macos_share_ci668_composition as joint


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


@contextmanager
def manifest_tree(stage):
    # Only the owning manifest is placed in a temporary tree. The document
    # parser gets an actual ordinary descriptor/portable reader, not a cached
    # filesystem result; no whole source-validator is claimed by this fixture.
    raw = (stage.ROOT / stage.SPEC).read_bytes()
    with tempfile.TemporaryDirectory(prefix="source-parser743-") as name:
        container = Path(name).resolve()
        root = container / "tree"
        target = root / stage.SPEC
        target.parent.mkdir(parents=True)
        target.write_bytes(raw)
        yield root, target, raw, container
    if container.exists():
        raise AssertionError("owned743-parser-fixture-was-not-removed")


class CiSourceDocumentPureParser743Controls(unittest.TestCase):
    def setUp(self):
        joint._cached_json_tree.cache_clear()
        self.addCleanup(joint._cached_json_tree.cache_clear)

    def _warm_documents(self, stage):
        with manifest_tree(stage) as (root, target, raw, container):
            expected = json.loads(raw)
            with patch.object(stage, "_ordinary", wraps=joint._ordinary) as ordinary, \
                 patch.object(domain, "_binding", wraps=domain._binding) as bindings:
                first = stage._document(root)
                self.assertEqual(expected, first)
                key = next(iter(first["bindings"]))
                first["bindings"][key]["fragments"][0]["before"] = "locally-mutated743"
                first["bindings"][key]["fragments"].append({"local743": True})
                second = stage._document(root)
                self.assertEqual(expected, second)
                self.assertIsNot(first, second)
                self.assertIsNot(first["bindings"], second["bindings"])
                self.assertIsNot(first["bindings"][key], second["bindings"][key])
                self.assertIsNot(first["bindings"][key]["fragments"], second["bindings"][key]["fragments"])
                self.assertIsNot(first["bindings"][key]["fragments"][0], second["bindings"][key]["fragments"][0])
                count = len(stage.MODIFIED) + (1 if stage is domain else 0)
                self.assertEqual(2 * count, bindings.call_count)
                self.assertEqual(2, ordinary.call_count)
                self.assertEqual([(root, stage.SPEC, stage.MAX_SPEC)] * 2,
                                 [call.args for call in ordinary.call_args_list])
                info = joint._cached_json_tree.cache_info()
                self.assertEqual((1, 1, 1, 16), (info.hits, info.misses, info.currsize, info.maxsize))
        self.assertFalse(container.exists())

    def test01_domain_warm_parse_retains_fresh_read_schema_and_disjoint_mutable_tree(self):
        self._warm_documents(domain)

    def test02_recovery_warm_parse_retains_fresh_read_row_validation_and_disjoint_mutable_tree(self):
        self._warm_documents(recovery)

    def test03_warm_parse_never_borrows_fresh_manifest_row_root_or_descriptor_refusals(self):
        for stage in (domain, recovery):
            with self.subTest(owner=stage.OWNER):
                joint._cached_json_tree.cache_clear()
                with manifest_tree(stage) as (root, target, raw, container):
                    with patch.object(stage, "_ordinary", wraps=joint._ordinary), \
                         patch.object(joint, "_json", wraps=joint._json) as parser:
                        stage._document(root)
                        warm = joint._cached_json_tree.cache_info()
                        target.write_bytes(raw + b"\n")
                        with self.assertRaisesRegex(ValueError, "exact.*transition-manifest-required"):
                            stage._document(root)
                        self.assertEqual(1, parser.call_count)
                        self.assertEqual(warm, joint._cached_json_tree.cache_info())
                        target.write_bytes(raw)
                        with self.assertRaisesRegex(ValueError, "ordinary-canonical-.*-root-required"):
                            stage._document(root / ".." / "tree")
                        self.assertEqual(1, parser.call_count)
                        self.assertEqual(warm, joint._cached_json_tree.cache_info())
                        target.unlink()
                        backing = target.with_name("backing743.json")
                        backing.write_bytes(raw)
                        target.hardlink_to(backing)
                        with self.assertRaisesRegex(ValueError, "bounded-ordinary-unaliased-.*-file-required"):
                            stage._document(root)
                        self.assertEqual(1, parser.call_count)
                        self.assertEqual(warm, joint._cached_json_tree.cache_info())
                        target.unlink()
                        fake = json.loads(raw)
                        key = next(iter(fake["bindings"]))
                        fake["bindings"][key]["fragments"][0]["after_fragment_sha256"] = "0" * 64
                        encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
                        target.write_bytes(encoded)
                        with patch.object(stage, "SPEC_SHA256", digest(encoded)), \
                             patch.object(domain, "_binding", wraps=domain._binding) as bindings:
                            for _ in range(2):
                                with self.assertRaisesRegex(ValueError, "exact740-unique-reversible-source-fragments-required"):
                                    stage._document(root)
                            self.assertGreaterEqual(bindings.call_count, 2)
                        info = joint._cached_json_tree.cache_info()
                        self.assertEqual((1, 2, 2, 16), (info.hits, info.misses, info.currsize, info.maxsize))
                        self.assertEqual(3, parser.call_count)
                self.assertFalse(container.exists())


if __name__ == "__main__":
    unittest.main()
