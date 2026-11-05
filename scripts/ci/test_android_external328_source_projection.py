# SPDX-License-Identifier: Apache-2.0
"""NEW finite source-history controls, not Android/library/native test passes.

No accepted historical test method is imported or executed by these controls.
Each positive current admission precedes an exact old-source inverse. Negative
fixtures are private copies; no live source, expected old pin or native gate edits.
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

import android_external328_source_projection as bridge

ROOT = Path(__file__).resolve().parents[2]
SELECTORS = {
    ".github/workflows/gradle.yml", "scripts/ci/android_device_tests.py",
    "scripts/ci/library_tests.py", "scripts/ci/workflow_matrix.py",
}
READERS = {
    "scripts/ci/camera_ci213_source_projection.py",
    "scripts/ci/camera_scalar_failfast_source_projection.py",
    "scripts/ci/terminal_awt240_source_projection.py",
    "scripts/ci/test_android_camera205_owning_admission.py",
    "scripts/ci/test_android_camera_owned_avd_console_name.py",
    "scripts/ci/test_android_camera_pre_reporter_fail_fast.py",
    "scripts/ci/test_android_camera_startup_readiness.py",
    "scripts/ci/test_android_io_named_gate_details.py",
    "scripts/ci/test_camera_ci213_source_projection.py",
    "scripts/ci/test_ci224_shared_source_composition.py",
    "scripts/ci/test_ci245_terminal_source_bridge.py",
    "scripts/ci/test_terminal_awt240_source_projection.py",
}
NATIVE_INPUTS = {
    "calf-io/src/androidDeviceTest/AndroidManifest.xml": "397d45d9201637e6a696b3c4148376bb02fe5c4bb1070c541616bdcdaefeeb19",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoNamedSystemProviderTest.kt": "ec15772e36b8d5676d9d98a5742f38c3b97b85c51123f27637f50a7238ca4909",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/AndroidIoSystemTreeGrantActivity.kt": "760634c61aa94ffb04b16f94fc20ceb67f4c58aa06477ee6dde14c3dda24fdde",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/DeviceDescriptorProbe.kt": "941c43e90bd8d32f113b3dc0b863b4885459a4f17716825eb26ffbf8b320a78a",
    "calf-io/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/io/NamedSystemDocumentsUi.kt": "e0251e1f3cc8bb4c93791b978d84de5bc4eb18469873c4879c190dbdd93956a0",
}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def fixture_boundary(relative, method, root):
    """Compile only the changed source reader, never an old test method/body."""
    source = (ROOT / relative).read_text()
    methods = [node for node in ast.walk(ast.parse(source))
               if isinstance(node, ast.FunctionDef) and node.name == method]
    if len(methods) != 1 or method not in {"setUpClass", "tearDownClass"}:
        raise AssertionError("One exact setup/teardown-only source reader is required")
    holder = ast.ClassDef(name="BoundaryOnly", bases=[], keywords=[],
                          body=[copy.deepcopy(methods[0])], decorator_list=[])
    if "type_params" in ast.ClassDef._fields:
        holder.type_params = []
    module = ast.fix_missing_locations(ast.Module(body=[holder], type_ignores=[]))
    expected = {"scripts/ci/library_tests.py": "5012c3e2be83e62eba8239a0db12104d5f9f7efb3f262abd3b3080012f7afdc2"}
    namespace = {"ROOT": root, "TREE": root, "EXPECTED": expected,
                 "EXPECTED_SHA256": expected, "digest": digest}
    exec(compile(module, "<external328-changed-source-reader-only>", "exec"), namespace)
    return namespace["BoundaryOnly"]


class External328SourceHistoryControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_spec = bridge.SPEC_PATH.read_bytes()
        cls.bindings = bridge._bindings()
        cls.actual_current = {relative: (ROOT / relative).read_bytes() for relative in cls.bindings}
        from arm64_stop_candidate_source_projection import current_source_before_arm64_stop_candidate
        cls.current = {relative: current_source_before_arm64_stop_candidate(relative, payload)
                       for relative, payload in cls.actual_current.items()}
        cls.native_before = {relative: (ROOT / relative).read_bytes() for relative in NATIVE_INPUTS}

    @classmethod
    def tearDownClass(cls):
        if bridge.SPEC_PATH.read_bytes() != cls.raw_spec:
            raise AssertionError("The held current manifest changed")
        if any((ROOT / relative).read_bytes() != payload
               for relative, payload in {**cls.actual_current, **cls.native_before}.items()):
            raise AssertionError("An actual current source changed during the controls")

    def test_manifest_has_only_the_exact_four_selectors_and_twelve_historical_readers(self):
        self.assertEqual(SELECTORS | READERS, set(self.bindings))
        contract = json.loads(self.raw_spec)
        self.assertEqual("8bfe511c7e625aea5140bdee310663b09d7cc83d", contract["before_selector_revision"])
        self.assertEqual("cfbc16a80b9d93d734130e1151a93551456d7bfe", contract["before_fixture_revision"])
        self.assertEqual(49, sum(len(binding["fragments"]) for binding in self.bindings.values()))
        self.assertEqual(bridge.SPEC_SHA256, digest(self.raw_spec))
        self.assertTrue(all(not path.startswith("calf-") for path in self.bindings))

    def test_all_sixteen_actual_postimages_restore_exact_whole_sources_and_roundtrip(self):
        for relative, binding in self.bindings.items():
            with self.subTest(relative=relative):
                current = self.current[relative]
                self.assertEqual(binding["after_sha256"], digest(current))
                previous = bridge.current_source_for_history(relative, self.actual_current[relative])
                self.assertEqual(binding["before_sha256"], digest(previous))
                self.assertEqual(previous, bridge.source_before_android_external328(relative, previous))
                forward = previous
                for fragment in binding["fragments"]:
                    before, after = fragment["before"].encode(), fragment["after"].encode()
                    self.assertEqual(fragment["before_fragment_sha256"], digest(before))
                    self.assertEqual(fragment["after_fragment_sha256"], digest(after))
                    self.assertEqual(1, forward.count(before))
                    forward = forward.replace(before, after, 1)
                self.assertEqual(current, forward)

    def test_raw_current_admission_refuses_previous_truncated_appended_or_foreign_images(self):
        for relative, current in self.current.items():
            previous = bridge.source_before_android_external328(relative, current)
            for candidate in (previous, current[:-1], current + b"\n", b"foreign source", b""):
                with self.subTest(relative=relative, candidate_size=len(candidate)):
                    with self.assertRaises(ValueError):
                        bridge.current_source_for_history(relative, candidate)
            for candidate in (current[:-1], current + b"\n", b"foreign source", b""):
                with self.assertRaises(ValueError):
                    bridge.source_before_android_external328(relative, candidate)

    def test_wrong_types_and_oversized_listed_inputs_cannot_become_source_admission(self):
        relative = next(iter(self.current))
        for payload in (None, bytearray(self.current[relative]), self.current[relative].decode(), []):
            for function in (bridge.current_source_for_history, bridge.source_before_android_external328):
                with self.subTest(function=function.__name__, kind=type(payload).__name__):
                    with self.assertRaises(ValueError):
                        function(relative, payload)
        for identity in (None, Path(relative), [], 1):
            with self.assertRaises(ValueError):
                bridge.current_source_for_history(identity, self.current[relative])
        with self.assertRaises(ValueError):
            bridge.source_before_android_external328(relative, b"x" * (bridge.MAX_SOURCE_BYTES + 1))

    def test_fragment_hashes_missing_sites_and_whole_preimage_bindings_remain_mandatory(self):
        relative = "scripts/ci/android_device_tests.py"
        for field, value in (("before_fragment_sha256", "0" * 64), ("after_fragment_sha256", "0" * 64),
                             ("before", "missing old fragment"), ("after", "missing current fragment")):
            altered = copy.deepcopy(self.bindings)
            altered[relative]["fragments"][0][field] = value
            with patch.object(bridge, "_bindings", return_value=altered), self.assertRaises(ValueError):
                bridge.source_before_android_external328(relative, self.current[relative])
        altered = copy.deepcopy(self.bindings)
        altered[relative]["before_sha256"] = "0" * 64
        with patch.object(bridge, "_bindings", return_value=altered), self.assertRaises(ValueError):
            bridge.source_before_android_external328(relative, self.current[relative])

    def test_manifest_mutation_symlink_hardlink_empty_and_oversize_refuse(self):
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-external328-spec-") as name:
            root = Path(name)
            path = root / "spec.json"
            for value in (self.raw_spec + b"\n", b"{}", b"", b"x" * (bridge.MAX_SPEC_BYTES + 1)):
                path.write_bytes(value)
                with patch.object(bridge, "SPEC_PATH", path), self.assertRaises(ValueError):
                    bridge._bindings()
            path.write_bytes(self.raw_spec)
            linked = root / "linked.json"
            linked.symlink_to(path)
            with patch.object(bridge, "SPEC_PATH", linked), self.assertRaises(ValueError):
                bridge._bindings()
            hard = root / "hard.json"
            hard.hardlink_to(path)
            with patch.object(bridge, "SPEC_PATH", hard), self.assertRaises(ValueError):
                bridge._bindings()

    def test_path_reader_uses_explicit_relative_identity_and_refuses_private_previous_file(self):
        relative = "scripts/ci/android_device_tests.py"
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-external328-path-") as name:
            root = Path(name)
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(self.actual_current[relative])
            expected = bridge.source_before_android_external328(relative, self.current[relative])
            self.assertEqual(expected, bridge.read_current_source_for_history(path, root))
            path.write_bytes(expected)
            with self.assertRaises(ValueError):
                bridge.read_current_source_for_history(path, root)
            with self.assertRaises(ValueError):
                bridge.read_current_source_for_history(ROOT / relative, root)

    def test_unlisted_source_is_unchanged_not_digest_guessed_into_another_identity(self):
        payload = self.current["scripts/ci/android_device_tests.py"]
        self.assertIs(payload, bridge.source_before_android_external328("unlisted-source", payload))
        self.assertIs(payload, bridge.current_source_for_history("unlisted-source", payload))
        with self.assertRaises(ValueError):
            bridge.current_source_for_history("scripts/ci/library_tests.py", payload)

    def test_historical_pin_declarations_are_not_rebased_to_current_hashes(self):
        for relative in READERS:
            if not relative.startswith("scripts/ci/test_"):
                continue
            current = self.current[relative].decode()
            previous = bridge.source_before_android_external328(relative, self.current[relative]).decode()
            def pin_declarations(source):
                return {ast.get_source_segment(source, node) for node in ast.parse(source).body
                        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and
                           ("SHA256" in target.id or target.id in {"EXPECTED", "BOUND_SOURCE_BEFORE47", "BOUND_SOURCE_AFTER47"})
                           for target in node.targets)}
            self.assertEqual(pin_declarations(previous), pin_declarations(current), relative)

    def test_no_live_selector_imports_the_history_bridge_and_native_inputs_stay_unchanged(self):
        for relative in SELECTORS:
            self.assertNotIn(b"android_external328_source_projection", self.current[relative])
        # NATIVE_INPUTS is the immutable External328 stage, not a new checkout
        # or native acceptance map. Admit only the newly bound IO manifest at
        # RAW, then compare its exact old DATA view. The other four unchanged
        # native operands retain their original raw-byte pins; no unregistered
        # source is enrolled. tearDownClass still holds actual native_before.
        native_ancestor = dict(self.native_before)
        manifest = "calf-io/src/androidDeviceTest/AndroidManifest.xml"
        native_ancestor[manifest] = bridge.current_source_for_history(manifest, self.native_before[manifest])
        self.assertEqual(NATIVE_INPUTS, {relative: digest(payload) for relative, payload in native_ancestor.items()})
        self.assertEqual(self.native_before, {relative: (ROOT / relative).read_bytes() for relative in NATIVE_INPUTS})
        source = self.native_before[next(path for path in NATIVE_INPUTS if path.endswith("AndroidIoNamedSystemProviderTest.kt"))].decode()
        self.assertEqual(2, source.count("@Test"))
        self.assertNotIn("@Ignore", source)
        self.assertNotIn("@Disabled", source)
        workflow = self.current[".github/workflows/gradle.yml"].decode()
        self.assertIn("contents: read", workflow)
        self.assertNotIn("contents: write", workflow)

    def test_existing_inverse_refusal_categories_and_chains_remain_strict(self):
        import camera_scalar_failfast_source_projection as camera
        import camera_ci213_source_projection as ci213
        import terminal_awt240_source_projection as terminal
        controller = self.current["scripts/ci/android_device_tests.py"].decode()
        with self.assertRaisesRegex(AssertionError, "Full current controller bytes differ from the qualified afterimage"):
            camera.historical_controller_source(controller + "\n")
        with self.assertRaisesRegex(ValueError, "Unreviewed terminal/AWT240 source is not an admitted postimage"):
            terminal.source_before_terminal_awt240("scripts/ci/library_tests.py", self.current["scripts/ci/library_tests.py"] + b"\n")
        relative = "scripts/ci/test_android_camera_startup_readiness.py"
        with self.assertRaisesRegex(ValueError, "Full current CI213 source differs from the qualified postimage"):
            ci213.historical_source_before_camera213(relative, self.current[relative] + b"\n")
        restored = camera.historical_controller_source(controller)
        contract = json.loads((ROOT / "scripts/ci/fixtures/android-camera-scalar-failfast-controller-inverse.json").read_bytes())
        self.assertEqual(contract["before_sha256"], digest(restored.encode()))

    def test_mutated_current_class_admissions_keep_original_assertion_refusals(self):
        cases = {
            "scripts/ci/test_android_camera205_owning_admission.py": "An exact Camera205 source input hash is required",
            "scripts/ci/test_camera_ci213_source_projection.py": "An exact bounded owning source input is required",
            "scripts/ci/test_ci224_shared_source_composition.py": "An exact bounded current source image is required",
        }
        relative = "scripts/ci/library_tests.py"
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-external328-admission-") as name:
            root = Path(name)
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(self.current[relative] + b"\n")
            for source, message in cases.items():
                with self.subTest(source=source):
                    owner = fixture_boundary(source, "setUpClass", root)
                    with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                        owner.setUpClass()

    def test_mutated_current_teardowns_keep_original_assertion_refusals(self):
        cases = {
            "scripts/ci/test_camera_ci213_source_projection.py": "The owning source changed during these controls",
            "scripts/ci/test_ci224_shared_source_composition.py": "The admitted source changed during these controls",
        }
        relative = "scripts/ci/library_tests.py"
        previous = bridge.source_before_android_external328(relative, self.current[relative])
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-external328-teardown-") as name:
            root = Path(name)
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(self.current[relative] + b"\n")
            for source, message in cases.items():
                with self.subTest(source=source):
                    owner = fixture_boundary(source, "tearDownClass", root)
                    owner.payloads = {relative: previous}
                    with self.assertRaisesRegex(AssertionError, "^" + message + "$"):
                        owner.tearDownClass()


if __name__ == "__main__":
    unittest.main()
