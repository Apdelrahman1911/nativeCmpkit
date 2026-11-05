# SPDX-License-Identifier: Apache-2.0
"""NEW owning source/metadata controls only, never SDK/build/KVM/native acceptance."""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import os
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import test_android_combined_finite_routing as combined
import test_android_kvm_timeline as timeline


class PermissionManifestKvmContextControls(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack(); self.addCleanup(self.guards.close)
        def forbidden(*args, **kwargs):
            raise AssertionError("Owning source contexts cannot execute external/host/native operations")
        for module, names in ((subprocess, ("Popen", "run", "check_call", "check_output")),
                              (socket, ("socket", "create_connection", "getaddrinfo")),
                              (os, ("system", "kill", "killpg"))):
            for name in names: self.guards.enter_context(patch.object(module, name, forbidden))
        self.payload = (combined.ROOT / combined.CORE / "src/androidDeviceTest/AndroidManifest.xml").read_bytes()

    def test_three_actual_signature_owners_and_each_missing_duplicate_or_foreign_control_refuse(self):
        manifest = combined.signature_control_source_manifest(self.payload)
        controls = combined.actual_signature_controls()
        self.assertEqual([combined.demo.PERMISSION, combined.lifecycle.PERMISSION, combined.probe.PERMISSION], controls)
        self.assertEqual(3, len(set(controls)))
        for control in controls:
            with self.subTest(missing=control):
                changed = deepcopy(manifest)
                changed.remove(next(node for node in changed.findall("uses-permission") if node.get(combined.probe.ANDROID + "name") == control))
                with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(changed))
            with self.subTest(duplicate=control):
                changed = deepcopy(manifest)
                ET.SubElement(changed, "uses-permission", {combined.probe.ANDROID + "name": control})
                with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(changed))
        for foreign in ("foreign.signature.CONTROL", "android.permission.CAMERA", combined.probe.WRITE, combined.probe.ALL_FILES):
            with self.subTest(foreign=foreign):
                changed = deepcopy(manifest)
                ET.SubElement(changed, "uses-permission", {combined.probe.ANDROID + "name": foreign})
                with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(changed))
        changed = deepcopy(manifest)
        ET.SubElement(changed, "uses-permission-sdk-23", {combined.probe.ANDROID + "name": controls[0]})
        with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(changed))
        changed = deepcopy(manifest)
        changed.find("uses-permission").set(combined.probe.ANDROID + "maxSdkVersion", "35")
        with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(changed))
        with self.assertRaises(ValueError): combined.signature_control_source_manifest(b'<!DOCTYPE manifest [<!ENTITY owned "ignored">]><manifest/>')

    def test_signature_metadata_owners_must_agree_and_order_drift_cannot_widen_the_whitelist(self):
        for module, attribute in ((combined.demo, "PERMISSION"), (combined.lifecycle, "PERMISSION"),
                                  (combined.probe, "PERMISSION"), (combined.probe, "PERMISSION_DEMO_BIND"),
                                  (combined.probe, "PERMISSION_LIFECYCLE_CONTROL"), (combined.lifecycle, "REPORTER")):
            with self.subTest(owner=module.__name__, attribute=attribute), patch.object(module, attribute, "foreign.signature.CONTROL"):
                with self.assertRaises(ValueError): combined.actual_signature_controls()
        manifest = combined.signature_control_source_manifest(self.payload)
        rows = list(manifest.findall("uses-permission"))
        for row in rows: manifest.remove(row)
        for row in reversed(rows): manifest.insert(0, row)
        # Explicitly move the first current control after the last; metadata stays owned.
        first = manifest.find("uses-permission"); manifest.remove(first); manifest.append(first)
        with self.assertRaises(ValueError): combined.signature_control_source_manifest(ET.tostring(manifest))

    def test_KVM_context_uses_actual_lifecycle_and_callback_admission_not_synthetic_noops(self):
        lifecycle, callback = timeline.selected_admission_dependencies()
        self.assertEqual(35, lifecycle.API)
        self.assertEqual("calf-permissions/core", lifecycle.MODULE)
        self.assertEqual(3, len(lifecycle.FOCUSES))
        self.assertEqual("calf-camera-picker", callback.MODULE)
        self.assertEqual("android-camera-callback-substitution", callback.FOCUS)
        self.assertIsNone(lifecycle.validate_request(35, (lifecycle.MODULE,), sorted(lifecycle.FOCUSES)[0]))
        with self.assertRaises(ValueError): lifecycle.validate_request(True, (lifecycle.MODULE,), sorted(lifecycle.FOCUSES)[0])
        with self.assertRaises(ValueError): lifecycle.validate_request(35, ("calf-io",), sorted(lifecycle.FOCUSES)[0])
        self.assertIsNone(callback.validate_discovery("android-device", (lifecycle.MODULE,), "android-permission-demo-contracts", (callback.FOCUS,)))
        for modules in (None, (), (callback.MODULE,)):
            with self.subTest(unfiltered=modules), self.assertRaises(ValueError):
                callback.validate_discovery("android-device", modules, None, (callback.FOCUS,))
        with self.assertRaises(ValueError): callback.validate_api(True, (callback.MODULE,))
        with self.assertRaises(ValueError): callback.validate_api(23, (callback.MODULE,))

    def test_KVM_context_missing_or_ambiguous_actual_declarations_refuse_without_host_or_planner(self):
        relatives = ("scripts/ci/android_permission_lifecycle_contract.py", "scripts/ci/android_camera_callback_native_focus.py")
        originals = {relative: (timeline.ROOT / relative).read_text(encoding="utf-8") for relative in relatives}
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-manifest-kvm-source-") as temporary:
            root = Path(temporary)
            for relative, text in originals.items():
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding="utf-8")
            with patch.object(timeline, "ROOT", root):
                lifecycle, callback = timeline.selected_admission_dependencies()
                self.assertEqual(3, len(lifecycle.FOCUSES)); self.assertEqual("calf-camera-picker", callback.MODULE)
                for relative, mutations in (
                    (relatives[0], (originals[relatives[0]] + "\nMODULE = 'foreign'\n", originals[relatives[0]].replace("def validate_plan(", "def missing_validate_plan(", 1))),
                    (relatives[1], (originals[relatives[1]] + "\nFOCUS = 'foreign'\n", originals[relatives[1]].replace("def validate_api(", "def missing_validate_api(", 1))),
                ):
                    target = root / relative
                    for mutation in mutations:
                        # New source negative controls, not historical or accepted-method replay.
                        target.write_text(mutation, encoding="utf-8")
                        with self.subTest(source=relative), self.assertRaises(ValueError): timeline.selected_admission_dependencies()
                        target.write_text(originals[relative], encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
