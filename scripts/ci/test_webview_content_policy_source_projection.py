# SPDX-License-Identifier: Apache-2.0
"""NEW exact WebView source custody only; no historical test/compiler/native replay."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import android_external328_source_projection as bridge
import ios_ui_related_source_projection as ui
import macos_share_missing_source_projection as share
import webview_content_policy_native_focus as policy
import webview_content_policy_source_projection as history
import camera_ios_ownership_source_projection as camera_history

ROOT = Path(__file__).resolve().parents[2]
GUARD_SHA256 = "c8b75a6b06454135db4b6143987855e27588648d4eb3aefc0d72611fc35ac875"
UI_GUARD_SHA256 = "b6e5bdc9cfd8b86117292d325419acdf4ad2fc7052559a8acdbcc3e8cfbf379e"
UI_SPEC_SHA256 = "5511b49eb4e164735508ccb596013a7ac59a3dadfe8adf2ce2acac710a2393f8"
UI_SHARE_GUARD_SHA256 = "19b33c0174e52ab85e603f6f0c7be45dd5b83cff93b278a2430c527692cc1c53"
SHARE_GUARD_SHA256 = "0b1f39f890df7cdb68db70d027b23340c2da1dd234b4387f68f2c8be41d8d3ad"
SHARE_SPEC_SHA256 = "79fa2b0394b10026402bef72992385c38684f19b70414606ed1833b40e3178b9"
UNCHANGED_EXECUTABLE_KEYSET_SHA256 = "b62d4e1c1cad872f790ef47a8ad9ac7359ddee6a978d4d0fa777c291ac22647e"
FIXTURE648_SHA256 = "75b52cd2abc6816bb23e02c01d89b7c5cade3219e737b18a9fe2ca17fd25c550"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture_inputs():
    document = history._document()
    return {history.SOURCE_RELATIVE, history.SPEC_RELATIVE, "scripts/ci/test_webview_content_policy_source_projection.py",
            *document["bindings"], *document["added_inputs"], *document["unchanged_inputs"]} | camera_history.fixture_inputs()


def copy_fixture(root):
    for name in fixture_inputs():
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((ROOT / name).read_bytes())


class WebViewContentPolicySourceProjectionControls(unittest.TestCase):
    def test_only_maintainer_instructions_are_not_executable_inputs_or_fixture_prerequisites(self):
        document = history._document()
        for group in ("bindings", "added_inputs", "unchanged_inputs"):
            self.assertNotIn("AGENTS.md", document[group])
        self.assertEqual(frozenset({"AGENTS.md"}), history.NONEXECUTABLE_MAINTAINER_INPUTS)
        self.assertNotIn("AGENTS.md", history.fixture_inputs())
        self.assertNotIn("AGENTS.md", fixture_inputs())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_fixture(root)
            from ios_popover_anchor_plan import _ordinary_bytes
            def executable_only(checkout, relative):
                if relative == "AGENTS.md":
                    raise AssertionError("Maintainer instructions must never be opened by an executable source guard")
                return _ordinary_bytes(checkout, relative)
            for instructions in (None, b"# unrelated maintainer update\n", b"arbitrary nonexecutable instructions\x00\xff"):
                if instructions is not None:
                    (root / "AGENTS.md").write_bytes(instructions)
                with patch("ios_popover_anchor_plan._ordinary_bytes", side_effect=executable_only):
                    self.assertTrue(history.validate_current_sources(root))
                    self.assertTrue(share.validate_current_sources(root))
                    self.assertTrue(ui.validate_current_sources(root))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            bad = copy.deepcopy(document); bad["unchanged_inputs"]["AGENTS.md"] = "a" * 64
            candidate = json.dumps(bad).encode(); path.write_bytes(candidate)
            with patch.object(history, "SPEC_PATH", path), patch.object(history, "SPEC_SHA256", sha(candidate)):
                with self.assertRaises(ValueError): history._document()

    def test_exact_reviewed648_predecessor_and_every_other_owned_input_remain_required(self):
        document = history._document()
        fixture = "scripts/ci/test_webview_content_policy_fixture.py"
        self.assertEqual(FIXTURE648_SHA256, document["unchanged_inputs"][fixture])
        self.assertEqual(FIXTURE648_SHA256, sha((ROOT / fixture).read_bytes()))
        self.assertEqual(149, len(document["unchanged_inputs"]))
        self.assertEqual(UNCHANGED_EXECUTABLE_KEYSET_SHA256,
                         sha(("\n".join(sorted(document["unchanged_inputs"])) + "\n").encode()))
        # Exact reviewed lead648 is the predecessor, not a waiver for unknown
        # fixtures or other docs, production, dependencies, guards or new inputs.
        representatives = (
            fixture, "docs/testing/webview-content-policy.md", "gradle/libs.versions.toml",
            "calf-webview/src/commonMain/kotlin/com.mohamedrejeb.calf/ui/web/WebView.kt",
            "scripts/ci/android_external328_source_projection.py", "scripts/ci/library_tests.py",
            "calf-webview/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/ui/web/AndroidContentPolicyVerificationFilter.kt",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_fixture(root)
            (root / "AGENTS.md").write_bytes(b"another unrelated maintainer update\n")
            self.assertTrue(history.validate_current_sources(root))
            for name in representatives:
                with self.subTest(owned_input=name):
                    target = root / name; raw = target.read_bytes(); target.write_bytes(raw + b"\n")
                    with self.assertRaisesRegex(ValueError, re.escape(name)):
                        history.validate_current_sources(root)
                    target.unlink()
                    with self.assertRaises(FileNotFoundError): history.validate_current_sources(root)
                    target.write_bytes(raw)
            self.assertTrue(history.validate_current_sources(root))

    def test_eight_complete_share_root_routing_images_preserve_all_ecff_bytes_and_finite_unique_fragments(self):
        document = history._document()
        self.assertEqual(8, len(document["bindings"]))
        self.assertEqual(33, sum(len(row["fragments"]) for row in document["bindings"].values()))
        self.assertEqual(GUARD_SHA256, sha(camera_history.source_before_camera_ios_ownership(history.SOURCE_RELATIVE, (ROOT / history.SOURCE_RELATIVE).read_bytes())))
        self.assertEqual(history.SPEC_SHA256, sha((ROOT / history.SPEC_RELATIVE).read_bytes()))
        for name, row in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes(); prior = history.current_source_before_content_policy(name, raw_current)
            raw = camera_history.source_before_camera_ios_ownership(name, raw_current)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(raw), len(raw)))
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(prior), len(prior)))
            self.assertIs(prior, history.source_before_content_policy(name, prior))
            forward = prior
            for fragment in row["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before)); self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, forward.count(before)); forward = forward.replace(before, after, 1)
            self.assertEqual(raw, forward)

    def test_latest_raw_ingress_refuses_old_partial_displaced_foreign_and_unbounded_images_before_older_share(self):
        for name in history.BOUND_PATHS:
            raw = (ROOT / name).read_bytes(); prior = history.source_before_content_policy(name, raw)
            fragment = history._document()["bindings"][name]["fragments"][0]["after"].encode()
            displaced = raw.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(raw, displaced)
            other = (ROOT / next(path for path in history.BOUND_PATHS if path != name)).read_bytes()
            for candidate in (prior, raw[:-1], raw + b"\n", displaced, other, b"", None, raw.decode(), bytearray(raw), b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with patch.object(share, "source_before_share_missing_ci", side_effect=AssertionError("Unqualified WebView raw crossed Share ingress")) as older:
                    with self.assertRaises(ValueError): share.current_source_before_share_missing_ci(name, candidate)
                    older.assert_not_called()

    def test_one_actual_checkout_webview_ingress_precedes_only_exact_share_ui_and_older_ancestors(self):
        for name in history.BOUND_PATHS:
            raw = (ROOT / name).read_bytes()
            with patch.object(history, "current_source_before_content_policy", wraps=history.current_source_before_content_policy) as newest:
                ancestor = history.read_current_source_for_history(ROOT / name, ROOT)
                newest.assert_called_once_with(name, raw)
                self.assertIsInstance(ancestor, bytes)
        source = (ROOT / "scripts/ci/macos_share_missing_source_projection.py").read_text()
        self.assertEqual(1, source.count("from webview_content_policy_source_projection import current_source_before_content_policy"))
        self.assertEqual(2, source.count("from webview_content_policy_source_projection import peel_content_policy_for_history"))

    def test_nested_history_is_exact_idempotent_and_unknown_bytes_are_not_current_certificates(self):
        for name in history.BOUND_PATHS:
            raw = (ROOT / name).read_bytes(); prior = history.source_before_content_policy(name, raw)
            self.assertEqual(prior, history.peel_content_policy_for_history(name, raw))
            self.assertIs(prior, history.peel_content_policy_for_history(name, prior))
            unknown = prior + b"\n# source-model unknown ancestor\n"
            self.assertIs(unknown, history.peel_content_policy_for_history(name, unknown))
            with self.assertRaises(ValueError): history.current_source_before_content_policy(name, prior)
            with self.assertRaises(ValueError): history.current_source_before_content_policy(name, unknown)
            with self.assertRaises(ValueError): history.source_before_content_policy(name, unknown)
        unlisted = b"unlisted bytes are not certified or executed"
        for reader in (history.source_before_content_policy, history.current_source_before_content_policy, history.peel_content_policy_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
            with self.assertRaises(ValueError): reader(Path("unlisted-source"), unlisted)

    def test_manifest_complete_schema_hash_duplicate_keys_and_fragment_identity_refuse_drift(self):
        raw = (ROOT / history.SPEC_RELATIVE).read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            for candidate in (raw + b"\n", b'{"schema_version":1,"schema_version":1}', b"{}", b"[]"):
                path.write_bytes(candidate)
                with patch.object(history, "SPEC_PATH", path):
                    with self.assertRaises(ValueError): history._document()
            document = json.loads(raw)
            for mutate in (lambda value: value.update(schema_version=True), lambda value: value.update(scope="native acceptance"),
                           lambda value: value["bindings"].pop(next(iter(value["bindings"]))),
                           lambda value: value["added_inputs"].update({"foreign.kt": "a" * 64})):
                bad = copy.deepcopy(document); mutate(bad); candidate = json.dumps(bad).encode(); path.write_bytes(candidate)
                with patch.object(history, "SPEC_PATH", path), patch.object(history, "SPEC_SHA256", sha(candidate)):
                    with self.assertRaises(ValueError): history._document()
        name = "scripts/ci/library_tests.py"; document = history._document(); document = copy.deepcopy(document)
        document["bindings"][name]["fragments"][0]["after_fragment_sha256"] = "a" * 64
        with patch.object(history, "_document", return_value=document):
            with self.assertRaises(ValueError): history.source_before_content_policy(name, (ROOT / name).read_bytes())

    def test_current_validator_requires_every_new_input_and_exact_raw_images_not_reconstructed_parents(self):
        self.assertTrue(history.validate_current_sources(ROOT)); self.assertTrue(share.validate_current_sources(ROOT)); self.assertTrue(ui.validate_current_sources(ROOT))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_fixture(root)
            self.assertTrue(history.validate_current_sources(root)); self.assertTrue(share.validate_current_sources(root)); self.assertTrue(ui.validate_current_sources(root))
            for name in history.ADDED_PATHS:
                target = root / name; raw = target.read_bytes(); target.unlink()
                with self.assertRaises(FileNotFoundError): history.validate_current_sources(root)
                target.write_bytes(raw + b"\n")
                with self.assertRaises(ValueError): history.validate_current_sources(root)
                target.write_bytes(raw)
            name = "scripts/ci/library_tests.py"; target = root / name; raw = target.read_bytes()
            target.write_bytes(history.source_before_content_policy(name, raw))
            with self.assertRaises(ValueError): history.validate_current_sources(root)
            with self.assertRaises(ValueError): share.validate_current_sources(root)
            with self.assertRaises(ValueError): ui.validate_current_sources(root)

    def test_ordinary_checkout_reader_refuses_foreign_symlink_hardlink_alias_and_relative_paths(self):
        name = "scripts/ci/library_tests.py"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); copy_fixture(root); target = root / name; raw = target.read_bytes()
            target.unlink(); target.symlink_to(ROOT / name)
            with self.assertRaises(ValueError): history.read_current_source_for_history(target, root)
            target.unlink(); backing = target.with_name("backing.py"); backing.write_bytes(raw); target.hardlink_to(backing)
            with self.assertRaises(ValueError): history.read_current_source_for_history(target, root)
            with self.assertRaises(ValueError): history.read_current_source_for_history(ROOT / name, root)
            with self.assertRaises(ValueError): history.read_current_source_for_history(Path(name), root)
            alias = root / "alias"; alias.symlink_to(ROOT, target_is_directory=True)
            with self.assertRaises(ValueError): history.read_current_source_for_history(alias / name, alias)

    def test_original_share_ui_manifests_guard_pins_control_assertions_and_unaffected_methods_remain_exact(self):
        self.assertEqual(UI_SPEC_SHA256, sha((ROOT / ui.SPEC_RELATIVE).read_bytes()))
        self.assertEqual(SHARE_SPEC_SHA256, sha((ROOT / share.SPEC_RELATIVE).read_bytes()))
        ui_guard = (ROOT / "scripts/ci/ios_ui_related_source_projection.py").read_bytes()
        self.assertEqual(UI_SHARE_GUARD_SHA256, sha(ui_guard))
        self.assertEqual(UI_GUARD_SHA256, sha(share.source_before_share_missing_ci("scripts/ci/ios_ui_related_source_projection.py", ui_guard)))
        self.assertEqual(SHARE_GUARD_SHA256, sha(history.source_before_content_policy("scripts/ci/macos_share_missing_source_projection.py", (ROOT / "scripts/ci/macos_share_missing_source_projection.py").read_bytes())))
        affected = {
            "scripts/ci/test_ios_ui_related_source_projection.py": {"test_original_application_launch_argv_deadlines_finally_sdk_and_native_bodies_are_unchanged"},
            "scripts/ci/test_macos_share_missing_source_projection.py": {"test_exact_six_path_inverse_roundtrip_and_one_newest_raw_ingress", "test_only_transparent_ui_history_hooks_and_narrow_fixture_operands_change"},
        }
        from ios_ui_split664_source_projection import current_source_before_ui_split664
        for name, changed in affected.items():
            raw = (ROOT / name).read_bytes()
            if name == "scripts/ci/test_ios_ui_related_source_projection.py":
                raw = current_source_before_ui_split664(name, raw)
            prior = history.source_before_content_policy(name, raw)
            old = {node.name: node for node in ast.walk(ast.parse(prior)) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            new = {node.name: node for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")}
            self.assertEqual(set(old), set(new))
            for method in set(old) - changed:
                self.assertEqual(ast.dump(old[method], include_attributes=False), ast.dump(new[method], include_attributes=False))
            for method in changed:
                def assertions(node):
                    return [ast.unparse(child.func) for child in ast.walk(node) if isinstance(child, ast.Call) and
                            isinstance(child.func, ast.Attribute) and child.func.attr.startswith("assert")]
                self.assertEqual(assertions(old[method]), assertions(new[method]))
        self.assertIn('GUARD_SHA256 = "' + UI_GUARD_SHA256 + '"', (ROOT / "scripts/ci/test_ios_ui_related_source_projection.py").read_text())
        self.assertIn('GUARD_SHA256 = "' + SHARE_GUARD_SHA256 + '"', (ROOT / "scripts/ci/test_macos_share_missing_source_projection.py").read_text())
        self.assertEqual((9, 36), (len(ui._document()["bindings"]), sum(len(row["fragments"]) for row in ui._document()["bindings"].values())))
        self.assertEqual(6, len(share._document()["bindings"]))

    def test_only_transparent_webview_hooks_and_finite_fixture_union_extend_exact_share_guard(self):
        name = "scripts/ci/macos_share_missing_source_projection.py"; raw = (ROOT / name).read_bytes()
        prior = history.source_before_content_policy(name, raw)
        class TransparentWebViewHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "webview_content_policy_source_projection" else node
            def visit_Import(self, node):
                return None if ast.unparse(node) == "import webview_content_policy_source_projection as content_history" else node
            def visit_Expr(self, node):
                return None if ast.unparse(node) == "content_history.validate_current_sources(root)" else self.generic_visit(node)
            def visit_Assign(self, node):
                if (len(node.targets) == 1 and ast.unparse(node.targets[0]) == "payload" and isinstance(node.value, ast.Call) and
                        ast.unparse(node.value.func) in {"peel_content_policy_for_history", "current_source_before_content_policy"}):
                    if [ast.unparse(arg) for arg in node.value.args] != ["relative", "payload"] or node.value.keywords:
                        raise AssertionError("Only exact binary source ingress hooks are allowed")
                    return None
                return self.generic_visit(node)
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if ast.unparse(node.func) == "content_history.source_before_content_policy":
                    if len(node.args) != 2 or node.keywords or ast.unparse(node.args[0]) != "name":
                        raise AssertionError("Only the owning exact current hash operand changes")
                    return node.args[1]
                return node
            def visit_BinOp(self, node):
                node = self.generic_visit(node)
                if isinstance(node.op, ast.BitOr) and isinstance(node.right, ast.Call) and ast.unparse(node.right.func) == "content_fixture_inputs":
                    if node.right.args or node.right.keywords:
                        raise AssertionError("Only the finite owning source fixture export is allowed")
                    return node.left
                return node
        self.assertEqual(ast.dump(ast.parse(prior), include_attributes=False),
                         ast.dump(TransparentWebViewHooks().visit(ast.parse(raw)), include_attributes=False))
        self.assertTrue(history.fixture_inputs() <= share.fixture_inputs())
        from test_ios_ui_related_source_projection import fixture_inputs as ui_fixture_inputs
        self.assertTrue(share.fixture_inputs() <= ui_fixture_inputs())
        self.assertFalse(history.BOUND_PATHS & {"scripts/ci/ios_ui_related_source_projection.py", ui.SPEC_RELATIVE, share.SPEC_RELATIVE})

    def test_every_original_webview_native_and_fixture_body_api_build_dependency_and_other_owners_remain_unchanged(self):
        document = history._document()
        for name, digest in document["unchanged_inputs"].items():
            self.assertEqual(digest, sha(camera_history.source_before_camera_ios_ownership(
                name, (ROOT / name).read_bytes())), name)
        self.assertTrue(set(policy.SOURCE_SHA256) - {policy.ANDROID_FILTER_SOURCE} <= set(document["unchanged_inputs"]))
        self.assertNotIn("AGENTS.md", history.BOUND_PATHS)
        self.assertNotIn("scripts/ci/runtime_context.py", history.BOUND_PATHS)
        self.assertNotIn("scripts/ci/android_external328_source_projection.py", history.BOUND_PATHS)
        self.assertFalse(any(name.startswith("calf-share/") or name.startswith("calf-ui/") for name in history.BOUND_PATHS))
        classes = {policy.spec(focus)["classname"]: policy.spec(focus)["source"] for focus in policy.FOCUSES}
        self.assertEqual(4, len(classes))
        self.assertEqual(14, sum(len(policy._METHOD.findall((ROOT / name).read_text())) for name in classes.values()))
