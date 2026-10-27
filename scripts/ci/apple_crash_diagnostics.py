"""Read-only, bounded diagnostics for this exact owned simulator application.

Never uploads a raw/private Apple report, executes it, searches foreign process names,
or treats missing diagnostics as proof no crash occurred. A report must match the
unique bundle, observed launch PID, linked Mach-O UUID and execution time window.
This helper cannot make failed transport or an unfinished testcase successful.
"""
from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

MAX_REPORT_BYTES = 8 * 1024**2
MAX_CANDIDATES = 32
MAX_DIRECTORY_ENTRIES = 8192
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
RUNTIME_SYMBOL_PREFIXES = (
    "kfun:kotlin.", "kfun:kotlinx.", "kfun:com.mohamedrejeb.calf.", "Kotlin_", "kotlin::",
)
OBJC_CLASSES = (
    "UIApplication", "UIWindow", "UIView", "UIViewController", "UIImage", "UIAlertController",
    "UIDatePicker", "UIPresentationController", "UIPopoverPresentationController",
    "NSObject", "NSRunLoop", "NSThread", "NSTimer", "NSAutoreleasePool",
)
SYSTEM_SYMBOLS = {
    "abort", "__abort_with_payload", "__pthread_kill", "pthread_kill", "_pthread_start",
    "_pthread_wqthread", "start_wqthread", "mach_msg2_trap", "mach_msg_trap", "mach_msg",
    "__ulock_wait", "__psynch_cvwait", "UIApplicationMain",
    "CFRunLoopRunSpecific", "CFRunLoopRun", "__CFRunLoopRun", "__CFRunLoopServiceMachPort",
    "__CFRunLoopDoTimers", "__CFRunLoopDoTimer", "__CFRUNLOOP_IS_CALLING_OUT_TO_A_TIMER_CALLBACK_FUNCTION__",
    "CGBitmapContextCreate", "CGBitmapContextCreateImage", "CGContextDrawImage", "CGImageRelease",
    "objc_msgSend", "objc_release", "objc_retain", "objc_autoreleasePoolPop", "objc_autoreleasePoolPush",
    "_dispatch_main_queue_drain", "_dispatch_main_queue_callback_4CF", "_dispatch_client_callout",
}
EXCEPTION_TYPES = {
    "EXC_BAD_ACCESS", "EXC_BAD_INSTRUCTION", "EXC_ARITHMETIC", "EXC_EMULATION", "EXC_SOFTWARE",
    "EXC_BREAKPOINT", "EXC_SYSCALL", "EXC_MACH_SYSCALL", "EXC_RPC_ALERT", "EXC_CRASH",
    "EXC_RESOURCE", "EXC_GUARD", "EXC_CORPSE_NOTIFY",
}
SIGNALS = {"SIGABRT", "SIGBUS", "SIGFPE", "SIGILL", "SIGKILL", "SIGSEGV", "SIGTRAP", "SIGTERM", "SIGQUIT", "SIGSYS"}
TERMINATION_NAMESPACES = {
    "SIGNAL", "FRONTBOARD", "SPRINGBOARD", "RUNNINGBOARD", "WATCHDOG", "MACH", "CODESIGNING",
    "LIBSYSTEM", "WEBKIT", "OPENGL", "DYLD", "TCC", "ASSERTION", "RESOURCE", "JETSAM", "GPU",
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


def apple_documents(payload: bytes) -> list[dict]:
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
    return values


def apple_document(payload: bytes) -> dict:
    return apple_documents(payload)[-1]


def aware_time(value: object) -> dt.datetime:
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError("Missing bounded diagnostic time")
    # Apple captureTime/timestamp commonly separates a numeric UTC offset by
    # a space ("...30.1234 +0000"), unlike our ISO receipts. Keep the zone
    # explicit; never infer runner local time or use filesystem mtime instead.
    normalized = re.sub(r" ([+-][0-9]{4})\Z", r"\1", value)
    result = dt.datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("Diagnostic time has no explicit timezone")
    return result


@contextmanager
def anchored_directory(path: Path):
    """Hold no-follow directory descriptors, never re-resolve swapped parents.

    Verify every parent entry again before accepting a summary. A renamed or
    replaced ancestor cannot redirect reads to its new/foreign target. This is
    a read-only filesystem lease, not an OS sandbox or trusted crash reporter.
    """
    if not getattr(os, "O_NOFOLLOW", 0) or not getattr(os, "O_DIRECTORY", 0):
        raise OSError("Secure directory-open primitives unavailable")
    path = path.absolute()
    if ".." in path.parts or len(path.parts) > 128:
        raise ValueError("Invalid diagnostic directory path")
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY | getattr(os, "O_NONBLOCK", 0)
    descriptors, entries = [], []
    try:
        descriptor = os.open(path.anchor, flags)
        descriptors.append(descriptor)
        for part in path.parts[1:]:
            parent = descriptor
            before = os.stat(part, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise ValueError("Diagnostic ancestor is not a regular directory")
            descriptor = os.open(part, flags, dir_fd=parent)
            descriptors.append(descriptor)
            opened = os.fstat(descriptor)
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino) or not stat.S_ISDIR(opened.st_mode):
                raise ValueError("Diagnostic directory changed during open")
            entries.append((parent, part, opened.st_dev, opened.st_ino))
        yield descriptor
        for parent, part, device, inode in entries:
            after = os.stat(part, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(after.st_mode) or (after.st_dev, after.st_ino) != (device, inode):
                raise ValueError("Diagnostic directory ownership changed during read")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def regular_bytes(path: Path, *, directory_fd: int | None = None) -> bytes:
    if directory_fd is None:
        with anchored_directory(path.parent) as descriptor:
            return regular_bytes(path, directory_fd=descriptor)
    # Caller holds the directory lease. Only one immediate basename is opened.
    before = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_REPORT_BYTES:
        raise ValueError("Expected bounded unshared regular diagnostic")
    descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0), dir_fd=directory_fd)
    try:
        opened = os.fstat(descriptor)
        identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or identity(before) != identity(opened):
            raise ValueError("Diagnostic identity changed before read")
        blocks, total = [], 0
        while total <= MAX_REPORT_BYTES:
            block = os.read(descriptor, min(65536, MAX_REPORT_BYTES + 1 - total))
            if not block:
                break
            total += len(block)
            blocks.append(block)
        payload = b"".join(blocks)
        after = os.fstat(descriptor)
        entry = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if identity(opened) != identity(after) or identity(after) != identity(entry) or len(payload) != before.st_size:
            raise ValueError("Diagnostic changed during read")
        return payload
    finally:
        os.close(descriptor)


def safe_symbol(symbol: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_.$:<>()? &,*+\[\]#{}\-;=]{1,1024}", symbol):
        return False
    # Only static public Kotlin/runtime namespaces and finite native framework
    # symbols/classes. An arbitrary ObjC/CF prefix does not grant export access.
    return (symbol in SYSTEM_SYMBOLS or symbol.startswith(RUNTIME_SYMBOL_PREFIXES) or
            bool(re.fullmatch(r"[-+]\[(?:" + "|".join(OBJC_CLASSES) + r") [A-Za-z_][A-Za-z0-9_:]*\]", symbol)))


def safe_frames(document: dict, images: list, owner_index: int) -> list[dict]:
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
            if image_name != "other-image" and safe_symbol(symbol):
                row["symbol"] = symbol
            else:
                # Do not emit even a dictionary-guessable hash of a private
                # symbol. Only the whole raw report has a provenance digest.
                row["symbol_omitted"] = True
        result.append(row)
    return result


def owned_summary(payload: bytes, *, bundle_id: str, pid: int, executable_uuid: str,
                  executable: str, started: dt.datetime, ended: dt.datetime) -> dict | None:
    documents = apple_documents(payload)
    document = documents[-1]
    bundle = document.get("bundleInfo")
    if not isinstance(bundle, dict) or bundle.get("CFBundleIdentifier") != bundle_id or not integer(document.get("pid"), 2**31 - 1) or document.get("pid") != pid or document.get("procName") != executable:
        return None
    captured = aware_time(document.get("captureTime"))
    if not started <= captured <= ended:
        return None
    if len(documents) == 2:
        metadata = documents[0]
        for key, value in (("app_name", executable), ("bundleID", bundle_id), ("slice_uuid", executable_uuid)):
            if key in metadata and (not isinstance(metadata[key], str) or
                    (metadata[key].lower() != value.lower() if key == "slice_uuid" else metadata[key] != value)):
                return None
        if "timestamp" in metadata and not started <= aware_time(metadata["timestamp"]) <= ended:
            return None
    images = document.get("usedImages")
    if not isinstance(images, list) or not 0 < len(images) <= MAX_IMAGES or not all(isinstance(i, dict) for i in images):
        raise ValueError("Invalid diagnostic image table")
    owners = [index for index, image in enumerate(images) if image.get("name") == executable and
              isinstance(image.get("uuid"), str) and image["uuid"].lower() == executable_uuid.lower()]
    if len(owners) != 1:
        return None
    # Watchdog/resource terminations may have no faultingThread. Retain their
    # numeric identity without inventing a stack or silently discarding them.
    faulting = document.get("faultingThread")
    frames = safe_frames(document, images, owners[0]) if "faultingThread" in document else []
    result = {
        "raw_report_sha256": hashlib.sha256(payload).hexdigest(), "raw_report_bytes": len(payload),
        "capture_time": captured.isoformat(), "bundle_id": bundle_id, "pid": pid,
        "linked_executable_uuid": executable_uuid.lower(), "faulting_thread": faulting,
        "faulting_thread_status": "observed" if "faultingThread" in document else "unavailable",
        "faulting_thread_frames": frames,
    }
    for source, destination, allowed in [
        ("exception", "exception", {"type": EXCEPTION_TYPES, "signal": SIGNALS}),
        ("termination", "termination", {"namespace": TERMINATION_NAMESPACES}),
    ]:
        value = document.get(source)
        if isinstance(value, dict):
            selected = {k: value[k] for k, choices in allowed.items() if isinstance(value.get(k), str) and value[k] in choices}
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
        "native_functionality_verified": False, "reports_examined": 0, "reports_rejected": 0, "directory_entries_examined": 0,
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
        # Inspect names of immediate children only. Never recurse or open another
        # process's candidate files, SDK/machine files or old archive attachments.
        # Same-executable candidates still need their embedded exact owner proof.
        matches = []
        with anchored_directory(directory) as descriptor, os.scandir(descriptor) as entries:
            for entry in entries:
                result["directory_entries_examined"] += 1
                if result["directory_entries_examined"] > MAX_DIRECTORY_ENTRIES:
                    raise ValueError("Diagnostic directory scan limit exceeded")
                path = Path(entry.name)
                if not path.name.startswith((executable + "-", executable + "_")) or path.suffix != ".ips":
                    continue
                if result["reports_examined"] >= MAX_CANDIDATES:
                    raise ValueError("Owned diagnostic candidate limit exceeded")
                result["reports_examined"] += 1
                try:
                    payload = regular_bytes(path, directory_fd=descriptor)
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
    except FileNotFoundError:
        result.update(status="no-matching-owned-report", reason="Diagnostic directory unavailable or changed; crash absence not established")
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        result.update(status="unavailable", error_type=type(error).__name__)
    return result
