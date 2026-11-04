# SPDX-License-Identifier: Apache-2.0
"""NEW Photos ownership/protocol models with fake simctl; never permission mutation."""
import copy
import hashlib
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import camera_ios_ownership_native_focus as focus
import ios_camera_photo_fixture as photos
import ios_ui_application as application

SOURCE = "a" * 40
NONCE = "b" * 32
BUNDLE = "io.github.apdelrahman1911.nativecmpkit.verification.ui.r" + SOURCE[:12] + ".t" + NONCE
DEVICE = "11111111-1111-1111-1111-111111111111"
PID = 321
ACTIVE = "NATIVECMPKIT_UIKIT_ACTIVE mainWorker=1 ownedWorker=2"
COMPLETE = "NATIVECMPKIT_UIKIT_COMPLETED runnerExit=0 workerTerminated=true"


def marker(status="authorized", pid=PID):
    return ("NATIVECMPKIT_CAMERA_PHOTOS phase=readback mainThread=true service=photos access=read-write "
            f"status={status} source={SOURCE[:12]} nonce={NONCE} pid={pid}")


def native_frames():
    frames = [ACTIVE, "##teamcity[testSuiteStarted name='" + focus.CLASS + "']"]
    for method in focus.METHODS:
        frames.extend(("##teamcity[testStarted name='" + method + "']",
                       "##teamcity[testFinished name='" + method + "' duration='1']"))
    return frames + ["##teamcity[testSuiteFinished name='" + focus.CLASS + "']", COMPLETE]


def protocol():
    return photos.protocol_adapter(application.NativeProtocol, bundle_id=BUNDLE, source_revision=SOURCE, session_nonce=NONCE)


def native_status():
    observer = protocol()
    observer.feed(marker())
    return observer.camera_photo_observation


class FakeSimctl:
    """Returns explicit synthetic command results; ordinary installed files are read."""
    def __init__(self, app):
        self.app = app
        self.events = []
        self.privacy_results = {}

    def __call__(self, argv):
        self.events.append(list(argv))
        if argv[2] == "get_app_container":
            return subprocess.CompletedProcess(argv, 0, str(self.app).encode(), b"")
        result = self.privacy_results.get(argv[4], subprocess.CompletedProcess(argv, 0, b"", b""))
        if isinstance(result, BaseException):
            raise result
        return result


class IosCameraPhotoFixtureControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.app = self.root / "installed" / "NativeCmpkitLibraryTests.app"
        self.app.mkdir(parents=True)
        (self.app / application.APP_EXECUTABLE).write_bytes(b"Source-only installed executable fixture; never launched")
        (self.app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": BUNDLE, **photos.privacy_information()}))
        self.signed_hash = hashlib.sha256((self.app / application.APP_EXECUTABLE).read_bytes()).hexdigest()
        self.plist_hash = hashlib.sha256((self.app / "Info.plist").read_bytes()).hexdigest()
        self.control = FakeSimctl(self.app)

    def arguments(self):
        return {"root": self.root, "simulator": DEVICE, "bundle_id": BUNDLE, "source_revision": SOURCE,
                "session_nonce": NONCE, "signed_hash": self.signed_hash, "plist_hash": self.plist_hash,
                "execute_control": self.control, "installed_identity": application.installed_identity,
                "control_status": application.control_status}

    def lease(self):
        return photos.OwnedPhotosLease(**self.arguments())

    def receipt_arguments(self):
        return {key: value for key, value in self.arguments().items()
                if key not in {"root", "execute_control", "installed_identity", "control_status"}} | {"native_pid": PID}

    def complete_receipt(self):
        lease = self.lease()
        lease.prepare()
        lease.close()
        return lease.receipt(native_status())

    def test_both_exact_nonblank_privacy_descriptions_are_returned_as_a_new_copy_without_foreign_keys(self):
        information = photos.privacy_information()
        self.assertEqual({"NSCameraUsageDescription", "NSPhotoLibraryUsageDescription"}, set(information))
        self.assertTrue(all(type(value) is str and value.strip() for value in information.values()))
        information["NSCameraUsageDescription"] = "changed model"
        information["NSAppTransportSecurity"] = {"NSAllowsArbitraryLoads": True}
        self.assertNotEqual(information, photos.privacy_information())
        self.assertNotIn("NSAppTransportSecurity", photos.privacy_information())

    def test_ordinary_root_and_exact_source_nonce_uuid_bundle_and_installed_hashes_precede_commands(self):
        for key, value in (("root", Path("relative")), ("simulator", "booted"), ("bundle_id", "foreign.app"),
                           ("source_revision", "f" * 40), ("session_nonce", "c" * 32),
                           ("signed_hash", "A" * 64), ("plist_hash", None)):
            arguments = self.arguments()
            arguments[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                photos.OwnedPhotosLease(**arguments)
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        arguments = self.arguments()
        arguments["root"] = alias
        with self.assertRaises(ValueError):
            photos.OwnedPhotosLease(**arguments)
        self.assertEqual([], self.control.events)

    def test_only_official_owned_photos_grant_and_reset_use_actual_installed_byte_readback_and_scalar_results(self):
        lease = self.lease()
        lease.prepare()
        lease.close()
        expected = [["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE, BUNDLE, "app"],
                    ["/usr/bin/xcrun", "simctl", "privacy", DEVICE, "grant", "photos", BUNDLE],
                    ["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE, BUNDLE, "app"],
                    ["/usr/bin/xcrun", "simctl", "get_app_container", DEVICE, BUNDLE, "app"],
                    ["/usr/bin/xcrun", "simctl", "privacy", DEVICE, "reset", "photos", BUNDLE]]
        self.assertEqual(expected, self.control.events)
        receipt = lease.receipt(native_status())
        self.assertTrue(photos.validate_receipt(receipt, **self.receipt_arguments()))
        self.assertEqual(photos.RECEIPT_FIELDS, set(receipt))
        for action in ("grant", "reset"):
            self.assertEqual(photos.PRIVACY_RESULT_FIELDS, set(receipt[action]))
            self.assertNotIn("stdout", receipt[action])
            self.assertNotIn("stderr", receipt[action])
        for action in ("camera", "photos-add", "all", "revoke", "grant photos", None, {}):
            with self.assertRaises(ValueError):
                lease._privacy(action)
        self.assertEqual(expected, self.control.events)

    def test_bounded_original_grant_nonzero_structured_error_stderr_invalid_and_uncertain_results_fail(self):
        results = (
            subprocess.CompletedProcess([], 1, b"", b""),
            subprocess.CompletedProcess([], 0, b"", b"(domain=NSPOSIXErrorDomain, code=1)"),
            subprocess.CompletedProcess([], 0, b"", b"unstructured warning"),
            subprocess.CompletedProcess([], True, b"", b""),
            subprocess.CompletedProcess([], 0, "not bytes", b""),
            subprocess.CompletedProcess([], 0, b"x" * (1024**2 + 1), b""),
            None,
        )
        for result in results:
            self.control.privacy_results["grant"] = result
            lease = self.lease()
            with self.subTest(result_type=type(result).__name__), self.assertRaises(ValueError):
                lease.prepare()
            self.assertTrue(lease.grant_attempted)
            lease.close()
            self.assertFalse(photos.validate_receipt(lease.receipt(native_status()), **self.receipt_arguments()))
            if isinstance(result, subprocess.CompletedProcess) and type(result.stdout) is bytes and type(result.stderr) is bytes and len(result.stdout) + len(result.stderr) <= 1024**2 and type(result.returncode) is int:
                self.assertEqual(result.returncode, lease.record["grant"]["exit_code"])
                self.assertEqual(hashlib.sha256(result.stderr).hexdigest(), lease.record["grant"]["stderr_sha256"])

    def test_uncertain_or_failed_grant_retains_failure_and_still_owns_one_verified_reset_attempt(self):
        self.control.privacy_results["grant"] = subprocess.TimeoutExpired("source-only-model", 1)
        lease = self.lease()
        with self.assertRaises(subprocess.TimeoutExpired):
            lease.prepare()
        self.assertEqual("TimeoutExpired", lease.record["grant_error_type"])
        lease.close()
        self.assertEqual(1, sum(event[2:5] == ["privacy", DEVICE, "reset"] for event in self.control.events))
        self.assertFalse(photos.validate_receipt(lease.receipt(native_status()), **self.receipt_arguments()))
        self.assertNotIn("source-only-model", json.dumps(lease.receipt(None)))

    def test_reset_error_or_exception_preserves_failed_receipt_and_independent_caller_continuation(self):
        for result in (subprocess.CompletedProcess([], 1, b"", b""),
                       subprocess.CompletedProcess([], 0, b"", b"warning"), OSError("source-only reset failure")):
            self.control.privacy_results["reset"] = result
            lease = self.lease()
            lease.prepare()
            continuation = []
            try:
                lease.close()
            except (ValueError, OSError):
                continuation.append("retained-reset-failure")
            finally:
                continuation.append("independent-owned-uninstall-and-local-cleanup-model")
            self.assertEqual(["retained-reset-failure", "independent-owned-uninstall-and-local-cleanup-model"], continuation)
            self.assertFalse(photos.validate_receipt(lease.receipt(native_status()), **self.receipt_arguments()))

    def test_identity_drift_or_unknown_installed_bytes_refuse_foreign_grant_reset_without_retry(self):
        executable = self.app / application.APP_EXECUTABLE
        original = executable.read_bytes()
        executable.write_bytes(original + b"drift")
        lease = self.lease()
        with self.assertRaises(ValueError):
            lease.prepare()
        self.assertFalse(lease.grant_attempted)
        self.assertFalse(any(event[2] == "privacy" for event in self.control.events))
        executable.write_bytes(original)
        self.control.events.clear()
        lease = self.lease()
        lease.prepare()
        executable.write_bytes(original + b"drift after grant")
        with self.assertRaises(ValueError):
            lease.close()
        self.assertTrue(lease.reset_attempted)
        self.assertFalse(any(event[2:5] == ["privacy", DEVICE, "reset"] for event in self.control.events))
        with self.assertRaises(ValueError):
            lease.close()

    def test_duplicate_prepare_and_close_and_refusing_ownership_queries_never_trigger_automatic_retry(self):
        lease = self.lease()
        lease.prepare()
        before = len(self.control.events)
        with self.assertRaises(ValueError):
            lease.prepare()
        self.assertEqual(before, len(self.control.events))
        lease.close()
        before = len(self.control.events)
        with self.assertRaises(ValueError):
            lease.close()
        self.assertEqual(before, len(self.control.events))
        for method in ("prepare", "close"):
            lease = self.lease()
            if method == "close":
                lease.prepare()
            lease.installed_identity = Mock(side_effect=OSError("refusing identity model"))
            with self.assertRaises(OSError):
                getattr(lease, method)()
            with self.assertRaises(ValueError):
                getattr(lease, method)()
            lease.installed_identity.assert_called_once()
        lease = self.lease()
        lease.close()
        with self.assertRaises(ValueError):
            lease.prepare()
        with self.assertRaises(ValueError):
            lease.close()

    def test_adapter_delegates_original_teamcity_worker_process_and_stream_gates_and_main_return_failure(self):
        observer = protocol()
        observer.feed(marker())
        observer.feed(BUNDLE + ": " + str(PID))
        for line in native_frames():
            observer.feed(line)
        result = observer.finish(0)
        self.assertEqual(5, result["counts"]["passed"])
        self.assertEqual(list(focus.METHODS), [case["name"] for case in result["testcases"]])
        self.assertEqual(native_status(), result["camera_photo_authorization"])
        for process_exit in (1, True, "0"):
            with self.assertRaises(ValueError):
                observer.finish(process_exit)
        for line in ("NATIVECMPKIT_CAMERA_UIKIT_MAIN_RETURNED", "##teamcity[testStarted name='without-suite']",
                     "x" * (application.MAX_LINE_BYTES + 1)):
            observer = protocol()
            with self.assertRaises(ValueError):
                observer.feed(line)

    def test_actual_authorized_main_marker_is_required_once_before_worker_and_other_states_are_retained_failures(self):
        for status in ("limited", "not-determined", "denied", "restricted", "unknown"):
            observer = protocol()
            with self.assertRaises(ValueError):
                observer.feed(marker(status))
            self.assertEqual(status, observer.partial()["camera_photo_authorization"]["status"])
            self.assertFalse(observer.camera_photo_observation["permission_denial_verified"])
            self.assertFalse(observer.camera_photo_observation["user_consent_verified"])
        observer = protocol()
        observer.feed(BUNDLE + ": " + str(PID))
        for line in native_frames():
            observer.feed(line)
        with self.assertRaises(ValueError):
            observer.finish(0)

    def test_duplicate_reordered_foreign_malformed_and_actual_pid_mismatch_markers_refuse_without_header_order_assumption(self):
        for header_first in (True, False):
            observer = protocol()
            for line in ([BUNDLE + ": " + str(PID), marker()] if header_first else [marker(), BUNDLE + ": " + str(PID)]):
                observer.feed(line)
            for line in native_frames():
                observer.feed(line)
            self.assertEqual(PID, observer.finish(0)["camera_photo_authorization"]["process_id"])
        observer = protocol()
        observer.feed(marker())
        with self.assertRaises(ValueError):
            observer.feed(marker())
        observer = protocol()
        observer.feed(ACTIVE)
        with self.assertRaises(ValueError):
            observer.feed(marker())
        for candidate in (marker().replace("mainThread=true", "mainThread=false"), marker().replace("service=photos", "service=all"),
                          marker().replace(SOURCE[:12], "c" * 12), marker().replace(NONCE, "c" * 32),
                          marker(pid=0), marker(pid=2**31), marker() + " extra=true", "NATIVECMPKIT_CAMERA_PHOTOS invalid"):
            with self.assertRaises(ValueError):
                protocol().feed(candidate)
        observer = protocol()
        observer.feed(marker())
        with self.assertRaises(ValueError):
            observer.feed(BUNDLE + ": " + str(PID + 1))

    def test_exact_receipt_source_nonce_uuid_signed_plist_pid_status_schema_and_boolean_fields_reject_substitution(self):
        receipt = self.complete_receipt()
        self.assertTrue(photos.validate_receipt(receipt, **self.receipt_arguments()))
        mutations = (
            lambda r: r.update(schema_version=True), lambda r: r.update(service="all"),
            lambda r: r.update(native_status=None), lambda r: r.update(reset=None),
            lambda r: r.update(owned_identity_before_reset=1), lambda r: r.update(user_consent_verified=0),
            lambda r: r.update(foreign_fixture="accepted"), lambda r: r.update(reset_error_type="OSError"),
            lambda r: r["grant"].update(exit_code=False), lambda r: r["grant"].update(stderr_bytes=False),
            lambda r: r["reset"].update(stdout_sha256="a" * 64),
            lambda r: r["reset"].update(stderr_sha256="a" * 64),
            lambda r: r["reset"].update(foreign="accepted"),
            lambda r: r["native_status"].update(status="limited"),
            lambda r: r["native_status"].update(process_id=PID + 1),
            lambda r: r["native_status"].update(main_thread=1),
        )
        for mutate in mutations:
            bad = copy.deepcopy(receipt)
            mutate(bad)
            self.assertFalse(photos.validate_receipt(bad, **self.receipt_arguments()))
        for key, value in (("source_revision", "c" * 40), ("session_nonce", "c" * 32), ("simulator", "booted"),
                           ("bundle_id", "foreign.app"), ("signed_hash", "c" * 64), ("plist_hash", "c" * 64),
                           ("native_pid", True), ("native_pid", None)):
            arguments = self.receipt_arguments()
            arguments[key] = value
            self.assertFalse(photos.validate_receipt(receipt, **arguments))


if __name__ == "__main__":
    unittest.main()
