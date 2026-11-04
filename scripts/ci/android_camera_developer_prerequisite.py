"""Sole Dont-keep route: fresh guest master prerequisite and exact disposal.

Not a native setter, Settings UI substitute or general device option. Only a
new exclusively owned API35 guest is admitted. The native method and its public
Settings/accessibility/task/native/scalar leases remain unchanged. Fixed-key
reads are bounded and private; every uncertain mutation is latched once. A new
kernel lifetime, not task absence or an adb acknowledgement, is the observer
barrier before master restoration. Discarding userdata never waives a failure.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

FOCUS = "android-camera-real-restoration-dont-keep"
MODULE = "calf-camera-picker"
SERIAL = "emulator-5588"
REPORTER = "com.mohamedrejeb.calf.calfcamerapicker.test"
RECEIVER = "io.github.apdelrahman1911.nativecmpkit.verification.camerareceiver"
MASTER = "development_settings_enabled"
SCALAR = "always_finish_activities"
PROCESS_HEADER = "ACTIVITY MANAGER RUNNING PROCESSES (dumpsys activity processes)"
READINESS = "  mProcessesReady=true mSystemReady=true mBooted=true mFactoryTest=0"
RECENTS_HEADER = "ACTIVITY MANAGER RECENT TASKS (dumpsys activity recents)"
ACTIVITIES_HEADER = "ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)"
CONTROL_BYTES = 65536
DUMP_BYTES = 1048576
ANDROID = "{http://schemas.android.com/apk/res/android}"
CONVENTION = "convention-plugins/src/main/kotlin/Android.kt"
CONVENTION_SHA256 = "204b7b0bb30e33144794ffda1d993f925f670cac87c809155d81fe9f09f7a256"
MODULE_SHA256 = "f074767f7042ac6e07955b361400e672ae43209f99b17986acd27cf5078428c7"
FAILURES = (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyboardInterrupt)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def is_required(api: int, modules: tuple[str, ...] | None, focus: str | None) -> bool:
    if focus != FOCUS:
        return False
    require(type(api) is int and api == 35 and type(modules) is tuple and modules == (MODULE,),
            "Only the existing sole API35/Dont-keep/camera route admits this prerequisite")
    return True


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate owned metadata field")
        result[key] = value
    return result


def identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def open_directory(path: Path) -> int:
    """Open every absolute ancestor without following a symlink."""
    require(path.is_absolute() and ".." not in path.parts, "Absolute confined path required")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def regular(path: Path, cap: int) -> tuple[int, os.stat_result]:
    parent = open_directory(path.parent)
    try:
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(descriptor)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= cap,
                "Expected bounded regular unshared owned file")
        return descriptor, info
    except BaseException:
        os.close(descriptor)
        raise


def file_digest(path: Path, cap: int) -> tuple[str, tuple[int, int, int, int]]:
    descriptor, before = regular(path, cap)
    try:
        digest, size = hashlib.sha256(), 0
        while payload := os.read(descriptor, 1048576):
            size += len(payload)
            require(size <= cap, "Owned file grew beyond its bound")
            digest.update(payload)
        after = os.fstat(descriptor)
        require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink) ==
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink) and size == before.st_size,
                "Owned file changed while reading")
        return digest.hexdigest(), (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    finally:
        os.close(descriptor)


def file_bytes(path: Path, cap: int) -> bytes:
    descriptor, before = regular(path, cap)
    try:
        payload = os.read(descriptor, cap + 1)
        require(len(payload) == before.st_size and len(payload) <= cap and
                identity(os.fstat(descriptor)) == identity(before), "Changed or unbounded owned file")
        return payload
    finally:
        os.close(descriptor)


class Journal:
    """Public-safe facts only, checkpointed before any uncertain IPC."""
    def __init__(self, directory: int, filename: str):
        self.directory, self.filename, self.last = directory, filename, None
        try:
            os.stat(filename, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise ValueError("A prior prerequisite receipt exists")

    def write(self, receipt: dict) -> None:
        if self.last is not None:
            info = os.stat(self.filename, dir_fd=self.directory, follow_symlinks=False)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and identity(info) == self.last,
                    "Prerequisite receipt identity changed")
        payload = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
        require(len(payload) <= CONTROL_BYTES, "Unbounded prerequisite facts")
        temporary = ".camera-prerequisite-" + uuid.uuid4().hex + ".tmp"
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY | os.O_CLOEXEC,
                             0o600, dir_fd=self.directory)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                require(written > 0, "Prerequisite checkpoint write failed")
                view = view[written:]
            os.fsync(descriptor)
            os.replace(temporary, self.filename, src_dir_fd=self.directory, dst_dir_fd=self.directory)
            self.last = identity(os.fstat(descriptor))
            os.fsync(self.directory)
        finally:
            os.close(descriptor)
            try:
                os.unlink(temporary, dir_fd=self.directory)
            except FileNotFoundError:
                pass


def probe_child(process: subprocess.Popen) -> bool:
    require(isinstance(process, subprocess.Popen) and type(process.pid) is int and process.pid > 0,
            "The actual captured Popen child is required")
    require(process.poll() is None and os.getsid(process.pid) == process.pid and os.getpgid(process.pid) == process.pid,
            "Owned live child session/group identity was lost")
    require(os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None,
            "Expected the same still-running direct child, not a PID lookup")
    return process.poll() is None


def stop_command(process: subprocess.Popen) -> None:
    """Only this bounded host-command child, never a guest/package/ADB daemon."""
    if process.poll() is not None:
        return  # No signal after reap.
    require(os.getpgid(process.pid) == process.pid and os.getsid(process.pid) == process.pid,
            "Bounded command child session lost")
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=2)


def bounded_run(argv: list[str], *, cwd: Path, timeout: float, limit: int,
                environment: dict[str, str]) -> subprocess.CompletedProcess:
    require(0 < timeout <= 120 and 0 < limit <= DUMP_BYTES and all(isinstance(arg, str) for arg in argv),
            "Bounded explicit argv control required")
    process = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    payloads = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for label, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, selectors.EVENT_READ, label)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Owned bounded command exceeded its deadline")
                for key, _ in selector.select(min(remaining, 0.2)):
                    part = os.read(key.fileobj.fileno(), min(65536, limit + 1))
                    if not part:
                        selector.unregister(key.fileobj)
                    else:
                        payloads[key.data].extend(part)
                        require(sum(map(len, payloads.values())) <= limit, "Owned control exceeded its byte bound")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Owned bounded command exceeded its deadline")
            process.wait(timeout=remaining)
        return subprocess.CompletedProcess(argv, process.returncode, bytes(payloads["stdout"]), bytes(payloads["stderr"]))
    finally:
        try:
            stop_command(process)
        finally:
            process.stdout.close()
            process.stderr.close()


def result_bytes(result: subprocess.CompletedProcess, cap: int, *, codes=(0,)) -> bytes:
    require(isinstance(result.stdout, bytes) and isinstance(result.stderr, bytes) and
            len(result.stdout) + len(result.stderr) <= cap and result.returncode in codes and not result.stderr,
            "Unknown or unbounded explicit control result")
    return result.stdout


def line(result: subprocess.CompletedProcess, cap: int, pattern: bytes, *, query_identity=None) -> bytes:
    payload = result_bytes(result, cap)
    try:
        require(re.fullmatch(pattern + rb"(?:\r?\n)?", payload) is not None, "Unknown scalar control shape")
    except ValueError as error:
        try:
            record_scalar_control_refusal(error, result, payload, cap, pattern, query_identity)
        except BaseException:
            pass  # Optional fixed facts must not replace the original scalar-shape refusal.
        raise
    return payload.removesuffix(b"\n").removesuffix(b"\r")


@dataclass(frozen=True)
class Row:
    present: bool
    value: str | None

    def safe(self) -> dict:
        return {"present": self.present, "value": self.value}


def parse_row(getter: subprocess.CompletedProcess, query: subprocess.CompletedProcess, key: str) -> Row:
    require(key in (MASTER, SCALAR), "No arbitrary settings key")
    value = line(getter, 512, rb"(?:null|0|1)",
                 query_identity=("global-settings-get-user0", key)).decode()
    row = line(query, 512, rb"(?:No result found\.|Row: 0 name=" + key.encode() + rb", value=(?:0|1))",
               query_identity=("global-settings-single-row-user0", key)).decode()
    if row == "No result found.":
        require(value == "null", "Getter and absent-row proof disagree")
        return Row(False, None)
    actual = row[-1]
    require(value == actual, "Getter and single-row value disagree")
    return Row(True, actual)


def parse_native(result: subprocess.CompletedProcess) -> tuple[bool, bool]:
    payload = result_bytes(result, DUMP_BYTES)
    require(not any(char in payload for char in (b"\r", b"\0", b"\x1b")), "Unsafe native observation bytes")
    text = payload.decode("utf-8").removesuffix("\n")
    rows = text.split("\n")
    require(rows[0] == PROCESS_HEADER and rows.count(PROCESS_HEADER) == 1, "Incomplete native process header")
    ready = [index for index, row in enumerate(rows) if "mProcessesReady" in row]
    footer = [index for index, row in enumerate(rows) if "mForceBackgroundCheck" in row]
    fields = [index for index, row in enumerate(rows) if "mAlwaysFinishActivities" in row]
    require(len(ready) == len(footer) == 1 and rows[ready[0]] == READINESS and
            footer[0] == len(rows) - 1 and ready[0] < footer[0] and
            re.fullmatch(r"  mForceBackgroundCheck=(true|false)", rows[footer[0]]) is not None,
            "Incomplete native readiness/footer branch")
    require(len(fields) <= 1 and (not fields or
            rows[fields[0]] == "  mAlwaysFinishActivities=true" and 0 < fields[0] < ready[0]),
            "Unknown native always-finish field")
    settings = re.search(r"(?<![A-Za-z0-9_.$])com\.android\.settings(?=$|[/:,\s}\]])", text) is not None
    return bool(fields), settings


def parse_settings_activity_absence(result: subprocess.CompletedProcess) -> None:
    """Require complete traversal emptiness, never a terminal sentinel alone."""
    payload = result_bytes(result, CONTROL_BYTES)
    require(not any(char in payload for char in (b"\r", b"\0", b"\x1b")), "Unsafe Settings activity bytes")
    rows = payload.decode("utf-8").removesuffix("\n").split("\n")
    require(len(rows) >= 3 and rows[0] == ACTIVITIES_HEADER and rows.count(ACTIVITIES_HEADER) == 1 and
            rows[-1] == "  (nothing)" and rows.count("  (nothing)") == 1,
            "Settings Activity absence header/footer is unproved")
    displays = set()
    for row_index, row in enumerate(rows[1:-1], 1):
        display = re.fullmatch(r"Display #(0|[1-9][0-9]{0,9}) \(activities from top to bottom\):", row)
        try:
            require(display is not None, "Settings Activity absence traversal is unproved")
        except ValueError as error:
            try:
                record_settings_activity_absence_refusal(error, payload, rows, row_index)
            except BaseException:
                pass  # Bounded observation must not replace the original refusing require.
            raise
        identifier = int(display[1])
        require(identifier <= 2147483647 and identifier not in displays,
                "Unknown or duplicate Settings Activity display traversal")
        displays.add(identifier)


def parse_recents(result: subprocess.CompletedProcess) -> None:
    payload = result_bytes(result, CONTROL_BYTES)
    require(not any(char in payload for char in (b"\r", b"\0", b"\x1b")), "Unsafe recents bytes")
    rows = payload.decode().removesuffix("\n").split("\n")
    require(len(rows) >= 5 and rows[0] == RECENTS_HEADER and rows.count(RECENTS_HEADER) == 1 and
            re.fullmatch(r"mRecentsUid=[0-9]+", rows[1]) is not None and
            re.fullmatch(r"mRecentsComponent=ComponentInfo\{[^{}]+}", rows[2]) is not None and
            re.fullmatch(r"mFreezeTaskListReordering=(true|false)", rows[3]) is not None and
            re.fullmatch(r"mFreezeTaskListReorderingPendingTimeout=(true|false)", rows[4]) is not None and
            rows[5:] in ([], ["  (nothing)"]), "Settings recent task absence is unproved")


def parse_live_tasks(result: subprocess.CompletedProcess) -> None:
    payload = result_bytes(result, CONTROL_BYTES)
    require(not any(char in payload for char in (b"\r", b"\0", b"\x1b")), "Unsafe live task bytes")
    rows = [row for row in payload.decode().split("\n") if row]
    starts = [index for index, row in enumerate(rows) if row.startswith("RootTask id=")]
    require(bool(starts) and starts[0] == 0, "Incomplete root task observation")
    bounds = r"\[-?[0-9]+,-?[0-9]+]\[-?[0-9]+,-?[0-9]+]"
    roots, children = set(), set()
    for number, start in enumerate(starts):
        block = rows[start:starts[number + 1] if number + 1 < len(starts) else len(rows)]
        root = re.fullmatch(r"RootTask id=([0-9]+) bounds=" + bounds + r" displayId=[0-9]+ userId=[0-9]+", block[0])
        require(root is not None and root[1] not in roots and len(block) >= 2 and
                block[1].startswith(" configuration={") and block[1].endswith("}"), "Incomplete root/configuration")
        roots.add(root[1])
        for row in block[2:]:
            child = re.fullmatch(r"  taskId=([0-9]+): ([^\s]+)(?: bounds=" + bounds +
                                r")? userId=[0-9]+ visible=(true|false)(?: topActivity=ComponentInfo\{([^{}]+)})?", row)
            require(child is not None and child[1] not in children and child[2] != "unknown", "Unknown live leaf task")
            children.add(child[1])
            require(not (child[2] == "com.android.settings" or child[2].startswith("com.android.settings/") or
                         (child[4] or "").startswith("com.android.settings/")), "Settings live task remains")


def parse_installed_path(result: subprocess.CompletedProcess) -> str | None:
    payload = result_bytes(result, CONTROL_BYTES, codes=(0, 1))
    if payload in (b"", b"\n"):
        return None
    require(result.returncode == 0, "Unknown package presence")
    match = re.fullmatch(rb"package:(/data/app/(?:[A-Za-z0-9_=+~.-]+/)+base\.apk)(?:\r?\n)?", payload)
    require(match is not None and b".." not in match[1], "Expected one exact unsplit installed APK")
    return match[1].decode()


def permission(result: subprocess.CompletedProcess) -> bool:
    return line(result, 512, rb"(?:0|-1)") == b"0"


def parse_properties(payload: bytes) -> dict[str, str]:
    require(0 < len(payload) <= CONTROL_BYTES and not any(char in payload for char in (b"\r", b"\0", b"\x1b")),
            "Unsafe owned AVD properties")
    pairs = []
    for row in payload.decode().splitlines():
        if not row or row.startswith("#"):
            continue
        require("=" in row, "Unknown owned AVD property row")
        key, value = row.split("=", 1)
        require(bool(key) and key == key.strip() and value == value.strip(), "Unknown owned AVD property shape")
        pairs.append((key, value))
    return unique(pairs)


class OwnedFreshGuest:
    """Exclusive parent/root FDs and actual child, with full confined teardown."""
    def __init__(self, root: Path, output: Path, name: str, environment: dict[str, str], *, child_probe=probe_child):
        require(re.fullmatch(r"nativecmpkit-api35-[a-f0-9]{12}", name) is not None and
                output.is_relative_to(root / "build/ci-verification") and output != root / "build/ci-verification",
                "Only a new exact camera guest output is admitted")
        require(environment.get("ANDROID_SERIAL") == SERIAL and
                environment.get("ANDROID_AVD_HOME") == str(output / "avd") and
                environment.get("ANDROID_EMULATOR_HOME") == str(output / "avd") and
                environment.get("ANDROID_USER_HOME") == str(output / "android-user"), "Private guest environment differs")
        self.root, self.output, self.name, self.environment = root, output, name, dict(environment)
        self.fd = open_directory(output)
        require(os.fstat(self.fd).st_uid == os.getuid(), "Fresh output is not owned by this controller UID")
        os.fchmod(self.fd, 0o700)
        self.parent_identity = identity(os.fstat(self.fd))
        self.roots, self.root_fds, self.avd_files = {}, {}, {}
        self.avd_identity = None
        self.process, self.pid, self.child_probe = None, None, child_probe
        self.launch_attempted = False
        self.disposal_attempted = False
        self.closed = False
        self.receipt = {"schema": "nativecmpkit.camera-fresh-guest.v1", "root_modes": "0700",
                        "launch_attempted": False, "roots_absent": False, "disposal_status": "not-started",
                        "errors": [], "raw_paths_environment_or_signing_material_exported": False}
        self.journal = Journal(self.fd, "camera-fresh-guest.json")
        self.journal.write(self.receipt)

    def verify_roots(self) -> None:
        check = open_directory(self.output)
        try:
            require(identity(os.fstat(check)) == self.parent_identity and
                    stat.S_IMODE(os.fstat(check).st_mode) == 0o700, "Fresh guest parent identity changed")
        finally:
            os.close(check)
        for name, original in self.roots.items():
            current = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            require(stat.S_ISDIR(current.st_mode) and identity(current) == original and
                    identity(os.fstat(self.root_fds[name])) == original and stat.S_IMODE(current.st_mode) == 0o700,
                    "Owned guest root was swapped or escaped")

    def create(self) -> None:
        require(not self.roots and not self.launch_attempted, "Fresh roots may only be created once")
        for name in ("avd", "android-user"):
            try:
                os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("A prior guest root exists")
            os.mkdir(name, 0o700, dir_fd=self.fd)
            descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.fd)
            self.root_fds[name] = descriptor
            self.roots[name] = identity(os.fstat(descriptor))
            self.receipt["created_roots"] = sorted(self.roots)
            self.journal.write(self.receipt)
        self.verify_roots()

    def capture_avd(self, home: Path) -> None:
        self.verify_roots()
        require(len(self.roots) == 2 and not self.launch_attempted and self.avd_identity is None,
                "Capture only the newly created pre-launch guest")
        directory = self.output / "avd" / (self.name + ".avd")
        descriptor = open_directory(directory)
        try:
            self.avd_identity = identity(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        definition = self.output / "avd" / (self.name + ".ini")
        config = directory / "config.ini"
        ini = parse_properties(file_bytes(definition, CONTROL_BYTES))
        # Capture the actual generated definition/config, not a guessed SDK
        # schema. Image/API/name admission is already the controller's fixed
        # create/launch argv plus actual boot/AVD readback. Do not demand an
        # encoding/target/AvdId/tag/abi row that has not been observed in config.
        require(ini.get("path") == str(directory), "Actual AVD definition is not the created owned directory")
        relative = ini.get("path.rel")
        require(relative is None or (not Path(relative).is_absolute() and ".." not in Path(relative).parts),
                "Alternative AVD definition path escapes the private Android roots")
        values = parse_properties(file_bytes(config, CONTROL_BYTES))
        image = home / "system-images/android-35/google_apis/x86_64"
        readonly_image = {"disk.dataPartition.initPath", "disk.systemPartition.initPath", "disk.vendorPartition.initPath",
                          "kernel.path", "ramdisk.path"}
        for key, value in values.items():
            if not value:
                continue  # Absent/default paths are not supplied external userdata.
            if key.startswith("image.sysdir."):
                reference = Path(value) if Path(value).is_absolute() else home / value
                require(reference == image and ".." not in reference.parts, "Image reference differs from fixed selected SDK input")
                continue
            if key in readonly_image:
                require(Path(value).is_absolute() and Path(value).is_relative_to(image) and ".." not in Path(value).parts,
                        "Readonly image input escaped the selected SDK image")
                continue
            if key == "skin.path" and value == "_no_skin":
                continue  # Non-path generated skin sentinel; not userdata.
            if key == "disk.dataPartition.path" and value == "<temp>":
                # Exact documented non-path default. The fixed -avd launch has
                # no -data/-datadir override; runtime selects userdata-qemu.img
                # in the captured AVD before creating the owned data/overlay.
                self.receipt["documented_data_partition_temp_default_observed"] = True
                continue
            path_field = ("path" in key.lower() or key.lower().endswith((".dir", ".file", ".filename")))
            if not path_field:
                continue
            # A supplied mutable path must be explicit and confined. No guessed
            # resolution of an unknown relative path or broad key whitelist.
            try:
                require(Path(value).is_absolute() and Path(value).is_relative_to(directory) and
                        ".." not in Path(value).parts, "Actual supplied mutable path confinement is unproved")
            except ValueError:
                try:
                    def observed_boolean(probe):
                        try:
                            observed = probe()
                        except (Exception, KeyboardInterrupt):
                            return None
                        return observed if type(observed) is bool else None

                    key_lower = key.lower()
                    self.receipt["mutable_path_refusal"] = {
                        "schema_version": 1,
                        "observation_phase": "after-refusal",
                        "key_is_skin_path": key == "skin.path",
                        "key_has_disk_prefix": key.startswith("disk."),
                        "key_has_hw_prefix": key.startswith("hw."),
                        "key_has_snapshot_prefix": key.startswith("snapshot."),
                        "key_contains_path": "path" in key_lower,
                        "key_ends_dir": key_lower.endswith(".dir"),
                        "key_ends_file": key_lower.endswith(".file"),
                        "key_ends_filename": key_lower.endswith(".filename"),
                        "is_absolute": observed_boolean(lambda: Path(value).is_absolute()),
                        "is_relative_to_owned_avd": observed_boolean(lambda: Path(value).is_relative_to(directory)),
                        "has_no_parent_component": observed_boolean(lambda: ".." not in Path(value).parts),
                        "native_success_inferred": False,
                    }
                    self.journal.write(self.receipt)
                except (Exception, KeyboardInterrupt):
                    pass  # Observation must never mask the original confinement refusal.
                raise
            descriptor = open_directory(Path(value).parent)
            os.close(descriptor)
            try:
                info = os.lstat(value)
            except FileNotFoundError:
                pass
            else:
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "Mutable guest path is shared/symlinked")
        self.avd_files = {path: file_digest(path, CONTROL_BYTES) for path in (definition, config)}
        self.receipt.update(avd_definition_sha256=self.avd_files[definition][0],
                            avd_config_sha256=self.avd_files[config][0], mutable_paths_confined=True)
        self.journal.write(self.receipt)

    def before_launch(self) -> None:
        self.verify_config()
        require(not self.launch_attempted, "Never retry an uncertain guest launch")
        self.launch_attempted = True
        self.receipt["launch_attempted"] = True
        self.journal.write(self.receipt)

    def attach(self, process: subprocess.Popen) -> None:
        require(self.launch_attempted and self.process is None, "A sole captured launch is required")
        self.process, self.pid = process, process.pid
        require(self.child_probe(process) is True, "Actual Popen child was not established")
        self.receipt["popen_child_session_established"] = True
        self.journal.write(self.receipt)

    def verify_config(self) -> None:
        self.verify_roots()
        require(self.avd_identity is not None and len(self.avd_files) == 2, "No created AVD identity")
        descriptor = open_directory(self.output / "avd" / (self.name + ".avd"))
        try:
            require(identity(os.fstat(descriptor)) == self.avd_identity, "Owned AVD directory identity changed")
        finally:
            os.close(descriptor)
        for path, original in self.avd_files.items():
            require(file_digest(path, CONTROL_BYTES) == original, "Owned AVD configuration changed")

    def verify_live(self) -> bool:
        self.verify_config()
        require(self.process is not None and self.process.pid == self.pid and self.child_probe(self.process) is True,
                "Same live owned Popen child/session required")
        return True

    def _remove_contents(self, descriptor: int, budget: list[int], depth=0) -> None:
        require(depth <= 32, "Guest disposal nesting exceeds its bound")
        with os.scandir(descriptor) as entries:
            names = []
            for entry in entries:
                budget[0] -= 1
                require(budget[0] >= 0, "Guest disposal inventory exceeds its bound")
                names.append(entry.name)
        for name in names:
            before = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISDIR(before.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=descriptor)
                try:
                    require(identity(os.fstat(child)) == identity(before), "Guest subtree swapped before opening")
                    self._remove_contents(child, budget, depth + 1)
                    require(identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)) == identity(before),
                            "Guest subtree swapped before removal")
                    os.rmdir(name, dir_fd=descriptor)
                finally:
                    os.close(child)
            else:
                # Unlink only this owned directory entry; never traverse a symlink target.
                require(identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)) == identity(before),
                        "Guest entry changed before removal")
                os.unlink(name, dir_fd=descriptor)

    def dispose(self, *, engine_exited: bool, transport_absent: bool, clean_shutdown: bool) -> dict:
        if self.disposal_attempted:
            return dict(self.receipt)  # No automatic deletion retry after partial disposal.
        self.disposal_attempted = True
        self.receipt["disposal_status"] = "running"
        try:
            self.journal.write(self.receipt)
            self.verify_roots()
            if self.launch_attempted:
                self.verify_config()  # Confinement must remain proved after the known engine exit.
                require(self.process is not None and self.process.pid == self.pid and
                        self.process.poll() is not None and engine_exited is True and transport_absent is True and
                        self.receipt.get("popen_child_session_established") is True,
                        "Unknown launch/engine/transport ownership; refuse guest deletion")
            self.receipt.update(engine_known_exited=not self.launch_attempted or engine_exited is True,
                                owned_transport_absent=not self.launch_attempted or transport_absent is True,
                                clean_shutdown=clean_shutdown is True)
            for name in ("avd", "android-user"):
                if name in self.roots:
                    require(identity(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) == self.roots[name],
                            "Owned disposal root identity changed")
                    self._remove_contents(self.root_fds[name], [32768])
                    require(identity(os.stat(name, dir_fd=self.fd, follow_symlinks=False)) == self.roots[name],
                            "Owned disposal root swapped before rmdir")
                    os.rmdir(name, dir_fd=self.fd)
                try:
                    os.stat(name, dir_fd=self.fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise ValueError("Exact ENOENT disposal proof unavailable")
            self.receipt.update(roots_absent=True, identity_confined_disposal=True, disposal_status="passed")
        except FAILURES as error:
            self.receipt["errors"].append({"phase": "disposal", "class": type(error).__name__})
            self.receipt["disposal_status"] = "failed"
        finally:
            try:
                self.journal.write(self.receipt)
            finally:
                for descriptor in self.root_fds.values():
                    os.close(descriptor)
                os.close(self.fd)
                self.closed = True
        return dict(self.receipt)


from android_camera_home_baseline import SettingsHomeTaskBaseline, parse_recent_home_baseline


@dataclass(frozen=True)
class Snapshot:
    master: Row
    scalar: Row
    native: bool
    boot: str
    settings_home: SettingsHomeTaskBaseline | None = None

    def pair(self) -> tuple[bool, Row]:
        return self.native, self.scalar


def pair_admitted(snapshot: Snapshot) -> bool:
    return snapshot.pair() in ((False, Row(False, None)), (False, Row(True, "0")), (True, Row(True, "1")))


class Unavailable(RuntimeError):
    """Only a proved owned offline/not-found transport, not an arbitrary error."""


class Reporter:
    def __init__(self, owner):
        self.owner, self.initial_absent, self.dispatch_attempted, self.remove_attempted = owner, False, False, False
        self.path, self.digest, self.apk_identity, self.metadata_identity = None, None, None, None

    def observe(self, package=REPORTER) -> str | None:
        require(package in (REPORTER, RECEIVER), "No arbitrary app inventory")
        path = parse_installed_path(self.owner.control("shell", "pm", "path", package))
        payload = result_bytes(self.owner.control("shell", "pm", "list", "packages", "--user", "0", "-U", package), CONTROL_BYTES)
        if path is None:
            require(payload in (b"", b"\n"), "Package path/list absence disagrees")
        else:
            match = re.fullmatch(rb"package:" + package.encode() + rb" uid:([0-9]+)(?:\r?\n)?", payload)
            require(match is not None and 10000 <= int(match[1]) <= 19999, "Reporter/helper user0 UID is unknown or shared")
        return path

    def capture_initial_absence(self) -> None:
        require(not self.initial_absent and not self.dispatch_attempted and not self.remove_attempted,
                "No initial package-absence recapture or installed reporter substitution")
        require(self.observe() is None and self.observe(RECEIVER) is None, "Prior test packages exist; never replace them")
        self.initial_absent = True
        self.owner.receipt.update(reporter_initial_absent=True, receiver_initial_absent=True)

    def freeze(self) -> None:
        require(self.observe() is None and self.observe(RECEIVER) is None, "Prior test packages exist; never replace them")
        self.initial_absent = True
        convention = file_bytes(self.owner.root / CONVENTION, CONTROL_BYTES)
        module = file_bytes(self.owner.root / MODULE / "build.gradle.kts", CONTROL_BYTES)
        from camera_ios_ownership_source_projection import current_source_before_camera_ios_ownership
        module = current_source_before_camera_ios_ownership(MODULE + "/build.gradle.kts", module)
        require(hashlib.sha256(convention).hexdigest() == CONVENTION_SHA256 and
                hashlib.sha256(module).hexdigest() == MODULE_SHA256,
                "Namespace-generating source changed; no classname package guess")
        base = self.owner.root / MODULE / "build/outputs/apk/androidTest"
        metadata = base / "output-metadata.json"
        self.metadata_identity = file_digest(metadata, CONTROL_BYTES)
        data = json.loads(file_bytes(metadata, CONTROL_BYTES), object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite APK metadata")))
        require(isinstance(data, dict) and isinstance(data.get("artifactType"), dict) and
                data["artifactType"].get("type") == "APK" and data.get("applicationId") == REPORTER and
                data.get("variantName") == "androidDeviceTest", "Wrong selected reporter metadata")
        elements = data.get("elements")
        require(isinstance(elements, list) and len(elements) == 1 and isinstance(elements[0], dict), "Reporter APK must be unsplit")
        row = elements[0]
        filename = row.get("outputFile")
        require(row.get("type") == "SINGLE" and row.get("filters") == [] and isinstance(filename, str) and
                re.fullmatch(r"[A-Za-z0-9_.-]+\.apk", filename) is not None and ".." not in filename,
                "Wrong bounded reporter APK filename")
        self.path = base / filename
        self.digest, self.apk_identity = file_digest(self.path, 256 * 1024**2)
        executable = self.owner.home / "cmdline-tools/23.0/bin/apkanalyzer"
        require(executable.is_file() and not executable.is_symlink() and os.access(executable, os.X_OK),
                "Installed official manifest analyzer is required")
        result = self.owner.run([str(executable), "manifest", "print", str(self.path)], 30, CONTROL_BYTES)
        payload = result_bytes(result, CONTROL_BYTES)
        require(not re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", payload, re.I), "Manifest DTD/entity is not admitted")
        try:
            manifest = ET.fromstring(payload)
        except ET.ParseError as error:
            raise ValueError("Compiled reporter manifest is not complete XML") from error
        require(manifest.tag == "manifest" and manifest.get("package") == REPORTER and
                manifest.get(ANDROID + "sharedUserId") is None and manifest.get(ANDROID + "sharedUserMaxSdkVersion") is None,
                "Compiled reporter namespace/shared UID differs")
        instrumentation = manifest.findall("instrumentation")
        require(len(instrumentation) == 1 and instrumentation[0].get(ANDROID + "name") == "androidx.test.runner.AndroidJUnitRunner" and
                instrumentation[0].get(ANDROID + "targetPackage") == REPORTER and len(manifest.findall("application")) == 1,
                "Compiled reporter instrumentation route differs")
        self.unchanged()
        self.owner.receipt.update(reporter_source_apk_sha256=self.digest, reporter_source_apk_bytes=self.apk_identity[2],
                                  reporter_namespace_source_sha256=CONVENTION_SHA256, reporter_initial_absent=True,
                                  receiver_initial_absent=True, reporter_compiled_manifest_sha256=hashlib.sha256(payload).hexdigest())

    def unchanged(self) -> None:
        require(self.path is not None and file_digest(self.path, 256 * 1024**2) == (self.digest, self.apk_identity) and
                file_digest(self.path.parent / "output-metadata.json", CONTROL_BYTES) == self.metadata_identity,
                "Frozen source APK/metadata changed; refuse managed install/uninstall")

    def cleanup(self) -> None:
        require(self.initial_absent, "No original reporter absence ownership")
        path = self.observe()
        if path is None:
            self.owner.receipt.update(reporter_removed=True, reporter_absence_observed=True,
                                      reporter_installed_bytes_verified=False)
            self.owner.publish()
            return
        require(self.dispatch_attempted and not self.remove_attempted, "No owned reporter install or cleanup retry")
        self.unchanged()
        digest = line(self.owner.control("shell", "sha256sum", path), CONTROL_BYTES,
                      rb"[a-f0-9]{64}  " + re.escape(path.encode())).decode().split("  ", 1)[0]
        require(digest == self.digest, "Installed reporter bytes are foreign; refuse uninstall and reboot")
        self.remove_attempted = True
        self.owner.receipt.update(reporter_installed_bytes_verified=True, reporter_uninstall_attempted=True)
        self.owner.publish()  # Own the single uninstall before uncertain IPC.
        try:
            reply = self.owner.control("uninstall", REPORTER, timeout=90)
            require(line(reply, CONTROL_BYTES, rb"Success") == b"Success", "Owned reporter uninstall was not successful")
        except FAILURES as error:
            self.owner.failure("reporter-uninstall", error)
        absent = self.observe() is None  # Read-only reconciliation, never an uninstall retry.
        self.owner.receipt.update(reporter_removed=absent, reporter_absence_observed=absent)
        require(absent, "Owned reporter removal is unverified")
        self.owner.publish()


class OwnedDeveloperPrerequisite:
    def __init__(self, root: Path, output: Path, home: Path, serial: str, guest: OwnedFreshGuest, *,
                 runner=bounded_run, clock=time.monotonic, sleep=time.sleep):
        require(serial == SERIAL and root == guest.root and output == guest.output and not guest.closed,
                "Only this controller's new guest may acquire the prerequisite")
        self.root, self.home, self.serial, self.guest = root, home, serial, guest
        self.runner, self.clock, self.sleep, self.deadline = runner, clock, sleep, None
        self.startup_deadline, self.startup_last_clock = None, None
        self.post_reporter_deadline, self.post_reporter_last_clock = None, None
        self._pre_reporter_capture_attempted, self._pre_reporter_capture_completed = False, False
        self._pre_reporter_original, self._pre_reporter_startup_home = None, None
        self._reporter_assembly_completed, self._post_reporter_started = False, False
        self.original, self.new_boot = None, None
        self.new_epoch_settings_home = None
        self.enable_attempted, self.enable_completed = False, False
        self.reboot_attempted, self.restore_attempted, self.closed = False, False, False
        self.receiver_prepare_attempted, self.receiver_cleanup = False, None
        self.receipt = {"schema": "nativecmpkit.camera-developer-prerequisite.v1", "focus": FOCUS, "api_level": 35,
                        "prepare_status": "not-started", "cleanup_status": "not-started", "errors": [],
                        "startup_readiness_status": "not-started", "startup_observations": 0,
                        "startup_ready_hold_verified": False, "startup_queries_read_only": True,
                        "startup_total_budget_seconds": 60.0, "startup_ready_hold_seconds": 0.5,
                        "startup_sleep_completion_bound_seconds": 1.0,
                        "master_enable_attempts": 0, "normal_reboot_attempts": 0, "master_restore_attempts": 0,
                        "reporter_dispatch_attempted": False, "reporter_removed": False, "receiver_removed": False,
                        "raw_boot_ids_dumps_paths_or_environment_exported": False, "native_acceptance_inferred": False}
        self.journal = Journal(guest.fd, "camera-developer-prerequisite.json")
        self.reporter = Reporter(self)
        self.publish()

    def publish(self) -> None:
        self.journal.write(self.receipt)

    def failure(self, phase: str, error: BaseException) -> None:
        self.receipt["errors"].append({"phase": phase, "class": type(error).__name__})
        try:
            self.receipt["errors"][-1]["require_call_origin"] = require_call_origin(error)
        except BaseException:
            pass  # Observation must never replace the already-recorded primary refusal.
        try:
            observation = settings_activity_absence_refusal(
                error, self.receipt["errors"][-1].get("require_call_origin"))
            if observation is not None:
                self.receipt["errors"][-1]["settings_activity_absence_refusal"] = observation
        except BaseException:
            pass  # Diagnostic unavailability never replaces the primary refusal or publication.
        try:
            observation = scalar_control_refusal(error, self.receipt["errors"][-1].get("require_call_origin"))
            if observation is not None:
                self.receipt["errors"][-1]["scalar_control_refusal"] = observation
        except BaseException:
            pass  # Scalar metadata is optional, bounded and never an admission or cleanup decision.
        self.publish()

    def run(self, argv: list[str], timeout: float, limit: int) -> subprocess.CompletedProcess:
        startup_started, post_reporter_started = None, None
        if self.post_reporter_deadline is not None:
            require(self.startup_deadline is None and self.deadline is None and
                    type(timeout) in (int, float) and 0 < timeout < float("inf"),
                    "Post-reporter commands cannot reuse initial startup or reboot budgets")
            timeout = min(timeout, 10.0, self.post_reporter_remaining())
            post_reporter_started = self.post_reporter_last_clock
        if self.startup_deadline is not None:
            require(type(timeout) in (int, float) and 0 < timeout < float("inf"),
                    "Initial startup command timeout is not finite and positive")
            timeout = min(timeout, 10.0, self.startup_remaining())
            startup_started = self.startup_last_clock
        if self.deadline is not None:
            timeout = min(timeout, self.deadline - self.clock())
            if timeout <= 0:
                raise TimeoutError("New-epoch observation exceeded its bound")
        result = self.runner(argv, cwd=self.root, timeout=timeout, limit=limit, environment=self.guest.environment)
        require(isinstance(result.stdout, bytes) and isinstance(result.stderr, bytes) and
                len(result.stdout) + len(result.stderr) <= limit, "Runner output is unbounded or not binary")
        if startup_started is not None:
            self.startup_remaining()
            if self.startup_last_clock - startup_started > timeout:
                raise TimeoutError("Initial startup command exceeded its clamped bound")
        if post_reporter_started is not None:
            self.post_reporter_remaining()
            if self.post_reporter_last_clock - post_reporter_started > timeout:
                raise TimeoutError("Post-reporter command exceeded its clamped bound")
        return result

    def control(self, *arguments: str, timeout=10, limit=CONTROL_BYTES, transient=False) -> subprocess.CompletedProcess:
        self.guest.verify_live()
        mutations = {
            ("shell", "settings", "--user", "0", "put", "global", MASTER, "1"),
            ("shell", "settings", "--user", "0", "put", "global", MASTER, "0"),
            ("shell", "settings", "--user", "0", "delete", "global", MASTER),
            ("uninstall", REPORTER), ("reboot",),
        }
        if arguments in mutations:
            # Re-establish the exact ready serial, AVD, actual shell UID and
            # expected kernel epoch immediately before each latched action.
            # Snapshot bracketing alone cannot protect this later IPC boundary.
            self.action_guard()
        result = self.run([str(self.home / "platform-tools/adb"), "-s", SERIAL, *arguments], timeout, limit)
        if transient and result.returncode != 0 and result.stdout == b"" and result.stderr in (
                b"error: device offline\n", b"error: device 'emulator-5588' not found\n", b"error: no devices/emulators found\n"):
            raise Unavailable("Owned reboot transport is not ready")
        try:
            if (scalar_query_identity(arguments) is not None and type(result) is subprocess.CompletedProcess and
                    type(result.args) is list and
                    result.args == [str(self.home / "platform-tools/adb"), "-s", SERIAL, *arguments]):
                result._nativecmpkit_scalar_query_context = (_SCALAR_QUERY_CONTEXT, result, arguments)
        except BaseException:
            pass  # This per-result observation cannot change the command, ownership or transient refusal.
        return result

    def action_guard(self) -> None:
        require(self.original is not None, "No exact original ownership for mutation")
        self.devices()
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD ownership changed before action")
        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                "Shell UID changed before action; never mutate as root")
        action_boot = self.boot_id()
        require(action_boot == (self.new_boot or self.original.boot), "Unrequested epoch before action")
        home = parse_recent_home_baseline(result_bytes(
            self.control("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"), CONTROL_BYTES))
        self.require_preserved_home(home, action_boot)
        require(self.boot_id() == action_boot, "Guest epoch changed around action-boundary HOME preservation")
        self.guest.verify_live()

    def devices(self, *, reboot=False) -> str:
        self.guest.verify_live()
        result = self.run([str(self.home / "platform-tools/adb"), "devices"], 10, CONTROL_BYTES)
        payload = result_bytes(result, CONTROL_BYTES)
        require(not any(char in payload for char in (b"\r", b"\0", b"\x1b")), "Unknown device table bytes")
        rows = payload.decode().splitlines()
        while rows and not rows[-1]:
            rows.pop()
        require(rows and rows[0] == "List of devices attached" and len(rows) <= 2 and
                (len(rows) == 1 or rows[1] in (SERIAL + "\tdevice", SERIAL + "\toffline")), "Foreign/unknown device table")
        state = "absent" if len(rows) == 1 else rows[1].split("\t")[1]
        require(reboot or state == "device", "Owned ready transport is unproved")
        return state

    def boot_id(self) -> str:
        value = line(self.control("shell", "cat", "/proc/sys/kernel/random/boot_id", transient=self.deadline is not None),
                     512, rb"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}").decode()
        require(value != "00000000-0000-0000-0000-000000000000", "Unproved kernel boot identity")
        return value

    def state_row(self, key: str) -> Row:
        return parse_row(self.control("shell", "settings", "--user", "0", "get", "global", key),
                         self.control("shell", "content", "query", "--user", "0", "--uri",
                                      "content://settings/global/" + key, "--projection", "name:value"), key)

    def require_preserved_home(self, home: SettingsHomeTaskBaseline | None, boot: str) -> None:
        """Exact same-epoch data preservation; parsing never grants task ownership."""
        if self.original is None:
            require(self.new_boot is None and not self.reboot_attempted, "No uncaptured epoch substitution")
        elif boot == self.original.boot:
            require(self.new_boot is None and home == self.original.settings_home,
                    "Original same-epoch HOME baseline changed, appeared, disappeared or was replaced")
        elif self.new_boot is not None:
            require(boot == self.new_boot and home == self.new_epoch_settings_home,
                    "Accepted new-epoch HOME baseline changed or was substituted")
        else:
            # Only wait_new_epoch, after the sole owned NORMAL reboot request,
            # may observe a first new baseline. stable still requires TWO exact
            # snapshots before close stores that new epoch and baseline together.
            require(self.reboot_attempted and self.deadline is not None and
                    self.enable_attempted and boot != self.original.boot,
                    "No unrequested kernel epoch or HOME baseline substitution")

    def snapshot(self, *, fresh: bool) -> Snapshot:
        self.devices()
        before_boot = self.boot_id()
        values = (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"), ("sys.boot_completed", b"1"))
        for key, expected in values:
            require(line(self.control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                    "New guest runtime does not match API35/x86_64/completed boot")
        require(line(self.control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing", "Non-enforcing guest refused")
        master, scalar = self.state_row(MASTER), self.state_row(SCALAR)
        native, settings = parse_native(self.control("shell", "dumpsys", "activity", "processes", limit=DUMP_BYTES))
        if fresh:
            # A cached process/package token is not a live Settings Activity.
            # The all-Activity reader also rejects nested/stopping/finishing rows.
            parse_settings_activity_absence(self.control("shell", "dumpsys", "activity", "-p",
                                                        "com.android.settings", "activities"))
        require(self.state_row(SCALAR) == scalar and self.state_row(MASTER) == master, "State changed around native read")
        settings_home = parse_recent_home_baseline(result_bytes(
            self.control("shell", "dumpsys", "activity", "-p", "com.android.settings", "recents"), CONTROL_BYTES))
        self.require_preserved_home(settings_home, before_boot)
        parse_live_tasks(self.control("shell", "am", "stack", "list"))
        require(self.boot_id() == before_boot, "Guest rebooted during state observation")
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD name changed")
        self.devices()
        return Snapshot(master, scalar, native, before_boot, settings_home)

    def stable(self, *, fresh: bool) -> Snapshot:
        first, second = self.snapshot(fresh=fresh), self.snapshot(fresh=fresh)
        require(first == second, "State/boot changed across complete snapshots")
        return second

    def startup_remaining(self) -> float:
        """Separate finite initial-phase budget; never the reboot deadline."""
        now = self.clock()
        require(type(now) in (int, float) and float("-inf") < now < float("inf") and
                type(self.startup_deadline) in (int, float) and
                float("-inf") < self.startup_deadline < float("inf") and
                type(self.startup_last_clock) in (int, float) and now >= self.startup_last_clock,
                "Initial startup clock is non-finite or moved backwards")
        self.startup_last_clock = now
        remaining = self.startup_deadline - now
        if remaining <= 0:
            raise TimeoutError("Initial startup observation exceeded its total bound")
        return remaining

    def startup_scalar(self, *arguments: str) -> str:
        """One complete ASCII scalar from a bounded read-only startup query."""
        payload = result_bytes(self.control(*arguments, timeout=10, limit=512), 512)
        require(type(payload) is bytes and re.fullmatch(rb"[ -~]+(?:\n)?", payload) is not None,
                "Unknown initial startup scalar bytes")
        return payload.removesuffix(b"\n").decode("ascii")

    def startup_observation(self, expected_boot: str) -> tuple[bool, str | None]:
        """Typed readiness opportunity only; not Settings Activity absence."""
        self.startup_remaining()
        self.guest.verify_live()
        self.devices()
        require(self.boot_id() == expected_boot, "Kernel epoch changed during initial startup")
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD ownership changed during initial startup")
        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                "Initial startup requires the actual non-root shell UID2000")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                              ("sys.boot_completed", b"1")):
            require(line(self.control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                    "Initial startup runtime is not API35/x86_64/completed boot")
        require(line(self.control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing",
                "Initial startup requires an Enforcing guest")
        require(self.startup_scalar("shell", "am", "get-current-user") == "0",
                "Current user changed during initial startup")
        state = self.startup_scalar("shell", "am", "get-started-user-state", "0")
        require(state in ("BOOTING", "RUNNING_LOCKED", "RUNNING_UNLOCKING", "RUNNING_UNLOCKED"),
                "Unknown or terminal initial startup user0 state")
        home = self.startup_scalar("shell", "cmd", "package", "resolve-activity", "--components",
                                   "--query-flags", "0", "--user", "0", "-a", "android.intent.action.MAIN",
                                   "-c", "android.intent.category.HOME")
        if home in ("No activity found", "com.android.settings/.FallbackHome"):
            component = None
        else:
            match = re.fullmatch(
                r"([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*)/"
                r"(\.[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*|"
                r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+)", home)
            require(match is not None, "Unknown initial startup HOME component shape")
            package, activity = match.groups()
            require(package not in ("android", "com.android.settings") and "." in package and
                    not activity.startswith(package + "."),
                    "Initial startup HOME is excluded or not canonically flattened")
            component = home
        # Recheck the complete fixed identity after typed reads, not just at entry.
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD ownership changed during initial startup")
        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                "Initial startup requires the actual non-root shell UID2000")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                              ("sys.boot_completed", b"1")):
            require(line(self.control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                    "Initial startup runtime is not API35/x86_64/completed boot")
        require(line(self.control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing",
                "Initial startup requires an Enforcing guest")
        require(self.startup_scalar("shell", "am", "get-current-user") == "0",
                "Current user changed during initial startup")
        require(self.boot_id() == expected_boot, "Kernel epoch changed during initial startup")
        self.devices()
        self.guest.verify_live()
        self.startup_remaining()
        return state == "RUNNING_UNLOCKED" and component is not None, component

    def wait_startup_readiness(self) -> tuple[str, str]:
        """Finite60s policy,0.5s cadence/hold; neither is an Android guarantee."""
        require(self.startup_deadline is None and self.deadline is None and self.original is None and
                self.receipt["startup_readiness_status"] == "not-started",
                "No initial startup readiness retry or reboot-budget reuse")
        self.receipt["startup_readiness_status"] = "running"
        started = self.clock()
        require(type(started) in (int, float) and float("-inf") < started < float("inf"),
                "Initial startup clock is not finite")
        self.startup_deadline, self.startup_last_clock = started + 60.0, started
        self.startup_remaining()
        self.publish()
        self.devices()
        expected_boot = self.boot_id()  # self.deadline stays None: transient=False.
        held_home, held_since = None, None
        while True:
            ready, home = self.startup_observation(expected_boot)
            observed_at = self.startup_last_clock
            self.receipt["startup_observations"] += 1
            self.publish()
            if ready:
                if home == held_home and held_since is not None:
                    if observed_at - held_since >= 0.5:
                        self.receipt["startup_ready_hold_verified"] = True
                        return expected_boot, home
                else:
                    held_home, held_since = home, observed_at
            else:
                held_home, held_since = None, None
            remaining = self.startup_remaining()
            duration, completion_bound = min(0.5, remaining), min(1.0, remaining)
            before_sleep = self.startup_last_clock
            self.sleep(duration)
            self.startup_remaining()
            elapsed = self.startup_last_clock - before_sleep
            require(elapsed >= duration, "Initial startup sleep returned before its requested hold")
            if elapsed > completion_bound:
                raise TimeoutError("Initial startup sleep exceeded its clamped completion bound")

    def prepare(self) -> dict:
        if vars(self).get("_pre_reporter_capture_attempted") is True:
            return self.complete_after_reporter()
        require(self.receipt["prepare_status"] == "not-started", "No prerequisite acquisition retry")
        self.receipt["prepare_status"] = "running"
        try:
            self.publish()
            self.devices()
            require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000", "Actual shell UID2000 required; no root")
            for name in ("DUMP", "ACCESS_CONTENT_PROVIDERS_EXTERNALLY"):
                require(permission(self.control("shell", "dumpsys", "package", "check-permission",
                                                "android.permission." + name, "com.android.shell", "0")), "Read permission not granted")
            self.reporter.freeze()
            try:
                startup_boot, startup_home = self.wait_startup_readiness()
                original = self.stable(fresh=True)
                require(pair_admitted(original), "Original native/scalar pair is inconsistent")
                require(original.boot == startup_boot, "Kernel epoch changed before original startup capture")
                ready, home = self.startup_observation(startup_boot)
                require(ready and home == startup_home, "Typed startup readiness changed before original capture")
                self.startup_remaining()  # Includes both complete snapshots, parsing and pair admission.
                self.receipt["startup_readiness_status"] = "passed"
                self.startup_remaining()  # Last admission check, after status; no call before original assignment.
                self.original = original
            finally:
                if self.original is None:
                    self.receipt["startup_readiness_status"] = "failed"
                self.startup_deadline, self.startup_last_clock = None, None
            self.receipt.update(original_master=original.master.safe(), original_scalar=original.scalar.safe(),
                                original_native=original.native, original_boot_id_sha256=hashlib.sha256(original.boot.encode()).hexdigest())
            self.publish()
            if original.master != Row(True, "1"):
                require(permission(self.control("shell", "dumpsys", "package", "check-permission",
                                                "android.permission.WRITE_SECURE_SETTINGS", "com.android.shell", "0")), "Write permission not granted")
                self.enable_attempted = True
                self.receipt["master_enable_attempts"] = 1
                self.publish()  # Before the sole possible PUT1.
                require(result_bytes(self.control("shell", "settings", "--user", "0", "put", "global", MASTER, "1"),
                                     CONTROL_BYTES) in (b"", b"\n"), "Master initialization reply was not empty success")
                current = self.stable(fresh=True)
                require(current.master == Row(True, "1") and current.pair() == original.pair() and current.boot == original.boot,
                        "Master1 initialization/native pair/original epoch unverified")
                self.enable_completed = True
            self.receipt.update(prepare_status="passed", master1_observed=True,
                                master_initialization_completed=self.enable_completed, master_was_already1=not self.enable_attempted)
            self.publish()
        except FAILURES as error:
            self.receipt["prepare_status"] = "failed"
            self.failure("prepare", error)
            raise
        return dict(self.receipt)

    def capture_before_reporter(self) -> dict:
        """Sole owned C1 read-only capture; neither APK compilation nor preparation success."""
        require(self.receipt["prepare_status"] == "not-started" and not self._pre_reporter_capture_attempted and
                self.original is None and not self.closed,
                "No pre-reporter prerequisite capture retry or original-state replacement")
        self._pre_reporter_capture_attempted = True
        self.receipt.update(prepare_status="running", reporter_compile_preflight_status="running",
                            reporter_compile_preflight_read_only=True, reporter_assembly_recorded_passed=False,
                            post_reporter_revalidation_status="not-started", post_reporter_revalidation_attempts=0,
                            post_reporter_revalidation_budget_seconds=120.0)
        try:
            self.publish()
            self.devices()
            require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000", "Actual shell UID2000 required; no root")
            for name in ("DUMP", "ACCESS_CONTENT_PROVIDERS_EXTERNALLY"):
                require(permission(self.control("shell", "dumpsys", "package", "check-permission",
                                                "android.permission." + name, "com.android.shell", "0")), "Read permission not granted")
            self.reporter.capture_initial_absence()
            try:
                startup_boot, startup_home = self.wait_startup_readiness()
                original = self.stable(fresh=True)
                require(pair_admitted(original), "Original native/scalar pair is inconsistent")
                require(original.boot == startup_boot, "Kernel epoch changed before original startup capture")
                ready, home = self.startup_observation(startup_boot)
                require(ready and home == startup_home, "Typed startup readiness changed before original capture")
                self.startup_remaining()  # Includes both complete snapshots, parsing and pair admission.
                self.receipt["startup_readiness_status"] = "passed"
                self.startup_remaining()  # Last admission check, after status; no call before original assignment.
                self.original = original
            finally:
                if self.original is None:
                    self.receipt["startup_readiness_status"] = "failed"
                self.startup_deadline, self.startup_last_clock = None, None
            self.receipt.update(original_master=original.master.safe(), original_scalar=original.scalar.safe(),
                                original_native=original.native, original_boot_id_sha256=hashlib.sha256(original.boot.encode()).hexdigest())
            self.publish()
            self._pre_reporter_original, self._pre_reporter_startup_home = self.original, startup_home
            self._pre_reporter_capture_completed = True
            self.receipt["reporter_compile_preflight_status"] = "passed"
            self.publish()
        except FAILURES as error:
            self.receipt.update(prepare_status="failed", reporter_compile_preflight_status="failed")
            self.failure("prepare", error)
            raise
        return dict(self.receipt)

    def record_reporter_assembly_success(self, execution: dict) -> None:
        require(self._pre_reporter_capture_completed and not self._reporter_assembly_completed and
                not self._post_reporter_started and self.receipt["prepare_status"] == "running" and
                self.original is self._pre_reporter_original and self.original is not None and not self.closed,
                "Only this captured C1 may record the sole reporter assembly")
        require(execution["exit_code"] == 0 and not execution.get("stop_reason"),
                "Reporter assembly did not pass the unchanged exit/stop guard")
        self._reporter_assembly_completed = True
        self.receipt["reporter_assembly_recorded_passed"] = True
        self.publish()

    def record_reporter_assembly_failure(self, error: BaseException) -> None:
        require(self._pre_reporter_capture_completed and not self._post_reporter_started and
                self.receipt["prepare_status"] == "running" and not self.closed,
                "Only the captured C1 may record its reporter assembly refusal")
        self.receipt["prepare_status"] = "failed"
        self.failure("reporter-assembly", error)

    def post_reporter_remaining(self) -> float:
        """One finite bracketing pass, not the initial60s or new-epoch deadline."""
        now = self.clock()
        require(type(now) in (int, float) and float("-inf") < now < float("inf") and
                type(self.post_reporter_deadline) in (int, float) and
                float("-inf") < self.post_reporter_deadline < float("inf") and
                type(self.post_reporter_last_clock) in (int, float) and now >= self.post_reporter_last_clock,
                "Post-reporter clock is non-finite or moved backwards")
        self.post_reporter_last_clock = now
        remaining = self.post_reporter_deadline - now
        if remaining <= 0:
            raise TimeoutError("Post-reporter revalidation exceeded its total one-shot bound")
        return remaining

    def post_reporter_observation(self, expected_boot: str) -> tuple[bool, str | None]:
        """Typed readiness opportunity only; not Settings Activity absence."""
        self.post_reporter_remaining()
        self.guest.verify_live()
        self.devices()
        require(self.boot_id() == expected_boot, "Kernel epoch changed during initial startup")
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD ownership changed during initial startup")
        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                "Initial startup requires the actual non-root shell UID2000")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                              ("sys.boot_completed", b"1")):
            require(line(self.control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                    "Initial startup runtime is not API35/x86_64/completed boot")
        require(line(self.control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing",
                "Initial startup requires an Enforcing guest")
        require(self.startup_scalar("shell", "am", "get-current-user") == "0",
                "Current user changed during initial startup")
        state = self.startup_scalar("shell", "am", "get-started-user-state", "0")
        require(state in ("BOOTING", "RUNNING_LOCKED", "RUNNING_UNLOCKING", "RUNNING_UNLOCKED"),
                "Unknown or terminal initial startup user0 state")
        home = self.startup_scalar("shell", "cmd", "package", "resolve-activity", "--components",
                                   "--query-flags", "0", "--user", "0", "-a", "android.intent.action.MAIN",
                                   "-c", "android.intent.category.HOME")
        if home in ("No activity found", "com.android.settings/.FallbackHome"):
            component = None
        else:
            match = re.fullmatch(
                r"([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*)/"
                r"(\.[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*|"
                r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+)", home)
            require(match is not None, "Unknown initial startup HOME component shape")
            package, activity = match.groups()
            require(package not in ("android", "com.android.settings") and "." in package and
                    not activity.startswith(package + "."),
                    "Initial startup HOME is excluded or not canonically flattened")
            component = home
        # Recheck the complete fixed identity after typed reads, not just at entry.
        require(owned_avd_console_name(self.control("emu", "avd", "name"), self.guest.name)
                == self.guest.name.encode(),
                "Actual AVD ownership changed during initial startup")
        require(line(self.control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                "Initial startup requires the actual non-root shell UID2000")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                              ("sys.boot_completed", b"1")):
            require(line(self.control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                    "Initial startup runtime is not API35/x86_64/completed boot")
        require(line(self.control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing",
                "Initial startup requires an Enforcing guest")
        require(self.startup_scalar("shell", "am", "get-current-user") == "0",
                "Current user changed during initial startup")
        require(self.boot_id() == expected_boot, "Kernel epoch changed during initial startup")
        self.devices()
        self.guest.verify_live()
        self.post_reporter_remaining()
        return state == "RUNNING_UNLOCKED" and component is not None, component

    def complete_after_reporter(self) -> dict:
        """Freeze compiled identity and revalidate the same capture before original master initialization."""
        require(self._pre_reporter_capture_completed and self._reporter_assembly_completed and
                not self._post_reporter_started and self.receipt["prepare_status"] == "running" and
                self.original is self._pre_reporter_original and self.original is not None and not self.closed and
                self.startup_deadline is None and self.startup_last_clock is None and self.deadline is None,
                "Only the sole compiled C1 may complete its unchanged original capture once")
        self._post_reporter_started = True
        try:
            self.reporter.freeze()  # Exact compiled APK/metadata/manifest/source identity, not a precompile guess.
            self.receipt.update(post_reporter_revalidation_status="running", post_reporter_revalidation_attempts=1)
            started = self.clock()
            require(type(started) in (int, float) and float("-inf") < started < float("inf"),
                    "Post-reporter clock is not finite")
            self.post_reporter_deadline, self.post_reporter_last_clock = started + 120.0, started
            post_reporter_completed = False
            try:
                self.post_reporter_remaining()
                self.publish()
                self.guest.verify_live()  # The unchanged live guard includes all captured FD/config identities.
                for name in ("DUMP", "ACCESS_CONTENT_PROVIDERS_EXTERNALLY"):
                    require(permission(self.control("shell", "dumpsys", "package", "check-permission",
                                                    "android.permission." + name, "com.android.shell", "0")), "Read permission not granted")
                ready, home = self.post_reporter_observation(self.original.boot)
                require(ready and home == self._pre_reporter_startup_home,
                        "Typed startup identity changed while the reporter compiled")
                current = self.stable(fresh=True)
                require(self.original is self._pre_reporter_original and current == self._pre_reporter_original,
                        "Exact original master/native/scalar/epoch changed while the reporter compiled")
                ready, home = self.post_reporter_observation(self.original.boot)
                require(ready and home == self._pre_reporter_startup_home,
                        "Typed startup identity changed across post-reporter original-state revalidation")
                self.reporter.unchanged()
                self.post_reporter_remaining()
                self.receipt["post_reporter_revalidation_status"] = "passed"
                self.post_reporter_remaining()
                post_reporter_completed = True
            finally:
                if not post_reporter_completed:
                    self.receipt["post_reporter_revalidation_status"] = "failed"
                self.post_reporter_deadline, self.post_reporter_last_clock = None, None
            original = self.original  # Never replace it with a postcompile snapshot.
            if original.master != Row(True, "1"):
                require(permission(self.control("shell", "dumpsys", "package", "check-permission",
                                                "android.permission.WRITE_SECURE_SETTINGS", "com.android.shell", "0")), "Write permission not granted")
                self.enable_attempted = True
                self.receipt["master_enable_attempts"] = 1
                self.publish()  # Before the sole possible PUT1.
                require(result_bytes(self.control("shell", "settings", "--user", "0", "put", "global", MASTER, "1"),
                                     CONTROL_BYTES) in (b"", b"\n"), "Master initialization reply was not empty success")
                current = self.stable(fresh=True)
                require(current.master == Row(True, "1") and current.pair() == original.pair() and current.boot == original.boot,
                        "Master1 initialization/native pair/original epoch unverified")
                self.enable_completed = True
            self.receipt.update(prepare_status="passed", master1_observed=True,
                                master_initialization_completed=self.enable_completed, master_was_already1=not self.enable_attempted)
            self.publish()
        except FAILURES as error:
            self.receipt["prepare_status"] = "failed"
            if self.receipt["post_reporter_revalidation_status"] != "passed":
                self.receipt["post_reporter_revalidation_status"] = "failed"
            self.failure("prepare", error)
            raise
        return dict(self.receipt)

    def mark_receiver_prepare(self) -> None:
        require(self.receipt["prepare_status"] == "passed" and not self.receiver_prepare_attempted,
                "Only the unchanged owned receiver preparation may follow acquisition")
        self.receiver_prepare_attempted = True
        self.receipt["receiver_prepare_attempted"] = True
        self.publish()

    def record_receiver_cleanup(self, receipt: dict | None) -> None:
        require(self.receiver_cleanup is None, "Record the sole receiver cleanup once")
        if self.receiver_prepare_attempted:
            require(isinstance(receipt, dict) and receipt.get("package") == RECEIVER,
                    "Exact acquired receiver cleanup receipt required")
            self.receiver_cleanup = {"removed": receipt.get("owned_recipient_removed") is True,
                                     "status": receipt.get("cleanup_status"), "error": bool(receipt.get("cleanup_error"))}
        else:
            self.receiver_cleanup = {"removed": self.receipt.get("receiver_initial_absent") is True,
                                     "status": "not-installed", "error": False}
        self.publish()

    def mark_reporter_dispatch(self) -> None:
        require(self.receipt["prepare_status"] == "passed" and self.receiver_prepare_attempted and
                not self.reporter.dispatch_attempted, "No unprepared or repeated reporter dispatch")
        self.reporter.unchanged()
        current = self.stable(fresh=False)
        require(current.master == Row(True, "1") and current.pair() == self.original.pair() and current.boot == self.original.boot,
                "Master/native/epoch changed before the managed install")
        self.reporter.dispatch_attempted = True
        self.receipt["reporter_dispatch_attempted"] = True
        self.publish()  # Before lt.run can install the frozen reporter.

    def wait_new_epoch(self) -> Snapshot:
        require(self.reboot_attempted and self.original is not None, "No unrequested epoch substitution")
        self.deadline = self.clock() + 360
        try:
            while self.clock() < self.deadline:
                state = self.devices(reboot=True)
                if state == "device":
                    try:
                        completed = line(self.control("shell", "getprop", "sys.boot_completed", transient=True), 512, rb"(?:0|1)")
                        candidate = self.boot_id() if completed == b"1" else self.original.boot
                        if candidate != self.original.boot:
                            current = self.stable(fresh=True)
                            require(current.boot == candidate, "Unstable new kernel identity")
                            return current
                    except Unavailable:
                        pass  # Read-only owned-offline reconciliation, never another reboot.
                remaining = self.deadline - self.clock()
                if remaining <= 0:
                    break
                self.sleep(min(0.25, remaining))
            raise TimeoutError("Same/unknown kernel lifetime after the sole normal reboot")
        finally:
            self.deadline = None

    def close(self) -> dict:
        if self.closed:
            return dict(self.receipt)  # Sticky failures; no cleanup action retry.
        self.closed = True
        start_errors = len(self.receipt["errors"])
        self.receipt["cleanup_status"] = "running"
        try:
            self.publish()
            if self.original is not None:
                self.action_guard()  # Refuse an unrequested epoch before app cleanup, too.
            self.reporter.cleanup()
            require(self.receiver_cleanup is not None and self.receiver_cleanup["removed"] is True and
                    self.reporter.observe(RECEIVER) is None, "Owned receiver cleanup/absence unproved")
            self.receipt["receiver_removed"] = True
            if self.receiver_cleanup["error"] or self.receiver_cleanup["status"] == "failed":
                self.failure("receiver-cleanup", ValueError("Prior receiver cleanup failed"))
            require(self.original is not None, "Original exact state was not acquired")
            current = self.stable(fresh=False)
            require(current.boot == self.original.boot, "Unrequested guest epoch changed before planned cleanup")
            permitted = (Row(True, "1"),) if self.enable_completed else (self.original.master, Row(True, "1"))
            require(current.master in permitted, "Foreign master state; refuse any restoring write")
            restored = current.pair() == self.original.pair()
            self.receipt["pre_barrier_native_scalar_restored"] = restored
            self.publish()
            if not restored:
                self.failure("pre-barrier-native-scalar", ValueError("Native cleanup mismatch; never compensate"))
            if self.enable_attempted:
                require(not self.reboot_attempted, "Never retry a normal reboot")
                self.reboot_attempted = True
                self.receipt["normal_reboot_attempts"] = 1
                self.publish()
                try:
                    reply = self.control("reboot", timeout=20)  # No reboot mode/argument.
                    require(result_bytes(reply, CONTROL_BYTES) in (b"", b"\n"), "Normal reboot reply is unknown")
                    self.receipt["normal_reboot_request_error_free"] = True
                    self.publish()
                except FAILURES as error:
                    self.failure("normal-reboot-request", error)
                current = self.wait_new_epoch()
                self.new_boot = current.boot
                self.new_epoch_settings_home = current.settings_home
                self.receipt.update(kernel_barrier_verified=True, new_boot_id_sha256=hashlib.sha256(current.boot.encode()).hexdigest(),
                                    new_boot_epoch_changed=True, same_popen_avd_userdata_verified=True)
                self.publish()
                require(self.reporter.observe() is None and self.reporter.observe(RECEIVER) is None,
                        "Test package reappeared after reboot; no uninstall retry or master write")
                require(current.master in permitted, "Unknown new-epoch master; refuse restoration")
                if current.master != self.original.master:
                    require(current.master == Row(True, "1") and not self.restore_attempted, "Restore only this owned1 row once")
                    self.restore_attempted = True
                    self.receipt["master_restore_attempts"] = 1
                    self.publish()
                    try:
                        if self.original.master.present:
                            reply = self.control("shell", "settings", "--user", "0", "put", "global", MASTER, "0")
                            require(result_bytes(reply, CONTROL_BYTES) in (b"", b"\n"), "Master0 restoration reply unknown")
                        else:
                            reply = self.control("shell", "settings", "--user", "0", "delete", "global", MASTER)
                            require(line(reply, CONTROL_BYTES, rb"Deleted 1 rows") == b"Deleted 1 rows", "Deletion count is not exactly1")
                    except FAILURES as error:
                        self.failure("master-restore-request", error)
                current = self.stable(fresh=True)
                require(current.boot == self.new_boot, "Guest epoch changed during master restoration")
            self.receipt["master_original_restored"] = current.master == self.original.master
            self.receipt["final_native_scalar_restored"] = current.pair() == self.original.pair()
            require(self.receipt["master_original_restored"] is True and self.receipt["final_native_scalar_restored"] is True,
                    "Exact original master presence/value/native/scalar restoration failed")
            self.publish()
        except FAILURES as error:
            self.failure("cleanup", error)
        self.receipt["cleanup_status"] = "passed" if len(self.receipt["errors"]) == start_errors else "failed"
        self.publish()
        return dict(self.receipt)


def accepted(receipt: dict, disposal: dict) -> bool:
    if not (isinstance(receipt, dict) and isinstance(disposal, dict) and
            receipt.get("schema") == "nativecmpkit.camera-developer-prerequisite.v1" and
            receipt.get("focus") == FOCUS and type(receipt.get("api_level")) is int and receipt["api_level"] == 35 and
            receipt.get("prepare_status") == receipt.get("cleanup_status") == "passed" and receipt.get("errors") == [] and
            all(receipt.get(key) is True for key in ("master1_observed", "reporter_dispatch_attempted", "reporter_removed", "receiver_removed",
                "pre_barrier_native_scalar_restored", "master_original_restored", "final_native_scalar_restored")) and
            disposal.get("schema") == "nativecmpkit.camera-fresh-guest.v1" and disposal.get("disposal_status") == "passed" and
            disposal.get("errors") == [] and all(disposal.get(key) is True for key in
                ("roots_absent", "identity_confined_disposal", "engine_known_exited", "owned_transport_absent", "clean_shutdown"))):
        return False
    if receipt.get("master_enable_attempts") == 1:
        return (receipt.get("normal_reboot_attempts") == 1 and
                receipt.get("master_restore_attempts") == 1 and all(receipt.get(key) is True for key in
                ("master_initialization_completed", "kernel_barrier_verified", "normal_reboot_request_error_free",
                 "new_boot_epoch_changed", "same_popen_avd_userdata_verified")))
    return (receipt.get("master_was_already1") is True and receipt.get("master_enable_attempts") == 0 and
            receipt.get("normal_reboot_attempts") == 0 and receipt.get("master_restore_attempts") == 0)


def require_call_origin(error: BaseException) -> dict:
    """Bounded failure-only owning callsite; no error text, locals or paths."""
    unavailable = {"source": "unavailable", "symbol": "unavailable", "line": 0}
    if type(error) is not ValueError:
        return unavailable
    previous, node = None, error.__traceback__
    for _ in range(64):
        if node is None:
            return unavailable
        if node.tb_frame.f_code is require.__code__:
            if previous is None or node.tb_next is not None:
                return unavailable
            caller = previous.tb_frame.f_code
            symbol, number = caller.co_name, previous.tb_lineno
            if (caller.co_filename != require.__code__.co_filename or
                    re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", symbol) is None or not 0 < number < 20000):
                return unavailable
            functions = (globals().get(symbol), *(vars(owner).get(symbol) for owner in
                         (Journal, OwnedFreshGuest, Reporter, OwnedDeveloperPrerequisite)))
            if not any(getattr(function, "__code__", None) is caller for function in functions):
                return unavailable
            if not any(start <= previous.tb_lasti < stop and line == number
                       for start, stop, line in caller.co_lines()):
                return unavailable
            return {"source": "android_camera_developer_prerequisite.py", "symbol": symbol, "line": number}
        previous, node = node, node.tb_next
    return unavailable



def record_settings_activity_absence_refusal(error: BaseException, payload: bytes,
                                           rows: list[str], row_index: int) -> None:
    """Attach bounded facts only after the unchanged display-row require refuses."""
    if (type(error) is not ValueError or type(payload) is not bytes or
            not 0 < len(payload) <= CONTROL_BYTES or type(rows) is not list or
            not 3 <= len(rows) <= len(payload) + 1 or type(row_index) is not int or
            not 1 <= row_index <= len(rows) - 2 or
            any(type(row) is not str for row in rows) or
            sum(len(row) for row in rows) > CONTROL_BYTES):
        return
    row = rows[row_index]
    encoded = row.encode("utf-8")
    if len(encoded) > len(payload):
        return
    interior = rows[1:-1]
    display_rows = sum(re.fullmatch(r"Display #(0|[1-9][0-9]{0,9}) \(activities from top to bottom\):", item)
                       is not None for item in interior)
    blank_rows = sum(item.strip(" \t") == "" for item in interior)
    marker_rows = sum("ActivityRecord{" in item for item in interior)
    # Reference syntax only: never identify an actual-image producer, row owner or
    # Activity absence from a fixed prefix. Unknown rows remain original refusals.
    fixed_shape = {
        "  Resumed activities in task display areas (from top to bottom):": "literal-resumed-areas-header",
        "  Activities waiting to finish:": "literal-waiting-to-finish-header",
        "  Activities waiting to stop:": "literal-waiting-to-stop-header",
    }.get(row)
    if fixed_shape is None:
        fixed_shape = ("ascii-even-indent-star-space-prefix" if
                       re.match(r"(?: {2})+\* ", row) is not None else
                       "ascii-top-resumed-prefix" if row.startswith("  ResumedActivity: ") else "unknown")
    # No row text, package/task/PID, argv, environment, error body or machine path.
    error._nativecmpkit_settings_activity_absence_refusal = {
        "schema": "nativecmpkit.camera-settings-activity-absence-refusal.v2",
        "payload_bytes": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "row_count": len(rows), "interior_row_count": len(rows) - 2,
        "interior_display_shape_rows": display_rows, "interior_ascii_blank_shape_rows": blank_rows,
        "interior_other_shape_rows": len(interior) - display_rows - blank_rows,
        "interior_activity_record_marker_rows": marker_rows,
        "rejected_row_index": row_index, "row_bytes": len(encoded),
        "row_sha256": hashlib.sha256(encoded).hexdigest(),
        "row_leading_ascii_spaces": len(row) - len(row.lstrip(" ")),
        "row_trailing_ascii_spaces": len(row) - len(row.rstrip(" ")),
        "row_empty": row == "", "row_ascii_whitespace_only": row.strip(" \t") == "",
        "row_ascii_only": row.isascii(), "row_contains_tab": "\t" in row,
        "row_display_prefix": row.startswith("Display #"),
        "row_indented_display_prefix": row.startswith(" ") and row.lstrip(" ").startswith("Display #"),
        "row_activity_record_marker": "ActivityRecord{" in row,
        "row_reference_fixed_shape": fixed_shape,
    }


def settings_activity_absence_refusal(error: BaseException, origin: dict | None) -> dict | None:
    """Allowlist optional metadata; never an Activity-absence or cleanup decision."""
    if (type(error) is not ValueError or type(origin) is not dict or
            any(type(key) is not str for key in origin) or
            set(origin) != {"source", "symbol", "line"} or
            origin["source"] != "android_camera_developer_prerequisite.py" or
            origin["symbol"] != "parse_settings_activity_absence" or
            type(origin["line"]) is not int or not 0 < origin["line"] < 20000):
        return None
    observation = vars(error).get("_nativecmpkit_settings_activity_absence_refusal")
    integers = ("payload_bytes", "row_count", "interior_row_count", "rejected_row_index",
                "row_bytes", "row_leading_ascii_spaces", "row_trailing_ascii_spaces",
                "interior_display_shape_rows", "interior_ascii_blank_shape_rows",
                "interior_other_shape_rows", "interior_activity_record_marker_rows")
    booleans = ("row_empty", "row_ascii_whitespace_only", "row_ascii_only", "row_contains_tab",
                "row_display_prefix", "row_indented_display_prefix", "row_activity_record_marker")
    digests = ("payload_sha256", "row_sha256")
    keys = {"schema", "row_reference_fixed_shape", *integers, *booleans, *digests}
    if (type(observation) is not dict or any(type(key) is not str for key in observation) or
            set(observation) != keys or
            observation["schema"] != "nativecmpkit.camera-settings-activity-absence-refusal.v2" or
            type(observation["row_reference_fixed_shape"]) is not str or
            observation["row_reference_fixed_shape"] not in {
                "literal-resumed-areas-header", "literal-waiting-to-finish-header",
                "literal-waiting-to-stop-header", "ascii-even-indent-star-space-prefix",
                "ascii-top-resumed-prefix", "unknown"} or
            any(type(observation[key]) is not int for key in integers) or
            any(type(observation[key]) is not bool for key in booleans) or
            any(type(observation[key]) is not str or
                re.fullmatch(r"[a-f0-9]{64}", observation[key]) is None for key in digests)):
        return None
    size, count = observation["payload_bytes"], observation["row_count"]
    if (not 0 < size <= CONTROL_BYTES or not 3 <= count <= size + 1 or
            observation["interior_row_count"] != count - 2 or
            any(not 0 <= observation[key] <= count - 2 for key in
                ("interior_display_shape_rows", "interior_ascii_blank_shape_rows", "interior_other_shape_rows")) or
            observation["interior_display_shape_rows"] + observation["interior_ascii_blank_shape_rows"] +
            observation["interior_other_shape_rows"] != count - 2 or
            not 0 <= observation["interior_activity_record_marker_rows"] <= observation["interior_other_shape_rows"] or
            not 1 <= observation["rejected_row_index"] <= count - 2 or
            not 0 <= observation["row_bytes"] <= size or
            not 0 <= observation["row_leading_ascii_spaces"] <= observation["row_bytes"] or
            not 0 <= observation["row_trailing_ascii_spaces"] <= observation["row_bytes"] or
            observation["row_empty"] != (observation["row_bytes"] == 0)):
        return None
    return dict(observation)



_SCALAR_QUERY_CONTEXT = object()  # Immutable per-module provenance marker; no global observation registry.


def scalar_query_identity(arguments: tuple[str, ...]) -> tuple[str, str | None] | None:
    """Exact fixed owner command identity only. Never publish argv, paths, values or result bodies."""
    if type(arguments) is not tuple or any(type(part) is not str for part in arguments):
        return None
    fixed = {
        ("emu", "avd", "name"): ("owned-avd-name", None),
        ("shell", "id", "-u"): ("shell-uid", None),
        ("shell", "cat", "/proc/sys/kernel/random/boot_id"): ("kernel-boot-id", None),
        ("shell", "getprop", "ro.build.version.sdk"): ("runtime-sdk", None),
        ("shell", "getprop", "ro.product.cpu.abi"): ("runtime-abi", None),
        ("shell", "getprop", "sys.boot_completed"): ("runtime-boot-completed", None),
        ("shell", "getenforce"): ("selinux-enforcement", None),
        ("shell", "dumpsys", "package", "check-permission", "android.permission.DUMP", "com.android.shell", "0"):
            ("shell-dump-permission-user0", None),
        ("shell", "dumpsys", "package", "check-permission", "android.permission.ACCESS_CONTENT_PROVIDERS_EXTERNALLY", "com.android.shell", "0"):
            ("shell-content-permission-user0", None),
        ("shell", "dumpsys", "package", "check-permission", "android.permission.WRITE_SECURE_SETTINGS", "com.android.shell", "0"):
            ("shell-write-permission-user0", None),
        ("shell", "settings", "--user", "0", "delete", "global", MASTER): ("global-master-delete-user0", MASTER),
        ("uninstall", REPORTER): ("owned-reporter-uninstall", None),
    }
    if arguments in fixed:
        return fixed[arguments]
    for key in (MASTER, SCALAR):
        if arguments == ("shell", "settings", "--user", "0", "get", "global", key):
            return "global-settings-get-user0", key
        if arguments == ("shell", "content", "query", "--user", "0", "--uri",
                         "content://settings/global/" + key, "--projection", "name:value"):
            return "global-settings-single-row-user0", key
    return None


def scalar_result_query_identity(error: BaseException, result: subprocess.CompletedProcess,
                                 query_identity) -> tuple[str, str | None] | None:
    """Prove a parse_row input position or the exact owner-requested result; never guess another getter."""
    if query_identity is not None:
        if (type(query_identity) is not tuple or len(query_identity) != 2 or
                type(query_identity[0]) is not str or type(query_identity[1]) is not str or
                query_identity[0] not in ("global-settings-get-user0", "global-settings-single-row-user0") or
                query_identity[1] not in (MASTER, SCALAR)):
            return None
        node = error.__traceback__
        for _ in range(64):
            if node is None:
                return None
            if node.tb_frame.f_code is line.__code__:
                name = "getter" if query_identity[0] == "global-settings-get-user0" else "query"
                caller = node.tb_frame.f_back
                values = caller.f_locals if caller is not None and caller.f_code is parse_row.__code__ else {}
                if (type(values.get("key")) is str and values["key"] == query_identity[1] and
                        values.get(name) is result and node.tb_frame.f_locals.get("result") is result):
                    return query_identity
                return None
            node = node.tb_next
        return None
    context = vars(result).get("_nativecmpkit_scalar_query_context")
    if (type(context) is not tuple or len(context) != 3 or context[0] is not _SCALAR_QUERY_CONTEXT or
            context[1] is not result or type(result.args) is not list or len(result.args) < 4 or
            any(type(part) is not str for part in result.args) or result.args[1:3] != ["-s", SERIAL] or
            tuple(result.args[3:]) != context[2]):
        return None
    return scalar_query_identity(context[2])


def scalar_control_refusal_observation(error: BaseException, result: subprocess.CompletedProcess,
                                       payload: bytes, cap: int, pattern: bytes, query_identity) -> dict | None:
    """Bounded fingerprints/byte shapes only, strictly after the original shape require refused."""
    if (type(error) is not ValueError or error.args != ("Unknown scalar control shape",) or
            type(result) is not subprocess.CompletedProcess or type(payload) is not bytes or
            type(cap) is not int or not 0 < cap <= CONTROL_BYTES or not 0 <= len(payload) <= cap or
            type(pattern) is not bytes or not 0 < len(pattern) <= CONTROL_BYTES or
            type(result.stdout) is not bytes or result.stdout is not payload or
            type(result.stderr) is not bytes or result.stderr != b"" or result.returncode != 0):
        return None
    identity = scalar_result_query_identity(error, result, query_identity)
    if identity is None:
        return None
    return {
        "schema": "nativecmpkit.camera-scalar-control-refusal.v1",
        "query": identity[0], "setting_key": identity[1], "cap_bytes": cap,
        "payload_bytes": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "pattern_bytes": len(pattern), "pattern_sha256": hashlib.sha256(pattern).hexdigest(),
        "ascii_only": all(value <= 127 for value in payload),
        "printable_ascii_or_line_endings_only": all(32 <= value <= 126 or value in (10, 13) for value in payload),
        "lf_bytes": payload.count(b"\n"), "cr_bytes": payload.count(b"\r"),
        "nul_bytes": payload.count(b"\0"), "escape_bytes": payload.count(b"\x1b"),
        "tab_bytes": payload.count(b"\t"), "space_bytes": payload.count(b" "),
        "leading_ascii_spaces": len(payload) - len(payload.lstrip(b" ")),
        "trailing_ascii_spaces": len(payload) - len(payload.rstrip(b" ")),
        "terminal_lf": payload.endswith(b"\n"), "terminal_crlf": payload.endswith(b"\r\n"),
        "empty": not payload,
    }


def record_scalar_control_refusal(error: BaseException, result: subprocess.CompletedProcess,
                                  payload: bytes, cap: int, pattern: bytes, query_identity) -> None:
    observation = scalar_control_refusal_observation(error, result, payload, cap, pattern, query_identity)
    if observation is not None:
        error._nativecmpkit_scalar_control_refusal = observation
        error._nativecmpkit_scalar_control_refusal_identity = error


def scalar_control_refusal(error: BaseException, origin: dict | None) -> dict | None:
    """Validate/copy optional facts against the actual live line traceback; never decide admission or cleanup."""
    if (type(error) is not ValueError or error.args != ("Unknown scalar control shape",) or
            vars(error).get("_nativecmpkit_scalar_control_refusal_identity") is not error or
            type(origin) is not dict or any(type(key) is not str for key in origin) or
            set(origin) != {"source", "symbol", "line"} or
            origin["source"] != "android_camera_developer_prerequisite.py" or origin["symbol"] != "line" or
            type(origin["line"]) is not int or not 0 < origin["line"] < 20000 or
            origin != require_call_origin(error)):
        return None
    observation = vars(error).get("_nativecmpkit_scalar_control_refusal")
    integers = ("cap_bytes", "payload_bytes", "pattern_bytes", "lf_bytes", "cr_bytes", "nul_bytes",
                "escape_bytes", "tab_bytes", "space_bytes", "leading_ascii_spaces", "trailing_ascii_spaces")
    booleans = ("ascii_only", "printable_ascii_or_line_endings_only", "terminal_lf", "terminal_crlf", "empty")
    digests = ("payload_sha256", "pattern_sha256")
    if (type(observation) is not dict or any(type(key) is not str for key in observation) or
            set(observation) != {"schema", "query", "setting_key", *integers, *booleans, *digests} or
            observation["schema"] != "nativecmpkit.camera-scalar-control-refusal.v1" or
            type(observation["query"]) is not str or
            (observation["setting_key"] is not None and type(observation["setting_key"]) is not str) or
            any(type(observation[key]) is not int for key in integers) or
            any(type(observation[key]) is not bool for key in booleans) or
            any(type(observation[key]) is not str or re.fullmatch(r"[a-f0-9]{64}", observation[key]) is None for key in digests) or
            not 0 < observation["cap_bytes"] <= CONTROL_BYTES or
            not 0 <= observation["payload_bytes"] <= observation["cap_bytes"] or
            not 0 < observation["pattern_bytes"] <= CONTROL_BYTES or
            any(not 0 <= observation[key] <= observation["payload_bytes"] for key in integers[3:])):
        return None
    node = error.__traceback__
    for _ in range(64):
        if node is None:
            return None
        if node.tb_frame.f_code is line.__code__:
            values = node.tb_frame.f_locals
            expected = scalar_control_refusal_observation(error, values.get("result"), values.get("payload"),
                values.get("cap"), values.get("pattern"), values.get("query_identity"))
            return dict(observation) if expected is not None and observation == expected else None
        node = node.tb_next
    return None


def owned_avd_console_name(result: subprocess.CompletedProcess, expected_name: str) -> bytes:
    """Exact owned console name/OK framing only; never a general scalar normalization."""
    require(type(expected_name) is str and
            re.fullmatch(r"nativecmpkit-api35-[a-f0-9]{12}", expected_name) is not None,
            "Unknown owned AVD name contract")
    name = expected_name.encode("ascii")
    payload = result_bytes(result, 512)
    require(payload in (name + b"\nOK\n", name + b"\r\nOK\r\n"),
            "Unknown owned AVD console-name frame")
    return name
