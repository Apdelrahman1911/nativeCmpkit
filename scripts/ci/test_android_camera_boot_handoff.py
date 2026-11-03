# SPDX-License-Identifier: Apache-2.0
"""Important synthetic handoff regressions; ZERO Android or library executions."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import copy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

import android_camera_boot_fallback as handoff
import android_camera_developer_prerequisite as camera
import camera_boot_handoff_source_projection as history

ROOT = Path(__file__).resolve().parents[2]
BOOT = "a0000000-0000-0000-0000-000000000001"
NAME = "nativecmpkit-api35-abcdef123456"
EMPTY = (camera.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n  (nothing)\n").encode()


def dump(*descriptors, extra=()):
    return (camera.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n"
            "  * Task{synthetic-not-an-actual-owner}\n" +
            "".join("    * Hist #0: " + row + "\n" for row in descriptors) +
            "".join(row + "\n" for row in extra) + "  (nothing)\n").encode()


FALLBACK = dump("ActivityRecord{aa u0 com.android.settings/.FallbackHome t1}")


def cp(payload, *, code=0, stderr=b""):
    return subprocess.CompletedProcess(["synthetic-not-executed"], code, payload, stderr)


def forbidden(*args, **kwargs):
    raise AssertionError("No SDK, process, network, real sleep or native action is admitted")


def capture_error(call, expected):
    # unittest's assertRaises intentionally clears the stored traceback.
    # Keep this actual original exception for exact callsite qualification.
    try:
        call()
    except expected as error:
        return error
    raise AssertionError("Expected the original synthetic refusal")


class FakeGuest:
    name = NAME

    def __init__(self):
        self.live_checks = 0
        self.lost = False

    def verify_live(self):
        self.live_checks += 1
        if self.lost:
            raise ValueError("Synthetic captured guest lost")


class Model:
    """Real waiter and strict parser; only its exterior read-only calls are modeled."""
    def __init__(self, observations=(EMPTY,)):
        self.now = 0.0
        self.observations = list(observations)
        self.calls, self.sleeps, self.publications = [], [], []
        self.hook, self.publish_hook = None, None
        self.owner = object.__new__(camera.OwnedDeveloperPrerequisite)
        owner = self.owner
        owner.original, owner.closed = None, False
        owner.startup_deadline = owner.deadline = None
        owner._pre_reporter_capture_attempted = False
        owner.receipt = {"prepare_status": "not-started", "focus": camera.FOCUS, "api_level": 35}
        owner.guest = FakeGuest()
        owner.clock = lambda: self.now
        owner.sleep = self.sleep
        owner.control = self.control
        owner.devices = lambda: owner.guest.verify_live()
        owner.publish = self.publish

    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration

    def publish(self):
        self.publications.append(copy.deepcopy(self.owner.receipt))
        if self.publish_hook is not None:
            self.publish_hook()

    def control(self, *arguments, timeout, limit):
        self.calls.append((arguments, timeout, limit))
        if self.hook is not None:
            value = self.hook(arguments)
            if value is not None:
                return value
        known = {
            ("shell", "cat", "/proc/sys/kernel/random/boot_id"): (BOOT + "\n").encode(),
            ("emu", "avd", "name"): (NAME + "\r\nOK\r\n").encode(),
            ("shell", "id", "-u"): b"2000\n",
            ("shell", "getprop", "ro.build.version.sdk"): b"35\n",
            ("shell", "getprop", "ro.product.cpu.abi"): b"x86_64\n",
            ("shell", "getprop", "sys.boot_completed"): b"1\n",
            ("shell", "getenforce"): b"Enforcing\n",
            ("shell", "am", "get-current-user"): b"0\n",
        }
        if arguments == handoff.ACTIVITIES:
            payload = self.observations.pop(0) if len(self.observations) > 1 else self.observations[0]
            return payload if isinstance(payload, subprocess.CompletedProcess) else cp(payload)
        if arguments not in known:
            raise AssertionError("Non-read-only or unknown synthetic command")
        return cp(known[arguments])

    def run(self):
        return handoff.wait_for_owned_boot_handoff(self.owner)


class CameraBootHandoffControls(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for obj, names in ((subprocess, ("Popen", "run", "check_call", "check_output")),
                           (socket, ("socket", "create_connection", "getaddrinfo"))):
            for name in names:
                self.guards.enter_context(patch.object(obj, name, forbidden))
        self.guards.enter_context(patch.object(camera, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(camera.time, "sleep", forbidden))

    def test_reference_first_cached_finishing_and_exiting_markers_are_wait_only(self):
        first = "ActivityRecord{ab u0 com.android.settings/.FallbackHome"
        cached = first + " t12}"
        finishing = first + " t12 f}}"
        exiting = first + " t12 isExiting}"
        both = first + " t-1 f} isExiting}"
        for descriptor in (first, cached, finishing, exiting, both):
            with self.subTest(descriptor=descriptor):
                facts = handoff.fallback_marker_facts(dump(descriptor))
                self.assertTrue(facts["only_reference_fallback_markers"])
                self.assertFalse(facts["activity_absence_inferred"])
                self.assertFalse(facts["actual_image_producer_or_ownership_inferred"])
                self.assertFalse(facts["detailed_body_grammar_certified"])
                with self.assertRaises(ValueError):
                    camera.parse_settings_activity_absence(cp(dump(descriptor)))

    def test_marker_near_misses_foreign_users_components_task_bounds_and_suffixes_refuse(self):
        base = "ActivityRecord{aa u0 com.android.settings/.FallbackHome t1}"
        bad = [base.replace("u0", "u10"), base.replace("FallbackHome", "FallbackHomeOther"),
               base.replace("com.android.settings", "com.android.settings.other"),
               base.replace("/.FallbackHome", "/com.android.settings.FallbackHome"),
               base.replace("aa", "AA", 1), base.replace("t1", "t2147483648"),
               base.replace("t1", "t01"), base.replace("t1", "t-2"), base + " private-suffix",
               base + " ActivityRecord{aa u0 com.android.settings/.FallbackHome t1}",
               "ActivityRecord{synthetic-unknown}"]
        for descriptor in bad:
            with self.subTest(descriptor=descriptor):
                self.assertFalse(handoff.fallback_marker_facts(dump(descriptor))["only_reference_fallback_markers"])

    def test_no_marker_or_mixed_reference_rows_never_mean_absence(self):
        self.assertFalse(handoff.fallback_marker_facts(EMPTY)["only_reference_fallback_markers"])
        self.assertFalse(handoff.fallback_marker_facts(dump("opaque detailed body"))["only_reference_fallback_markers"])
        mixed = dump("ActivityRecord{aa u0 com.android.settings/.FallbackHome t1}",
                     "ActivityRecord{bb u0 com.android.settings/.Settings t2}")
        facts = handoff.fallback_marker_facts(mixed)
        self.assertEqual((2, 1, 1), (facts["activity_record_marker_rows"],
                                    facts["reference_fallback_marker_rows"], facts["unqualified_marker_rows"]))
        self.assertFalse(facts["only_reference_fallback_markers"])

    def test_missing_duplicate_or_malformed_outer_traversal_cannot_be_provisional(self):
        samples = (FALLBACK.replace(b"Display #0", b"Display #01"),
                   FALLBACK.replace(b"Display #0", b"Display #2147483648"),
                   FALLBACK.replace(b"Display #0", b"  Display #0"),
                   FALLBACK.replace(b"Display #0 (activities from top to bottom):\n", b""),
                   FALLBACK.replace(b"  (nothing)\n", b""),
                   FALLBACK + b"  (nothing)\n",
                   FALLBACK.replace(b"  (nothing)", b"Display #0 (activities from top to bottom):\n  (nothing)"),
                   FALLBACK.replace(b"  (nothing)", camera.ACTIVITIES_HEADER.encode() + b"\n  (nothing)"))
        for payload in samples:
            self.assertFalse(handoff.fallback_marker_facts(payload)["only_reference_fallback_markers"])

    def test_marker_metadata_is_bounded_and_never_exports_row_identifiers(self):
        facts = handoff.fallback_marker_facts(FALLBACK)
        text = json.dumps(facts)
        for value in ("FallbackHome", "com.android.settings", "synthetic-not-an-actual-owner", " u0 ", BOOT, NAME):
            self.assertNotIn(value, text)
        self.assertLess(len(text), 1024)
        for value in (None, bytearray(FALLBACK), FALLBACK.decode(), b"", b"x" * (camera.CONTROL_BYTES + 1),
                      b"unsafe\0", b"unsafe\r", b"unsafe\x1b", b"\xff"):
            with self.assertRaises((ValueError, UnicodeError)):
                handoff.fallback_marker_facts(value)

    def test_already_empty_dump_passes_without_sleep_capture_native_or_mutation(self):
        model = Model()
        result = model.run()
        self.assertEqual("passed", result["status"])
        self.assertTrue(result["strict_absence_observed"])
        self.assertEqual(1, result["activity_observations"])
        self.assertEqual(0, result["fallback_wait_observations"])
        self.assertEqual([], model.sleeps)
        self.assertIsNone(model.owner.original)
        self.assertEqual("not-started", model.owner.receipt["prepare_status"])
        self.assertFalse(result["native_acceptance_inferred"])
        self.assertTrue(all(0 < timeout <= 10 and 0 < limit <= camera.CONTROL_BYTES
                            for _, timeout, limit in model.calls))

    def test_fallback_handoff_waits_then_requires_strict_empty_dump(self):
        model = Model((FALLBACK, FALLBACK, EMPTY))
        result = model.run()
        self.assertEqual(("passed", 3, 2), (result["status"], result["activity_observations"],
                                           result["fallback_wait_observations"]))
        self.assertEqual([0.5, 0.5], model.sleeps)
        self.assertTrue(result["strict_absence_observed"])
        self.assertIsNone(model.owner.original)
        camera.parse_settings_activity_absence(cp(EMPTY))

    def test_unknown_dump_preserves_original307_and_never_sleeps(self):
        model = Model((dump("ActivityRecord{aa u0 com.android.settings/.Settings t1}"), EMPTY))
        caught = capture_error(model.run, ValueError)
        self.assertEqual({"source": "android_camera_developer_prerequisite.py",
                          "symbol": "parse_settings_activity_absence", "line": 307},
                         camera.require_call_origin(caught))
        self.assertEqual([], model.sleeps)
        self.assertEqual("failed", model.owner.receipt["boot_handoff_preflight"]["status"])
        self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])

    def test_unknown_body_after_a_fallback_observation_never_admits_absence(self):
        model = Model((FALLBACK, dump("unknown body without a qualified marker"), EMPTY))
        with self.assertRaises(ValueError): model.run()
        self.assertEqual([0.5], model.sleeps)
        self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])

    def test_bad_exit_stderr_bytes_headers_and_duplicate_empty_display_fail_fast(self):
        samples = (cp(FALLBACK, code=1), cp(FALLBACK, stderr=b"synthetic stderr"),
                   FALLBACK.replace(b"\n", b"\r\n"), b"unframed", b"\xff", b"unsafe\0",
                   EMPTY.replace(b"  (nothing)", b"Display #0 (activities from top to bottom):\n  (nothing)"))
        for payload in samples:
            model = Model((payload, EMPTY))
            with self.assertRaises((ValueError, UnicodeError)): model.run()
            self.assertEqual([], model.sleeps)
            self.assertEqual("failed", model.owner.receipt["boot_handoff_preflight"]["status"])

    def test_never_departing_fallback_times_out_without_capture_or_acceptance(self):
        model = Model((FALLBACK,))
        with self.assertRaises(TimeoutError): model.run()
        receipt = model.owner.receipt["boot_handoff_preflight"]
        self.assertEqual(("failed", False), (receipt["status"], receipt["strict_absence_observed"]))
        self.assertEqual(60.0, model.now)
        self.assertLessEqual(receipt["activity_observations"], 120)
        self.assertIsNone(model.owner.original)

    def test_late_successful_command_at_deadline_is_not_admitted(self):
        model = Model()
        def late(arguments):
            if arguments == handoff.ACTIVITIES:
                model.now = 60.0
                return cp(EMPTY)
        model.hook = late
        with self.assertRaises(TimeoutError): model.run()
        self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])
        self.assertEqual("failed", model.owner.receipt["boot_handoff_preflight"]["status"])

    def test_clock_nan_infinite_boolean_backwards_and_early_sleep_refuse(self):
        for value in (float("nan"), float("inf"), True):
            model = Model(); model.now = value
            with self.assertRaises(ValueError): model.run()
            self.assertEqual("failed", model.owner.receipt["boot_handoff_preflight"]["status"])
        model = Model((FALLBACK, EMPTY))
        model.owner.sleep = lambda duration: setattr(model, "now", model.now - 1)
        with self.assertRaises(ValueError): model.run()
        model = Model((FALLBACK, EMPTY)); model.owner.sleep = lambda duration: None
        with self.assertRaises(ValueError): model.run()

    def test_epoch_avd_shell_runtime_user_and_selinux_drift_never_accept(self):
        bad = {
            ("shell", "cat", "/proc/sys/kernel/random/boot_id"): (BOOT[:-1]+"2\n").encode(),
            ("emu", "avd", "name"): b"nativecmpkit-api35-000000000000\nOK\n",
            ("shell", "id", "-u"): b"0\n",
            ("shell", "getprop", "ro.build.version.sdk"): b"34\n",
            ("shell", "getprop", "ro.product.cpu.abi"): b"arm64-v8a\n",
            ("shell", "getprop", "sys.boot_completed"): b"0\n",
            ("shell", "getenforce"): b"Permissive\n",
            ("shell", "am", "get-current-user"): b"10\n",
        }
        for target, value in bad.items():
            model = Model((FALLBACK, EMPTY)); seen = 0
            def hook(arguments):
                nonlocal seen
                if arguments == target:
                    seen += 1
                    if seen >= 2: return cp(value)
            model.hook = hook
            with self.assertRaises(ValueError): model.run()
            self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])

    def test_lost_captured_guest_or_foreign_device_table_refuses(self):
        model = Model(); model.owner.guest.lost = True
        with self.assertRaises(ValueError): model.run()
        model = Model(); model.owner.devices = lambda: (_ for _ in ()).throw(ValueError("synthetic foreign table"))
        with self.assertRaises(ValueError): model.run()
        self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])

    def test_primary_parser_failure_survives_secondary_publication_failure(self):
        model = Model((dump("unknown marker"),))
        def secondary():
            if model.owner.receipt["boot_handoff_preflight"]["status"] == "failed":
                raise OSError("synthetic secondary publication")
        model.publish_hook = secondary
        caught = capture_error(model.run, ValueError)
        self.assertEqual("parse_settings_activity_absence", camera.require_call_origin(caught)["symbol"])

    def test_failed_success_publication_does_not_return_a_passing_preflight(self):
        model = Model()
        def fail():
            if model.owner.receipt["boot_handoff_preflight"]["status"] == "passed":
                raise OSError("synthetic success checkpoint failure")
        model.publish_hook = fail
        with self.assertRaises(OSError): model.run()
        self.assertEqual("failed", model.owner.receipt["boot_handoff_preflight"]["status"])
        self.assertIsNone(model.owner.original)

    def test_one_shot_prepared_closed_wrong_focus_api_and_nonactual_owner_refuse(self):
        model = Model(); model.run(); calls = list(model.calls)
        with self.assertRaises(ValueError): model.run()
        self.assertEqual(calls, model.calls)
        for edit in (lambda o: setattr(o, "closed", True), lambda o: setattr(o, "original", object()),
                     lambda o: o.receipt.update(prepare_status="running"),
                     lambda o: o.receipt.update(focus="android-camera-provider"),
                     lambda o: o.receipt.update(api_level=34), lambda o: o.receipt.update(api_level=True),
                     lambda o: setattr(o, "startup_deadline", 1), lambda o: setattr(o, "deadline", 1),
                     lambda o: setattr(o, "_pre_reporter_capture_attempted", True)):
            model = Model(); edit(model.owner)
            with self.assertRaises(ValueError): model.run()
            self.assertEqual([], model.calls)
        with self.assertRaises(ValueError): handoff.wait_for_owned_boot_handoff(object())

    def test_new_stage_exact_inverse_preserves_old_pins_sources_and_roundtrip(self):
        for relative, binding in history._bindings().items():
            current = (ROOT / relative).read_bytes()
            previous = history.current_source_before_boot_handoff(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            self.assertEqual(previous, history.source_before_boot_handoff(relative, previous))
            for fragment in binding["fragments"]:
                self.assertEqual(1, previous.count(fragment["before"].encode()))
                previous = previous.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(current, previous)

    def test_new_stage_history_refuses_mutated_old_partial_and_wrong_type_current_bytes(self):
        for relative, binding in history._bindings().items():
            current = (ROOT / relative).read_bytes()
            old = history.source_before_boot_handoff(relative, current)
            for value in (old, current + b"\n", current[:-1], b"", bytearray(current), current.decode(), None):
                with self.assertRaises(ValueError): history.current_source_before_boot_handoff(relative, value)
            with self.assertRaises(ValueError): history.source_before_boot_handoff(relative, current + b"\n")
        with self.assertRaises(ValueError): history.source_before_boot_handoff(Path("foreign"), b"x")

    def test_changed_controller_keeps_capture_compile_revalidation_and_native_order(self):
        path = "scripts/ci/android_device_tests.py"
        source = (ROOT / path).read_text()
        native = ast.parse(source)
        run = next(n for n in native.body if isinstance(n, ast.FunctionDef) and n.name == "_run")
        text = ast.get_source_segment(source, run)
        anchors = ["wait_for_owned_boot_handoff(developer)", "developer.capture_before_reporter()",
                   'lt.execute(root, assemble, output / "apk-assembly.log", 900',
                   "developer.record_reporter_assembly_success(execution)", "developer.prepare()",
                   'lt.run(root, "android-device",']
        positions = [text.index(anchor) for anchor in anchors]
        self.assertEqual(sorted(positions), positions)
        self.assertEqual(1, text.count("wait_for_owned_boot_handoff(developer)"))
        self.assertIn("if guest is not None:", text)
        self.assertIn('"android_camera_boot_fallback.py"', source)
        old = history.source_before_boot_handoff(path, source.encode()).decode()
        self.assertNotIn("wait_for_owned_boot_handoff", old)
        self.assertIn("developer.capture_before_reporter()", old)


if __name__ == "__main__":
    unittest.main()
