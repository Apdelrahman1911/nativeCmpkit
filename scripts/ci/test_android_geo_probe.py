"""Synthetic separate-UID installer ownership guards; no actual Android/consumer pass."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import android_geo_probe as p


class OwnedAndroidGeoProbeTests(unittest.TestCase):
    def test_presence_must_be_one_actual_path_and_unknown_errors_never_authorize_overwrite(self):
        result = lambda code, out, err=b"": subprocess.CompletedProcess([], code, out, err)
        self.assertIsNone(p.installed_path(result(1, b"")))
        self.assertEqual("/data/app/~~actual/owned-abc/base.apk", p.installed_path(result(0, b"package:/data/app/~~actual/owned-abc/base.apk\n")))
        for code, body, error in [(0, b"package:/foreign/base.apk", b""), (0, b"package:/data/app/../base.apk", b""),
                                   (0, b"package:/data/app/owned/base.apk\npackage:/data/app/other/base.apk", b""),
                                   (1, b"", b"unknown service failure"), (149, b"", b"")]:
            with self.assertRaises(ValueError): p.installed_path(result(code, body, error))

    def test_permissions_are_exactly_user_zero_and_missing_duplicate_or_granted_values_are_observed(self):
        body = ("Package owned:\n User 0:\n  runtime permissions:\n" + "".join("   " + name + ": granted=false, flags=[]\n" for name in p.PERMISSIONS)).encode()
        self.assertEqual({name: False for name in p.PERMISSIONS}, p.permission_state(body))
        self.assertTrue(p.permission_state(body.replace(b"granted=false", b"granted=true", 1))[p.PERMISSIONS[0]])
        omitted = p.permission_state(body.replace(p.PERMISSIONS[0].encode(), b"foreign"))
        self.assertIsNone(omitted[p.PERMISSIONS[0]], "Missing dumpsys rows are unknown, never an inferred denial")
        for invalid in (body + b" User 1:\n", body.replace(b" User 0:", b" User 4:"), body + body,
                        body + ("   " + p.PERMISSIONS[0] + ": granted=false, flags=[]\n").encode(), b"private unknown dump"):
            with self.assertRaises(ValueError): p.permission_state(invalid)

    def test_probe_assembly_receives_the_same_private_signing_environment_without_export_or_parent_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root / "build/ci-verification/synthetic"; output.mkdir(parents=True)
            user = output / "android-user"; user.mkdir()
            environment = {"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(user),
                           "PRIVATE_FIXTURE_VALUE": "synthetic-private-not-for-receipts"}
            probe = p.OwnedGeoProbe(root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: True,
                                    environment=environment)
            environment["PRIVATE_FIXTURE_VALUE"] = "parent-later-change"
            with patch.object(probe, "readback", return_value=None), patch.object(p.lt, "execute", return_value={"exit_code": 1}) as execute:
                with self.assertRaises(RuntimeError): probe.prepare()
            self.assertEqual("synthetic-private-not-for-receipts", execute.call_args.kwargs["env"]["PRIVATE_FIXTURE_VALUE"])
            self.assertEqual(str(user), execute.call_args.kwargs["env"]["ANDROID_USER_HOME"])
            self.assertEqual("parent-later-change", environment["PRIVATE_FIXTURE_VALUE"])
            self.assertNotIn("PRIVATE_FIXTURE_VALUE", json.dumps(probe.receipt))
            self.assertNotIn("synthetic-private-not-for-receipts", json.dumps(probe.receipt))

    def test_metadata_requires_one_unsplit_owned_regular_apk_and_rejects_escape_symlinks_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); base = root / p.FIXTURE / "build/outputs/apk/debug"; base.mkdir(parents=True)
            apk = base / "owned-debug.apk"; apk.write_bytes(b"synthetic-not-Android-bytes")
            metadata = base / "output-metadata.json"
            data = {"applicationId": p.PACKAGE, "variantName": "debug", "artifactType": {"type": "APK"},
                    "elements": [{"type": "SINGLE", "filters": [], "outputFile": apk.name}]}
            metadata.write_text(json.dumps(data)); self.assertEqual(apk, p.metadata_apk(root))
            for key, value in [("applicationId", "foreign.app"), ("variantName", "release")]:
                invalid = dict(data); invalid[key] = value; metadata.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError): p.metadata_apk(root)
            metadata.write_text(json.dumps(data)); apk.unlink(); apk.symlink_to(metadata)
            with self.assertRaises(ValueError): p.metadata_apk(root)
            with self.assertRaises(ValueError): p.unique([("a", 1), ("a", 2)])

    def test_selected_avd_lease_is_rechecked_before_every_control_without_fallback_or_private_transcripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root / "build/ci-verification/synthetic"; output.mkdir(parents=True)
            probe = p.OwnedGeoProbe(root, output, Path("/synthetic/sdk"), "emulator-5588", lambda: False,
                                    environment={"ANDROID_SERIAL": "emulator-5588", "ANDROID_USER_HOME": str(output / "android-user")})
            with patch.object(p.subprocess, "run") as command, self.assertRaises(ValueError): probe.control("uninstall", p.PACKAGE)
            command.assert_not_called()
            self.assertFalse(probe.receipt["packages_published"])
            self.assertFalse(probe.receipt["raw_package_dump_paths_or_console_uploaded"])

    def test_source_install_has_no_auto_grant_or_replace_and_cleanup_reverifies_the_same_bytes(self):
        source = Path(p.__file__).read_text()
        self.assertIn('self.control("install", "-t", str(apk)', source)
        self.assertNotIn('self.control("install", "-g"', source)
        self.assertNotIn('self.control("install", "-r"', source)
        self.assertIn('actual["apk_sha256"] != self.digest', source)
        self.assertIn('self.readback() is None', source)
        self.assertIn('initial_actual_foreground_permissions', source)


if __name__ == "__main__": unittest.main()
