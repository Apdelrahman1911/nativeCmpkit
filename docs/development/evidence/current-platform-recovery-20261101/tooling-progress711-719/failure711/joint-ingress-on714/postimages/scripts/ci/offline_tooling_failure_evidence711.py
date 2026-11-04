"""Pure bounded lexical progress from an original failed-scope prefix.

This observes unittest-looking parent progress lines only. It neither identifies
an authenticated/current test nor infers a hang/failure cause. No raw output,
messages, parameters, environment, paths, filesystem, subprocess or network I/O.
The existing failure inventory remains separate and unchanged.
"""
import io
import re

MAX_INPUT_BYTES = 16 * 1024**2
MAX_LINES = 200000
MAX_LINE_BYTES = 4096
MAX_ID_BYTES = 384
LIMIT_FIELDS = ("input_byte_cap", "line_cap", "line_byte_cap", "non_utf8_line",
                "unqualified_progress", "credential_shaped_id")
_IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_]*"
_PROGRESS = re.compile(r"(test_[A-Za-z0-9_]*) \((" + _IDENTIFIER
                       + r"(?:\." + _IDENTIFIER + r")+)\) \.\.\.(.*)\Z")
_CREDENTIAL = re.compile(r"(?i)github_pat_|gh[pousr]_|(?:^|[._-])sk[-_]")


def observe_progress(output):
    """Return capped fixed-field metadata, never a raw or inferred last test."""
    if type(output) is not bytes:
        raise ValueError("Progress observation requires original byte data")
    prefix = output[:MAX_INPUT_BYTES]
    result = {"qualified_parent_progress_observations": 0,
              "terminal_token_observations": {"ok": 0, "FAIL": 0, "ERROR": 0},
              "unresolved_or_interleaved_progress_observations": 0,
              "last_qualified_parent_progress": None,
              "parsed_prefix_bytes": len(prefix),
              "limits_observed": {field: False for field in LIMIT_FIELDS}}
    result["limits_observed"]["input_byte_cap"] = len(output) > MAX_INPUT_BYTES
    offset = 0
    for index, raw in enumerate(io.BytesIO(prefix)):
        if index >= MAX_LINES:
            result["limits_observed"]["line_cap"] = True
            break
        original_offset, offset = offset, offset + len(raw)
        if len(raw) > MAX_LINE_BYTES:
            result["limits_observed"]["line_byte_cap"] = True
            continue
        try:
            line = raw.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            result["limits_observed"]["non_utf8_line"] = True
            continue
        # No lstrip/ANSI peeling: decorated output is not a qualified parent line.
        if not line.startswith("test_"):
            continue
        match = _PROGRESS.fullmatch(line)
        if (match is None or any(ord(char) < 32 or ord(char) == 127 for char in line)):
            result["limits_observed"]["unqualified_progress"] = True
            continue
        display, identifier, suffix = match.groups()
        if len(identifier) > MAX_ID_BYTES or display != identifier.rsplit(".", 1)[-1]:
            result["limits_observed"]["unqualified_progress"] = True
            continue
        if _CREDENTIAL.search(identifier):
            result["limits_observed"]["credential_shaped_id"] = True
            continue
        # Any interleaved stdout/status/parameter text is omitted, never parsed.
        token = suffix[1:] if suffix in (" ok", " FAIL", " ERROR") else "unresolved-or-interleaved"
        result["qualified_parent_progress_observations"] += 1
        if token in result["terminal_token_observations"]:
            result["terminal_token_observations"][token] += 1
        else:
            result["unresolved_or_interleaved_progress_observations"] += 1
        result["last_qualified_parent_progress"] = {
            "testcase_id": identifier, "result_token": token,
            "line_number": index + 1, "byte_offset": original_offset,
            "line_terminated": raw.endswith(b"\n")}
    return result
