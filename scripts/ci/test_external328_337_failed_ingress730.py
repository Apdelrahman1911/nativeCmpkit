# SPDX-License-Identifier: Apache-2.0
"""NEW finite controls for original730 failed external/import boundary recovery.

No old history/test/native method is invoked. Only current ordinary source,
exact complete inverses as DATA and immutable owning guard ASTs are compared.
No source, expected old pin, SDK, compiler, process, Git or network mutation.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = "scripts/ci/android_external328_source_projection.py"
SHARED = "scripts/ci/macos_share_ci668_composition.py"
EXTERNAL328 = "scripts/ci/test_android_external328_source_projection.py"
EXTERNAL337 = "scripts/ci/test_android_external337_fixture_recovery.py"
CONTROLLER = "scripts/ci/android_device_tests.py"
IO_MANIFEST = "calf-io/src/androidDeviceTest/AndroidManifest.xml"


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def declared(source, name):
    rows = [node.value for node in ast.parse(source).body if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(rows) != 1:
        raise AssertionError("One exact inert source declaration required")
    return ast.literal_eval(rows[0])


def owning_function(relative, name):
    rows = [node for node in ast.parse((ROOT / relative).read_text()).body
            if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(rows) != 1:
        raise AssertionError("One exact owning function source required")
    return rows[0]


class External328337FailedIngress730Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.held = {relative: (ROOT / relative).read_bytes() for relative in
                    (BRIDGE, SHARED, EXTERNAL328, EXTERNAL337, CONTROLLER, IO_MANIFEST,
                     "scripts/ci/fixtures/android-external328-source-inverse.json",
                     "scripts/ci/fixtures/android-permission-lifecycle-source-inverse.json",
                     "scripts/ci/fixtures/macos-share-ci668-composition.json",
                     "scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json")}

    @classmethod
    def tearDownClass(cls):
        if any((ROOT / relative).read_bytes() != payload for relative, payload in cls.held.items()):
            raise AssertionError("Actual external730 source/manifest/native bytes changed")

    def test01_raw_android_then_after_only_budget_then_geometry_has_no_inner_raw_readmission(self):
        owner = owning_function(BRIDGE, "current_source_for_history")
        choices = [node for node in owner.body if isinstance(node, ast.If) and
                   ast.dump(node.test, include_attributes=False) ==
                   ast.dump(ast.parse("relative in ANDROID_PATCH_PATHS", mode="eval").body,
                            include_attributes=False)]
        self.assertEqual(1, len(choices))
        choice = choices[0]
        calls = [node.value.func.id for node in choice.body if isinstance(node, ast.Assign) and
                 isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)]
        self.assertEqual(["source_before_android_lifecycle", "peel_budget707_for_history",
                          "source_before_owned_geometry"], calls)
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and
                             node.func.id.startswith("current_source_") for node in ast.walk(ast.Module(body=choice.body, type_ignores=[]))))
        other_calls = [node.value.func.id for node in choice.orelse if isinstance(node, ast.Assign) and
                       isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)]
        self.assertEqual(["current_source_before_owned_geometry"], other_calls)
        android = json.loads(self.held["scripts/ci/fixtures/android-permission-lifecycle-source-inverse.json"])
        budget_paths = declared(self.held[SHARED].decode(), "BUDGET707_FRAGMENT_COUNTS")
        self.assertEqual({".github/workflows/gradle.yml"}, set(android["original_bindings"]) & set(budget_paths))
        joint = json.loads(self.held["scripts/ci/fixtures/macos-share-ci668-composition.json"])
        workflow = ".github/workflows/gradle.yml"
        self.assertEqual(android["original_bindings"][workflow]["before_sha256"],
                         joint["derivative_bindings"][workflow]["after_sha256"])
        self.assertEqual(joint["derivative_bindings"][workflow]["before_sha256"],
                         joint["predecessor_inputs"]["final_ci175"][workflow]["sha256"])

    def test02_actual_native_manifest_is_held_and_only_immutable_io_data_inverse_matches_old328_pin(self):
        import android_external328_source_projection as bridge
        import android_io_remote_routing_source_projection as remote
        old = declared(self.held[EXTERNAL328].decode(), "NATIVE_INPUTS")
        row = json.loads(self.held["scripts/ci/fixtures/android-io-controlled-remote-routing-source-inverse.json"])["bindings"][IO_MANIFEST]
        current = self.held[IO_MANIFEST]
        self.assertEqual((row["after_sha256"], row["after_bytes"]), (sha(current), len(current)))
        self.assertEqual(old[IO_MANIFEST], row["before_sha256"])
        self.assertEqual("397d45d9201637e6a696b3c4148376bb02fe5c4bb1070c541616bdcdaefeeb19", old[IO_MANIFEST])
        ancestor = bridge.current_source_for_history(IO_MANIFEST, current)
        self.assertEqual((row["before_sha256"], row["before_bytes"]), (sha(ancestor), len(ancestor)))
        self.assertNotEqual(current, ancestor)
        self.assertEqual(current, (ROOT / IO_MANIFEST).read_bytes())
        with self.assertRaises(ValueError):
            remote.current_source_before_remote_routing(IO_MANIFEST, ancestor)
        forward = ancestor
        for fragment in row["fragments"]:
            before, after = fragment["before"].encode(), fragment["after"].encode()
            self.assertEqual(fragment["before_fragment_sha256"], sha(before))
            self.assertEqual(fragment["after_fragment_sha256"], sha(after))
            self.assertEqual(1, forward.count(before))
            forward = forward.replace(before, after, 1)
        self.assertEqual(current, forward)

    def test03_controller_outer_raw_then_exact_android_then_old328_data_keeps_unknown_refusals(self):
        import android_external328_source_projection as bridge
        import macos_share_ci668_composition as joint
        raw = self.held[CONTROLLER]
        android = json.loads(self.held["scripts/ci/fixtures/android-permission-lifecycle-source-inverse.json"])["original_bindings"][CONTROLLER]
        self.assertNotEqual(android["after_sha256"], sha(raw))
        ancestor = joint.source_before_android_lifecycle(CONTROLLER, raw)
        self.assertEqual((android["before_sha256"], android["before_bytes"]), (sha(ancestor), len(ancestor)))
        old = json.loads(self.held["scripts/ci/fixtures/android-external328-source-inverse.json"])["bindings"][CONTROLLER]
        historical = bridge.current_source_for_history(CONTROLLER, raw)
        self.assertEqual((old["before_sha256"], old["before_bytes"]), (sha(historical), len(historical)))
        for candidate in (ancestor, historical, raw[:-1], raw + b"\n", b"foreign"):
            with self.subTest(size=len(candidate)), self.assertRaisesRegex(
                    ValueError, "^complete740-current-source-afterimage-required$"):
                joint.source_before_android_lifecycle(CONTROLLER, candidate)
        with self.assertRaisesRegex(ValueError, "^bounded-complete-share-CI-source-operands-required$"):
            joint.source_before_android_lifecycle(CONTROLLER, b"")


if __name__ == "__main__":
    unittest.main()
