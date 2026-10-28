import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import runtime_context as r


class SimulatorStartupBudgetTest(unittest.TestCase):
    def test_only_the_two_finite_inventory_commands_get_a_cold_start_budget(self):
        inventory = [("xcrun", "simctl", "list", kind, "--json") for kind in ("devices", "runtimes")]
        ordinary = [
            ("java", "-version"), ("git", "rev-parse", "HEAD"),
            ("rustc", "--version", "--verbose"), ("xcodebuild", "-version"),
            ("xcrun", "--sdk", "iphonesimulator", "--show-sdk-version"),
            ("xcrun", "simctl", "boot", "01234567-0123-0123-0123-0123456789AB"),
            ("xcrun", "simctl", "list", "devices"),
            ("xcrun", "simctl", "list", "devices", "--json", "extra"),
        ]
        for args in inventory + ordinary:
            with self.subTest(args=args), mock.patch.object(r.subprocess, "run") as run:
                run.return_value = subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")
                self.assertEqual("{}", r.command(*args))
                run.assert_called_once_with(args, cwd=r.ROOT, capture_output=True, text=True,
                                            timeout=180 if args in inventory else 60)

    def test_expired_inventory_remains_a_failure_and_is_not_retried(self):
        args = ("xcrun", "simctl", "list", "devices", "--json")
        expired = subprocess.TimeoutExpired(args, 180)
        with mock.patch.object(r.subprocess, "run", side_effect=expired) as run:
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                r.command(*args)
            self.assertIs(expired, caught.exception)
            run.assert_called_once_with(args, cwd=r.ROOT, capture_output=True, text=True, timeout=180)

    def test_nonzero_inventory_is_not_accepted_and_private_diagnostics_stay_out(self):
        args = ("xcrun", "simctl", "list", "runtimes", "--json")
        with mock.patch.object(r.subprocess, "run") as run:
            run.return_value = subprocess.CompletedProcess(args, 1, stdout="private-user-data", stderr="private-path")
            with self.assertRaisesRegex(RuntimeError, "^xcrun returned exit 1$") as caught:
                r.command(*args)
            self.assertNotIn("private", str(caught.exception))
            self.assertEqual(1, run.call_count)

    def test_inventory_budget_never_waives_device_availability_or_actual_boot_state(self):
        runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-5"
        device = "01234567-0123-0123-0123-0123456789AB"
        for available, state, requested in [(False, "Booted", device), (True, "Shutdown", device),
                                            (True, "Booted", "11111111-1111-1111-1111-111111111111")]:
            with self.subTest(available=available, state=state, requested=requested), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.98.0"\n')
                responses = {
                    ("git", "rev-parse", "HEAD"): "a" * 40,
                    ("git", "status", "--porcelain", "--untracked-files=normal"): "",
                    ("java", "-version"): 'openjdk version "17.0.20"',
                    ("rustc", "--version", "--verbose"): "release: 1.98.0\nhost: aarch64-apple-darwin\ncommit-hash: "
                        + "b" * 40 + "\ncommit-date: 2026-08-18\n",
                    ("xcodebuild", "-version"): "Xcode 26.6\nBuild version 17F113\n",
                    ("xcrun", "simctl", "list", "devices", "--json"): json.dumps({"devices": {runtime: [{
                        "udid": device, "isAvailable": available, "state": state,
                        "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-Air"}]}}),
                    ("xcrun", "simctl", "list", "runtimes", "--json"): json.dumps({"runtimes": [{
                        "identifier": runtime, "version": "26.5", "buildversion": "23F77", "isAvailable": True}]}),
                    **{("xcrun", "--sdk", sdk, "--show-sdk-version"): "26.5"
                       for sdk in ("macosx", "iphoneos", "iphonesimulator")},
                }
                with (mock.patch.object(r, "ROOT", root),
                      mock.patch.object(r, "command", side_effect=lambda *args: responses[args]) as commands,
                      mock.patch.object(r.platform, "machine", return_value="arm64"),
                      mock.patch.object(r.platform, "system", return_value="Darwin"),
                      mock.patch.object(r, "compiler_runtime_fingerprint") as fingerprint):
                    with self.assertRaises(ValueError):
                        r.capture(expected_arch="arm64", apple=True, device=requested,
                                  require_booted=True, require_clean=True)
                    fingerprint.assert_not_called()
                    self.assertEqual(1, commands.call_args_list.count(
                        mock.call("xcrun", "simctl", "list", "devices", "--json")))
                    self.assertEqual(1, commands.call_args_list.count(
                        mock.call("xcrun", "simctl", "list", "runtimes", "--json")))


if __name__ == "__main__":
    unittest.main()
