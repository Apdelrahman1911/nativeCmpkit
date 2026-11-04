# SPDX-License-Identifier: Apache-2.0
"""NEW offline history controls, not current HOME behavior or native outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import camera_home_baseline_source_projection as history
import ios_geometry_simulator_source_projection as owned_history
from camera_home_affinity_source_projection import current_source_before_home_affinity

ROOT = Path(__file__).resolve().parents[2]
HELPER = "scripts/ci/android_camera_developer_prerequisite.py"
NATIVE = "calf-camera-picker/src/androidDeviceTest/kotlin/com/mohamedrejeb/calf/camerapicker/OwnedDeveloperSettingsUi.kt"
OWNING = {HELPER, NATIVE, "scripts/ci/camera_boot_busy_source_projection.py",
          "scripts/ci/camera_scalar_failfast_source_projection.py", "scripts/ci/test_android_camera_boot_busy.py",
          "scripts/ci/android_external328_source_projection.py"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def preserved_home_stage(relative, payload):
    # Admit the complete newest listed bytes before this dated HOME-stage pin.
    # Unlisted paths are not certified here; their original HOME pin still owns
    # them. This pure source view never replaces an actual helper/native input.
    from ios_geometry_simulator_source_projection import current_source_before_owned_geometry
    payload = current_source_before_owned_geometry(relative, payload)
    from camera_tooling566_source_projection import current_source_before_tooling566
    return current_source_before_tooling566(relative, payload)


class HomeBaselineHistoryTests(unittest.TestCase):
    def test_exact_six_complete_afterimages_roundtrip_to_unchanged_beforeimages(self):
        bindings = history._bindings()
        self.assertEqual(OWNING, set(bindings))
        for relative, binding in bindings.items():
            current = preserved_home_stage(relative, (ROOT / relative).read_bytes())
            previous = history.current_source_before_home_baseline(relative, current)
            self.assertEqual(binding["after_sha256"], sha(current))
            self.assertEqual(binding["before_sha256"], sha(previous))
            for fragment in binding["fragments"]:
                before, after = fragment["before"].encode(), fragment["after"].encode()
                self.assertEqual(fragment["before_fragment_sha256"], sha(before))
                self.assertEqual(fragment["after_fragment_sha256"], sha(after))
                self.assertEqual(1, previous.count(before))
                previous = previous.replace(before, after, 1)
            self.assertEqual(current, previous)

    def test_current_admission_refuses_old_partial_displaced_and_mutated_images(self):
        for relative in OWNING:
            current = preserved_home_stage(relative, (ROOT / relative).read_bytes())
            old = history.source_before_home_baseline(relative, current)
            for bad in (old, current[:-1], current + b"\n", b"", None, bytearray(current), current.decode(),
                        b"x" * (history.MAX_SOURCE_BYTES + 1)):
                with self.subTest(relative=relative, kind=type(bad).__name__), self.assertRaises(ValueError):
                    history.current_source_before_home_baseline(relative, bad)
            binding = history._bindings()[relative]
            fragment = binding["fragments"][0]
            after = fragment["after"].encode()
            displaced = current.replace(after, b"", 1) + after
            self.assertNotEqual(current, displaced)
            with self.assertRaises(ValueError):
                history.current_source_before_home_baseline(relative, displaced)

    def test_ancestor_peeling_is_idempotent_but_never_repairs_unknown_bytes(self):
        for relative in OWNING:
            current = preserved_home_stage(relative, (ROOT / relative).read_bytes())
            old = history.current_source_before_home_baseline(relative, current)
            self.assertEqual(old, history.peel_current_home_baseline_for_older_history(relative, current))
            self.assertEqual(old, history.peel_current_home_baseline_for_older_history(relative, old))
            unknown = current + b"\n# synthetic unknown source\n"
            self.assertEqual(unknown, history.peel_current_home_baseline_for_older_history(relative, unknown))
            with self.assertRaises(ValueError):
                history.source_before_home_baseline(relative, unknown)

    def test_shared_current_chain_keeps_all_original_source_pins_not_new_behavior(self):
        from android_external328_source_projection import current_source_for_history, source_before_android_external328
        original_pins = {HELPER: "0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26",
                         NATIVE: "a1fb76c6092881a3681ec38002b4820f1d0d8282727a4d18fa89968f6b8c5b50",
                         "scripts/ci/camera_scalar_failfast_source_projection.py":
                         "6858fbd343cefad52b709663fbf5e98bccfa52111c2a1b8fd6eff8d8536cdb12"}
        for relative, original_pin in original_pins.items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_home_baseline(relative, current)
            ancestor = current_source_for_history(relative, current)
            self.assertEqual(original_pin, sha(ancestor))
            self.assertEqual(source_before_android_external328(relative, previous), ancestor)
            with self.assertRaises(ValueError):
                current_source_for_history(relative, current + b"\n")
        self.assertEqual("0e47097d10f1886bec0ee8eebc280b29afb704dc47d09df1bbdb41ddaa651b26",
                         sha(current_source_for_history(HELPER, (ROOT / HELPER).read_bytes())))

    def test_direct_older_console_reader_retains_exact_hash_refusal_and_inverse(self):
        from camera_scalar_failfast_source_projection import camera197_helper_source_before_owned_console
        current = (ROOT / HELPER).read_text()
        older = camera197_helper_source_before_owned_console(current)
        self.assertEqual("da07bedb680e9ce36842bbf581f22bf7b3ebf8ab1c5d307b05745069c77bb5a4", sha(older.encode()))
        self.assertNotIn("parse_recent_home_baseline", older)
        for bad in (current + "\n", current.replace("action_boot = self.boot_id()", "action_boot = 'foreign'", 1)):
            self.assertNotEqual(current, bad)
            with self.assertRaises(AssertionError):
                camera197_helper_source_before_owned_console(bad)

    def test_manifest_is_ordinary_single_link_exact_and_bounded(self):
        raw = history.SPEC_PATH.read_bytes()
        self.assertEqual(history.SPEC_SHA256, sha(raw))
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-home-history-") as name:
            copied = Path(name) / "manifest.json"
            copied.write_bytes(raw)
            linked = copied.with_name("linked.json")
            linked.symlink_to(copied)
            with patch.object(history, "SPEC_PATH", linked), self.assertRaises(ValueError):
                history._bindings()
            linked.unlink()
            linked.hardlink_to(copied)
            with patch.object(history, "SPEC_PATH", copied), self.assertRaises(ValueError):
                history._bindings()
            linked.unlink()
            copied.write_bytes(raw + b"\n")
            with patch.object(history, "SPEC_PATH", copied), self.assertRaises(ValueError):
                history._bindings()

    def test_original_native_actions_cleanup_and_accepted_parser_sources_are_held(self):
        document = json.loads(history.SPEC_PATH.read_bytes())
        for relative, expected in document["added_behavior_sources"].items():
            self.assertEqual(expected, sha(current_source_before_home_affinity(relative, (ROOT / relative).read_bytes())), relative)
        for relative, expected in document["unchanged_native_inputs"].items():
            self.assertEqual(expected, sha(owned_history.current_source_before_owned_geometry(relative, (ROOT / relative).read_bytes())), relative)
        current = (ROOT / NATIVE).read_bytes()
        previous = history.current_source_before_home_baseline(NATIVE, current)
        def body(raw, name):
            text = raw.decode()
            start = text.index(name)
            end = text.find("\n    private fun ", start + len(name))
            return text[start:end if end >= 0 else len(text)]
        for name in ("fun setNative(", "private fun openSettings(", "private fun closeSettings(", "private fun runComplete("):
            self.assertEqual(body(previous, name), body(current, name), name)

    def test_latest_shared_entry_itself_is_bound_and_refuses_its_old_or_unknown_image(self):
        from android_external328_source_projection import current_source_for_history, source_before_android_external328
        relative = "scripts/ci/android_external328_source_projection.py"
        current = (ROOT / relative).read_bytes()
        stage = preserved_home_stage(relative, current)
        previous = history.current_source_before_home_baseline(relative, stage)
        self.assertEqual(source_before_android_external328(relative, previous), current_source_for_history(relative, current))
        for bad in (previous, current[:-1], current + b"\n", b"", bytearray(current), None):
            with self.subTest(kind=type(bad).__name__), self.assertRaises(ValueError):
                current_source_for_history(relative, bad)
        # A current-source request cannot use a listed older caller as a shortcut.
        for relative in (HELPER, NATIVE):
            current = (ROOT / relative).read_bytes()
            old = history.source_before_home_baseline(relative, current)
            with self.assertRaises(ValueError):
                current_source_for_history(relative, old)


if __name__ == "__main__":
    unittest.main()
