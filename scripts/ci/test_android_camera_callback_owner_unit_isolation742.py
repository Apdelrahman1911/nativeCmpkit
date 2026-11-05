# SPDX-License-Identifier: Apache-2.0
"""NEW742 static owner-unit scaffold control; no target import or validator call.

This source-only control is explicitly held/unregistered, not current303,
recovery enrollment, a real CLI result or Android/compiler/native acceptance.
"""
import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "scripts/ci/test_android_camera_callback_native_focus.py"
METHOD = "test_exact_api35_one_method_profile_requires_explicit_receiver_and_delayed_focus"
CLI = "test_genuine_api35_callback_profile_cli_retains_unmocked_source_integration"
EXPECTED_AFTER_SHA256 = '7d94a858040461caf5cd84094e5e31f2b177a656727bc35e175d84a4f46aca96'
ORIGINAL_METHOD_AST_SHA256 = "b87fb9fc7794faf1df987f558c1ad9ac7c8fcfeaa4838274e63aa461f6314087"
OTHER_ORIGINAL_METHOD_AST_SHA256 = {'test_leaf668_exact_three_fragments_and_native_hold_recomposition_cleanup_without_injection': 'd36ed9b1b264cda7c6fd6a228cd54c7d30232b5df80a189513fbb3cf3fe048c9', 'test_unfiltered_wrong_api_and_foreign_contract_refuse_before_host_output_or_source_pruning': '5bc5c30a30c8832e0da44161d5a3957c4b1227f753a13c67ed1b1e58c2ef094d', 'test_only_complete_declared_non_camera_fixture_minimum_admits_source_discovery_never_default_or_deleted_camera': 'bbfe6466d84685a272bf992fdb173526d96e2e8bcf62133b2d6c91faa0e8df27', 'test_one_fresh_callback_xml_task_and_context_reject_missing_duplicate_skip_failure_stale_or_old_substitution': '5ae83c48309da9d28045382d117f968861ed05b0c2a441d99fa3b6b73ef97610'}


def ast_text(node):
    return ast.dump(node, include_attributes=False)


def ast_sha(node):
    return hashlib.sha256(ast_text(node).encode()).hexdigest()


class AndroidCameraCallbackOwnerUnitIsolation742Controls(unittest.TestCase):
    def test_NEW_genuine_positive_frozen_command_units_and_real_cli_keep_all_original_assertions(self):
        raw = (ROOT / SOURCE).read_bytes()
        self.assertEqual(EXPECTED_AFTER_SHA256, hashlib.sha256(raw).hexdigest())
        tree = ast.parse(raw.decode("utf-8"))
        owner, = [node for node in tree.body if isinstance(node, ast.ClassDef)
                  and node.name == "AndroidCameraCallbackSourceRoutingTests"]
        methods = {node.name: node for node in owner.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(OTHER_ORIGINAL_METHOD_AST_SHA256) | {METHOD, CLI},
                         {name for name in methods if name.startswith("test_")})
        for name, digest in OTHER_ORIGINAL_METHOD_AST_SHA256.items():
            self.assertEqual(digest, ast_sha(methods[name]))
        selected = methods[METHOD]
        self.assertEqual(17, len(selected.body))
        self.assertEqual(ast_text(ast.parse("plan = self.plan()").body[0]), ast_text(selected.body[3]))
        self.assertEqual(ast_text(ast.parse("self.assertTrue(library.validate_test_focus(plan))").body[0]),
                         ast_text(selected.body[4]))
        self.assertEqual([ast_text(node) for node in ast.parse(
            'frozen_contract = deepcopy(item[callback.CONTRACT_KEY])\n'
            'frozen_inputs = deepcopy(frozen_contract["source_inputs"])').body],
            [ast_text(node) for node in selected.body[14:16]])
        scope = selected.body[16]
        self.assertIsInstance(scope, ast.With)
        self.assertEqual(2, len(scope.items))
        expected_scope = ast.parse(
            'with patch.object(callback, "current_contract_hashes", '
            'side_effect=lambda *args, **kwargs: deepcopy(frozen_inputs)) as current_inputs, '
            'patch.object(callback, "source_contract", '
            'side_effect=lambda *args, **kwargs: deepcopy(frozen_contract)) as current_contract:\n'
            '    pass').body[0]
        self.assertEqual([ast_text(item) for item in expected_scope.items],
                         [ast_text(item) for item in scope.items])
        patches = [node for node in ast.walk(selected) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                   and node.func.value.id == "patch" and node.func.attr == "object"]
        self.assertEqual(2, len(patches))  # No surrounding positive or real CLI patch.
        self.assertEqual(21, len(scope.body))
        def exact_rows(rows, expected_source):
            self.assertEqual([ast_text(node) for node in ast.parse(expected_source).body],
                             [ast_text(node) for node in rows])
        command_counts = ('current_inputs.assert_called_once_with()\n'
                          'current_contract.assert_called_once_with(library.ROOT)\n'
                          'current_inputs.reset_mock()\ncurrent_contract.reset_mock()')
        exact_rows(scope.body[1:5], command_counts)
        exact_rows(scope.body[11:15], command_counts)
        serial = scope.body[17]
        self.assertIsInstance(serial, ast.For)
        self.assertEqual(5, len(serial.body))
        exact_rows(serial.body[1:5], 'current_inputs.assert_called_once_with()\n'
                   'current_contract.assert_not_called()\n'
                   'current_inputs.reset_mock()\ncurrent_contract.reset_mock()')
        shape = scope.body[19]
        self.assertIsInstance(shape, ast.For)
        # Original semicolon line is TWO Assign nodes, then the refusal With.
        self.assertEqual(7, len(shape.body))
        self.assertIsInstance(shape.body[0], ast.Assign)
        self.assertIsInstance(shape.body[1], ast.Assign)
        self.assertIsInstance(shape.body[2], ast.With)
        exact_rows(shape.body[3:7], 'current_inputs.assert_not_called()\n'
                   'current_contract.assert_not_called()\n'
                   'current_inputs.reset_mock()\ncurrent_contract.reset_mock()')
        contract = scope.body[20]
        self.assertIsInstance(contract, ast.For)
        self.assertEqual(7, len(contract.body))
        exact_rows(contract.body[3:7], 'if field == "delayed_opt_in":\n'
                   '    current_inputs.assert_called_once_with()\n'
                   'else:\n    current_inputs.assert_not_called()\n'
                   'current_contract.assert_not_called()\n'
                   'current_inputs.reset_mock()\ncurrent_contract.reset_mock()')
        integration = methods[CLI]
        self.assertEqual(5, len(integration.body))
        self.assertEqual(ast_text(selected.args), ast_text(integration.args))
        self.assertEqual([], integration.decorator_list)
        self.assertIsNone(integration.returns)
        self.assertIsNone(integration.type_comment)
        units = deepcopy(scope.body)
        units[17].body = units[17].body[:1]
        units[19].body = units[19].body[:3]
        units[20].body = units[20].body[:3]
        reconstructed = deepcopy(selected)
        reconstructed.body = (deepcopy(selected.body[:14]) + [units[0]] + units[5:11]
                              + units[15:21] + deepcopy(integration.body))
        self.assertEqual(ORIGINAL_METHOD_AST_SHA256, ast_sha(reconstructed))
        # Original32 nodes, genuine plan/validate positive, all20 command/schema
        # cases, original CLI five statements and four untouched methods survive.
        self.assertEqual(32, len(reconstructed.body))
