#!/usr/bin/env python3
"""Bounded public-fixture failure evidence, not tests or a success classifier.

The previous last-180-line job tail hid earlier Android/UTP failures behind the
final Gradle stack trace. Keep selected task sections, all exact cause-chain
headers, and an inert file inventory instead. Never upload APKs, caches, a full
terminal/environment transcript, or infer a passing testcase from a diagnostic.
Credential-related lines are omitted defensively; this is not a general-purpose
secret scrubber. Run only on the repository's reviewed public verification jobs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import library_tests as lt

MAX_LOG_BYTES = 4 * 1024 * 1024
MAX_EXCERPT_BYTES = 24 * 1024
MAX_EXCERPTS = 24
MAX_INVENTORY_FILES = 512
MAX_HASH_BYTES = 64 * 1024 * 1024
LOGS = ("gradle.log", "library/gradle.log", "apk-assembly.log",
        "owned-avd-create.log", "emulator.log")
CREDENTIAL = re.compile(
    r"(?i)(authorization|password|passwd|secret|token|credential|"
    r"BEGIN .*PRIVATE KEY|https?://[^/\s]+@|[?&](?:sig|key|auth)=)")
TASK = re.compile(r"^> Task (:[a-zA-Z0-9:_-]+)(?:\s|$)")


def sanitized(lines: list[str]) -> str:
    result = []
    size = 0
    for line in lines:
        # Remove control characters; retain the explicit newline/tab separators.
        normalized = "".join(c for c in line if c == "\t" or ord(c) >= 32)
        value = "[omitted credential-related diagnostic line]" if CREDENTIAL.search(normalized) else normalized[:2000]
        encoded = (value + "\n").encode("utf-8")
        if size + len(encoded) > MAX_EXCERPT_BYTES:
            result.append("[bounded excerpt truncated]")
            break
        result.append(value)
        size += len(encoded)
    return "\n".join(result) + ("\n" if result else "")


def sections(lines: list[str]) -> list[dict]:
    """Select explicit diagnostics, not arbitrary surrounding application output."""
    ranges = []
    headers = [(i, TASK.match(line)) for i, line in enumerate(lines) if TASK.match(line)]
    for position, (start, match) in enumerate(headers):
        if match[1].endswith(":connectedAndroidDeviceTest"):
            end = headers[position + 1][0] if position + 1 < len(headers) else len(lines)
            ranges.append((start, min(end, start + 140), "connected-task"))
    for i, line in enumerate(lines):
        if line.startswith("e: "):
            # Kotlin's source diagnostic can precede every Gradle cause/summary,
            # including during APK assembly. Select the explicit error line,
            # never arbitrary surrounding compiler/application output.
            ranges.append((i, i + 1, "compiler-error"))
        elif line.startswith("*** Terminating app due to uncaught exception "):
            # A real UIKit launch can fail before activation/TeamCity/JUnit.
            # Retain only the explicit Objective-C exception header; no nearby
            # app output, arbitrary stack or raw console transcript is selected.
            ranges.append((i, i + 1, "objc-exception"))
        elif line.startswith("Caused by:"):
            end = i + 1
            while end < min(len(lines), i + 18) and lines[end].startswith(("\tat ", "\t... ")):
                end += 1
            ranges.append((i, end, "cause-chain"))
        elif line.startswith("* Where:"):
            end = i + 1
            while end < min(len(lines), i + 8) and not lines[end].startswith("* "):
                end += 1
            ranges.append((i, end, "failure-location"))
        elif line.startswith("* What went wrong:"):
            end = i + 1
            while end < min(len(lines), i + 20) and not lines[end].startswith("* "):
                end += 1
            ranges.append((i, end, "task-failure"))
    ranges = sorted(set(ranges))
    return [{"kind": kind, "first_line": start + 1, "last_line": end,
             "text": sanitized(lines[start:end])} for start, end, kind in ranges[:MAX_EXCERPTS]]


def inventory(root: Path, relative: str) -> dict:
    """Hashes/paths only: never upload or interpret native test binary payloads."""
    folder = lt.safe_path(root, relative)
    files = []
    byte_count = 0
    if not folder.exists():
        return {"directory": relative, "exists": False, "files": [], "complete": True}
    if not folder.is_dir():
        raise ValueError("Expected a selected test-result directory")
    pending, entries = [folder], 0
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                entries += 1
                if entries > MAX_INVENTORY_FILES:
                    return {"directory": relative, "exists": True, "files": sorted(files, key=lambda f: f["path"]),
                            "complete": False, "limit": "Bounded result-tree entry inventory"}
                path = lt.safe_path(root, Path(child.path).relative_to(root).as_posix())
                if path.is_dir():
                    pending.append(path)
                    continue
                stat = path.stat()
                if not path.is_file() or stat.st_nlink != 1:
                    raise ValueError("Non-regular or hardlinked result evidence")
                if byte_count + stat.st_size > MAX_HASH_BYTES:
                    return {"directory": relative, "exists": True, "files": sorted(files, key=lambda f: f["path"]),
                            "complete": False, "limit": "Bounded hash-byte inventory"}
                before = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
                digest = lt.sha256(path)
                after = path.stat()
                if before != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                    raise ValueError("Result inventory input changed while hashing")
                files.append({"path": path.relative_to(root).as_posix(), "bytes": stat.st_size, "sha256": digest})
                byte_count += stat.st_size
    files.sort(key=lambda f: f["path"])
    return {"directory": relative, "exists": True, "files": files, "complete": True}


def capture(root: Path, output_relative: str) -> dict:
    output = lt.safe_path(root, output_relative)
    base = lt.safe_path(root, "build/ci-verification")
    if output == base or not output.is_relative_to(base) or not output.is_dir():
        raise ValueError("Use an existing dedicated verification output directory")
    logs = []
    for name in LOGS:
        path = lt.safe_path(root, (output / name).relative_to(root).as_posix())
        if not path.exists():
            continue
        stat = path.stat()
        if not path.is_file() or stat.st_nlink != 1:
            raise ValueError("Non-regular or hardlinked diagnostic log")
        if stat.st_size > MAX_LOG_BYTES:
            logs.append({"name": name, "bytes": stat.st_size, "inspected": False,
                         "limit": "Log exceeds bounded diagnostic input size"})
            continue
        before = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
        payload = path.read_bytes()
        after = path.stat()
        if before != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("Diagnostic input changed during readback")
        lines = payload.decode("utf-8", errors="replace").splitlines()
        excerpts = sections(lines) if name.endswith("gradle.log") or name == "apk-assembly.log" else []
        logs.append({"name": name, "bytes": stat.st_size, "sha256": hashlib.sha256(payload).hexdigest(),
                     "inspected": True, "excerpts": excerpts,
                     "excerpt_limit_may_omit_sections": len(excerpts) == MAX_EXCERPTS,
                     "tail": sanitized(lines[-40:]) if name == "emulator.log" else ""})
    android_results = []
    # These are the finite controller's modules, not a user-controlled path list.
    for module in lt.MINIMUM_MODULES["android-device"]:
        for relative in (f"{module}/build/intermediates/android_test_results/androidMain/connectedAndroidDeviceTest",
                         f"{module}/build/outputs/androidTest-results/connected/androidMain"):
            android_results.append(inventory(root, relative))
    return {"schema_version": 1, "recorded_utc": lt.utc_now(), "logs": logs,
            "android_result_file_inventories": android_results,
            "test_success_inferred": False, "full_logs_uploaded": False,
            "scope": "Bounded reviewed public-fixture diagnostics; not testcase evidence, a secret-scrubbing guarantee, native functionality or release certification"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = capture(lt.ROOT, args.output)
    target = lt.safe_path(lt.ROOT, args.output + "/failure-diagnostics.json")
    with target.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"Bounded failure capture refused: {type(error).__name__}", file=sys.stderr)
        sys.exit(2)
