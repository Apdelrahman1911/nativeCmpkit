# SPDX-License-Identifier: Apache-2.0
"""Essential NEW final659 binding/ingress controls; no accepted-population replay."""
from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ci_source_recovery740_742 as recovery
import camera_ios_ownership_source_projection as camera
import platform_recovery659_source_projection as newest
import webview_content_policy_source_projection as content_history
import webview_current_contract667_source_projection as contract_history

ROOT = Path(__file__).resolve().parents[2]
IMAGE_CONTROL = "scripts/ci/test_apple_image_launcher_source_projection.py"
CAMERA4697_GUARD_SHA256 = "3b1d14ca28edcca507a645b301f577ce845161172bd9f28f6d354e5ccc9eebdc"
WEBVIEW4697_GUARD_SHA256 = "cc3f7cb7099e744d08db6273194c6bcf586613521d0c8fae7757d3defa4af878"
WEBVIEW659_GUARD_SHA256 = "bb0b63b32a41667c0c33401f44873bd20426524ece52caaa3cfa41ffd880f60d"
CAMERA651_SPEC_SHA256 = "90844a99910a622024f769dd16ffe504308e1a94324d9192e406cda681e680bd"
WEBVIEW874_SPEC_SHA256 = "c44400087570740d3248704c2165c3222229f2c05ff1a2a3840dbda9aa04b916"


def function(tree, name):
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("One exact top-level source function is required")
    return matches[0]


def copy_fixture(root):
    for name in content_history.fixture_inputs() | recovery.dependency_inputs():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())


class PlatformRecovery659SourceProjectionControls(unittest.TestCase):
    def setUp(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("An outer source control cannot execute external processes")
        for name in ("run", "Popen"):
            control = patch.object(subprocess, name, forbidden)
            control.start()
            self.addCleanup(control.stop)

    def test_one_complete_outer_inverse_restores4697_and_rejects_old_partial_displaced_foreign_and_type_drift(self):
        document = newest._document()
        self.assertEqual("4697c3ec65427a12e53645ecffac5e2b52821dd5", document["predecessor"])
        self.assertEqual(20, len(document["bindings"]))
        self.assertEqual(newest.BOUND_PATHS, set(document["bindings"]))
        for name, row in document["bindings"].items():
            raw_current = (ROOT / name).read_bytes()
            raw = contract_history.source_before_contract667(name, raw_current)
            before = newest.current_source_before_platform_recovery659(name, raw_current)
            self.assertEqual((row["after_sha256"], row["after_bytes"]), (newest.sha(raw), len(raw)), name)
            self.assertEqual((row["before_sha256"], row["before_bytes"]), (newest.sha(before), len(before)), name)
            self.assertIs(before, newest.source_before_platform_recovery659(name, before))
            self.assertEqual(before, newest.peel_platform_recovery659_for_history(name, raw))
            self.assertIs(before, newest.peel_platform_recovery659_for_history(name, before))
            forward = before
            for fragment in row["fragments"]:
                old, new = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual((newest.sha(old), newest.sha(new)),
                                 (fragment["before_fragment_sha256"], fragment["after_fragment_sha256"]))
                self.assertEqual(1, forward.count(old))
                forward = forward.replace(old, new, 1)
            self.assertEqual(raw, forward)
            fragment = row["fragments"][0]["after"].encode()
            displaced = raw.replace(fragment, b"", 1) + fragment
            self.assertNotEqual(raw, displaced)
            foreign = (ROOT / next(path for path in newest.BOUND_PATHS if path != name)).read_bytes()
            for bad in (before, raw[:-1], raw + b"\n", displaced, foreign, b"", b"unknown", None,
                        bytearray(raw), raw.decode(), b"x" * (newest.MAX_SOURCE_BYTES + 1)):
                with self.subTest(relative=name, kind=type(bad).__name__), self.assertRaises(ValueError):
                    newest.current_source_before_platform_recovery659(name, bad)
            unknown = before + b"\n# uncertified source\n"
            self.assertIs(unknown, newest.peel_platform_recovery659_for_history(name, unknown))
            with self.assertRaises(ValueError):
                newest.source_before_platform_recovery659(name, unknown)
        unlisted = b"pass-through never certifies a current source"
        for reader in (newest.source_before_platform_recovery659, newest.current_source_before_platform_recovery659,
                       newest.peel_platform_recovery659_for_history):
            self.assertIs(unlisted, reader("unlisted-source", unlisted))
            with self.assertRaises(ValueError):
                reader(Path("unlisted-source"), unlisted)
        self.assertEqual(CAMERA4697_GUARD_SHA256, document["bindings"][camera.SOURCE_RELATIVE]["before_sha256"])
        self.assertEqual(WEBVIEW4697_GUARD_SHA256, document["bindings"][content_history.SOURCE_RELATIVE]["before_sha256"])
        self.assertEqual(WEBVIEW659_GUARD_SHA256, newest.sha((ROOT / content_history.SOURCE_RELATIVE).read_bytes()))

    def test_nonrecursive_camera_hooks_peel_actual_raw_guards_before_original_validation_without_rewriting_pins(self):
        raw = (ROOT / camera.SOURCE_RELATIVE).read_bytes()
        before = newest.source_before_platform_recovery659(camera.SOURCE_RELATIVE, raw)
        class TransparentOuterHooks(ast.NodeTransformer):
            def visit_ImportFrom(self, node):
                return None if node.module == "platform_recovery659_source_projection" else node
            def visit_Import(self, node):
                return None if ast.unparse(node) == "import platform_recovery659_source_projection as newest" else node
            def visit_Expr(self, node):
                return None if ast.unparse(node) == "newest.validate_current_sources(root)" else self.generic_visit(node)
            def visit_Assign(self, node):
                if (len(node.targets) == 1 and ast.unparse(node.targets[0]) == "payload" and isinstance(node.value, ast.Call) and
                        ast.unparse(node.value.func) in {"peel_platform_recovery659_for_history", "current_source_before_platform_recovery659"}):
                    if [ast.unparse(arg) for arg in node.value.args] != ["relative", "payload"] or node.value.keywords:
                        raise AssertionError("Only the exact binary outer source hook is allowed")
                    return None
                return self.generic_visit(node)
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if ast.unparse(node.func) == "newest.source_before_platform_recovery659":
                    if len(node.args) != 2 or node.keywords or ast.unparse(node.args[0]) != "name":
                        raise AssertionError("Only the exact owning validator source operand changes")
                    return node.args[1]
                return node
            def visit_BinOp(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.op, ast.BitOr) and isinstance(node.right, ast.Call) and
                        ast.unparse(node.right.func) == "newest_fixture_inputs"):
                    if node.right.args or node.right.keywords:
                        raise AssertionError("Only the finite outer fixture union is allowed")
                    return node.left
                return node
        self.assertEqual(ast.dump(ast.parse(before), include_attributes=False),
                         ast.dump(TransparentOuterHooks().visit(ast.parse(raw)), include_attributes=False))
        guard_tree = ast.parse((ROOT / newest.SOURCE_RELATIVE).read_bytes())
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                             any(name in ast.unparse(node) for name in ("camera_ios_ownership", "webview_content_policy"))
                             for node in ast.walk(guard_tree)))
        prohibited = {"exec", "eval", "compile", "__import__", "run", "Popen", "write_bytes", "write_text"}
        guarded = [node for node in ast.walk(guard_tree) if isinstance(node, ast.Call) and
                   ast.unparse(node.func).rsplit(".", 1)[-1] in prohibited]
        self.assertEqual(["re.compile"], [ast.unparse(node.func) for node in guarded])
        self.assertEqual([r"[0-9a-f]{64}\Z"], [ast.literal_eval(node.args[0]) for node in guarded])
        self.assertTrue(all(len(node.args) == 1 and not node.keywords for node in guarded))
        for name in newest.BOUND_PATHS:
            raw_current = (ROOT / name).read_bytes()
            with patch.object(newest, "current_source_before_platform_recovery659",
                              wraps=newest.current_source_before_platform_recovery659) as raw_ingress:
                content_history.current_source_before_content_policy(name, raw_current)
                raw_ingress.assert_called_once_with(name, raw_current)
        self.assertEqual(CAMERA651_SPEC_SHA256, camera.SPEC_SHA256)
        self.assertEqual(WEBVIEW874_SPEC_SHA256, content_history.SPEC_SHA256)
        self.assertEqual(CAMERA651_SPEC_SHA256, newest.sha((ROOT / camera.SPEC_RELATIVE).read_bytes()))
        self.assertEqual(WEBVIEW874_SPEC_SHA256, newest.sha((ROOT / content_history.SPEC_RELATIVE).read_bytes()))
        with patch.object(newest, "validate_current_sources", wraps=newest.validate_current_sources) as raw_validator:
            self.assertTrue(camera.validate_current_sources(ROOT))
            raw_validator.assert_called_once_with(ROOT)

    def test_raw_finite_inputs_own_guard_singleton_template_and_new_controls_refuse_missing_drift_links_and_old_images(self):
        document = newest._document()
        self.assertEqual(2, len(document["added_inputs"]))
        self.assertNotIn("AGENTS.md", newest.fixture_inputs())
        self.assertTrue(newest.fixture_inputs() <= camera.fixture_inputs())
        self.assertTrue(newest.fixture_inputs() <= content_history.fixture_inputs())
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            copy_fixture(root)
            self.assertTrue(newest.validate_current_sources(root))
            self.assertTrue(camera.validate_current_sources(root))
            self.assertTrue(content_history.validate_current_sources(root))
            (root / "AGENTS.md").write_bytes(b"unrelated maintainer bytes\x00\xff")
            self.assertTrue(newest.validate_current_sources(root))
            for name in sorted(newest.fixture_inputs()):
                with self.subTest(owned_input=name):
                    target = root / name
                    raw = target.read_bytes()
                    target.write_bytes(raw + b"\n")
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    with self.assertRaises(FileNotFoundError):
                        camera.validate_current_sources(root)
                    target.symlink_to(ROOT / name)
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    backing = target.with_name(target.name + ".backing")
                    backing.write_bytes(raw)
                    target.hardlink_to(backing)
                    with self.assertRaises(ValueError):
                        camera.validate_current_sources(root)
                    target.unlink()
                    backing.unlink()
                    target.write_bytes(raw)
            for name in sorted(newest.BOUND_PATHS):
                target = root / name
                raw = target.read_bytes()
                target.write_bytes(newest.source_before_platform_recovery659(name, raw))
                with self.assertRaises(ValueError):
                    camera.validate_current_sources(root)
                with self.assertRaises(ValueError):
                    content_history.validate_current_sources(root)
                target.write_bytes(raw)
            guard = root / newest.SOURCE_RELATIVE
            raw_guard = guard.read_bytes()
            approved_guard = contract_history.source_before_contract667(newest.SOURCE_RELATIVE, raw_guard)
            needle = ('SPEC_SHA256 = "' + newest.SPEC_SHA256 + '"\n').encode()
            self.assertEqual(1, raw_guard.count(needle))
            normalized = approved_guard.replace(needle, ('SPEC_SHA256 = "' + "0" * 64 + '"\n').encode(), 1)
            self.assertEqual((document["own_guard"]["template_sha256"], document["own_guard"]["bytes"]),
                             (newest.sha(normalized), len(approved_guard)))
            for bad in (raw_guard.replace(needle, needle + needle, 1), raw_guard.replace(needle, b"", 1),
                        raw_guard.replace(needle, ('SPEC_SHA256 = "' + "a" * 64 + '"\n').encode(), 1),
                        raw_guard.replace(b"return True", b"return None", 1)):
                guard.write_bytes(bad)
                with self.assertRaises(ValueError):
                    newest.validate_current_sources(root)
            guard.write_bytes(raw_guard)
            self.assertTrue(content_history.validate_current_sources(root))

    def test_manifest_exact_schema_and_raw_image_fixture_operand_do_not_double_peel_or_certify_pass_through(self):
        raw = (ROOT / newest.SPEC_RELATIVE).read_bytes()
        document = newest._document()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_bytes(raw + b"\n")
            with patch.object(newest, "SPEC_PATH", path), self.assertRaises(ValueError):
                newest._document()
            for candidate in (b'{"schema_version":1,"schema_version":1}', b'{"schema_version":NaN}', b"{}", b"[]"):
                path.write_bytes(candidate)
                with patch.object(newest, "SPEC_PATH", path), patch.object(newest, "SPEC_SHA256", newest.sha(candidate)), self.assertRaises(ValueError):
                    newest._document()
            mutations = (
                lambda d: d.update(schema_version=True),
                lambda d: d.update(scope="native acceptance"),
                lambda d: d.update(predecessor="unknown"),
                lambda d: d["bindings"].pop(next(iter(d["bindings"]))),
                lambda d: d["added_inputs"].update({"foreign.py": "a" * 64}),
                lambda d: d["unchanged_inputs"].update({"AGENTS.md": "a" * 64}),
                lambda d: d["own_guard"].update(bytes=True),
                lambda d: d["own_guard"].update(template_sha256="A" * 64),
                lambda d: d["bindings"][camera.SOURCE_RELATIVE].update(after_bytes=True),
                lambda d: d["bindings"][camera.SOURCE_RELATIVE].update(after_sha256="A" * 64),
            )
            for mutate in mutations:
                bad = deepcopy(document)
                mutate(bad)
                candidate = json.dumps(bad).encode()
                path.write_bytes(candidate)
                with patch.object(newest, "SPEC_PATH", path), patch.object(newest, "SPEC_SHA256", newest.sha(candidate)), self.assertRaises(ValueError):
                    newest._document()
        name = camera.SOURCE_RELATIVE
        bad = deepcopy(document)
        bad["bindings"][name]["fragments"][0]["after_fragment_sha256"] = "a" * 64
        with patch.object(newest, "_document", return_value=bad), self.assertRaises(ValueError):
            newest.source_before_platform_recovery659(name, (ROOT / name).read_bytes())
        image = (ROOT / IMAGE_CONTROL).read_bytes()
        from tooling_recovery671_source_projection import current_source_before_tooling671
        literal656 = current_source_before_tooling671(IMAGE_CONTROL, image)
        # The original platform659 inverse is historical DATA only.
        # Current Content calls and raw-call-count checks retain image.
        old_image = newest.source_before_platform_recovery659(IMAGE_CONTROL, literal656)
        self.assertEqual(old_image, content_history._current_tooling656_control_source(IMAGE_CONTROL, image))
        self.assertEqual("9d7870ffcd1cf584c7e2914143d93066defba889638df05f0f91781ab5dd2fa9", newest.sha(old_image))
        with self.assertRaises(ValueError):
            content_history._current_tooling656_control_source(IMAGE_CONTROL, old_image)
        with self.assertRaises(ValueError):
            content_history.current_source_before_content_policy(IMAGE_CONTROL, old_image)
        with patch.object(newest, "validate_current_sources", wraps=newest.validate_current_sources) as raw_gate, \
                patch.object(content_history, "_current_tooling656_control_source",
                             wraps=content_history._current_tooling656_control_source) as fixture_operand:
            self.assertTrue(content_history.validate_current_sources(ROOT))
            raw_gate.assert_called_once_with(ROOT)
            actual = [call for call in fixture_operand.call_args_list if call.args[0] == IMAGE_CONTROL]
            self.assertEqual(1, len(actual))
            self.assertEqual((IMAGE_CONTROL, image), actual[0].args)
        owner = function(ast.parse((ROOT / content_history.SOURCE_RELATIVE).read_bytes()), "validate_current_sources")
        operands = [node for node in ast.walk(owner) if isinstance(node, ast.Call) and
                    ast.unparse(node.func) == "_current_tooling656_control_source"]
        self.assertEqual(1, len(operands))
        self.assertEqual("_ordinary_bytes(root, name)[0]", ast.unparse(operands[0].args[1]))


    def test_new743_invalid_platform_extra_refuses_before_ancestor_without_remote_growth(self):
        from ios_popover_anchor_plan import _ordinary_bytes
        import macos_share_ci668_composition as joint
        self.assertEqual(10, len(newest.PLATFORM_EXTRA_CURRENT_PATHS743))
        self.assertTrue(newest.PLATFORM_EXTRA_CURRENT_PATHS743 <= newest.BOUND_PATHS)
        self.assertFalse(newest.PLATFORM_EXTRA_CURRENT_PATHS743 & joint.fixture_inputs(ROOT))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in sorted(newest.PLATFORM_EXTRA_CURRENT_PATHS743):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(_ordinary_bytes(ROOT, name)[0])
            changed = sorted(newest.PLATFORM_EXTRA_CURRENT_PATHS743)[0]
            target = root / changed
            target.write_bytes(target.read_bytes() + b"\n")
            with patch.object(contract_history, "validate_current_sources",
                              side_effect=AssertionError("An invalid owning extra must not enter ancestors")) as ancestor:
                with self.assertRaisesRegex(ValueError, "Current platform-recovery659 input differs"):
                    newest.validate_current_sources(root)
            ancestor.assert_not_called()

    def test_new743_valid_platform_extras_reach_ancestor_and_keep_original_tail(self):
        from ios_popover_anchor_plan import _ordinary_bytes
        class AncestorReached(RuntimeError):
            pass
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in sorted(newest.PLATFORM_EXTRA_CURRENT_PATHS743):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(_ordinary_bytes(ROOT, name)[0])
            with patch.object(contract_history, "validate_current_sources",
                              side_effect=AncestorReached("fresh owning prefix reached unchanged ancestor")) as ancestor:
                with self.assertRaises(AncestorReached):
                    newest.validate_current_sources(root)
            ancestor.assert_called_once_with(root)
        # AST conservation is source-only, not a second native/full pass.
        source = _ordinary_bytes(ROOT, newest.SOURCE_RELATIVE)[0].decode()
        owner = function(ast.parse(source), "validate_current_sources")
        calls = [ast.unparse(node.func) for node in ast.walk(owner) if isinstance(node, ast.Call)]
        self.assertEqual(1, calls.count("current.validate_current_sources"))
        self.assertEqual(1, calls.count("_validate_own_guard"))
        self.assertEqual(2, calls.count("_document"))
        self.assertEqual(2, calls.count("current.source_before_contract667"))

    @staticmethod
    def _new743_tooling_composition_case():
        import tooling_recovery671_source_projection as tooling
        def row(before, after, old, new):
            return {"before_sha256": tooling.sha(before), "after_sha256": tooling.sha(after),
                    "before_bytes": len(before), "after_bytes": len(after),
                    "fragments": [{"before": old, "after": new,
                        "before_fragment_sha256": tooling.sha(old.encode()),
                        "after_fragment_sha256": tooling.sha(new.encode()),
                        "obligation": "Controlled exact inverse arithmetic, not source admission"}]}
        name, before = "controlled743.py", b"base OLD end\n"
        after = before.replace(b"OLD", b"NEW")
        owning = {"bindings": {name: row(before, after, "OLD", "NEW")},
                  "added_inputs": {}, "unchanged_inputs": {}}
        views = {view: {name: row(before, before.replace(b"base", prefix.encode()), "base", prefix)}
                 for view, prefix in (("callback_above_io", "above"), ("callback_isolated", "isolated"))}
        return tooling, name, before, after, owning, views

    def _exercise_new743_tooling_composition_scope(self, failure=None):
        import macos_share_ci668_composition as joint
        tooling, name, before, after, document, composition = self._new743_tooling_composition_case()
        root, spec = Path("/controlled-tooling743-no-filesystem"), b"controlled spec bytes"
        ordinary = {name: after, tooling.SPEC_RELATIVE: spec}
        if failure == "raw":
            ordinary[name] += b"drift"
        events, primary = [], ValueError("controlled743 primary " + str(failure))
        class Operation:
            def _validate_tooling(self, actual):
                self_test.assertEqual(root, actual)
                return tooling._validate_current_sources_operation(actual, document, self)
            def _validate_ci(self, actual):
                self_test.assertEqual(root, actual)
                events.append(("ci", actual))
                if failure == "ci":
                    raise primary
                return True
            def _ci_history(self, relative, payload):
                events.append(("history", relative, payload))
                return payload
        class Scope:
            def __enter__(self):
                events.append(("enter", root))
                return operation
            def __exit__(self, kind, value, traceback):
                events.append(("exit", kind, value))
                return False
        self_test, operation = self, Operation()
        def read(actual, relative):
            self.assertEqual(root, actual)
            events.append(("ordinary", relative))
            return ordinary[relative], {}
        def guard(actual, owning):
            self.assertEqual(root, actual)
            self.assertIs(document, owning)
            events.append(("guard", actual))
            if failure == "guard":
                raise primary
            return "controlled guard"
        def qualify():
            events.append(("composition",))
            return composition
        with patch.object(tooling, "SPEC_SHA256", tooling.sha(spec)), \
                patch.object(joint, "_source_projection_operation", return_value=Scope()) as scope, \
                patch("ios_popover_anchor_plan._ordinary_bytes", side_effect=read) as source_reads, \
                patch.object(tooling, "_validate_own_guard", side_effect=guard) as own_guard, \
                patch.object(tooling, "_composition_document", side_effect=qualify) as fresh_composition, \
                patch.object(tooling, "source_before_tooling671", side_effect=AssertionError("No repeated standalone history route")) as standalone_inverse, \
                patch.object(tooling, "_complete_composition_view", side_effect=AssertionError("No repeated standalone composition shaping")) as standalone_view, \
                patch.object(tooling, "_source_before_tooling671_document", wraps=tooling._source_before_tooling671_document) as inverse, \
                patch.object(tooling, "_complete_composition_view_row680", wraps=tooling._complete_composition_view_row680) as view:
            result, error = None, None
            try:
                result = tooling.validate_current_sources(root)
            except Exception as caught:
                error = caught
        scope.assert_called_once_with(root)
        standalone_inverse.assert_not_called()
        standalone_view.assert_not_called()
        return {"root": root, "name": name, "before": before, "after": after,
                "document": document, "events": events, "primary": primary,
                "result": result, "error": error, "reads": source_reads, "guard": own_guard,
                "composition": fresh_composition, "inverse": inverse, "view": view}

    def test_new743_tooling_composition_reuses_one_existing_scope_and_private_rows(self):
        case = self._exercise_new743_tooling_composition_scope()
        self.assertIsNone(case["error"])
        self.assertIs(True, case["result"])
        case["guard"].assert_called_once_with(case["root"], case["document"])
        case["composition"].assert_called_once_with()
        self.assertEqual(4, case["reads"].call_count)
        self.assertEqual(2, case["inverse"].call_count)
        self.assertEqual(2, case["view"].call_count)
        for call in case["inverse"].call_args_list:
            self.assertEqual((case["name"], case["after"]), call.args[:2])
            self.assertIs(case["document"], call.args[2])
        for call in case["view"].call_args_list:
            self.assertIs(case["before"], call.args[0]) if case["before"] is call.args[0] else self.assertEqual(case["before"], call.args[0])
        self.assertEqual(["enter", "ci", "guard", "ordinary", "history", "ordinary", "history",
                          "composition", "ordinary", "history", "ordinary", "history", "exit"],
                         [event[0] for event in case["events"]])
        self.assertEqual(("exit", None, None), case["events"][-1])

    def test_new743_tooling_composition_keeps_primary_and_refuses_before_reuse(self):
        for failure in ("ci", "guard", "raw"):
            with self.subTest(failure=failure):
                case = self._exercise_new743_tooling_composition_scope(failure)
                self.assertIsNone(case["result"])
                self.assertIsInstance(case["error"], ValueError)
                case["composition"].assert_not_called()
                case["inverse"].assert_not_called()
                case["view"].assert_not_called()
                self.assertEqual("exit", case["events"][-1][0])
                self.assertIs(ValueError, case["events"][-1][1])
                self.assertIs(case["error"], case["events"][-1][2])
                if failure in ("ci", "guard"):
                    self.assertIs(case["primary"], case["error"])
                else:
                    self.assertIn("Current tooling671 input differs", str(case["error"]))
                self.assertEqual(0 if failure == "ci" else 1, case["guard"].call_count)

    def test_new743_tooling_private_inverse_preserves_fresh_public_doc_and_all_arithmetic_guards(self):
        import ci668_outer_source_projection as ci668
        import ci_source_domain740 as domain740
        tooling, name, before, after, document, composition = self._new743_tooling_composition_case()
        held = deepcopy(document)
        for raw in (before, after):
            self.assertEqual(before, tooling._source_before_tooling671_document(name, raw, document))
        unknown = b"unlisted bytes remain uncertified"
        self.assertIs(unknown, tooling._source_before_tooling671_document("unlisted", unknown, document))
        for relative, raw in ((Path(name), after), (name, None), (name, bytearray(after)),
                              (name, after.decode()), (name, b""), (name, after[:-1]),
                              (name, after + b"drift"), (name, b"foreign"),
                              (name, b"x" * (tooling.MAX_SOURCE_BYTES + 1))):
            with self.subTest(relative=type(relative).__name__, payload=type(raw).__name__), self.assertRaises(ValueError):
                tooling._source_before_tooling671_document(relative, raw, document)
        bad = deepcopy(document)
        bad["bindings"][name]["fragments"][0]["after_fragment_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "unique tooling671 inverse"):
            tooling._source_before_tooling671_document(name, after, bad)
        bad = deepcopy(document)
        repeated = after + b"NEW"
        bad["bindings"][name].update(after_sha256=tooling.sha(repeated), after_bytes=len(repeated))
        with self.assertRaisesRegex(ValueError, "unique tooling671 inverse"):
            tooling._source_before_tooling671_document(name, repeated, bad)
        bad = deepcopy(document)
        old, new = b"OLD OLD", b"NEW OLD"
        bad["bindings"][name].update(before_sha256=tooling.sha(old), before_bytes=len(old),
                                     after_sha256=tooling.sha(new), after_bytes=len(new))
        with self.assertRaisesRegex(ValueError, "unique tooling671 forward"):
            tooling._source_before_tooling671_document(name, new, bad)
        def passthrough(relative, payload):
            return payload
        with patch.object(domain740, "peel_domain740_for_history", side_effect=passthrough), \
                patch.object(ci668, "peel_ci668_for_history", side_effect=passthrough), \
                patch.object(domain740, "peel_bridge740_for_history", side_effect=passthrough), \
                patch.object(tooling, "_document", return_value=document) as fresh:
            self.assertEqual(before, tooling.source_before_tooling671(name, after))
            self.assertEqual(before, tooling.source_before_tooling671(name, before))
            self.assertEqual(2, fresh.call_count)
            with self.assertRaises(ValueError):
                tooling.source_before_tooling671(Path(name), after)
            self.assertEqual(2, fresh.call_count)
        self.assertEqual(held, document)

    def test_new743_tooling_private_view_rows_preserve_public_freshness_and_exact_roundtrips(self):
        tooling, name, before, after, document, composition = self._new743_tooling_composition_case()
        held = deepcopy(composition)
        with patch.object(tooling, "_composition_document", return_value=composition) as fresh:
            for view in ("callback_above_io", "callback_isolated"):
                row = composition[view][name]
                expected = before.replace(b"base", row["fragments"][0]["after"].encode())
                actual = tooling._complete_composition_view_row680(before, row)
                self.assertEqual(expected, actual)
                self.assertEqual((row["after_sha256"], row["after_bytes"]), (tooling.sha(actual), len(actual)))
                self.assertIs(actual, tooling._complete_composition_view_row680(actual, row))
                self.assertEqual(expected, tooling._complete_composition_view(name, before, view))
            self.assertEqual(2, fresh.call_count)
            for relative, raw, view in ((Path(name), before, "callback_above_io"),
                                        (name, bytearray(before), "callback_above_io"),
                                        (name, before, "native"), (name, before, None)):
                with self.assertRaises(ValueError):
                    tooling._complete_composition_view(relative, raw, view)
            self.assertEqual(2, fresh.call_count)
        row = composition["callback_above_io"][name]
        for raw in (None, bytearray(before), before.decode(), b"", before[:-1],
                    before + b"drift", b"foreign", b"x" * (tooling.MAX_SOURCE_BYTES + 1)):
            with self.subTest(payload=type(raw).__name__), self.assertRaises(ValueError):
                tooling._complete_composition_view_row680(raw, row)
        unknown = b"unlisted view bytes remain uncertified"
        self.assertIs(unknown, tooling._complete_composition_view_row680(unknown, None))
        identity = {"before_sha256": tooling.sha(before), "after_sha256": tooling.sha(before),
                    "before_bytes": len(before), "after_bytes": len(before), "fragments": []}
        self.assertIs(before, tooling._complete_composition_view_row680(before, identity))
        bad = deepcopy(row)
        bad["fragments"][0]["before_fragment_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "unique composed680 source-view fragments"):
            tooling._complete_composition_view_row680(before, bad)
        bad = deepcopy(row)
        duplicate = before + b"base"
        bad.update(before_sha256=tooling.sha(duplicate), before_bytes=len(duplicate))
        with self.assertRaisesRegex(ValueError, "unique composed680 source-view fragments"):
            tooling._complete_composition_view_row680(duplicate, bad)
        bad = deepcopy(row)
        old, new = b"base above", b"above above"
        bad.update(before_sha256=tooling.sha(old), before_bytes=len(old),
                   after_sha256=tooling.sha(new), after_bytes=len(new))
        with self.assertRaisesRegex(ValueError, "unique composed680 source-view reverse"):
            tooling._complete_composition_view_row680(old, bad)
        self.assertEqual(held, composition)


    def test_new743_operation_raw_endpoint_precedence_is_fresh_finite_refusal_data(self):
        import macos_share_ci668_composition as joint
        import ci_fixture_successor730 as successor
        plain = "scripts/ci/plain743.py"
        layered = "scripts/ci/tests/test_cookie_ci668_outer_scope609.py"
        ordinary = "scripts/ci/test_ci_source_domain740.py"
        related = "scripts/ci/camera_handoff_fixture_source_projection.py"
        copied = "scripts/ci/tests/test_webview_kotlin_test_filter_api777.py"
        foreign = "scripts/ci/unlisted743.py"
        def endpoint(raw):
            return (len(raw), joint.sha(raw))
        def row(raw):
            return dict(zip(("after_bytes", "after_sha256"), endpoint(raw)))
        names = (plain, layered, ordinary, related, copied, successor.CONTROL,
                 successor.CAPACITY, successor.REMOTE)
        base = {"raw_inputs": {name: dict(zip(("bytes", "sha256"), endpoint(b"base")))
                              for name in names}}
        domain = {"bindings": {layered: row(b"domain"), joint.OWNER: row(b"domain owner")}}
        recovery_rows = {"bindings": {layered: row(b"recovery")}}
        fixture = {
            "bindings": {layered: row(b"fixture"), ordinary: row(b"fixture ordinary"),
                         joint.OWNER: row(b"fixture owner"), foreign: row(b"never enrolled")},
            "capacity_binding": row(b"capacity"), "routing_binding": row(b"routing"),
            "remote_binding": row(b"remote"),
            "ordinary_fixture_bindings": {ordinary: row(b"ordinary")},
            "related_bindings": {layered: row(b"related"), related: row(b"related only")},
            "failure_bindings": {layered: row(b"failure"), copied: row(b"copied is not modified")},
            "platform_custody_bindings743": {layered: row(b"platform"), joint.OWNER: row(b"platform owner"),
                                             successor.CONTROL: row(b"control is not modified")},
        }
        documents = (base, domain, recovery_rows, fixture)
        held = deepcopy(documents)
        expected = {name: endpoint(b"base") for name in names}
        expected.update({layered: endpoint(b"platform"), ordinary: endpoint(b"ordinary"),
                         related: endpoint(b"related only"), joint.OWNER: endpoint(b"platform owner"),
                         successor.CAPACITY: endpoint(b"capacity"), successor.REMOTE: endpoint(b"remote")})
        self.assertEqual(expected, joint._operation_raw_endpoints743(*documents))
        self.assertEqual(held, documents)
        self.assertNotIn(foreign, expected)
        self.assertEqual(set(names) | {joint.OWNER}, set(expected))
        # Each call derives current expected DATA again, without mutating its operands.
        for section, previous in (("platform_custody_bindings743", b"failure"),
                                  ("failure_bindings", b"related"),
                                  ("related_bindings", b"fixture"),
                                  ("bindings", b"recovery")):
            fixture[section].pop(layered)
            self.assertEqual(endpoint(previous), joint._operation_raw_endpoints743(*documents)[layered])
        recovery_rows["bindings"].pop(layered)
        self.assertEqual(endpoint(b"domain"), joint._operation_raw_endpoints743(*documents)[layered])
        domain["bindings"].pop(layered)
        self.assertEqual(endpoint(b"base"), joint._operation_raw_endpoints743(*documents)[layered])
        fixture["platform_custody_bindings743"].pop(joint.OWNER)
        self.assertEqual(endpoint(b"routing"), joint._operation_raw_endpoints743(*documents)[joint.OWNER])
        # Separate current-control and copied rows cannot masquerade as modified RAW.
        final = joint._operation_raw_endpoints743(*documents)
        self.assertEqual(endpoint(b"base"), final[copied])
        self.assertEqual(endpoint(b"base"), final[successor.CONTROL])

    def test_new743_operation_capture_raw_refusal_precedes_shape_and_keeps_valid_tail(self):
        import macos_share_ci668_composition as joint
        import ci_fixture_successor730 as successor
        import ci_source_domain740 as domain
        import ci668_outer_source_projection as ci668
        import producer698_source_fixture_recovery as producer
        import tooling_recovery671_source_projection as tooling
        inventories = {}
        for owner in (joint, domain, recovery, successor):
            raw = joint._ordinary(ROOT, owner.SPEC, joint.MAX_SPEC)[0]
            self.assertEqual(owner.SPEC_SHA256, joint.sha(raw))
            inventories[(ROOT, owner.SPEC)] = raw
        for owner in (ci668, producer, tooling):
            raw = joint._ordinary(owner.SPEC_PATH.parent, owner.SPEC_PATH.name, joint.MAX_SPEC)[0]
            self.assertEqual(owner.SPEC_SHA256, joint.sha(raw))
            inventories[(owner.SPEC_PATH.parent, owner.SPEC_PATH.name)] = raw
        name = sorted(json.loads(inventories[(ROOT, joint.SPEC)])["raw_inputs"])[0]
        good = b"fresh current endpoint data"
        operand, seen = [good], []
        def capture(origin, relative, maximum=joint.MAX_SOURCE):
            seen.append((origin, relative, maximum))
            if (origin, relative) == (ROOT, name):
                if isinstance(operand[0], BaseException):
                    raise operand[0]
                return operand[0]
            return inventories.get((origin, relative), b"captured but not admitted")
        class ShapeReached(RuntimeError):
            pass
        # The endpoint helper's branch arithmetic is exercised independently above.
        # This bounded constructor control observes captures and the mandatory tail;
        # reaching that tail is deliberately NOT a successful current admission.
        with patch.object(joint, "_operation_raw_endpoints743",
                          side_effect=lambda *args: {name: (len(good), joint.sha(good))}) as endpoints, \
                patch.object(joint, "_document", side_effect=ShapeReached("original schema tail")) as shape:
            for bad in (b"x" * len(good), good + b"\n", FileNotFoundError("missing raw"),
                        ValueError("ordinary descriptor link refusal")):
                operand[0] = bad
                seen.clear()
                expected_error = type(bad) if isinstance(bad, BaseException) else ValueError
                with self.assertRaises(expected_error) as failed:
                    joint._build_source_projection_operation(ROOT, capture)
                if isinstance(bad, BaseException):
                    self.assertIs(bad, failed.exception)
                self.assertEqual(1, sum((origin, relative) == (ROOT, name)
                                       for origin, relative, maximum in seen))
                shape.assert_not_called()
            operand[0] = good
            with self.assertRaises(ShapeReached):
                joint._build_source_projection_operation(ROOT, capture)
            shape.assert_called_once_with(ROOT)
            # A previous good prefix never caches a source or authenticates a new manifest.
            before = endpoints.call_count
            inventory_key = (ROOT, joint.SPEC)
            original = inventories[inventory_key]
            inventories[inventory_key] = original + b"\n"
            with self.assertRaisesRegex(ValueError, "exact-share-CI-latest-manifest-required"):
                joint._build_source_projection_operation(ROOT, capture)
            self.assertEqual(before, endpoints.call_count)
            inventories[inventory_key] = original
            operand[0] = good + b"\n"
            with self.assertRaisesRegex(ValueError, "source-projection-operation-current-raw-before-shape-required"):
                joint._build_source_projection_operation(ROOT, capture)
            self.assertEqual(before + 1, endpoints.call_count)
            shape.assert_called_once_with(ROOT)


    def test_new743_metadata_prefix_is_fresh_refusal_only_and_retains_whole_owning_tail(self):
        import macos_share_ci668_composition as joint
        import macos_share_appkit_only_source_projection as ordinary
        import ci_source_domain740 as domain
        import ci_fixture_successor730 as successor
        supported = (joint._descriptor_source_io_supported() and
                     joint.os.stat in joint.os.supports_follow_symlinks)
        # Unsupported providers do not acquire new capabilities or bypass the tail.
        with patch.object(joint, "_descriptor_source_io_supported", return_value=False), \
                patch.object(joint, "_ordinary", side_effect=AssertionError("no new portable read")), \
                patch.object(ordinary, "open_directory", side_effect=AssertionError("no invented dirfd")):
            self.assertIsNone(joint._source_projection_metadata_refusal743(ROOT))
            self.assertIsNone(joint._operation_metadata_refusal743(ROOT, {}))
        if supported:
            owners = (joint, domain, recovery, successor)
            raws = {owner.SPEC: joint._ordinary(ROOT, owner.SPEC, joint.MAX_SPEC)[0]
                    for owner in owners}
            for owner in owners:
                self.assertEqual(owner.SPEC_SHA256, joint.sha(raws[owner.SPEC]))
            calls = []
            def inventory(origin, relative, maximum):
                self.assertEqual((ROOT, joint.MAX_SPEC), (origin, maximum))
                calls.append(relative)
                return raws[relative], None
            with patch.object(joint, "_ordinary", side_effect=inventory), \
                    patch.object(joint, "_operation_metadata_refusal743") as metadata:
                self.assertIsNone(joint._source_projection_metadata_refusal743(ROOT))
                expected = joint._operation_raw_endpoints743(
                    *(json.loads(raws[owner.SPEC]) for owner in owners))
                metadata.assert_called_once_with(ROOT, expected)
                self.assertEqual([owner.SPEC for owner in owners], calls)
                original = raws[joint.SPEC]
                raws[joint.SPEC] = original + b"\n"
                with self.assertRaisesRegex(ValueError, "exact-share-CI-latest-manifest-required"):
                    joint._source_projection_metadata_refusal743(ROOT)
                self.assertEqual(1, metadata.call_count)
                raws[joint.SPEC] = original
                joint._source_projection_metadata_refusal743(ROOT)
                self.assertEqual(2, metadata.call_count)

            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                payload = b"abc\n"
                names = ("d/a.py", "d/b.py", "z/c.py")
                endpoints = {name: (len(payload), joint.sha(payload)) for name in names}
                for name in names:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(payload)
                (root / "unlisted").symlink_to(root / "absent")
                real_close = ordinary.close_owned
                closings = []
                def close(descriptors, primary):
                    held = tuple(descriptors)
                    real_close(descriptors, primary)
                    for fd in held:
                        with self.assertRaises(OSError):
                            joint.os.fstat(fd)
                    closings.append((held, primary))
                with patch.object(ordinary, "open_directory", wraps=ordinary.open_directory) as opening, \
                        patch.object(ordinary, "close_owned", side_effect=close), \
                        patch.object(ordinary, "ordinary_bytes",
                                     side_effect=AssertionError("metadata is not a byte capture")):
                    self.assertIsNone(joint._operation_metadata_refusal743(root, endpoints))
                    self.assertEqual(["d", "z"], [call.args[1] for call in opening.call_args_list])
                    self.assertEqual(2, len(closings))
                    target = root / names[0]
                    # Same-length different bytes are deliberately not admitted here:
                    # only the unchanged mandatory byte/schema suffix can decide them.
                    target.write_bytes(b"xyz\n")
                    self.assertIsNone(joint._operation_metadata_refusal743(root, endpoints))
                    target.write_bytes(payload + b"\n")
                    with self.assertRaises(ValueError) as changed:
                        joint._operation_metadata_refusal743(root, endpoints)
                    self.assertIs(changed.exception, closings[-1][1])
                    target.unlink()
                    with self.assertRaises(FileNotFoundError) as missing:
                        joint._operation_metadata_refusal743(root, endpoints)
                    self.assertIs(missing.exception, closings[-1][1])
                    target.symlink_to(root / names[1])
                    with self.assertRaises(ValueError):
                        joint._operation_metadata_refusal743(root, endpoints)
                    target.unlink()
                    target.hardlink_to(root / names[1])
                    with self.assertRaises(ValueError):
                        joint._operation_metadata_refusal743(root, endpoints)
                    target.unlink()
                    target.write_bytes(payload)
                    self.assertIsNone(joint._operation_metadata_refusal743(root, endpoints))
                    (root / "alias").symlink_to(root / "d", target_is_directory=True)
                    with self.assertRaises(ValueError):
                        joint._operation_metadata_refusal743(
                            root, {"alias/a.py": (len(payload), joint.sha(payload))})

        events = []
        class OriginalTailReached(RuntimeError):
            pass
        def original_document():
            events.append("original-document")
            raise OriginalTailReached("unchanged owning/history/acquisition tail")
        with patch.object(joint, "_source_projection_metadata_refusal743",
                          side_effect=lambda root: events.append("metadata")) as prefix, \
                patch.object(newest, "_document", side_effect=original_document) as document:
            with self.assertRaises(OriginalTailReached):
                newest.validate_current_sources(ROOT)
            self.assertEqual(["metadata", "original-document"], events)
            prefix.assert_called_once_with(ROOT)
            document.assert_called_once_with()
            document.reset_mock()
            failed = ValueError("fresh metadata refusal")
            prefix.side_effect = failed
            with self.assertRaises(ValueError) as refused:
                newest.validate_current_sources(ROOT)
            self.assertIs(failed, refused.exception)
            document.assert_not_called()
        with patch.object(joint, "_descriptor_source_io_supported", return_value=False), \
                patch.object(newest, "_document", side_effect=OriginalTailReached):
            with self.assertRaises(OriginalTailReached):
                newest.validate_current_sources(ROOT)




if __name__ == "__main__":
    unittest.main()
