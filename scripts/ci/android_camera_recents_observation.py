# SPDX-License-Identifier: Apache-2.0
"""Failure-only recent-task fingerprints; never a parser or an absence decision.

The actual camera482 request failed the existing compound recents require before
APK/native work. Inspect only its real traceback and fixed, already-returned
read-only query. Do not repeat the query, trim input, retry a parser, export rows,
or change the original failure. Android's source template is not proof of the
actual hosted payload or its cause.
"""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
import re
import subprocess

import android_camera_developer_prerequisite as camera

MAX_FRAMES = 64
MAX_ROW_OBSERVATIONS = 8
QUERY_ARGUMENTS = ("-s", camera.SERIAL, "shell", "dumpsys", "activity",
                   "-p", "com.android.settings", "recents")


def recents_refusal(error: BaseException) -> dict | None:
    """Observe one exact live refusing parse_recents frame, not caller metadata.

    Budgets are finite iteration/input bounds, not hard wall-clock guarantees.
    No filesystem, network, shell, process, registry or native operation occurs.
    Missing/foreign/unsafe/partial observations are unavailable, never zero.
    """
    if type(error) is not ValueError or error.args != ("Settings recent task absence is unproved",):
        return None
    origin = camera.require_call_origin(error)
    if (type(origin) is not dict or set(origin) != {"source", "symbol", "line"} or
            origin["source"] != "android_camera_developer_prerequisite.py" or
            origin["symbol"] != "parse_recents" or type(origin["line"]) is not int or
            not 0 < origin["line"] < 20000):
        return None
    trace = error.__traceback__
    for _ in range(MAX_FRAMES):
        if trace is None:
            return None
        if trace.tb_frame.f_code is camera.parse_recents.__code__:
            values = trace.tb_frame.f_locals
            result, payload, rows = (values.get(name) for name in ("result", "payload", "rows"))
            if (type(result) is not subprocess.CompletedProcess or type(result.args) is not list or
                    len(result.args) != 9 or any(type(value) is not str for value in result.args) or
                    tuple(result.args[1:]) != QUERY_ARGUMENTS or
                    type(result.stdout) is not bytes or payload is not result.stdout or
                    type(result.stderr) is not bytes or result.stderr != b"" or
                    type(result.returncode) is not int or result.returncode != 0 or
                    not 0 < len(payload) <= camera.CONTROL_BYTES or
                    any(byte in payload for byte in (b"\r", b"\0", b"\x1b")) or
                    type(rows) is not list or any(type(row) is not str for row in rows)):
                return None
            tool = PurePosixPath(result.args[0])
            if (not tool.is_absolute() or ".." in tool.parts or tool.name != "adb" or
                    tool.parent.name != "platform-tools" or
                    any(char in result.args[0] for char in ("\0", "\r", "\n", "\x1b"))):
                return None
            try:
                if rows != payload.decode("utf-8").removesuffix("\n").split("\n"):
                    return None
            except UnicodeError:
                return None
            tail = rows[5:]
            matches = {
                "minimum_five_rows": len(rows) >= 5,
                "header": bool(rows) and rows[0] == camera.RECENTS_HEADER,
                "unique_header": rows.count(camera.RECENTS_HEADER) == 1,
                "unsigned_uid": len(rows) > 1 and re.fullmatch(r"mRecentsUid=[0-9]+", rows[1]) is not None,
                "component_info": len(rows) > 2 and re.fullmatch(r"mRecentsComponent=ComponentInfo\{[^{}]+}", rows[2]) is not None,
                "freeze_flag": len(rows) > 3 and re.fullmatch(r"mFreezeTaskListReordering=(true|false)", rows[3]) is not None,
                "pending_timeout_flag": len(rows) > 4 and re.fullmatch(r"mFreezeTaskListReorderingPendingTimeout=(true|false)", rows[4]) is not None,
                "exact_tail": tail in ([], ["  (nothing)"]),
            }
            # These are the original compound operands, not a second parser.
            if all(matches.values()):
                return None  # Refusal/locals disagreement must not invent facts.
            return {
                "schema": "nativecmpkit.camera-recents-refusal.v1",
                "require_call_origin": dict(origin),
                "payload_bytes": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "row_count": len(rows), "header_occurrences": rows.count(camera.RECENTS_HEADER),
                "original_operand_matches": matches,
                "tail_rows": len(tail), "tail_empty_rows": tail.count(""),
                "tail_ascii_blank_rows": sum(not row.strip(" \t") for row in tail),
                "tail_nothing_rows": tail.count("  (nothing)"),
                "observed_rows": [{
                    "index": index, "bytes": len(row.encode("utf-8")),
                    "sha256": hashlib.sha256(row.encode("utf-8")).hexdigest(),
                    "leading_ascii_spaces": len(row) - len(row.lstrip(" ")),
                    "trailing_ascii_spaces": len(row) - len(row.rstrip(" ")),
                    "ascii_only": row.isascii(), "empty": row == "",
                } for index, row in enumerate(rows[:MAX_ROW_OBSERVATIONS])],
                "read_only_returned_query": True, "new_queries_or_native_operations": 0,
                "parser_retried": False, "original_reader_still_refused": True,
                "recents_absence_verified": False, "original_scalar_or_cause_inferred": False,
                "raw_rows_identifiers_paths_or_environment_exported": False,
            }
        trace = trace.tb_next
    return None
