"""Synthetic profile ownership/privacy/failure tests, never Apple/library passes."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import apple_image_profile as p
import ios_ui_application as app

DEVICE = "11111111-1111-1111-1111-111111111111"
BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
PID = 12345
PRIVATE = "private-profile-value-must-not-be-exported"


class AppleImageProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "build/ci-verification/native-ui-application/session"
        self.output.mkdir(parents=True)
        self.data = self.root / "11111111-2222-3333-4444-555555555555"
        (self.data / "tmp").mkdir(parents=True)
        self.installed = self.root / "NativeCmpkitLibraryTests.app"
        self.installed.mkdir()
        self.binary = self.installed / app.APP_EXECUTABLE
        self.binary.write_bytes(b"Synthetic installed identity, not an executable native test")
        self.plist = self.installed / "Info.plist"
        self.plist.write_bytes(plistlib.dumps({"CFBundleIdentifier": BUNDLE}))
        self.signed_hash = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        self.plist_hash = hashlib.sha256(self.plist.read_bytes()).hexdigest()
        self.controls = []
        self.commands = []
        self.driver = p.ImageProfileDriver(self.root, self.output, DEVICE, BUNDLE,
                                           self.signed_hash, self.plist_hash, self.control)

    def control(self, command, timeout):
        self.controls.append(command)
        value = str(self.binary) if command[0] == "/bin/ps" else str(self.data if command[-1] == "data" else self.installed)
        return subprocess.CompletedProcess(command, 0, (value + "\n").encode(), b"")

    def execute(self, root, command, log, timeout, reserve):
        self.commands.append(command)
        self.assertEqual(8192, reserve)
        self.assertTrue(1 <= timeout <= 150)
        log.write_text(PRIVATE)
        if "record" in command:
            trace = Path(command[command.index("--output") + 1]); trace.mkdir()
            (trace / "private.bin").write_text(PRIVATE)
        elif "--toc" in command:
            Path(command[-1]).write_text('<trace-toc><table schema="allocation-event"/></trace-toc>')
        elif "--xpath" in command:
            Path(command[-1]).write_text('<trace-query-result><row><frame name="' + p.NATIVE_SYMBOLS[0] +
                                       '" address="0x12345"/>' + PRIVATE + '</row></trace-query-result>')
        elif command[0] == "/usr/bin/leaks":
            log.write_text(PRIVATE + '\nProcess 12345: 0 leaks for 0 total leaked bytes.\n')
        return {"exit_code": 0, "elapsed_seconds": 0.01}

    def prepare(self):
        with patch.object(p.shutil, "disk_usage", return_value=Mock(free=16 * 1024**3)):
            return self.driver.prepare()

    def request(self, execute=None):
        with patch.object(p.lt, "execute", side_effect=execute or self.execute):
            self.driver.request(PID)

    def test_real_selected_pid_and_owned_bytes_are_required_and_only_safe_summary_survives(self):
        environment = self.prepare()
        for name, value in p.DARWIN_REQUESTS.items(): self.assertEqual(value, environment["SIMCTL_CHILD_" + name])
        self.assertNotIn("SIMCTL_CHILD_MallocScribble", __import__('os').environ)
        self.request()
        self.assertTrue(self.driver.receipt["profile_passed"])
        self.assertEqual(0, self.driver.receipt["leak_summary"]["leaks"])
        self.assertIn(["/bin/ps", "-p", str(PID), "-o", "comm="], self.controls)
        record = self.commands[0]
        self.assertEqual(["--attach", str(PID)], record[-2:])
        self.assertNotIn("--launch", record)
        self.driver.close()
        self.assertTrue(p.validate_attempt(self.driver.receipt, DEVICE, BUNDLE))
        encoded = json.dumps(self.driver.receipt)
        self.assertNotIn(PRIVATE, encoded)
        self.assertNotIn("0x12345", encoded)
        self.assertNotIn(str(self.data), encoded)
        self.assertFalse(self.driver.receipt["ASan_verified"])
        self.assertFalse(self.driver.receipt["release_readiness_certified"])
        self.assertFalse(self.driver.private.exists())

    def test_successful_xctrace_with_no_useful_rows_is_explicitly_not_a_profile_pass(self):
        self.prepare()
        def execute(*arguments):
            result = self.execute(*arguments)
            command = arguments[1]
            if "--toc" in command: Path(command[-1]).write_text('<trace-toc/>')
            return result
        self.request(execute)
        self.assertFalse(self.driver.receipt["supported"])
        self.assertFalse(self.driver.receipt["profile_passed"])
        self.assertTrue(self.driver.receipt["errors"])
        self.assertTrue(self.driver.ack.is_file())  # Attempt completion only.
        self.driver.close()
        self.assertTrue(p.validate_attempt(self.driver.receipt, DEVICE, BUNDLE))

    def test_actual_command_failure_does_not_retry_or_invent_native_profile_success(self):
        self.prepare()
        def execute(*arguments):
            result = self.execute(*arguments); return {**result, "exit_code": 1}
        self.request(execute)
        self.assertEqual(1, len(self.commands))
        self.assertFalse(self.driver.receipt["profile_passed"])
        self.assertNotIn("leak_summary", self.driver.receipt)
        self.driver.close()

    def test_missing_foreign_or_nonzero_leak_results_are_never_defaulted_to_zero(self):
        for body in (b"missing summary", b"Process 999: 0 leaks for 0 total leaked bytes.",
                     b"Process 12345: 0 leaks for 0 total leaked bytes.\nProcess 12345: 0 leaks for 0 total leaked bytes."):
            path = self.output / "leaks.log"; path.write_bytes(body)
            with self.assertRaises(ValueError): p.leak_summary(path, PID)
        path.write_text("Process 12345: 2 leaks for 99 total leaked bytes.")
        summary = p.leak_summary(path, PID)
        self.assertEqual((2, 99), (summary["leaks"], summary["leaked_bytes"]))

    def test_foreign_process_identity_is_not_profiled_or_mutated(self):
        self.prepare()
        original = self.driver.control
        def control(command, timeout):
            value = original(command, timeout)
            if command[0] == "/bin/ps": value.stdout = b"/unrelated/Foreign.app/program\n"
            return value
        self.driver.control = control
        self.request()
        self.assertEqual([], self.commands)
        self.assertFalse(self.driver.receipt["profile_passed"])
        self.driver.close()

    def test_invalid_pid_repeated_request_or_changed_executable_never_attaches(self):
        self.prepare()
        for pid in (True, 0, -1, 2**31, "12345"):
            with self.assertRaises(ValueError): self.driver.request(pid)
        self.binary.write_bytes(b"changed installed bytes")
        self.request()
        self.assertEqual([], self.commands)
        with self.assertRaises(ValueError): self.driver.request(PID)
        self.driver.close()

    def test_tool_xml_entities_unrelated_symbols_aliases_or_overflow_cannot_be_evidence(self):
        path = self.output / "tool.xml"
        path.write_text('<!DOCTYPE foo [<!ENTITY x "private">]><foo>&x;</foo>')
        with self.assertRaises(ValueError): p.allocation_summary(path)
        path.write_text('<trace-query-result><row><frame name="unrelated"/></row></trace-query-result>')
        self.assertFalse(p.allocation_summary(path)["owned_library_frame_seen"])
        with patch.object(p.discovery, "MAX_XML_BYTES", 2):
            with self.assertRaises(ValueError): p.allocation_summary(path)
        alias = self.output / "alias.xml"; alias.symlink_to(path)
        with self.assertRaises(ValueError): p.allocation_summary(alias)

    def test_profile_preflight_respects_capacity_and_inherited_native_selection(self):
        with patch.object(p.shutil, "disk_usage", return_value=Mock(free=8192 * 1024**2 - 1)):
            with self.assertRaises(OSError): self.driver.prepare()
        self.assertEqual([], self.controls)
        with patch.dict(p.os.environ, {"SIMCTL_CHILD_MallocScribble": "foreign"}):
            with self.assertRaises(ValueError): self.prepare()
        self.driver.close()
        self.assertEqual([], self.commands)

    def test_foreign_ack_or_private_alias_is_preserved_not_removed_to_hide_failure(self):
        self.prepare(); self.request()
        foreign = self.root / "preserve.txt"; foreign.write_text("preserve")
        self.driver.ack.unlink(); self.driver.ack.symlink_to(foreign)
        self.driver.close()
        self.assertEqual("preserve", foreign.read_text())
        self.assertTrue(self.driver.ack.is_symlink())
        self.assertFalse(self.driver.receipt["profile_passed"])
        self.assertFalse(p.validate_attempt(self.driver.receipt, DEVICE, BUNDLE))

    def test_incomplete_or_foreign_attempt_receipts_cannot_certify_native_or_profile_work(self):
        self.prepare(); self.request(); self.driver.close()
        good = copy.deepcopy(self.driver.receipt)
        self.assertTrue(p.validate_attempt(good, DEVICE, BUNDLE))
        for key, value in (("schema_version", True), ("process_id", True), ("process_id", 2**31),
                           ("simulator_udid", "foreign"), ("bundle_identifier", "foreign"),
                           ("owned_ack_removed", False), ("owned_private_tree_removed", False),
                           ("attempt_completion_ack_created", False), ("private_files_uploaded", True)):
            doc = copy.deepcopy(good); doc[key] = value
            self.assertFalse(p.validate_attempt(doc, DEVICE, BUNDLE))


if __name__ == "__main__": unittest.main()
