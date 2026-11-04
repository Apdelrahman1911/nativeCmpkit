"""Exact focused JUnit report gate; not native authenticity or release proof."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
import xml.etree.ElementTree as ET


EXPECTED_CLASS = "nativecmpkit.consumer.PublishedNativeConsumerTest"
EXPECTED_METHODS = (
    "pickerNativeLibraryLoadsAndInitializes",
    "packagedPickerCreatesAndReleasesValidHandles",
    "shareNativeLibraryLoadsAndReportsActualHostCapability",
)
EXPECTED_FILE = f"TEST-{EXPECTED_CLASS}.xml"
MAX_XML_BYTES = 4 * 1024 * 1024


class InvalidNativeResults(ValueError):
    pass


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _read_xml(path: Path) -> bytes:
    descriptor = None
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_XML_BYTES:
            raise InvalidNativeResults("Focused XML must be one bounded regular, nonlinked file")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
                             | getattr(os, "O_BINARY", 0))
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or _identity(opened) != _identity(before):
            raise InvalidNativeResults("Focused XML was replaced before opening")
        stream = os.fdopen(descriptor, "rb")
        descriptor = None
        with stream:
            payload = stream.read(MAX_XML_BYTES + 1)
            held = os.fstat(stream.fileno())
        after = path.lstat()
        if len(payload) != before.st_size or _identity(before) != _identity(held) or _identity(before) != _identity(after):
            raise InvalidNativeResults("Focused XML changed or exceeded its bound during inspection")
        return payload
    except OSError as exc:
        raise InvalidNativeResults("Could not read the task-owned focused XML") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def verify(results: Path, invocation: str) -> dict:
    try:
        canonical = str(uuid.UUID(invocation))
    except (ValueError, AttributeError, TypeError) as exc:
        raise InvalidNativeResults("A full independently supplied invocation UUID is required") from exc
    if canonical != invocation or results.name != invocation:
        raise InvalidNativeResults("Focused XML directory must match the exact invocation UUID")
    if not results.is_dir() or results.is_symlink():
        raise InvalidNativeResults("Fresh focused XML directory is missing or linked")
    try:
        paths = []
        for count, entry in enumerate(results.iterdir(), 1):
            if count > 16 or entry.is_symlink() or entry.is_dir():
                raise InvalidNativeResults("Focused JUnit output must be bounded, flat and nonlinked")
            if entry.suffix == ".xml":
                paths.append(entry)
                if len(paths) > 1:
                    raise InvalidNativeResults("Exactly one owning native-consumer XML is required; foreign results refuse")
    except OSError as exc:
        raise InvalidNativeResults("Could not inspect the task-owned focused results directory") from exc
    if len(paths) != 1 or paths[0].relative_to(results).as_posix() != EXPECTED_FILE:
        raise InvalidNativeResults("Exactly one owning native-consumer XML is required; empty/foreign results refuse")
    payload = _read_xml(paths[0])
    try:
        text = payload.decode("utf-8")
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", text, re.I):
            raise InvalidNativeResults("DTD/entity declarations are forbidden in focused XML")
        suite = ET.fromstring(text)
    except (UnicodeError, ET.ParseError) as exc:
        raise InvalidNativeResults("Focused XML is not a valid UTF-8 JUnit report") from exc
    if suite.tag != "testsuite" or suite.get("name") != EXPECTED_CLASS:
        raise InvalidNativeResults("Focused suite must be the exact native consumer class")
    counts = {"tests": "3", "failures": "0", "errors": "0", "skipped": "0"}
    if any(suite.get(name) != value for name, value in counts.items()):
        raise InvalidNativeResults("Focused suite must report exactly three methods and zero failures/errors/skips")
    if any(node.tag in {"failure", "error", "skipped"} for node in suite.iter()):
        raise InvalidNativeResults("Failure/error/skip elements cannot hide behind passing suite counters")
    if any(node.tag not in {"testcase", "properties", "system-out", "system-err"} for node in suite):
        raise InvalidNativeResults("Unrecognized focused suite elements refuse")
    cases = list(suite.findall("testcase"))
    identities = [(case.get("classname"), case.get("name")) for case in cases]
    expected = {(EXPECTED_CLASS, name) for name in EXPECTED_METHODS}
    if len(identities) != 3 or len(set(identities)) != 3 or set(identities) != expected:
        raise InvalidNativeResults("All three exact native method identities must occur once, with no foreign methods")
    if any(child.tag not in {"properties", "system-out", "system-err"} for case in cases for child in case):
        raise InvalidNativeResults("Unrecognized focused testcase elements refuse")
    allowed_tags = {"testsuite", "testcase", "properties", "property", "system-out", "system-err"}
    if len(list(suite.iter("testsuite"))) != 1 or len(list(suite.iter("testcase"))) != 3 or any(
            node.tag not in allowed_tags for node in suite.iter()):
        raise InvalidNativeResults("Nested or unrecognized foreign JUnit elements cannot hide in focused output")
    return {
        "schema_version": 1, "success": True, "invocation_id": invocation,
        "reported_method_count": 3, "methods": list(EXPECTED_METHODS),
        "xml_file": EXPECTED_FILE, "xml_bytes": len(payload), "xml_sha256": hashlib.sha256(payload).hexdigest(),
        "release_readiness_certified": False,
        "scope": "Exact focused JUnit report inspection; not native authenticity, minimum-platform, full21/API-ABI/legal/release certification",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--invocation-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        print("Result receipt already exists; preserve it and use a fresh invocation", file=sys.stderr)
        return 1
    try:
        receipt = verify(args.results_dir, args.invocation_id)
        code = 0
    except InvalidNativeResults as exc:
        receipt = {"schema_version": 1, "success": False, "invocation_id": args.invocation_id,
                   "release_readiness_certified": False, "error": str(exc)}
        code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
