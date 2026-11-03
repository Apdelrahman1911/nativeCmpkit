# SPDX-License-Identifier: Apache-2.0
"""NEW owning-stage controls for CI455; ZERO compiler/Apple/native tests."""
import ast
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import ios_sheet_repeat_source_projection as repeat
import ios_worker_completion_source_projection as completion
import ios_modal_worker_source_projection as worker

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = "scripts/ci/test_ios_sheet_cancellation_repeat.py"


def qualify_current_repeat(relative, payload):
    stage = completion.current_source_before_worker_completion(relative, payload)
    return repeat.current_source_before_sheet_repeat(relative, stage)


class SheetRepeatFixtureRecoveryControls(unittest.TestCase):
    def test_all_three_exact_repeat_postimages_are_admitted_at_the_current_owning_stage_first(self):
        bindings = repeat._bindings()
        self.assertEqual(3, len(bindings))
        self.assertEqual(7, sum(len(binding["fragments"]) for binding in bindings.values()))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            stage = completion.current_source_before_worker_completion(relative, current)
            self.assertNotEqual(current, stage)
            self.assertEqual(binding["after_sha256"], hashlib.sha256(stage).hexdigest())
            with self.assertRaises(ValueError): repeat.current_source_before_sheet_repeat(relative, current)
            previous = qualify_current_repeat(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(worker.source_before_modal_worker(relative, previous),
                             worker.current_source_before_modal_worker(relative, current))
        self.assertEqual("a821c1b93c44e71afa2142b4ba10d84e0117bbf017f790130a38c565890c971a", repeat.SPEC_SHA256)
        self.assertEqual("5e08c7a05137b117d080b74f698a13a0fe6cd25c439eab40750de0e260faef60", completion.SPEC_SHA256)

    def test_invalid_current_images_cannot_reach_the_older_repeat_reader(self):
        for relative in repeat._bindings():
            current = (ROOT / relative).read_bytes()
            stage = completion.current_source_before_worker_completion(relative, current)
            previous = repeat.current_source_before_sheet_repeat(relative, stage)
            for invalid in (stage, previous, current + b"\n", current[:-1],
                            current.replace(b"\n", b"\r\n"), b"", None, bytearray(current)):
                with patch.object(repeat, "current_source_before_sheet_repeat",
                                  side_effect=AssertionError("Historical reader crossed invalid current custody")) as reader:
                    with self.assertRaises(ValueError): qualify_current_repeat(relative, invalid)
                    reader.assert_not_called()
            real_reader = repeat.current_source_before_sheet_repeat
            with patch.object(repeat, "current_source_before_sheet_repeat", wraps=real_reader) as reader:
                self.assertEqual(previous, qualify_current_repeat(relative, current))
                reader.assert_called_once_with(relative, stage)

    def test_repaired_fixture_uses_stage_bytes_for_the_prior_inverse_and_its_negative_controls(self):
        source = (ROOT / FIXTURE).read_text()
        nodes = [node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef) and
                 node.name == "test_seven_exact_additive_fragments_preserve_every_old_worker_pin_and_refuse_mutation"]
        self.assertEqual(1, len(nodes))
        body = ast.get_source_segment(source, nodes[0])
        self.assertIn("stage = completion_history.current_source_before_worker_completion(relative, current)", body)
        self.assertIn("previous = history.current_source_before_sheet_repeat(relative, stage)", body)
        self.assertIn("self.assertEqual(stage, forward)", body)
        self.assertNotIn("self.assertEqual(current, forward)", body)
        self.assertIn('stage.replace(b"\\n", b"\\r\\n")', body)
        self.assertIn("history.current_source_before_sheet_repeat(relative, changed)", body)
        self.assertIn("completion_history.current_source_before_worker_completion(relative, changed)", body)
        self.assertEqual(1, source.count("import ios_worker_completion_source_projection as completion_history"))


if __name__ == "__main__":
    unittest.main()
