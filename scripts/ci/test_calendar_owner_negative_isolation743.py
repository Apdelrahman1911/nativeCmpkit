# SPDX-License-Identifier: Apache-2.0
"""NEW bounded source/AST control; no Calendar method, source validator or native IO."""
import ast
import copy
import hashlib
from pathlib import Path
import unittest

from macos_share_appkit_only_source_projection import ordinary_bytes

ROOT = Path(__file__).resolve().parents[2]
TARGET = "scripts/ci/test_calendar_share_selector_source_projection.py"
TARGET_SHA256 = "9583701bdc13a0b5903c57c795f142c369b5b8c08bf50a173a17b806c17bde3e"
TARGET_BYTES = 15715
BASELINE_METHOD_AST_SHA256 = "2b17fd7bd3b9922ebc7105b2de19bd50cd4deeb8032bb9ec2df7bd85f18fafc8"
OWNER_CLASS = "CalendarShareSelectorSourceControls"
OWNER_METHOD = "test_owning_validator_requires_all_four_added_inputs_and_ordinary_current_images"


def _call(node, owner, member, arguments):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == owner
            and node.func.attr == member and not node.keywords
            and len(node.args) == len(arguments)
            and all(isinstance(value, ast.Name) and value.id == name
                    for value, name in zip(node.args, arguments)))


class CalendarOwnerNegativeIsolation743Controls(unittest.TestCase):
    def test_NEW_one_genuine_positive_and_twenty_owner_local_negative_obligations(self):
        raw = ordinary_bytes(ROOT, TARGET, 65536)[0]
        self.assertEqual((TARGET_SHA256, TARGET_BYTES), (hashlib.sha256(raw).hexdigest(), len(raw)))
        tree = ast.parse(raw, filename=TARGET)
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == OWNER_CLASS]
        self.assertEqual(1, len(classes))
        methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == OWNER_METHOD]
        self.assertEqual(1, len(methods))
        method = methods[0]
        fixtures = [n for n in ast.walk(method) if isinstance(n, ast.With)
                    and any(isinstance(i.context_expr, ast.Call)
                            and isinstance(i.context_expr.func, ast.Attribute)
                            and isinstance(i.context_expr.func.value, ast.Name)
                            and i.context_expr.func.value.id == "tempfile"
                            and i.context_expr.func.attr == "TemporaryDirectory"
                            and any(k.arg == "prefix" and isinstance(k.value, ast.Constant)
                                    and k.value.value == "nativecmpkit-selectors617-"
                                    for k in i.context_expr.keywords) for i in n.items)]
        self.assertEqual(1, len(fixtures))
        fixture = fixtures[0]
        patches = [n for n in ast.walk(method) if isinstance(n, ast.With)
                   and any(isinstance(i.optional_vars, ast.Name) and i.optional_vars.id == "downstream" for i in n.items)]
        self.assertEqual(1, len(patches))
        negative = patches[0]
        self.assertIn(negative, fixture.body)
        self.assertEqual(1, len(negative.items))
        patch_call = negative.items[0].context_expr
        self.assertIsInstance(patch_call, ast.Call)
        self.assertIsInstance(patch_call.func, ast.Attribute)
        self.assertIsInstance(patch_call.func.value, ast.Name)
        self.assertEqual(("patch", "object"), (patch_call.func.value.id, patch_call.func.attr))
        self.assertEqual(2, len(patch_call.args))
        self.assertIsInstance(patch_call.args[0], ast.Name)
        self.assertEqual("image_history", patch_call.args[0].id)
        self.assertIsInstance(patch_call.args[1], ast.Constant)
        self.assertEqual("validate_current_sources", patch_call.args[1].value)
        self.assertEqual(1, len(patch_call.keywords))
        self.assertEqual("return_value", patch_call.keywords[0].arg)
        self.assertIsInstance(patch_call.keywords[0].value, ast.Constant)
        self.assertIs(True, patch_call.keywords[0].value.value)
        positive = [n for n in fixture.body if isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Call)
                    and isinstance(n.value.func, ast.Attribute)
                    and isinstance(n.value.func.value, ast.Name)
                    and n.value.func.value.id == "self" and n.value.func.attr == "assertTrue"
                    and len(n.value.args) == 1
                    and _call(n.value.args[0], "selectors", "validate_current_sources", ("root",))]
        self.assertEqual(1, len(positive))
        self.assertLess(fixture.body.index(positive[0]), fixture.body.index(negative))
        calls = [n for n in ast.walk(method) if _call(n, "selectors", "validate_current_sources", ("root",))]
        negative_calls = [n for n in ast.walk(negative) if _call(n, "selectors", "validate_current_sources", ("root",))]
        self.assertEqual(6, len(calls))
        self.assertEqual(5, len(negative_calls))
        self.assertEqual(2, len(negative.body))
        self.assertTrue(all(isinstance(n, ast.For) for n in negative.body))
        self.assertEqual(["document['added_inputs']", "document['bindings']"],
                         [ast.unparse(n.iter) for n in negative.body])
        assertion_pairs = 0
        exception_names = []
        for loop in negative.body:
            for index, node in enumerate(loop.body):
                if not isinstance(node, ast.With):
                    continue
                validators = [n for n in ast.walk(node) if _call(n, "selectors", "validate_current_sources", ("root",))]
                if not validators:
                    continue
                self.assertEqual(1, len(validators))
                self.assertEqual(1, len(node.items))
                assertion = node.items[0].context_expr
                self.assertIsInstance(assertion, ast.Call)
                self.assertIsInstance(assertion.func, ast.Attribute)
                self.assertIsInstance(assertion.func.value, ast.Name)
                self.assertEqual(("self", "assertRaises"), (assertion.func.value.id, assertion.func.attr))
                self.assertEqual(1, len(assertion.args))
                self.assertIsInstance(assertion.args[0], ast.Name)
                exception_names.append(assertion.args[0].id)
                self.assertIsInstance(loop.body[index + 1], ast.Expr)
                self.assertIsInstance(loop.body[index + 2], ast.Expr)
                self.assertTrue(_call(loop.body[index + 1].value, "downstream", "assert_called_once_with", ("root",)))
                self.assertTrue(_call(loop.body[index + 2].value, "downstream", "reset_mock", ()))
                assertion_pairs += 1
        self.assertEqual(5, assertion_pairs)
        self.assertEqual(["FileNotFoundError", "ValueError", "ValueError", "ValueError", "ValueError"], exception_names)
        self.assertEqual(5, len([n for n in ast.walk(negative) if _call(n, "downstream", "assert_called_once_with", ("root",))]))
        self.assertEqual(5, len([n for n in ast.walk(negative) if _call(n, "downstream", "reset_mock", ())]))
        # Removing only the specifically asserted scaffold must recover the exact
        # original C9 method AST: all16+4 refusals, real FS/hash/peeling/manifest
        # operations, untouched genuine positive, and cleanup/restoration bodies.
        class RemoveApprovedScaffold(ast.NodeTransformer):
            def visit_With(self, node):
                if any(isinstance(i.optional_vars, ast.Name) and i.optional_vars.id == "downstream" for i in node.items):
                    return [self.visit(n) for n in node.body]
                return self.generic_visit(node)

            def visit_Expr(self, node):
                if (_call(node.value, "downstream", "assert_called_once_with", ("root",))
                        or _call(node.value, "downstream", "reset_mock", ())):
                    return None
                return self.generic_visit(node)

        restored = RemoveApprovedScaffold().visit(copy.deepcopy(method))
        observed = hashlib.sha256(ast.dump(restored, annotate_fields=True, include_attributes=False).encode()).hexdigest()
        self.assertEqual(BASELINE_METHOD_AST_SHA256, observed)


if __name__ == "__main__":
    unittest.main()
