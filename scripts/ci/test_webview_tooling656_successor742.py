# SPDX-License-Identifier: Apache-2.0
"""NEW exact tooling successor primitive; no accepted/native population replay."""
from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import ci_source_recovery740_742 as recovery
import tooling_recovery671_source_projection as tooling
import webview_content_policy_source_projection as content
from ios_popover_anchor_plan import _ordinary_bytes

ROOT = Path(__file__).resolve().parents[2]
TARGET = "scripts/ci/test_apple_image_launcher_source_projection.py"
CASES = "scripts/ci/test_calendar_appkit_content_boundary740.py"
COMMON = "scripts/ci/test_cookie_common_jdk_content_boundary740.py"
STRICT_LINES = '    from tooling_recovery671_source_projection import current_source_before_tooling671\n    payload = current_source_before_tooling671(relative, payload)\n'
CASES_BEFORE = '                if node.name == "_appkit_key_wait_source":\n                    return None\n                previous = self.function\n'
CASES_AFTER = '                if node.name == "_appkit_key_wait_source":\n                    return None\n                if node.name == "_current_tooling656_control_source":\n                    successor = ast.parse(\'from tooling_recovery671_source_projection import current_source_before_tooling671\\npayload = current_source_before_tooling671(relative, payload)\\n\').body\n                    if (len(node.body) < 5 or\n                            ast.dump(ast.Module(body=node.body[3:5], type_ignores=[]), include_attributes=False) !=\n                            ast.dump(ast.Module(body=successor, type_ignores=[]), include_attributes=False)):\n                        raise AssertionError("Only the exact single strict tooling671 successor is transparent")\n                    del node.body[3:5]\n                previous = self.function\n'
COUNT_BEFORE = '        self.assertEqual(38, len(recovery.MODIFIED))\n        self.assertEqual(51, len(recovery.dependency_inputs()))\n'
COUNT_AFTER = '        self.assertEqual(38, len(recovery.MODIFIED - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(51, len(recovery.dependency_inputs() - recovery.FIXTURE_SUCCESSORS742 - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(41, len(recovery.MODIFIED - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(54, len(recovery.dependency_inputs() - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(42, len(recovery.MODIFIED - {"scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(55, len(recovery.dependency_inputs() - {"scripts/ci/android_camera_callback_native_focus.py"}))\n        self.assertEqual(43, len(recovery.MODIFIED))\n        self.assertEqual(56, len(recovery.dependency_inputs()))\n'


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


class WebViewTooling656Successor742Controls(unittest.TestCase):
    def test_NEW_exact_latest_tooling671_chain_restores_original656_and_preserves_appkit_history(self):
        # These two source derivatives leave all accepted AppKit/runtime bodies
        # byte-exact; the modified cases method is still separately affected.
        source = _ordinary_bytes(ROOT, content.SOURCE_RELATIVE)[0]
        self.assertEqual(1, source.count(STRICT_LINES.encode()))
        self.assertEqual(("8f55163ea129ee17bb37f529b82184bb6b6be61b811262f13d1f74ac0eb6f541", 16161),
                         (sha(source.replace(STRICT_LINES.encode(), b"", 1)),
                          len(source) - len(STRICT_LINES.encode())))
        old_tree = ast.parse(source.replace(STRICT_LINES.encode(), b"", 1))
        new_tree = ast.parse(source)
        previous = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == "_current_tooling656_control_source")
        current = copy.deepcopy(next(n for n in new_tree.body if isinstance(n, ast.FunctionDef)
                                     and n.name == previous.name))
        expected = ast.parse(STRICT_LINES.lstrip().replace("\n    payload", "\npayload"))
        self.assertEqual(ast.dump(expected, include_attributes=False),
                         ast.dump(ast.Module(body=current.body[3:5], type_ignores=[]), include_attributes=False))
        del current.body[3:5]
        self.assertEqual(ast.dump(previous, include_attributes=False),
                         ast.dump(current, include_attributes=False))
        case_source = _ordinary_bytes(ROOT, CASES)[0]
        self.assertEqual(1, case_source.count(CASES_AFTER.encode()))
        self.assertEqual("d6f9e693348443c5ab8d33cd9b5dfb1541d1aaf1dda1c5ef51fbb7a099d7ceec",
                         sha(case_source.replace(CASES_AFTER.encode(), CASES_BEFORE.encode(), 1)))

        # Independently check the common comparator's new DATA-only inverse,
        # without executing its original failed/modified important method.
        common_source = _ordinary_bytes(ROOT, COMMON)[0]
        # Selectively restore only the new domain-count comparison DATA
        # before checking the already-declared original R5 source mask.
        self.assertEqual(1, common_source.count(COUNT_AFTER.encode()))
        common_source = common_source.replace(COUNT_AFTER.encode(), COUNT_BEFORE.encode(), 1)
        common_text = common_source.decode()
        begin = '        # R5 is immutable source DATA; exact later deltas are not its old pin.\n'
        end = '        self.assertEqual(CONTENT_R5, (sha(r5), len(r5)))\n'
        self.assertEqual(1, common_text.count(begin))
        left = common_text.index(begin)
        right = common_text.index(end, left)
        added = common_text[left:right]
        added_tree = ast.parse("\n".join(line[8:] for line in added.splitlines()) + "\n")
        statements = added_tree.body
        self.assertEqual(2, len(statements))
        self.assertIsInstance(statements[0], ast.Assign)
        self.assertEqual("historical_deltas", statements[0].targets[0].id)
        pairs = ast.literal_eval(statements[0].value)
        self.assertEqual(2, len(pairs))
        self.assertEqual((STRICT_LINES.encode(), b""), pairs[0])
        appkit = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef)
                      and n.name == "_appkit_key_wait_source")
        self.assertEqual(ast.get_source_segment(source.decode(), appkit).encode(), pairs[1][0])
        self.assertEqual("9e26d8dd2108afa2ef1ac9d6b2c38447f1a413bbb92151f988ec7064c07c74fd",
                         sha(pairs[1][1]))
        expected_loop = ast.parse(
            "for after, before in historical_deltas:\n"
            "    self.assertEqual(1, r5.count(after))\n"
            "    r5 = r5.replace(after, before, 1)\n").body[0]
        self.assertEqual(ast.dump(expected_loop, include_attributes=False),
                         ast.dump(statements[1], include_attributes=False))
        self.assertEqual("e2658a27f21c94cdf64038e47408faa40c742f0bbb3d324af0f75c092b821b22",
                         sha((common_text[:left] + common_text[right:]).encode()))

        document = recovery._document(ROOT)
        row = document["bindings"][content.SOURCE_RELATIVE]
        self.assertEqual(5, len(row["fragments"]))
        self.assertEqual(("ad544703072bd892274a08b29304f313d1915d8c24840f6d136474ea1e560253", 14440),
                         (row["before_sha256"], row["before_bytes"]))
        self.assertEqual((sha(source), len(source)), (row["after_sha256"], row["after_bytes"]))
        original_content = recovery._inverse(source, row)
        self.assertEqual((row["before_sha256"], row["before_bytes"]),
                         (sha(original_content), len(original_content)))

        def inverse(payload, binding):
            self.assertEqual((binding["after_sha256"], binding["after_bytes"]), (sha(payload), len(payload)))
            result = payload
            for fragment in reversed(binding["fragments"]):
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, result.count(after))
                result = result.replace(after, before, 1)
            self.assertEqual((binding["before_sha256"], binding["before_bytes"]), (sha(result), len(result)))
            forward = result
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(1, forward.count(before))
                forward = forward.replace(before, after, 1)
            self.assertEqual(payload, forward)
            return result

        # Only these three already-current303 historical fixture successors
        # extend strict recovery. Original303/raw301 and every named map stay
        # unchanged; old38/51 and actual41/54 are deliberately distinct DATA.
        fixture_successors = frozenset({
            "scripts/ci/test_tooling656_fixture_recovery.py",
            "scripts/ci/test_platform_recovery659_source_projection.py",
            "scripts/ci/test_producer698_shared_fixture_recovery676.py",
        })
        self.assertEqual(fixture_successors, recovery.FIXTURE_SUCCESSORS742)
        self.assertEqual(38, len(recovery.MODIFIED - fixture_successors - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(51, len(recovery.dependency_inputs() - fixture_successors - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(41, len(recovery.MODIFIED - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(54, len(recovery.dependency_inputs() - {"scripts/ci/test_source_path_memoization714.py", "scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(42, len(recovery.MODIFIED - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(55, len(recovery.dependency_inputs() - {"scripts/ci/android_camera_callback_native_focus.py"}))
        self.assertEqual(43, len(recovery.MODIFIED))
        self.assertEqual(56, len(recovery.dependency_inputs()))
        self.assertNotIn("scripts/ci/test_cookie_content_owner_successor740.py", recovery.MODIFIED)
        self.assertNotIn("scripts/ci/test_cookie_content_owner_successor740.py", recovery.dependency_inputs())
        import macos_share_ci668_composition as joint
        self.assertEqual(301, len(joint._document(ROOT)["raw_inputs"]))
        self.assertEqual(303, len(joint.fixture_inputs(ROOT)))
        self.assertEqual("06d04d038b06c00e5aafb9b7defdf39ae069f3df305e4dbc84198bc8ed178a24",
                         sha(_ordinary_bytes(ROOT, joint.SPEC)[0]))
        self.assertEqual("5b450daf9874a62a4b452b0d6502c3a77426e670ec6fd79a6b1ed3a3aecf6e52",
                         sha(_ordinary_bytes(ROOT, recovery.DOMAIN740_SPEC)[0]))
        fixture_before = {
            "scripts/ci/test_tooling656_fixture_recovery.py":
                ("935bf50eaaa0d07614aa3537d2d27a8fa1794521c2300c02c6f62cf46fcfbf17", 13641),
            "scripts/ci/test_platform_recovery659_source_projection.py":
                ("c7d3a9239fb5c20bd0cad7a4aaf38261ab50e5e62d26851fee96e9bc27e9070e", 17706),
            "scripts/ci/test_producer698_shared_fixture_recovery676.py":
                ("59d98496da46334866742972b89d2d44d14074835d9122fdabff48419e04ccf1", 38034),
        }
        fixture_masks = {'scripts/ci/test_tooling656_fixture_recovery.py': {'test_ancestor_hooks_and_exact_image_operand_keep_every_original_method_and_assertion', 'test_one_complete_fixture_derivative_keeps_original_pin_and_refuses_stale_partial_and_type_drift'}, 'scripts/ci/test_platform_recovery659_source_projection.py': {'test_manifest_exact_schema_and_raw_image_fixture_operand_do_not_double_peel_or_certify_pass_through'}, 'scripts/ci/test_producer698_shared_fixture_recovery676.py': {'test_tooling656_image_operand_strictly_qualifies_shared671_before_original_exact656_guard'}}
        for relative in sorted(fixture_successors):
            actual = _ordinary_bytes(ROOT, relative)[0]
            fixture_row = document["bindings"][relative]
            self.assertEqual(fixture_before[relative],
                             (fixture_row["before_sha256"], fixture_row["before_bytes"]))
            previous = inverse(actual, fixture_row)
            self.assertEqual(fixture_before[relative], (sha(previous), len(previous)))
            self.assertEqual(previous, recovery.current_source_before_recovery(relative, actual, ROOT))
            self.assertIs(previous, recovery.peel_recovery_for_history(relative, previous, ROOT))
            old_tests = {node.name: node for node in ast.walk(ast.parse(previous))
                         if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            new_tests = {node.name: node for node in ast.walk(ast.parse(actual))
                         if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            self.assertEqual(set(old_tests), set(new_tests))
            self.assertEqual(fixture_masks[relative],
                             {name for name in old_tests if ast.dump(old_tests[name], include_attributes=False) !=
                              ast.dump(new_tests[name], include_attributes=False)})
            for rejected in (previous, actual[:-1], actual + b"\n", b"", None, bytearray(actual), actual.decode()):
                with self.subTest(relative=relative, kind=type(rejected).__name__), self.assertRaises(ValueError):
                    recovery.current_source_before_recovery(relative, rejected, ROOT)
            if relative.endswith("test_producer698_shared_fixture_recovery676.py"):
                def bindings(payload):
                    nodes = [node for node in ast.parse(payload).body if isinstance(node, ast.Assign) and
                             any(isinstance(target, ast.Name) and target.id == "FIXTURE_BINDINGS" for target in node.targets)]
                    self.assertEqual(1, len(nodes))
                    return ast.literal_eval(nodes[0].value)
                self.assertEqual(bindings(previous), bindings(actual))
                self.assertEqual(2, len(bindings(actual)["scripts/ci/test_tooling656_fixture_recovery.py"]["fragments"]))
        self.assertEqual(TARGET, content._TOOLING656_CONTROL_PATH)
        raw = _ordinary_bytes(ROOT, TARGET)[0]
        self.assertEqual(("094923f12217f7c8571966e230f96abbf6ffaaedbcd0ad1f06db5048fdd1498e", 23006),
                         (sha(raw), len(raw)))
        recovered = inverse(raw, document["bindings"][TARGET])
        self.assertEqual(("e9af322336f08c49c6a4456fe60edaa8fa44884c8161dff42f707d94effb4ad7", 22811),
                         (sha(recovered), len(recovered)))
        tooling_row = tooling._document()["bindings"][TARGET]
        stage = inverse(recovered, tooling_row)
        self.assertEqual(("4dd74834552bb6bf06e8ac79b42d268926dad567dda5430894129c76075b4a26", 22664),
                         (sha(stage), len(stage)))
        legacy = content._TOOLING656_CONTROL_BINDING
        legacy_row = {key: legacy[key] for key in ("before_sha256", "after_sha256", "before_bytes", "after_bytes")}
        legacy_row["fragments"] = [{key: legacy[key] for key in
                                  ("before", "after", "before_fragment_sha256", "after_fragment_sha256")}]
        original = inverse(stage, legacy_row)
        self.assertEqual(("9d7870ffcd1cf584c7e2914143d93066defba889638df05f0f91781ab5dd2fa9", 22593),
                         (sha(original), len(original)))
        self.assertEqual(sha(original), content._document()["unchanged_inputs"][TARGET])

        # One strict existing outer ingress sees RAW, never a pre-peeled old
        # operand; every literal656 endpoint and final forward check remains.
        real_current = tooling.current_source_before_tooling671
        stages = []
        def owning(relative, payload):
            result = real_current(relative, payload)
            stages.append(result)
            return result
        with patch.object(tooling, "current_source_before_tooling671", side_effect=owning) as strict:
            self.assertEqual(original, content._current_tooling656_control_source(TARGET, raw))
            strict.assert_called_once_with(TARGET, raw)
        self.assertEqual([stage], stages)
        fragment = document["bindings"][TARGET]["fragments"][0]["after"].encode()
        displaced = raw.replace(fragment, b"", 1) + fragment
        self.assertNotEqual(raw, displaced)
        for bad in (original, stage, recovered, raw[:-1], raw + b"\n", displaced,
                    b"unknown", b"", None, bytearray(raw), raw.decode()):
            with self.subTest(type=type(bad).__name__), self.assertRaises(ValueError):
                content._current_tooling656_control_source(TARGET, bad)
        for relative in (None, 1, Path(TARGET), []):
            with self.subTest(relative=type(relative).__name__), self.assertRaises(ValueError):
                content._current_tooling656_control_source(relative, raw)
        with patch.object(tooling, "current_source_before_tooling671",
                          side_effect=AssertionError("Unlisted bytes earned a current certificate")):
            foreign = b"foreign unlisted DATA"
            self.assertIs(foreign, content._current_tooling656_control_source("unlisted-source", foreign))
        changed = dict(legacy, after_fragment_sha256="0" * 64)
        with patch.object(content, "_TOOLING656_CONTROL_BINDING", changed), self.assertRaises(ValueError):
            content._current_tooling656_control_source(TARGET, raw)
        changed_document = copy.deepcopy(content._document())
        changed_document["unchanged_inputs"][TARGET] = "0" * 64
        with patch.object(content, "_document", return_value=changed_document), self.assertRaises(ValueError):
            content._current_tooling656_control_source(TARGET, raw)


if __name__ == "__main__":
    unittest.main()
