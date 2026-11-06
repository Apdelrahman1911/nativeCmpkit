# SPDX-License-Identifier: Apache-2.0
"""NEW finite fixture-successor controls; no old accepted population is replayed.

Only ordinary source/data and an owned finite copied fixture are exercised.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import ci_fixture_successor730 as successor
import ci_source_domain740 as domain740
import ci_source_recovery740_742 as recovery
import macos_share_ci668_composition as joint

ROOT = Path(__file__).resolve().parents[2]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CiFixtureSuccessor730Controls(unittest.TestCase):
    def test_new01_exact_six_fixtures_and_owning_routing_control_roundtrips_keep_old_guards(self):
        document = successor._document(ROOT)
        self.assertEqual(6, len(successor.FIXTURES))
        self.assertEqual(3, len(successor.RAW_FIXTURES))
        self.assertEqual(9, len(document["bindings"]))
        self.assertEqual(frozenset(successor.BEFORE), set(document["bindings"]))
        for relative, row in document["bindings"].items():
            raw = (ROOT / relative).read_bytes()
            old = successor.current_source_before_fixture_successor(relative, raw, ROOT)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)), relative)
            forward = old
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before), relative)
                forward = forward.replace(before, after, 1)
            if relative == successor.ROUTING:
                routing = document["routing_binding"]
                self.assertEqual((routing["before_sha256"], routing["before_bytes"]),
                                 (sha(forward), len(forward)), relative)
                for fragment in routing["fragments"]:
                    before, after = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(1, forward.count(before), relative)
                    forward = forward.replace(before, after, 1)
            self.assertEqual(raw, forward, relative)
            self.assertEqual(old, successor.peel_fixture_successor_for_history(relative, raw, ROOT))
            self.assertEqual(old, successor.peel_fixture_successor_for_history(relative, old, ROOT))
            for bad in (old, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
                with self.subTest(relative=relative, operand=type(bad).__name__), self.assertRaises(ValueError):
                    successor.current_source_before_fixture_successor(relative, bad, ROOT)
            unknown = raw + b"\n# unknown fixture successor\n"
            self.assertEqual(unknown, successor.peel_fixture_successor_for_history(relative, unknown, ROOT))
        for relative in (Path("unlisted-source"), "../foreign", "/foreign", "a/../foreign"):
            with self.subTest(relative=str(relative)), self.assertRaises(ValueError):
                successor.current_source_before_fixture_successor(relative, b"unlisted-data", ROOT)
        self.assertEqual(b"unlisted-data", successor.current_source_before_fixture_successor("unlisted-source", b"unlisted-data", ROOT))
        for relative in ("scripts/ci/test_camera_tooling562_source_projection.py", "scripts/ci/test_camera_tooling566_source_projection.py"):
            raw = (ROOT / relative).read_bytes()
            self.assertNotIn(relative, recovery.MODIFIED)
            self.assertEqual(successor.current_source_before_fixture_successor(relative, raw, ROOT),
                             recovery.current_source_before_recovery(relative, raw, ROOT))
            self.assertEqual(recovery.current_source_before_recovery(relative, raw, ROOT),
                             recovery.peel_recovery_for_history(relative, raw, ROOT))
        for relative, endpoint in successor.ORIGINALS.items():
            raw = (ROOT / relative).read_bytes()
            self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(raw), len(raw)), relative)
        self.assertEqual(512 * 1024, successor.MAX_SPEC)
        self.assertEqual(4 * 1024 * 1024, successor.MAX_SOURCE)

    def test_new02_raw301_current303_and_exact_copied_dependencies_remain_distinct(self):
        from test_macos_share_ci668_composition import source_model
        expected = joint.fixture_inputs(ROOT) | domain740.dependency_inputs() | recovery.dependency_inputs()
        with source_model() as root:
            model_name = root
            actual_files = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(expected, actual_files)
            self.assertTrue(successor.validate_current_sources(root))
            self.assertTrue(recovery.validate_current_sources(root))
            self.assertTrue(domain740.validate_current_sources(root))
            document = joint._document(root)
            self.assertEqual(301, len(document["raw_inputs"]))
            actual = joint.current_input_hashes(root)
            self.assertEqual(303, len(actual))
            self.assertEqual(joint.fixture_inputs(root), set(actual))
            self.assertEqual({relative: sha((root / relative).read_bytes()) for relative in actual}, actual)
            self.assertEqual(successor.RAW_FIXTURES, successor.FIXTURES & set(document["raw_inputs"]))
            for relative in successor.RAW_FIXTURES:
                self.assertNotEqual(document["raw_inputs"][relative]["sha256"], actual[relative])
                raw = (root / relative).read_bytes()
                historical = domain740.current_source_before_domain740(relative, raw, root)
                endpoint = document["raw_inputs"][relative]
                self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(historical), len(historical)))
            for relative in (successor.OWNER, successor.CONTROL, successor.SPEC):
                self.assertIn(relative, expected)
                self.assertNotIn(relative, actual)
                with self.assertRaises(ValueError):
                    joint.current_source_in_view(relative, (root / relative).read_bytes(), joint.CI_VIEW, root)
            for view, count in ((joint.CI_VIEW, 175), (joint.PRODUCER_VIEW, 190), (joint.COOKIE_VIEW, 40), (joint.SHARE_VIEW, 36)):
                self.assertEqual(count, len(joint.predecessor_input_hashes(view, root)))
        self.assertFalse(model_name.exists())

    def test_new03_schema_alias_size_and_changed_copied_dependency_refuse_with_owned_cleanup(self):
        document = successor._document(ROOT)
        selected = sorted(document["bindings"])[0]
        changes = (
            lambda doc: doc["originals"][domain740.SPEC].update(sha256="0" * 64),
            lambda doc: doc["bindings"][selected].update(before_sha256="0" * 64),
            lambda doc: doc["bindings"][selected].update(after_bytes=True),
            lambda doc: doc["bindings"][selected]["fragments"][0].update(after_fragment_sha256="0" * 64),
            lambda doc: doc["bindings"][selected]["fragments"].append(copy.deepcopy(doc["bindings"][selected]["fragments"][0])),
            lambda doc: doc["bindings"].update({"foreign-data": copy.deepcopy(doc["bindings"][selected])}),
            lambda doc: doc["control"].update(path="scripts/ci/foreign-control.py"),
            lambda doc: doc["own_guard"].update(bytes=True),
        )
        for change in changes:
            fake = copy.deepcopy(document); change(fake)
            encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with tempfile.TemporaryDirectory(prefix="fixture-successor-grammar-") as folder:
                root = Path(folder); target = root / successor.SPEC
                target.parent.mkdir(parents=True); target.write_bytes(encoded)
                with patch.object(successor, "SPEC_SHA256", sha(encoded)), self.assertRaises(ValueError):
                    successor._document(root)
            self.assertFalse(root.exists())
        raw = (ROOT / successor.SPEC).read_bytes()
        with tempfile.TemporaryDirectory(prefix="fixture-successor-alias-") as folder:
            root = Path(folder); target = root / successor.SPEC
            target.parent.mkdir(parents=True); target.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError): successor._document(root)
            target.write_bytes(b"x" * (successor.MAX_SPEC + 1))
            with self.assertRaises(ValueError): successor._document(root)
            target.unlink(); backing = target.with_name("backing.json"); backing.write_bytes(raw)
            target.symlink_to(backing)
            with self.assertRaises(ValueError): successor._document(root)
        self.assertFalse(root.exists())
        from test_macos_share_ci668_composition import source_model
        with source_model() as root:
            model_name = root
            inverse = successor._inverse
            changed = []
            def inverse_then_change_owned_dependency(payload, row):
                value = inverse(payload, row)
                if not changed:
                    target = root / successor.CONTROL
                    with target.open("ab") as handle: handle.write(b"\n# owned custody mutation\n")
                    changed.append(True)
                return value
            with patch.object(successor, "_inverse", inverse_then_change_owned_dependency), self.assertRaisesRegex(ValueError, "source-projection-custody-cleanup-refused"):
                successor.validate_current_sources(root)
            self.assertEqual([True], changed)
        self.assertFalse(model_name.exists())

    def test_new04_exact_capacity734_raw_pin_and_two_copied_inputs_preserve_r1_nine_routes_without_enrollment(self):
        document = successor._document(ROOT)
        original = joint._document(ROOT)
        relative = successor.CAPACITY
        row = document["capacity_binding"]
        self.assertEqual(9, len(document["bindings"]))
        self.assertEqual(11, len(successor.MODIFIED))
        self.assertEqual(301, len(original["raw_inputs"]))
        self.assertEqual(successor.CAPACITY_BEFORE, original["raw_inputs"][relative])
        self.assertEqual(2, len(row["fragments"]))
        self.assertEqual(1, len(document["routing_binding"]["fragments"]))
        self.assertEqual({"scripts/ci/offline_tooling_ci_parallel734.py",
                          "scripts/ci/test_offline_tooling_ci_parallel734.py"}, set(successor.COPIED734))
        raw = (ROOT / relative).read_bytes()
        old = successor.current_source_before_fixture_successor(relative, raw, ROOT)
        self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)))
        self.assertEqual(old, domain740.current_source_before_domain740(relative, raw, ROOT))
        self.assertEqual(old, recovery.current_source_before_recovery(relative, raw, ROOT))
        self.assertEqual(old, successor.peel_fixture_successor_for_history(relative, raw, ROOT))
        self.assertEqual(old, successor.peel_fixture_successor_for_history(relative, old, ROOT))
        for bad in (old, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
            with self.subTest(operand=type(bad).__name__), self.assertRaises(ValueError):
                successor.current_source_before_fixture_successor(relative, bad, ROOT)
        unknown = raw + b"\n# unknown capacity source\n"
        self.assertEqual(unknown, successor.peel_fixture_successor_for_history(relative, unknown, ROOT))
        remote_relative = successor.REMOTE
        remote_row = document["remote_binding"]
        self.assertIn(remote_relative, original["raw_inputs"])
        self.assertEqual(1, len(remote_row["fragments"]))
        remote_raw = (ROOT / remote_relative).read_bytes()
        remote_r1 = successor.current_source_before_fixture_successor(remote_relative, remote_raw, ROOT)
        self.assertEqual(successor.REMOTE_BEFORE, {"bytes": len(remote_r1), "sha256": sha(remote_r1)})
        self.assertNotEqual(successor.REMOTE_BEFORE, original["raw_inputs"][remote_relative])
        remote_ancestor = domain740.current_source_before_domain740(remote_relative, remote_raw, ROOT)
        self.assertEqual(original["raw_inputs"][remote_relative],
                         {"bytes": len(remote_ancestor), "sha256": sha(remote_ancestor)})
        self.assertEqual(remote_r1, successor.peel_fixture_successor_for_history(remote_relative, remote_raw, ROOT))
        self.assertEqual(remote_r1, successor.peel_fixture_successor_for_history(remote_relative, remote_r1, ROOT))
        for bad in (remote_r1, remote_raw[:-1], remote_raw + b"\n", remote_raw + remote_raw,
                    b"", None, bytearray(remote_raw), remote_raw.decode()):
            with self.subTest(remote_operand=type(bad).__name__), self.assertRaises(ValueError):
                successor.current_source_before_fixture_successor(remote_relative, bad, ROOT)
        remote_unknown = remote_raw + b"\n# unknown remote hotpath source\n"
        self.assertEqual(remote_unknown,
                         successor.peel_fixture_successor_for_history(remote_relative, remote_unknown, ROOT))
        current_joint = (ROOT / successor.ROUTING).read_bytes()
        r1_joint = successor._inverse(current_joint, document["routing_binding"])
        with self.assertRaises(ValueError):
            successor.current_source_before_fixture_successor(successor.ROUTING, r1_joint, ROOT)
        self.assertEqual(successor._inverse(r1_joint, document["bindings"][successor.ROUTING]),
                         successor.peel_fixture_successor_for_history(successor.ROUTING, r1_joint, ROOT))
        from test_macos_share_ci668_composition import source_model
        with source_model() as root:
            model_name = root
            expected = joint.fixture_inputs(ROOT) | domain740.dependency_inputs() | recovery.dependency_inputs()
            self.assertEqual(expected, {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()})
            actual = joint.current_input_hashes(root)  # One fresh full joint check, no all-input mutation loop.
            self.assertEqual(303, len(actual))
            self.assertEqual(joint.fixture_inputs(root), set(actual))
            self.assertEqual(sha((root / relative).read_bytes()), actual[relative])
            self.assertNotEqual(original["raw_inputs"][relative]["sha256"], actual[relative])
            self.assertIn(remote_relative, actual)
            self.assertEqual(sha((root / remote_relative).read_bytes()), actual[remote_relative])
            self.assertNotEqual(original["raw_inputs"][remote_relative]["sha256"], actual[remote_relative])
            self.assertIn(remote_relative, recovery.dependency_inputs())
            for name, endpoint in successor.COPIED734.items():
                target = root / name
                payload = target.read_bytes()
                self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(payload), len(payload)))
                self.assertIn(name, recovery.dependency_inputs())
                self.assertNotIn(name, actual)
                with self.assertRaises(ValueError):
                    joint.current_source_in_view(name, payload, joint.CI_VIEW, root)
                try:
                    target.write_bytes(payload + b"\n# drifted owned capacity dependency\n")
                    with self.assertRaises(ValueError):
                        successor.validate_current_sources(root)
                finally:
                    target.write_bytes(payload)
                try:
                    target.unlink()
                    with self.assertRaises(FileNotFoundError):
                        successor.validate_current_sources(root)
                finally:
                    target.write_bytes(payload)
            remote_target = root / remote_relative
            remote_payload = remote_target.read_bytes()
            try:
                remote_target.write_bytes(remote_payload + b"\n# drifted owned remote hotpath source\n")
                with self.assertRaises(ValueError):
                    successor.validate_current_sources(root)
            finally:
                remote_target.write_bytes(remote_payload)
            try:
                remote_target.unlink()
                with self.assertRaises(FileNotFoundError):
                    successor.validate_current_sources(root)
            finally:
                remote_target.write_bytes(remote_payload)
            self.assertTrue(successor.validate_current_sources(root))
            for view, count in ((joint.CI_VIEW, 175), (joint.PRODUCER_VIEW, 190),
                                (joint.COOKIE_VIEW, 40), (joint.SHARE_VIEW, 36)):
                self.assertEqual(count, len(joint.predecessor_input_hashes(view, root)))
        self.assertFalse(model_name.exists())
