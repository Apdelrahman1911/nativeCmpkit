"""Owned portal startup/shutdown synthetic fixtures. Zero native dialog executions."""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import picker_dialog_context as portal


class FakeProcess:
    def __init__(self, pid): self.pid, self.returncode, self.force = pid, None, False
    def poll(self): return self.returncode
    def wait(self, timeout):
        if self.force:
            self.force = False
            raise subprocess.TimeoutExpired("synthetic-owned-service", timeout)
        if self.returncode is None: self.returncode = -signal.SIGTERM
        return self.returncode


class PickerDialogContextTests(unittest.TestCase):
    def plan(self, suite="desktop", selected=True):
        return {"suite": suite, "expected": [{"module": "calf-file-picker" if selected else "calf-io",
                "test_source_files": [portal.SOURCE] if selected else []}]}

    def test_nonlinux_other_suite_and_unselected_module_start_nothing(self):
        for system, suite, selected in (("Darwin", "desktop", True), ("Windows", "desktop", True),
                                       ("Linux", "js", True), ("Linux", "android-device", True),
                                       ("Linux", "desktop", False)):
            with patch.object(portal.platform, "system", return_value=system), patch.object(portal.subprocess, "Popen") as spawn:
                context = portal.OwnedPickerPortal(Path.cwd(), Path("unused"), self.plan(suite, selected)).start()
                self.assertIsNone(context.environment); self.assertIsNone(context.receipt)
                context.close(); spawn.assert_not_called()

    def test_outside_symlink_and_missing_display_fail_before_starting_any_process(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(portal.platform, "system", return_value="Linux"), \
                patch.object(portal.subprocess, "Popen") as spawn:
            root = Path(directory).resolve(); base = root / "build/ci-verification"; base.mkdir(parents=True)
            outside = root / "outside"; outside.mkdir(); link = base / "link"; link.symlink_to(outside, target_is_directory=True)
            for output in (outside, base, link):
                with self.assertRaises(ValueError): portal.OwnedPickerPortal(root, output, self.plan()).start()
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "display is required"):
                    portal.OwnedPickerPortal(root, base / "new", self.plan()).start()
            spawn.assert_not_called()

    def exercise(self, mutation=None, failed_launch=None, kill_failure=None, wrong_version=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); output = root / "build/ci-verification/test"; output.mkdir(parents=True)
            frontend, backend = root / "frontend", root / "backend"; frontend.touch(); backend.touch()
            folder = root / "private-portal"; folder.mkdir(mode=0o700)
            processes, commands = [], []
            context = None
            def popen(command, **kwargs):
                commands.append(command)
                self.assertTrue(kwargs["start_new_session"])
                if failed_launch == len(commands): raise OSError("controlled owning launch failure")
                process = FakeProcess(7654300 + len(commands)) # Synthetic PID; every killpg is mocked.
                processes.append(process)
                if len(commands) == 1: (folder / "runtime/bus").touch() # Synthetic readiness, not a real socket.
                return process
            def run(command, **kwargs):
                self.assertEqual(["gdbus", "call", "--session", "--dest", "org.freedesktop.portal.Desktop",
                                  "--object-path", "/org/freedesktop/portal/desktop", "--method",
                                  "org.freedesktop.DBus.Properties.Get", "org.freedesktop.portal.FileChooser", "version"], command)
                return SimpleNamespace(returncode=0, stdout="(<uint32 4>,)" if wrong_version else "(<uint32 3>,)")
            def kill(pid, sig):
                if kill_failure and pid == processes[-1].pid and sig == signal.SIGTERM: raise kill_failure
            before = dict(os.environ)
            with patch.object(portal.platform, "system", return_value="Linux"), patch.dict(os.environ, {"DISPLAY": ":876"}), \
                    patch.object(portal, "FRONTEND", frontend), patch.object(portal, "BACKEND", backend), \
                    patch.object(portal.shutil, "which", return_value="/synthetic/tool"), \
                    patch.object(portal.tempfile, "mkdtemp", return_value=str(folder)), \
                    patch.object(portal.subprocess, "Popen", side_effect=popen), \
                    patch.object(portal.subprocess, "run", side_effect=run), patch.object(portal.os, "killpg", side_effect=kill) as signals:
                context = portal.OwnedPickerPortal(root, output, self.plan())
                if failed_launch:
                    with self.assertRaises(OSError): context.start()
                elif wrong_version:
                    with patch.object(portal.time, "monotonic", side_effect=[0, 0, 21]):
                        with self.assertRaisesRegex(ValueError, "v3 interface"): context.start()
                else:
                    context.start()
                    self.assertFalse(context.receipt["closed"])
                    self.assertNotIn("clean_owned_shutdown", context.receipt)
                    self.assertEqual(0o700, folder.stat().st_mode & 0o777)
                    for name in ("runtime", "config", "data", "cache"):
                        self.assertEqual(0o700, (folder / name).stat().st_mode & 0o777)
                    configuration = (folder / "bus.conf").read_text()
                    self.assertIn("<auth>EXTERNAL</auth>", configuration)
                    for unwanted in ("<servicedir>", "<standard_session_servicedirs", "<include", "ANONYMOUS"):
                        self.assertNotIn(unwanted, configuration)
                    self.assertNotEqual(os.environ.get("DBUS_SESSION_BUS_ADDRESS"), context.environment["DBUS_SESSION_BUS_ADDRESS"])
                    self.assertEqual(":876", context.environment["NATIVECMPKIT_PICKER_OWNED_DISPLAY"])
                    self.assertEqual(str(processes[1].pid), context.environment["NATIVECMPKIT_PICKER_PORTAL_PID"])
                    if mutation: mutation(processes)
                    context.close()
                context.close() # Must not signal an already handled group.
                calls = [call.args for call in signals.call_args_list]
            self.assertEqual(before, dict(os.environ))
            self.assertTrue(all(log.closed for log in context.logs))
            return context.receipt, calls, processes

    def test_success_uses_private_external_bus_real_service_commands_and_exact_owned_cleanup(self):
        receipt, signals, processes = self.exercise()
        self.assertTrue(receipt["clean_owned_shutdown"])
        self.assertEqual(3, receipt["actual_filechooser_version"])
        self.assertFalse(receipt["mock_portal"]); self.assertFalse(receipt["existing_user_bus_used"])
        self.assertEqual([(p.pid, signal.SIGTERM) for p in reversed(processes)], signals)

    def test_launch_and_version_failures_reap_only_created_groups_and_close_all_logs(self):
        for failed in (1, 2, 3):
            receipt, signals, processes = self.exercise(failed_launch=failed)
            self.assertFalse(receipt["clean_owned_shutdown"])
            self.assertEqual("OSError", receipt["startup_error"])
            self.assertEqual([(p.pid, signal.SIGTERM) for p in reversed(processes)], signals)
        receipt, signals, processes = self.exercise(wrong_version=True)
        self.assertFalse(receipt["clean_owned_shutdown"])
        self.assertEqual([(p.pid, signal.SIGTERM) for p in reversed(processes)], signals)

    def test_unexpected_early_exit_and_forced_group_termination_are_not_clean(self):
        for mutation in (lambda processes: setattr(processes[-1], "returncode", 0),
                         lambda processes: setattr(processes[-1], "force", True),
                         lambda processes: setattr(processes[-1], "returncode", 9)):
            receipt, _, _ = self.exercise(mutation=mutation)
            self.assertFalse(receipt["clean_owned_shutdown"])

    def test_shutdown_exit_race_is_reaped_not_accepted_and_other_owned_groups_are_still_closed(self):
        receipt, signals, processes = self.exercise(kill_failure=ProcessLookupError())
        self.assertFalse(receipt["clean_owned_shutdown"])
        self.assertTrue(receipt["shutdown"][0]["early_exit"])
        self.assertEqual(3, len(receipt["shutdown"]))
        self.assertTrue(all(process.returncode is not None for process in processes))

    def test_one_cleanup_error_never_skips_other_groups_and_logs(self):
        receipt, signals, processes = self.exercise(kill_failure=PermissionError())
        self.assertFalse(receipt["clean_owned_shutdown"])
        self.assertEqual("PermissionError", receipt["shutdown"][0]["cleanup_error"])
        self.assertEqual(3, len(signals)); self.assertEqual(3, len(receipt["shutdown"]))

    def test_child_audio_and_portal_overrides_are_preserved_without_mutating_the_base_and_conflicts_fail(self):
        base = {"DISPLAY": ":1", "XDG_RUNTIME_DIR": "/base"}
        audio = {**base, "PULSE_SERVER": "unix:/owned-audio", "PULSE_COOKIE": "/synthetic-private"}
        native = {**base, "XDG_RUNTIME_DIR": "/owned-portal", "DBUS_SESSION_BUS_ADDRESS": "unix:/owned-bus"}
        merged = portal.merge_owned_environments(base, audio, native)
        self.assertEqual(audio["PULSE_SERVER"], merged["PULSE_SERVER"])
        self.assertEqual(native["XDG_RUNTIME_DIR"], merged["XDG_RUNTIME_DIR"])
        self.assertEqual("/base", base["XDG_RUNTIME_DIR"])
        with self.assertRaises(ValueError):
            portal.merge_owned_environments(base, {"XDG_RUNTIME_DIR": "/first"}, {"XDG_RUNTIME_DIR": "/second"})


if __name__ == "__main__": unittest.main()
