# SPDX-License-Identifier: Apache-2.0
"""Finite owned geometry simulator lifecycle; never a native/readiness waiver.

Create one predetermined same-type/runtime device BEFORE any boot attempt.
Never retry a failed boot, erase/rename a preinstalled device or guess a cleanup
target. The workflow still recaptures clean Git/toolchain/SDK/Booted identity.
Command deadlines are cooperative; this is not an OS or hostile-runner sandbox.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import time

import runtime_context as runtime

ROOT = Path(__file__).resolve().parents[2]
FOCUSES = {"ui-native-popover-portrait-traits": "iphone", "ui-native-popover-os-rotation": "ipad"}
SELECTION = "build/ci-runtime/selection.json"
LEASE = "build/ci-runtime/geometry-simulator.json"
CLEANUP_CLAIM = "build/ci-runtime/geometry-simulator-cleanup-claim.json"
MAX_BYTES = 2 * 1024 * 1024
STATES = {"Shutdown", "Booted", "Booting", "Shutting Down", "Creating"}
SUCCESS_STATUS = 4294967295
XCRUN = "/usr/bin/xcrun"
BUDGETS = {"list-devices": 180, "list-runtimes": 180, "create": 60,
           "boot": 60, "bootstatus": 180, "shutdown": 60, "delete": 60}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate simulator record fields are forbidden")
        result[key] = value
    return result


def _json(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Ordinary bounded simulator JSON bytes are required")
    return json.loads(raw, object_pairs_hook=_unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite simulator JSON is forbidden")))


def _path(root, relative):
    root = root.absolute()
    path = root / relative
    if root != root.resolve() or path.absolute() != path.resolve():
        raise ValueError("Aliased simulator receipt paths are forbidden")
    return path


def _read(root, relative):
    path = _path(root, relative)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_BYTES:
        raise ValueError("One ordinary bounded simulator receipt is required")
    raw = path.read_bytes()
    after = path.lstat()
    if any(getattr(before, key) != getattr(after, key) for key in
           ("st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime_ns")):
        raise ValueError("Simulator receipt changed during its read")
    return _json(raw)


def _write(root, document, *, exclusive=False):
    path = _path(root, LEASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    _path(root, LEASE)
    if path.exists():
        if exclusive:
            raise ValueError("An earlier simulator lease must never be overwritten")
        _read(root, LEASE)
    raw = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    if len(raw) > MAX_BYTES:
        raise ValueError("Simulator lease exceeded its bounded record budget")
    if exclusive:
        # The target itself, not a temporary pathname, arbitrates first ownership.
        # Two simultaneous initial writers must never replace each other's lease.
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return
    temporary = path.with_name(path.name + ".tmp")
    # Never follow or overwrite someone else's temporary/receipt file.
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _claim_cleanup(root, record):
    """Atomically claim disposal; an interrupted cleanup must never be replayed.

    The lease's in-memory command list alone cannot arbitrate concurrent cleanup
    processes. A target-file O_EXCL claim covers both processes before any SDK
    command. It is custody, not a hostile-filesystem or OS-sandbox attestation.
    """
    path = _path(root, CLEANUP_CLAIM)
    raw = (json.dumps({"scope": record["scope"], "owned_udid": record["owned_udid"],
        "cleanup_claimed": True, "native_acceptance": False}, sort_keys=True) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def ci_scope(focus):
    if type(focus) is not str or focus not in FOCUSES:
        raise ValueError("Only the two exact geometry focuses are authorized")
    if (platform.system() != "Darwin" or platform.machine().lower() not in {"arm64", "aarch64"} or
            os.environ.get("GITHUB_ACTIONS") != "true" or
            os.environ.get("GITHUB_REPOSITORY") != "Apdelrahman1911/nativeCmpkit" or
            os.environ.get("GITHUB_REF") != "refs/heads/development/preview-hardening" or
            os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise ValueError("Owned geometry simulator requires its explicit read-only Apple CI scope")
    sha = os.environ.get("GITHUB_SHA", "")
    run = os.environ.get("GITHUB_RUN_ID", "")
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    if (not re.fullmatch(r"[0-9a-f]{40}", sha) or not re.fullmatch(r"[1-9][0-9]{0,19}", run) or
            not re.fullmatch(r"[1-9][0-9]{0,3}", attempt)):
        raise ValueError("Exact CI source/run/attempt identity is required")
    return {"source_sha": sha, "run_id": int(run), "run_attempt": int(attempt),
            "focus": focus, "kind": FOCUSES[focus]}


def inventory_snapshot(devices, runtimes):
    """Bounded identity/state and name hashes, never user names or private paths."""
    if type(devices) is not dict or type(devices.get("devices")) is not dict or type(runtimes) is not dict:
        raise ValueError("Exact simulator inventory objects are required")
    records = {}
    for identifier, rows in devices["devices"].items():
        if (type(identifier) is not str or len(identifier) > 180 or
                not re.fullmatch(r"com\.apple\.CoreSimulator\.SimRuntime\.[A-Za-z0-9.-]+", identifier) or
                type(rows) is not list or len(rows) > 1024):
            raise ValueError("Bounded public simulator inventory roles are required")
        for row in rows:
            if type(row) is not dict:
                raise ValueError("Ordinary simulator inventory rows are required")
            udid, name, device_type = (row.get(key) for key in ("udid", "name", "deviceTypeIdentifier"))
            if (type(udid) is not str or not runtime.UUID.fullmatch(udid) or udid.upper() in records or
                    type(name) is not str or len(name.encode()) > 4096 or
                    type(device_type) is not str or not re.fullmatch(
                        r"com\.apple\.CoreSimulator\.SimDeviceType\.[A-Za-z0-9.-]+", device_type) or
                    row.get("state") not in STATES or type(row.get("isAvailable")) is not bool):
                raise ValueError("Unambiguous simulator identities/states are required")
            records[udid.upper()] = {"runtime_identifier": identifier, "device_type": device_type,
                "state": row["state"], "available": row["isAvailable"],
                "name_sha256": hashlib.sha256(name.encode()).hexdigest()}
            if len(records) > 1024:
                raise ValueError("Simulator inventory exceeded its finite device budget")
    runtime_rows = runtimes.get("runtimes")
    if type(runtime_rows) is not list or len(runtime_rows) > 128:
        raise ValueError("Bounded runtime inventory is required")
    identities = {}
    for row in runtime_rows:
        if type(row) is not dict:
            raise ValueError("Ordinary runtime inventory rows are required")
        identifier = row.get("identifier")
        if (type(identifier) is not str or not re.fullmatch(
                r"com\.apple\.CoreSimulator\.SimRuntime\.[A-Za-z0-9.-]+", identifier) or identifier in identities or
                type(row.get("isAvailable")) is not bool or type(row.get("version")) is not str or
                type(row.get("buildversion")) is not str):
            raise ValueError("Unambiguous actual runtime identities are required")
        runtime.sdk_version(row["version"])
        if not re.fullmatch(r"[0-9A-Za-z]{1,64}", row["buildversion"]):
            raise ValueError("Exact runtime build identity is required")
        identities[identifier] = {"version": row["version"], "build": row["buildversion"],
                                  "available": row["isAvailable"]}
    return {"devices": records, "runtimes": identities}


def boot_terminal(raw, udid, owner_name):
    """A successful command exit/Finished word alone is not boot/readiness proof."""
    if (type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES or type(udid) is not str or
            not runtime.UUID.fullmatch(udid) or type(owner_name) is not str or not re.fullmatch(
                r"nativecmpkit-geometry-[1-9][0-9]{0,19}-[1-9][0-9]{0,3}-(iphone|ipad)", owner_name)):
        raise ValueError("Exact bounded bootstatus input and selected UUID are required")
    lines = [line.strip() for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not lines or len(lines) > 4096 or any(len(line.encode()) > 4096 for line in lines):
        raise ValueError("Bounded complete bootstatus lines are required")
    if lines[0] != f"Monitoring boot status for {owner_name} ({udid}).":
        raise ValueError("Bootstatus does not identify the predetermined owned simulator")
    if lines[1:] == ["Device already booted, skipping."]:
        return {"successful": True, "shape": "already-booted", "terminal_status": None,
                "data_migration_failed": False, "readiness_verified": False}
    terminal = []
    for index, line in enumerate(lines[1:], 1):
        if "isTerminal=YES" not in line:
            continue
        match = re.fullmatch(r"\[[0-9-]{10} [0-9:]{8} [+-][0-9]{4}\] Status=([0-9]{1,10}), "
                             r"isTerminal=YES, Elapsed=[0-9]{2,4}:[0-9]{2}\.", line)
        if not match:
            raise ValueError("Malformed terminal bootstatus cannot be admitted")
        terminal.append((index, int(match.group(1))))
    if len(terminal) != 1 or terminal[0][0] != len(lines) - 2:
        raise ValueError("Exactly one complete final bootstatus terminal is required")
    migration_failed = "Data Migration Failed" in lines
    successful = terminal[0][1] == SUCCESS_STATUS and lines[-1] == "Finished" and not migration_failed
    return {"successful": successful, "shape": "terminal", "terminal_status": terminal[0][1],
            "data_migration_failed": migration_failed, "readiness_verified": False}


def execute(arguments, timeout):
    return subprocess.run(arguments, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False, timeout=timeout)


class OwnedGeometrySimulator:
    def __init__(self, root, focus):
        self.root = root
        self.scope = ci_scope(focus)
        self.name = f"nativecmpkit-geometry-{self.scope['run_id']}-{self.scope['run_attempt']}-{self.scope['kind']}"
        self.record = None
        self.last_owned_state = None
        self.cleaning = False

    def persist(self, *, exclusive=False):
        _write(self.root, self.record, exclusive=exclusive)

    def command(self, kind, arguments):
        if type(kind) is not str or kind not in BUDGETS or type(arguments) is not tuple:
            raise ValueError("Only exact finite simulator commands are allowed")
        commands = self.record.get("commands")
        if type(commands) is not list or len(commands) >= 32 or any(type(row) is not dict for row in commands):
            raise ValueError("Finite ordinary command custody is required")
        if kind.startswith("list-"):
            expected = (XCRUN, "simctl", "list", kind.removeprefix("list-"), "--json")
        elif kind == "create":
            source = self.record["source_simulator"]
            expected = (XCRUN, "simctl", "create", self.name, source["device_type"], source["runtime_identifier"])
            if (self.record.get("creation_requested") is not True or self.record.get("creation_returned") is not False or
                    self.record.get("owned_udid") is not None or self.cleaning):
                raise ValueError("Only one acknowledged creation intent is allowed")
        else:
            udid = self.record.get("owned_udid")
            if (self.record.get("creation_returned") is not True or type(udid) is not str or
                    not runtime.UUID.fullmatch(udid) or udid in self.record["baseline"]["devices"]):
                raise ValueError("Mutation requires the exact acknowledged nonbaseline UUID")
            expected = (XCRUN, "simctl", kind, udid) + (("-b",) if kind == "bootstatus" else ())
            if ((kind == "boot" and (self.cleaning or self.last_owned_state != "Shutdown")) or
                    (kind == "bootstatus" and (self.cleaning or not any(
                        row.get("command") == "boot" and row.get("completed") is True and row.get("exit_code") == 0
                        for row in commands))) or
                    (kind == "shutdown" and (not self.cleaning or self.last_owned_state not in {"Booted", "Booting"})) or
                    (kind == "delete" and (not self.cleaning or self.last_owned_state != "Shutdown"))):
                raise ValueError("Simulator mutation is outside its acknowledged lifecycle phase")
        if arguments != expected or (not kind.startswith("list-") and any(row.get("command") == kind for row in commands)):
            raise ValueError("Unexpected command or repeated simulator mutation is forbidden")
        event = {"command": kind, "timeout_seconds": BUDGETS[kind], "exit_code": None,
                 "timed_out": False, "completed": False}
        self.record["commands"].append(event)
        self.record["phase"] = kind
        self.persist()
        started = time.monotonic()
        try:
            result = execute(tuple(arguments), BUDGETS[kind])
        except subprocess.TimeoutExpired:
            event.update(timed_out=True, elapsed_seconds=time.monotonic() - started)
            self.persist()
            raise
        event["elapsed_seconds"] = time.monotonic() - started
        if (type(result) is not subprocess.CompletedProcess or type(result.returncode) is not int or
                type(result.stdout) is not bytes or type(result.stderr) is not bytes or
                len(result.stdout) + len(result.stderr) > MAX_BYTES):
            raise ValueError("Ordinary bounded actual simulator command result is required")
        event.update(exit_code=result.returncode, completed=True,
            stdout_bytes=len(result.stdout), stderr_bytes=len(result.stderr),
            stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
        self.persist()
        if result.returncode != 0:
            raise RuntimeError("Owned simulator command returned nonzero; no retry or fallback")
        return result

    def inventory(self):
        documents = []
        for kind in ("devices", "runtimes"):
            result = self.command("list-" + kind, (XCRUN, "simctl", "list", kind, "--json"))
            if result.stderr:
                raise ValueError("Inventory stderr is not an admitted JSON replacement")
            documents.append(_json(result.stdout))
        return documents, inventory_snapshot(*documents)

    def owned(self, documents, snapshot):
        udid = self.record["owned_udid"]
        source = self.record["source_simulator"]
        selected = runtime.simulator(*documents, kind=self.scope["kind"], udid=udid)
        if (selected["udid"].upper() != udid or any(selected[key] != source[key] for key in
                ("device_type", "runtime_identifier", "runtime_version", "runtime_build")) or
                snapshot["devices"][udid]["name_sha256"] != hashlib.sha256(self.name.encode()).hexdigest()):
            raise ValueError("Created simulator is not the exact owned same-type/runtime device")
        self.last_owned_state = selected["state"]
        return selected

    def preserved(self, snapshot):
        current = {key: row for key, row in snapshot["devices"].items() if key != self.record["owned_udid"]}
        return current == self.record["baseline"]["devices"] and snapshot["runtimes"] == self.record["baseline"]["runtimes"]

    def prepare(self):
        selection = _read(self.root, SELECTION)
        if (type(selection) is not dict or type(selection.get("schema_version")) is not int or
                selection["schema_version"] != 1 or selection.get("source_revision") != self.scope["source_sha"] or
                selection.get("source_tree_dirty") is not False or
                selection.get("host", {}).get("system") != "Darwin" or
                selection.get("host", {}).get("architecture") != "arm64" or
                type(selection.get("java", {}).get("major")) is not int or selection["java"]["major"] != 17):
            raise ValueError("Actual clean preboot CI source/Apple/JDK identity is required")
        source = selection.get("simulator")
        if type(source) is not dict or source.get("state") not in {"Shutdown", "Booted"}:
            raise ValueError("One exact recorded source simulator is required")
        self.record = {"schema_version": 1, "scope": self.scope, "source_simulator": source,
            "owner_name_sha256": hashlib.sha256(self.name.encode()).hexdigest(), "baseline": None,
            "creation_requested": False, "creation_returned": False, "owned_udid": None,
            "prepared": False, "boot_terminal": None, "commands": [], "phase": "intent",
            "primary_failure": None, "cleanup": None, "library_native_methods_executed": 0,
            "library_readiness_verified": False, "release_readiness_certified": False, "packages_published": False}
        self.persist(exclusive=True)
        try:
            documents, snapshot = self.inventory()
            selected = runtime.simulator(*documents, kind=self.scope["kind"], udid=source.get("udid"))
            if selected != source or any(row["name_sha256"] == self.record["owner_name_sha256"] for row in snapshot["devices"].values()):
                raise ValueError("Preinstalled identity changed or the owned name is not exclusive")
            self.record["baseline"] = snapshot
            self.record["creation_requested"] = True
            self.persist()
            created = self.command("create", (XCRUN, "simctl", "create", self.name,
                source["device_type"], source["runtime_identifier"]))
            raw = created.stdout.decode("ascii")
            udid = raw.removesuffix("\n")
            if (created.stderr or not runtime.UUID.fullmatch(udid) or raw not in {udid, udid + "\n"} or
                    udid.upper() in snapshot["devices"]):
                raise ValueError("Creation must return one new nonbaseline UUID; never guess ownership")
            self.record.update(owned_udid=udid.upper(), creation_returned=True)
            self.persist()  # Custody before the next external command.
            documents, snapshot = self.inventory()
            if self.owned(documents, snapshot)["state"] != "Shutdown" or not self.preserved(snapshot):
                raise ValueError("New shutdown identity and untouched preinstalled baseline are required")
            self.command("boot", (XCRUN, "simctl", "boot", self.record["owned_udid"]))
            status = self.command("bootstatus", (XCRUN, "simctl", "bootstatus", self.record["owned_udid"], "-b"))
            self.record["boot_terminal"] = boot_terminal(status.stdout + status.stderr, self.record["owned_udid"], self.name)
            self.persist()
            if self.record["boot_terminal"]["successful"] is not True:
                raise ValueError("Terminal simulator boot failed despite command exit zero")
            documents, snapshot = self.inventory()
            if self.owned(documents, snapshot)["state"] != "Booted" or not self.preserved(snapshot):
                raise ValueError("Actual owned Booted state and original baseline must both hold")
            self.record.update(prepared=True, phase="prepared")
            self.persist()
            return self.record
        except Exception as error:
            self.record["primary_failure"] = {"phase": self.record["phase"], "type": type(error).__name__}
            self.persist()
            raise

    def cleanup(self):
        if not _path(self.root, LEASE).exists():
            return {"status": "no-owned-lease", "owned_deleted": False, "cleanup_passed": True,
                    "native_acceptance": False}  # No create receipt, no device actions.
        self.record = _read(self.root, LEASE)
        scope = self.record.get("scope") if type(self.record) is dict else None
        if (type(self.record) is not dict or type(self.record.get("schema_version")) is not int or
                self.record["schema_version"] != 1 or type(scope) is not dict or scope.keys() != self.scope.keys() or
                any(type(scope[key]) is not type(value) or scope[key] != value for key, value in self.scope.items()) or
                self.record.get("owner_name_sha256") != hashlib.sha256(self.name.encode()).hexdigest() or
                self.record.get("cleanup") is not None or self.record.get("packages_published") is not False or
                self.record.get("release_readiness_certified") is not False or
                type(self.record.get("library_native_methods_executed")) is not int or
                self.record["library_native_methods_executed"] != 0 or self.record.get("library_readiness_verified") is not False):
            raise ValueError("Exact fresh same-run simulator lease is required; no cleanup replay")
        if self.record.get("creation_requested") is False:
            _claim_cleanup(self.root, self.record)
            result = {"status": "creation-not-requested", "owned_deleted": False,
                      "nonowned_preserved": None, "cleanup_passed": True, "native_acceptance": False}
            self.record["cleanup"] = result; self.persist(); return result
        udid = self.record.get("owned_udid")
        baseline = self.record.get("baseline")
        if (self.record.get("creation_requested") is not True or self.record.get("creation_returned") is not True or
                type(udid) is not str or not runtime.UUID.fullmatch(udid) or udid != udid.upper() or
                type(baseline) is not dict or type(baseline.get("devices")) is not dict or udid in baseline["devices"] or
                type(self.record.get("source_simulator")) is not dict or
                self.record["source_simulator"].get("udid", "").upper() not in baseline["devices"]):
            raise ValueError("Unknown, preinstalled or unacknowledged device must never be a cleanup target")
        _claim_cleanup(self.root, self.record)
        result = {"status": "cleanup-started", "owned_deleted": False,
                  "nonowned_preserved": False, "cleanup_passed": False, "native_acceptance": False}
        self.cleaning = True
        try:
            documents, snapshot = self.inventory()
            selected = self.owned(documents, snapshot)
            preserved_before = self.preserved(snapshot)
            if selected["state"] in {"Booted", "Booting"}:
                self.command("shutdown", (XCRUN, "simctl", "shutdown", udid))
                documents, snapshot = self.inventory()
                selected = self.owned(documents, snapshot)
            if selected["state"] != "Shutdown":
                raise ValueError("Owned shutdown state must be observed before deletion")
            self.command("delete", (XCRUN, "simctl", "delete", udid))
            _, snapshot = self.inventory()
            result["owned_deleted"] = udid not in snapshot["devices"]
            result["nonowned_preserved"] = preserved_before and self.preserved(snapshot)
            result["cleanup_passed"] = result["owned_deleted"] and result["nonowned_preserved"]
            result["status"] = "owned-deleted" if result["owned_deleted"] else "deletion-not-verified"
        except Exception as error:
            result["error"] = {"phase": self.record["phase"], "type": type(error).__name__}
            raise
        finally:
            # Independent owned disposal can pass while original-state custody
            # fails. Neither may erase the primary boot/runtime/native failure.
            self.record["cleanup"] = result
            self.persist()
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "cleanup"))
    parser.add_argument("--focus", required=True, choices=tuple(FOCUSES))
    args = parser.parse_args()
    try:
        owner = OwnedGeometrySimulator(ROOT, args.focus)
        result = owner.prepare() if args.mode == "prepare" else owner.cleanup()
        print(json.dumps({key: result.get(key) for key in ("prepared", "owned_udid", "boot_terminal", "status",
            "owned_deleted", "nonowned_preserved", "cleanup_passed") if key in result}, sort_keys=True))
        return 0 if args.mode == "prepare" or result["cleanup_passed"] else 1
    except Exception as error:
        # No exception text, native output, inherited environment or user names.
        print(json.dumps({"mode": args.mode, "passed": False, "error_type": type(error).__name__,
                          "native_acceptance": False}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
