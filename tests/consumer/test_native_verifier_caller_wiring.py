"""Finite caller/source controls and one notice fixture, never native/legal proof.

The inventory classifies every currently executable Python ArtifactVerifier call
in tests/ and scripts/. It must not silently admit a new unreviewed native owner.
Historical documentation/evidence copies are not current executable callers.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest
from unittest import mock

import test_native_license_supplements as supplements_fixture
import verify_artifacts as gate


ROOT = Path(__file__).resolve().parents[2]
NATIVE_OWNERS = {"nativecmpkit-file-picker", "nativecmpkit-share"}
NOTICE_METHODS = {
    "test_independent_notice_gate_accepts_exact_source_bound_material_only",
    "test_notice_gate_rejects_changed_external_repository",
    "test_notice_gate_rejects_missing_external_origin_record",
    "test_notice_gate_rejects_external_text_reclassified_as_archive_material",
    "test_notice_gate_rejects_self_rehashed_license_text_substitute",
    "test_notice_gate_rejects_missing_original_manifest_proof",
    "test_notice_gate_rejects_self_rehashed_catalog_provenance",
    "test_notice_gate_rejects_external_material_without_approved_catalog",
    "test_notice_gate_rejects_unrecorded_stale_provenance_material",
    "test_notice_gate_retains_fail_closed_missing_text_requirement",
}

# Keys are source, enclosing declaration, and ordinal within that declaration;
# line shifts are harmless, additional unreviewed constructors are not.
CALLER_SCOPES = {
    ("tests/consumer/test_derived_apache_notices.py", "DerivedApacheArtifactTest.verifier", 1): "nonnative",
    ("tests/consumer/test_derived_apache_notices.py", "DerivedApacheArtifactTest.verifier", 2): "nonnative",
    ("tests/consumer/test_derived_apache_notices.py", "DerivedApacheArtifactTest.test_navigation_model_identity_is_scoped_and_default_rejection_remains", 1): "invalid",
    ("tests/consumer/test_gradle_module_identity.py", "GradleOwningComponentTest.target_identity_passes", 1): "nonnative",
    ("tests/consumer/test_native_license_legacy_winapi.py", "LegacyWinapiLicenseTest.inspect_notices", 1): "material-only",
    ("tests/consumer/test_native_license_supplements.py", "VcsLicenseSupplementTest.notice_checks", 1): "native",
    ("tests/consumer/test_native_package_provenance.py", "NativePackageProvenanceTest.verifier", 1): "native",
    ("tests/consumer/test_verify_artifacts.py", "CupertinoFontResourceTest.test_owning_maven_verifier_rejects_empty_android_and_resource_archives", 1): "nonnative",
    ("tests/consumer/test_verify_artifacts.py", "RepositoryFixtureBase.run_gate", 1): "nonnative",
    ("tests/consumer/test_verify_artifacts.py", "RepositoryFixtureTest.test_candidate_dynamic_or_snapshot_versions_rejected", 1): "invalid",
    ("tests/consumer/test_verify_artifacts.py", "RepositoryFixtureTest.test_unknown_target_or_module_rejected", 1): "invalid",
    ("tests/consumer/test_verify_artifacts.py", "RepositoryFixtureTest.test_unknown_target_or_module_rejected", 2): "invalid",
    ("tests/consumer/test_verify_artifacts.py", "RepositoryFixtureTest.test_full_matrix_request_cannot_pass_partial_repository", 1): "nonnative",
    ("tests/consumer/test_verify_artifacts.py", "NativeContractFixtureTest.verifier", 1): "native",
    ("tests/consumer/verify_artifacts.py", "main", 1): "native",
    ("scripts/ci/core_io_consumer.py", "verify_static", 1): "nonnative",
    ("scripts/ci/webview_consumer.py", "run", 1): "nonnative",
}


def constructor_sites() -> dict[tuple[str, str, int], ast.Call]:
    result = {}
    for directory in ("tests", "scripts"):
        for source in sorted((ROOT / directory).rglob("*.py")):
            if any(part in {"build", "__pycache__", ".gradle"} for part in source.relative_to(ROOT).parts):
                continue
            tree = ast.parse(source.read_text())
            aliases = {"ArtifactVerifier"}
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "verify_artifacts":
                    aliases.update(item.asname or item.name for item in node.names if item.name == "ArtifactVerifier")

            class Visitor(ast.NodeVisitor):
                def __init__(self):
                    self.stack = []
                    self.ordinals = {}

                def declaration(self, node):
                    self.stack.append(node.name)
                    self.generic_visit(node)
                    self.stack.pop()

                visit_ClassDef = declaration
                visit_FunctionDef = declaration
                visit_AsyncFunctionDef = declaration

                def visit_Call(self, node):
                    literal = node.func.attr if isinstance(node.func, ast.Attribute) else (
                        node.func.id if isinstance(node.func, ast.Name) else "")
                    if literal in aliases:
                        context = ".".join(self.stack)
                        ordinal = self.ordinals.get(context, 0) + 1
                        self.ordinals[context] = ordinal
                        result[(source.relative_to(ROOT).as_posix(), context, ordinal)] = node
                    self.generic_visit(node)

            Visitor().visit(tree)
    return result


class NativeVerifierCallerWiringTest(unittest.TestCase):
    def test_native_supplement_helper_uses_independent_fixture_revision_and_default_clean_mode(self):
        sample = supplements_fixture.VcsLicenseSupplementTest()
        sample.setUp()
        self.addCleanup(sample.tearDown)
        identity = json.loads((sample.source / "docs/migration/identity.json").read_text())
        self.assertEqual({"nativecmpkit-file-picker"}, {row["new_artifact"] for row in identity["modules"]})
        entries = sample.actual_entries()
        original = gate.ArtifactVerifier
        with mock.patch.object(gate, "ArtifactVerifier", wraps=original) as constructor:
            checks = sample.notice_checks(entries)
        constructor.assert_called_once()
        keywords = constructor.call_args.kwargs
        self.assertEqual("c" * 40, keywords["expected_native_revision"])
        self.assertNotEqual(sample.revision, keywords["expected_native_revision"],
                            "Dependency VCS revision is not the native producer revision")
        self.assertNotIn("allow_dirty_native_diagnostic", keywords)
        self.assertTrue(checks)
        self.assertTrue(all(row["passed"] for row in checks), checks)

    def test_every_audited_executable_constructor_is_classified_and_native_revision_is_wired(self):
        sites = constructor_sites()
        self.assertEqual(set(CALLER_SCOPES), set(sites), "Review any new executable constructor/ownership scope")
        for identity, call in sites.items():
            if CALLER_SCOPES[identity] == "native":
                with self.subTest(site=identity):
                    self.assertIn("expected_native_revision", {keyword.arg for keyword in call.keywords})

    def test_real_nonnative_controllers_keep_explicit_non_native_module_scopes(self):
        sites = constructor_sites()
        for filename, function, constant, expected, expression in (
            ("core_io_consumer.py", "verify_static", "ROOTS", ("nativecmpkit-core", "nativecmpkit-io"), "list(ROOTS)"),
            ("webview_consumer.py", "run", "MODULE", "nativecmpkit-webview", "[MODULE]"),
        ):
            source = "scripts/ci/" + filename
            tree = ast.parse((ROOT / source).read_text())
            assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name) and target.id == constant for target in node.targets))
            declared = ast.literal_eval(assignment.value)
            self.assertEqual(expected, declared)
            self.assertFalse(NATIVE_OWNERS.intersection(declared if isinstance(declared, tuple) else [declared]))
            self.assertEqual(expression, ast.unparse(sites[(source, function, 1)].args[3]))

    def test_schema3_material_only_site_cannot_waive_original_native_revision_gates(self):
        identity = ("tests/consumer/test_native_license_legacy_winapi.py", "LegacyWinapiLicenseTest.inspect_notices", 1)
        self.assertEqual({identity}, {key for key, scope in CALLER_SCOPES.items() if scope == "material-only"})
        call = constructor_sites()[identity]
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        self.assertEqual(["nativecmpkit-file-picker"], ast.literal_eval(keywords["modules"]))
        self.assertEqual(["metadata"], ast.literal_eval(keywords["targets"]))
        self.assertEqual(["linux-x64"], ast.literal_eval(keywords["native_platforms"]))
        self.assertNotIn("expected_native_revision", keywords)  # No fabricated native producer claim.
        source = ast.parse((ROOT / identity[0]).read_text())
        owner = next(node for node in ast.walk(source) if isinstance(node, ast.FunctionDef)
                     and node.name == "inspect_notices")
        calls = [node for node in ast.walk(owner) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == "inspector"]
        self.assertEqual(["native_notices"], [node.func.attr for node in calls])
        returned = [ast.unparse(node.value) for node in ast.walk(owner) if isinstance(node, ast.Return)]
        self.assertEqual(["inspector.checks"], returned)
        self.assertEqual("native", CALLER_SCOPES[("tests/consumer/verify_artifacts.py", "main", 1)])

    def test_actual_cli_passes_independent_revision_and_explicit_diagnostic_fields(self):
        source = (ROOT / "tests/consumer/verify_artifacts.py").read_text()
        tree = ast.parse(source)
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        call = next(node for node in ast.walk(main) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name) and node.func.id == "ArtifactVerifier")
        keywords = {keyword.arg: ast.unparse(keyword.value) for keyword in call.keywords}
        self.assertEqual("args.expected_native_revision", keywords["expected_native_revision"])
        self.assertEqual("args.allow_dirty_native_diagnostic", keywords["allow_dirty_native_diagnostic"])
        flags = {argument.value for node in ast.walk(main) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
                 for argument in node.args if isinstance(argument, ast.Constant) and isinstance(argument.value, str)}
        self.assertIn("--expected-native-revision", flags)
        self.assertIn("--allow-dirty-native-diagnostic", flags)

    def test_changed_notice_helper_reaches_exact_original_ten_methods_only(self):
        tree = ast.parse((ROOT / "tests/consumer/test_native_license_supplements.py").read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "VcsLicenseSupplementTest")
        methods = {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef)}

        def reaches(name, seen=frozenset()):
            if name == "notice_checks":
                return True
            if name in seen or name not in methods:
                return False
            calls = {node.func.attr for node in ast.walk(methods[name]) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                     and node.func.value.id == "self"}
            return any(reaches(call, seen | {name}) for call in calls)

        tests = {name for name in methods if name.startswith("test_")}
        self.assertEqual(50, len(tests))
        self.assertEqual(NOTICE_METHODS, {name for name in tests if reaches(name)})
        self.assertEqual(40, len(tests - NOTICE_METHODS))


if __name__ == "__main__":
    unittest.main()
