"""Synthetic exact-target/error-observation guards, never Instruments or native passes."""
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import apple_image_profile as profile
import test_apple_image_profile as fixture


class AppleProfileTargetingTests(unittest.TestCase):
    def owner(self):
        owner = fixture.AppleImageProfileTests()
        self.addCleanup(owner.doCleanups)
        owner.setUp()
        original = owner.driver.control

        def control(command, timeout):
            if command[:4] == ["/usr/bin/xcrun", "xctrace", "list", "devices"]:
                return subprocess.CompletedProcess(command, 0,
                    ("== Simulators ==\nOwned Simulator (" + fixture.DEVICE + ")\n").encode(), b"")
            if command[0] == "/usr/bin/codesign":
                return subprocess.CompletedProcess(command, 0, b"", b"private executable path")
            return original(command, timeout)

        owner.driver.control = control
        return owner

    def test_actual_record_targets_the_verified_simulator_not_the_default_mac(self):
        owner = self.owner()
        owner.prepare(); owner.request(); owner.driver.close()
        command = owner.commands[0]
        self.assertIn("--device", command, "The library PID belongs to the selected iOS simulator, not the default Mac target")
        self.assertEqual(fixture.DEVICE, command[command.index("--device") + 1])
        self.assertEqual(["--attach", str(fixture.PID)], command[-2:])
        self.assertTrue(owner.driver.receipt["device_selection_preflight"]["selected_simulator_verified"])
        self.assertTrue(owner.driver.receipt["actual_process_executable_identity_verified"])
        self.assertTrue(profile.validate_attempt(owner.driver.receipt, fixture.DEVICE, fixture.BUNDLE))

    def test_missing_foreign_or_ambiguous_simulator_listing_never_attaches_or_uses_fallback(self):
        for body in (b"", b"private physical device (99999999-9999-9999-9999-999999999999)",
                     (fixture.DEVICE + "\n" + fixture.DEVICE).encode(), ("prefix" + fixture.DEVICE + "suffix").encode()):
            with self.subTest(body=body):
                owner = self.owner()
                original = owner.driver.control

                def control(command, timeout):
                    if command[:4] == ["/usr/bin/xcrun", "xctrace", "list", "devices"]:
                        return subprocess.CompletedProcess(command, 0, body, b"private listing path")
                    return original(command, timeout)

                owner.driver.control = control
                with self.assertRaises(ValueError): owner.prepare()
                self.assertEqual([], owner.commands)
                self.assertFalse(owner.driver.receipt["profile_passed"])
                owner.driver.close()

    def test_actual_exit21_preserves_fixed_tool_categories_before_owned_log_cleanup(self):
        owner = self.owner(); owner.prepare()
        body = b"Cannot find process for provided pid.\n" + fixture.PRIVATE.encode()

        def execute(root, command, log, timeout, reserve):
            owner.commands.append(command); log.write_bytes(body)
            return {"exit_code": 21, "elapsed_seconds": 0.01}

        owner.request(execute); owner.driver.close()
        self.assertEqual(1, len(owner.commands), "No failed tool retry or successful library-method replay")
        self.assertFalse(owner.driver.receipt["profile_passed"])
        self.assertNotIn("leak_summary", owner.driver.receipt)
        observed = owner.driver.receipt["commands"][0]["failure_diagnostic"]
        self.assertEqual(["process-not-found"], observed["matched_fixed_categories"])
        self.assertEqual(hashlib.sha256(body).hexdigest(), observed["sha256"])
        self.assertFalse(observed["root_cause_proven"])
        self.assertNotIn(fixture.PRIVATE, json.dumps(owner.driver.receipt))
        self.assertTrue(owner.driver.receipt["owned_private_tree_removed"])

    def test_diagnostic_matches_are_observations_not_authorization_or_success_assumptions(self):
        owner = self.owner()
        for body, expected in ((b"Authorization failed", ["authorization-refused"]),
                               (b"Failed to attach to process", ["attach-refused"]),
                               (b"get-task-allow is not enabled", ["debug-entitlement-refused"]),
                               (b"unknown option: --private", ["unknown-option"]),
                               (b"Unknown Instruments failure", [])):
            with self.subTest(body=body):
                path = owner.output / "explicitly-synthetic-tool.log"; path.write_bytes(body)
                observed = profile.tool_failure_summary(path)
                self.assertEqual(expected, observed["matched_fixed_categories"])
                self.assertFalse(observed["raw_output_uploaded"])
                self.assertFalse(observed["root_cause_proven"])

    def test_diagnostic_read_rejects_foreign_alias_shared_file_nonregular_and_overflow(self):
        owner = self.owner()
        foreign = owner.root / "preserve.txt"; foreign.write_text(fixture.PRIVATE)
        alias = owner.output / "alias.log"; alias.symlink_to(foreign)
        with self.assertRaises(ValueError): profile.tool_failure_summary(alias)
        import os
        shared = owner.output / "shared.log"; os.link(foreign, shared)
        with self.assertRaises(ValueError): profile.tool_failure_summary(shared)
        directory = owner.output / "directory.log"; directory.mkdir()
        with self.assertRaises(ValueError): profile.tool_failure_summary(directory)
        bounded = owner.output / "bounded.log"; bounded.write_bytes(b"xxx")
        with patch.object(profile, "MAX_TOOL_DIAGNOSTIC_BYTES", 2), self.assertRaises(ValueError):
            profile.tool_failure_summary(bounded)
        self.assertEqual(fixture.PRIVATE, foreign.read_text())

    def test_codesign_observation_never_invents_entitlements_or_exports_unknown_fields(self):
        for info in ({}, {"get-task-allow": True, "private-secret-field": fixture.PRIVATE},
                     {"com.apple.security.get-task-allow": True},
                     {"get-task-allow": False}, {"get-task-allow": "true"}):
            with self.subTest(info=info):
                result = subprocess.CompletedProcess([], 0, plistlib.dumps(info), b"private app path")
                observed = profile.debug_entitlement_observation(result)
                self.assertEqual(info.get("get-task-allow") is True, observed["ios_debug_allowed"])
                self.assertEqual(info.get("com.apple.security.get-task-allow") is True, observed["mac_debug_allowed"])
                self.assertFalse(observed["attach_authorization_proven"])
                self.assertNotIn(fixture.PRIVATE, json.dumps(observed))
        empty = profile.debug_entitlement_observation(subprocess.CompletedProcess([], 0, b"", b"private app path"))
        self.assertFalse(empty["ios_debug_allowed"]); self.assertFalse(empty["mac_debug_allowed"])
        for result in (subprocess.CompletedProcess([], 1, b"", b"not signed"),
                       subprocess.CompletedProcess([], 0, b"malformed plist", b""),
                       subprocess.CompletedProcess([], 0, plistlib.dumps([]), b"")):
            with self.assertRaises(ValueError): profile.debug_entitlement_observation(result)

    def test_selected_device_and_entitlement_diagnostics_do_not_change_native_or_signing_inputs(self):
        owner = self.owner(); initial = owner.binary.read_bytes()
        owner.prepare(); owner.request(); owner.driver.close()
        observed = owner.driver.receipt["debug_entitlement_observation"]
        self.assertFalse(observed["ios_debug_allowed"])
        self.assertFalse(observed["mac_debug_allowed"])
        self.assertFalse(observed["attach_authorization_proven"])
        self.assertEqual(initial, owner.binary.read_bytes())
        self.assertEqual("selected-simulator-uuid", owner.driver.receipt["record_target_selection"])

    def test_control_observations_reject_nonzero_boolean_unbounded_or_entity_payloads(self):
        for result in (subprocess.CompletedProcess([], 1, fixture.DEVICE.encode(), b""),
                       subprocess.CompletedProcess([], False, fixture.DEVICE.encode(), b""),
                       subprocess.CompletedProcess([], 0, b"x" * (profile.MAX_TOOL_DIAGNOSTIC_BYTES + 1), b"")):
            with self.assertRaises(ValueError): profile.selected_simulator_observation(result, fixture.DEVICE)
            with self.assertRaises(ValueError): profile.debug_entitlement_observation(result)
        entity = b'<!DOCTYPE plist [<!ENTITY x "private">]><plist><dict><key>get-task-allow</key><string>&x;</string></dict></plist>'
        with self.assertRaises(ValueError):
            profile.debug_entitlement_observation(subprocess.CompletedProcess([], 0, entity, b""))

    def test_diagnostic_change_during_read_is_rejected_and_only_owned_descriptor_is_closed(self):
        owner = self.owner()
        path = owner.output / "changed-tool.log"; path.write_text("Authorization failed")
        original_read = profile.os.read
        original_close = profile.os.close

        def changed(descriptor, count):
            body = original_read(descriptor, count)
            path.write_text("Unknown tool failure")
            return body

        with patch.object(profile.os, "read", side_effect=changed), \
                patch.object(profile.os, "close", wraps=original_close) as closed, self.assertRaises(ValueError):
            profile.tool_failure_summary(path)
        self.assertEqual(1, closed.call_count)
        self.assertEqual("Unknown tool failure", path.read_text())


if __name__ == "__main__": unittest.main()
