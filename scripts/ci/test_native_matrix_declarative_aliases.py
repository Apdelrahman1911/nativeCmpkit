# SPDX-License-Identifier: Apache-2.0
"""Affected declarative-ingress regressions; zero SDK/compiler/native execution."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest

import native_matrix_declarative_aliases as reader

ROOT = Path(__file__).resolve().parents[2]
MATRIX = (ROOT / "scripts/ci/workflow_matrix.py").read_text(encoding="utf-8")
SOURCES = {"scripts/ci/" + module + ".py": (ROOT / ("scripts/ci/" + module + ".py")).read_text(encoding="utf-8")
           for module, _ in reader._DECLARATIONS.values()}


def aliases(matrix=MATRIX, sources=SOURCES):
    return reader.native_aliases(ast.parse(matrix), sources.__getitem__)


def declaration(tree, name):
    return next(node.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))


class NativeMatrixDeclarativeAliasTests(unittest.TestCase):
    def test_both_exact_aliases_read_actual_literals_without_executing_helper_bodies(self):
        paths = []
        def read(path):
            paths.append(path)
            return SOURCES[path] + '\nraise AssertionError("Native controller code must not execute")\n'
        actual = reader.native_aliases(ast.parse(MATRIX), read)
        self.assertEqual(list(SOURCES), paths)
        for alias, (_, expected) in reader._DECLARATIONS.items():
            self.assertEqual(expected, vars(actual[alias]))

    def test_current_all_slots_and_both_native_profile_modules_remain_coherent(self):
        tree, actual = ast.parse(MATRIX), aliases()
        reader.validate_literal_matrix_declarations(tree, actual)
        profiles = declaration(tree, "PROFILES")
        rows = {reader.literal_metadata(key, actual): value for key, value in zip(profiles.keys, profiles.values)}
        modules = reader.literal_metadata(declaration(tree, "MODULE_SUBSETS"), actual)
        self.assertEqual(("ios-iphone",), reader.literal_metadata(rows[actual["calendar_native"].PROFILE], actual))
        self.assertEqual(("desktop-macos-arm64",), reader.literal_metadata(rows[actual["macos_share_native"].PROFILE], actual))
        for alias in actual.values():
            self.assertEqual(alias.MODULE, modules[alias.PROFILE])
        self.assertEqual(11, len(reader.literal_metadata(declaration(tree, "SLOTS"), actual)))

    def test_unknown_alias_attribute_nested_access_and_calls_refuse_without_execution(self):
        actual = aliases()
        for expression in ("unknown_native.PROFILE", "calendar_native.UNKNOWN", "calendar_native.PROFILE.upper",
                           "calendar_native.__dict__", "calendar_native.PROFILE.upper()", "profile_name",
                           "__import__('os').system('false')", "calendar_native.PROFILE + ''", "{**calendar_native}"):
            with self.subTest(expression=expression), self.assertRaises(AssertionError):
                reader.literal_metadata(ast.parse(expression, mode="eval").body, actual)

    def test_missing_duplicate_dynamic_annotated_and_wrong_constants_refuse_for_both_helpers(self):
        for alias, (module, expected) in reader._DECLARATIONS.items():
            path = "scripts/ci/" + module + ".py"
            for name, value in expected.items():
                assignment = name + ' = "' + value + '"'
                for change in ("", assignment + "\n" + assignment, name + ' = str("' + value + '")',
                               name + ': str = "' + value + '"', name + ' = "wrong"',
                               assignment + '\n' + name + ' += ""'):
                    source = SOURCES[path]
                    self.assertEqual(1, source.count(assignment))
                    changed = dict(SOURCES, **{path: source.replace(assignment, change, 1)})
                    with self.subTest(alias=alias, name=name, change=change), self.assertRaises(AssertionError):
                        aliases(sources=changed)

    def test_wrong_missing_duplicate_or_from_imports_and_alias_reassignments_refuse(self):
        for alias, (module, _) in reader._DECLARATIONS.items():
            exact = "import " + module + " as " + alias
            for changed in ("", exact + "\n" + exact, "import unknown_native as " + alias,
                            "from " + module + " import PROFILE as " + alias,
                            exact + "\n" + alias + " = None", exact + "\n" + alias + ".PROFILE = 'wrong'"):
                with self.subTest(alias=alias, changed=changed), self.assertRaises(AssertionError):
                    aliases(MATRIX.replace(exact, changed, 1))

    def test_fake_alias_values_missing_helpers_and_unbounded_sources_do_not_supply_metadata(self):
        actual = aliases()
        for alias in actual:
            bad = deepcopy(actual)
            bad[alias] = SimpleNamespace(PROFILE="unqualified", MODULE="calf-share", FOCUS="wrong")
            with self.subTest(alias=alias), self.assertRaises(AssertionError):
                reader.literal_metadata(ast.parse(alias + ".PROFILE", mode="eval").body, bad)
        for invalid in (None, b"not text", "", "x" * (reader.MAX_DECLARATION_BYTES + 1)):
            with self.subTest(invalid=type(invalid).__name__), self.assertRaises(AssertionError):
                reader.native_aliases(ast.parse(MATRIX), lambda _: invalid)
        with self.assertRaises(KeyError):
            reader.native_aliases(ast.parse(MATRIX), {}.__getitem__)

    def test_duplicate_literal_and_aliased_mapping_keys_never_silently_collapse(self):
        actual = aliases()
        for expression in ('{"same": 1, "same": 2}',
                           '{calendar_native.PROFILE: "calf-permissions/calendar", "permissions-ios-calendar-configuration": "calf-share"}',
                           '{macos_share_native.PROFILE: "calf-share", macos_share_native.PROFILE: "calf-ui"}'):
            with self.subTest(expression=expression), self.assertRaises(AssertionError):
                reader.literal_metadata(ast.parse(expression, mode="eval").body, actual)

    def test_unknown_declaration_expressions_and_changed_all_generator_refuse_before_old_execution(self):
        exact = '"android-permission-demo": ("android-device-api35",),'
        for changed in ('"android-permission-demo": unknown_native.PROFILE,',
                        '"android-permission-demo": tuple(["android-device-api35"]),',
                        exact + "\n    " + exact):
            matrix = MATRIX.replace(exact, changed, 1)
            with self.subTest(changed=changed), self.assertRaises(AssertionError):
                reader.validate_literal_matrix_declarations(ast.parse(matrix), aliases(matrix))
        tree = ast.parse(MATRIX)
        profiles = declaration(tree, "PROFILES")
        index = next(i for i, key in enumerate(profiles.keys) if isinstance(key, ast.Constant) and key.value == "all")
        profiles.values[index] = ast.parse('tuple(slot["slot"] for slot in SLOTS if True)', mode="eval").body
        with self.assertRaises(AssertionError):
            reader.validate_literal_matrix_declarations(tree, aliases())


if __name__ == "__main__":
    unittest.main()
