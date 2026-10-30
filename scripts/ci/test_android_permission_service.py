"""Synthetic permission-service/owned-install contracts, not Android test results."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import android_geo_probe as p


class AndroidPermissionServiceTests(unittest.TestCase):
    def test_only_actual_permission_manager_constants_are_accepted(self):
        for output, expected in [(b"-1\n", False), (b"0\n", True), (b"-1\r\n", False), (b"0", True)]:
            self.assertIs(expected, p.permission_result(subprocess.CompletedProcess([], 0, output, b"")))
        for code, output, error in [(1, b"-1\n", b""), (0, b"", b""), (0, b"0\n-1\n", b""),
                                    (0, b"-2\n", b""), (0, b"denied\n", b""),
                                    (0, b"Error: unknown command\n", b""),
                                    (0, b"-1\n", b"unknown service error"),
                                    (0, b"0" * 32, b""), (0, b"\x1b[0m-1\n", b"")]:
            with self.assertRaises(ValueError):
                p.permission_result(subprocess.CompletedProcess([], code, output, error))

    def fixture(self, root):
        output = root / "build/ci-verification/synthetic-permission-service"
        output.mkdir(parents=True)
        apk = root / "synthetic-owned.apk"
        apk.write_bytes(b"synthetic-not-an-Android-APK")
        probe = p.OwnedGeoProbe(root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: True,
                                environment={"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(output / "android-user")})
        identity = {"apk_sha256": p.lt.sha256(apk), "exact_one_APK_path_observed": True, "raw_path_uploaded": False}
        return probe, apk, identity

    def responses(self, *arguments, granted=False, malformed=False, **unused):
        if arguments[0] == "install":
            self.assertEqual("-t", arguments[1])
            self.assertNotIn("-g", arguments); self.assertNotIn("-r", arguments)
            return subprocess.CompletedProcess([], 0, b"Success\n", b"")
        if arguments[:4] == ("shell", "dumpsys", "package", "check-permission"):
            self.assertIn(arguments[4], p.PERMISSIONS)
            self.assertEqual((p.PACKAGE, "0"), arguments[5:])
            output = b"unsupported-private-body\n" if malformed else (b"0\n" if granted else b"-1\n")
            return subprocess.CompletedProcess([], 0, output, b"")
        self.assertIn(arguments[0], ("shell", "uninstall"))
        return subprocess.CompletedProcess([], 0, b"", b"")

    def test_install_queries_the_real_service_for_both_permissions_and_exact_user_without_human_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            probe, apk, identity = self.fixture(Path(directory))
            with patch.object(p.lt, "execute", return_value={"exit_code": 0}), patch.object(p, "metadata_apk", return_value=apk), \
                    patch.object(probe, "readback", side_effect=[None, identity]), \
                    patch.object(probe, "control", side_effect=self.responses) as control:
                receipt = probe.prepare()
            calls = [c.args for c in control.call_args_list]
            self.assertEqual([("shell", "dumpsys", "package", "check-permission", permission, p.PACKAGE, "0")
                              for permission in p.PERMISSIONS], calls[1:])
            self.assertEqual({permission: False for permission in p.PERMISSIONS}, receipt["initial_actual_foreground_permissions"])
            self.assertTrue(receipt["initial_denial_verified_by_permission_service"])
            self.assertTrue(receipt["actual_native_permission_reads_still_required"])
            self.assertNotIn("initial_denial_verified_by_package_dump", receipt)
            self.assertNotIn("stdout", json.dumps(receipt))

    def test_unexpected_grant_fails_before_native_suite_and_owned_cleanup_still_removes_only_exact_apk(self):
        with tempfile.TemporaryDirectory() as directory:
            probe, apk, identity = self.fixture(Path(directory))
            with patch.object(p.lt, "execute", return_value={"exit_code": 0}), patch.object(p, "metadata_apk", return_value=apk), \
                    patch.object(probe, "readback", side_effect=[None, identity, identity, None]), \
                    patch.object(probe, "control", side_effect=lambda *args, **kw: self.responses(*args, granted=True, **kw)) as control:
                with self.assertRaises(ValueError): probe.prepare()
                receipt = probe.close()
            self.assertFalse(receipt["initial_denial_verified_by_permission_service"])
            self.assertTrue(receipt["owned_identity_reverified"]); self.assertTrue(receipt["owned_probe_removed"])
            self.assertEqual(1, sum(c.args[0] == "install" for c in control.call_args_list))
            self.assertEqual(1, sum(c.args[0] == "uninstall" for c in control.call_args_list))

    def test_unknown_service_output_is_never_denial_or_success_and_cannot_skip_owned_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            probe, apk, identity = self.fixture(Path(directory))
            with patch.object(p.lt, "execute", return_value={"exit_code": 0}), patch.object(p, "metadata_apk", return_value=apk), \
                    patch.object(probe, "readback", side_effect=[None, identity, identity, None]), \
                    patch.object(probe, "control", side_effect=lambda *args, **kw: self.responses(*args, malformed=True, **kw)):
                with self.assertRaises(ValueError): probe.prepare()
                receipt = probe.close()
            self.assertNotIn("initial_actual_foreground_permissions", receipt)
            self.assertNotIn("unsupported-private-body", json.dumps(receipt))
            self.assertTrue(receipt["owned_identity_reverified"]); self.assertTrue(receipt["owned_probe_removed"])

    def test_prior_or_foreign_app_prevents_permission_reads_install_and_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            probe, unused_apk, identity = self.fixture(Path(directory))
            with patch.object(probe, "readback", return_value=identity), patch.object(probe, "control") as control, \
                    patch.object(p.lt, "execute") as build:
                with self.assertRaises(ValueError): probe.prepare()
            build.assert_not_called(); control.assert_not_called()


if __name__ == "__main__": unittest.main()
