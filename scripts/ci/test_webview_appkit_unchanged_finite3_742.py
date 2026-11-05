# SPDX-License-Identifier: Apache-2.0
"""NEW finite3 AppKit/WebView primitive; original R7 failure remains preserved."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import macos_share_key_wait_observation as key_wait
import webview_content_policy_source_projection as content
from ios_popover_anchor_plan import _ordinary_bytes

ROOT = Path(__file__).resolve().parents[2]
PATHS = (
    "calf-share/native/tests/appkit_lifecycle/cases.rs",
    "scripts/ci/macos_share_appkit_lifecycle.py",
    "scripts/ci/test_macos_share_missing_only.py",
)


class WebViewAppKitUnchangedFinite3Controls(unittest.TestCase):
    def test_NEW_exact_three_current_history_original_pins_and_fourth_exclusion(self):
        source = _ordinary_bytes(ROOT, content.SOURCE_RELATIVE)[0]
        helper = next(node for node in ast.parse(source).body
                      if isinstance(node, ast.FunctionDef) and node.name == "_appkit_key_wait_source")
        guards = [node.test for node in helper.body
                  if isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                  and isinstance(node.test.left, ast.Name) and node.test.left.id == "relative"]
        self.assertEqual(1, len(guards))
        self.assertEqual(ast.dump(ast.parse("relative not in " + repr(PATHS), mode="eval").body,
                                  include_attributes=False),
                         ast.dump(guards[0], include_attributes=False))
        document = content._document()
        owning = key_wait._document()
        self.assertEqual(149, len(document["unchanged_inputs"]))
        self.assertEqual(4, len(owning["bindings"]))
        for relative in PATHS:
            with self.subTest(relative=relative):
                self.assertNotIn(relative, content.BOUND_PATHS)
                original_pin = document["unchanged_inputs"][relative]
                self.assertEqual(original_pin, owning["bindings"][relative]["before_sha256"])
                raw = _ordinary_bytes(ROOT, relative)[0]
                with patch.object(key_wait, "current_source_before_key_wait",
                                  wraps=key_wait.current_source_before_key_wait) as strict:
                    old = content._appkit_key_wait_source(relative, raw, current=True)
                    strict.assert_called_once_with(relative, raw)
                self.assertEqual(original_pin, hashlib.sha256(old).hexdigest())
                self.assertEqual(owning["bindings"][relative]["before_bytes"], len(old))
                self.assertEqual(old, content._appkit_key_wait_source(relative, raw, current=False))
                self.assertIs(old, content._appkit_key_wait_source(relative, old, current=False))
                unknown = raw + b"\n# NEW unreviewed source DATA\n"
                self.assertIs(unknown, content._appkit_key_wait_source(relative, unknown, current=False))
                for bad in (old, raw[:-1], raw + b"\n", b"", bytearray(raw)):
                    with self.subTest(bad_type=type(bad).__name__), self.assertRaises(ValueError):
                        content._appkit_key_wait_source(relative, bad, current=True)
                mismatch = dict(document, unchanged_inputs=dict(document["unchanged_inputs"]))
                mismatch["unchanged_inputs"][relative] = "0" * 64
                with patch.object(content, "_document", return_value=mismatch), \
                        patch.object(key_wait, "current_source_before_key_wait",
                                     side_effect=AssertionError("A changed original pin was admitted")):
                    with self.assertRaises(ValueError):
                        content._appkit_key_wait_source(relative, raw, current=True)

        fourth = set(owning["bindings"]) - set(PATHS)
        self.assertEqual({"scripts/ci/test_macos_share_appkit_lifecycle_runner.py"}, fourth)
        self.assertTrue(fourth.isdisjoint(document["unchanged_inputs"]))
        unlisted = b"unlisted DATA is not certified"
        with patch.object(key_wait, "current_source_before_key_wait",
                          side_effect=AssertionError("Unlisted current admission")), \
                patch.object(key_wait, "peel_key_wait_for_history",
                             side_effect=AssertionError("Unlisted history admission")):
            for relative in ("unlisted-source", *fourth):
                for mode in (False, True):
                    self.assertIs(unlisted, content._appkit_key_wait_source(relative, unlisted, current=mode))
        for bad_mode in (None, 0, 1, "current"):
            with self.subTest(mode=bad_mode), self.assertRaises(ValueError):
                content._appkit_key_wait_source(PATHS[0], b"", current=bad_mode)
        for bad_identity in (None, 1, Path(PATHS[0])):
            with self.subTest(identity=type(bad_identity).__name__), self.assertRaises(ValueError):
                content._appkit_key_wait_source(bad_identity, b"", current=True)


if __name__ == "__main__":
    unittest.main()
