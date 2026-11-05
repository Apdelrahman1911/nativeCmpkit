# SPDX-License-Identifier: Apache-2.0
"""NEW620 current source/data controls; never native, consumer or reuse."""
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import macos_share_ci668_composition as latest

ROOT = Path(__file__).resolve().parents[2]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class RelatedCurrentIngress620Controls(unittest.TestCase):
    """NEW exact source/data qualification only, never native or reuse."""

    def test47_exact658_roundtrips_before_original711_then707(self):
        doc = latest._document(ROOT)
        row = latest._failure658_binding(doc)
        raw = (ROOT / latest.OFFLINE).read_bytes()
        old = latest._failure658_to711(raw, doc)
        self.assertEqual((59762, latest.FAILURE711_CURRENT_SHA256), (len(old), sha(old)))
        forward = old
        for part in row["fragments"]:
            self.assertEqual(1, forward.count(part["before"].encode()))
            forward = forward.replace(part["before"].encode(), part["after"].encode(), 1)
        self.assertEqual(raw, forward)
        order = []
        def mark(tag, function):
            def observed(*args):
                order.append(tag)
                return function(*args)
            return observed
        with patch.object(latest, "_failure658_to711", side_effect=mark("658", latest._failure658_to711)), \
             patch.object(latest, "_failure711_to_budget707", side_effect=mark("711", latest._failure711_to_budget707)), \
             patch.object(latest, "_budget707_in_named_domain", side_effect=mark("707", latest._budget707_in_named_domain)):
            latest.current_source_in_view(latest.OFFLINE, raw, latest.PRODUCER_VIEW, ROOT)
        self.assertEqual(["658", "711", "707"], order)

    def test48_old711_tailed_partial_and_rehashed658_mutants_refuse(self):
        doc = latest._document(ROOT)
        raw = (ROOT / latest.OFFLINE).read_bytes()
        old = latest._failure658_to711(raw, doc)
        for image in (old, raw[:-1], raw + b"\n# foreign658 tail\n", raw + raw):
            with self.assertRaises(ValueError):
                latest.source_before_failure_parent658(latest.OFFLINE, image, ROOT)
            for view in (latest.CI_VIEW, latest.PRODUCER_VIEW):
                with self.assertRaises(ValueError):
                    latest.current_source_in_view(latest.OFFLINE, image, view, ROOT)
                self.assertEqual(image, latest.peel_for_history(latest.OFFLINE, image, view, ROOT))
            self.assertEqual(image, latest.peel_budget707_for_history(latest.OFFLINE, image, ROOT))
        bad = copy.deepcopy(doc)
        part = bad["failure658_bindings"][latest.OFFLINE]["fragments"][0]
        part["after"] += "# unknown hook\n"
        part["after_fragment_sha256"] = sha(part["after"].encode())
        with self.assertRaises(ValueError):
            latest._failure658_binding(bad)

    def test49_separate620_controls_roundtrip_above_immutable718_and711(self):
        doc = latest._document(ROOT)
        rows = latest._current_context620_bindings(doc)
        self.assertEqual({latest.NEW_CONTROL, latest.PRODUCER_CONTROL, latest.ANDROID_CONTROL, latest.FAILURE711_CONTROL}, set(rows))
        for relative, row in rows.items():
            raw = (ROOT / relative).read_bytes()
            old = latest.source_before_current_context620(relative, raw, ROOT)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(old), len(old)))
            forward = old
            for part in row["fragments"]:
                self.assertEqual(1, forward.count(part["before"].encode()))
                forward = forward.replace(part["before"].encode(), part["after"].encode(), 1)
            self.assertEqual(raw, forward)
        self.assertEqual("c82a70f4890b4a7d2bddfa60ef2273dfb4a41c9005871234282363e745fed14f", rows[latest.FAILURE711_CONTROL]["before_sha256"])
        self.assertEqual(latest.ANDROID_TRANSITION_ENDPOINT["sha256"], sha((ROOT / latest.ANDROID_SPEC).read_bytes()))

    def test50_unknown620_schema_mutants_and_old_control_endpoints_refuse(self):
        doc = latest._document(ROOT)
        for relative, row in latest._current_context620_bindings(doc).items():
            raw = (ROOT / relative).read_bytes()
            old = latest._current_context620_before(relative, raw, doc)
            with self.assertRaises(ValueError):
                latest.source_before_current_context620(relative, old, ROOT)
            bad = copy.deepcopy(doc)
            bad["raw_inputs"][relative] = {"sha256": row["before_sha256"], "bytes": row["before_bytes"]}
            with self.assertRaises(ValueError):
                latest._shape(bad, ROOT)
            bad = copy.deepcopy(doc)
            bad["current_context620_bindings"][relative]["before_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                latest._current_context620_bindings(bad)
        bad = copy.deepcopy(doc)
        bad["foreign620_key"] = False
        with self.assertRaises(ValueError):
            latest._shape(bad, ROOT)

    def test51_narrow658_and620_read_one_fresh_manifest_without_named_traversal(self):
        for relative, reader in ((latest.OFFLINE, latest.source_before_failure_parent658), (latest.FAILURE711_CONTROL, latest.source_before_current_context620)):
            raw = (ROOT / relative).read_bytes()
            with patch.object(latest, "_document", side_effect=AssertionError("no traversal")), \
                 patch.object(latest, "_view", side_effect=AssertionError("no named view")), \
                 patch.object(latest, "_sealed_predecessor_hashes", side_effect=AssertionError("no ancestors")), \
                 patch.object(latest, "_ordinary", wraps=latest._ordinary) as reads:
                reader(relative, raw, ROOT)
            self.assertEqual([(ROOT, latest.SPEC, latest.MAX_SPEC)], [call.args for call in reads.call_args_list])

    def test52_new_sources_and_nonowning_domains_never_peel_into_diagnostics(self):
        raw = (ROOT / latest.OFFLINE).read_bytes()
        for view in (latest.COOKIE_VIEW, latest.SHARE_VIEW):
            with patch.object(latest, "_failure658_to711", side_effect=AssertionError("not this domain")):
                self.assertEqual(raw, latest.current_source_in_view(latest.OFFLINE, raw, view, ROOT))
        doc = latest._document(ROOT)
        for relative in latest.RELATED620_ADDITION_ENDPOINTS:
            raw = (ROOT / relative).read_bytes()
            for view in latest.VIEWS:
                self.assertNotIn(relative, doc["predecessor_inputs"][view])
                self.assertNotIn(relative, doc["views"][view])
                self.assertEqual(raw, latest.peel_for_history(relative, raw, view, ROOT))
            with patch.object(latest, "_ordinary", side_effect=AssertionError("new source is not a transition")):
                self.assertEqual(raw, latest.peel_budget707_for_history(relative, raw, ROOT))
        self.assertNotIn("scripts/ci/android_permission_compatibility_plan.py", doc["raw_inputs"])


if __name__ == "__main__":
    unittest.main()
