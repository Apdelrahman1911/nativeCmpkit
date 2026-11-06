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
            if relative in successor.ORDINARY_FIXTURES:
                ordinary = document["ordinary_fixture_bindings"][relative]
                self.assertEqual((ordinary["before_sha256"], ordinary["before_bytes"]),
                                 (sha(forward), len(forward)), relative)
                for fragment in ordinary["fragments"]:
                    before, after = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(1, forward.count(before), relative)
                    forward = forward.replace(before, after, 1)
            if relative in successor.PLATFORM_CUSTODY_MODIFIED743:
                platform = document["platform_custody_bindings743"][relative]
                self.assertEqual((platform["before_sha256"], platform["before_bytes"]),
                                 (sha(forward), len(forward)), relative)
                for fragment in platform["fragments"]:
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
        self.assertEqual(11, len(successor.BASE_MODIFIED))
        self.assertEqual(16, len(successor.ORDINARY_MODIFIED))
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
        current_joint = successor._inverse(current_joint,
            document["platform_custody_bindings743"][successor.ROUTING])
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

    def test_new05_ordinary_six_roundtrips_refuse_old_partial_foreign_and_preserve_original730_bytes(self):
        document = successor._document(ROOT)
        self.assertEqual(6, len(successor.ORDINARY_FIXTURES))
        self.assertEqual(11, len(successor.BASE_MODIFIED)); self.assertEqual(16, len(successor.ORDINARY_MODIFIED))
        self.assertEqual(successor.ORDINARY_MODIFIED | successor.RELATED_MODIFIED | successor.FAILURE_MODIFIED,
                         successor.MODIFIED)
        legacy = {key: value for key, value in document.items() if key not in
                  {"ordinary_fixture_scope", "ordinary_fixture_bindings", "ordinary_previous730",
                   "related_scope", "related_bindings", "related_previous730", "related_copied",
                    "failure_scope", "failure_bindings", "failure_previous730", "failure_copied"}}
        legacy["control"] = successor.ORDINARY_PREVIOUS730["control"]
        legacy["own_guard"] = successor.ORDINARY_PREVIOUS730["own_guard"]
        encoded = (json.dumps(legacy, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(("65e45763c96ee12d6317f35be7566038ea21b319661ccbb68b3c8e34013694f7", 34278),
                         (sha(encoded), len(encoded)))
        for relative, row in document["ordinary_fixture_bindings"].items():
            raw = (ROOT / relative).read_bytes()
            previous = successor._inverse(raw, row)
            self.assertEqual(successor.ORDINARY_FIXTURE_BEFORE[relative],
                             {"sha256": sha(previous), "bytes": len(previous)}, relative)
            forward = previous
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before), relative)
                forward = forward.replace(before, after, 1)
            self.assertEqual(raw, forward, relative)
            expected = (successor._inverse(previous, document["bindings"][relative])
                        if relative in successor.BASE_MODIFIED else previous)
            self.assertEqual(expected, successor.current_source_before_fixture_successor(relative, raw, ROOT))
            self.assertEqual(expected, successor.peel_fixture_successor_for_history(relative, raw, ROOT))
            for bad in (previous, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
                with self.subTest(relative=relative, operand=type(bad).__name__), self.assertRaises(ValueError):
                    successor.current_source_before_fixture_successor(relative, bad, ROOT)
            unknown = raw + b"\n# unknown ordinary fixture\n"
            self.assertEqual(unknown, successor.peel_fixture_successor_for_history(relative, unknown, ROOT))
        for relative, endpoint in successor.ORIGINALS.items():
            raw = (ROOT / relative).read_bytes()
            self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(raw), len(raw)))
        self.assertEqual(512 * 1024, successor.MAX_SPEC); self.assertEqual(4 * 1024 * 1024, successor.MAX_SOURCE)

    def test_new06_existing734_then_original711_620_and_inventory_guards_hold_without_owner_execution(self):
        from test_offline_tooling_failure_evidence711 import original711_source
        import test_offline_tooling_failure_parent_ids658 as original658
        from test_offline_tooling_failure_inventory import _owner_sources, OLD_OWNER_SHA256
        self.assertEqual("58f08f3fcda1e490743a8d28f7881473a28f5fcd1a3127abfffce35d6e7b2cb5", sha(original711_source()))
        self.assertEqual(original658.BEFORE_OWNER_SHA256, sha(original658.backing("owner_before")))
        for key, expected in original658.PRESERVED_SHA256.items():
            self.assertEqual(expected, sha(original658.backing(key)))
        before, after = _owner_sources()
        self.assertEqual(OLD_OWNER_SHA256, sha(before)); self.assertNotEqual(before, after)

    def test_new07_related_ten_roundtrips_strict_current_and_history_keep_copied777_out_of_raw301(self):
        document = successor._document(ROOT)
        self.assertEqual((11, 6, 16, 10), (len(successor.BASE_MODIFIED), len(successor.ORDINARY_FIXTURES),
                                        len(successor.ORDINARY_MODIFIED), len(successor.RELATED_MODIFIED)))
        self.assertFalse(successor.ORDINARY_MODIFIED & successor.RELATED_MODIFIED)
        for relative, row in document["related_bindings"].items():
            raw = (ROOT / relative).read_bytes()
            original = successor.current_source_before_fixture_successor(relative, raw, ROOT)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(original), len(original)), relative)
            forward = original
            for fragment in row["fragments"]:
                self.assertEqual(1, forward.count(fragment["before"].encode()), relative)
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            if relative in successor.FAILURE_MODIFIED:
                for fragment in document["failure_bindings"][relative]["fragments"]:
                    self.assertEqual(1, forward.count(fragment["before"].encode()), relative)
                    forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(raw, forward, relative)
            self.assertEqual(original, successor.peel_fixture_successor_for_history(relative, raw, ROOT))
            self.assertIs(original, successor.peel_fixture_successor_for_history(relative, original, ROOT))
            for invalid in (original, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
                with self.subTest(relative=relative, invalid=type(invalid).__name__), self.assertRaises(ValueError):
                    successor.current_source_before_fixture_successor(relative, invalid, ROOT)
            unknown = raw + b"\n# unreviewed related fixture\n"
            self.assertIs(unknown, successor.peel_fixture_successor_for_history(relative, unknown, ROOT))
        for relative, pin in successor.RELATED_COPIED.items():
            self.assertIn(relative, successor.dependency_inputs())
            self.assertNotIn(relative, successor.MODIFIED)
            raw = (ROOT / relative).read_bytes()
            comparison = successor._inverse(raw, document["failure_bindings"][relative])
            self.assertEqual((pin["sha256"], pin["bytes"]), (sha(comparison), len(comparison)))
            self.assertNotEqual(comparison, raw)
            current = json.loads((ROOT / recovery.CURRENT303_SPEC).read_bytes())
            self.assertNotIn(relative, current["raw_inputs"])
            self.assertEqual(301, len(current["raw_inputs"]))
        self.assertTrue(successor.validate_current_sources(ROOT))

    def test_new08_related_previous_first_nine_and_original730_are_exact_data_not_reexecuted_source(self):
        document = successor._document(ROOT)
        v1 = {key: value for key, value in document.items() if key not in
              {"failure_scope", "failure_bindings", "failure_previous730", "failure_copied"}}
        v1["control"] = successor.FAILURE_PREVIOUS730["control"]
        v1["own_guard"] = successor.FAILURE_PREVIOUS730["own_guard"]
        encoded = (json.dumps(v1, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(("1e4b8338579207f1530b91ed75472ece6492a162fa6613ddfb132ce7acd68cf3", 84713),
                         (sha(encoded), len(encoded)))
        prior = {key: value for key, value in v1.items() if key not in
                 {"related_scope", "related_bindings", "related_previous730", "related_copied"}}
        prior["control"] = successor.RELATED_PREVIOUS730["control"]
        prior["own_guard"] = successor.RELATED_PREVIOUS730["own_guard"]
        encoded = (json.dumps(prior, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(("792ce3e18e070877a95d69f514b36c7552bdaa9bf91904f4b57baaa01b096817", 55485),
                         (sha(encoded), len(encoded)))
        original = {key: value for key, value in prior.items() if key not in
                    {"ordinary_fixture_scope", "ordinary_fixture_bindings", "ordinary_previous730"}}
        original["control"] = successor.ORDINARY_PREVIOUS730["control"]
        original["own_guard"] = successor.ORDINARY_PREVIOUS730["own_guard"]
        encoded = (json.dumps(original, sort_keys=True, indent=2) + "\n").encode()
        self.assertEqual(("65e45763c96ee12d6317f35be7566038ea21b319661ccbb68b3c8e34013694f7", 34278),
                         (sha(encoded), len(encoded)))
        current_base = (recovery.MODIFIED | set(recovery.ADDED_INPUTS) |
                        {recovery.OWNER, recovery.CONTROL, recovery.SPEC,
                         recovery.CURRENT303_SPEC, recovery.DOMAIN740_SPEC})
        self.assertEqual(59, len(current_base))
        self.assertEqual(current_base | successor.dependency_inputs(), recovery.dependency_inputs())
        for relative, pin in successor.ORIGINALS.items():
            raw = (ROOT / relative).read_bytes()
            self.assertEqual((pin["sha256"], pin["bytes"]), (sha(raw), len(raw)))
        self.assertEqual((512 * 1024, 4 * 1024 * 1024), (successor.MAX_SPEC, successor.MAX_SOURCE))


    def test_new09_failed10_six_rows_keep_strict_raw_old_refusal_and_sealed_copy_split(self):
        document = successor._document(ROOT)
        self.assertEqual((6, 5, 1), (len(document["failure_bindings"]),
                                    len(successor.FAILURE_MODIFIED), len(successor.FAILURE_COPIED)))
        self.assertEqual(successor.V1_MODIFIED | successor.FAILURE_MODIFIED, successor.PRE_PLATFORM_MODIFIED743)
        self.assertEqual(successor.PRE_PLATFORM_MODIFIED743 | successor.PLATFORM_CUSTODY_MODIFIED743, successor.MODIFIED)
        self.assertEqual(26, len(successor.V1_MODIFIED))
        self.assertEqual(29, len(successor.PRE_PLATFORM_MODIFIED743))
        self.assertEqual(31, len(successor.MODIFIED))
        for relative, row in document["failure_bindings"].items():
            actual = (ROOT / relative).read_bytes()
            raw = (successor._inverse(actual, document["platform_custody_bindings743"][relative])
                   if relative in successor.PLATFORM_CUSTODY_MODIFIED743 else actual)
            prior = successor._inverse(raw, row)
            self.assertEqual(successor.FAILURE_BEFORE[relative], {"bytes": len(prior), "sha256": sha(prior)})
            if relative in successor.FAILURE_COPIED:
                self.assertNotIn(relative, successor.MODIFIED)
                self.assertEqual(successor.RELATED_COPIED[relative], {"bytes": len(prior), "sha256": sha(prior)})
                with self.assertRaises(ValueError):
                    successor._inverse(prior, row)
                continue
            expected = (successor._inverse(prior, document["related_bindings"][relative])
                        if relative in successor.RELATED_MODIFIED else prior)
            self.assertEqual(expected, successor.current_source_before_fixture_successor(relative, actual, ROOT))
            self.assertEqual(expected, successor.peel_fixture_successor_for_history(relative, actual, ROOT))
            self.assertEqual(expected, successor.peel_fixture_successor_for_history(relative, expected, ROOT))
            for bad in (prior, actual[:-1], actual + b"\n", actual + actual, b"", None, bytearray(actual), actual.decode()):
                with self.subTest(relative=relative, operand=type(bad).__name__), self.assertRaises(ValueError):
                    successor.current_source_before_fixture_successor(relative, bad, ROOT)
            unknown = actual + b"\n# unknown failed10 source\n"
            self.assertIs(unknown, successor.peel_fixture_successor_for_history(relative, unknown, ROOT))
        selected = sorted(successor.FAILURE_MODIFIED)[0]
        changes = (
            lambda doc: doc["failure_bindings"][selected].update(before_sha256="0" * 64),
            lambda doc: doc["failure_bindings"][selected].update(after_bytes=True),
            lambda doc: doc["failure_bindings"][selected]["fragments"].append(
                copy.deepcopy(doc["failure_bindings"][selected]["fragments"][0])),
            lambda doc: doc["failure_copied"].append("foreign-copy"),
            lambda doc: doc["failure_previous730"].update(sha256="0" * 64),
        )
        for change in changes:
            fake = copy.deepcopy(document); change(fake)
            encoded = (json.dumps(fake, sort_keys=True, separators=(",", ":")) + "\n").encode()
            with tempfile.TemporaryDirectory(prefix="failed10-schema-") as directory:
                root = Path(directory); target = root / successor.SPEC
                target.parent.mkdir(parents=True); target.write_bytes(encoded)
                with patch.object(successor, "SPEC_SHA256", sha(encoded)), self.assertRaises(ValueError):
                    successor._document(root)
            self.assertFalse(root.exists())

    def test_new10_raw_ff_boundaries_qualify_once_then_existing_ancestor_data_refuses_old_and_drift(self):
        import android_external328_source_projection as external
        import arm64_stop_candidate_source_projection as arm64
        document = successor._document(ROOT)
        relative = "scripts/ci/test_android_camera_pre_reporter_fail_fast.py"
        self.assertNotIn(relative, successor.FAILURE_MODIFIED)
        raw = (ROOT / relative).read_bytes()
        row = document["related_bindings"][relative]
        self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(raw), len(raw)))
        old730 = successor._inverse(raw, row)
        external_row = external._bindings()[relative]
        stage = arm64.current_source_before_arm64_stop_candidate(relative, raw)
        history = external.current_source_for_history(relative, raw)
        self.assertEqual(external_row["after_sha256"], sha(stage))
        self.assertEqual(external_row["before_sha256"], sha(history))
        for boundary in (arm64.current_source_before_arm64_stop_candidate, external.current_source_for_history):
            for bad in (old730, stage, history, raw[:-1], raw + b"\n", raw + raw, b"", None, bytearray(raw), raw.decode()):
                with self.subTest(boundary=boundary.__name__, operand=type(bad).__name__), self.assertRaises(ValueError):
                    boundary(relative, bad)
        self.assertEqual(history, external.source_before_android_external328(relative, history))

    def test_new11_copied777_current_custody_refuses_prior_drift_missing_and_alias_in_owned_finite_copy(self):
        import os
        document = successor._document(ROOT)
        relative = next(iter(successor.FAILURE_COPIED))
        raw = (ROOT / relative).read_bytes()
        old = successor._inverse(raw, document["failure_bindings"][relative])
        with tempfile.TemporaryDirectory(prefix="failed10-copy777-") as directory:
            root = Path(directory)
            for name in successor.dependency_inputs():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / name).read_bytes())
            self.assertTrue(successor.validate_current_sources(root))
            target = root / relative
            for refused in (old, raw + b"\n", raw + raw):
                try:
                    target.write_bytes(refused)
                    with self.assertRaises(ValueError): successor.validate_current_sources(root)
                finally:
                    target.write_bytes(raw)
            try:
                target.unlink()
                with self.assertRaises(FileNotFoundError): successor.validate_current_sources(root)
                backing = target.with_name("owned777-backing.py")
                backing.write_bytes(raw)
                target.symlink_to(backing)
                with self.assertRaises((ValueError, OSError)): successor.validate_current_sources(root)
                target.unlink()
                os.link(backing, target)
                with self.assertRaises((ValueError, OSError)): successor.validate_current_sources(root)
            finally:
                if target.exists() or target.is_symlink(): target.unlink()
                target.write_bytes(raw)
            self.assertTrue(successor.validate_current_sources(root))
        self.assertFalse(root.exists())


    def test_new12_ancestor_cache_hits_keep_fresh_ordinary_json_and_all34_bindings(self):
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        with patch.object(successor, "_ordinary", wraps=successor._ordinary) as ordinary, \
                patch.object(joint, "_json", wraps=joint._json) as parser, \
                patch.object(domain740, "_binding", wraps=domain740._binding) as binding:
            first = successor._document(ROOT)
            cold = successor._ancestor_cached743.cache_info()
            second = successor._document(ROOT)
            warm = successor._ancestor_cached743.cache_info()
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertEqual(2, ordinary.call_count)
        self.assertEqual(2, parser.call_count)
        self.assertEqual(68, binding.call_count)
        self.assertEqual((3, 3), (cold.misses, cold.currsize))
        self.assertEqual(3, warm.hits - cold.hits)
        self.assertEqual(3, warm.maxsize)
        first["control"]["bytes"] = 1
        self.assertNotEqual(first, second)

    def test_new13_ancestor_type_authority_and_stage_keys_never_cache_refusals(self):
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        reason = "ancestor743-essential-refusal"
        raw = b"ordinary immutable authority"
        boolean = {"value": True}
        expected = successor._ancestor_uncached743(boolean)
        self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, boolean, expected, 1, reason))
        warm = successor._ancestor_cached743.cache_info()
        self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, boolean, expected, 1, reason))
        self.assertEqual(warm.hits + 1, successor._ancestor_cached743.cache_info().hits)
        for changed in ({"value": 1}, {"value": 1.0}, {"value": "True"}, {"value": None}):
            before = successor._ancestor_cached743.cache_info()
            for attempt in range(2):
                with self.subTest(changed=changed, attempt=attempt), self.assertRaisesRegex(ValueError, reason):
                    successor._canonical_ancestor_identity743(raw, changed, expected, 1, reason)
            after = successor._ancestor_cached743.cache_info()
            self.assertEqual(before.currsize, after.currsize)
            self.assertEqual(before.misses + 2, after.misses)
            own_expected = successor._ancestor_uncached743(changed)
            self.assertEqual(own_expected, successor._canonical_ancestor_identity743(raw, changed, own_expected, 1, reason))
        for stage in (True, 1.0, -1, 3, "1"):
            before = successor._ancestor_cached743.cache_info()
            self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, boolean, expected, stage, reason))
            self.assertEqual(before, successor._ancestor_cached743.cache_info())
        before = successor._ancestor_cached743.cache_info()
        for attempt in range(2):
            with self.assertRaisesRegex(ValueError, reason):
                successor._canonical_ancestor_identity743(raw, boolean, ("0" * 64, expected[1]), 1, reason)
        self.assertEqual(before.currsize, successor._ancestor_cached743.cache_info().currsize)
        self.assertEqual(before.misses + 2, successor._ancestor_cached743.cache_info().misses)
        self.assertLessEqual(successor._ancestor_cached743.cache_info().currsize, 3)

    def test_new14_warm_changed_parser_tree_still_faces_exact_ancestor_hash(self):
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        document = successor._document(ROOT)
        selected = next(iter(document["bindings"]))
        changed = copy.deepcopy(document)
        changed["bindings"][selected]["after_sha256"] = "0" * 64
        before = successor._ancestor_cached743.cache_info()
        with patch.object(joint, "_json", return_value=changed):
            for attempt in range(2):
                with self.subTest(attempt=attempt), self.assertRaisesRegex(
                    ValueError, "all-sealed-V1-related-and-ordinary-bindings"
                ):
                    successor._document(ROOT)
        after = successor._ancestor_cached743.cache_info()
        self.assertEqual(before.currsize, after.currsize)
        self.assertEqual(before.misses + 2, after.misses)
        self.assertEqual(before.hits, after.hits)

    def test_new15_warm_serializer_and_helper_drift_use_original_uncached_behavior(self):
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        document = {"ordinary": [True, 1, 1.0, -0.0, 0.0, "\U0001f680"]}
        raw = b"ordinary snapshot"
        expected = successor._ancestor_uncached743(document)
        self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, document, expected, 0, "ancestor743"))
        before = successor._ancestor_cached743.cache_info()
        with patch.object(json, "dumps", wraps=json.dumps) as serializer:
            self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, document, expected, 0, "ancestor743"))
            self.assertEqual(1, serializer.call_count)
        self.assertEqual(before, successor._ancestor_cached743.cache_info())
        with patch.object(successor, "sha", return_value="0" * 64) as digest:
            actual = successor._canonical_ancestor_identity743(raw, document, expected, 0, "ancestor743")
            self.assertEqual(("0" * 64, expected[1]), actual)
            self.assertEqual(1, digest.call_count)
        self.assertEqual(before, successor._ancestor_cached743.cache_info())
        with patch.object(successor, "_ancestor_uncached743", return_value=("1" * 64, expected[1])) as original:
            self.assertEqual(("1" * 64, expected[1]),
                             successor._canonical_ancestor_identity743(raw, document, expected, 0, "ancestor743"))
            original.assert_called_once_with(document)
        self.assertEqual(before, successor._ancestor_cached743.cache_info())
        # indent=2 still reads key_separator from the live encoder class. Merely
        # comparing class/method identities would wrongly reuse a warm hash.
        with patch.object(json.JSONEncoder, "key_separator", ":"):
            changed = successor._ancestor_uncached743(document)
            self.assertNotEqual(expected, changed)
            self.assertEqual(changed, successor._canonical_ancestor_identity743(
                raw, document, expected, 0, "ancestor743"))
        self.assertEqual(before, successor._ancestor_cached743.cache_info())
        # item_separator is overridden by indent2, but changed serializer class
        # state still stays outside the original verified context without a hit.
        with patch.object(json.JSONEncoder, "item_separator", ",  "):
            self.assertEqual(expected, successor._canonical_ancestor_identity743(
                raw, document, expected, 0, "ancestor743"))
        self.assertEqual(before, successor._ancestor_cached743.cache_info())
        successor._document(ROOT)
        manifest_warm = successor._ancestor_cached743.cache_info()
        with patch.object(json.JSONEncoder, "key_separator", ":"):
            with self.assertRaisesRegex(ValueError, "all-sealed-V1-related-and-ordinary-bindings"):
                successor._document(ROOT)
        self.assertEqual(manifest_warm, successor._ancestor_cached743.cache_info())

    def test_new16_nonfinite_foreign_and_key_bounds_fall_back_with_bounded_concurrent_results(self):
        from concurrent.futures import ThreadPoolExecutor
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        raw = b"ordinary snapshot"
        foreign_values = (
            {"value": float("nan")}, {"value": float("inf")}, {"value": (True, 1)},
            {"value": 1 << 80}, {"value": "x" * (successor.MAX_ANCESTOR_KEY_CHARS743 + 1)},
            {"value": [0] * (successor.MAX_ANCESTOR_KEY_NODES743 + 1)},
        )
        for document in foreign_values:
            expected = successor._ancestor_uncached743(document)
            before = successor._ancestor_cached743.cache_info()
            self.assertEqual(expected, successor._canonical_ancestor_identity743(raw, document, expected, 2, "ancestor743"))
            self.assertEqual(before, successor._ancestor_cached743.cache_info())
        ordinary = {"value": [True, 1, 1.0, -0.0, 0.0, None, "\U0001f680"]}
        expected = successor._ancestor_uncached743(ordinary)
        for unsupported_raw in (bytearray(raw), raw.decode(), b"", b"x" * (successor.MAX_ANCESTOR_RAW743 + 1)):
            before = successor._ancestor_cached743.cache_info()
            self.assertEqual(expected, successor._canonical_ancestor_identity743(unsupported_raw, ordinary, expected, 2, "ancestor743"))
            self.assertEqual(before, successor._ancestor_cached743.cache_info())
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: successor._canonical_ancestor_identity743(
                raw, ordinary, expected, 2, "ancestor743"), range(8)))
        self.assertEqual([expected] * 8, results)
        self.assertTrue(all(type(result) is tuple for result in results))
        self.assertLessEqual(successor._ancestor_cached743.cache_info().currsize, 3)

    def test_new17_warm_manifest_hash_missing_symlink_and_hardlink_refuse_before_cache(self):
        import os
        successor._ancestor_cached743.cache_clear()
        self.addCleanup(successor._ancestor_cached743.cache_clear)
        raw = (ROOT / successor.SPEC).read_bytes()
        with tempfile.TemporaryDirectory(prefix="ancestor743-fresh-manifest-") as directory:
            root = Path(directory)
            target = root / successor.SPEC
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            successor._document(root)
            successor._document(root)
            before = successor._ancestor_cached743.cache_info()
            try:
                target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError):
                    successor._document(root)
                target.unlink()
                with self.assertRaises(FileNotFoundError):
                    successor._document(root)
                backing = target.with_name("owned-ancestor743-backing.json")
                backing.write_bytes(raw)
                target.symlink_to(backing)
                with self.assertRaises((ValueError, OSError)):
                    successor._document(root)
                target.unlink()
                os.link(backing, target)
                with self.assertRaises((ValueError, OSError)):
                    successor._document(root)
            finally:
                if target.exists() or target.is_symlink():
                    target.unlink()
                target.write_bytes(raw)
            self.assertEqual(before, successor._ancestor_cached743.cache_info())
        self.assertFalse(root.exists())


# CI743 NEW scalar-materialization controls in the existing owning control.
import ast

from collections import Counter

from concurrent.futures import ThreadPoolExecutor

import math

import os

import stat

import macos_share_ci668_composition as target

EXPECTED_OWNER_BYTES = 80690

EXPECTED_OWNER_SHA256 = 'dae1623566e2ecad0184580dc81cb8ec1b57d018e96fdaf66fd13b3a653e7873'

EXPECTED_UNCHANGED_MODULE_AST_SHA256 = '631f36ec42fced7dbf59cb41a2394452ac7b383db9feb930b52f59a7e356fca9'

EXPECTED_GUARD_AST_SHA256 = {'need': '1db915c194b493b7fd38193804424c73648aa805b86a1dc583ac867e239aee29', '_portable_ordinary': 'b718e70eb8d21ae27fda58fa9187d3d2353c96ce6c074a8942ed08b79666de93', '_freeze_json_content': '88b687074abe05da831e0989bce50686ae8b1abd694f028d3d7a5c1d03216e9a', '_json_parser_context': '6fb02de4694b8b7eed2b36a779997b030570d27fa4c5ae123f8490574b359db8', '_cached_json_tree': 'c6d22d251626b1d229696e9c582bfc7642cd489efb9c91f1bcdcfde70c6914e7', '_json': '66b758f87140c1c4223755c21159642c0afb4200d878ba92284d566d393e4c89', '_shape': 'a09b8162bbdb0815cb8195a99a2e725d5ed8c4ac23f1b241fdfe7622a43808da', '_document': '85367f3a54191ad3566b23c0af5b65d16237ad6f4cafb6673f40f0db359a4ed4', '_sealed_predecessor_hashes': '774b28c3ac4e61bf5ace41b89ad57624d2b53037f2c4613a1279f77608c284c4'}

FULL10 = ("st_atime_ns", "st_ctime_ns", "st_dev", "st_gid", "st_ino",
          "st_mode", "st_mtime_ns", "st_nlink", "st_size", "st_uid")

PAYLOAD = b'{"array":[1,true,null,"leaf",-0.0,{"nested":[2,3]}],"scalar":7}'

EXPECTED = {"array": [1, True, None, "leaf", -0.0, {"nested": [2, 3]}], "scalar": 7}

def _mutable_ids(value):
    if type(value) is dict:
        return {id(value)}.union(*(_mutable_ids(child) for child in value.values()))
    if type(value) is list:
        return {id(value)}.union(*(_mutable_ids(child) for child in value))
    return set()

def _ast_sha(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode("utf-8")).hexdigest()

class JsonScalarMaterialization743Tests(unittest.TestCase):
    def setUp(self):
        target._cached_json_tree.cache_clear()
        self.addCleanup(target._cached_json_tree.cache_clear)

    def test_new01_nested_scalar_types_signed_zero_and_container_roundtrip(self):
        values = [None, False, True, 0, 1, -1, 2**63 - 1, -(2**63), "", "unicode-\u03bb", 0.0, -0.0]
        nested = {"array": values, "object": {"empty": [], "inner": {"none": None}}}
        frozen = target._freeze_json_content(nested)
        actual = target._thaw_json_content(frozen)
        self.assertEqual(actual, nested)
        self.assertFalse(_mutable_ids(actual) & _mutable_ids(nested))
        for expected, observed in zip(values, actual["array"]):
            self.assertIs(type(observed), type(expected))
        self.assertEqual(math.copysign(1.0, actual["array"][-2]), 1.0)
        self.assertEqual(math.copysign(1.0, actual["array"][-1]), -1.0)
        for scalar in values:
            observed = target._thaw_json_content(target._freeze_json_content(scalar))
            self.assertIs(type(observed), type(scalar))
            self.assertEqual(observed, scalar)
        class IntSubclass(int):
            pass
        for refused in ({1: "non-string-key"}, (1,), {1}, IntSubclass(1), {"bad": (1,)}):
            with self.subTest(refused_type=type(refused).__name__):
                with self.assertRaises(TypeError):
                    target._freeze_json_content(refused)

    def test_new02_warm_cache_materializes_fresh_nested_mutable_containers(self):
        first = target._json(PAYLOAD)
        warm = target._cached_json_tree.cache_info()
        second = target._json(PAYLOAD)
        after = target._cached_json_tree.cache_info()
        self.assertEqual(first, EXPECTED)
        self.assertEqual(second, EXPECTED)
        self.assertEqual(after.hits, warm.hits + 1)
        self.assertEqual(after.misses, warm.misses)
        self.assertFalse(_mutable_ids(first) & _mutable_ids(second))
        first["array"].append("changed")
        first["array"][5]["nested"].append(99)
        first["added"] = []
        third = target._json(PAYLOAD)
        self.assertEqual(second, EXPECTED)
        self.assertEqual(third, EXPECTED)
        self.assertFalse(_mutable_ids(second) & _mutable_ids(third))

    def test_new03_recursive_calls_remain_for_containers_not_scalar_leaves(self):
        tree = target._freeze_json_content(EXPECTED)
        original = target._thaw_json_content
        observed = []
        def tracked(node):
            observed.append(node[0])
            return original(node)
        with patch.object(target, "_thaw_json_content", side_effect=tracked):
            actual = target._thaw_json_content(tree)
        self.assertEqual(actual, EXPECTED)
        self.assertEqual(Counter(observed), Counter({"object": 2, "array": 2}))
        self.assertNotIn("value", observed)

    def test_new04_existing_success_cache_remains_immutable_and_bounded16(self):
        calls = []
        def parser(payload):
            calls.append(payload)
            return json.loads(payload)
        context = (parser,)
        tree = target._cached_json_tree(PAYLOAD, context)
        second_tree = target._cached_json_tree(PAYLOAD, context)
        self.assertIs(second_tree, tree)
        self.assertEqual(calls, [PAYLOAD])
        def assert_immutable(node):
            self.assertIs(type(node), tuple)
            self.assertEqual(len(node), 2)
            kind, value = node
            if kind == "object":
                self.assertIs(type(value), tuple)
                for pair in value:
                    self.assertIs(type(pair), tuple)
                    self.assertEqual(len(pair), 2)
                    key, child = pair
                    self.assertIs(type(key), str)
                    assert_immutable(child)
            elif kind == "array":
                self.assertIs(type(value), tuple)
                for child in value:
                    assert_immutable(child)
            else:
                self.assertEqual(kind, "value")
                self.assertIn(type(value), (str, int, float, bool, type(None)))
        assert_immutable(tree)
        mutable = target._thaw_json_content(tree)
        mutable["array"][5]["nested"].append(99)
        self.assertEqual(target._thaw_json_content(tree), EXPECTED)
        self.assertEqual(target._cached_json_tree.cache_info().maxsize, 16)
        for index in range(17):
            target._cached_json_tree(json.dumps({"index": index}).encode("utf-8"), context)
        full = target._cached_json_tree.cache_info()
        self.assertEqual(full.currsize, 16)
        call_count = len(calls)
        self.assertEqual(target._thaw_json_content(target._cached_json_tree(PAYLOAD, context)), EXPECTED)
        self.assertEqual(len(calls), call_count + 1)
        self.assertEqual(target._cached_json_tree.cache_info().currsize, 16)

    def test_new05_parser_refusals_are_not_cached_or_converted_to_success(self):
        target._json(PAYLOAD)
        refused_payloads = (
            b'{"duplicate":1,"duplicate":2}',
            b'{"bad":NaN}', b'{"bad":Infinity}', b'{"bad":-Infinity}',
            b'{"bad":"\xff"}',
            b'{"nested":' + b'[' * 65 + b'0' + b']' * 65 + b'}',
        )
        for payload in refused_payloads:
            baseline = target._cached_json_tree.cache_info()
            for repeat in range(2):
                with self.subTest(payload=payload[:48], repeat=repeat):
                    with self.assertRaises(ValueError):
                        target._json(payload)
            after = target._cached_json_tree.cache_info()
            self.assertEqual(after.hits, baseline.hits)
            self.assertEqual(after.misses, baseline.misses + 2)
            self.assertEqual(after.currsize, baseline.currsize)
        foreign_calls = []
        def unfreezable_parser(payload):
            foreign_calls.append(payload)
            return {"unfreezable": set()}
        baseline = target._cached_json_tree.cache_info()
        for repeat in range(2):
            with self.assertRaises(target._UncachedJSONResult):
                target._cached_json_tree(b"{}", (unfreezable_parser,))
        after = target._cached_json_tree.cache_info()
        self.assertEqual(foreign_calls, [b"{}", b"{}"])
        self.assertEqual(after.hits, baseline.hits)
        self.assertEqual(after.misses, baseline.misses + 2)
        self.assertEqual(after.currsize, baseline.currsize)

    def test_new06_exact_bytes_and_size_refusals_stay_before_cache_hash(self):
        traps = []
        class TrapBytes(bytes):
            def __len__(self):
                traps.append("len")
                raise AssertionError("subclass length must not be evaluated")
            def __hash__(self):
                traps.append("hash")
                raise AssertionError("subclass hash must not be evaluated")
        baseline = target._cached_json_tree.cache_info()
        refused = (TrapBytes(b"{}"), bytearray(b"{}"), memoryview(b"{}"), "{}", None,
                   b"", b"x" * (target.MAX_SPEC + 1))
        for payload in refused:
            with self.subTest(payload_type=type(payload).__name__):
                with patch.object(target, "_json_parser_context", side_effect=AssertionError("context reached")) as context:
                    with patch.object(target, "_cached_json_tree", side_effect=AssertionError("cache reached")) as cache:
                        with self.assertRaises(ValueError):
                            target._json(payload)
                        context.assert_not_called()
                        cache.assert_not_called()
        self.assertEqual(traps, [])
        self.assertEqual(target._cached_json_tree.cache_info(), baseline)

    def test_new07_concurrent_warm_materialization_has_no_mutable_aliases(self):
        target._json(PAYLOAD)
        warm = target._cached_json_tree.cache_info()
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="json-scalar743") as pool:
            results = list(pool.map(lambda _: target._json(PAYLOAD), range(16)))
        after = target._cached_json_tree.cache_info()
        self.assertEqual(after.hits, warm.hits + 16)
        self.assertEqual(after.misses, warm.misses)
        identities = []
        for result in results:
            self.assertEqual(result, EXPECTED)
            current = _mutable_ids(result)
            for prior in identities:
                self.assertFalse(current & prior)
            identities.append(current)
        for index, result in enumerate(results):
            result["array"][5]["nested"].append(index)
        for index, result in enumerate(results):
            self.assertEqual(result["array"][5]["nested"], [2, 3, index])
        self.assertEqual(target._json(PAYLOAD), EXPECTED)

    def test_new08_original_filesystem_parser_shape_and_custody_guards_are_unchanged(self):
        # The actual current source is still fully read and qualified first.
        # Only the explicitly appended operation spans become historical DATA for
        # the original80690 whole-source/hash/AST pins; none of those pins change.
        import ci_fixture_successor730 as owning
        import ci_source_domain740 as arithmetic
        current_row = owning._document(ROOT)["platform_custody_bindings743"][target.OWNER]
        current_bytes = current_row["after_bytes"]
        self.assertTrue(type(current_bytes) is int and 0 < current_bytes <= target.MAX_SOURCE)
        self.assertTrue(type(target.__file__) is str and target.__file__.endswith(".py"))
        fd = os.open(target.__file__, os.O_RDONLY | os.O_NOATIME | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            before_stat = os.fstat(fd)
            before = {field: getattr(before_stat, field) for field in FULL10}
            self.assertTrue(stat.S_ISREG(before["st_mode"]))
            self.assertEqual(before["st_size"], current_bytes)
            chunks = []
            used = 0
            while used <= current_bytes:
                chunk = os.read(fd, min(65536, current_bytes + 1 - used))
                if not chunk:
                    break
                chunks.append(chunk)
                used += len(chunk)
            payload = b"".join(chunks)
            after_stat = os.fstat(fd)
            after = {field: getattr(after_stat, field) for field in FULL10}
            self.assertEqual(before, after)
        finally:
            os.close(fd)
        self.assertEqual(len(payload), current_row["after_bytes"])
        self.assertEqual(hashlib.sha256(payload).hexdigest(), current_row["after_sha256"])
        payload = arithmetic._inverse(payload, {
            "before_sha256": EXPECTED_OWNER_SHA256, "before_bytes": EXPECTED_OWNER_BYTES,
            "after_sha256": current_row["after_sha256"], "after_bytes": current_row["after_bytes"],
            "fragments": current_row["fragments"][2:]})
        self.assertEqual(len(payload), EXPECTED_OWNER_BYTES)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), EXPECTED_OWNER_SHA256)
        module = ast.parse(payload.decode("utf-8"))
        guards = ast.Module(body=[node for node in module.body
            if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "_thaw_json_content")], type_ignores=module.type_ignores)
        self.assertEqual(_ast_sha(guards), EXPECTED_UNCHANGED_MODULE_AST_SHA256)
        functions = {node.name: node for node in module.body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name, expected in EXPECTED_GUARD_AST_SHA256.items():
            self.assertEqual(_ast_sha(functions[name]), expected, name)
        self.assertEqual(target._cached_json_tree.cache_info().maxsize, 16)


class CiRawOperation743R5Controls(unittest.TestCase):
    def test_new743_private_raw_rows_preserve_owner_root_documents_fresh_public_and_every_inverse_guard(self):
        from dataclasses import FrozenInstanceError, replace as replace_operation
        from types import MappingProxyType
        import tooling_recovery671_source_projection as tooling
        fixture, recovered, domain, current = (successor._document(ROOT), recovery._document(ROOT),
                                              domain740._document(ROOT), joint._document(ROOT))
        modules = ((successor, fixture), (recovery, recovered), (domain740, domain))
        documents = MappingProxyType({ROOT: MappingProxyType({
            module.SPEC: (module.SPEC_SHA256, joint._operation_freeze(document))
            for module, document in modules})})
        operation = joint._SourceProjectionOperation(ROOT,
            MappingProxyType({ROOT: joint._operation_freeze(current)}),
            joint._operation_freeze({}), joint._operation_freeze({}), joint._operation_freeze({}),
            tuple((ROOT, module.SPEC, module.SPEC_SHA256) for module, document in modules) +
            ((ROOT, joint.SPEC, joint.SPEC_SHA256),), documents)
        self.assertEqual(tuple(current["raw_inputs"]), operation._raw_inputs743(ROOT))
        # Important distinct branch owners; not any previously accepted selector.
        important = {joint.OWNER, successor.REMOTE, tooling.SOURCE_RELATIVE, recovery.SETTINGS,
                     successor.ROUTING, sorted(successor.FAILURE_MODIFIED)[0],
                     sorted(successor.ORDINARY_FIXTURES)[0]}
        enrolled = set(current["raw_inputs"]) | {joint.OWNER, joint.SPEC}
        names = sorted(important & enrolled)
        operands = {name: joint._ordinary(ROOT, name)[0] for name in names}
        # Dependency custody is not RAW303 enrollment. Never assume tooling671
        # or the newly added fixture730 owner belongs to the immutable RAW map.
        self.assertNotIn(successor.OWNER, enrolled)
        for name in sorted((important - enrolled) | {successor.OWNER}):
            raw = joint._ordinary(ROOT, name)[0]
            with self.subTest(unlisted_dependency=name), self.assertRaises(ValueError):
                joint._raw_payload(name, raw, current, ROOT)
            with self.subTest(unlisted_dependency=name), self.assertRaises(ValueError):
                operation._raw743(name, raw, ROOT)
        with patch.object(successor, "_document", return_value=fixture) as fresh_fixture, \
                patch.object(recovery, "_document", return_value=recovered) as fresh_recovery, \
                patch.object(domain740, "_document", return_value=domain) as fresh_domain:
            for name in names:
                raw = operands[name]
                expected = joint._raw_payload(name, raw, current, ROOT)
                counts = (fresh_fixture.call_count, fresh_recovery.call_count, fresh_domain.call_count)
                self.assertEqual(expected, operation._raw743(name, raw, ROOT), name)
                self.assertEqual(counts, (fresh_fixture.call_count, fresh_recovery.call_count,
                                          fresh_domain.call_count), name)
                for bad in (expected, raw[:-1], raw + b"\n", raw + raw, b"", None,
                            bytearray(raw), raw.decode("utf-8")):
                    with self.subTest(name=name, operand=type(bad).__name__), self.assertRaises(ValueError):
                        operation._raw743(name, bad, ROOT)
            self.assertGreater(fresh_fixture.call_count, 0)
            self.assertGreater(fresh_recovery.call_count, 0)
            self.assertGreater(fresh_domain.call_count, 0)
            count = fresh_fixture.call_count
            successor.current_source_before_fixture_successor(joint.OWNER, operands[joint.OWNER], ROOT)
            successor.current_source_before_fixture_successor(joint.OWNER, operands[joint.OWNER], ROOT)
            self.assertEqual(count + 2, fresh_fixture.call_count)  # Public calls still qualify each time.
        for root in (Path("/foreign-operation743-root"), str(ROOT), None):
            with self.subTest(root=str(root)), self.assertRaises(ValueError):
                operation._raw743(joint.OWNER, operands[joint.OWNER], root)
        with self.assertRaises(ValueError):
            joint._SourceProjectionOperation._raw743(object(), joint.OWNER, operands[joint.OWNER], ROOT)
        with self.assertRaises(ValueError):
            replace_operation(operation, _target_root=object())._raw743(
                joint.OWNER, operands[joint.OWNER], ROOT)
        with self.assertRaises(ValueError):
            replace_operation(operation, _spec_origins=())._raw743(
                joint.OWNER, operands[joint.OWNER], ROOT)
        with self.assertRaises(ValueError):
            replace_operation(operation, _raw_documents743=dict(documents))._raw743(
                joint.OWNER, operands[joint.OWNER], ROOT)
        class DigestSubclass(str):
            pass
        for digest in ("0" * 64, DigestSubclass(successor.SPEC_SHA256)):
            changed = dict(documents[ROOT])
            changed[successor.SPEC] = (digest, changed[successor.SPEC][1])
            with self.subTest(digest_type=type(digest).__name__), self.assertRaises(ValueError):
                replace_operation(operation, _raw_documents743=MappingProxyType({
                    ROOT: MappingProxyType(changed)}))._raw743(joint.OWNER, operands[joint.OWNER], ROOT)
        changed = dict(documents[ROOT])
        changed[successor.SPEC] = (successor.SPEC_SHA256, dict(changed[successor.SPEC][1]))
        with self.assertRaises(ValueError):
            replace_operation(operation, _raw_documents743=MappingProxyType({
                ROOT: MappingProxyType(changed)}))._raw743(joint.OWNER, operands[joint.OWNER], ROOT)
        with self.assertRaises(TypeError):
            documents[ROOT][successor.SPEC][1]["bindings"][joint.OWNER]["after_bytes"] = 1
        with self.assertRaises(FrozenInstanceError):
            operation._target_root = Path("/foreign")
        with self.assertRaises(ValueError):
            operation._raw743("unlisted-source", b"unlisted-not-admitted", ROOT)
        # Named arithmetic itself is unchanged and reused, not replayed: verify only
        # the changed private RAW-to-existing-view routing for the four named owners.
        sentinel = object()
        for view in sorted(joint.VIEWS):
            with patch.object(joint._SourceProjectionOperation, "_raw743", return_value=b"qualified RAW") as raw, \
                    patch.object(joint, "_view", return_value=sentinel) as named, \
                    patch.object(joint, "_raw_payload", side_effect=AssertionError("No repeated public RAW shaping")):
                self.assertIs(sentinel, operation._current(joint.OWNER, operands[joint.OWNER], view, ROOT))
                raw.assert_called_once_with(joint.OWNER, operands[joint.OWNER], ROOT)
                named.assert_called_once()
                self.assertEqual((view, joint.OWNER, b"qualified RAW"), named.call_args.args[:3])
                self.assertEqual(ROOT, named.call_args.args[-1])

    def test_new743_remote_raw_prefix_and_tooling_reuse_one_existing_scope_keep_full_tail(self):
        from types import SimpleNamespace
        import android_io_remote_routing_source_projection as remote_owner
        import tooling_recovery671_source_projection as tooling
        root = Path("/controlled-remote743-no-filesystem")
        name = "scripts/ci/controlled-remote743.py"
        raw, owner_raw, joint_spec, remote_spec = b"controlled raw", b"controlled own", b"joint spec", b"remote spec"
        document = {"bindings": {}, "added_inputs": {name: sha(raw)}, "unchanged_inputs": {}}
        for mode in ("success", "raw", "tooling", "guard", "tail"):
            with self.subTest(mode=mode):
                events, primary = [], ValueError("controlled743 " + mode)
                test = self
                class Operation:
                    def _raw_inputs743(self, actual):
                        test.assertEqual(root, actual); events.append(("names", actual)); return (name,)
                    def _raw743(self, relative, payload, actual):
                        test.assertEqual(root, actual); events.append(("raw", relative, payload))
                        if mode == "raw":
                            raise primary
                        test.assertEqual({name: raw, joint.OWNER: owner_raw, joint.SPEC: joint_spec}[relative], payload)
                        return payload
                    def _validate_tooling(self, actual):
                        test.assertEqual(root, actual); events.append(("tooling", actual))
                        if mode == "tooling":
                            raise primary
                        return True
                operation = Operation()
                class Scope:
                    def __enter__(self):
                        events.append(("enter", root)); return operation
                    def __exit__(self, kind, value, traceback):
                        events.append(("exit", kind, value)); return False
                def prefix(actual, relative, maximum):
                    test.assertEqual(root, actual)
                    test.assertEqual(joint.MAX_SPEC if relative == joint.SPEC else joint.MAX_SOURCE, maximum)
                    events.append(("ordinary-prefix", relative))
                    return {name: raw, joint.OWNER: owner_raw, joint.SPEC: joint_spec}[relative], {}
                def tail_read(actual, relative):
                    test.assertEqual(root, actual); events.append(("ordinary-tail", relative))
                    value = {name: raw, remote_owner.SPEC_RELATIVE: remote_spec}[relative]
                    return value + b"drift" if mode == "tail" and relative == name else value, {}
                def guard(actual, owning):
                    test.assertEqual(root, actual); test.assertIs(document, owning); events.append(("guard", actual))
                    if mode == "guard":
                        raise primary
                    return "exact controlled guard"
                def history(relative, payload):
                    events.append(("history", relative)); return payload
                def composition(relative, payload):
                    events.append(("composition", relative)); return payload
                with patch.object(joint, "_source_projection_operation", return_value=Scope()) as scope, \
                        patch.object(joint, "_ordinary", side_effect=prefix) as ordinary_prefix, \
                        patch.object(joint, "_document", side_effect=AssertionError("No extra standalone joint shaping")), \
                        patch.object(joint, "_raw_payload", side_effect=AssertionError("No per-row public RAW shaping")), \
                        patch.object(tooling, "validate_current_sources", side_effect=AssertionError("No second owning scope")) as standalone, \
                        patch.object(remote_owner, "_document", return_value=document) as owning_document, \
                        patch.object(remote_owner, "SPEC_SHA256", sha(remote_spec)), \
                        patch.object(remote_owner, "_validate_own_guard", side_effect=guard) as owning_guard, \
                        patch("ios_popover_anchor_plan._ordinary_bytes", side_effect=tail_read), \
                        patch.object(tooling, "source_before_tooling671", side_effect=history) as original_history, \
                        patch.object(tooling, "source_before_callback_composition680", side_effect=composition) as original_composition:
                    result, caught = None, None
                    try:
                        result = remote_owner.validate_current_sources(root)
                    except Exception as error:
                        caught = error
                scope.assert_called_once_with(root)
                standalone.assert_not_called()
                self.assertEqual(("enter", root), events[0])
                exits = [event for event in events if event[0] == "exit"]
                self.assertEqual(1, len(exits))
                if mode in ("raw", "tooling"):
                    self.assertIs(primary, caught)
                    self.assertEqual(("exit", ValueError, primary), exits[0])
                    owning_document.assert_not_called(); owning_guard.assert_not_called()
                    original_history.assert_not_called(); original_composition.assert_not_called()
                    self.assertEqual(1 if mode == "raw" else 3, ordinary_prefix.call_count)
                    if mode == "raw":
                        self.assertFalse(any(event[0] == "tooling" for event in events))
                else:
                    self.assertEqual(("exit", None, None), exits[0])
                    self.assertEqual(3, ordinary_prefix.call_count)
                    owning_document.assert_called_once_with()
                    owning_guard.assert_called_once_with(root, document)
                    if mode == "success":
                        self.assertIsNone(caught); self.assertIs(True, result)
                        self.assertEqual(2, original_history.call_count)
                        self.assertEqual(2, original_composition.call_count)
                    elif mode == "guard":
                        self.assertIs(primary, caught)
                        original_history.assert_not_called(); original_composition.assert_not_called()
                    else:
                        self.assertIsInstance(caught, ValueError)
                        self.assertIn("Current remote IO input differs", str(caught))
                        self.assertEqual(1, original_history.call_count)
                        self.assertEqual(1, original_composition.call_count)


    def test_new743_remote_platform_operand_precedes_sealed_history_with_fresh_public_custody(self):
        # LAST659 exposed a current16609 operand incorrectly sent to a sealed16661
        # inverse. Exercise the actual owning validator once, not any accepted test.
        documents = []
        original_document, original_inverse = successor._document, successor._inverse
        def fresh(actual=ROOT):
            document = original_document(actual)
            documents.append(document)
            return document
        with patch.object(successor, "_document", side_effect=fresh) as current_document, \
                patch.object(successor, "_inverse", wraps=original_inverse) as inverses:
            self.assertTrue(successor.validate_current_sources(ROOT))
        current_document.assert_called_once_with(ROOT)
        self.assertEqual(1, len(documents))
        document = documents[0]
        platform = document["platform_custody_bindings743"][successor.REMOTE]
        historical = document["remote_binding"]
        self.assertEqual((platform["before_sha256"], platform["before_bytes"]),
                         (historical["after_sha256"], historical["after_bytes"]))
        raw = joint._ordinary(ROOT, successor.REMOTE, joint.MAX_SOURCE)[0]
        self.assertEqual((platform["after_sha256"], platform["after_bytes"]), (sha(raw), len(raw)))
        predecessor = original_inverse(raw, platform)
        ancestor = original_inverse(predecessor, historical)
        self.assertNotEqual(raw, predecessor)
        self.assertEqual((historical["after_sha256"], historical["after_bytes"]),
                         (sha(predecessor), len(predecessor)))
        self.assertEqual((historical["before_sha256"], historical["before_bytes"]),
                         (sha(ancestor), len(ancestor)))
        calls = inverses.call_args_list
        platform_calls = [(index, call) for index, call in enumerate(calls)
                          if call.args[1] is platform]
        historical_calls = [(index, call) for index, call in enumerate(calls)
                            if call.args[1] is historical]
        self.assertEqual((1, 1), (len(platform_calls), len(historical_calls)))
        self.assertLess(platform_calls[0][0], historical_calls[0][0])
        self.assertEqual(raw, platform_calls[0][1].args[0])
        self.assertEqual(predecessor, historical_calls[0][1].args[0])
        # Keep both exact endpoint guards: raw is not historical-current; OLD,
        # truncation, suffix, duplication and foreign types are not current RAW.
        with self.assertRaises(ValueError):
            original_inverse(raw, historical)
        for bad in (predecessor, ancestor, raw[:-1], raw + b"\n", raw + raw, b""):
            with self.subTest(operand=type(bad).__name__), self.assertRaises(ValueError):
                original_inverse(bad, platform)
        # Foreign types belong to the public exact-bytes identity boundary.
        for bad in (None, bytearray(raw), raw.decode()):
            with self.subTest(operand=type(bad).__name__), self.assertRaises(ValueError):
                successor.current_source_before_fixture_successor(successor.REMOTE, bad, ROOT)


if __name__ == "__main__":
    unittest.main()
