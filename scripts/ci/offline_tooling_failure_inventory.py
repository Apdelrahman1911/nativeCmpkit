"""Bounded metadata from one original unittest failure output; never eligibility.

Identifiers and frames are conservatively lexical observations, not authenticated
test/source provenance. Subtest parameters, messages and absolute path prefixes
are never returned. No filesystem, environment, subprocess or network access.
"""
import io
import json
import re

SCHEMA = "nativecmpkit-offline-failure-inventory-v1"
PREFIX = "[offline-failure-inventory] "
MAX_INPUT_BYTES = 16 * 1024**2
MAX_LINES = 200000
MAX_LINE_BYTES = 4096
MAX_RECORDS = 256
MAX_PUBLIC_BYTES = 65536
MAX_ID_BYTES = 384
MAX_SOURCE_BYTES = 192
MAX_NUMBER = 100000

_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_ID = re.compile(_IDENTIFIER + r"(?:\." + _IDENTIFIER + r")*\Z")
_HEADER = re.compile(r"(FAIL|ERROR): (" + _IDENTIFIER + r") \(([^)]+)\)(.*)\Z")
_FRAME = re.compile(r'  File "([^"\r\n]+)", line ([0-9]{1,6})(?:, in ' + _IDENTIFIER + r")?\Z")
_CLASS = re.compile(r"(" + _IDENTIFIER + r"(?:\." + _IDENTIFIER + r")*)(?::.*)?\Z")
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PHASES = {"setUpClass", "tearDownClass", "setUpModule", "tearDownModule"}


def _credential_shaped(value):
    # Do not return common credential-shaped strings even in purported IDs.
    return bool(re.search(r"(?i)github_pat_|gh[pousr]_|(?:^|[._-])sk[-_]", value))


def _source(path, line):
    if "\\" in path or line <= 0 or line > MAX_NUMBER:
        return None
    parts = path.split("/")
    starts = [i for i, part in enumerate(parts) if part in ("scripts", "tests")]
    if len(starts) != 1:
        return None
    relative = "/".join(parts[starts[0]:])
    leaf = parts[-1]
    if (len(relative) > MAX_SOURCE_BYTES or _credential_shaped(relative)
            or len(parts[starts[0]:]) < 3 or not leaf.endswith(".py")
            or re.fullmatch(_IDENTIFIER, leaf[:-3]) is None
            or any(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", part) is None
                   for part in parts[starts[0]:-1])):
        return None
    return {"file": relative, "line": line}


def _error_class(line):
    match = _CLASS.fullmatch(line)
    if match is None:
        return None
    name = match[1].rsplit(".", 1)[-1]
    if len(name) > 96 or _credential_shaped(match[1]):
        return None
    if (re.fullmatch(r"[A-Z][A-Za-z0-9_]*(?:Error|Exception|Failure)", name)
            or name in {"Exception", "BaseException", "SystemExit", "KeyboardInterrupt", "GeneratorExit", "StopIteration",
                        "StopAsyncIteration", "ExceptionGroup", "BaseExceptionGroup"}):
        return name
    return None


def _header(line):
    match = _HEADER.fullmatch(line)
    if match is None:
        return None
    kind, display, identifier, suffix = match.groups()
    if (len(identifier) > MAX_ID_BYTES or _ID.fullmatch(identifier) is None
            or _credential_shaped(identifier) or any(ord(char) < 32 or ord(char) == 127 for char in line)):
        return None
    if display in _PHASES:
        if display.endswith("Class") and "." not in identifier:
            return None
        phase = display
    elif identifier.startswith("unittest.loader._FailedTest.") and display == identifier.rsplit(".", 1)[-1]:
        phase = "loader"
    elif display.startswith("test_") and "." in identifier and display == identifier.rsplit(".", 1)[-1]:
        phase = "test"
    else:
        return None
    # Keep the parent ID only. Never parse or return bracket/parenthesis payloads.
    subtest = bool(suffix)
    if suffix and (phase != "test" or not suffix.startswith((" (", " [")) or not suffix.endswith((")", "]"))):
        return None
    return {"kind": kind, "testcase_id": identifier, "phase": phase,
            "subtest": subtest, "occurrences": 1, "source": None, "error_class": None}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def failure_inventory(output):
    """Return only capped identifier-level metadata, with explicit incompleteness."""
    reasons, records, counts, accepted = set(), {}, {"FAIL": 0, "ERROR": 0}, {"FAIL": 0, "ERROR": 0}
    summaries, ran, pending = [], 0, None

    def finish():
        nonlocal pending
        if pending is None:
            return
        record = pending["record"]
        record["source"] = pending["frame"]
        if pending["traceback"] and len(pending["classes"]) == 1:
            record["error_class"] = pending["classes"][0]
        key = (record["kind"], record["testcase_id"], record["phase"], record["subtest"])
        if key in records:
            existing = records[key]
            existing["occurrences"] += 1
            if not record["subtest"]:
                reasons.add("duplicate-header")
            for field in ("source", "error_class"):
                if existing[field] != record[field]:
                    existing[field] = None
        elif len(records) < MAX_RECORDS:
            records[key] = record
        else:
            reasons.add("record-cap")
        pending = None

    if type(output) is not bytes:
        reasons.add("invalid-input-type")
        output = b""
    if len(output) > MAX_INPUT_BYTES:
        reasons.add("input-byte-cap")
        output = output[:MAX_INPUT_BYTES]
    for index, raw in enumerate(io.BytesIO(output)):
        if index >= MAX_LINES:
            reasons.add("line-cap")
            break
        if len(raw) > MAX_LINE_BYTES:
            reasons.add("line-byte-cap")
            finish()
            continue
        try:
            line = raw.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            reasons.add("non-utf8-output")
            finish()
            continue
        plain = _ANSI.sub("", line).lstrip(" \t")
        is_header = plain.startswith(("FAIL:", "ERROR:"))
        is_summary = plain.startswith("FAILED")
        if (is_header or is_summary or plain.startswith("Ran ")) and plain != line:
            reasons.add("decorated-output")
        if is_header:
            finish()
            kind = "FAIL" if plain.startswith("FAIL:") else "ERROR"
            counts[kind] += 1
            record = _header(plain)
            if record is None:
                reasons.add("unqualified-header")
            else:
                accepted[kind] += 1
                pending = {"record": record, "frame": None, "traceback": False, "classes": []}
        elif is_summary:
            finish()
            declared = {"FAIL": 0, "ERROR": 0}
            parts = plain[8:-1].split(", ") if plain.startswith("FAILED (") and plain.endswith(")") else []
            seen = set()
            for part in parts:
                field = re.fullmatch(r"(failures|errors)=([0-9]{1,6})", part)
                if field is None or field[1] in seen or int(field[2]) > MAX_NUMBER:
                    reasons.add("unqualified-summary")
                    continue
                seen.add(field[1])
                declared["FAIL" if field[1] == "failures" else "ERROR"] = int(field[2])
            if not seen or not sum(declared.values()):
                reasons.add("unqualified-summary")
            summaries.append(declared)
        elif re.fullmatch(r"Ran [0-9]{1,6} tests? in [0-9.]+s", plain):
            ran += 1
        elif pending is not None:
            if line == "Traceback (most recent call last):":
                pending["traceback"] = True
            elif line.startswith('  File "'):
                frame = _FRAME.fullmatch(line)
                pending["frame"] = _source(frame[1], int(frame[2])) if frame else None
            elif pending["traceback"]:
                name = _error_class(line)
                if name is not None and len(pending["classes"]) < 2:
                    pending["classes"].append(name)
    finish()
    if len(summaries) != 1 or ran != 1:
        reasons.add("missing-or-ambiguous-summary")
    declared = summaries[0] if len(summaries) == 1 else None
    if declared != counts or accepted != counts:
        reasons.add("summary-header-count-mismatch")
    result = {"schema": SCHEMA, "diagnostic_only": True, "status": "complete",
              "reason_codes": sorted(reasons), "header_counts": counts,
              "qualified_header_counts": accepted, "declared_counts": declared,
              "subtest_parameters_omitted": True, "records": list(records.values())}
    if reasons:
        result["status"] = "partial" if result["records"] else "unknown"
    while len((PREFIX + _canonical(result)).encode("ascii")) > MAX_PUBLIC_BYTES and result["records"]:
        result["records"].pop()
        reasons.add("public-byte-cap")
        result["reason_codes"] = sorted(reasons)
        result["status"] = "partial" if result["records"] else "unknown"
    return result


def failure_inventory_line(output):
    result = failure_inventory(output)
    line = PREFIX + _canonical(result)
    if len(line.encode("ascii")) > MAX_PUBLIC_BYTES:
        # Only fixed metadata remains; never truncate into raw/invalid JSON.
        line = PREFIX + _canonical({"schema": SCHEMA, "diagnostic_only": True, "status": "unknown",
                                    "reason_codes": ["public-byte-cap"], "records": []})
    return line
