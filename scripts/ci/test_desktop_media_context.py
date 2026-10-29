"""Owned audio orchestration guards using mocked tools; zero native media executions."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import desktop_media_context as audio


class FakeOwnedProcess:
    pid = 7654321  # Synthetic identifier; killpg is mocked, never targets a real process.
    def __init__(self): self.returncode = None; self.force = False
    def poll(self): return self.returncode
    def wait(self, timeout):
        if self.force:
            self.force = False
            raise subprocess.TimeoutExpired("synthetic-owned-pulse", timeout)
        if self.returncode is None: self.returncode = 0
        return self.returncode


class DesktopMediaContextTests(unittest.TestCase):
    def plan(self, suite="desktop", selected=True):
        return {"suite": suite, "expected": [{"module": "calf-webview" if selected else "calf-io",
                "test_source_files": [audio.MEDIA_SOURCE] if selected else []}]}

    def test_other_targets_modules_and_nonlinux_hosts_do_not_start_tools_or_mutate_environment(self):
        for system, suite, selected in (("Darwin", "desktop", True), ("Windows", "desktop", True),
                                        ("Linux", "js", True), ("Linux", "android-device", True),
                                        ("Linux", "desktop", False)):
            with patch.object(audio.platform, "system", return_value=system), patch.object(audio.subprocess, "Popen") as spawn:
                context = audio.OwnedAudio(Path.cwd(), Path("unused"), self.plan(suite, selected)).start()
                self.assertIsNone(context.environment); self.assertIsNone(context.receipt)
                context.close(); spawn.assert_not_called()

    def test_invalid_external_delimiter_symlink_and_overlong_socket_paths_fail_before_tools(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audio.platform, "system", return_value="Linux"), patch.object(audio.subprocess, "Popen") as spawn:
            root = Path(directory); base = root / "build/ci-verification"; base.mkdir(parents=True)
            outside = root / "outside"; outside.mkdir(); linked = base / "linked"; linked.symlink_to(outside, target_is_directory=True)
            for output in (outside, linked, base / 'bad"path', base / "bad\npath", base / ("x" * 108)):
                with self.assertRaises(ValueError): audio.OwnedAudio(root, output, self.plan()).start()
            spawn.assert_not_called()

    def exercise(self, mutation=None, wrong_sink=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); output = root / "build/ci-verification/test"; output.mkdir(parents=True)
            process = FakeOwnedProcess(); unix = socket.socket(socket.AF_UNIX)
            def popen(command, **kwargs):
                self.assertTrue(kwargs["start_new_session"])
                self.assertIn("--daemonize=no", command); self.assertIn("-n", command)
                self.assertNotEqual(os.environ.get("HOME"), kwargs["env"]["HOME"])
                unix.bind(str(output / "desktop-audio/native"))
                return process
            def run(command, **kwargs):
                if command == ["pulseaudio", "--version"]: return SimpleNamespace(stdout="pulseaudio 16.1\n", returncode=0)
                if command == ["pactl", "get-default-sink"]: return SimpleNamespace(stdout=("foreign-sink" if wrong_sink else audio.SINK) + "\n", returncode=0)
                if command == ["pactl", "list", "short", "sinks"]: return SimpleNamespace(stdout="0\t" + audio.SINK + "\tmodule-null-sink.c\ts16le 1ch 16000Hz\tIDLE\n", returncode=0)
                self.fail("Unexpected command")
            context = audio.OwnedAudio(root, output, self.plan())
            before = dict(os.environ)
            try:
                with patch.object(audio.platform, "system", return_value="Linux"), patch.object(audio.subprocess, "Popen", side_effect=popen), patch.object(audio.subprocess, "run", side_effect=run), patch.object(audio.os, "killpg") as kill:
                    if wrong_sink:
                        with patch.object(audio.time, "monotonic", side_effect=[0, 0, 11]):
                            with self.assertRaises(RuntimeError): context.start()
                        self.assertFalse(context.passed()); self.assertEqual([(process.pid, signal.SIGTERM)], [c.args for c in kill.call_args_list]); return
                    context.start()
                    self.assertFalse(context.passed(), "Readiness without owned shutdown cannot be accepted")
                    folder = output / "desktop-audio"
                    self.assertEqual(0o700, folder.stat().st_mode & 0o777)
                    cookie = folder / "private-cookie"
                    self.assertEqual(0o600, cookie.stat().st_mode & 0o777); self.assertEqual(256, cookie.stat().st_size)
                    self.assertNotIn("cookie", json.dumps(context.receipt))
                    self.assertEqual(before, dict(os.environ), "Override only the child environment, never the invoking process/global service")
                    self.assertIn("PULSE_COOKIE", context.environment)
                    self.assertNotIn("auth-anonymous", (folder / "pulse.conf").read_text())
                    if mutation is not None: mutation(folder, process)
                    context.close(); context.close()  # Idempotent; never signal a reaped child again.
                    return context.passed(), context.receipt, [c.args for c in kill.call_args_list]
            finally:
                unix.close()

    def test_positive_calibration_has_authenticated_owned_clocked_sink_and_exact_clean_shutdown(self):
        passed, receipt, signals = self.exercise()
        self.assertTrue(passed); self.assertTrue(receipt["ready_verified"])
        self.assertTrue(receipt["alive_before_owned_shutdown"])
        self.assertFalse(receipt["physical_or_audible_output_verified"])
        self.assertFalse(receipt["engine_decoder_or_callback_substitution"])
        self.assertEqual([(FakeOwnedProcess.pid, signal.SIGTERM)], signals)

    def test_tampered_missing_or_symlinked_configuration_is_not_accepted_after_cleanup(self):
        for mutation in (lambda f, p: (f / "alsa-pulse.conf").write_text("tampered"),
                         lambda f, p: (f / "pulse.conf").unlink(),
                         lambda f, p: ((f / "pulse.conf").unlink(), (f / "pulse.conf").symlink_to(f / "private-cookie"))):
            passed, receipt, signals = self.exercise(mutation)
            self.assertFalse(passed); self.assertFalse(receipt["configuration_unchanged"])
            self.assertEqual([(FakeOwnedProcess.pid, signal.SIGTERM)], signals)

    def test_unexpected_early_exit_and_forced_cleanup_are_not_clean_success(self):
        for mutation in (lambda f, p: setattr(p, "returncode", 0), lambda f, p: setattr(p, "force", True)):
            passed, receipt, _ = self.exercise(mutation)
            self.assertFalse(passed); self.assertFalse(receipt["shutdown"]["clean"])

    def test_failed_readiness_still_terminates_only_the_owned_process(self): self.exercise(wrong_sink=True)

    def test_launch_failure_closes_its_log_and_never_signals_an_uncreated_process(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(audio.platform, "system", return_value="Linux"):
            root = Path(directory).resolve(); output = root / "build/ci-verification/test"; output.mkdir(parents=True)
            context = audio.OwnedAudio(root, output, self.plan())
            with patch.object(audio.subprocess, "run", return_value=SimpleNamespace(stdout="pulseaudio 16.1\n")), \
                    patch.object(audio.subprocess, "Popen", side_effect=OSError("controlled launch failure")), \
                    patch.object(audio.os, "killpg") as kill:
                with self.assertRaises(OSError): context.start()
                self.assertTrue(context.log.closed); self.assertFalse(context.passed())
                context.close(); kill.assert_not_called()

    def test_exit_racing_owned_shutdown_is_reaped_but_not_accepted(self):
        # exercise() patches killpg; override its single shutdown call only.
        original_close = audio.OwnedAudio.close
        def raced_close(context):
            with patch.object(audio.os, "killpg", side_effect=ProcessLookupError):
                original_close(context)
        with patch.object(audio.OwnedAudio, "close", raced_close):
            passed, receipt, _ = self.exercise()
        self.assertFalse(passed); self.assertFalse(receipt["alive_before_owned_shutdown"])
        self.assertEqual(0, receipt["shutdown"]["exit_code"]); self.assertFalse(receipt["shutdown"]["clean"])


if __name__ == "__main__": unittest.main()
