# SPDX-License-Identifier: Apache-2.0
"""NEW finite producer698 fixture controls; no checkout/controller/native adoption.

The four executable fixture postimages and current ROOT source/data inputs are
separate in external preparation. In an integrated checkout they are the same
ROOT, only after the lead's single exact batch successor has been qualified.
All inverse-produced source is AST/data only, never imported or executed.
"""
import ast
import hashlib
import json
from pathlib import Path
import unittest

import ios_ui_split664_source_projection as split
import webview_content_policy_source_projection as content

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE_ROOT = ROOT

FIXTURE_BINDINGS = {'scripts/ci/test_ios_geometry_simulator_source_projection.py': {'after_bytes': 10169,
                                                                 'after_sha256': '1201e8b8211cccac34960de13008ae93489ff1e98a01669ec6920f13f4e70e29',
                                                                 'before_bytes': 9925,
                                                                 'before_sha256': 'a13aa64cdc102fe1d755c5e4c95c7a5e4b24330f32109312927a688713b150d4',
                                                                 'changed_class': 'OwnedGeometrySourceControls',
                                                                 'changed_method': 'test_native_compiler_and_old_manifest_inputs_are_exactly_unchanged',
                                                                 'fragments': [{'after': '        from '
                                                                                         'ios_ui_split664_source_projection '
                                                                                         'import '
                                                                                         'current_source_before_ui_split664\n'
                                                                                         '        for '
                                                                                         'name, '
                                                                                         'expected in '
                                                                                         '(document["unchanged_native_compiler_inputs"] '
                                                                                         '| '
                                                                                         'document["unchanged_dated_manifests"]).items():\n'
                                                                                         '            '
                                                                                         'current = '
                                                                                         '(ROOT / '
                                                                                         'name).read_bytes()\n'
                                                                                         '            '
                                                                                         'if name == '
                                                                                         '"calf-ui/build.gradle.kts":\n'
                                                                                         '                '
                                                                                         'current = '
                                                                                         'current_source_before_ui_split664(name, '
                                                                                         'current)\n'
                                                                                         '            '
                                                                                         'self.assertEqual(expected, '
                                                                                         'sha(current), '
                                                                                         'name)\n',
                                                                                'after_fragment_sha256': '4eaf106a64f27971de2a629840016ddd3d1215ac7f9cda7391ea519f7af981ec',
                                                                                'before': '        for '
                                                                                          'name, '
                                                                                          'expected in '
                                                                                          '(document["unchanged_native_compiler_inputs"] '
                                                                                          '| '
                                                                                          'document["unchanged_dated_manifests"]).items():\n'
                                                                                          '            '
                                                                                          'self.assertEqual(expected, '
                                                                                          'sha((ROOT / '
                                                                                          'name).read_bytes()), '
                                                                                          'name)\n',
                                                                                'before_fragment_sha256': '09635940f8216c2c9177fe5393f0eee985b779b9a027207a498ce56ceea61f0b',
                                                                                'id': 'producer698-four676-exact-hunk-1'}],
                                                                 'mode': '0o644'},
 'scripts/ci/test_ios_ui_split664_native_routing.py': {'after_bytes': 42767,
                                                       'after_sha256': '2d581af413ded91349a4828a24aba2eaf7b48d65cf4cc186a0b137f9145d208f',
                                                       'before_bytes': 42720,
                                                       'before_sha256': '58a6e93641d2f221fb09a74f2ae69fa28b2b2278624c96605782cd1bc89447a2',
                                                       'changed_class': 'UiSplit664SourceControls',
                                                       'changed_method': 'test_one_newest_split_ingress_reaches_sealed667_and659_without_repinning_or_recursive_controller_calls',
                                                       'fragments': [{'after': '        '
                                                                               'self.assertEqual({"__future__", '
                                                                               '"pathlib", '
                                                                               '"ios_popover_anchor_plan", '
                                                                               '"android_io_remote_routing_source_projection"}, '
                                                                               '{node.module for node '
                                                                               'in imports})\n',
                                                                      'after_fragment_sha256': 'fd93cd10dcc527d691785b96f6fddd90370e65e14c3a8559eec60f5d0e85fb88',
                                                                      'before': '        '
                                                                                'self.assertEqual({"__future__", '
                                                                                '"pathlib", '
                                                                                '"ios_popover_anchor_plan"}, '
                                                                                '{node.module for node '
                                                                                'in imports})\n',
                                                                      'before_fragment_sha256': '29fab486ab8d1931e0593575e95b4436d6fb628d52a578ce465523a9afc186aa',
                                                                      'id': 'producer698-four676-exact-hunk-1'}],
                                                       'mode': '0o600'},
 'scripts/ci/test_tooling656_fixture_recovery.py': {'after_bytes': 13641,
                                                    'after_sha256': '935bf50eaaa0d07614aa3537d2d27a8fa1794521c2300c02c6f62cf46fcfbf17',
                                                    'before_bytes': 13493,
                                                    'before_sha256': '8107f77ebc0e2c74aa4fcf6b55eed9b644160fb8bdfb8e19d8670dee4bd71e33',
                                                    'changed_class': 'Tooling656FixtureRecoveryControls',
                                                    'changed_method': 'test_ancestor_hooks_and_exact_image_operand_keep_every_original_method_and_assertion',
                                                    'fragments': [{'after': '                                 '
                                                                            '("current_source_before_recents_observation", '
                                                                            '"recents_fixture_after_qualified_outer_ingress")):\n',
                                                                   'after_fragment_sha256': 'ebd9da160a631aec93de7adb0d5dda34be8ee55243a24b6edb277e26c2576b4e',
                                                                   'before': '                                 '
                                                                             '("current_source_before_recents_observation", '
                                                                             '"current_source_before_recents_fixture")):\n',
                                                                   'before_fragment_sha256': 'b9bf74c386b1caad6417bf5541163b38198dc2c23c516d9be66c17282c164bf0',
                                                                   'id': 'producer698-four676-exact-hunk-1'},
                                                                  {'after': '        from '
                                                                            'tooling_recovery671_source_projection '
                                                                            'import '
                                                                            'current_source_before_tooling671\n'
                                                                            '        current = '
                                                                            'current_source_before_tooling671(IMAGE_CONTROL, '
                                                                            '(ROOT / '
                                                                            'IMAGE_CONTROL).read_bytes())\n'
                                                                            '        previous = '
                                                                            'content_history._current_tooling656_control_source(IMAGE_CONTROL, '
                                                                            'current)\n',
                                                                   'after_fragment_sha256': 'cd6185e26e9e88c1605fc00f497a1a3550fc7e3d0a8d3d72b6dd8dd57e7b8193',
                                                                   'before': '        current = (ROOT / '
                                                                             'IMAGE_CONTROL).read_bytes()\n'
                                                                             '        previous = '
                                                                             'content_history._current_tooling656_control_source(IMAGE_CONTROL, '
                                                                             'current)\n',
                                                                   'before_fragment_sha256': 'c1ead625ab8258dd16b5afa523c6af0c05a6769e471ace8e8b9acbf7ce0a6794',
                                                                   'id': 'producer698-four676-exact-hunk-2-image671-operand'}],
                                                    'mode': '0o600'},
 'scripts/ci/test_webview_content_policy_source_projection.py': {'after_bytes': 22013,
                                                                 'after_sha256': '00634b43d622900c8c0a5319dde44034959407128733213fb4dccef28ab8ae2e',
                                                                 'before_bytes': 21769,
                                                                 'before_sha256': '22d11f050ee284d1002fb1349425cd17e2638964790bf577b83c6844a5e0c3ef',
                                                                 'changed_class': 'WebViewContentPolicySourceProjectionControls',
                                                                 'changed_method': 'test_original_share_ui_manifests_guard_pins_control_assertions_and_unaffected_methods_remain_exact',
                                                                 'fragments': [{'after': '        from '
                                                                                         'ios_ui_split664_source_projection '
                                                                                         'import '
                                                                                         'current_source_before_ui_split664\n'
                                                                                         '        for '
                                                                                         'name, changed '
                                                                                         'in '
                                                                                         'affected.items():\n'
                                                                                         '            '
                                                                                         'raw = (ROOT / '
                                                                                         'name).read_bytes()\n'
                                                                                         '            '
                                                                                         'if name == '
                                                                                         '"scripts/ci/test_ios_ui_related_source_projection.py":\n'
                                                                                         '                '
                                                                                         'raw = '
                                                                                         'current_source_before_ui_split664(name, '
                                                                                         'raw)\n'
                                                                                         '            '
                                                                                         'prior = '
                                                                                         'history.source_before_content_policy(name, '
                                                                                         'raw)\n',
                                                                                'after_fragment_sha256': '684c9c8797f13b64bdf0715ccc197b00b99e60b938d827e4d11b2c2186899221',
                                                                                'before': '        for '
                                                                                          'name, '
                                                                                          'changed in '
                                                                                          'affected.items():\n'
                                                                                          '            '
                                                                                          'raw = (ROOT '
                                                                                          '/ '
                                                                                          'name).read_bytes(); '
                                                                                          'prior = '
                                                                                          'history.source_before_content_policy(name, '
                                                                                          'raw)\n',
                                                                                'before_fragment_sha256': '01f086fbc2cb47c1f28531281c8d4f749789ae34752861f2e7c17588b1c63b18',
                                                                                'id': 'producer698-four676-exact-hunk-1'}],
                                                                 'mode': '0o600'}}

SEALED_SPECS = {'scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json': '4dee514d6aa6bdfaf5856a24416cfb7a677f67daeed9f7fed9b43215e31e95de',
 'scripts/ci/fixtures/ci668-outer-source-inverse.json': 'bbfdb2454182ce8c1fc90e793c3552e49f317b35437b61fcd3e8743b86f9d86e',
 'scripts/ci/fixtures/ios-owned-geometry575-source-inverse.json': '736ef0e38d1e89baa0c7cbdd0707189d28a197b08fb11500943d94cede28efdd',
 'scripts/ci/fixtures/ios-owned-geometry581-fixture-recovery.json': '441995a9a586509700a8359c744c6a2d7420abed2df2924333c6f111598dcd58',
 'scripts/ci/fixtures/ios-ui-split664-source-inverse.json': '1455a8edb3553a87a409f7fc30568ede9f7f52fe97042690b668dc6ebc145f4a',
 'scripts/ci/fixtures/platform-recovery659-source-inverse.json': 'c9a56d4288e1d6a71914de27b0218d0877840136e9d24d448e2d192fcf7d90e9',
 'scripts/ci/fixtures/tooling-recovery671-source-inverse.json': '9def6c416e199237600bdcdc2a16a3fd22dc2158796e1116f999b8681c96a110',
 'scripts/ci/fixtures/webview-content-policy-routing-source-inverse.json': 'c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916'}

UI_BUILD = "calf-ui/build.gradle.kts"
UI_CONTROL = "scripts/ci/test_ios_ui_related_source_projection.py"
UI_SPLIT_GUARD = "scripts/ci/ios_ui_split664_source_projection.py"
RECENTS_GUARD = "scripts/ci/camera_recents_source_projection.py"
RECENTS_FIXTURE_GUARD = "scripts/ci/camera_recents_fixture_source_projection.py"
UI_SPLIT_SPEC = "scripts/ci/fixtures/ios-ui-split664-source-inverse.json"
IO_SPEC = "scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json"
GUARDS = {
    UI_SPLIT_GUARD: "3fe6ba6239409536db53b1121bf6830b7dedfd521a5aef77c557833f7cda212f",
    RECENTS_GUARD: "dcdc53cccbf7d0ffa4c9608d64d6f4a4dd3aee1c634438fb19960914c504dfa0",
    RECENTS_FIXTURE_GUARD: "05c445b75a1811db3b98e999cdbbae35f3347d652a9867f344887ce436c5a932",
}


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _function(tree, name):
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact named source function is required")
    return matches[0]


def _test_methods(raw):
    return {node.name: node for node in ast.walk(ast.parse(raw))
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}


def _assertions(tree):
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and
            node.func.value.id == "self" and node.func.attr.startswith("assert")]


def _exact_inverse_for_control(payload, row):
    # Byte/data calculation only, not a source admission API or a generic peeling stage.
    if (type(payload) is not bytes or not 0 < len(payload) <= 4 * 1024 * 1024 or
            sha(payload) != row["after_sha256"] or len(payload) != row["after_bytes"]):
        raise ValueError("One exact complete current control image is required")
    restored = payload
    for fragment in reversed(row["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (sha(before) != fragment["before_fragment_sha256"] or
                sha(after) != fragment["after_fragment_sha256"] or restored.count(after) != 1):
            raise ValueError("Only a sealed unique inverse fragment is allowed")
        restored = restored.replace(after, before, 1)
    if sha(restored) != row["before_sha256"] or len(restored) != row["before_bytes"]:
        raise ValueError("The whole named ancestor must be restored exactly")
    forward = restored
    for fragment in row["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("The exact ancestor has one unique forward site")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("The complete finite image must round trip")
    return restored


def _fixture_before_for_control(relative, payload):
    if type(relative) is not str or relative not in FIXTURE_BINDINGS:
        raise ValueError("Only the four named proposal fixtures are control inputs")
    return _exact_inverse_for_control(payload, FIXTURE_BINDINGS[relative])


def _sealed_document(relative):
    if relative not in SEALED_SPECS:
        raise ValueError("Only the explicitly named old immutable spec is allowed")
    raw = (ROOT / relative).read_bytes()
    if sha(raw) != SEALED_SPECS[relative]:
        raise ValueError("An original pin must not be rewritten")
    return json.loads(raw)


def _payload_calls(owner):
    return [ast.unparse(node.value.func) for node in owner.body if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Name) and target.id == "payload" for target in node.targets) and
            isinstance(node.value, ast.Call)]


def _recents_topology(outer_raw, fixture_raw):
    outer, fixture = ast.parse(outer_raw), ast.parse(fixture_raw)
    current = _function(outer, "current_source_before_recents_observation")
    historical = _function(outer, "source_before_recents_observation")
    raw_entry = _function(fixture, "current_source_before_recents_fixture")
    child = _function(fixture, "recents_fixture_after_qualified_outer_ingress")
    if _payload_calls(current) != ["peel_content_policy_for_history", "recents_fixture_after_qualified_outer_ingress"]:
        raise AssertionError("The already-qualified recents caller must use its exact child")
    if _payload_calls(historical) != ["peel_content_policy_for_history", "source_before_recents_fixture"]:
        raise AssertionError("The historical reader stays historical")
    if (_payload_calls(raw_entry) != ["current_source_before_platform_recovery659"] or
            ast.unparse(raw_entry.body[-1]) != "return recents_fixture_after_qualified_outer_ingress(relative, payload)"):
        raise AssertionError("Raw fixture admission must retain one strict outer qualification")
    if _payload_calls(child) != ["peel_current_tooling566_for_older_history", "peel_current_tooling_for_older_history",
                                 "peel_current_boot_busy_for_older_history"]:
        raise AssertionError("The qualified child permits only three named older stages")
    if any(isinstance(node, ast.Call) and ast.unparse(node.func).startswith("current_source_before_")
           for node in ast.walk(child)):
        raise AssertionError("A qualified child must not repeat current/raw admission")
    condition = "binding is not None and hashlib.sha256(payload).hexdigest() != binding['after_sha256']"
    if not any(isinstance(node, ast.If) and ast.unparse(node.test) == condition for node in child.body):
        raise AssertionError("The exact dated afterimage pin must remain in the child")
    if ast.unparse(child.body[-1]) != "return source_before_recents_fixture(relative, payload)":
        raise AssertionError("Only the named fixture ancestor inverse may follow")
    return True


class Producer698SharedFixtureRecoveryControls(unittest.TestCase):
    def test_geometry_hash_operand_qualifies_only_exact_ui664_build_and_refuses_ancestor_or_drift(self):
        row = _sealed_document(UI_SPLIT_SPEC)["bindings"][UI_BUILD]
        raw = (ROOT / UI_BUILD).read_bytes()
        previous = _exact_inverse_for_control(raw, row)
        self.assertEqual("ad833c62e9e492b3ef5e5019f4d805326ed267c17b1b159aa543b8b8896c448e", sha(previous))
        self.assertEqual(previous, split.current_source_before_ui_split664(UI_BUILD, raw))
        for rejected in (previous, raw + b"\n", raw[:-1] + bytes([raw[-1] ^ 1])):
            with self.assertRaises(ValueError):
                split.current_source_before_ui_split664(UI_BUILD, rejected)
        relative = "scripts/ci/test_ios_geometry_simulator_source_projection.py"
        method = _function(ast.parse((EXECUTABLE_ROOT / relative).read_bytes()), FIXTURE_BINDINGS[relative]["changed_method"])
        qualifiers = [node for node in ast.walk(method) if isinstance(node, ast.If) and
                      ast.unparse(node.test) == "name == 'calf-ui/build.gradle.kts'"]
        self.assertEqual(1, len(qualifiers))
        self.assertEqual("current = current_source_before_ui_split664(name, current)", ast.unparse(qualifiers[0].body[0]))
        self.assertEqual(1, len([node for node in ast.walk(method) if isinstance(node, ast.Call) and
                                 ast.unparse(node.func) == "current_source_before_ui_split664"]))
        self.assertEqual(["ios_ui_split664_source_projection"], [node.module for node in ast.walk(method) if isinstance(node, ast.ImportFrom)])

    def test_split_import_envelope_is_exact_current_four_and_sealed_io665_three_import_ancestor(self):
        raw = (ROOT / UI_SPLIT_GUARD).read_bytes()
        self.assertEqual(GUARDS[UI_SPLIT_GUARD], sha(raw))
        row = _sealed_document(IO_SPEC)["bindings"][UI_SPLIT_GUARD]
        prior = _exact_inverse_for_control(raw, row)
        self.assertEqual("fa7dc60a3d5c89094d5981b14f16df870b75abb64581fbbdeaa914565261bd0f", sha(prior))
        older = {"__future__", "pathlib", "ios_popover_anchor_plan"}
        latest = older | {"android_io_remote_routing_source_projection"}
        self.assertEqual(latest, {node.module for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.ImportFrom)})
        self.assertEqual(older, {node.module for node in ast.walk(ast.parse(prior)) if isinstance(node, ast.ImportFrom)})
        relative = "scripts/ci/test_ios_ui_split664_native_routing.py"
        method = _function(ast.parse((EXECUTABLE_ROOT / relative).read_bytes()), FIXTURE_BINDINGS[relative]["changed_method"])
        permitted = [ast.literal_eval(node.args[0]) for node in ast.walk(method) if isinstance(node, ast.Call) and
                     ast.unparse(node.func) == "self.assertEqual" and node.args and isinstance(node.args[0], ast.Set)]
        self.assertEqual([latest], permitted)
        prohibited = {"exec", "eval", "compile"}
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in prohibited
                             for node in ast.walk(ast.parse(raw))))

    def test_recents_strict_raw_wrapper_and_exact_qualified_child_reject_arbitrary_reader_substitution(self):
        outer, fixture = (ROOT / RECENTS_GUARD).read_bytes(), (ROOT / RECENTS_FIXTURE_GUARD).read_bytes()
        self.assertEqual(GUARDS[RECENTS_GUARD], sha(outer))
        self.assertEqual(GUARDS[RECENTS_FIXTURE_GUARD], sha(fixture))
        self.assertTrue(_recents_topology(outer, fixture))
        for bad_outer, bad_fixture in (
                (outer.replace(b"payload = recents_fixture_after_qualified_outer_ingress(relative, payload)",
                               b"payload = current_source_before_recents_fixture(relative, payload)", 1), fixture),
                (outer, fixture.replace(b"payload = current_source_before_platform_recovery659(relative, payload)",
                                        b"payload = peel_platform_recovery659_for_history(relative, payload)", 1)),
                (outer, fixture.replace(b"payload = peel_current_boot_busy_for_older_history(relative, payload)",
                                        b"payload = generic_source_peeling(relative, payload)")),
                (outer, fixture.replace(b"!= binding[\"after_sha256\"]", b"!= binding[\"before_sha256\"]"))):
            with self.assertRaises(AssertionError):
                _recents_topology(bad_outer, bad_fixture)
        relative = "scripts/ci/test_tooling656_fixture_recovery.py"
        method = _function(ast.parse((EXECUTABLE_ROOT / relative).read_bytes()), FIXTURE_BINDINGS[relative]["changed_method"])
        loop = next(node for node in method.body if isinstance(node, ast.For))
        self.assertEqual((("source_before_recents_observation", "source_before_recents_fixture"),
                          ("current_source_before_recents_observation", "recents_fixture_after_qualified_outer_ingress")),
                         ast.literal_eval(loop.iter))

    def test_webview_ui_comparison_normalizes_exact_two_ui664_changes_without_extra_exception(self):
        row = _sealed_document(UI_SPLIT_SPEC)["bindings"][UI_CONTROL]
        self.assertEqual(2, len(row["fragments"]))
        raw = (ROOT / UI_CONTROL).read_bytes()
        previous = _exact_inverse_for_control(raw, row)
        self.assertEqual("39a14cc6b00790d4954ae9c116e6487206f0ce6b9234903837a6bee80c817f64", sha(previous))
        self.assertEqual(previous, split.current_source_before_ui_split664(UI_CONTROL, raw))
        for rejected in (previous, raw + b"\n"):
            with self.assertRaises(ValueError):
                split.current_source_before_ui_split664(UI_CONTROL, rejected)
        before, after = _test_methods(previous), _test_methods(raw)
        self.assertEqual(set(before), set(after))
        delta = {name for name in before if ast.dump(before[name], include_attributes=False) != ast.dump(after[name], include_attributes=False)}
        self.assertEqual({"test_camera_bridge_175c_and_runtime620_inputs_are_not_edited_or_replayed",
                          "test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged"}, delta)
        old_webview = _test_methods(content.source_before_content_policy(UI_CONTROL, previous))
        self.assertEqual(set(before), set(old_webview))
        self.assertEqual({"test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged"},
                         {name for name in before if ast.dump(before[name], include_attributes=False) != ast.dump(old_webview[name], include_attributes=False)})
        relative = "scripts/ci/test_webview_content_policy_source_projection.py"
        method = _function(ast.parse((EXECUTABLE_ROOT / relative).read_bytes()), FIXTURE_BINDINGS[relative]["changed_method"])
        affected = next(node for node in method.body if isinstance(node, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == "affected" for target in node.targets))
        self.assertEqual({UI_CONTROL: {"test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged"},
                          "scripts/ci/test_macos_share_missing_source_projection.py": {"test_exact_six_path_inverse_roundtrip_and_one_newest_raw_ingress",
                           "test_only_transparent_ui_history_hooks_and_narrow_fixture_operands_change"}}, ast.literal_eval(affected.value))
        qualifiers = [node for node in ast.walk(method) if isinstance(node, ast.If) and
                      ast.unparse(node.test) == "name == 'scripts/ci/test_ios_ui_related_source_projection.py'"]
        self.assertEqual(1, len(qualifiers))
        self.assertEqual("raw = current_source_before_ui_split664(name, raw)", ast.unparse(qualifiers[0].body[0]))

    def test_four_complete_fixture_postimages_preserve_all_other_methods_and_original_assertion_callees(self):
        self.assertEqual(4, len(FIXTURE_BINDINGS))
        for relative, row in FIXTURE_BINDINGS.items():
            raw = (EXECUTABLE_ROOT / relative).read_bytes()
            ancestor = _fixture_before_for_control(relative, raw)
            before, after = _test_methods(ancestor), _test_methods(raw)
            self.assertEqual(set(before), set(after), relative)
            changed = [name for name in before if ast.dump(before[name], include_attributes=False) != ast.dump(after[name], include_attributes=False)]
            self.assertEqual([row["changed_method"]], changed, relative)
            old_asserts, new_asserts = _assertions(ast.parse(ancestor)), _assertions(ast.parse(raw))
            self.assertEqual(len(old_asserts), len(new_asserts), relative)
            self.assertEqual([ast.unparse(node.func) for node in old_asserts], [ast.unparse(node.func) for node in new_asserts], relative)
            if relative not in {"scripts/ci/test_ios_geometry_simulator_source_projection.py", "scripts/ci/test_ios_ui_split664_native_routing.py"}:
                self.assertEqual([ast.dump(node, include_attributes=False) for node in old_asserts],
                                 [ast.dump(node, include_attributes=False) for node in new_asserts], relative)
        for relative in SEALED_SPECS:
            self.assertEqual(SEALED_SPECS[relative], sha((ROOT / relative).read_bytes()), relative)

    def test_four_leaf_control_inverse_refuses_old_drift_duplicate_fragment_foreign_path_and_nonbytes(self):
        for relative in FIXTURE_BINDINGS:
            current = (EXECUTABLE_ROOT / relative).read_bytes()
            ancestor = _fixture_before_for_control(relative, current)
            for rejected in (ancestor, current + b"\n", current + FIXTURE_BINDINGS[relative]["fragments"][0]["after"].encode(),
                             bytearray(current), memoryview(current)):
                with self.assertRaises(ValueError):
                    _fixture_before_for_control(relative, rejected)
        with self.assertRaises(ValueError):
            _fixture_before_for_control("scripts/ci/foreign_producer_fixture.py", b"source")
        with self.assertRaises(ValueError):
            _fixture_before_for_control(Path(next(iter(FIXTURE_BINDINGS))), b"source")

    def test_tooling656_image_operand_strictly_qualifies_shared671_before_original_exact656_guard(self):
        from tooling_recovery671_source_projection import current_source_before_tooling671
        name = "scripts/ci/test_apple_image_launcher_source_projection.py"
        raw = (ROOT / name).read_bytes()
        self.assertEqual("e9af322336f08c49c6a4456fe60edaa8fa44884c8161dff42f707d94effb4ad7", sha(raw))
        document = _sealed_document("scripts/ci/fixtures/tooling-recovery671-source-inverse.json")
        row = document["bindings"][name]
        qualified = _exact_inverse_for_control(raw, row)
        self.assertEqual("4dd74834552bb6bf06e8ac79b42d268926dad567dda5430894129c76075b4a26", sha(qualified))
        self.assertEqual(qualified, current_source_before_tooling671(name, raw))
        for rejected in (qualified, raw + b"\n"):
            with self.assertRaises(ValueError):
                current_source_before_tooling671(name, rejected)
        ancestor = content._current_tooling656_control_source(name, qualified)
        self.assertEqual("9d7870ffcd1cf584c7e2914143d93066defba889638df05f0f91781ab5dd2fa9", sha(ancestor))
        self.assertEqual([ast.dump(node, include_attributes=False) for node in _assertions(ast.parse(ancestor))],
                         [ast.dump(node, include_attributes=False) for node in _assertions(ast.parse(qualified))])
        old, latest = _test_methods(qualified), _test_methods(raw)
        self.assertEqual(set(old), set(latest))
        self.assertEqual({"test_fragment_hashes_unique_sites_and_complete_restoration_are_mandatory"},
                         {method for method in old if ast.dump(old[method], include_attributes=False) != ast.dump(latest[method], include_attributes=False)})
        relative = "scripts/ci/test_tooling656_fixture_recovery.py"
        postimage = (EXECUTABLE_ROOT / relative).read_bytes()
        self.assertEqual(2, len(FIXTURE_BINDINGS[relative]["fragments"]))
        restored = _fixture_before_for_control(relative, postimage)
        before, after = _test_methods(restored), _test_methods(postimage)
        self.assertEqual([FIXTURE_BINDINGS[relative]["changed_method"]],
                         [method for method in before if ast.dump(before[method], include_attributes=False) != ast.dump(after[method], include_attributes=False)])
        self.assertEqual([ast.dump(node, include_attributes=False) for node in _assertions(ast.parse(restored))],
                         [ast.dump(node, include_attributes=False) for node in _assertions(ast.parse(postimage))])
        method = _function(ast.parse(postimage), FIXTURE_BINDINGS[relative]["changed_method"])
        assignments = [node for node in method.body if isinstance(node, ast.Assign) and
                       any(isinstance(target, ast.Name) and target.id == "current" for target in node.targets)]
        self.assertEqual(1, len(assignments))
        self.assertEqual("current_source_before_tooling671(IMAGE_CONTROL, (ROOT / IMAGE_CONTROL).read_bytes())", ast.unparse(assignments[0].value))
