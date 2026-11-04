# SPDX-License-Identifier: Apache-2.0
"""Per-installed-bundle Photos setup, never consent/denial acceptance.

Only fixed official simctl grant/reset photos commands on this invocation's
source/nonce/signed/plist-bound installed application. No camera/photos-add/all,
foreign bundle, ambient resolver/privacy database access, retries or fallback.
Actual Main PHPhotoLibrary readback is separate from command acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

import camera_ios_ownership_native_focus as focus

BUNDLE = re.compile(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r([0-9a-f]{12})\.t([0-9a-f]{32})\Z")
UUID = re.compile(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
PHOTO_MARKER = re.compile(r"NATIVECMPKIT_CAMERA_PHOTOS phase=readback mainThread=true service=photos access=read-write "
    r"status=(authorized|limited|not-determined|denied|restricted|unknown) source=([0-9a-f]{12}) "
    r"nonce=([0-9a-f]{32}) pid=([1-9][0-9]{0,9})\Z")
PRIVACY_INFORMATION = {
    "NSCameraUsageDescription": "Disposable library Camera ownership verification; no physical capture is performed.",
    "NSPhotoLibraryUsageDescription": "Disposable library Camera fallback presentation verification with controlled tiny images.",
}
RECEIPT_FIELDS = frozenset({
    "schema_version", "operation", "focus", "service", "simulator_udid", "bundle_id",
    "source_revision", "session_nonce", "signed_application_executable_sha256", "application_plist_sha256",
    "grant", "reset", "native_status", "owned_identity_before_grant", "owned_identity_after_grant",
    "owned_identity_before_reset", "camera_or_photos_add_or_all_service_modified", "foreign_app_permissions_mutated",
    "permission_denial_verified", "user_consent_verified", "privacy_database_read_or_written",
    "retries_or_fallback", "raw_command_output_or_user_photos_uploaded",
})
PRIVACY_RESULT_FIELDS = frozenset({
    "action", "service", "exit_code", "error_identities", "stdout_bytes", "stderr_bytes",
    "stdout_sha256", "stderr_sha256",
})


def privacy_information() -> dict:
    return dict(PRIVACY_INFORMATION)


def protocol_adapter(base_protocol, *, bundle_id: str, source_revision: str, session_nonce: str):
    """New Camera-only observer delegates every original protocol/TeamCity gate.

    No fabricated XML, changed logger/argv/deadline or completion synthesis. The
    actual simctl PID header may be buffered independently; equality is mandatory
    at finish, never an invented stdout arrival order.
    """
    match = BUNDLE.fullmatch(bundle_id) if type(bundle_id) is str else None
    if (match is None or type(source_revision) is not str or re.fullmatch(r"[0-9a-f]{40}", source_revision) is None or
            type(session_nonce) is not str or match.groups() != (source_revision[:12], session_nonce)):
        raise ValueError("Camera observer requires exact source-bound disposable bundle/nonce")

    class CameraPrivacyProtocol(base_protocol):
        def __init__(self):
            super().__init__(bundle_id=bundle_id)
            self.camera_photo_observation = None

        def feed(self, line: str):
            # Preserve all original byte/line bounds and actual protocol parsing.
            super().feed(line)
            marker = PHOTO_MARKER.fullmatch(line)
            if marker:
                if (self.camera_photo_observation is not None or self.active is not None or self.completed is not None or
                        self.stack or self.open_case is not None or self.cases or
                        marker.groups()[1:3] != (source_revision[:12], session_nonce) or int(marker[4]) > 2**31 - 1):
                    raise ValueError("Missing/duplicate/reordered/foreign Camera native Photos readback")
                self.camera_photo_observation = {
                    "phase": "readback", "main_thread": True, "service": "photos", "access_level": "read-write",
                    "status": marker[1], "source_revision_prefix": marker[2], "session_nonce": marker[3],
                    "process_id": int(marker[4]), "permission_denial_verified": False, "user_consent_verified": False,
                }
                if marker[1] != "authorized":
                    raise ValueError("Actual native Photos status refuses the controlled fallback setup")
            elif line.startswith("NATIVECMPKIT_CAMERA_"):
                # Includes the original Camera UIApplicationMain-return failure.
                raise ValueError("Unknown or failing Camera application lifecycle/readback marker")
            if self.camera_photo_observation is not None and self.observed_launch_pid is not None and \
                    self.camera_photo_observation["process_id"] != self.observed_launch_pid:
                raise ValueError("Camera native status PID differs from actual source-bound simctl launch PID")

        def partial(self):
            return {**super().partial(), "camera_photo_authorization": self.camera_photo_observation}

        def finish(self, process_exit):
            result = super().finish(process_exit)
            status = self.camera_photo_observation
            if (type(status) is not dict or status["status"] != "authorized" or
                    type(self.observed_launch_pid) is not int or status["process_id"] != self.observed_launch_pid):
                raise ValueError("Camera requires one actual Authorized Main readback from the exact launched app PID")
            return {**result, "camera_photo_authorization": status}

    return CameraPrivacyProtocol()


class OwnedPhotosLease:
    """One new object per exact owned installation; reset cannot skip uninstall."""
    def __init__(self, *, root: Path, simulator: str, bundle_id: str, source_revision: str,
                 session_nonce: str, signed_hash: str, plist_hash: str, execute_control,
                 installed_identity, control_status):
        match = BUNDLE.fullmatch(bundle_id) if type(bundle_id) is str else None
        if (type(root) is not type(Path()) or not root.is_absolute() or root != root.resolve(strict=True) or
                type(simulator) is not str or UUID.fullmatch(simulator) is None or match is None or
                type(source_revision) is not str or re.fullmatch(r"[0-9a-f]{40}", source_revision) is None or
                type(session_nonce) is not str or match.groups() != (source_revision[:12], session_nonce) or
                any(type(value) is not str or DIGEST.fullmatch(value) is None for value in (signed_hash, plist_hash))):
            raise ValueError("Camera Photos lease requires exact ordinary checkout and source/nonce/installed bytes")
        self.root, self.simulator, self.bundle_id = root, simulator, bundle_id
        self.execute_control, self.installed_identity, self.control_status = execute_control, installed_identity, control_status
        self.signed_hash, self.plist_hash = signed_hash, plist_hash
        self.prepare_called = self.grant_attempted = self.reset_attempted = self.close_called = False
        self.record = {"schema_version": 1, "operation": "owned-camera-photos-controlled-setup",
            "focus": focus.FOCUS, "service": "photos", "simulator_udid": simulator, "bundle_id": bundle_id,
            "source_revision": source_revision, "session_nonce": session_nonce,
            "signed_application_executable_sha256": signed_hash, "application_plist_sha256": plist_hash,
            "grant": None, "reset": None, "native_status": None,
            "owned_identity_before_grant": False, "owned_identity_after_grant": False, "owned_identity_before_reset": False,
            "camera_or_photos_add_or_all_service_modified": False, "foreign_app_permissions_mutated": False,
            "permission_denial_verified": False, "user_consent_verified": False, "privacy_database_read_or_written": False,
            "retries_or_fallback": False, "raw_command_output_or_user_photos_uploaded": False}

    def _owned(self) -> bool:
        result = self.execute_control(["/usr/bin/xcrun", "simctl", "get_app_container", self.simulator, self.bundle_id, "app"])
        owned = self.installed_identity(result, self.bundle_id, self.signed_hash, self.plist_hash)
        if type(owned) is not bool:
            raise ValueError("One exact installed-byte ownership verdict is required")
        return owned

    def _privacy(self, action: str) -> dict:
        if type(action) is not str or action not in {"grant", "reset"}:
            raise ValueError("Only fixed official grant/reset photos may be requested")
        result = self.execute_control(["/usr/bin/xcrun", "simctl", "privacy", self.simulator, action, "photos", self.bundle_id])
        if (not isinstance(result, subprocess.CompletedProcess) or type(result.returncode) is not int or
                type(result.stdout) is not bytes or type(result.stderr) is not bytes or
                len(result.stdout) + len(result.stderr) > 1024**2):
            raise ValueError("Preserve one actual bounded simulator privacy command result")
        return {"action": action, "service": "photos", **self.control_status(result),
                "stdout_bytes": len(result.stdout), "stderr_bytes": len(result.stderr),
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr).hexdigest()}

    def prepare(self):
        if self.prepare_called or self.close_called:
            raise ValueError("No duplicate Camera privacy grant/retry")
        self.prepare_called = True  # Even an ownership-query refusal is never automatically retried.
        self.record["owned_identity_before_grant"] = self._owned()
        if not self.record["owned_identity_before_grant"]:
            raise ValueError("Refuse privacy changes on an unknown/foreign installed bundle")
        self.grant_attempted = True  # A failing/uncertain command still requires an owning reset attempt.
        try:
            self.record["grant"] = self._privacy("grant")
        except Exception as error:
            self.record["grant_error_type"] = type(error).__name__
            raise
        self.record["owned_identity_after_grant"] = self._owned()
        if (self.record["grant"]["exit_code"] != 0 or self.record["grant"]["error_identities"] or
                self.record["grant"]["stderr_bytes"] != 0 or not self.record["owned_identity_after_grant"]):
            raise ValueError("Unsupported/error/identity drift refuses Camera Photos setup; no retry or broad service fallback")

    def close(self):
        if self.close_called:
            raise ValueError("No duplicate Camera privacy reset/retry")
        self.close_called = True
        if not self.grant_attempted:
            return
        self.reset_attempted = True  # A refusing ownership query cannot authorize another attempt.
        self.record["owned_identity_before_reset"] = self._owned()
        if not self.record["owned_identity_before_reset"]:
            raise ValueError("Refuse reset of a changed/nonowned installed bundle")
        try:
            self.record["reset"] = self._privacy("reset")
        except Exception as error:
            self.record["reset_error_type"] = type(error).__name__
            raise
        if (self.record["reset"]["exit_code"] != 0 or self.record["reset"]["error_identities"] or
                self.record["reset"]["stderr_bytes"] != 0):
            raise ValueError("Owned photos reset is unverified; preserve failure but independently uninstall the owned app")

    def receipt(self, native_status):
        # The transport supplies its actual bounded marker or None on prelaunch failure.
        self.record["native_status"] = native_status
        return json.loads(json.dumps(self.record))


def validate_receipt(receipt, *, simulator: str, bundle_id: str, source_revision: str,
                     session_nonce: str, signed_hash: str, plist_hash: str, native_pid: int) -> bool:
    try:
        match = BUNDLE.fullmatch(bundle_id) if type(bundle_id) is str else None
        if (type(simulator) is not str or UUID.fullmatch(simulator) is None or match is None or
                type(source_revision) is not str or re.fullmatch(r"[0-9a-f]{40}", source_revision) is None or
                type(session_nonce) is not str or match.groups() != (source_revision[:12], session_nonce) or
                any(type(value) is not str or DIGEST.fullmatch(value) is None for value in (signed_hash, plist_hash)) or
                type(receipt) is not dict or set(receipt) != RECEIPT_FIELDS or type(receipt.get("schema_version")) is not int or
                receipt["schema_version"] != 1 or receipt.get("operation") != "owned-camera-photos-controlled-setup" or
                receipt.get("focus") != focus.FOCUS or receipt.get("service") != "photos" or
                receipt.get("simulator_udid") != simulator or receipt.get("bundle_id") != bundle_id or
                receipt.get("source_revision") != source_revision or receipt.get("session_nonce") != session_nonce or
                receipt.get("signed_application_executable_sha256") != signed_hash or
                receipt.get("application_plist_sha256") != plist_hash or any("error" in name for name in receipt) or
                any(receipt.get(key) is not True for key in
                    ("owned_identity_before_grant", "owned_identity_after_grant", "owned_identity_before_reset")) or
                any(receipt.get(key) is not False for key in
                    ("camera_or_photos_add_or_all_service_modified", "foreign_app_permissions_mutated", "permission_denial_verified",
                     "user_consent_verified", "privacy_database_read_or_written", "retries_or_fallback",
                     "raw_command_output_or_user_photos_uploaded"))):
            return False
        for action in ("grant", "reset"):
            result = receipt[action]
            if (type(result) is not dict or set(result) != PRIVACY_RESULT_FIELDS or
                    result.get("action") != action or result.get("service") != "photos" or
                    type(result.get("exit_code")) is not int or result["exit_code"] != 0 or
                    type(result.get("error_identities")) is not list or result["error_identities"] != [] or
                    result.get("stderr_bytes") != 0 or
                    any(type(result.get(key)) is not int or not 0 <= result[key] <= 1024**2 for key in ("stdout_bytes", "stderr_bytes")) or
                    any(type(result.get(key)) is not str or DIGEST.fullmatch(result[key]) is None for key in
                        ("stdout_sha256", "stderr_sha256")) or
                    result["stderr_sha256"] != hashlib.sha256(b"").hexdigest() or
                    result["stdout_bytes"] == 0 and result["stdout_sha256"] != hashlib.sha256(b"").hexdigest()):
                return False
        observed = receipt["native_status"]
        return (type(native_pid) is int and 0 < native_pid <= 2**31 - 1 and type(observed) is dict and
                observed == {"phase": "readback", "main_thread": True, "service": "photos", "access_level": "read-write",
                    "status": "authorized", "source_revision_prefix": source_revision[:12], "session_nonce": session_nonce,
                    "process_id": native_pid, "permission_denial_verified": False, "user_consent_verified": False} and
                type(observed.get("process_id")) is int and observed.get("main_thread") is True and
                observed.get("permission_denial_verified") is False and observed.get("user_consent_verified") is False)
    except (KeyError, TypeError, ValueError):
        return False
