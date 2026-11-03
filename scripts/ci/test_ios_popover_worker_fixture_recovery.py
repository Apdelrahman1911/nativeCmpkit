# SPDX-License-Identifier: Apache-2.0
"""Focused historical-reader regression controls, not Apple/native tests."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

import ios_popover_geometry_plan as geometry
import ios_popover_geometry_source_projection as projection
import test_ios_worker_completion as worker_fixture

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "scripts/ci/test_ios_worker_completion.py"
SPEC = "scripts/ci/fixtures/ios-popover-worker-fixture-recovery.json"
SPEC_SHA256 = "31d431f33543962e8f54413a82e34d77f9c0990cdc4efef3f4c8654e55e2ae11"


def restored_fixture(payload):
    """An exact fixture afterimage, never arbitrary source normalization."""
    raw = (ROOT / SPEC).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("Exact Worker-fixture recovery manifest required")
    binding = json.loads(raw)["bindings"][FIXTURE]
    if type(payload) is not bytes or hashlib.sha256(payload).hexdigest() != binding["after_sha256"]:
        raise ValueError("Exact current Worker-fixture image required")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact unique Worker-fixture inverse required")
        restored = restored.replace(after, before, 1)
    if hashlib.sha256(restored).hexdigest() != binding["before_sha256"]:
        raise ValueError("Complete original Worker-fixture image required")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact unique Worker-fixture forward required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Worker-fixture round trip differs from current source")
    return restored


class PopoverWorkerFixtureRecoveryControls(unittest.TestCase):
    def test_two_exact_fragments_preserve_the_complete_original_fixture(self):
        current = (ROOT / FIXTURE).read_bytes()
        old = restored_fixture(current)
        spec = json.loads((ROOT / SPEC).read_bytes())
        self.assertEqual([FIXTURE], list(spec["bindings"]))
        self.assertEqual(2, len(spec["bindings"][FIXTURE]["fragments"]))
        self.assertIn(b"self.assertEqual(old, body)", old)
        self.assertEqual(old.count(b"self.assertEqual(old, body)"), current.count(b"self.assertEqual(old, body)"))
        old_tree = ast.parse(old)
        new_tree = ast.parse(current)
        old_class = next(n for n in old_tree.body if isinstance(n, ast.ClassDef))
        new_class = next(n for n in new_tree.body if isinstance(n, ast.ClassDef))
        self.assertEqual(len(old_class.body), len(new_class.body))
        for before, after in zip(old_class.body[1:], new_class.body[1:]):
            self.assertEqual(ast.dump(before), ast.dump(after))

    def test_only_the_exact_current_scene_image_precedes_historical_cleanup_comparison(self):
        current = (ROOT / geometry.HOST).read_bytes()
        historical = projection.current_source_before_geometry(geometry.HOST, current)
        self.assertEqual(1, current.count(b"        ownedGeometryScene = null"))
        self.assertNotIn(b"        ownedGeometryScene = null", historical)
        self.assertEqual(historical, projection.source_before_geometry(geometry.HOST, current))
        for invalid in (historical, current + b"\n", current.replace(b"ownedGeometryScene = null", b"ownedGeometryScene = scene", 1)):
            with self.subTest(bytes=len(invalid)), self.assertRaises(ValueError):
                projection.current_source_before_geometry(geometry.HOST, invalid)

    def test_partial_displaced_historical_and_foreign_fixture_images_are_refused(self):
        current = (ROOT / FIXTURE).read_bytes()
        old = restored_fixture(current)
        variants = (old, current + b"\n", current.replace(b"current_source_before_geometry", b"source_before_geometry", 1),
                    current.replace(b"self.assertEqual(old, body)", b"self.assertTrue(True)", 1), bytearray(current))
        for invalid in variants:
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(ValueError):
                restored_fixture(invalid)

    def test_current_native_admission_still_requires_the_complete_unchanged_geometry_sources(self):
        # Passive validation only: no native execution, compiler or accepted
        # source-control population is replayed by this focused obligation.
        self.assertTrue(geometry.validate_sources(ROOT))
        source = (ROOT / FIXTURE).read_text()
        self.assertEqual(1, source.count("geometry_history.current_source_before_geometry(HOST, (ROOT / HOST).read_bytes())"))
        self.assertIn("previous = history.current_source_before_worker_completion(HOST, source.encode()).decode()", source)
        self.assertIn("self.assertEqual(old, body)", source)
        self.assertNotIn("ownedGeometryScene = null", restored_fixture(source.encode()).decode())
        self.assertEqual(geometry.HOST, worker_fixture.HOST)


if __name__ == "__main__":
    unittest.main()
