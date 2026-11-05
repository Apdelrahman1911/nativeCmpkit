# SPDX-License-Identifier: Apache-2.0
"""NEW cases-only Content/AppKit source control; no original test/native replay."""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import camera_ios_ownership_source_projection as camera
import ci_source_recovery740_742 as recovery
import macos_share_key_wait_observation as key_wait
import webview_content_policy_source_projection as content
from ios_popover_anchor_plan import _ordinary_bytes

ROOT = Path(__file__).resolve().parents[2]
CASES = "calf-share/native/tests/appkit_lifecycle/cases.rs"
CONTENT_BEFORE = ("ad544703072bd892274a08b29304f313d1915d8c24840f6d136474ea1e560253", 14440)
CASES_BEFORE = ("9e038b83b4e2e4d3d4718869ec05c9eaa198ce1f3c886a38b97b7c13ff83842b", 20272)
CASES_AFTER = ("2ee076e833b1cdc619a5aa94194d5d23e3b62d2da1a9797ebe37ac377361b790", 24072)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class CalendarAppKitContentBoundary740Controls(unittest.TestCase):
    def test01_exact_cases_only_boundary_preserves_original_pins_and_ordinary_custody(self):
        # The common R5 assembly must bind this source derivative separately from
        # immutable current303/Cookie40 and the original Content/Share manifests.
        source = _ordinary_bytes(ROOT, content.SOURCE_RELATIVE)[0]
        binding = recovery._document(ROOT)["bindings"][content.SOURCE_RELATIVE]
        self.assertEqual(CONTENT_BEFORE, (binding["before_sha256"], binding["before_bytes"]))
        self.assertEqual((sha(source), len(source)), (binding["after_sha256"], binding["after_bytes"]))
        self.assertEqual(5, len(binding["fragments"]))
        previous_source = recovery._inverse(source, binding)
        self.assertEqual(CONTENT_BEFORE, (sha(previous_source), len(previous_source)))

        class OnlyFourTransparentHooks(ast.NodeTransformer):
            def __init__(self):
                self.function = None
                self.sites = []
                self.branches = []

            def visit_FunctionDef(self, node):
                if node.name == "_appkit_key_wait_source":
                    return None
                if node.name == "_current_tooling656_control_source":
                    successor = ast.parse('from tooling_recovery671_source_projection import current_source_before_tooling671\npayload = current_source_before_tooling671(relative, payload)\n').body
                    if (len(node.body) < 5 or
                            ast.dump(ast.Module(body=node.body[3:5], type_ignores=[]), include_attributes=False) !=
                            ast.dump(ast.Module(body=successor, type_ignores=[]), include_attributes=False)):
                        raise AssertionError("Only the exact single strict tooling671 successor is transparent")
                    del node.body[3:5]
                previous = self.function
                self.function = node.name
                result = self.generic_visit(node)
                self.function = previous
                return result

            def visit_Assign(self, node):
                if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and
                        node.targets[0].id == "payload" and isinstance(node.value, ast.Call) and
                        isinstance(node.value.func, ast.Name) and node.value.func.id == "_appkit_key_wait_source"):
                    self.visit_Call(node.value)
                    return None
                return self.generic_visit(node)

            def visit_If(self, node):
                if (self.function == "current_source_before_content_policy" and
                        ast.dump(node.test, include_attributes=False) == ast.dump(ast.parse(
                            'relative == "calf-share/native/tests/appkit_lifecycle/cases.rs"',
                            mode="eval").body, include_attributes=False)):
                    exact = ast.parse('if relative == "calf-share/native/tests/appkit_lifecycle/cases.rs":\n'
                                      '    return source_before_content_policy(relative, payload)\n').body[0]
                    if ast.dump(node, include_attributes=False) != ast.dump(exact, include_attributes=False):
                        raise AssertionError("Only the exact cases-only after/history branch is allowed")
                    self.branches.append(self.function)
                    return None
                return self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == "_appkit_key_wait_source":
                    if (len(node.args) != 2 or len(node.keywords) != 1 or node.keywords[0].arg != "current" or
                            not isinstance(node.keywords[0].value, ast.Constant) or
                            type(node.keywords[0].value.value) is not bool):
                        raise AssertionError("Only one exact binary AppKit source operand and explicit Boolean mode are allowed")
                    if self.function == "validate_current_sources":
                        if (ast.unparse(node.args[0]) != "name" or
                                ast.unparse(node.args[1]) != "_current_tooling656_control_source(name, _ordinary_bytes(root, name)[0])"):
                            raise AssertionError("The unchanged ordinary/tooling656 validator operand must remain exact")
                    elif [ast.unparse(arg) for arg in node.args] != ["relative", "payload"]:
                        raise AssertionError("Only exact relative/payload source-hook operands are allowed")
                    self.sites.append((self.function, node.keywords[0].value.value))
                    return self.visit(node.args[1])
                return self.generic_visit(node)

        transparent = OnlyFourTransparentHooks()
        cleaned = transparent.visit(ast.parse(source))
        self.assertEqual([
            ("source_before_content_policy", False), ("current_source_before_content_policy", True),
            ("peel_content_policy_for_history", False), ("validate_current_sources", True),
        ], transparent.sites)
        self.assertEqual(["current_source_before_content_policy"], transparent.branches)
        self.assertEqual(ast.dump(ast.parse(previous_source), include_attributes=False),
                         ast.dump(cleaned, include_attributes=False))

        self.assertEqual("c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916",
                         sha(_ordinary_bytes(ROOT, content.SPEC_RELATIVE)[0]))
        self.assertEqual("dd5872cb1a7e23beb064dfcad7ef10544e0b547d734498b564dd73ae5ee3a0e6",
                         sha(_ordinary_bytes(ROOT, key_wait.SPEC_RELATIVE)[0]))
        from macos_share_missing_source_projection import SPEC_RELATIVE as share_spec, _document as share_document
        self.assertEqual("79fa2b0394b10026402bef72992385c38684f19b70414606ed1833b40e3178b9",
                         sha(_ordinary_bytes(ROOT, share_spec)[0]))
        document = content._document()
        self.assertEqual(149, len(document["unchanged_inputs"]))
        self.assertEqual(CASES_BEFORE[0], document["unchanged_inputs"][CASES])
        self.assertEqual(CASES_BEFORE[0], share_document()["unchanged_inputs"][CASES])
        self.assertNotIn(CASES, content.BOUND_PATHS)
        row = key_wait._document()["bindings"][CASES]
        self.assertEqual(CASES_BEFORE, (row["before_sha256"], row["before_bytes"]))
        self.assertEqual(CASES_AFTER, (row["after_sha256"], row["after_bytes"]))
        self.assertEqual(2, len(row["fragments"]))
        raw = _ordinary_bytes(ROOT, CASES)[0]
        self.assertEqual(CASES_AFTER, (sha(raw), len(raw)))
        # This existing owning arithmetic executes no restored/native source.
        with patch.object(key_wait, "current_source_before_key_wait", wraps=key_wait.current_source_before_key_wait) as strict, \
                patch.object(camera, "current_source_before_camera_ios_ownership",
                             side_effect=AssertionError("Peeled cases were readmitted as current raw")) as older:
            old = content.current_source_before_content_policy(CASES, raw)
            strict.assert_called_once_with(CASES, raw)
            older.assert_not_called()
        self.assertEqual(CASES_BEFORE, (sha(old), len(old)))
        self.assertEqual(old, content.source_before_content_policy(CASES, raw))
        self.assertEqual(old, content.peel_content_policy_for_history(CASES, raw))
        self.assertIs(old, content._appkit_key_wait_source(CASES, old, current=False))
        unknown = raw + b"\n# NEW unreviewed cases source data\n"
        self.assertIs(unknown, content._appkit_key_wait_source(CASES, unknown, current=False))
        fragment = row["fragments"][0]["after"].encode()
        displaced = raw.replace(fragment, b"", 1) + fragment
        self.assertNotEqual(raw, displaced)
        for bad in (old, raw[:-1], raw + b"\n", displaced, b"", None, bytearray(raw), raw.decode(),
                    b"x" * (content.MAX_SOURCE_BYTES + 1)):
            with self.subTest(kind=type(bad).__name__), patch.object(
                    camera, "current_source_before_camera_ios_ownership",
                    side_effect=AssertionError("Unqualified cases crossed its strict Content ingress")) as older:
                with self.assertRaises(ValueError):
                    content.current_source_before_content_policy(CASES, bad)
                older.assert_not_called()
        for identity in (Path(CASES), None, [], 1):
            with self.subTest(identity=type(identity).__name__), self.assertRaises(ValueError):
                content._appkit_key_wait_source(identity, raw, current=True)
        for mode in (None, 0, 1, "current"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                content._appkit_key_wait_source(CASES, raw, current=mode)
        unlisted = b"unlisted source data is not a current certificate"
        with patch.object(key_wait, "current_source_before_key_wait", side_effect=AssertionError("Unlisted strict admission")), \
                patch.object(key_wait, "peel_key_wait_for_history", side_effect=AssertionError("Unlisted historical broadening")):
            for name in ("unlisted-source", "scripts/ci/test_macos_share_appkit_lifecycle_runner.py"):
                for mode in (False, True):
                    self.assertIs(unlisted, content._appkit_key_wait_source(name, unlisted, current=mode))

        # Exercise only the NEW leaf/manifest boundary, not the accepted complete
        # Calendar/private472 population. Its missing-only validator remains separate.
        with tempfile.TemporaryDirectory(prefix="calendar-appkit-boundary740-") as temporary:
            root = Path(temporary).resolve()
            target = root / CASES
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            self.assertEqual(old, content._appkit_key_wait_source(CASES, _ordinary_bytes(root, CASES)[0], current=True))
            target.unlink()
            with self.assertRaises(FileNotFoundError):
                _ordinary_bytes(root, CASES)
            target.symlink_to(ROOT / CASES)
            with self.assertRaises(ValueError):
                _ordinary_bytes(root, CASES)
            target.unlink()
            backing = target.with_name("cases.backing.rs")
            backing.write_bytes(raw)
            target.hardlink_to(backing)
            with self.assertRaises(ValueError):
                _ordinary_bytes(root, CASES)
            target.unlink(); backing.unlink()
            target.write_bytes(raw + b"\n")
            with self.assertRaises(ValueError):
                content._appkit_key_wait_source(CASES, _ordinary_bytes(root, CASES)[0], current=True)
            target.unlink()
            manifest = root / "key-wait.json"
            sealed = _ordinary_bytes(ROOT, key_wait.SPEC_RELATIVE)[0]
            with patch.object(key_wait, "SPEC_PATH", manifest):
                for bad in (sealed + b"\n", b'{"schema_version":1,"schema_version":1}', b'{}'):
                    manifest.write_bytes(bad)
                    with self.assertRaises(ValueError):
                        content._appkit_key_wait_source(CASES, raw, current=True)
                manifest.unlink(); manifest.symlink_to(ROOT / key_wait.SPEC_RELATIVE)
                with self.assertRaises(ValueError):
                    content._appkit_key_wait_source(CASES, raw, current=True)
                manifest.unlink(); backing = manifest.with_name("key-wait.backing.json")
                backing.write_bytes(sealed); manifest.hardlink_to(backing)
                with self.assertRaises(ValueError):
                    content._appkit_key_wait_source(CASES, raw, current=True)
                manifest.unlink(); backing.unlink()


if __name__ == "__main__":
    unittest.main()
