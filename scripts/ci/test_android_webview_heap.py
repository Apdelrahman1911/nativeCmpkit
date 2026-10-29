"""Synthetic privacy/ownership/process fixtures: no Android device, GC or native execution."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import android_webview_heap as h


class OwnedHeapFixtures(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "build/ci-verification/synthetic-heap"
        self.output.mkdir(parents=True)
        self.home = self.root / "synthetic-sdk"
        converter = self.home / "platform-tools/hprof-conv"
        converter.parent.mkdir(parents=True)
        converter.write_text("synthetic converter, never executed")
        converter.chmod(0o700)
        source = self.root / h.SOURCE
        source.parent.mkdir(parents=True)
        source.write_text("// Synthetic profiler source, never compiled\n")
        self.process = Mock()
        self.process.poll.return_value = None
        self.name = "nativecmpkit-api35-0123456789ab"
        self.owner = Mock(return_value=self.name)
        self.heap = h.OwnedHeap(self.root, self.output, self.home, "emulator-5588", self.process, self.name, self.owner)
        self.payload = b"Synthetic private HPROF bytes; not a real heap"
        self.marker = {"file": "unmounted-media.hprof", "bytes": len(self.payload), "sha256": hashlib.sha256(self.payload).hexdigest()}
        self.analysis = {"schema_version": 1, "scope": "Nearest heap root paths only; not all paths or native allocations",
                         "raw_ids_or_values_exported": False, "targets": [{"target_class": "android.webkit.WebView",
                         "nearest_path": [{"child_class": "android.webkit.WebView", "parent_class": "android.view.ViewRootImpl",
                                            "fields": ["android.view.ViewRootImpl.mView"]}],
                         "root_reached": True, "weak_reference_edge": False, "root_kinds": ["JNI global"]}]}

    def test_marker_positive_calibration_and_bounded_exact_app_filename_size_hash_contract(self):
        self.assertEqual(self.marker, h.marker(json.dumps(self.marker).encode()))
        for changed in ({**self.marker, "file": "../../another-app"}, {**self.marker, "bytes": True},
                        {**self.marker, "bytes": 31}, {**self.marker, "bytes": h.MAX_DUMP_BYTES + 1},
                        {**self.marker, "sha256": "bad"}, {**self.marker, "secret": "must-not-export"}, []):
            with self.assertRaises(ValueError): h.marker(json.dumps(changed).encode())
        for raw in (b"", b"x" * 4097, b'{"file":"a","file":"b"}', b'{"bytes":NaN}'):
            with self.assertRaises(ValueError): h.marker(raw)

    def test_only_exact_controller_avd_slot_is_permitted_not_guessed_or_physical_devices(self):
        for serial, name in (("emulator-5554", self.name), ("private-phone", self.name), ("emulator-5588", "another-avd")):
            with self.assertRaises(ValueError):
                h.OwnedHeap(self.root, self.output, self.home, serial, self.process, name, self.owner)

    def test_closed_or_foreign_avd_prevents_any_app_command(self):
        for exited in (True, False):
            self.process.poll.return_value = 1 if exited else None
            self.owner.return_value = "foreign" if not exited else self.name
            with patch.object(h.subprocess, "run") as command:
                self.heap.capture()
            command.assert_not_called()
            self.assertFalse(self.heap.record["capture_found"])
            self.assertEqual("ValueError", self.heap.record["capture_error"])

    def test_complete_bounded_transfer_is_hashed_and_avd_reverified_without_other_app_or_value_export(self):
        self.heap.private.mkdir(mode=0o700)
        def command(args, **kwargs):
            self.assertEqual([str(self.home / "platform-tools/adb"), "-s", "emulator-5588", "shell", "run-as", h.PACKAGE], args[:6])
            if args[-1] == h.MARKER:
                return subprocess.CompletedProcess(args, 0, json.dumps(self.marker).encode(), b"private stderr not exported")
            self.assertEqual(["head", "-c", str(len(self.payload) + 1), h.DUMP], args[6:])
            kwargs["stdout"].write(self.payload)
            return subprocess.CompletedProcess(args, 0)
        with patch.object(h.subprocess, "run", side_effect=command): self.heap.capture()
        self.assertTrue(self.heap.record["capture_found"])
        self.assertEqual(3, self.owner.call_count)
        self.assertEqual(self.payload, (self.heap.private / "owned-android.hprof").read_bytes())
        self.assertNotIn("private stderr", json.dumps(self.heap.record))
        self.assertFalse(self.heap.record["raw_heap_or_parser_uploaded"])

    def test_incomplete_changed_or_failed_transfer_cannot_supply_heap_evidence(self):
        self.heap.private.mkdir(mode=0o700)
        def command(args, **kwargs):
            if args[-1] == h.MARKER: return subprocess.CompletedProcess(args, 0, json.dumps(self.marker).encode())
            kwargs["stdout"].write(b"wrong or incomplete")
            return subprocess.CompletedProcess(args, 0)
        with patch.object(h.subprocess, "run", side_effect=command): self.heap.capture()
        self.assertFalse(self.heap.record["capture_found"])
        self.assertEqual("ValueError", self.heap.record["capture_error"])

    def test_parser_hash_size_redirect_and_capacity_fail_before_any_execution(self):
        self.assertEqual(64, len(h.PARSER_SHA256))
        for label, url, payload in (("size", h.PARSER_URL, b"wrong parser bytes"),
                                   ("digest", h.PARSER_URL, b"x" * h.PARSER_BYTES),
                                   ("redirect", h.PARSER_URL + "?unreviewed", b"never read")):
            with self.subTest(label=label):
                response = Mock()
                response.geturl.return_value = url
                response.read.return_value = payload
                response.__enter__ = Mock(return_value=response)
                response.__exit__ = Mock(return_value=False)
                # These are synthetic acquisition failures, not a real host
                # capacity test. Hold adequate capacity so the intended parser
                # guard, not the machine's unrelated free space, is exercised.
                with (patch.object(h.shutil, "disk_usage", return_value=Mock(free=16 * 1024**3)),
                      patch.object(h.urllib.request, "urlopen", return_value=response),
                      patch.object(h.subprocess, "run") as execute):
                    with self.assertRaises(ValueError): self.heap.prepare()
                execute.assert_not_called()
                self.assertFalse((self.heap.private / "parser.jar").exists())
                if label == "redirect": response.read.assert_not_called()
                self.heap.private.rmdir()
        with (patch.object(h.shutil, "disk_usage", return_value=Mock(free=8192 * 1024 * 1024 - 1)),
              patch.object(h.urllib.request, "urlopen") as acquire,
              patch.object(h.subprocess, "run") as execute):
            with self.assertRaises(ValueError): self.heap.prepare()
        acquire.assert_not_called()
        execute.assert_not_called()
        self.assertFalse(self.heap.private.exists())

    def test_synthetic_parser_positive_size_hash_precedes_compilation_and_paths_stay_private(self):
        payload = b"synthetic-not-executed-jar"
        response = Mock()
        response.geturl.return_value = h.PARSER_URL
        response.read.return_value = payload
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with (patch.object(h, "PARSER_BYTES", len(payload)), patch.object(h, "PARSER_SHA256", hashlib.sha256(payload).hexdigest()),
              patch.object(h.shutil, "disk_usage", return_value=Mock(free=16 * 1024**3)),
              patch.object(h.urllib.request, "urlopen", return_value=response), patch.dict(os.environ, {"JAVA_HOME": "/synthetic/jdk17"}),
              patch.object(h.subprocess, "run") as execute):
            self.heap.prepare()
        self.assertEqual(payload, (self.heap.private / "parser.jar").read_bytes())
        self.assertTrue(execute.call_args.kwargs["check"])
        self.assertEqual(0o700, self.heap.private.stat().st_mode & 0o777)
        self.assertFalse(self.heap.record["raw_heap_or_parser_uploaded"])

    def test_existing_symlinked_or_outside_private_directory_never_overwrites_other_data(self):
        self.heap.private.mkdir()
        with self.assertRaises(ValueError): self.heap.prepare()
        self.heap.private.rmdir()
        destination = self.root / "do-not-touch"; destination.mkdir()
        self.heap.private.symlink_to(destination, target_is_directory=True)
        with self.assertRaises(ValueError): self.heap.prepare()
        self.assertEqual([], list(destination.iterdir()))

    def test_actual_root_shape_can_report_weak_edges_but_never_raw_strings_ids_or_extra_values(self):
        self.assertEqual(self.analysis, h.reviewed_analysis(json.dumps(self.analysis).encode()))
        changed = copy.deepcopy(self.analysis); changed["targets"][0]["weak_reference_edge"] = True
        changed["targets"][0]["nearest_path"][0]["fields"] = ["java.lang.ref.Reference.referent"]
        self.assertTrue(h.reviewed_analysis(json.dumps(changed).encode())["targets"][0]["weak_reference_edge"])
        for changed in ({**self.analysis, "raw_values": "private"}, {**self.analysis, "raw_ids_or_values_exported": True},
                        {**self.analysis, "targets": "private"}, {**self.analysis, "targets": self.analysis["targets"] * 33}):
            with self.assertRaises(ValueError): h.reviewed_analysis(json.dumps(changed).encode())
        for key, value in (("nearest_path", [{"raw_value": "private"}]), ("target_class", "another.app.Private"),
                           ("root_kinds", ["private\nbody"]), ("root_reached", 1)):
            changed = copy.deepcopy(self.analysis); changed["targets"][0][key] = value
            with self.assertRaises(ValueError): h.reviewed_analysis(json.dumps(changed).encode())

    def test_failed_analysis_is_preserved_not_automatically_retried_or_converted_to_a_native_pass(self):
        self.heap.private.mkdir()
        self.heap.record["capture_found"] = True
        with patch.object(h.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "synthetic converter")) as command:
            self.heap.close(); self.heap.close()
        command.assert_called_once()
        self.assertEqual("CalledProcessError", self.heap.record["analysis_error"])
        self.assertNotIn("analysis", self.heap.record)
        self.assertTrue(self.heap.record["clean_monitor_shutdown"])
        self.assertFalse(self.heap.record["raw_heap_or_parser_uploaded"])

    def test_owned_monitor_failure_to_join_is_an_error_not_silent_cleanup_success(self):
        self.heap.thread = Mock()
        self.heap.thread.is_alive.return_value = True
        result = self.heap.close()
        self.heap.thread.join.assert_called_once_with(30)
        self.assertFalse(result["clean_monitor_shutdown"])
        self.assertEqual("OwnedMonitorShutdownTimeout", result["capture_error"])


if __name__ == "__main__": unittest.main()
