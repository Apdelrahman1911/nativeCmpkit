#!/usr/bin/env python3
"""Bounded Instruments/leaks observation of an exact owned UIKit test app/PID.

No profiles, addresses, heap contents, process paths, logs or binaries are exported.
Unsupported/missing allocation rows stay explicit; native test success is NOT a
profile success. The app's unique ack witnesses attempt completion only.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid
import xml.etree.ElementTree as ET

import apple_memory_discovery as discovery
import library_tests as lt
import runtime_context as runtime

NATIVE_SYMBOLS = ("com.mohamedrejeb.calf.ui.utils", "UIImageMemoryDiagnosticsTest", "ImageUtils.kt")
DARWIN_REQUESTS = {"MallocScribble": "1", "MallocGuardEdges": "1", "MallocErrorAbort": "1",
                   "MallocStackLogging": "1"}
ATTEMPT_SECONDS = 180


def allocation_summary(path: Path) -> dict:
    tree, payload = discovery.bounded_xml(path)
    tag = lambda node: node.tag.rsplit("}", 1)[-1]
    rows, definitions = [], {}
    for index, node in enumerate(tree.iter()):
        if index >= 200_000:
            raise ValueError("Allocation XML exceeds its semantic inspection bound")
        if tag(node) == "row":
            rows.append(node)
        if tag(node) in {"frame", "backtrace"} and node.get("id"):
            key = (tag(node), node.get("id"))
            if key in definitions:
                raise ValueError("Ambiguous native allocation frame/backtrace reference")
            definitions[key] = node
    symbols = set()
    owned_rows = 0
    for row in rows:
        pending, visited_references, matched = list(row), set(), set()
        inspected = 0
        while pending:
            node = pending.pop()
            inspected += 1
            if inspected > 4096:
                raise ValueError("Allocation row/backtrace exceeds its traversal bound")
            if tag(node) == "frame":
                # Only actual stack-frame fields in this allocation row (or its
                # explicit frame/backtrace references) establish correlation.
                # Symbol-bearing metadata beside an unrelated row is not evidence.
                for value in (node.text or "", node.get("name", ""), node.get("fmt", "")):
                    matched.update(symbol for symbol in NATIVE_SYMBOLS if symbol in value)
            reference = (tag(node), node.get("ref"))
            if reference[0] in {"frame", "backtrace"} and reference[1] and reference not in visited_references:
                visited_references.add(reference)
                definition = definitions.get(reference)
                if definition is not None:
                    pending.append(definition)
            pending.extend(node)
        if matched:
            owned_rows += 1
            symbols.update(matched)
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "rows": len(rows),
            "owned_allocation_rows": owned_rows,
            "owned_library_frame_seen": owned_rows > 0, "matched_fixed_symbols": sorted(symbols),
            "raw_rows_addresses_values_or_trace_uploaded": False}


def leak_summary(path: Path, pid: int) -> dict:
    stat = path.stat()
    if (not path.is_file() or path.is_symlink() or stat.st_nlink != 1 or
            not 0 < stat.st_size <= discovery.MAX_XML_BYTES):
        raise ValueError("Expected bounded private leak-tool output")
    body = path.read_bytes()
    lines = re.findall(rb"Process\s+([0-9]+):\s+([0-9]+)\s+leaks?\s+for\s+([0-9]+)\s+total\s+leaked\s+bytes", body)
    if len(lines) != 1 or int(lines[0][0]) != pid:
        raise ValueError("Missing or foreign actual leak summary; do not invent zero leaks")
    return {"process_id": pid, "leaks": int(lines[0][1]), "leaked_bytes": int(lines[0][2]),
            "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "raw_output_uploaded": False}


class ImageProfileDriver:
    def __init__(self, root: Path, output: Path, device: str, bundle: str,
                 signed_hash: str, plist_hash: str, control):
        import ios_ui_application as app
        if not runtime.UUID.fullmatch(device) or not app.crashes.BUNDLE.fullmatch(bundle):
            raise ValueError("Profile only the exact owned simulator/application")
        if not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in (signed_hash, plist_hash)):
            raise ValueError("Profile ownership requires installed executable/plist hashes")
        self.root, self.output, self.device, self.bundle = root, output, device, bundle
        self.signed_hash, self.plist_hash, self.control = signed_hash, plist_hash, control
        self.private = lt.safe_path(root, (output / "image-profile-private").relative_to(root).as_posix())
        self.ack = None
        self.ack_identity = None
        self.started = False
        self.receipt = {"schema_version": 1, "simulator_udid": device, "bundle_identifier": bundle,
                        "signed_application_executable_sha256": signed_hash, "application_plist_sha256": plist_hash,
                        "supported": False, "profile_passed": False, "commands": [], "exports": [], "errors": [],
                        "darwin_heap_requests": DARWIN_REQUESTS.copy(), "ASan_verified": False,
                        "every_allocator_check_attested": False, "private_files_uploaded": False,
                        "scope": "Actual Instruments/leaks tool attempt on this exact owned library UIKit app/PID. Only useful owned-frame allocation rows and an actual zero-leak summary can pass this profile; test passes alone cannot.",
                        "release_readiness_certified": False}

    def prepare(self) -> dict[str, str]:
        if self.ack is not None or self.private.exists():
            raise ValueError("Never repeat or overwrite an owned profile attempt")
        if shutil.disk_usage(self.root).free < 8192 * 1024**2 + discovery.MAX_PRIVATE_BYTES:
            raise OSError("Profile staging must preserve the production 8 GiB reserve")
        result = self.control(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.bundle, "data"], 30)
        if result.returncode or not isinstance(result.stdout, bytes) or len(result.stdout) > 4096:
            raise RuntimeError("Exact application data container is unavailable")
        container = Path(result.stdout.decode("utf-8", errors="strict").strip())
        if not container.is_absolute() or not container.is_dir() or not runtime.UUID.fullmatch(container.name):
            raise ValueError("Unexpected actual simulator application data container")
        # Follow Apple's own canonical container path, never a guessed session/device/root.
        container = container.resolve(strict=True)
        temporary = (container / "tmp").resolve(strict=True)
        if not temporary.is_dir() or not temporary.is_relative_to(container):
            raise ValueError("Profile ack must stay in this application's actual private tmp")
        self.ack = temporary / ("nativecmpkit-image-profile-" + uuid.uuid4().hex + ".ack")
        if self.ack.exists() or self.ack.is_symlink():
            raise ValueError("Refuse any preexisting completion witness")
        self.private.mkdir(mode=0o700)
        environment = os.environ.copy()
        requested = {"NATIVECMPKIT_IMAGE_PROFILE_ACK": str(self.ack), **DARWIN_REQUESTS}
        for name, value in requested.items():
            key = "SIMCTL_CHILD_" + name
            if environment.get(key) not in (None, value):
                raise ValueError("Inherited native diagnostic selector conflicts with this owned attempt")
            environment[key] = value
        self.receipt["ack_basename_sha256"] = hashlib.sha256(self.ack.name.encode()).hexdigest()
        self.receipt["prepared"] = True
        return environment

    def request(self, pid: int) -> None:
        import ios_ui_application as app
        if self.ack is None or self.started or type(pid) is not int or not 0 < pid < 2**31:
            raise ValueError("One exact actual native process must own the profile request")
        self.started = True
        self.receipt.update(process_id=pid, started_at_utc=lt.utc_now())
        started = time.monotonic()

        def execute(command: list[str], name: str) -> dict:
            remaining = ATTEMPT_SECONDS - (time.monotonic() - started)
            if remaining < 1:
                raise TimeoutError("Owned profile attempt exceeded its total bound")
            log = self.private / (name + ".log")
            result = lt.execute(self.root, command, log, min(150, int(remaining)), 8192)
            self.receipt["commands"].append({"command": command, **result})
            discovery.private_inventory(self.root, self.private)
            return result

        try:
            lease = self.control(["/usr/bin/xcrun", "simctl", "get_app_container", self.device, self.bundle, "app"], 30)
            if not app.installed_identity(lease, self.bundle, self.signed_hash, self.plist_hash):
                raise ValueError("Installed profile application ownership changed")
            process = self.control(["/bin/ps", "-p", str(pid), "-o", "comm="], 15)
            if process.returncode or not isinstance(process.stdout, bytes) or len(process.stdout) > 4096:
                raise ValueError("Actual selected native process is unavailable")
            binary = Path(process.stdout.decode("utf-8", errors="strict").strip())
            installed = Path(lease.stdout.decode("utf-8", errors="strict").strip())
            if (not binary.is_absolute() or binary != installed / app.APP_EXECUTABLE or
                    not binary.is_file() or binary.is_symlink() or lt.sha256(binary) != self.signed_hash):
                raise ValueError("Native PID does not execute the exact installed owned binary")
            self.receipt["actual_process_executable_identity_verified"] = True
            trace = self.private / "owned-library.trace"
            outcome = execute(["/usr/bin/xcrun", "xctrace", "record", "--template", "Allocations",
                               "--time-limit", "12s", "--output", str(trace), "--attach", str(pid)], "allocations")
            if outcome["exit_code"] or outcome.get("stop_reason"):
                raise RuntimeError("Actual Instruments recording failed")
            toc = self.private / "toc.xml"
            outcome = execute(["/usr/bin/xcrun", "xctrace", "export", "--input", str(trace),
                               "--toc", "--output", str(toc)], "toc")
            if outcome["exit_code"] or outcome.get("stop_reason"):
                raise RuntimeError("Actual Instruments TOC export failed")
            tree, body = discovery.bounded_xml(toc)
            self.receipt["toc_sha256"] = hashlib.sha256(body).hexdigest()
            self.receipt["actual_allocation_schemas"] = discovery.allocation_schemas(tree)
            for index, schema in enumerate(self.receipt["actual_allocation_schemas"]):
                exported = self.private / ("allocation-" + str(index) + ".xml")
                outcome = execute(["/usr/bin/xcrun", "xctrace", "export", "--input", str(trace),
                                   "--xpath", "//table[@schema='" + schema + "']", "--output", str(exported)],
                                  "table-" + str(index))
                if outcome["exit_code"] or outcome.get("stop_reason"):
                    raise RuntimeError("Actual allocation export failed")
                self.receipt["exports"].append({"schema": schema, **allocation_summary(exported)})
            # A real PID-specific zero is required. Never parse missing output as no leaks.
            outcome = execute(["/usr/bin/leaks", str(pid)], "leaks")
            self.receipt["leak_summary"] = leak_summary(self.private / "leaks.log", pid)
            self.receipt["supported"] = any(e["owned_allocation_rows"] > 0 and e["owned_library_frame_seen"]
                                              for e in self.receipt["exports"])
            self.receipt["profile_passed"] = (self.receipt["supported"] and outcome["exit_code"] == 0 and
                not outcome.get("stop_reason") and self.receipt["leak_summary"]["leaks"] == 0 and
                self.receipt["leak_summary"]["leaked_bytes"] == 0)
            if not self.receipt["profile_passed"]:
                self.receipt["errors"].append({"error": "No useful owned-library allocation rows or no actual zero-leak summary; profile NOT verified"})
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, ET.ParseError) as error:
            self.receipt["errors"].append({"error_type": type(error).__name__, "profile_pass_inferred": False})
        finally:
            try:
                if self.ack.exists() or self.ack.is_symlink():
                    raise ValueError("Refuse replacing a foreign completion witness")
                with self.ack.open("xb") as handle:
                    handle.write(b"complete\n")
                stat = self.ack.stat()
                self.ack_identity = (stat.st_dev, stat.st_ino)
                self.receipt["attempt_completion_ack_created"] = True
            except (OSError, ValueError) as error:
                self.receipt["errors"].append({"ack_error_type": type(error).__name__})
                self.receipt["profile_passed"] = False
            self.receipt.update(finished_at_utc=lt.utc_now(), elapsed_seconds=round(time.monotonic() - started, 2))

    def close(self) -> None:
        try:
            if self.ack is not None and (self.ack.exists() or self.ack.is_symlink()):
                stat = self.ack.lstat()
                if (self.ack.is_symlink() or not self.ack.is_file() or stat.st_nlink != 1 or
                        (stat.st_dev, stat.st_ino) != self.ack_identity or self.ack.read_bytes() != b"complete\n"):
                    raise ValueError("Refuse removing a foreign or changed profile ack")
                self.ack.unlink()
            if self.private.exists():
                self.receipt["private_inventory"] = discovery.private_inventory(self.root, self.private)
                if self.private != lt.safe_path(self.root, self.private.relative_to(self.root).as_posix()):
                    raise ValueError("Owned private profile tree changed")
                shutil.rmtree(self.private)
            self.receipt["owned_private_tree_removed"] = not self.private.exists()
            self.receipt["owned_ack_removed"] = self.ack is None or not self.ack.exists()
        except (OSError, ValueError) as error:
            self.receipt["errors"].append({"cleanup_error_type": type(error).__name__})
            self.receipt["profile_passed"] = False


def validate_attempt(document: dict, device: str, bundle: str) -> bool:
    """Structural attempt contract, NOT a native or Instruments pass by itself."""
    pid = document.get("process_id")
    return (type(document.get("schema_version")) is int and document["schema_version"] == 1 and document.get("simulator_udid") == device and
            document.get("bundle_identifier") == bundle and type(pid) is int and 0 < pid < 2**31 and
            document.get("darwin_heap_requests") == DARWIN_REQUESTS and document.get("ASan_verified") is False and
            document.get("private_files_uploaded") is False and document.get("prepared") is True and
            document.get("attempt_completion_ack_created") is True and document.get("owned_ack_removed") is True and
            document.get("owned_private_tree_removed") is True and
            not any("ack_error_type" in error or "cleanup_error_type" in error for error in document.get("errors", [])))
