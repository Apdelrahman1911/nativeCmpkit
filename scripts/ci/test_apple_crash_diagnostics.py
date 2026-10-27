"""Synthetic public-shaped .ips fixtures, NOT Apple crashes/native execution.

No raw report from a person/device is used here. These tests exercise bounded
read-only collection, owner binding and privacy; missing diagnostics never
certify an absent crash, a finished testcase or release readiness.
"""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import apple_crash_diagnostics as d

BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + "a" * 12 + ".t" + "b" * 32
EXECUTABLE = "NativeCmpkitLibraryTests"
UUID = "12345678-1234-5678-9abc-123456789abc"
PID = 321
START = "2026-10-27T13:00:00+00:00"
END = "2026-10-27T13:01:00+00:00"
PRIVATE = "synthetic-private-sentinel-never-export"


def document():
    return {
        "bundleInfo": {"CFBundleIdentifier": BUNDLE, "private": PRIVATE},
        "pid": PID, "procName": EXECUTABLE,
        "captureTime": "2026-10-27 13:00:30.1234 +0000",
        "usedImages": [
            {"name": EXECUTABLE, "uuid": UUID, "path": "/private/" + PRIVATE},
            {"name": "CoreFoundation", "uuid": "f" * 32},
            {"name": PRIVATE, "uuid": "e" * 32},
        ],
        "faultingThread": 0,
        "threads": [{"name": PRIVATE, "frames": [
            {"imageIndex": 0, "imageOffset": 123, "symbol": "kfun:kotlin.native.runtime.GC#collect(){}"},
            {"imageIndex": 1, "imageOffset": 456, "symbol": "CFRunLoopRunSpecific"},
            {"imageIndex": 2, "imageOffset": 789, "symbol": PRIVATE},
        ]}],
        "exception": {"type": "EXC_CRASH", "signal": "SIGABRT", "rawCodes": [0, 0], "message": PRIVATE},
        "termination": {"namespace": "SIGNAL", "code": 6, "indicator": PRIVATE},
        "private_annotations": PRIVATE,
    }


def payload(body=None, metadata=None):
    body = document() if body is None else body
    prefix = "" if metadata is None else json.dumps(metadata) + "\n"
    return (prefix + json.dumps(body)).encode()


def summary(data):
    return d.owned_summary(data, bundle_id=BUNDLE, pid=PID, executable_uuid=UUID, executable=EXECUTABLE,
        started=dt.datetime.fromisoformat(START), ended=dt.datetime.fromisoformat(END))


class AppleDocumentTests(unittest.TestCase):
    def test_actual_apple_capture_time_shape_has_explicit_zone_and_fraction(self):
        self.assertEqual(dt.datetime(2026, 10, 27, 13, 0, 30, 123400, tzinfo=dt.timezone.utc),
                         d.aware_time(document()["captureTime"]))

    def test_iso_timestamps_offsets_and_apple_offsets_compare_as_instants(self):
        expected = d.aware_time(START)
        for value in ["2026-10-27T13:00:00Z", "2026-10-27T15:00:00+02:00", "2026-10-27 06:00:00.0000 -0700"]:
            with self.subTest(value=value): self.assertEqual(expected, d.aware_time(value))

    def test_naive_invalid_unbounded_or_nonstring_timestamps_are_rejected(self):
        for value in ["2026-10-27T13:00:00", "2026-10-27", "y" * 81, True, None, "2026-99-99T13:00:00Z"]:
            with self.subTest(value=value), self.assertRaises(ValueError): d.aware_time(value)

    def test_single_and_modern_two_document_reports_decode_without_key_merging(self):
        body = document()
        self.assertEqual(body, d.apple_document(payload(body)))
        self.assertEqual(body, d.apple_document(payload(body, {"app_name": EXECUTABLE, "private": PRIVATE})))

    def test_duplicate_keys_at_every_document_depth_are_rejected(self):
        for data in [b'{"pid":321,"pid":321}', b'{"bundleInfo":{"x":1,"x":2}}',
                     b'{"x":1,"x":2}\n' + payload(), payload() + b'\n{"x":1,"x":2}']:
            with self.subTest(data=data[:50]), self.assertRaises(ValueError): d.apple_document(data)

    def test_nonfinite_constants_and_overflowing_floats_are_rejected(self):
        for value in [b"NaN", b"Infinity", b"-Infinity", b"1e9999"]:
            with self.subTest(value=value), self.assertRaises(ValueError): d.apple_document(b'{"number":' + value + b'}')

    def test_no_third_document_trailing_garbage_scalar_or_non_utf8_is_accepted(self):
        for data in [payload() + b"\n{}\n{}", payload() + b" trailing", b"[]", b"1", b"true", b"\xff", b"  \n"]:
            with self.subTest(data=data[:30]), self.assertRaises((ValueError, UnicodeError)): d.apple_document(data)

    def test_integer_contract_excludes_bool_negative_noninteger_and_oversize(self):
        self.assertTrue(d.integer(0)); self.assertTrue(d.integer(2**64 - 1))
        for value in [True, False, -1, 2**64, 0.0, "1", None]:
            with self.subTest(value=value): self.assertFalse(d.integer(value))


class OwnedSummaryTests(unittest.TestCase):
    def test_owner_pid_uuid_time_and_numeric_exception_are_independently_bound(self):
        result = summary(payload())
        self.assertIsNotNone(result)
        self.assertEqual(BUNDLE, result["bundle_id"])
        self.assertEqual(PID, result["pid"])
        self.assertEqual(UUID, result["linked_executable_uuid"])
        self.assertEqual({"namespace": "SIGNAL", "code": 6}, result["termination"])
        self.assertEqual({"type": "EXC_CRASH", "signal": "SIGABRT", "raw_codes": [0, 0]}, result["exception"])

    def test_bundle_pid_executable_uuid_and_capture_window_mismatch_are_not_owned(self):
        changes = [lambda b: b["bundleInfo"].update(CFBundleIdentifier="foreign.bundle"),
                   lambda b: b.update(pid=PID + 1), lambda b: b.update(procName="ForeignExecutable"),
                   lambda b: b["usedImages"][0].update(uuid="e" * 36),
                   lambda b: b.update(captureTime="2026-10-27T12:59:59Z"),
                   lambda b: b.update(captureTime="2026-10-27T13:01:01Z")]
        for change in changes:
            with self.subTest(change=change):
                body = document(); change(body); self.assertIsNone(summary(payload(body)))

    def test_boolean_pid_cannot_impersonate_an_observed_integer_pid(self):
        body = document(); body["pid"] = True
        self.assertIsNone(d.owned_summary(payload(body), bundle_id=BUNDLE, pid=1, executable_uuid=UUID,
            executable=EXECUTABLE, started=d.aware_time(START), ended=d.aware_time(END)))

    def test_modern_metadata_owner_claims_must_not_contradict_the_body(self):
        metadata = {"app_name": EXECUTABLE, "bundleID": BUNDLE, "slice_uuid": UUID,
                    "timestamp": "2026-10-27 13:00:30.1234 +0000", "bug_type": "309"}
        self.assertIsNotNone(summary(payload(metadata=metadata)))
        for key, value in [("app_name", "Foreign"), ("bundleID", "foreign.bundle"),
                           ("slice_uuid", "e" * 36), ("timestamp", "2000-01-01T00:00:00Z")]:
            with self.subTest(key=key):
                changed = {**metadata, key: value}
                self.assertIsNone(summary(payload(metadata=changed)))

    def test_uuid_matching_is_case_insensitive_but_duplicate_owner_images_are_ambiguous(self):
        body = document(); body["usedImages"][0]["uuid"] = UUID.upper()
        self.assertIsNotNone(summary(payload(body)))
        body["usedImages"].append(copy.deepcopy(body["usedImages"][0]))
        self.assertIsNone(summary(payload(body)))

    def test_watchdog_termination_is_retained_when_no_faulting_thread_is_available(self):
        body = document(); body.pop("faultingThread"); body.pop("threads")
        body["termination"] = {"namespace": "FRONTBOARD", "code": 0x8BADF00D, "reasons": [PRIVATE]}
        result = summary(payload(body))
        self.assertEqual({"namespace": "FRONTBOARD", "code": 0x8BADF00D}, result["termination"])
        self.assertEqual("unavailable", result["faulting_thread_status"])
        self.assertEqual([], result["faulting_thread_frames"])

    def test_private_paths_messages_unknown_images_and_unknown_symbols_are_not_exported(self):
        body = document()
        body["threads"][0]["frames"].append({"imageIndex": 0, "symbol": PRIVATE})
        result = summary(payload(body)); encoded = json.dumps(result)
        self.assertNotIn(PRIVATE, encoded); self.assertNotIn("/private/", encoded)
        frames = result["faulting_thread_frames"]
        self.assertEqual("other-image", frames[2]["image"])
        self.assertTrue(frames[2]["symbol_omitted"])
        self.assertTrue(frames[3]["symbol_omitted"])
        self.assertNotIn("unexported_symbol_sha256", encoded)

    def test_public_runtime_and_finite_framework_symbols_remain_useful(self):
        result = summary(payload())
        self.assertEqual("kfun:kotlin.native.runtime.GC#collect(){}", result["faulting_thread_frames"][0]["symbol"])
        self.assertEqual("CFRunLoopRunSpecific", result["faulting_thread_frames"][1]["symbol"])

    def test_symbol_prefix_alone_does_not_export_unknown_objc_classes_or_private_paths(self):
        for symbol in ["-[PrivateOwner secretMethod]", "CF" + PRIVATE, "kfun:kotlin." + "/private/" + PRIVATE,
                       "kfun:kotlin.foo(){}\n" + PRIVATE, "x" * 1025]:
            with self.subTest(symbol=symbol[:50]):
                body = document(); body["threads"][0]["frames"][0]["symbol"] = symbol
                result = summary(payload(body))
                self.assertNotIn(symbol, json.dumps(result))
                self.assertTrue(result["faulting_thread_frames"][0]["symbol_omitted"])

    def test_invalid_image_thread_and_frame_tables_fail_closed(self):
        changes = [lambda b: b.update(usedImages=[]), lambda b: b.update(usedImages=[None]),
                   lambda b: b.update(faultingThread=True), lambda b: b.update(faultingThread=-1),
                   lambda b: b.update(faultingThread=2), lambda b: b.update(threads="invalid"),
                   lambda b: b["threads"][0].update(frames=[None]),
                   lambda b: b["threads"][0].update(frames=[{"imageIndex": True}]),
                   lambda b: b["threads"][0].update(frames=[{"imageIndex": 3}])]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                body = document(); change(body); summary(payload(body))

    def test_frame_export_is_bounded_and_untrusted_exception_fields_are_omitted(self):
        body = document(); body["threads"][0]["frames"] *= 20
        body["exception"] = {"type": PRIVATE, "signal": "SIGABRT", "rawCodes": [True], "code": -1}
        body["termination"] = {"namespace": PRIVATE, "code": True}
        result = summary(payload(body))
        self.assertEqual(d.MAX_FRAMES, len(result["faulting_thread_frames"]))
        self.assertEqual({"signal": "SIGABRT"}, result["exception"])
        self.assertNotIn("termination", result)

    def test_arbitrary_uppercase_exception_signal_and_namespace_strings_are_not_exported(self):
        body = document(); secret = "SYNTHETIC_PRIVATE_SENTINEL"
        body["exception"] = {"type": secret, "signal": secret, "code": 1}
        body["termination"] = {"namespace": secret, "code": 2}
        result = summary(payload(body))
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual({"code": 1}, result["exception"])
        self.assertEqual({"code": 2}, result["termination"])

    def test_oversized_image_thread_and_native_frame_tables_are_rejected_before_export(self):
        for field in ["images", "threads", "frames"]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                body = document()
                if field == "images": body["usedImages"] *= 342
                elif field == "threads": body["threads"] *= 129
                else: body["threads"][0]["frames"] *= 1366
                summary(payload(body))


class ReadOnlyCollectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / "reports"; self.directory.mkdir()
        self.file = self.directory / (EXECUTABLE + "-2026-10-27.ips")
        self.file.write_bytes(payload())

    def collect(self, directory=None, **overrides):
        options = dict(bundle_id=BUNDLE, pid=PID, executable_uuid=UUID, executable=EXECUTABLE,
                       started_utc=START, ended_utc=END)
        options.update(overrides)
        return d.collect(directory or self.directory, **options)

    def test_one_exact_owned_report_is_sanitized_not_uploaded_or_deleted(self):
        before = self.file.read_bytes(); result = self.collect()
        self.assertEqual("matched-owned-report", result["status"])
        self.assertFalse(result["raw_reports_uploaded"]); self.assertFalse(result["native_functionality_verified"])
        self.assertEqual(before, self.file.read_bytes()); self.assertNotIn(PRIVATE, json.dumps(result))

    def test_both_common_exact_process_filename_separators_are_supported(self):
        self.file.rename(self.directory / (EXECUTABLE + "_2026-10-27.ips"))
        self.assertEqual("matched-owned-report", self.collect()["status"])

    def test_other_processes_nested_files_and_non_ips_are_not_opened(self):
        for name in ["Foreign-2026.ips", EXECUTABLE + "Foreign-2026.ips", EXECUTABLE + "-2026.log"]:
            (self.directory / name).write_bytes(b"invalid foreign data")
        nested = self.directory / "nested"; nested.mkdir(); (nested / self.file.name).write_bytes(payload())
        with patch.object(d, "regular_bytes", wraps=d.regular_bytes) as read:
            result = self.collect()
        self.assertEqual("matched-owned-report", result["status"]); self.assertEqual(1, read.call_count)

    def test_unknown_pid_uuid_or_bundle_refuses_reading_any_report(self):
        with patch.object(d, "regular_bytes", side_effect=AssertionError("must not read")):
            for options in [dict(pid=None), dict(pid=True), dict(pid=0), dict(pid=2**31),
                            dict(executable_uuid=None), dict(executable_uuid="not-a-uuid"), dict(bundle_id="foreign.bundle")]:
                with self.subTest(options=options): self.assertEqual("unavailable", self.collect(**options)["status"])

    def test_invalid_execution_window_or_executable_never_searches(self):
        with patch.object(d, "regular_bytes", side_effect=AssertionError("must not read")):
            for options in [dict(ended_utc="2026-10-27T12:00:00Z"), dict(ended_utc="2026-10-27T14:00:01Z"),
                            dict(executable="../foreign"), dict(started_utc="2026-10-27T13:00:00")]:
                with self.subTest(options=options): self.assertEqual("unavailable", self.collect(**options)["status"])

    def test_missing_directory_and_no_matching_reports_are_unknown_not_crash_absence(self):
        self.file.unlink()
        for directory in [self.directory, self.root / "missing"]:
            with self.subTest(directory=directory):
                result = self.collect(directory)
                self.assertEqual("no-matching-owned-report", result["status"])
                self.assertFalse(result["native_functionality_verified"])
                self.assertIn("crash absence not established", result["reason"])

    def test_multiple_owned_reports_are_not_arbitrarily_selected(self):
        (self.directory / (EXECUTABLE + "-second.ips")).write_bytes(payload())
        result = self.collect(); self.assertEqual("ambiguous-owned-reports", result["status"])
        self.assertEqual(2, result["matching_report_count"]); self.assertNotIn("report", result)

    def test_malformed_or_changed_files_are_rejected_without_exporting_errors(self):
        self.file.write_bytes(b'{"private":"' + PRIVATE.encode() + b'", invalid}')
        result = self.collect(); self.assertEqual(1, result["reports_rejected"])
        self.assertEqual("no-matching-owned-report", result["status"]); self.assertNotIn(PRIVATE, json.dumps(result))

    def test_empty_oversized_symlink_hardlink_and_directory_candidates_are_rejected(self):
        for mode in ["empty", "oversize", "symlink", "hardlink", "directory"]:
            with self.subTest(mode=mode):
                self.file.unlink(missing_ok=True)
                other = self.root / (mode + ".data"); other.write_bytes(payload())
                if mode == "empty": self.file.write_bytes(b"")
                elif mode == "oversize": self.file.write_bytes(b"x" * 2049)
                elif mode == "symlink": self.file.symlink_to(other)
                elif mode == "hardlink": os.link(other, self.file)
                else: self.file.mkdir()
                with patch.object(d, "MAX_REPORT_BYTES", 2048): result = self.collect()
                self.assertEqual(1, result["reports_rejected"]); self.assertNotIn("report", result)
                if mode == "directory": self.file.rmdir()

    def test_symlink_ancestors_and_traversal_do_not_open_foreign_reports(self):
        linked = self.root / "linked"; linked.symlink_to(self.directory, target_is_directory=True)
        with patch.object(d, "regular_bytes", side_effect=AssertionError("must not read")):
            self.assertEqual("unavailable", self.collect(linked)["status"])
            self.assertEqual("unavailable", self.collect(linked / "../reports")["status"])

    def test_candidate_limit_cannot_keep_an_early_match_as_success(self):
        (self.directory / (EXECUTABLE + "-second.ips")).write_bytes(payload())
        with patch.object(d, "MAX_CANDIDATES", 1): result = self.collect()
        self.assertEqual("unavailable", result["status"]); self.assertNotIn("report", result)

    def test_directory_scan_has_a_separate_bound_even_for_nonmatching_names(self):
        for index in range(4): (self.directory / ("foreign-" + str(index))).write_bytes(b"unknown")
        with patch.object(d, "MAX_DIRECTORY_ENTRIES", 2, create=True): result = self.collect()
        self.assertEqual("unavailable", result["status"]); self.assertNotIn("report", result)

    def test_secure_open_primitives_are_required_not_silently_emulated(self):
        with patch.object(d.os, "O_NOFOLLOW", 0): result = self.collect()
        self.assertEqual("unavailable", result["status"])

    def test_file_mutation_between_metadata_and_open_is_rejected(self):
        real = d.os.open
        def replace(path, flags, *args, **kwargs):
            if os.fspath(path) in {self.file.name, str(self.file)}: self.file.write_bytes(payload() + b" ")
            return real(path, flags, *args, **kwargs)
        with patch.object(d.os, "open", side_effect=replace): result = self.collect()
        self.assertEqual(1, result["reports_rejected"]); self.assertNotIn("report", result)

    def test_file_replacement_during_read_is_rejected(self):
        real = d.os.read; done = False
        def replace(fd, size):
            nonlocal done
            result = real(fd, size)
            if not done:
                done = True; self.file.unlink(); self.file.write_bytes(payload())
            return result
        with patch.object(d.os, "read", side_effect=replace): result = self.collect()
        self.assertEqual(1, result["reports_rejected"]); self.assertNotIn("report", result)

    def test_anchored_directory_replacement_never_reads_the_new_foreign_target(self):
        real = d.os.open; old = self.root / "held"; foreign = self.root / "foreign"; foreign.mkdir()
        (foreign / self.file.name).write_bytes(b"foreign data must not be opened")
        observed_file_parent = []
        def replace(path, flags, *args, **kwargs):
            if os.fspath(path) in {self.file.name, str(self.file)}:
                self.directory.rename(old); self.directory.symlink_to(foreign, target_is_directory=True)
                if kwargs.get("dir_fd") is not None: observed_file_parent.append(os.fstat(kwargs["dir_fd"]).st_ino)
            return real(path, flags, *args, **kwargs)
        with patch.object(d.os, "open", side_effect=replace): result = self.collect()
        self.assertEqual("unavailable", result["status"]); self.assertNotIn("report", result)
        self.assertEqual([old.stat().st_ino], observed_file_parent)


if __name__ == "__main__":
    unittest.main()
