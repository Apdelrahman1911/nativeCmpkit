"""Read-only, bounded diagnostics for this exact owned simulator application.

Never uploads a raw/private Apple report, executes it, searches other applications,
or treats missing diagnostics as proof no crash occurred. A report must match the
unique bundle, observed launch PID, linked Mach-O UUID and execution time window.
This helper cannot make failed transport or an unfinished testcase successful.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

MAX_REPORT_BYTES = 8 * 1024**2
MAX_CANDIDATES = 128
MAX_IMAGES = 1024
MAX_THREADS = 128
MAX_FRAMES = 32
BUNDLE = re.compile(r"io\.github\.apdelrahman1911\.nativecmpkit\.verification\.ui\.r[0-9a-f]{12}\.t[0-9a-f]{32}\Z")
UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
SYSTEM_IMAGES = {
    "UIKitCore", "UIKit", "Foundation", "CoreFoundation", "CoreGraphics", "QuartzCore",
    "libobjc.A.dylib", "libdispatch.dylib", "libsystem_kernel.dylib", "libsystem_pthread.dylib",
    "libsystem_c.dylib", "libsystem_platform.dylib", "libc++abi.dylib", "libc++.1.dylib",
}
SYMBOL_PREFIXES = (
    "kfun:kotlin.", "kfun:kotlinx.", "kfun:com.mohamedrejeb.calf.", "Kotlin_", "kotlin::",
    "objc_", "CF", "CG", "_CF", "_CG", "dispatch_", "_dispatch_", "CA::", "-[", "+[",
)
SYSTEM_SYMBOLS = {
    "abort", "__abort_with_payload", "__pthread_kill", "pthread_kill", "_pthread_start",
    "_pthread_wqthread", "start_wqthread", "mach_msg2_trap", "mach_msg_trap", "mach_msg",
    "__ulock_wait", "__psynch_cvwait", "UIApplicationMain",
}


def integer(value: object, maximum: int = 2**64 - 1) -> bool:
    return type(value) is int and 0 <= value <= maximum


def unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate diagnostic key")
        result[key] = value
    return result


def finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Nonfinite diagnostic number")
    return value


def apple_document(payload: bytes) -> dict:
    # Modern .ips is a metadata object followed by one payload object. Accept a
    # single payload too, but no trailing third document/garbage or merged keys.
    decoder = json.JSONDecoder(object_pairs_hook=unique, parse_float=finite_float,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite diagnostic constant")))
    text = payload.decode("utf-8")
    values = []
    while text.strip():
        value, end = decoder.raw_decode(text.lstrip())
        if not isinstance(value, dict) or len(values) == 2:
            raise ValueError("Unexpected diagnostic document")
        values.append(value)
        text = text.lstrip()[end:]
    if not values:
        raise ValueError("Empty diagnostic document")
    return values[-1]


def aware_time(value: object) -> dt.datetime:
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError("Missing bounded diagnostic time")
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Diagnostic time has no explicit timezone")
    return result


def regular_bytes(path: Path) -> bytes:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_REPORT_BYTES:
        raise ValueError("Expected bounded unshared regular diagnostic")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        opened = os.fstat(descriptor)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or identity(before) != identity(opened):
            raise ValueError("Diagnostic identity changed before read")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read(MAX_REPORT_BYTES + 1)
        after = os.fstat(descriptor)
        if identity(opened) != identity(after) or identity(after) != identity(path.lstat()) or len(payload) != before.st_size:
            raise ValueError("Diagnostic changed during read")
        return payload
    finally:
        os.close(descriptor)


def safe_frames(document: dict, images: list, executable: str, owner_index: int) -> list[dict]:
    threads = document.get("threads")
    faulting = document.get("faultingThread")
    if not isinstance(threads, list) or len(threads) > MAX_THREADS or not integer(faulting, MAX_THREADS - 1) or faulting >= len(threads):
        raise ValueError("Missing bounded faulting thread")
    thread = threads[faulting]
    if not isinstance(thread, dict) or not isinstance(thread.get("frames"), list) or len(thread["frames"]) > 4096:
        raise ValueError("Invalid diagnostic frame table")
    result = []
    for frame in thread["frames"][:MAX_FRAMES]:
        if not isinstance(frame, dict) or not integer(frame.get("imageIndex"), MAX_IMAGES - 1) or frame["imageIndex"] >= len(images):
            raise ValueError("Invalid diagnostic image index")
        index = frame["imageIndex"]
        name = images[index].get("name")
        image_name = "owned-application" if index == owner_index else name if name in SYSTEM_IMAGES else "other-image"
        row = {"image": image_name}
        if integer(frame.get("imageOffset")):
            row["image_offset"] = frame["imageOffset"]
        symbol = frame.get("symbol")
        if isinstance(symbol, str):
            # No report paths, object descriptions, raw messages, arbitrary
            # annotations or unknown/private symbol strings leave the runner.
            safe = bool(re.fullmatch(r"[A-Za-z0-9_.$:<>()? &,*+\[\]#{}\-;=]{1,1024}", symbol))
            if image_name != "other-image" and safe and (symbol in SYSTEM_SYMBOLS or symbol.startswith(SYMBOL_PREFIXES)):
                row["symbol"] = symbol
            else:
                row["unexported_symbol_sha256"] = hashlib.sha256(symbol.encode()).hexdigest()
        result.append(row)
    return result


def owned_summary(payload: bytes, *, bundle_id: str, pid: int, executable_uuid: str,
                  executable: str, started: dt.datetime, ended: dt.datetime) -> dict | None:
    document = apple_document(payload)
    bundle = document.get("bundleInfo")
    if not isinstance(bundle, dict) or bundle.get("CFBundleIdentifier") != bundle_id or document.get("pid") != pid or document.get("procName") != executable:
        return None
    captured = aware_time(document.get("captureTime"))
    if not started <= captured <= ended:
        return None
    images = document.get("usedImages")
    if not isinstance(images, list) or not 0 < len(images) <= MAX_IMAGES or not all(isinstance(i, dict) for i in images):
        raise ValueError("Invalid diagnostic image table")
    owners = [index for index, image in enumerate(images) if image.get("name") == executable and
              isinstance(image.get("uuid"), str) and image["uuid"].lower() == executable_uuid.lower()]
    if len(owners) != 1:
        return None
    result = {
        "raw_report_sha256": hashlib.sha256(payload).hexdigest(), "raw_report_bytes": len(payload),
        "capture_time": captured.isoformat(), "bundle_id": bundle_id, "pid": pid,
        "linked_executable_uuid": executable_uuid.lower(), "faulting_thread": document.get("faultingThread"),
        "faulting_thread_frames": safe_frames(document, images, executable, owners[0]),
    }
    for source, destination, keys in [
        ("exception", "exception", ("type", "signal")),
        ("termination", "termination", ("namespace",)),
    ]:
        value = document.get(source)
        if isinstance(value, dict):
            selected = {k: value[k] for k in keys if isinstance(value.get(k), str) and re.fullmatch(r"[A-Z_]{1,40}", value[k])}
            if integer(value.get("code")):
                selected["code"] = value["code"]
            if source == "exception" and isinstance(value.get("rawCodes"), list) and len(value["rawCodes"]) <= 8 and all(integer(c) for c in value["rawCodes"]):
                selected["raw_codes"] = value["rawCodes"]
            if selected:
                result[destination] = selected
    return result


def collect(directory: Path, *, bundle_id: str, pid: int | None, executable_uuid: str | None,
            executable: str, started_utc: str, ended_utc: str) -> dict:
    result = {
        "schema_version": 1, "status": "unavailable", "raw_reports_uploaded": False,
        "native_functionality_verified": False, "reports_examined": 0, "reports_rejected": 0,
        "scope": "Read-only owner/PID/UUID/time-bound Apple crash diagnostics. Only selected numeric identities and known native symbols; no private raw report/path/message. Missing diagnostics do not prove absence of a crash or satisfy transport/test/release gates.",
    }
    try:
        if not BUNDLE.fullmatch(bundle_id) or not integer(pid, 2**31 - 1) or pid == 0 or not isinstance(executable_uuid, str) or not UUID.fullmatch(executable_uuid):
            result["reason"] = "Exact observed launch PID or linked UUID unavailable; no report read"
            return result
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,63}", executable):
            raise ValueError("Invalid owned executable name")
        started, ended = aware_time(started_utc), aware_time(ended_utc)
        if not 0 <= (ended - started).total_seconds() <= 3600:
            raise ValueError("Invalid diagnostic execution window")
        if not directory.exists():
            result.update(status="no-matching-owned-report", reason="Diagnostic directory unavailable; crash absence not established")
            return result
        if any(part.is_symlink() for part in [directory, *directory.parents]) or not directory.is_dir():
            raise ValueError("Diagnostic directory must not traverse symlinks")
        # Inspect names of immediate children only. Never recurse or open another
        # application's reports, SDK/machine files or old archive attachments.
        matches = []
        for path in directory.iterdir():
            if not path.name.startswith(executable + "-") or path.suffix != ".ips":
                continue
            if result["reports_examined"] >= MAX_CANDIDATES:
                raise ValueError("Owned diagnostic candidate limit exceeded")
            result["reports_examined"] += 1
            try:
                payload = regular_bytes(path)
                row = owned_summary(payload, bundle_id=bundle_id, pid=pid, executable_uuid=executable_uuid,
                                    executable=executable, started=started, ended=ended)
                if row is not None:
                    matches.append(row)
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                result["reports_rejected"] += 1
        if len(matches) == 1:
            result.update(status="matched-owned-report", report=matches[0])
        elif matches:
            result.update(status="ambiguous-owned-reports", matching_report_count=len(matches))
        else:
            result.update(status="no-matching-owned-report", reason="No uniquely verified owned report found; crash absence not established")
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        result.update(status="unavailable", error_type=type(error).__name__)
    return result
