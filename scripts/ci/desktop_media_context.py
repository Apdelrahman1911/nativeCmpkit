"""Owned, clocked Linux audio output for real JavaFX/WebKit media verification.

A PulseAudio null sink replaces only physical/audible output, never the native
engine, decoder, media clock, load/cancel operations or callbacks. No global
service, anonymous protocol, user configuration or credentials are used. The
random local protocol cookie is private, temporary test data and is NOT evidence.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import platform
import signal
import subprocess
import time

MEDIA_SOURCE = "calf-webview/src/desktopTest/kotlin/com/mohamedrejeb/calf/ui/web/DesktopWebViewLifetimeTest.kt"
SINK = "nativecmpkit_verification"
ALSA = b"# Owned verification process only; real PulseAudio-clocked software output.\npcm.!default { type pulse }\nctl.!default { type pulse }\n"


class OwnedAudio:
    def __init__(self, root: Path, output: Path, plan: dict):
        self.root = root.resolve()
        self.output = output
        self.requested = (platform.system() == "Linux" and plan["suite"] == "desktop" and any(
            item["module"] == "calf-webview" and MEDIA_SOURCE in item["test_source_files"] for item in plan["expected"]))
        self.environment = None
        self.receipt = None
        self.process = None
        self.log = None

    def start(self) -> "OwnedAudio":
        if not self.requested:
            return self
        allowed = self.root / "build/ci-verification"
        folder = self.output / "desktop-audio"
        if (not folder.resolve().is_relative_to(allowed) or folder == allowed or
                any(p.is_symlink() for p in (folder, *folder.parents))):
            raise ValueError("Audio output must be confined to owned verification files")
        if any(character in str(folder) for character in ('"', '\\', '\r', '\n')):
            raise ValueError("Audio configuration paths must not contain command delimiters")
        if len(os.fsencode(folder / "native")) >= 108:
            raise ValueError("Owned PulseAudio socket exceeds Linux's Unix-socket path limit")
        folder.mkdir(mode=0o700)
        for name in ("home", "runtime", "state"):
            (folder / name).mkdir(mode=0o700)
        socket = folder / "native"
        cookie = folder / "private-cookie"
        with cookie.open("xb") as handle:
            os.chmod(cookie, 0o600)
            handle.write(os.urandom(256))
        config = folder / "pulse.conf"
        config.write_text("load-module module-null-sink sink_name=" + SINK + " rate=16000 channels=1 format=s16le\n" +
                          'load-module module-native-protocol-unix socket="' + str(socket) + '" auth-cookie="' + str(cookie) + '"\n' +
                          "set-default-sink " + SINK + "\n", encoding="utf-8")
        alsa = folder / "alsa-pulse.conf"
        alsa.write_bytes(ALSA)
        env = os.environ.copy()
        env.update(PULSE_SERVER="unix:" + str(socket), PULSE_COOKIE=str(cookie), ALSA_CONFIG_PATH=str(alsa))
        pulse_env = {**env, "HOME": str(folder / "home"), "PULSE_RUNTIME_PATH": str(folder / "runtime"),
                     "PULSE_STATE_PATH": str(folder / "state"), "XDG_RUNTIME_DIR": str(folder / "runtime")}
        version = subprocess.run(["pulseaudio", "--version"], check=True, capture_output=True, text=True, timeout=5).stdout.strip()
        if not version.startswith("pulseaudio ") or len(version) > 100:
            raise ValueError("Actual PulseAudio version was not established")
        self.receipt = {"adapter": "clocked-native-pulseaudio-null-output", "version": version,
                        "physical_or_audible_output_verified": False, "engine_decoder_or_callback_substitution": False,
                        "anonymous_protocol_enabled": False, "global_service_started": False,
                        "alsa_configuration_sha256": hashlib.sha256(ALSA).hexdigest(),
                        "pulse_configuration_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                        "ready_verified": False}
        self.log = (folder / "owned-pulse.log").open("w")
        try:
            self.process = subprocess.Popen(["pulseaudio", "--daemonize=no", "--use-pid-file=no", "--exit-idle-time=-1",
                                             "--disable-shm=yes", "-n", "--file=" + str(config)],
                                            env=pulse_env, stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and self.process.poll() is None:
                if socket.exists():
                    result = subprocess.run(["pactl", "get-default-sink"], env=env, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and result.stdout.strip() == SINK:
                        sinks = subprocess.run(["pactl", "list", "short", "sinks"], env=env,
                                               check=True, capture_output=True, text=True, timeout=5).stdout.splitlines()
                        rows = [line.split("\t") for line in sinks]
                        if (len(rows) != 1 or len(rows[0]) != 5 or rows[0][1:4] !=
                                [SINK, "module-null-sink.c", "s16le 1ch 16000Hz"]):
                            raise ValueError("Actual audio sink differs from the owned software-clock/output contract")
                        self.receipt.update(ready_verified=True, sink=SINK, native_module=rows[0][2], format=rows[0][3])
                        self.environment = env
                        return self
                time.sleep(0.1)
            raise RuntimeError("Owned clocked audio output did not establish readiness")
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        if self.process is None:
            if self.log is not None:
                self.log.close()
            return
        forced = False
        running = self.process.poll() is None
        if running:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                running = False # An unexpected exit raced the signal; reap, but never accept it.
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            forced = True
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass # The owned child may have exited meanwhile; still forced/not clean.
            self.process.wait(timeout=5)
        if self.log is not None:
            self.log.close()
        folder = self.output / "desktop-audio"
        try:
            configs = (folder / "alsa-pulse.conf", folder / "pulse.conf")
            unchanged = (all(p.is_file() and not p.is_symlink() and p.stat().st_nlink == 1 for p in configs) and
                         hashlib.sha256(configs[0].read_bytes()).hexdigest() == self.receipt["alsa_configuration_sha256"] and
                         hashlib.sha256(configs[1].read_bytes()).hexdigest() == self.receipt["pulse_configuration_sha256"])
        except OSError:
            unchanged = False
        self.receipt.update(configuration_unchanged=unchanged, alive_before_owned_shutdown=running,
                            shutdown={"exit_code": self.process.returncode, "forced_owned_group": forced,
                                      "clean": self.process.returncode == 0 and not forced and running})
        self.process = None

    def passed(self) -> bool:
        return (self.receipt is not None and self.receipt.get("ready_verified") is True and
                self.receipt.get("configuration_unchanged") is True and self.receipt.get("shutdown", {}).get("clean") is True)
