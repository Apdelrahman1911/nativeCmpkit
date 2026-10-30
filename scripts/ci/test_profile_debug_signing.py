"""Synthetic owned debug-signing guards, not Apple signing or memory evidence."""
import hashlib
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ios_ui_application as app


class ProfileDebugSigningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = self.root / "build/ci-verification/owned-profile/session/NativeCmpkitLibraryTests.app"
        self.bundle.mkdir(parents=True)
        self.input = self.bundle.parent / "owned-image-profile-debug.entitlements.plist"
        self.commands = []
        self.details = {}
        self.focus = app.lt.IOS_IMAGE_PROFILE_RECOVERY_FOCUS

    def control(self, command, timeout):
        self.commands.append((command, timeout))
        if "--display" in command:
            return subprocess.CompletedProcess(command, 0, plistlib.dumps({"get-task-allow": True}), b"")
        self.assertEqual(["/usr/bin/codesign", "--force", "--sign", "-", "--entitlements",
                          str(self.input), str(self.bundle)], command)
        self.assertEqual(120, timeout)
        self.assertEqual({"get-task-allow": True}, plistlib.loads(self.input.read_bytes()))
        self.assertEqual(0o600, self.input.stat().st_mode & 0o777)
        return subprocess.CompletedProcess(command, 0, b"", b"")

    def sign(self, control=None):
        with patch.object(app, "execute_control", side_effect=control or self.control):
            return app.sign_owned_debug_profile_application(self.root, self.bundle, self.focus, self.details)

    def test_only_failed_darwin_profile_recovery_requests_one_explicit_debug_entitlement(self):
        self.assertEqual({"get-task-allow": True}, app.profile_debug_entitlements(self.focus))
        first = app.profile_debug_entitlements(self.focus)
        first["get-task-allow"] = False
        self.assertEqual({"get-task-allow": True}, app.profile_debug_entitlements(self.focus))
        with self.assertRaises(ValueError): app.profile_debug_entitlements("arbitrary-mode")

    def test_strict_full_and_other_library_modes_never_get_debug_entitlements(self):
        for focus in (None, *app.lt.UI_APPLICATION_FOCUS_SPECS):
            if focus != self.focus:
                with self.subTest(focus=focus):
                    self.assertIsNone(app.profile_debug_entitlements(focus))
        self.focus = app.lt.IOS_IMAGE_MEMORY_FOCUS
        with self.assertRaises(ValueError): self.sign()
        self.assertEqual([], self.commands)
        self.assertFalse(self.input.exists())

    def test_owned_exact_input_and_signed_readback_do_not_infer_attach_authorization(self):
        result = self.sign()
        self.assertEqual(0, result.returncode)
        self.assertTrue(self.details["owned_entitlement_input_removed"])
        self.assertEqual(hashlib.sha256(plistlib.dumps({"get-task-allow": True}, sort_keys=True)).hexdigest(),
                         self.details["requested_entitlements_sha256"])
        self.assertTrue(self.details["signed_debug_flag_observation"]["ios_debug_allowed"])
        self.assertFalse(self.details["signed_debug_flag_observation"]["mac_debug_allowed"])
        self.assertFalse(self.details["attach_authorization_proven"])
        self.assertFalse(self.details["public_framework_or_package_signing"])
        self.assertFalse(self.input.exists())
        self.assertEqual((["/usr/bin/codesign", "--display", "--entitlements", ":-", str(self.bundle)], 30),
                         self.commands[1])
        with self.assertRaises(ValueError): self.sign()
        self.assertEqual(2, len(self.commands), "A reused receipt must not silently retry signing")

    def test_signing_failure_still_removes_only_the_owned_input_without_readback(self):
        def fail(command, timeout):
            self.control(command, timeout)
            return subprocess.CompletedProcess(command, 21, b"", b"synthetic failure")
        self.assertEqual(21, self.sign(fail).returncode)
        self.assertEqual(1, len(self.commands))
        self.assertTrue(self.details["owned_entitlement_input_removed"])
        self.assertFalse(self.input.exists())
        self.assertNotIn("signed_debug_flag_observation", self.details)

    def test_missing_or_unexpected_signed_flags_fail_before_install_with_owned_cleanup(self):
        for flags in ({}, {"get-task-allow": False}, {"get-task-allow": True,
                     "com.apple.security.get-task-allow": True}):
            with self.subTest(flags=flags):
                self.details = {}
                def control(command, timeout):
                    if "--display" in command:
                        return subprocess.CompletedProcess(command, 0, plistlib.dumps(flags), b"")
                    return self.control(command, timeout)
                with self.assertRaises(ValueError): self.sign(control)
                self.assertFalse(self.input.exists())
                self.assertTrue(self.details["owned_entitlement_input_removed"])

    def test_preexisting_regular_symlink_and_hardlink_inputs_are_never_overwritten(self):
        outside = self.root / "foreign.plist"
        outside.write_bytes(b"foreign input must remain untouched")
        for kind in ("regular", "symlink", "hardlink"):
            with self.subTest(kind=kind):
                self.details = {}
                if kind == "regular": self.input.write_bytes(outside.read_bytes())
                elif kind == "symlink": self.input.symlink_to(outside)
                else: os.link(outside, self.input)
                with self.assertRaises((FileExistsError, ValueError)): self.sign()
                self.assertEqual(b"foreign input must remain untouched", outside.read_bytes())
                self.assertEqual(b"foreign input must remain untouched", self.input.read_bytes())
                self.input.unlink()
        self.assertEqual([], self.commands)

    def test_changed_owned_input_is_preserved_and_never_counted_as_cleanup(self):
        def change(command, timeout):
            result = self.control(command, timeout)
            if "--display" in command: self.input.write_bytes(b"changed owned input")
            return result
        with self.assertRaises(ValueError): self.sign(change)
        self.assertEqual(b"changed owned input", self.input.read_bytes())
        self.assertFalse(self.details["owned_entitlement_input_removed"])

    def test_non_verification_or_symlink_bundle_is_refused_without_signing(self):
        foreign = self.root / "Foreign.app"; foreign.mkdir()
        owned = self.bundle
        for invalid in (foreign, owned.parent / "Another.app"):
            invalid.mkdir(exist_ok=True); self.bundle = invalid
            with self.assertRaises(ValueError): self.sign()
        self.bundle = owned.parent / "NativeCmpkitLibraryTests.app-link"
        self.bundle.symlink_to(owned, target_is_directory=True)
        with self.assertRaises(ValueError): self.sign()
        self.assertEqual([], self.commands)


if __name__ == "__main__":
    unittest.main()
