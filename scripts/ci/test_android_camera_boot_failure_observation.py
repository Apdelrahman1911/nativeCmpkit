# SPDX-License-Identifier: Apache-2.0
"""Important failure-only boot controls; ZERO SDK, Android or library executions."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

import android_camera_boot_fallback as boot
import android_camera_developer_prerequisite as camera
from test_android_camera_boot_handoff import EMPTY, Model, capture_error, dump, forbidden

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts/ci/fixtures/camera-boot-failure-observation-source-inverse.json"
SPEC_SHA256 = "33c20dc9f166d1aa3e91c1d7a3655c9c0d0d9a1b197e5d5f4f70563347c154a0"
SOURCE = "scripts/ci/android_camera_boot_fallback.py"
ARGV = ["/synthetic-sdk/platform-tools/adb", "-s", camera.SERIAL, *boot.ACTIVITIES]


def cp(payload, *, code=0, stderr=b""):
    return subprocess.CompletedProcess(list(ARGV), code, payload, stderr)


def parse_failure(result):
    return capture_error(lambda: camera.parse_settings_activity_absence(result), ValueError)


def model_for(result):
    model = Model()
    model.hook = lambda arguments: result if arguments == boot.ACTIVITIES else None
    return model


class CameraBootFailureObservationControls(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for obj, names in ((subprocess, ("Popen", "run", "check_call", "check_output")),
                           (socket, ("socket", "create_connection", "getaddrinfo"))):
            for name in names:
                self.guards.enter_context(patch.object(obj, name, forbidden))
        self.guards.enter_context(patch.object(camera, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(camera.time, "sleep", forbidden))

    def test_first_header_footer_refusal_retains_exact_operands_without_query_or_wait(self):
        payload = EMPTY.removesuffix(b"  (nothing)\n")
        model = model_for(cp(payload))
        error = capture_error(model.run, ValueError)
        receipt = model.owner.receipt["boot_handoff_preflight"]
        origin = {"source": "android_camera_developer_prerequisite.py",
                  "symbol": "parse_settings_activity_absence", "line": 300}
        self.assertEqual(origin, camera.require_call_origin(error))
        self.assertEqual(origin, receipt["primary_require_call_origin"])
        observation = receipt["parser_refusal"]
        self.assertEqual({"minimum_three_rows": False, "header": True, "unique_header": True,
                          "footer": False, "unique_footer": False},
                         observation["original_header_footer_operands"])
        self.assertEqual(2, observation["row_count"])
        self.assertEqual(1, receipt["activity_observations"])
        self.assertEqual(1, sum(arguments == boot.ACTIVITIES for arguments, _, _ in model.calls))
        self.assertEqual([], model.sleeps)
        self.assertIsNone(model.owner.original)
        self.assertEqual("not-started", model.owner.receipt["prepare_status"])
        self.assertEqual(("failed", False), (receipt["status"], receipt["strict_absence_observed"]))

    def test_original_interior307_refusal_is_not_reclassified_as_header_or_absence(self):
        payload = dump("unknown detailed body without a recognized owner")
        error = parse_failure(cp(payload))
        observation = boot.activity_refusal(error)
        self.assertEqual(307, observation["require_call_origin"]["line"])
        self.assertTrue(all(observation["original_header_footer_operands"].values()))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), observation["stdout_sha256"])
        self.assertFalse(observation["activity_absence_verified"])
        self.assertFalse(observation["actual_producer_or_cause_inferred"])
        self.assertEqual(0, observation["new_queries_or_native_operations"])
        self.assertFalse(observation["parser_retried"])

    def test_duplicate_header_footer_and_extra_terminal_newline_keep_original_false_operands(self):
        examples = (
            (EMPTY + camera.ACTIVITIES_HEADER.encode() + b"\n", "unique_header"),
            (EMPTY + b"  (nothing)\n", "unique_footer"),
            (EMPTY + b"\n", "footer"),
            (EMPTY.replace(camera.ACTIVITIES_HEADER.encode(), b"unrecognized header"), "header"),
        )
        for payload, operand in examples:
            with self.subTest(operand=operand):
                observation = boot.activity_refusal(parse_failure(cp(payload)))
                self.assertFalse(observation["original_header_footer_operands"][operand])
                self.assertTrue(observation["original_reader_still_refused"])
                self.assertFalse(observation["activity_absence_verified"])

    def test_exit_stderr_unsafe_utf8_and_predecode_failures_have_no_invented_rows(self):
        examples = (cp(EMPTY, code=1), cp(EMPTY, stderr=b"synthetic stderr"),
                    cp(EMPTY.replace(b"\n", b"\r\n")), cp(b"unsafe\0"), cp(b"unsafe\x1b"),
                    cp(b"\xff"))
        for result in examples:
            with self.subTest(code=result.returncode, bytes=len(result.stdout)):
                observation = boot.activity_refusal(parse_failure(result))
                self.assertIsNotNone(observation)
                self.assertFalse(observation["original_rows_available"])
                self.assertNotIn("row_count", observation)
                self.assertNotIn("original_header_footer_operands", observation)
                self.assertEqual(result.returncode, observation["command_exit_code"])
                self.assertEqual(len(result.stderr), observation["stderr_bytes"])
                self.assertFalse(observation["activity_absence_verified"])
                if result.stdout == b"\xff":
                    self.assertFalse(observation["decoded_utf8"])

    def test_foreign_trace_query_types_bounds_and_changed_payload_are_unavailable_not_zero(self):
        self.assertIsNone(boot.activity_refusal(ValueError("Settings Activity absence header/footer is unproved")))
        for edit in (
            lambda r: setattr(r, "args", ["/synthetic-sdk/platform-tools/adb", "-s", "foreign", *boot.ACTIVITIES]),
            lambda r: setattr(r, "args", ["/synthetic-sdk/platform-tools/adb", "-s", camera.SERIAL, "shell", "getprop"]),
            lambda r: setattr(r, "args", ["relative/platform-tools/adb", *ARGV[1:]]),
            lambda r: setattr(r, "args", ["/synthetic-sdk/../platform-tools/adb", *ARGV[1:]]),
            lambda r: setattr(r, "stdout", bytearray(b"x")),
            lambda r: setattr(r, "stderr", ""),
            lambda r: setattr(r, "stdout", b"x" * (camera.CONTROL_BYTES + 1)),
            lambda r: setattr(r, "returncode", True),
        ):
            result = cp(b"unframed")
            error = parse_failure(result)
            edit(result)
            self.assertIsNone(boot.activity_refusal(error))
        result = cp(b"unframed")
        error = parse_failure(result)
        result.stdout = bytes(bytearray(result.stdout))
        self.assertIsNone(boot.activity_refusal(error))

    def test_observer_and_secondary_journal_failure_never_replace_original_exception(self):
        result = cp(b"unframed")
        model = model_for(result)
        def secondary():
            if model.owner.receipt["boot_handoff_preflight"]["status"] == "failed":
                raise OSError("synthetic secondary journal failure")
        model.publish_hook = secondary
        with patch.object(boot, "activity_refusal", side_effect=RuntimeError("synthetic observer failure")):
            error = capture_error(model.run, ValueError)
        self.assertEqual("Settings Activity absence header/footer is unproved", str(error))
        receipt = model.owner.receipt["boot_handoff_preflight"]
        self.assertEqual("failed", receipt["status"])
        self.assertEqual(300, receipt["primary_require_call_origin"]["line"])
        self.assertNotIn("parser_refusal", receipt)
        self.assertEqual([], model.sleeps)

    def test_success_never_invokes_failure_observer_and_one_shot_custody_is_retained(self):
        model = model_for(cp(EMPTY))
        with patch.object(boot, "activity_refusal", side_effect=AssertionError("No observation on success")):
            receipt = model.run()
        self.assertTrue(receipt["strict_absence_observed"])
        self.assertNotIn("parser_refusal", receipt)
        self.assertNotIn("primary_require_call_origin", receipt)
        calls = list(model.calls)
        with self.assertRaises(ValueError): model.run()
        self.assertEqual(calls, model.calls)
        self.assertIsNone(model.owner.original)

    def test_observations_are_eight_row_bounded_and_export_no_raw_payload_or_identifiers(self):
        payload = (camera.ACTIVITIES_HEADER + "\n" + ("synthetic-secret-component-row\n" * 900)).encode()
        self.assertLess(len(payload), camera.CONTROL_BYTES)
        observation = boot.activity_refusal(parse_failure(cp(payload)))
        self.assertEqual(8, len(observation["observed_rows"]))
        serialized = json.dumps(observation)
        self.assertLess(len(serialized), 12000)
        for value in ("synthetic-secret-component-row", "/synthetic-sdk", "emulator-5588",
                      camera.ACTIVITIES_HEADER, "Settings Activity absence header/footer is unproved"):
            self.assertNotIn(value, serialized)
        self.assertFalse(observation["raw_rows_identifiers_paths_or_environment_exported"])
        self.assertFalse(observation["actual_producer_or_cause_inferred"])

    def test_three_fragment_exact_roundtrip_keeps_original_parser_controller_and_old_pins(self):
        raw = SPEC.read_bytes()
        self.assertEqual(SPEC_SHA256, hashlib.sha256(raw).hexdigest())
        spec = json.loads(raw)
        self.assertEqual(1, spec["schema_version"])
        self.assertEqual([SOURCE], list(spec["bindings"]))
        binding = spec["bindings"][SOURCE]
        current = (ROOT / SOURCE).read_bytes()
        from camera_boot_busy_source_projection import current_source_before_boot_busy
        current = current_source_before_boot_busy(SOURCE, current)
        self.assertEqual(binding["after_sha256"], hashlib.sha256(current).hexdigest())
        self.assertEqual(3, len(binding["fragments"]))
        previous = current
        for fragment in reversed(binding["fragments"]):
            before, after = fragment["before"].encode(), fragment["after"].encode()
            self.assertEqual(fragment["before_fragment_sha256"], hashlib.sha256(before).hexdigest())
            self.assertEqual(fragment["after_fragment_sha256"], hashlib.sha256(after).hexdigest())
            self.assertEqual(1, previous.count(after))
            previous = previous.replace(after, before, 1)
        self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
        restored = previous
        for fragment in binding["fragments"]:
            before, after = fragment["before"].encode(), fragment["after"].encode()
            self.assertEqual(1, restored.count(before))
            restored = restored.replace(before, after, 1)
        self.assertEqual(current, restored)
        original_ast, current_ast = ast.parse(previous), ast.parse(current)
        find = lambda module: next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "fallback_marker_facts")
        self.assertEqual(ast.dump(find(original_ast)), ast.dump(find(current_ast)))
        for name, digest in {
            "camera-boot-handoff-source-inverse.json": "525f7f43222f92ab5730d0154e817dbfc60858e21b1daaa60d5203d954535367",
            "camera-handoff-fixture-source-inverse.json": "29da5ee28cd1aa1c1859c076895c0d62080743d2ab4bd447983dddd15684b565",
            "camera-recents-observation-source-inverse.json": "0329eb385d26e9ef90e6c3f92604672e1e76215c9513bbf88c06498eb5f1e028",
            "camera-recents-fixture-source-inverse.json": "4aaaac4178b727c388ae0969985171de0df802d0f1268b4dc6100b255c25d982",
        }.items():
            self.assertEqual(digest, hashlib.sha256((SPEC.parent / name).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
