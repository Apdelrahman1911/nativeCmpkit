# SPDX-License-Identifier: Apache-2.0
"""NEW Android successor source/custody controls, not the accepted Android23/8.

Only current source guards and stdlib are imported. Literal projected bytes are
compared, never imported/executed. Source models do not certify Android/native,
compiler, consumer, resource lifecycle, producer reuse, security or publication.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import macos_share_ci668_composition as latest

ROOT = Path(__file__).resolve().parents[2]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(document):
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


class AndroidPermissionLifecycleFixtureAdmissionTests(unittest.TestCase):
    def test01_original_Android18_six36_and_accepted_control_sources_remain_exact(self):
        document = latest._android_transition(ROOT)
        self.assertEqual("e2260f56286ee946bed458e76e2d29126d80c6f6ce3fb1b04ab19b2da02562e6", document["original_recipe_sha256"])
        self.assertEqual("39c02ea6930a7024a1dd83bda1a6dc6236894937ea75f7a11c2702157a8b81c8", document["original_final_map_sha256"])
        self.assertEqual((6, 36), (len(document["original_bindings"]),
                         sum(len(row["fragments"]) for row in document["original_bindings"].values())))
        self.assertEqual(13, len(document["source_inputs"]))
        for relative, endpoint in document["source_inputs"].items():
            raw = (ROOT / relative).read_bytes()
            self.assertEqual((endpoint["sha256"], endpoint["bytes"]), (sha(raw), len(raw)))
        self.assertEqual("797a60036440024d61bd73c538f188966934b0f8351df6d23e611bebe94f2c6b",
                         sha((ROOT / "scripts/ci/test_android_permission_lifecycle_source.py").read_bytes()))
        # This is a source-hash comparison, not a fresh23/FIRST8 execution.

    def test02_actual_current299_and_immutable_four_named_domains_are_distinct(self):
        document = latest._document(ROOT)
        hashes = latest.current_input_hashes(ROOT)
        self.assertEqual((301, 303), (len(document["raw_inputs"]), len(hashes)))
        self.assertEqual(set(hashes), latest.fixture_inputs(ROOT))
        self.assertTrue(all(sha((ROOT / name).read_bytes()) == digest for name, digest in hashes.items()))
        self.assertEqual({"final_ci175": 175, "producer676_raw190": 190, "cookie609_raw40": 40, "share607": 36},
                         {view: len(latest.predecessor_input_hashes(view, ROOT)) for view in latest.VIEWS})
        self.assertEqual("6fdc0947617c41b199f13e63b13056de6c76bb215698e259109c324f219c2127", hashes[latest.LIBRARY])
        self.assertEqual("a1ea0950a96472e6c602e3a776f74ce519cb8bdadf78920512a1ee6649961d5b", hashes[latest.WORKFLOW])
        self.assertEqual("038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299",
                         latest.predecessor_input_hashes(latest.SHARE_VIEW, ROOT)[latest.LIBRARY])
        self.assertEqual(latest.CI_SPEC_SHA256, hashes[latest.CI_SPEC])
        self.assertEqual(latest.PRODUCER_SPEC_SHA256, hashes[latest.PRODUCER_SPEC])

    def test03_new_Android_and_current_context_rows_roundtrip_before_unchanged_ancestors(self):
        android = latest._android_transition(ROOT)
        rows = android["original_bindings"] | android["current_context_bindings"]
        self.assertEqual(latest.ANDROID_BOUND_PATHS, set(rows))
        for relative, row in rows.items():
            raw = (ROOT / relative).read_bytes()
            before = latest.source_before_android_lifecycle(relative, raw, ROOT)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(before), len(before)))
            forward = before
            for fragment in row["fragments"]:
                old, new = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(old))
                forward = forward.replace(old, new, 1)
            context620 = latest._current_context620_bindings(latest._document(ROOT)).get(relative)
            if context620 is not None:
                for fragment in context620["fragments"]:
                    self.assertEqual(1, forward.count(fragment["before"].encode()))
                    forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(raw, forward)
            if relative in latest.ANDROID_GENERIC_EXCLUSIONS:
                self.assertEqual(raw, latest.peel_android_lifecycle_for_history(relative, raw, ROOT))
            else:
                self.assertEqual(before, latest.peel_android_lifecycle_for_history(relative, raw, ROOT))
            self.assertEqual(before, latest.peel_android_lifecycle_for_history(relative, before, ROOT))

    def test04_raw_current_refuses_old_partial_tailed_and_unknown_before_named_view(self):
        document = latest._document(ROOT)
        android = latest._android_transition(ROOT)
        rows = android["original_bindings"] | android["current_context_bindings"]
        for relative, row in rows.items():
            raw = (ROOT / relative).read_bytes()
            old = latest.source_before_android_lifecycle(relative, raw, ROOT)
            fragment = row["fragments"][0]
            self.assertEqual(1, old.count(fragment["before"].encode()))
            partial = old.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            bad = [old, raw[:-1], raw + b"\n# unqualified Android tail\n", b"unknown source bytes"]
            if partial != raw:
                bad.append(partial)
            for payload in bad:
                with patch.object(latest, "_document", return_value=document), \
                     patch.object(latest, "_view", side_effect=AssertionError("refusal must precede inverse")):
                    with self.assertRaisesRegex(ValueError, "old or unknown image"):
                        latest.current_source_in_view(relative, payload, latest.CI_VIEW, ROOT)
                with self.assertRaises(ValueError):
                    latest.source_before_android_lifecycle(relative, payload, ROOT)

    def test05_generic_history_excludes_new_controls_sources_and_init_even_when_named_comparison_exists(self):
        document = latest._document(ROOT)
        exclusions = latest.ANDROID_GENERIC_EXCLUSIONS | {latest.CALLBACK_INIT, latest.OWNING_COOKIE_CONTROL}
        for relative in exclusions:
            raw = (ROOT / relative).read_bytes()
            for view in latest.VIEWS:
                self.assertEqual(raw, latest.peel_for_history(relative, raw, view, ROOT))
                self.assertNotIn(relative, document["views"][view]) if relative in latest.ANDROID_ADDED_INPUTS else None
        control = latest.NEW_COOKIE_CONTROL
        raw = (ROOT / control).read_bytes()
        named = latest.current_source_in_view(control, raw, latest.COOKIE_VIEW, ROOT)
        self.assertNotEqual(raw, named)  # Explicit source comparison is not generic history.
        self.assertEqual(raw, latest.peel_for_history(control, raw, latest.COOKIE_VIEW, ROOT))
        for relative in (latest.LIBRARY, latest.WORKFLOW):
            raw = (ROOT / relative).read_bytes()
            for view in latest.VIEWS:
                if relative in document["predecessor_inputs"][view]:
                    expected = latest.current_source_in_view(relative, raw, view, ROOT)
                    self.assertEqual(expected, latest.peel_for_history(relative, raw, view, ROOT))
                    old = latest.source_before_android_lifecycle(relative, raw, ROOT)
                    self.assertEqual(old, latest.peel_for_history(relative, old, view, ROOT))

    def test06_narrow_Android_then_unchanged711_707_reads_only_explicit_repository_data(self):
        document = latest._document(ROOT)
        for relative in (latest.WORKFLOW, latest.LIBRARY, latest.OFFLINE):
            raw = (ROOT / relative).read_bytes()
            with patch.object(latest, "_document", side_effect=AssertionError("no whole named view")), \
                 patch.object(latest, "_sealed_predecessor_hashes", side_effect=AssertionError("no old manifests")), \
                 patch.object(latest, "_view", side_effect=AssertionError("no named traversal")), \
                 patch.object(latest, "_ordinary", wraps=latest._ordinary) as read:
                first = latest.peel_android_lifecycle_for_history(relative, raw, ROOT)
                final = latest.peel_budget707_for_history(relative, first, ROOT)
            expected_reads = []
            if relative in latest.ANDROID_BOUND_PATHS:
                expected_reads.append((ROOT, latest.ANDROID_SPEC, latest.MAX_SPEC))
            if relative in latest.BUDGET707_FRAGMENT_COUNTS:
                expected_reads.append((ROOT, latest.SPEC, latest.MAX_SPEC))
            self.assertEqual(expected_reads, [call.args for call in read.call_args_list])
            if relative in latest.BUDGET707_FRAGMENT_COUNTS:
                row = document["derivative_bindings"][relative]
                self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(final), len(final)))
            else:
                self.assertEqual("038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299", sha(final))
        for relative in latest.ANDROID_ADDED_INPUTS:
            raw = (ROOT / relative).read_bytes()
            with patch.object(latest, "_ordinary", side_effect=AssertionError("new source is not a historic layer")):
                self.assertEqual(raw, latest.peel_android_lifecycle_for_history(relative, raw, ROOT))

    def test07_joint_metadata_reference_keeps_cap_and_immutable_row_pins(self):
        document = latest._document(ROOT)
        self.assertEqual({"path": latest.ANDROID_SPEC, **latest.ANDROID_TRANSITION_ENDPOINT},
                         document["android_lifecycle_transition"])
        self.assertLessEqual(len((ROOT / latest.SPEC).read_bytes()), 512 * 1024)
        self.assertEqual(512 * 1024, latest.MAX_SPEC)
        self.assertEqual(13, len(document["derivative_bindings"]))
        self.assertEqual(39, sum(len(document["derivative_bindings"][name]["fragments"])
                               for name in latest.HISTORICAL_DERIVATIVE_FRAGMENT_COUNTS))
        for relative, digest in latest.BUDGET707_BINDING_SHA256.items():
            self.assertEqual(digest, sha(canonical(document["derivative_bindings"][relative])))
        self.assertEqual(latest.FAILURE711_BINDING_SHA256,
                         sha(canonical(document["failure711_bindings"][latest.OFFLINE])))
        self.assertEqual(latest.FAILURE711_CURRENT_SHA256, document["failure658_bindings"][latest.OFFLINE]["before_sha256"])
        self.assertEqual(latest.FAILURE658_CURRENT_SHA256, document["raw_inputs"][latest.OFFLINE]["sha256"])
        literal = (json.dumps(document["named_cookie609_manifest"], indent=2, sort_keys=True) + "\n").encode()
        self.assertEqual(latest.COOKIE609_SPEC_SHA256, sha(literal))
        self.assertEqual({latest.CI_VIEW: 7, latest.COOKIE_VIEW: 4, latest.SHARE_VIEW: 3, latest.PRODUCER_VIEW: 8},
                         {view: len(rows) for view, rows in document["views"].items()})
        bad = copy.deepcopy(document)
        bad["raw_inputs"][latest.LIBRARY] = {"sha256": "038ffa83f883f24396b35103edafa47a9b4a13fe4df6faf88175e56768819299", "bytes": 409466}
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)

    def test08_path_cache_never_caches_leaf_or_raw_payload_after_owned_model_warmup(self):
        inputs = latest.fixture_inputs(ROOT)
        with tempfile.TemporaryDirectory(prefix="android-source-custody-model-") as folder:
            root = Path(folder).resolve()
            for relative in inputs:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            library = (root / latest.LIBRARY).read_bytes()
            first = latest.current_source_in_view(latest.LIBRARY, library, latest.CI_VIEW, root)
            self.assertEqual("ddd7b38615bef7ec99bfefddb625bf0816d9c90c297604d7baaea898a6e90aa6", sha(first))
            leaf = root / latest.ANDROID_SPEC
            original = leaf.read_bytes()
            leaf.write_bytes(original + b"\n")
            with self.assertRaisesRegex(ValueError, "separately-sealed-Android18-transition"):
                latest.current_source_in_view(latest.LIBRARY, library, latest.CI_VIEW, root)
            leaf.write_bytes(original)
            changed = root / latest.LIBRARY
            changed.write_bytes(library + b"\n")
            with self.assertRaises(ValueError):
                latest.validate_current_sources(root)

    def test09_real_Cookie_library_and_External328_raw_boundaries_precede_old_current_pins(self):
        from android_external328_source_projection import current_source_for_history
        raw = (ROOT / latest.LIBRARY).read_bytes()
        old = latest.source_before_android_lifecycle(latest.LIBRARY, raw, ROOT)
        row = latest._android_transition(ROOT)["original_bindings"][latest.LIBRARY]
        fragment = row["fragments"][0]
        self.assertEqual(1, old.count(fragment["before"].encode()))
        partial = old.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
        self.assertNotEqual(partial, raw)
        for refused in (old, partial, raw[:-1], raw + b"\n# unqualified outer Android tail\n"):
            with self.assertRaises(ValueError):
                current_source_for_history(latest.LIBRARY, refused)
        # The changed memo714 test10 owns the real positive-path output once;
        # NEW refusal coverage here does not replay that accepted happy path.
        cookie_source = (ROOT / latest.COOKIE_OWNER).read_text()
        cookie = {node.name: node for node in ast.parse(cookie_source).body if isinstance(node, ast.FunctionDef)}
        current = cookie["current_source_before_cookie_outer"]
        calls = [node for node in ast.walk(current) if isinstance(node, ast.Call)]
        transition = next(node.lineno for node in calls if ast.unparse(node.func) == "source_before_android_lifecycle")
        old_document = next(node.lineno for node in calls if ast.unparse(node.func) == "_document")
        self.assertLess(transition, old_document)
        self.assertNotIn("macos_share_ci668_composition", ast.unparse(cookie["validate_current_sources"]))
        self.assertNotIn("ANDROID_SPEC", ast.unparse(cookie["_document"]))
        bridge_source = (ROOT / latest.ANDROID_BRIDGE).read_text()
        functions = {node.name: node for node in ast.parse(bridge_source).body if isinstance(node, ast.FunctionDef)}
        bridge = functions["current_source_for_history"]
        calls = [node for node in ast.walk(bridge) if isinstance(node, ast.Call)]
        first_android = next(node.lineno for node in calls if ast.unparse(node.func) == "source_before_android_lifecycle")
        old_geometry = next(node.lineno for node in calls if ast.unparse(node.func) == "current_source_before_owned_geometry")
        self.assertLess(first_android, old_geometry)
        decorators = [node.name for node in ast.parse((ROOT / latest.OWNER).read_text()).body
                      if isinstance(node, ast.FunctionDef) and node.decorator_list]
        self.assertEqual(["_cached_source_path_parts", "_cached_json_tree"], decorators)
        memo = (ROOT / latest.ANDROID_MEMO).read_text()
        self.assertIn("412990", memo)
        self.assertIn("5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2", memo)
