"""Read-only bundle/time-bound system launch events for one failed profile app.

No raw logs/messages/paths, arbitrary process names or diagnostic success can
establish launch, native functionality, debugger authorization or a memory pass.
The launcher may refuse before supplying a PID: do not guess one or read crashes
from unrelated apps. Only fixed observations survive an actual selected log query.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess

import apple_crash_diagnostics as crashes
import runtime_context as runtime

MAX_BYTES = 1024**2
MAX_ROWS = 2048
MAX_MESSAGE_BYTES = 8192
SYSTEM_PROCESSES = {"SpringBoard", "runningboardd", "amfid", "installd", "securityd", "launchd_sim"}
FIXED_CATEGORIES = {
    "signature-invalid": r"\binvalid code signature\b|\bcode signature invalid\b|\bsignature verification failed\b",
    "service-delegate-denial": r"\bdenied by service delegate\b",
    "required-entitlement-missing": r"\bmissing required entitlement\b|\brequired entitlement is missing\b",
    "application-unregistered": r"\bapplication is not registered\b|\bno such application\b",
}


def timestamp(text: str) -> dt.datetime:
    if not isinstance(text, str) or not 1 <= len(text) <= 64:
        raise ValueError("Expected bounded actual diagnostic timestamp")
    value = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("Diagnostic time must carry its actual timezone")
    return value.astimezone(dt.timezone.utc)


def window(started: str, ended: str) -> tuple[dt.datetime, dt.datetime]:
    start, end = timestamp(started), timestamp(ended)
    if not 0 < (end - start).total_seconds() <= 360:
        raise ValueError("Only one bounded actual failed-launch time window may be queried")
    return start, end


def summarize(payload: bytes, bundle: str, started: str, ended: str) -> dict:
    if not crashes.BUNDLE.fullmatch(bundle):
        raise ValueError("Use the exact owned unique verification bundle")
    start, end = window(started, ended)
    if not isinstance(payload, bytes) or not 0 < len(payload) <= MAX_BYTES:
        raise ValueError("Only bounded actual system-log JSON may be inspected")
    try:
        rows = json.loads(payload, object_pairs_hook=crashes.unique,
                          parse_float=crashes.finite_float,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite diagnostic constant")))
    except (RecursionError, UnicodeError) as error:
        raise ValueError("Unreviewable system-log document") from error
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("Expected bounded system-log event array")
    token = re.compile(r"(?<![A-Za-z0-9_.-])" + re.escape(bundle) + r"(?![A-Za-z0-9_.-])")
    count, rejected = 0, 0
    processes, categories = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected actual system-log event object")
        message, path = row.get("eventMessage"), row.get("processImagePath")
        if (not isinstance(message, str) or len(message.encode()) > MAX_MESSAGE_BYTES or
                not isinstance(path, str) or len(path.encode()) > MAX_MESSAGE_BYTES):
            raise ValueError("Unbounded/missing actual log message or process identity")
        moment = timestamp(row.get("timestamp"))
        process = path.rsplit("/", 1)[-1]
        if not start <= moment <= end or process not in SYSTEM_PROCESSES or not token.search(message):
            rejected += 1
            continue
        count += 1
        processes.add(process)
        categories.update(name for name, pattern in FIXED_CATEGORIES.items() if re.search(pattern, message, re.I))
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            "events_examined": len(rows), "owned_system_rows": count, "rejected_events": rejected,
            "system_process_names": sorted(processes), "matched_fixed_categories": sorted(categories),
            "raw_messages_paths_or_log_uploaded": False, "root_cause_proven": False,
            "native_functionality_verified": False}


def collect(device: str, bundle: str, started: str, ended: str, control) -> dict:
    if not runtime.UUID.fullmatch(device) or not crashes.BUNDLE.fullmatch(bundle):
        raise ValueError("No foreign simulator, bundle, command or guessed launch PID")
    start, end = window(started, ended)
    # log show accepts timezone-bearing timestamps at second precision. Expand
    # the query endpoints only; summarize still enforces the original exact times.
    lower = start.replace(microsecond=0)
    upper = end.replace(microsecond=0) + (dt.timedelta(seconds=1) if end.microsecond else dt.timedelta())
    command = ["/usr/bin/xcrun", "simctl", "spawn", device, "log", "show",
               "--start", lower.strftime("%Y-%m-%d %H:%M:%S%z"),
               "--end", upper.strftime("%Y-%m-%d %H:%M:%S%z"), "--style", "json",
               "--predicate", 'eventMessage CONTAINS "' + bundle + '"']
    result = {"schema_version": 1, "status": "unavailable", "owned_system_rows": 0,
              "command": command, "timeout_seconds": 30, "raw_messages_paths_or_log_uploaded": False,
              "root_cause_proven": False, "native_functionality_verified": False,
              "scope": "Read-only exact bundle/time/selected-simulator system events after a pre-PID launch refusal. Fixed observations do not prove its cause, launch, native tests, attach authorization or memory/release readiness."}
    try:
        actual = control(command, 30)
        if (type(actual.returncode) is not int or not isinstance(actual.stdout, bytes) or
                not isinstance(actual.stderr, bytes) or len(actual.stdout) + len(actual.stderr) > MAX_BYTES):
            raise ValueError("Unbounded/unreviewable actual log-tool result")
        result.update(exit_code=actual.returncode, stdout_bytes=len(actual.stdout),
                      stdout_sha256=hashlib.sha256(actual.stdout).hexdigest(),
                      stderr_bytes=len(actual.stderr), stderr_sha256=hashlib.sha256(actual.stderr).hexdigest())
        if actual.returncode == 0:
            result.update(summarize(actual.stdout, bundle, started, ended))
            if result["owned_system_rows"]:
                result["status"] = "observed-owned-system-events"
    except (OSError, ValueError, RecursionError, subprocess.SubprocessError) as error:
        result["error_type"] = type(error).__name__
    return result
