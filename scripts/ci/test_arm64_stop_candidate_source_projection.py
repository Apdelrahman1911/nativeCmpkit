# SPDX-License-Identifier: Apache-2.0
"""New exact source-history obligations; no accepted native/control replay."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import arm64_stop_candidate_source_projection as arm
import android_external328_source_projection as previous

ROOT = Path(__file__).resolve().parents[2]


class Arm64StopHistoryTests(unittest.TestCase):
    def test_three_exact_full_sources_roundtrip_and_preserve_original_eight_fragments(self):
        bindings = arm._bindings()
        self.assertEqual(set(bindings), {"scripts/ci/library_tests.py",
            "scripts/ci/android_external328_source_projection.py", "scripts/ci/test_android_external328_source_projection.py"})
        self.assertEqual(sum(len(row["fragments"]) for row in bindings.values()), 8)
        for relative, row in bindings.items():
            current = (ROOT / relative).read_bytes()
            self.assertEqual(hashlib.sha256(current).hexdigest(), row["after_sha256"])
            old = arm.current_source_before_arm64_stop_candidate(relative, current)
            self.assertEqual(hashlib.sha256(old).hexdigest(), row["before_sha256"])
            forward = old
            for fragment in row["fragments"]:
                self.assertEqual(forward.count(fragment["before"].encode()), 1)
                forward = forward.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, forward)
            self.assertEqual(old, arm.source_before_arm64_stop_candidate(relative, old))

    def test_current_admission_refuses_old_partial_unknown_oversize_types_and_identity_guessing(self):
        for relative in arm._bindings():
            current = (ROOT / relative).read_bytes()
            old = arm.source_before_arm64_stop_candidate(relative, current)
            for payload in (old, current[:-1], current + b"\n", b"unknown", b"", b"x" * (arm.MAX_SOURCE_BYTES + 1)):
                with self.subTest(relative=relative), self.assertRaises(ValueError):
                    arm.current_source_before_arm64_stop_candidate(relative, payload)
            for payload in (None, bytearray(current), current.decode()):
                with self.assertRaises(ValueError):
                    arm.source_before_arm64_stop_candidate(relative, payload)
        payload = (ROOT / "scripts/ci/library_tests.py").read_bytes()
        self.assertIs(arm.source_before_arm64_stop_candidate("unlisted", payload), payload)
        with self.assertRaises(ValueError):
            arm.current_source_before_arm64_stop_candidate("scripts/ci/android_external328_source_projection.py", payload)

    def test_all_fragment_bytes_hashes_unique_sites_and_complete_preimage_digest_are_mandatory(self):
        relative = "scripts/ci/library_tests.py"
        current = (ROOT / relative).read_bytes()
        bindings = arm._bindings()
        for field in ("before", "after", "before_fragment_sha256", "after_fragment_sha256"):
            changed = copy.deepcopy(bindings)
            changed[relative]["fragments"][0][field] += "corruption"
            with patch.object(arm, "_bindings", return_value=changed), self.assertRaises(ValueError):
                arm.source_before_arm64_stop_candidate(relative, current)
        changed = copy.deepcopy(bindings)
        changed[relative]["before_sha256"] = "0" * 64
        with patch.object(arm, "_bindings", return_value=changed), self.assertRaises(ValueError):
            arm.source_before_arm64_stop_candidate(relative, current)

    def test_manifest_mutation_alias_links_empty_and_oversize_are_not_admitted(self):
        raw = arm.SPEC_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "spec.json"
            for payload in (raw + b"\n", b"{}", b"", b"x" * (arm.MAX_SPEC_BYTES + 1)):
                file.write_bytes(payload)
                with patch.object(arm, "SPEC_PATH", file), self.assertRaises(ValueError):
                    arm._bindings()
            file.write_bytes(raw)
            symbolic = root / "symbolic"
            symbolic.symlink_to(file)
            with patch.object(arm, "SPEC_PATH", symbolic), self.assertRaises(ValueError):
                arm._bindings()
            hard = root / "hard"
            hard.hardlink_to(file)
            with patch.object(arm, "SPEC_PATH", hard), self.assertRaises(ValueError):
                arm._bindings()

    def test_actual_current_composes_old_inverse_without_ever_admitting_an_old_source_as_current(self):
        relative = "scripts/ci/library_tests.py"
        actual = (ROOT / relative).read_bytes()
        old_current = arm.source_before_arm64_stop_candidate(relative, actual)
        historical = previous.source_before_android_external328(relative, actual)
        self.assertEqual(hashlib.sha256(historical).hexdigest(), previous._bindings()[relative]["before_sha256"])
        self.assertEqual(previous.current_source_for_history(relative, actual), historical)
        self.assertEqual(previous.source_before_android_external328(relative, historical), historical)
        for payload in (old_current, historical):
            with self.assertRaises(ValueError):
                previous.current_source_for_history(relative, payload)

    def test_old_manifest_all_hash_literals_native_sources_and_xml_acceptance_are_preserved(self):
        self.assertEqual(hashlib.sha256(previous.SPEC_PATH.read_bytes()).hexdigest(),
                         "ec166c161309144efd8ffc2b5726a7fa98cbd0f83a6becbfd37ea539562a2c7a")
        old = json.loads(previous.SPEC_PATH.read_bytes())
        self.assertEqual(len(old["bindings"]), 16)
        self.assertEqual(sum(len(row["fragments"]) for row in old["bindings"].values()), 49)
        core = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertNotIn("arm64_stop_candidate_source_projection", core)
        start = '        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_DESKTOP_REQUEST_FOCUSES:\n'
        end = '        elif boundary_focus and test_plan["explicit_test_focus"] in WEBVIEW_IDENTITY_FOCUSES:\n'
        branch = start + core.split(start, 1)[1].split(end, 1)[0]
        self.assertEqual(hashlib.sha256(branch.encode()).hexdigest(),
                         "b3df23f2636d6c1a420294d9ebdc8d37c8f24c0eb455fd1589dcb4e9447e00ad")
        native = {
            "DesktopWebViewRequestStateAcceptanceTest.kt": "c08bcdc062d18d24c5a370aaa818a8171c352d06acca35af1202fd4eb2c13f13",
            "DesktopWebViewStopRedirectAcceptanceTest.kt": "8eb3cbe9e91974c423998eb3007ed64ed9d98863dcc27d0b72da901caad411a3",
            "BoundedDesktopAwtWindow.kt": "c7bccc89f020490ea6198b837c7a9e386b051a0926ec22e17b3557699420b082",
        }
        path = ROOT / "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web"
        for name, expected in native.items():
            self.assertEqual(hashlib.sha256((path / name).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
