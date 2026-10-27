"""Own ONLY a controlled single-root Linux Gradle9.7.1/JDK17 invocation.

Fresh private daemon-log names nominate candidates, never authorize a signal.
Every daemon must be a live, exact-command/private-environment child of this
runner's verified Java client and be pinned/revalidated before admission.
Detached groups use pidfds, not guessed killpg targets or receipt PIDs. A
temporary single-threaded subreaper lease permits exact adopted-child reaping;
there is no /proc PID scan, wildcard wait, jcmd, wrapper or descendant claim.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from itertools import islice
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import threading
import time

import gradle_process as g
import integrity_model as m

MAX_PROC = 256 * 1024
MAX_DIRECTORY_ENTRIES = 128
MAX_DAEMONS = 16
LOG_NAME = re.compile(r"daemon-([1-9][0-9]{0,9})\.out\.log\Z")
PR_SET_CHILD_SUBREAPER = 36
PR_GET_CHILD_SUBREAPER = 37
_ACTIVE = False


def proc_bytes(pid: int, name: str, limit: int = MAX_PROC) -> bytes:
    g.require(type(pid) is int and pid > 1, "invalid-process-id")
    g.require(name in {"stat", "cmdline", "environ"}, "unsupported-proc-read")
    with (Path("/proc") / str(pid) / name).open("rb") as stream:
        raw = stream.read(limit + 1)
    g.require(len(raw) <= limit, "proc-input-limit")
    return raw


def identity(pid: int) -> g.ProcessIdentity:
    g.require((Path("/proc") / str(pid)).stat().st_uid == os.getuid(), "foreign-process-user")
    return g.parse_stat(proc_bytes(pid, "stat", 8192), pid)


def exited(handle: int) -> bool:
    return bool(select.select([handle], [], [], 0)[0])


def check_environment(actual: dict[str, str], workspace: Path, jdk_home: Path) -> None:
    _, expected, options = g.private_values(workspace)
    g.require(all(actual.get(key) == value for key, value in expected.items()), "private-environment-mismatch")
    g.require(actual.get("JAVA_TOOL_OPTIONS") == options and actual.get("JAVA_HOME") == str(jdk_home),
              "jvm-environment-mismatch")
    g.require(not any(key in actual for key in g.FORBIDDEN_ENVIRONMENT), "inherited-jvm-override")
    g.require(actual.get("PATH", "").startswith(str(jdk_home / "bin") + os.pathsep), "jdk-path-mismatch")
    for relative in set(m.JVM_PRIVATE_PATHS.values()) | set(m.ENV_PRIVATE_PATHS.values()):
        g.require(m.confined(workspace, relative, must_exist=True).is_dir(), "private-directory-missing")


@dataclass
class Lease:
    process: g.ProcessIdentity
    handle: int
    role: str
    java_verified: bool = False
    term_sent: bool = False
    kill_sent: bool = False
    wait_status: str | None = None
    exited: bool = False
    pid_absent: bool = False
    handle_closed: bool = False
    signal_permitted: bool = True

    def public(self) -> dict:
        return {**self.process.public(), "role": self.role, "java_verified": self.java_verified,
                "term_sent": self.term_sent, "kill_sent": self.kill_sent,
                "wait_status": self.wait_status, "exited": self.exited,
                "pid_absent": self.pid_absent, "handle_closed": self.handle_closed}


class OwnedGradle:
    """Dedicated, serial controller lease. Calls must stay on the main thread."""

    def __init__(self, command: list[str], workspace: Path, environment: dict[str, str], gradle_home: Path):
        self.command = list(command)
        self.workspace = workspace
        self.jdk = Path(environment.get("JAVA_HOME", ""))
        self.gradle = gradle_home
        self.environment = environment
        self.process: subprocess.Popen | None = None
        self.client: Lease | None = None
        self.daemons: dict[int, Lease] = {}
        self.directory_handle: int | None = None
        self.directory_identity: tuple[int, int] | None = None
        self.baseline_names: set[str] = set()
        self.admitted_names: set[str] = set()
        self.previous_subreaper: int | None = None
        self.previous_signals: dict[int, object] = {}
        self.subreaper_restored = False
        self.signals_restored = False
        self.active = False
        self.errors: list[str] = []
        self.receipt: dict | None = None
        self.controller: g.ProcessIdentity | None = None

    @property
    def daemon_directory(self) -> Path:
        return m.confined(self.workspace, f".dependency-cache/daemon/{m.GRADLE_VERSION}")

    def _error(self, code: str) -> None:
        if code not in self.errors and len(self.errors) < 32:
            self.errors.append(code)

    def _directory_files(self) -> list[tuple[str, tuple[int, int, int, int, int]]]:
        """Bounded, no-follow filename/stat reads; no daemon-log body is read."""
        path = self.daemon_directory
        if not path.exists():
            g.require(self.directory_handle is None, "owned-daemon-directory-disappeared")
            return []
        g.require(path.is_dir() and not path.is_symlink(), "owned-daemon-directory-invalid")
        if self.directory_handle is None:
            handle = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                record = os.fstat(handle)
                g.require(record.st_uid == os.getuid(), "owned-daemon-directory-user")
                self.directory_identity = (record.st_dev, record.st_ino)
                self.directory_handle = handle
            finally:
                if self.directory_handle is None:
                    os.close(handle)
        current = path.stat(follow_symlinks=False)
        g.require((current.st_dev, current.st_ino) == self.directory_identity,
                  "owned-daemon-directory-replaced")
        with os.scandir(self.directory_handle) as stream:
            entries = [entry.name for entry in islice(stream, MAX_DIRECTORY_ENTRIES + 1)]
        g.require(len(entries) <= MAX_DIRECTORY_ENTRIES, "owned-daemon-directory-limit")
        files = []
        for name in sorted(entries):
            if not LOG_NAME.fullmatch(name):
                continue
            record = os.stat(name, dir_fd=self.directory_handle, follow_symlinks=False)
            g.require(stat.S_ISREG(record.st_mode) and record.st_uid == os.getuid() and record.st_nlink == 1,
                      "owned-daemon-log-not-private-regular")
            files.append((name, (record.st_dev, record.st_ino, record.st_uid, record.st_mode, record.st_nlink)))
        g.require(len(files) <= MAX_DAEMONS, "owned-daemon-log-limit")
        return files

    def _subreaper(self, value: int | None = None) -> int:
        libc = ctypes.CDLL(None, use_errno=True)
        if value is not None:
            g.require(libc.prctl(PR_SET_CHILD_SUBREAPER, value, 0, 0, 0) == 0, "owned-subreaper-set-failed")
        current = ctypes.c_int()
        g.require(libc.prctl(PR_GET_CHILD_SUBREAPER, ctypes.byref(current), 0, 0, 0) == 0 and
                  current.value in {0, 1}, "owned-subreaper-read-failed")
        return current.value

    def begin(self) -> None:
        global _ACTIVE
        g.require(sys.platform == "linux" and callable(getattr(os, "pidfd_open", None)) and
                  callable(getattr(signal, "pidfd_send_signal", None)),
                  "owned-linux-pidfd-required")
        g.require(threading.current_thread() is threading.main_thread() and not _ACTIVE,
                  "owned-dedicated-controller-required")
        with os.scandir("/proc/self/task") as stream:
            g.require(len(list(islice(stream, 2))) == 1, "owned-single-thread-required")
        for path in (self.workspace, self.jdk, self.gradle):
            g.require(path.is_absolute() and path == path.resolve() and not path.is_symlink() and
                      not any(parent.is_symlink() for parent in path.parents), "owned-noncanonical-path")
        g.require(self.command and self.command[0] == str(self.gradle / "bin/gradle") and
                  self.gradle.name == "gradle-9.7.1" and "--no-daemon" in self.command,
                  "owned-installed-gradle-command-required")
        check_environment(self.environment, self.workspace, self.jdk)
        self.baseline_names = {name for name, _ in self._directory_files()}
        self.controller = identity(os.getpid())
        self.previous_subreaper = self._subreaper()
        _ACTIVE = self.active = True
        g.require(self._subreaper(1) == 1, "owned-subreaper-not-enabled")

        def interrupt(signum, frame):
            raise KeyboardInterrupt

        for signum in (signal.SIGINT, signal.SIGTERM):
            self.previous_signals[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupt)

    def start(self, process: subprocess.Popen) -> None:
        self.process = process
        first = identity(process.pid)
        g.require(first.parent == os.getpid() and first.group == first.session == first.pid and
                  first.start_ticks >= self.controller.start_ticks, "owned-launcher-ancestry")
        handle = os.pidfd_open(process.pid, 0)
        try:
            g.require(not exited(handle) and identity(process.pid) == first, "owned-launcher-pin-changed")
            self.client = Lease(first, handle, "launcher")
        finally:
            if self.client is None:
                os.close(handle)

    def _java(self, pid: int, role: str, *, cleanup: bool = False) -> g.ProcessIdentity:
        first = identity(pid)
        g.require(self.client is not None and identity(os.getpid()) == self.controller, "owned-controller-changed")
        g.require(Path(os.readlink(f"/proc/{pid}/exe")) == self.jdk / "bin/java", "java-executable-mismatch")
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
        g.require(cwd.is_relative_to(self.workspace), "java-cwd-outside-candidate")
        arguments = g.fields(proc_bytes(pid, "cmdline"))
        g.require(arguments[0] == str(self.jdk / "bin/java"), "java-command-mismatch")
        if role == "client":
            g.require(first == self.client.process and cwd == self.workspace, "owned-client-changed")
            g.require(arguments == [*g.client_prefix(self.jdk, self.gradle), *self.command[1:]],
                      "gradle-client-command-mismatch")
        else:
            client = self.client.process
            if not cleanup:
                g.require(not exited(self.client.handle) and self.client.java_verified and
                          identity(client.pid) == client, "owned-live-client-required")
            parents = {client.pid, os.getpid()} if cleanup else {client.pid}
            g.require(pid != client.pid and first.parent in parents and first.start_ticks >= client.start_ticks and
                      ((first.group == client.group and first.session == client.session) or
                       first.group == first.session == pid), "daemon-ancestry-mismatch")
            g.daemon_entrypoint(arguments, self.gradle, self.workspace)
        check_environment(g.environment(proc_bytes(pid, "environ")), self.workspace, self.jdk)
        g.require(identity(pid) == first, "java-identity-changed")
        return first

    def poll(self) -> None:
        if self.client is None:
            raise g.WitnessError("owned-launcher-not-pinned")
        if not self.client.java_verified and not exited(self.client.handle):
            # bin/gradle starts as a shell then execs Java without changing PID/start.
            actual = Path(os.readlink(f"/proc/{self.client.process.pid}/exe"))
            if actual == self.jdk / "bin/java":
                g.require(self._java(self.client.process.pid, "client") == self.client.process,
                          "owned-client-changed")
                self.client.java_verified = True
                self.client.role = "client"
        for name, file_identity in self._directory_files():
            if name in self.baseline_names or name in self.admitted_names:
                continue
            pid = int(LOG_NAME.fullmatch(name)[1])
            first = self._java(pid, "daemon")
            handle = os.pidfd_open(pid, 0)
            try:
                current = dict(self._directory_files()).get(name)
                g.require(current == file_identity and not exited(handle) and self._java(pid, "daemon") == first,
                          "owned-daemon-pin-changed")
                self.daemons[pid] = Lease(first, handle, "daemon", java_verified=True)
                self.admitted_names.add(name)
            finally:
                if pid not in self.daemons:
                    os.close(handle)
        # Prove/pin every candidate first, so ambiguity cannot abandon proven leases.
        g.require(len(self.daemons) <= 1, "ambiguous-gradle-daemon")

    def _signal(self, lease: Lease, signum: int) -> None:
        if not lease.signal_permitted or exited(lease.handle):
            return
        try:
            now = (self._java(lease.process.pid, "daemon", cleanup=True) if lease.role == "daemon"
                   else identity(lease.process.pid))
            original = lease.process
            g.require((now.pid, now.group, now.session, now.start_ticks) ==
                      (original.pid, original.group, original.session, original.start_ticks),
                      "owned-process-changed-before-signal")
            if lease.role != "daemon":
                g.require(now.parent == os.getpid(), "owned-launcher-ancestry")
            if exited(lease.handle):
                return
            signal.pidfd_send_signal(lease.handle, signum)
            if signum == signal.SIGTERM:
                lease.term_sent = True
            else:
                lease.kill_sent = True
        except (g.WitnessError, OSError, ValueError):
            if not exited(lease.handle):
                lease.signal_permitted = False
                self._error("owned-signal-revalidation-failed")

    def _wait_until(self, leases: list[Lease], deadline: float) -> None:
        while time.monotonic() < deadline:
            if self.process is not None:
                self.process.poll()  # Reap ONLY the direct Popen child; allow exact daemon adoption.
            if all(exited(lease.handle) for lease in leases):
                return
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))

    def cleanup(self, max_seconds: float = 10) -> dict:
        """Bounded best effort on every path; incomplete ownership never succeeds."""
        global _ACTIVE
        if self.receipt is not None:
            return self.receipt
        g.require(0 < max_seconds <= 10, "owned-cleanup-budget")
        began = time.monotonic()
        deadline = began + max_seconds
        leases = [*self.daemons.values(), *([self.client] if self.client is not None else [])]
        try:
            # Repeated cancellation cannot interrupt the bounded ownership cleanup.
            for signum in self.previous_signals:
                signal.signal(signum, signal.SIG_IGN)
            for lease in leases:
                self._signal(lease, signal.SIGTERM)
            # A direct launcher that failed before pidfd admission is still an
            # unreaped child constructed by us, never a receipt-discovered PID.
            if self.process is not None and self.client is None and self.process.poll() is None:
                self.process.terminate()
            self._wait_until(leases, began + max_seconds / 2)
            for lease in leases:
                self._signal(lease, signal.SIGKILL)
            if self.process is not None and self.client is None and self.process.poll() is None:
                self.process.kill()
            self._wait_until(leases, deadline)
            if self.process is not None:
                try:
                    self.process.wait(timeout=max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    self._error("owned-client-wait-timeout")
            for lease in leases:
                lease.exited = exited(lease.handle)
                if not lease.exited:
                    self._error("owned-process-still-running")
                    continue
                if lease.role == "daemon":
                    try:
                        pid, _ = os.waitpid(lease.process.pid, os.WNOHANG)
                        g.require(pid == lease.process.pid, "owned-daemon-not-reaped")
                        lease.wait_status = "exact-adopted-daemon-reaped"
                    except ChildProcessError:
                        lease.wait_status = "not-waitable-by-controller"
                else:
                    lease.wait_status = "direct-popen-child-reaped"
                lease.pid_absent = not (Path("/proc") / str(lease.process.pid)).exists()
                if not lease.pid_absent:
                    self._error("owned-process-absence-unverified")
        except (g.WitnessError, OSError, ValueError):
            self._error("owned-cleanup-error")
        finally:
            for lease in leases:
                try:
                    os.close(lease.handle)
                    lease.handle_closed = True
                except OSError:
                    self._error("owned-pidfd-close-error")
            if self.directory_handle is not None:
                try:
                    os.close(self.directory_handle)
                    self.directory_handle = None
                except OSError:
                    self._error("owned-directory-close-error")
            if self.previous_subreaper is not None:
                try:
                    self.subreaper_restored = self._subreaper(self.previous_subreaper) == self.previous_subreaper
                    if not self.subreaper_restored:
                        self._error("owned-subreaper-restore-error")
                except (g.WitnessError, OSError):
                    self._error("owned-subreaper-restore-error")
            for signum, previous in self.previous_signals.items():
                signal.signal(signum, previous)
            self.signals_restored = True
            if self.active:
                _ACTIVE = self.active = False
        complete = (not self.errors and self.client is not None and self.client.java_verified and
                    len(self.daemons) == 1 and self.subreaper_restored and self.signals_restored and
                    all(lease.exited and lease.pid_absent and lease.handle_closed for lease in leases))
        self.receipt = {"schema_version": 1, "record_type": "owned-gradle-cleanup",
                        "scope": "Controlled single-root Linux installed Gradle9.7.1/JDK17 client and exactly proven daemon only",
                        "complete": complete, "errors": list(self.errors),
                        "client": self.client.public() if self.client is not None else None,
                        "daemons": [lease.public() for lease in self.daemons.values()],
                        "temporary_subreaper_previous": self.previous_subreaper,
                        "temporary_subreaper_restored": self.subreaper_restored,
                        "signal_handlers_restored": self.signals_restored,
                        "cleanup_elapsed_seconds": round(time.monotonic() - began, 3),
                        "directory_handle_closed": self.directory_handle is None,
                        "log_bodies_read": False, "receipt_pid_used": False,
                        "global_process_scan_or_wildcard_wait": False, "all_descendants_verified": False,
                        "ordinary_wrapper_or_other_host_verified": False, "release_readiness_certified": False}
        return self.receipt
