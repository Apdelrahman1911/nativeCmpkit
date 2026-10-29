"""Owned real Linux GTK/FileChooser portal for library-level native lifetime tests.

Only a private EXTERNAL-authenticated D-Bus and two explicitly started real portal
services are used. No mock FileChooser, existing user bus, auto-activation,
unrelated desktop window, global service or raw private log is evidence.
"""
from __future__ import annotations

import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import tempfile
import time

SOURCE = "calf-file-picker/src/desktopTest/kotlin/com/mohamedrejeb/calf/picker/NativePickerComposeLifetimeTest.kt"
FRONTEND = Path("/usr/libexec/xdg-desktop-portal")
BACKEND = Path("/usr/libexec/xdg-desktop-portal-gtk")


class OwnedPickerPortal:
    def __init__(self, root: Path, output: Path, plan: dict):
        self.root, self.output = root.resolve(), output
        self.requested = platform.system() == "Linux" and plan["suite"] == "desktop" and any(
            item["module"] == "calf-file-picker" and SOURCE in item["test_source_files"] for item in plan["expected"])
        self.environment = None
        self.receipt = None
        self.folder = None
        self.processes = []
        self.logs = []
        self.closed = False

    def start(self) -> "OwnedPickerPortal":
        if not self.requested:
            return self
        allowed = self.root / "build/ci-verification"
        if (not self.output.resolve().is_relative_to(allowed) or self.output == allowed or
                any(p.is_symlink() for p in (self.output, *self.output.parents))):
            raise ValueError("Portal output must be owned and confined to library verification")
        if not os.environ.get("DISPLAY"):
            raise ValueError("A real owned Xvfb/X11 display is required, not a headless/native substitute")
        for tool in ("dbus-daemon", "gdbus", "xdotool"):
            if not shutil.which(tool):
                raise ValueError(f"Required real native dialog prerequisite absent: {tool}")
        if not FRONTEND.is_file() or not BACKEND.is_file():
            raise ValueError("Both real installed FileChooser portal services are required")
        self.folder = Path(tempfile.mkdtemp(prefix="nck-picker-", dir="/tmp"))
        os.chmod(self.folder, 0o700)
        for name in ("runtime", "config", "data", "cache"):
            (self.folder / name).mkdir(mode=0o700)
        configs = self.folder / "config/xdg-desktop-portal"
        configs.mkdir(mode=0o700)
        (configs / "portals.conf").write_text("[preferred]\ndefault=gtk\norg.freedesktop.impl.portal.FileChooser=gtk\n")
        socket = self.folder / "runtime/bus"
        bus_config = self.folder / "bus.conf"
        # No standard service directories/includes: never launch arbitrary user/session services.
        bus_config.write_text(
            '<busconfig><type>session</type><listen>unix:path=' + str(socket) + '</listen>'
            '<auth>EXTERNAL</auth><policy context="default"><allow own="*"/>'
            '<allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
        env = os.environ.copy()
        env.update(DBUS_SESSION_BUS_ADDRESS="unix:path=" + str(socket),
                   XDG_RUNTIME_DIR=str(self.folder / "runtime"), XDG_CONFIG_HOME=str(self.folder / "config"),
                   XDG_DATA_HOME=str(self.folder / "data"), XDG_CACHE_HOME=str(self.folder / "cache"),
                   XDG_CURRENT_DESKTOP="GNOME", GTK_USE_PORTAL="0", NO_AT_BRIDGE="1")
        self.environment = env
        self.receipt = {"requested": True, "real_private_bus": True, "authentication": "EXTERNAL",
                        "auto_activation_service_directories": False, "real_frontend": str(FRONTEND),
                        "real_backend": str(BACKEND), "mock_portal": False,
                        "existing_user_bus_used": False, "closed": False}
        try:
            self._spawn(["dbus-daemon", "--nofork", "--config-file=" + str(bus_config)], "bus")
            deadline = time.monotonic() + 10
            while not socket.exists():
                self._live()
                if time.monotonic() >= deadline:
                    raise ValueError("Owned private D-Bus socket did not become ready")
                time.sleep(0.05)
            backend = self._spawn([str(BACKEND)], "gtk")
            self._spawn([str(FRONTEND)], "portal")
            deadline = time.monotonic() + 20
            reply = None
            while time.monotonic() < deadline:
                self._live()
                response = subprocess.run(
                    ["gdbus", "call", "--session", "--dest", "org.freedesktop.portal.Desktop",
                     "--object-path", "/org/freedesktop/portal/desktop", "--method",
                     "org.freedesktop.DBus.Properties.Get", "org.freedesktop.portal.FileChooser", "version"],
                    env=env, capture_output=True, text=True, timeout=3)
                if response.returncode == 0 and response.stdout.strip() == "(<uint32 3>,)":
                    reply = response.stdout.strip()
                    break
                time.sleep(0.1)
            if reply is None:
                raise ValueError("Actual private GTK FileChooser v3 interface did not become ready; inspect private owned logs")
            self.environment["NATIVECMPKIT_PICKER_PORTAL_PID"] = str(backend.pid)
            self.environment["NATIVECMPKIT_PICKER_OWNED_DISPLAY"] = env["DISPLAY"]
            self.receipt.update(actual_filechooser_version=3, ready=True, backend_pid=backend.pid,
                                owned_service_pids=[process.pid for process in self.processes])
            return self
        except BaseException as error:
            self.receipt.update(startup_error=type(error).__name__, ready=False)
            self.close()
            raise

    def _spawn(self, command: list[str], name: str) -> subprocess.Popen:
        # Private logs/config/runtime are intentionally outside upload/committed receipts.
        log = (self.folder / (name + ".private.log")).open("xb")
        self.logs.append(log)
        process = subprocess.Popen(command, env=self.environment, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        self.processes.append(process)
        return process

    def _live(self) -> None:
        if any(p.poll() is not None for p in self.processes):
            raise ValueError("An owned real FileChooser service exited early; no native pass")

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        shutdown = []
        for process in reversed(self.processes):
            forced = False
            early = process.poll() is not None
            error = None
            try:
                if not early:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        early = True # Reap a raced exit, but never accept it as clean.
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    forced = True
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass # A raced forced exit still fails the cleanup gate.
                    process.wait(timeout=5)
            except (OSError, subprocess.SubprocessError) as failure:
                # Continue reaping the other owned groups/logs after one failure.
                error = type(failure).__name__
            shutdown.append({"pid": process.pid, "exit_code": process.returncode, "forced": forced,
                             "early_exit": early, "cleanup_error": error})
        for log in self.logs:
            log.close()
        if self.receipt is not None:
            self.receipt.update(closed=True, shutdown=shutdown,
                                clean_owned_shutdown=(self.receipt.get("ready") is True and len(shutdown) == 3 and
                                    all(not item["forced"] and not item["early_exit"] and not item["cleanup_error"] and
                                        item["exit_code"] in {0, -signal.SIGTERM} for item in shutdown)))
        # The owner reviews runtime outcome separately. Clean service shutdown alone
        # must not delete diagnostics from a failed library test. Private files remain
        # in the owned 0700 folder, never an artifact or a global cache purge.


def merge_owned_environments(base: dict[str, str], *environments: dict[str, str] | None) -> dict[str, str]:
    """Keep distinct child-only audio/portal overrides; conflicting ownership fails."""
    result, changed = dict(base), {}
    for environment in environments:
        for key, value in (environment or {}).items():
            if base.get(key) == value:
                continue
            if key in changed and changed[key] != value:
                raise ValueError("Conflicting owned runtime environment overrides")
            changed[key] = value
            result[key] = value
    return result
