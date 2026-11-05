# SPDX-License-Identifier: Apache-2.0
"""Important synthetic busy-boot controls; ZERO Android/native executions.

Android15 prints '(nothing)' only when no filtered activities were printed.
A recognized FallbackHome reference can justify bounded read-only waiting,
never original-state capture or native admission. The unchanged strict empty
parser must succeed on a later, separately owned observation.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import android_camera_boot_fallback as boot
import android_camera_developer_prerequisite as camera
from test_android_camera_boot_handoff import BOOT, EMPTY, FALLBACK, Model, capture_error, forbidden
from test_android_camera_boot_failure_observation import cp

ROOT = Path(__file__).resolve().parents[2]
DESCRIPTOR = "ActivityRecord{ab u0 com.android.settings/.FallbackHome t1}"


def busy(descriptor=DESCRIPTOR, *, extra=(), label="Hist  #0: "):
    # Task/body text is deliberately synthetic, not an actual Android owner.
    return (camera.ACTIVITIES_HEADER + "\nDisplay #0 (activities from top to bottom):\n"
            "  * Task{synthetic-not-an-owner}\n    * " + label + descriptor + "\n" +
            "".join(row + "\n" for row in extra)).encode()


def model_for(*payloads):
    return Model(tuple(cp(payload) for payload in payloads))


class CameraBootBusyControls(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for obj, names in ((subprocess, ("Popen", "run", "check_call", "check_output")),
                           (socket, ("socket", "create_connection", "getaddrinfo"))):
            for name in names:
                self.guards.enter_context(patch.object(obj, name, forbidden))
        self.guards.enter_context(patch.object(camera, "bounded_run", forbidden))
        self.guards.enter_context(patch.object(camera.time, "sleep", forbidden))

    def test_known_busy_first_cached_finishing_and_exiting_shapes_are_wait_only(self):
        first = "ActivityRecord{ab u0 com.android.settings/.FallbackHome"
        for descriptor in (first, first + " t1}", first + " t1 f}}",
                           first + " t1 isExiting}", first + " t-1 f} isExiting}"):
            with self.subTest(descriptor=descriptor):
                facts = boot.busy_fallback_marker_facts(busy(descriptor))
                self.assertTrue(facts["only_reference_fallback_markers"])
                self.assertEqual(1, facts["history_marker_rows"])
                self.assertFalse(facts["detailed_body_grammar_certified"])
                self.assertFalse(facts["activity_absence_inferred"])
                self.assertFalse(facts["actual_image_producer_or_ownership_inferred"])
                error = capture_error(lambda: camera.parse_settings_activity_absence(cp(busy(descriptor))), ValueError)
                self.assertEqual(300, camera.require_call_origin(error)["line"])

    def test_busy_wait_requires_later_strict_empty_with_no_capture_native_or_write(self):
        model = model_for(busy(), busy(), EMPTY)
        result = model.run()
        self.assertEqual(("passed", 3, 2), (result["status"], result["activity_observations"],
                                           result["fallback_wait_observations"]))
        self.assertEqual([0.5, 0.5], model.sleeps)
        self.assertTrue(result["strict_absence_observed"])
        self.assertEqual(300, result["last_header_footer_refusal_origin"]["line"])
        self.assertFalse(result["parser_refusal"]["original_header_footer_operands"]["footer"])
        self.assertTrue(result["parser_refusal"]["original_reader_still_refused"])
        self.assertIsNone(model.owner.original)
        self.assertEqual("not-started", model.owner.receipt["prepare_status"])
        self.assertFalse(result["native_acceptance_inferred"])
        self.assertEqual(3, sum(args == boot.ACTIVITIES for args, _, _ in model.calls))

    def test_busy_to_existing_interior_fallback_then_empty_keeps_both_origins(self):
        model = model_for(busy(), FALLBACK, EMPTY)
        result = model.run()
        self.assertEqual([0.5, 0.5], model.sleeps)
        self.assertEqual(300, result["last_header_footer_refusal_origin"]["line"])
        self.assertEqual(307, result["last_interior_refusal_origin"]["line"])
        self.assertTrue(result["strict_absence_observed"])

    def test_foreign_mixed_near_miss_and_untyped_markers_preserve_original_refusal(self):
        examples = (busy(DESCRIPTOR.replace("u0", "u10")),
                    busy(DESCRIPTOR.replace("FallbackHome", "FallbackHomeOther")),
                    busy(DESCRIPTOR.replace("t1", "t2147483648")),
                    busy(DESCRIPTOR.replace("t1", "t01")),
                    busy(DESCRIPTOR + " private-suffix"),
                    busy(extra=("  ResumedActivity: ActivityRecord{bb u0 foreign/.Main t2}",)),
                    busy(label="unqualified-role: "),
                    busy("opaque body without marker"),
                    busy(extra=("  arbitrary ActivityRecord{ab u0 com.android.settings/.FallbackHome t1}",)))
        for payload in examples:
            with self.subTest(payload_sha256=hashlib.sha256(payload).hexdigest()):
                self.assertFalse(boot.busy_fallback_marker_facts(payload)["only_reference_fallback_markers"])
                model = model_for(payload, EMPTY)
                error = capture_error(model.run, ValueError)
                self.assertEqual(300, camera.require_call_origin(error)["line"])
                self.assertEqual([], model.sleeps)
                self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])

    def test_headers_displays_sentinels_and_unsafe_or_nonordinary_envelopes_fail_fast(self):
        payload = busy()
        malformed = (payload.replace(b"Display #0", b"Display #01"),
                     payload.replace(b"Display #0", b"  Display #0"),
                     payload.replace(b"Display #0", b"Display #2147483648"),
                     payload + b"Display #0 (activities from top to bottom):\n",
                     payload + camera.ACTIVITIES_HEADER.encode() + b"\n",
                     payload.replace(camera.ACTIVITIES_HEADER.encode(), b"unknown header"),
                     payload.removesuffix(b"\n"),
                     payload + b"  (nothing)\ntrailing unknown record\n",
                     payload.replace(b"\n", b"\r\n"), b"unsafe\0", b"unsafe\x1b", b"unsafe\x08", b"\xff")
        for value in malformed:
            model = model_for(value, EMPTY)
            with self.assertRaises((ValueError, UnicodeError)):
                model.run()
            self.assertEqual([], model.sleeps)
            self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])
        for value in (cp(payload, code=1), cp(payload, stderr=b"synthetic stderr")):
            model = Model((value, cp(EMPTY)))
            with self.assertRaises(ValueError): model.run()
            self.assertEqual([], model.sleeps)

    def test_permanent_busy_times_out_and_never_means_activity_absence(self):
        model = model_for(busy())
        with self.assertRaises(TimeoutError): model.run()
        result = model.owner.receipt["boot_handoff_preflight"]
        self.assertEqual(("failed", False), (result["status"], result["strict_absence_observed"]))
        self.assertEqual(60.0, model.now)
        self.assertLessEqual(result["activity_observations"], 120)
        self.assertIsNone(model.owner.original)

    def test_busy_does_not_hide_late_reply_early_sleep_epoch_user_or_guest_drift(self):
        for failure in ("late", "early", "epoch", "user", "guest"):
            model = model_for(busy(), EMPTY)
            if failure == "early": model.owner.sleep = lambda _: None
            else:
                def hook(arguments):
                    if not model.sleeps:
                        return None
                    if failure == "late" and arguments == boot.ACTIVITIES:
                        model.now = 60.0
                        return cp(EMPTY)
                    if failure == "epoch" and arguments == ("shell", "cat", "/proc/sys/kernel/random/boot_id"):
                        return cp((BOOT[:-1] + "2\n").encode())
                    if failure == "user" and arguments == ("shell", "am", "get-current-user"):
                        return cp(b"10\n")
                    if failure == "guest":
                        model.owner.guest.lost = True
                        model.owner.guest.verify_live()
                    return None
                model.hook = hook
            with self.subTest(failure=failure), self.assertRaises((ValueError, TimeoutError)):
                model.run()
            self.assertFalse(model.owner.receipt["boot_handoff_preflight"]["strict_absence_observed"])
            self.assertIsNone(model.owner.original)

    def test_new_classifier_failure_cannot_replace_original_or_allow_capture(self):
        model = model_for(busy(), EMPTY)
        with patch.object(boot, "busy_fallback_marker_facts", side_effect=OSError("synthetic observer")):
            error = capture_error(model.run, ValueError)
        self.assertEqual(300, camera.require_call_origin(error)["line"])
        self.assertEqual([], model.sleeps)
        self.assertIsNone(model.owner.original)

    def test_reference_roles_need_history_and_export_only_bounded_counts(self):
        refs = ("    topPausingActivity=" + DESCRIPTOR, "    topResumedActivity=" + DESCRIPTOR,
                "    mLastPausedActivity: " + DESCRIPTOR, "    Resumed: " + DESCRIPTOR,
                "  ResumedActivity: " + DESCRIPTOR)
        facts = boot.busy_fallback_marker_facts(busy(extra=refs))
        self.assertTrue(facts["only_reference_fallback_markers"])
        self.assertEqual((6, 6, 0, 1), (facts["activity_record_marker_rows"],
                                       facts["reference_fallback_marker_rows"],
                                       facts["unqualified_marker_rows"], facts["history_marker_rows"]))
        for label in ("Fin #0: ", "Stop #0: "):
            self.assertTrue(boot.busy_fallback_marker_facts(busy(label=label))["only_reference_fallback_markers"])
        text = json.dumps(facts)
        self.assertLess(len(text), 1024)
        for raw in ("com.android.settings", "FallbackHome", "ActivityRecord", BOOT, "synthetic-not-an-owner"):
            self.assertNotIn(raw, text)
        for raw in (None, bytearray(busy()), busy().decode(), b"", b"x" * (camera.CONTROL_BYTES + 1)):
            with self.assertRaises(ValueError): boot.busy_fallback_marker_facts(raw)

    def test_exact_additive_history_roundtrip_refuses_old_drift_and_linked_manifest(self):
        import camera_boot_busy_source_projection as history
        raw = history.SPEC_PATH.read_bytes()
        self.assertEqual(history.SPEC_SHA256, hashlib.sha256(raw).hexdigest())
        spec = history._bindings()
        self.assertEqual({"scripts/ci/android_camera_boot_fallback.py",
                          "scripts/ci/camera_recents_fixture_source_projection.py",
                          "scripts/ci/test_android_camera_boot_failure_observation.py"}, set(spec))
        self.assertEqual(5, sum(len(v["fragments"]) for v in spec.values()))
        for relative, binding in spec.items():
            raw_current = (ROOT / relative).read_bytes()
            # The old busy inverse owns its own stage, not the latest platform659
            # source. Admit actual RAW once and keep all old inverse pins, native
            # guards, fragments, mutation refusals and forward comparisons intact.
            from camera_home_affinity_source_projection import current_source_before_home_affinity
            current = current_source_before_home_affinity(relative, raw_current)
            with self.assertRaises(ValueError):
                history.current_source_before_boot_busy(
                    relative, current_source_before_home_affinity(relative, raw_current + b"\n"))
            from camera_tooling566_source_projection import current_source_before_tooling566
            from camera_tooling562_source_projection import current_source_before_tooling
            stage = current_source_before_tooling(relative,
                current_source_before_tooling566(relative, current))
            previous = history.current_source_before_boot_busy(relative, current)
            self.assertEqual(binding["before_sha256"], hashlib.sha256(previous).hexdigest())
            for fragment in binding["fragments"]:
                self.assertEqual(1, previous.count(fragment["before"].encode()))
                previous = previous.replace(fragment["before"].encode(), fragment["after"].encode(), 1)
            self.assertEqual(stage, previous)  # This old forward ends at its own stage.
            for bad in (current[:-1], current + b"\n", b"", bytearray(current), None):
                with self.assertRaises(ValueError): history.current_source_before_boot_busy(relative, bad)
            old = history.source_before_boot_busy(relative, current)
            with self.assertRaises(ValueError): history.current_source_before_boot_busy(relative, old)
        with tempfile.TemporaryDirectory(prefix="nativecmpkit-boot-busy-manifest-") as name:
            path = Path(name) / "manifest.json"
            path.write_bytes(raw)
            linked = path.with_name("linked.json")
            linked.symlink_to(path)
            with patch.object(history, "SPEC_PATH", linked), self.assertRaises(ValueError): history._bindings()
            linked.unlink()
            linked.hardlink_to(path)
            with patch.object(history, "SPEC_PATH", linked), self.assertRaises(ValueError): history._bindings()
            linked.unlink()
            path.write_bytes(raw + b"\n")
            with patch.object(history, "SPEC_PATH", path), self.assertRaises(ValueError): history._bindings()

    def test_old_classifier_parser_controller_and_native_inputs_remain_unchanged(self):
        import camera_boot_busy_source_projection as history
        document = json.loads(history.SPEC_PATH.read_bytes())
        for relative, expected in document["unchanged_owning_inputs"].items():
            from camera_home_baseline_source_projection import current_source_before_home_baseline
            from webview_content_policy_source_projection import current_source_before_content_policy
            previous = current_source_before_home_baseline(relative,
                current_source_before_content_policy(relative, (ROOT / relative).read_bytes()))
            self.assertEqual(expected, hashlib.sha256(previous).hexdigest(), relative)
        relative = "scripts/ci/android_camera_boot_fallback.py"
        current = (ROOT / relative).read_bytes()
        previous = history.current_source_before_boot_busy(relative, current)
        def function(payload, name):
            return next(node for node in ast.parse(payload).body if isinstance(node, ast.FunctionDef) and node.name == name)
        for name in ("fallback_marker_facts", "activity_refusal"):
            self.assertEqual(ast.dump(function(previous, name)), ast.dump(function(current, name)), name)

    def test_busy_to_unknown_never_uses_marker_history_as_absence_or_second_admission(self):
        model = model_for(busy(), busy(DESCRIPTOR.replace("FallbackHome", "Settings")), EMPTY)
        error = capture_error(model.run, ValueError)
        self.assertEqual(300, camera.require_call_origin(error)["line"])
        self.assertEqual([0.5], model.sleeps)
        result = model.owner.receipt["boot_handoff_preflight"]
        self.assertFalse(result["last_busy_marker_facts"]["only_reference_fallback_markers"])
        self.assertFalse(result["strict_absence_observed"])
        calls = list(model.calls)
        with self.assertRaises(ValueError): model.run()
        self.assertEqual(calls, model.calls)


if __name__ == "__main__":
    unittest.main()
