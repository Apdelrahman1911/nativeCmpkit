# SPDX-License-Identifier: Apache-2.0
"""NEW failed-CI history controls; no compilation/UIKit/native execution."""
import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import ios_popover_anchor_source_projection as anchor
import ios_worker_completion_source_projection as completion
import ios_sheet_repeat_source_projection as repeat
import ios_modal_worker_source_projection as worker

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts/ci/fixtures/ios-popover-worker-history-composition.json"
SPEC_SHA = "33ed809dc04f17f46d9bbdebe50381583b4be51f9bddfcda0efa54c067ec6f29"
SHARED = ("scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py", ".github/workflows/gradle.yml")


class PopoverWorkerHistoryCompositionControls(unittest.TestCase):
    def test_exact_three_fragments_change_only_the_unbound_offline_reader(self):
        raw = SPEC.read_bytes()
        self.assertEqual(SPEC_SHA, hashlib.sha256(raw).hexdigest())
        spec = json.loads(raw)
        self.assertEqual(1, len(spec["bindings"]))
        relative, binding = next(iter(spec["bindings"].items()))
        self.assertEqual("scripts/ci/ios_worker_completion_source_projection.py", relative)
        self.assertEqual(3, len(binding["fragments"]))
        self.assertNotIn(relative, anchor._bindings())
        self.assertNotIn(relative, completion._bindings())
        current = (ROOT / relative).read_bytes()
        self.assertEqual(binding["after_sha256"], hashlib.sha256(current).hexdigest())
        previous = current
        for row in reversed(binding["fragments"]):
            before, after = row["before"].encode(), row["after"].encode()
            self.assertEqual(row["before_fragment_sha256"], hashlib.sha256(before).hexdigest())
            self.assertEqual(row["after_fragment_sha256"], hashlib.sha256(after).hexdigest())
            self.assertEqual(1, previous.count(after))
            previous = previous.replace(after, before, 1)
        self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
        forward = previous
        for row in binding["fragments"]:
            self.assertEqual(1, forward.count(row["before"].encode()))
            forward = forward.replace(row["before"].encode(), row["after"].encode(), 1)
        self.assertEqual(current, forward)

    def test_all_three_later_postimages_reach_unchanged_complete_worker_and_repeat_stages(self):
        for relative in SHARED:
            live = (ROOT / relative).read_bytes()
            anchor_stage = anchor.current_source_before_popover_anchor(relative, live)
            self.assertEqual(completion._bindings()[relative]["after_sha256"], hashlib.sha256(anchor_stage).hexdigest())
            previous = completion.current_source_before_worker_completion(relative, live)
            self.assertEqual(completion._bindings()[relative]["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, completion.source_before_worker_completion(relative, live))
            repeated = repeat.current_source_before_sheet_repeat(relative, previous)
            self.assertEqual(repeat._bindings()[relative]["before_sha256"], hashlib.sha256(repeated).hexdigest())
            self.assertEqual(worker._bindings()[relative]["before_sha256"], hashlib.sha256(worker.current_source_before_modal_worker(relative, live)).hexdigest())

    def test_ancestor_idempotence_is_not_latest_popover_current_certification(self):
        for relative in SHARED:
            live = (ROOT / relative).read_bytes()
            stage = anchor.current_source_before_popover_anchor(relative, live)
            self.assertEqual(completion.current_source_before_worker_completion(relative, live),
                             completion.current_source_before_worker_completion(relative, stage))
            with self.assertRaises(ValueError):
                anchor.current_source_before_popover_anchor(relative, stage)
            old = completion.current_source_before_worker_completion(relative, live)
            self.assertIs(old, completion.source_before_worker_completion(relative, old))
            with self.assertRaises(ValueError):
                completion.current_source_before_worker_completion(relative, old)

    def test_partial_foreign_and_changed_latest_bytes_never_reach_repeat_admission(self):
        for relative in SHARED:
            live = (ROOT / relative).read_bytes()
            for bad in (live + b"\n", live[:-1], live.replace(b"\n", b"\r\n"), b"", None,
                        bytearray(live), (ROOT / SHARED[(SHARED.index(relative) + 1) % len(SHARED)]).read_bytes()):
                with patch.object(repeat, "current_source_before_sheet_repeat",
                                  side_effect=AssertionError("Invalid bytes crossed ancestor admission")) as reader:
                    with self.assertRaises(ValueError):
                        stage = completion.current_source_before_worker_completion(relative, bad)
                        repeat.current_source_before_sheet_repeat(relative, stage)
                    reader.assert_not_called()
            with self.assertRaises(ValueError):
                completion.current_source_before_worker_completion(None, live)

    def test_old_manifest_pins_native_inputs_and_nonrecursive_composition_stay_intact(self):
        self.assertEqual("145287111a3c12354efa3b30c2df93ee3a8120f3a42a37f2193a02d17065544f", hashlib.sha256(anchor.SPEC_PATH.read_bytes()).hexdigest())
        self.assertEqual("5e08c7a05137b117d080b74f698a13a0fe6cd25c439eab40750de0e260faef60", hashlib.sha256(completion.SPEC_PATH.read_bytes()).hexdigest())
        self.assertEqual("a821c1b93c44e71afa2142b4ba10d84e0117bbf017f790130a38c565890c971a", hashlib.sha256(repeat.SPEC_PATH.read_bytes()).hexdigest())
        self.assertEqual("8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48", hashlib.sha256(worker.SPEC_PATH.read_bytes()).hexdigest())
        source = (ROOT / "scripts/ci/ios_worker_completion_source_projection.py").read_text()
        tree = ast.parse(source)
        for name in ("source_before_worker_completion", "current_source_before_worker_completion"):
            node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
            body = ast.get_source_segment(source, node)
            self.assertEqual(1, body.count("anchor_history.peel_current_popover_for_older_history(relative, payload)"))
            self.assertLess(body.index("anchor_history.peel_current_popover_for_older_history"), body.index("binding = _bindings().get(relative)"))
            self.assertNotIn("anchor_history.current_source_before_popover_anchor", body)
        for path in ("scripts/ci/library_tests.py", "scripts/ci/ios_ui_application.py", "scripts/ci/native_ui_input.py"):
            live = (ROOT / path).read_text()
            self.assertNotIn("import ios_worker_completion_source_projection", live)
            self.assertNotIn("import ios_popover_anchor_source_projection", live)


if __name__ == "__main__":
    unittest.main()
