import json
from pathlib import Path
import tempfile
import unittest

import runtime_context as r


class RuntimeContextTest(unittest.TestCase):
    def fixtures(self):
        runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-1"
        phone = {"udid": "01234567-0123-0123-0123-0123456789AB", "isAvailable": True,
                 "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17", "state": "Booted",
                 "name": "PRIVATE USER DEVICE NAME", "dataPath": "/private/machine/path"}
        runtimes = {"runtimes": [{"identifier": runtime, "version": "26.1", "buildversion": "23B77", "isAvailable": True}]}
        return {"devices": {runtime: [phone]}}, runtimes

    def test_java_version_and_major(self):
        self.assertEqual({"version": "17.0.20", "major": 17}, r.parse_java('openjdk version "17.0.20" 2026-10-20\nother vendor details'))
        with self.assertRaises(ValueError): r.parse_java("could not start java")

    def test_actual_rust_fields_only(self):
        text = "rustc 1.98.0 (hash)\nrelease: 1.98.0\nhost: aarch64-apple-darwin\ncommit-hash: " + "a" * 40 + "\ncommit-date: 2026-10-01\nprivate: do not export\n"
        self.assertEqual("1.98.0", r.parse_rust(text)["release"])
        self.assertNotIn("private", r.parse_rust(text))
        with self.assertRaises(ValueError): r.parse_rust("release: nightly")

    def test_actual_xcode_and_sdk(self):
        self.assertEqual({"version": "26.1", "build": "17B31"}, r.parse_xcode("Xcode 26.1\nBuild version 17B31\n"))
        self.assertEqual("26.1", r.sdk_version("26.1\n"))
        with self.assertRaises(ValueError): r.parse_xcode("Xcode 26.1")
        with self.assertRaises(ValueError): r.sdk_version("unknown")

    def test_actual_explicit_browser_version_is_sanitized(self):
        self.assertEqual({"name": "Google Chrome", "version": "144.0.1.2"}, r.parse_browser("Google Chrome 144.0.1.2\n"))
        with self.assertRaises(ValueError): r.parse_browser("Could not start /private/path/chrome")

    def test_simulator_selection_records_runtime_not_names_or_paths(self):
        devices, runtimes = self.fixtures()
        selected = r.simulator(devices, runtimes, kind="iphone")
        self.assertEqual("26.1", selected["runtime_version"])
        self.assertEqual("Booted", selected["state"])
        self.assertNotIn("PRIVATE", json.dumps(selected))
        self.assertNotIn("/private", json.dumps(selected))

    def test_simulator_must_match_kind_and_availability(self):
        devices, runtimes = self.fixtures()
        with self.assertRaises(ValueError): r.simulator(devices, runtimes, kind="ipad")
        runtimes["runtimes"][0]["isAvailable"] = False
        with self.assertRaises(ValueError): r.simulator(devices, runtimes, kind="iphone")

    def test_invalid_and_missing_udid_does_not_choose_another_device(self):
        devices, runtimes = self.fixtures()
        with self.assertRaises(ValueError): r.simulator(devices, runtimes, udid="$(anything)")
        with self.assertRaises(ValueError): r.simulator(devices, runtimes, udid="11111111-1111-1111-1111-111111111111")

    def test_android_platform_excludes_private_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "platforms/android-37.0"; folder.mkdir(parents=True)
            (folder / "source.properties").write_text("AndroidVersion.ApiLevel=37\nPkg.Revision=1\nPrivateField=sensitive\n")
            result = r.android_platform(root, "android-37.0")
            self.assertEqual("platforms;android-37.0", result["package"])
            self.assertNotIn("sensitive", json.dumps(result))
            with self.assertRaises(ValueError): r.android_platform(root, "../../private")
            with self.assertRaises(ValueError): r.android_platform(root, "android-36")

    def test_cache_partition_uses_actual_runtime_not_ephemeral_device_identity(self):
        devices, runtimes = self.fixtures()
        context = {"observed_at_utc": "first", "source_revision": "a" * 40,
                   "host": {"system": "Darwin", "architecture": "arm64"},
                   "simulator": r.simulator(devices, runtimes, kind="iphone"),
                   "apple_sdks": {"iphonesimulator": "26.1"}}
        key = r.compiler_runtime_fingerprint(context)
        context["simulator"]["udid"] = "11111111-1111-1111-1111-111111111111"
        context["simulator"]["state"] = "Shutdown"
        context["observed_at_utc"] = "second"
        self.assertEqual(key, r.compiler_runtime_fingerprint(context))
        context["apple_sdks"]["iphonesimulator"] = "26.2"
        self.assertNotEqual(key, r.compiler_runtime_fingerprint(context))


if __name__ == "__main__":
    unittest.main()
