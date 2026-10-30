"""Synthetic bundle/time-bound launch diagnostics; never native/profile success."""
import json
import subprocess
import unittest

BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
DEVICE = "12345678-1234-1234-1234-123456789abc"
START = "2026-10-30T10:09:26+00:00"
END = "2026-10-30T10:10:04+00:00"


class AppleLaunchDiagnosticTests(unittest.TestCase):
    def subject(self):
        import apple_launch_diagnostics
        return apple_launch_diagnostics

    def row(self, message=None, **extra):
        return {"timestamp": "2026-10-30 10:09:30.100000+0000",
                "processImagePath": "/private/system/path/SpringBoard",
                "eventMessage": message or ("Request " + BUNDLE + " denied; invalid code signature"), **extra}

    def summary(self, rows):
        return self.subject().summarize(json.dumps(rows).encode(), BUNDLE, START, END)

    def test_only_exact_owned_bundle_in_actual_window_retains_fixed_system_observations(self):
        summary = self.summary([self.row()])
        self.assertEqual(1, summary["owned_system_rows"])
        self.assertEqual(["SpringBoard"], summary["system_process_names"])
        self.assertEqual(["signature-invalid"], summary["matched_fixed_categories"])
        self.assertFalse(summary["root_cause_proven"])
        self.assertFalse(summary["native_functionality_verified"])
        self.assertFalse(summary["raw_messages_paths_or_log_uploaded"])

    def test_foreign_bundle_prefix_time_and_process_never_establish_owned_errors(self):
        cases = [self.row(BUNDLE + "foreign invalid code signature"),
                 self.row("foreign bundle invalid code signature"),
                 self.row(timestamp="2026-10-30T10:08:00+00:00"),
                 self.row(timestamp="2026-10-30T10:11:00+00:00"),
                 self.row(processImagePath="/private/user/MyApplication")]
        for row in cases:
            with self.subTest(row=row):
                summary = self.summary([row])
                self.assertEqual(0, summary["owned_system_rows"])
                self.assertEqual([], summary["matched_fixed_categories"])

    def test_private_messages_unknown_symbols_addresses_and_paths_are_never_serialized(self):
        private = "FAKE_SECRET_TOKEN /private/user/arbitrary.file 0xabcdef UNIQUE_PRIVATE_LOG_MESSAGE UNKNOWN_PRIVATE_SYMBOL"
        summary = self.summary([self.row(BUNDLE + " " + private)])
        self.assertEqual(1, summary["owned_system_rows"])
        self.assertEqual([], summary["matched_fixed_categories"])
        for token in private.split():
            self.assertNotIn(token, json.dumps(summary))

    def test_byte_row_message_duplicate_json_and_timestamp_bounds_are_fail_closed(self):
        module = self.subject()
        for body in (b"x" * (module.MAX_BYTES + 1), b'{"not":"a list"}',
                     b'[{"timestamp":"a","timestamp":"b"}]',
                     json.dumps([self.row()] * (module.MAX_ROWS + 1)).encode(),
                     json.dumps([self.row("x" * (module.MAX_MESSAGE_BYTES + 1))]).encode()):
            with self.assertRaises(ValueError): module.summarize(body, BUNDLE, START, END)
        for start, end in ((END, START), (START, START), ("2026-10-30T10:09:26", END),
                           (START, "2026-10-30T11:00:00+00:00")):
            with self.assertRaises(ValueError): module.summarize(b"[]", BUNDLE, start, end)

    def test_readonly_selected_device_bundle_time_command_never_dispatches_or_relaunches(self):
        commands = []
        def control(command, timeout):
            commands.append((command, timeout))
            return subprocess.CompletedProcess(command, 0, json.dumps([self.row()]).encode(), b"")
        result = self.subject().collect(DEVICE, BUNDLE, START, END, control)
        self.assertEqual(1, result["owned_system_rows"])
        self.assertEqual(1, len(commands))
        command, timeout = commands[0]
        self.assertEqual(["/usr/bin/xcrun", "simctl", "spawn", DEVICE, "log", "show"], command[:6])
        self.assertEqual('eventMessage CONTAINS "' + BUNDLE + '"', command[command.index("--predicate") + 1])
        self.assertIn("--start", command); self.assertIn("--end", command)
        self.assertEqual(30, timeout)
        self.assertFalse(result["native_functionality_verified"])
        for value in ("foreign", DEVICE + " --launch"):
            with self.assertRaises(ValueError): self.subject().collect(value, BUNDLE, START, END, control)
        with self.assertRaises(ValueError): self.subject().collect(DEVICE, "foreign.bundle", START, END, control)
        self.assertEqual(1, len(commands))

    def test_nonzero_tool_empty_or_unparseable_log_stays_unavailable_not_success(self):
        for exit_code, payload in ((1, b"private tool error"), (0, b"not-json"), (0, b"[]")):
            def control(command, timeout): return subprocess.CompletedProcess(command, exit_code, payload, b"")
            result = self.subject().collect(DEVICE, BUNDLE, START, END, control)
            self.assertEqual("unavailable", result["status"])
            self.assertFalse(result["root_cause_proven"])
            self.assertFalse(result["native_functionality_verified"])


if __name__ == "__main__":
    unittest.main()
