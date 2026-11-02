# SPDX-License-Identifier: Apache-2.0
"""NEW CI245 source-bridge controls; not library/native/platform test passes.

Select only inert functions and class setup/teardown. No historical test method,
model driver, compiler, SDK, network or native command is imported or executed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

if __package__:
    from .terminal_awt240_source_projection import source_before_terminal_awt240, text_before_terminal_awt240
else:
    from terminal_awt240_source_projection import source_before_terminal_awt240, text_before_terminal_awt240

ROOT = Path(__file__).resolve().parents[2]
SPEC = "scripts/ci/fixtures/ci245-terminal-source-bridge.json"
SPEC_SHA256 = "5d3ff2fe79b61b8486b2bd83542670626894656fec141d4869d01dcac442a720"
ALERT = "scripts/ci/test_ui_alert_container_timeout_observation.py"
HISTORY = "scripts/ci/test_ui_alert_important_recovery.py"
CI213 = "scripts/ci/test_camera_ci213_source_projection.py"
CI224 = "scripts/ci/test_ci224_shared_source_composition.py"
NATIVE_AND_PLANNER_SHA256 = {'calf-share/src/iosMain/kotlin/com/mohamedrejeb/calf/share/ShareLauncher.ios.kt': 'f09c7c66584ede4d55f248412275c11d372fad6d59619fa73147e4123c98407f', 'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/IosSharePresentationOwnershipTest.kt': '3578abbb43e545201da1d4846f68547ac7ca01e0221e3a5c68aa81f629ee9d05', 'calf-share/src/iosTest/kotlin/com/mohamedrejeb/calf/share/ShareTerminalBarrierScenarios.kt': 'c60c9aa31dc3e23734184ced80b2911ac655ec105d7197c5defad56bf8e84679', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindow.kt': 'c7bccc89f020490ea6198b837c7a9e386b051a0926ec22e17b3557699420b082', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/BoundedDesktopAwtWindowTest.kt': '0ab669d606bc6416e892f8509a694758c5a24447f904ed439de763886597bdc5', 'calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewStopRedirectAcceptanceTest.kt': '8eb3cbe9e91974c423998eb3007ed64ed9d98863dcc27d0b72da901caad411a3', 'scripts/ci/library_tests.py': '5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2', 'scripts/ci/terminal_awt240_source_projection.py': 'e839883e8c80a49de66ff334489dadd4189b40a862d924920ffa35fc35b2ae1d', 'scripts/ci/fixtures/terminal-awt240-source-inverse.json': '57aea63782e79cf6bce95c4d443c73bceaf2c7a4e1a4d74d963bbb82e7eb69b2'}  # Exact unchanged c660de30 owning inputs.


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def current_bytes(relative):
    """Raw current admission precedes the unchanged CI245/terminal historical pins."""
    from android_external328_source_projection import read_current_source_for_history
    return read_current_source_for_history(ROOT / relative, ROOT)


def assignment(source, name):
    matches = [n for n in ast.parse(source).body if isinstance(n, ast.Assign) and
               any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    if len(matches) != 1:
        raise ValueError("One exact inert declaration is required")
    return matches[0]


def literal(source, name):
    # Only simple, explicit string-name aliases are resolved. No evaluation of
    # imports, functions, attributes, operators or top-level statements.
    aliases = {n.targets[0].id: n.value.value for n in ast.parse(source).body
               if isinstance(n, ast.Assign) and len(n.targets) == 1 and
               isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant) and
               type(n.value.value) is str}

    class Names(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id not in aliases:
                raise ValueError("Unknown literal alias")
            return ast.copy_location(ast.Constant(aliases[node.id]), node)

    return ast.literal_eval(Names().visit(copy.deepcopy(assignment(source, name).value)))


def raw_methods(source):
    return {c.name + "." + n.name: ast.get_source_segment(source, n)
            for c in ast.parse(source).body if isinstance(c, ast.ClassDef)
            for n in c.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")}


def original_source(relative, current, binding):
    from android_external328_source_projection import source_before_android_external328
    current = source_before_android_external328(relative, current)
    if type(current) is not bytes or digest(current) != binding["after_sha256"]:
        raise ValueError("Exact reviewed postimage required")
    restored = current
    for fragment in reversed(binding["fragments"]):
        old, new = fragment["before"].encode(), fragment["after"].encode()
        if (digest(old) != fragment["before_fragment_sha256"] or
                digest(new) != fragment["after_fragment_sha256"] or restored.count(new) != 1):
            raise ValueError("Exact unique inverse required")
        restored = restored.replace(new, old, 1)
    if digest(restored) != binding["before_sha256"]:
        raise ValueError("Whole original source required")
    forward = restored
    for fragment in binding["fragments"]:
        old, new = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(old) != 1:
            raise ValueError("Exact unique forward site required")
        forward = forward.replace(old, new, 1)
    if forward != current:
        raise ValueError("Exact current round-trip required")
    return restored


class CI245TerminalBridgeControls(unittest.TestCase):
    def setUp(self):
        raw = (ROOT / SPEC).read_bytes()
        self.assertEqual(SPEC_SHA256, digest(raw))
        self.spec = json.loads(raw)
        self.assertEqual("c660de30f4ede3303dd4af27614082ed2bb5abd1", self.spec["baseline_head"])
        self.sources = {r: current_bytes(r).decode() for r in self.spec["bindings"]}

    def alert_namespace(self):
        source = self.sources[ALERT]
        names = ("RETAINED_ASSIGNMENTS", "OBSERVATION_DECLARATION", "INERT_FUNCTION_PINS", "SHARE188_OUTER_GUARD_PINS")
        namespace = {n: literal(source, n) for n in names}
        namespace.update(ast=ast, hashlib=hashlib, json=json, ROOT=ROOT, HISTORICAL=HISTORY,
                         source_before_terminal_awt240=source_before_terminal_awt240,
                         text_before_terminal_awt240=text_before_terminal_awt240)
        selected = {"digest", "portable_ast", "ast_digest", "raw_node", "compose_share188_outer_guard", "authored_guard_namespace"}
        functions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name in selected]
        self.assertEqual(len(selected), len(functions))
        self.assertFalse(any(isinstance(n, (ast.ClassDef, ast.Import, ast.ImportFrom))
                             for n in ast.walk(ast.Module(body=functions, type_ignores=[]))))
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<ci245-inert-byte-functions-only>", "exec"), namespace)
        return namespace

    def test_new_three_whole_images_and_eleven_fragments_round_trip_without_native_or_planner_changes(self):
        self.assertEqual({ALERT, CI213, CI224}, set(self.spec["bindings"]))
        self.assertEqual(11, sum(len(b["fragments"]) for b in self.spec["bindings"].values()))
        for relative, binding in self.spec["bindings"].items():
            original_source(relative, (ROOT / relative).read_bytes(), binding)
        self.assertGreaterEqual(len(NATIVE_AND_PLANNER_SHA256), 9)
        for relative, expected in NATIVE_AND_PLANNER_SHA256.items():
            self.assertEqual(expected, digest(current_bytes(relative)))

    def test_all_original_alert_and_camera_bodies_and_three_ci224_assertion_bodies_are_retained(self):
        for relative, count in ((ALERT, 6), (CI213, 5), (CI224, 5)):
            current = self.sources[relative]
            before = original_source(relative, current.encode(), self.spec["bindings"][relative]).decode()
            old_methods, methods = raw_methods(before), raw_methods(current)
            self.assertEqual(count, len(methods)); self.assertEqual(set(old_methods), set(methods))
            changed = {n for n in methods if methods[n] != old_methods[n]}
            if relative != CI224:
                self.assertFalse(changed)
            else:
                self.assertEqual({"CI224SharedSourceCompositionTests.test_ci224_01_current_share_images_reverse_before_the_intact_alert_and_wasm_chain",
                                  "CI224SharedSourceCompositionTests.test_ci224_02_missing_duplicate_or_modified_outer_symbols_refuse_before_compilation",
                                  "CI224SharedSourceCompositionTests.test_ci224_03_old_partial_wrong_type_and_mutated_share_images_remain_refused"}, changed)
                for name in changed:
                    restored = methods[name].replace("payload = source_before_terminal_awt240(relative, self.payloads[relative])", "payload = self.payloads[relative]")
                    restored = restored.replace("source = text_before_terminal_awt240(HISTORY, self.sources[HISTORY])", "source = self.sources[HISTORY]")
                    self.assertEqual(old_methods[name], restored)
            self.assertNotIn("@unittest.skip", current)
            self.assertNotIn("@unittest.expectedFailure", current)

    def test_current_alert_namespace_projects_before_exact_symbol_checks_and_keeps_original_chain(self):
        guard = self.alert_namespace()
        history = (ROOT / HISTORY).read_text()
        _, _, namespace = guard["authored_guard_namespace"](history)
        combined = namespace["source_before_share_alert153_rebase"]
        for relative, binding in namespace["SHARE_ALERT153_REBASE"].items():
            payload = (ROOT / relative).read_bytes()
            self.assertEqual(binding["original153_sha256"], digest(combined(relative, payload)))
        with patch.dict(guard, {"exec": lambda *a, **k: self.fail("Unreviewed history reached compilation")}):
            for bad in (history + "\n", history[:-1], "unreviewed", None):
                with self.assertRaises(ValueError):
                    guard["authored_guard_namespace"](bad)
        for relative in namespace["SHARE188_FAILED_ONLY_REBASE"]:
            payload = (ROOT / relative).read_bytes()
            for bad in (payload + b"\n", payload[:-1], None, payload.decode(), bytearray(payload)):
                with self.assertRaises(ValueError):
                    combined(relative, bad)

    def test_finite_current_overlays_match_actual_sources_and_original_literals_not_generic_repinning(self):
        for relative, expected_size in ((CI213, 2), (CI224, 6)):
            source = self.sources[relative]
            before = original_source(relative, source.encode(), self.spec["bindings"][relative]).decode()
            self.assertEqual(ast.get_source_segment(before, assignment(before, "EXPECTED")),
                             ast.get_source_segment(source, assignment(source, "EXPECTED")))
            original = literal(source, "EXPECTED")
            overlay = literal(source, "CURRENT_TERMINAL_AWT240_SOURCE_SHA256")
            self.assertEqual(expected_size, len(overlay))
            self.assertLessEqual(set(overlay), set(original))
            current = {**original, **overlay}
            for path, expected in current.items():
                self.assertEqual(expected, digest(current_bytes(path)))
            updates = [n for n in ast.parse(source).body if isinstance(n, ast.Expr) and
                       isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and
                       isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == "EXPECTED"]
            self.assertEqual(1, len(updates))
            self.assertEqual(ast.dump(ast.parse("EXPECTED.update(CURRENT_TERMINAL_AWT240_SOURCE_SHA256)").body[0], include_attributes=False),
                             ast.dump(updates[0], include_attributes=False))

    def test_both_exact_setups_and_teardowns_qualify_actual_bytes_without_old_method_execution(self):
        for relative, name in ((CI213, "CameraCI213ProjectionTests"), (CI224, "CI224SharedSourceCompositionTests")):
            # Exercise the new raw-current reader, not an extracted older setup.
            source = (ROOT / relative).read_text()
            original = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == name)
            functions = [copy.deepcopy(n) for n in original.body if isinstance(n, ast.FunctionDef) and n.name in {"setUpClass", "tearDownClass"}]
            self.assertEqual(2, len(functions))
            holder = ast.ClassDef(name="CI245SetupOnly", bases=[ast.Attribute(ast.Name("unittest", ast.Load()), "TestCase", ast.Load())],
                                  keywords=[], body=functions, decorator_list=[])
            if "type_params" in ast.ClassDef._fields:
                holder.type_params = []
            module = ast.fix_missing_locations(ast.Module(body=[holder], type_ignores=[]))
            self.assertFalse(any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in ast.walk(module)))
            expected = {**literal(source, "EXPECTED"), **literal(source, "CURRENT_TERMINAL_AWT240_SOURCE_SHA256")}
            namespace = {"unittest": unittest, "ROOT": ROOT, "EXPECTED": expected, "digest": digest}
            exec(compile(module, "<ci245-owning-setup-and-teardown-only>", "exec"), namespace)
            fixture = namespace["CI245SetupOnly"]
            fixture.setUpClass()
            self.assertEqual(expected, {r: digest(b) for r, b in fixture.payloads.items()})
            fixture.tearDownClass()
            with tempfile.TemporaryDirectory() as folder:
                synthetic = Path(folder)
                for path in expected:
                    destination = synthetic / path; destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes((ROOT / path).read_bytes())
                changed = synthetic / next(iter(expected)); changed.write_bytes(changed.read_bytes() + b"\n")
                with patch.dict(namespace, {"ROOT": synthetic}), self.assertRaises(AssertionError):
                    fixture.setUpClass()

    def test_new_alert_setup_keeps_projected_source_and_ast_raw_coordinates_together(self):
        current = self.sources[ALERT]
        before = original_source(ALERT, current.encode(), self.spec["bindings"][ALERT]).decode()

        def setup_only(source):
            owner = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and
                         n.name == "AlertContainerTimeoutNewSourceControls")
            functions = [copy.deepcopy(n) for n in owner.body if isinstance(n, ast.FunctionDef) and n.name == "setUp"]
            self.assertEqual(1, len(functions))
            holder = ast.ClassDef(name="CI247AlertSetupOnly", bases=[ast.Attribute(ast.Name("unittest", ast.Load()), "TestCase", ast.Load())],
                                  keywords=[], body=functions, decorator_list=[])
            if "type_params" in ast.ClassDef._fields:
                holder.type_params = []
            module = ast.fix_missing_locations(ast.Module(body=[holder], type_ignores=[]))
            self.assertFalse(any(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in ast.walk(module)))
            namespace = self.alert_namespace()
            namespace.update(unittest=unittest, NATIVE="calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativeAlertImportantRegressionTest.kt")
            exec(compile(module, "<ci247-alert-setup-only-no-historical-test-bodies>", "exec"), namespace)
            fixture = namespace["CI247AlertSetupOnly"]()
            fixture.setUp()
            return fixture

        projected = text_before_terminal_awt240(HISTORY, (ROOT / HISTORY).read_text())
        fixture = setup_only(current)
        self.assertEqual(projected, fixture.historical)
        self.assertEqual(ast.dump(ast.parse(projected), include_attributes=True),
                         ast.dump(fixture.parsed, include_attributes=True))
        expected = literal(current, "ACCEPTED_METHODS")
        owner = next(n for n in fixture.parsed.body if isinstance(n, ast.ClassDef) and
                     n.name == "AlertImportantRecoveryNewOnlyTests")
        methods = [n for n in owner.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        self.assertEqual(19, len(methods))
        guard = self.alert_namespace()
        for node in methods:
            self.assertEqual(expected[node.name]["raw_sha256"], digest(guard["raw_node"](fixture.historical, node)))
        # The actual failed246 setup kept current text beside a projected AST.
        # Reconstruct only that setup, not any historical test method or driver.
        mismatched = setup_only(before)
        self.assertNotEqual(projected, mismatched.historical)
        self.assertEqual(19, sum(expected[n.name]["raw_sha256"] != digest(guard["raw_node"](mismatched.historical, n))
                                 for n in methods))


if __name__ == "__main__":
    unittest.main()
