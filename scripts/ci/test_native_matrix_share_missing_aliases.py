# SPDX-License-Identifier: Apache-2.0
"""Finite one-hop source regression controls; zero native/controller execution."""
import ast
from pathlib import Path
import unittest

import native_matrix_declarative_aliases as reader

ROOT = Path(__file__).resolve().parents[2]
MATRIX = (ROOT / "scripts/ci/workflow_matrix.py").read_text(encoding="utf-8")
HELPER = "scripts/ci/macos_share_missing_ci.py"
UPSTREAM = "scripts/ci/macos_share_missing_only.py"
PATHS = tuple("scripts/ci/" + module + ".py" for module, _ in reader._DECLARATIONS.values()) + (HELPER, UPSTREAM)
SOURCES = {path: (ROOT / path).read_text(encoding="utf-8") for path in PATHS}
EXPECTED = {"PROFILE": "macos-share-missing-lifecycle", "MODULE": "calf-share",
            "FOCUS": "macos-share-timeout-retention-recovery"}


def aliases(matrix=MATRIX, sources=SOURCES):
    return reader.native_aliases(ast.parse(matrix), sources.__getitem__)


class NativeMatrixShareMissingAliasTests(unittest.TestCase):
    def test_current_exact_one_hop_share_alias_qualifies_all_literals_without_execution(self):
        calls = []
        def read(path):
            calls.append(path)
            return SOURCES[path] + '\nraise AssertionError("No controller execution is permitted")\n'
        actual = reader.native_aliases(ast.parse(MATRIX), read)
        self.assertIn("share_missing", actual)
        self.assertEqual(EXPECTED, vars(actual["share_missing"]))
        self.assertEqual(list(PATHS), calls)

    def test_current_share_profile_and_module_are_coherent_with_unchanged_finite_matrix(self):
        tree, actual = ast.parse(MATRIX), aliases()
        self.assertIn("share_missing", actual)
        reader.validate_literal_matrix_declarations(tree, actual)
        for field, expected in EXPECTED.items():
            self.assertEqual(expected, reader.literal_metadata(ast.parse("share_missing." + field, mode="eval").body, actual))

    def test_helper_import_missing_duplicate_wrong_from_or_reassigned_refuses(self):
        original = "import macos_share_missing_only as recovery"
        self.assertEqual(1, SOURCES[HELPER].count(original))
        for change in ("", original + "\n" + original, "import unknown_native as recovery",
                       "from macos_share_missing_only import JNI_PROFILE as recovery",
                       original + "\nrecovery = None", original + "\nrecovery.JNI_PROFILE = 'wrong'"):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                aliases(sources=dict(SOURCES, **{HELPER: SOURCES[HELPER].replace(original, change, 1)}))

    def test_only_exact_single_hop_attribute_declarations_are_admitted(self):
        for field, upstream in (("PROFILE", "JNI_PROFILE"), ("FOCUS", "JNI_FOCUS")):
            original = field + " = recovery." + upstream
            self.assertEqual(1, SOURCES[HELPER].count(original))
            for change in ("", original + "\n" + original, field + " = recovery.UNKNOWN",
                           field + " = recovery." + upstream + ".upper()",
                           field + " = recovery.alias." + upstream,
                           field + ': str = recovery.' + upstream,
                           field + ' = "' + EXPECTED[field] + '"', original + '\n' + field + ' += ""'):
                with self.subTest(field=field, change=change), self.assertRaises(AssertionError):
                    aliases(sources=dict(SOURCES, **{HELPER: SOURCES[HELPER].replace(original, change, 1)}))

    def test_forwarded_upstream_values_must_be_unique_bounded_exact_literals(self):
        for field, upstream in (("PROFILE", "JNI_PROFILE"), ("FOCUS", "JNI_FOCUS")):
            original = upstream + ' = "' + EXPECTED[field] + '"'
            self.assertEqual(1, SOURCES[UPSTREAM].count(original))
            for change in ("", original + "\n" + original, upstream + ' = "wrong"',
                           upstream + ': str = "' + EXPECTED[field] + '"',
                           upstream + ' = str("' + EXPECTED[field] + '")', original + '\n' + upstream + ' += ""'):
                with self.subTest(field=field, change=change), self.assertRaises(AssertionError):
                    aliases(sources=dict(SOURCES, **{UPSTREAM: SOURCES[UPSTREAM].replace(original, change, 1)}))
        for path in (HELPER, UPSTREAM):
            for invalid in (None, b"not text", "", "x" * (reader.MAX_DECLARATION_BYTES + 1)):
                with self.subTest(path=path, invalid=type(invalid).__name__), self.assertRaises(AssertionError):
                    aliases(sources=dict(SOURCES, **{path: invalid}))

    def test_current_matrix_import_alias_mutations_and_missing_import_refuse(self):
        original = "import macos_share_missing_ci as share_missing"
        self.assertEqual(1, MATRIX.count(original))
        for change in ("", original + "\n" + original, "import unknown_native as share_missing",
                       "from macos_share_missing_ci import PROFILE as share_missing",
                       original + "\nshare_missing = None", original + "\nshare_missing.PROFILE = 'wrong'"):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                aliases(MATRIX.replace(original, change, 1))

    def test_unknown_alias_calls_deeper_attributes_and_duplicate_profile_keys_refuse(self):
        actual = aliases()
        for expression in ("share_missing.UNKNOWN", "share_missing.PROFILE.upper", "share_missing.PROFILE.upper()",
                           "unknown_missing.PROFILE", "share_missing.PROFILE + ''", "share_missing.__dict__",
                           '{share_missing.PROFILE: "calf-share", "macos-share-missing-lifecycle": "calf-ui"}'):
            with self.subTest(expression=expression), self.assertRaises(AssertionError):
                reader.literal_metadata(ast.parse(expression, mode="eval").body, actual)

    def test_exact_historical_matrix_without_new_alias_never_reads_new_controller(self):
        from macos_share_missing_source_projection import source_before_share_missing_ci
        prior = source_before_share_missing_ci("scripts/ci/workflow_matrix.py", MATRIX.encode("utf-8"))
        tree = ast.parse(prior)
        # The exact qualified historical preimage has neither the new import nor
        # the new selection code. Merely deleting its new keys is not that image.
        paths = []
        def read(path):
            paths.append(path)
            return SOURCES[path]
        actual = reader.native_aliases(tree, read)
        self.assertEqual(set(reader._DECLARATIONS), set(actual))
        self.assertEqual(list(PATHS[:2]), paths)
        with self.assertRaises(AssertionError):
            reader.literal_metadata(ast.parse("share_missing.PROFILE", mode="eval").body, actual)


if __name__ == "__main__":
    unittest.main()
