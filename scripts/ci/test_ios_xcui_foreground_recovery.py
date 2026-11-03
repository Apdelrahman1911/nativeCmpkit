# SPDX-License-Identifier: Apache-2.0
"""Important source/diagnostic regressions; ZERO XCTest or library executions."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import native_ui_input as native
import library_tests as library
import ios_modal_worker_source_projection as worker
from test_native_ui_input import AUTH, TOKEN, driver_fixture

ROOT = Path(__file__).resolve().parents[2]


class XcuiForegroundRecoveryControls(unittest.TestCase):
    def test_bounded_foreground_wait_precedes_every_public_input_without_activation_or_relaunch(self):
        source = (ROOT / native.SWIFT).read_text()
        delivery = source.split("    private func deliver(", 1)[1].split("    private func coordinate(", 1)[0]
        self.assertIn("let initialState = application.state", delivery)
        self.assertIn("application.wait(for: .runningForeground, timeout: 5)", delivery)
        self.assertIn("let finalState = application.state", delivery)
        guard = "guard observedForeground && finalState == .runningForeground else"
        self.assertIn(guard, delivery)
        self.assertLess(delivery.index(guard), delivery.index("switch operation"))
        self.assertLess(delivery.index("application.wait("), delivery.index(guard))
        self.assertIn("let waited = initialState != .runningForeground", delivery)
        self.assertIn("let observedForeground = !waited ||", delivery)
        self.assertIn("throw InputError.foreignOrInactiveApplication", delivery)
        self.assertNotRegex(source, r"\.(launch|activate|performSelector)\s*\(")
        self.assertNotRegex(source, r"\.setValue\([^\n]*forKey:")
        self.assertNotIn("Thread.sleep", delivery)
        for token in ("button.tap()", "field.typeText(text)", "query.count == 1", "thenDragTo: to"):
            self.assertIn(token, delivery)

    def test_original_seven_native_bodies_compiler_and_lifecycle_transport_are_unchanged(self):
        pins = {
            library.IOS_MODAL_XCUI_SOURCE: "e468733ea7652fd32a2e9224e3ac3ddc18839cdb29c17e817ab9a25dd0bfd0f5",
            native.NATIVE: "315c2f3fab43219b9b1c14997e248707e822f6e79c3d107d7251afbdcc95a28a",
        }
        for relative, expected in pins.items():
            self.assertEqual(expected, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
        source = (ROOT / library.IOS_MODAL_XCUI_SOURCE).read_text()
        self.assertEqual(library.IOS_MODAL_XCUI_METHODS, tuple(re.findall(r"@Test fun (\w+)\(", source)))
        self.assertNotRegex(source, r"@(Ignore|Disabled|IgnoredTest)\b")
        plan = library.plan(ROOT, "ios", only_modules=("calf-ui",), focus=library.IOS_MODAL_XCUI_FOCUS)
        self.assertEqual(7, len(plan["expected"][0]["required_testcases"]))
        collector = (ROOT / "scripts/ci/library_tests.py").read_text()
        self.assertIn('native_ui_input.validate_receipt(document.get("native_xctest_input")', collector)

    def test_failure_observations_accept_only_typed_public_state_scalars_and_never_export_secrets(self):
        raw = (
            "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=1 initial=0 final=2 waited=true observed=false\n"
            "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=96 initial=4 final=3 waited=false observed=true\n"
            "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=1 initial=0 final=2 waited=true observed=false " + AUTH + "\n"
            "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=1 initial=0 final=2 waited=true observed=false " + TOKEN + "\n"
        ).encode()
        observed = native.foreground_refusal_observations(raw, AUTH, TOKEN)
        self.assertEqual([
            dict(sequence=1, initial_state=0, final_state=2, wait_attempted=True, wait_reported_foreground=False),
            dict(sequence=96, initial_state=4, final_state=3, wait_attempted=False, wait_reported_foreground=True),
        ], observed)
        self.assertNotIn(AUTH, json.dumps(observed))
        self.assertNotIn(TOKEN, json.dumps(observed))
        self.assertEqual([], native.foreground_refusal_observations(b"untrusted traceback", AUTH, TOKEN))

    def test_failure_observations_reject_unknown_states_sequences_flags_and_unbounded_input(self):
        line = "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=1 initial=0 final=2 waited=true observed=false"
        bad = [line.replace("sequence=1", "sequence=" + sequence) for sequence in ("0", "01", "97", "100", "-1")]
        bad += [line.replace("initial=0", "initial=" + state) for state in ("-1", "5", "00", "unknown")]
        bad += [line.replace("final=2", "final=" + state) for state in ("-1", "5", "02", "foreground")]
        bad += [line + " extra=secret", line.replace("waited=true", "waited=1"),
                line.replace("observed=false", "observed=False"), "prefix " + line]
        for value in bad:
            with self.subTest(value=value):
                self.assertEqual([], native.foreground_refusal_observations(value.encode(), AUTH, TOKEN))
        self.assertEqual(24, len(native.foreground_refusal_observations((line + "\n").encode() * 30, AUTH, TOKEN)))
        for raw in (None, bytearray(b"plain"), b"x" * (16 * 1024**2 + 1)):
            with self.assertRaises(ValueError): native.foreground_refusal_observations(raw, AUTH, TOKEN)

    def test_held_log_capture_keeps_startup_and_foreground_receipts_separate_without_certifying_input(self):
        with driver_fixture() as driver:
            driver.scratch.mkdir(parents=True)
            raw = ("NATIVECMPKIT_XCTEST_STARTUP ready-acknowledged\n"
                   "NATIVECMPKIT_XCTEST_FOREGROUND_REFUSAL sequence=1 initial=0 final=2 waited=true observed=false\n"
                   "do not export " + AUTH + " or " + TOKEN + "\n").encode()
            driver.log = (driver.scratch / "xcodebuild.log").open("xb")
            driver.log.write(raw)
            driver._capture_log()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), driver.receipt["private_log_sha256"])
            self.assertEqual([{"phase": "ready-acknowledged"}], driver.receipt["startup_diagnostics"])
            self.assertEqual([dict(sequence=1, initial_state=0, final_state=2,
                                   wait_attempted=True, wait_reported_foreground=False)], driver.receipt["foreground_refusals"])
            self.assertFalse(driver.receipt["verified"])
            self.assertEqual([], driver.receipt["operations"])
            self.assertNotIn(AUTH, json.dumps(driver.receipt))
            self.assertNotIn(TOKEN, json.dumps(driver.receipt["foreground_refusals"]))

    def test_current_two_path_inverse_is_exact_and_old_worker_six23_pins_remain_immutable(self):
        import ios_xcui_foreground_source_projection as history
        bindings = history._bindings()
        self.assertEqual({native.SOURCE, native.SWIFT}, set(bindings))
        self.assertEqual(3, sum(len(binding["fragments"]) for binding in bindings.values()))
        for relative, binding in bindings.items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_xcui_foreground(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_xcui_foreground(relative, previous))
            original = worker.current_source_before_modal_worker(relative, current)
            self.assertEqual(worker._bindings()[relative]["before_sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(original, worker.source_before_modal_worker(relative, original))
            for bad in (previous, current + b"\n", current[:-1], current.replace(b"\n", b"\r\n"), b"", bytearray(current)):
                with self.assertRaises(ValueError): history.current_source_before_xcui_foreground(relative, bad)
        self.assertEqual(6, len(worker._bindings()))
        self.assertEqual(23, sum(len(binding["fragments"]) for binding in worker._bindings().values()))
        self.assertEqual("8a1f2c4b0f418b9aab96f9d3c8f615acff5efce31fe457886204559fd2448d48",
                         hashlib.sha256(worker.SPEC_PATH.read_bytes()).hexdigest())
        self.assertNotIn("ios_xcui_foreground_source_projection", (ROOT / native.SOURCE).read_text())

    def test_inverse_rejects_manifest_and_fragment_tampering_without_a_hash_refresh(self):
        import ios_xcui_foreground_source_projection as history
        bindings = history._bindings()
        current = (ROOT / native.SWIFT).read_bytes()
        binding = json.loads(json.dumps(bindings))
        binding[native.SWIFT]["fragments"][0]["before"] += "unreviewed"
        with patch.object(history, "_bindings", return_value=binding), self.assertRaises(ValueError):
            history.current_source_before_xcui_foreground(native.SWIFT, current)
        with patch.object(history, "SPEC_SHA256", "0" * 64), self.assertRaises(ValueError): history._bindings()


if __name__ == "__main__":
    unittest.main()
