# SPDX-License-Identifier: Apache-2.0
"""Observe one original live-leaf refusal, never parse, query or admit a task.

Camera630 failed the unchanged three-term require before APK/native work. Its
individual operands and returned row were not recorded. Observe only a future
actual registered terminal require and consistent already-returned query/locals.
Captured match/set facts are source-conditional observations, not instruction,
guest ownership, row provenance, registration, absence or root-cause proof.
No raw row, ID, leaf label, component, affinity or path is returned.
"""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
import re
import subprocess

import android_camera_developer_prerequisite as camera

MAX_FRAMES = 64
MAX_ROWS = 128
MAX_ROW_BYTES = 2048
GUARD = "Unknown live leaf task"
QUERY_ARGUMENTS = ("-s", camera.SERIAL, "shell", "am", "stack", "list")
BOUNDS = r"\[-?[0-9]+,-?[0-9]+]\[-?[0-9]+,-?[0-9]+]"
ROOT_PATTERN = r"RootTask id=([0-9]+) bounds=" + BOUNDS + r" displayId=[0-9]+ userId=[0-9]+"
CHILD_PATTERN = (r"  taskId=([0-9]+): ([^\s]+)(?: bounds=" + BOUNDS +
                 r")? userId=[0-9]+ visible=(true|false)(?: topActivity=ComponentInfo\{([^{}]+)})?")
FIXED_ROW_MARKERS = ("taskId=", ": ", " bounds=", " userId=", " visible=", " topActivity=ComponentInfo{")


def _original_frame(error):
    if (type(error) is not ValueError or type(error.args) is not tuple or len(error.args) != 1 or
            type(error.args[0]) is not str or error.args != (GUARD,)):
        return None
    previous, leaf, node = None, None, error.__traceback__
    for _ in range(MAX_FRAMES):
        if node is None:
            return None
        code = node.tb_frame.f_code
        if code is camera.parse_live_tasks.__code__:
            if leaf is not None:
                return None
            leaf = node
        if code is camera.require.__code__:
            if (leaf is None or previous is not leaf or node.tb_next is not None or
                    leaf.tb_frame.f_code.co_filename != code.co_filename or
                    type(leaf.tb_lineno) is not int or not 0 < leaf.tb_lineno < 20000 or
                    not any(start <= leaf.tb_lasti < stop and line == leaf.tb_lineno
                            for start, stop, line in leaf.tb_frame.f_code.co_lines())):
                return None
            values = node.tb_frame.f_locals
            if (type(values.get("condition")) is not bool or values["condition"] is not False or
                    type(values.get("message")) is not str or values["message"] != GUARD):
                return None
            return leaf, {"source": "android_camera_developer_prerequisite.py",
                          "symbol": "parse_live_tasks", "line": leaf.tb_lineno}
        previous, node = node, node.tb_next
    return None


def _captured_match(match, row, pattern, groups):
    """Inspect the original immutable re.Match, never call a regex matcher."""
    return (type(match) is re.Match and type(match.re) is re.Pattern and
            match.re.pattern == pattern and match.re.flags == re.UNICODE and
            match.re.groups == groups and match.string is row and
            match.span() == (0, len(row)))


def live_task_refusal(error: BaseException) -> dict | None:
    """Finite cooperative trace/input bounds, not a hard deadline or sandbox.

Nonordinary, foreign, changed, ambiguous or over-budget state is unavailable
(None), not absence/zero. No filesystem, shell, native, parser or regex query is
performed. The unchanged controller's primary failure and cleanup stay in charge.
"""
    original = _original_frame(error)
    if original is None:
        return None
    trace, origin = original
    values = trace.tb_frame.f_locals
    result, payload, rows = (values.get(name) for name in ("result", "payload", "rows"))
    if (type(result) is not subprocess.CompletedProcess or type(result.args) is not list or
            len(result.args) != len(QUERY_ARGUMENTS) + 1 or any(type(value) is not str for value in result.args) or
            tuple(result.args[1:]) != QUERY_ARGUMENTS or type(result.returncode) is not int or
            result.returncode != 0 or type(result.stdout) is not bytes or payload is not result.stdout or
            type(result.stderr) is not bytes or result.stderr != b"" or
            not 0 < len(payload) <= camera.CONTROL_BYTES or payload.count(b"\n") > MAX_ROWS or
            any(byte in payload for byte in (b"\r", b"\0", b"\x1b")) or
            type(rows) is not list or not 2 <= len(rows) <= MAX_ROWS or
            any(type(row) is not str for row in rows)):
        return None
    tool = PurePosixPath(result.args[0])
    if (not tool.is_absolute() or ".." in tool.parts or tool.name != "adb" or
            tool.parent.name != "platform-tools" or
            any(char in result.args[0] for char in ("\0", "\r", "\n", "\x1b"))):
        return None
    try:
        split_rows = payload.decode("utf-8").split("\n")
    except UnicodeError:
        return None
    if (rows != [row for row in split_rows if row] or
            any(len(row.encode("utf-8")) > MAX_ROW_BYTES for row in rows)):
        return None
    starts, number, start, block, root, row, child, roots, children = (
        values.get(name) for name in ("starts", "number", "start", "block", "root", "row", "child", "roots", "children"))
    if (type(values.get("bounds")) is not str or values["bounds"] != BOUNDS or type(starts) is not list or not starts or
            any(type(index) is not int or not 0 <= index < len(rows) for index in starts) or
            starts != sorted(set(starts)) or starts[0] != 0 or
            starts != [index for index, item in enumerate(rows) if item.startswith("RootTask id=")] or
            type(number) is not int or not 0 <= number < len(starts) or
            type(start) is not int or start != starts[number] or type(block) is not list or len(block) < 3 or
            type(row) is not str or type(roots) is not set or type(children) is not set or
            len(roots) != number + 1 or len(children) > MAX_ROWS or
            any(type(identifier) is not str or not identifier or not identifier.isascii() or
                not identifier.isdecimal() for identifier in roots | children)):
        return None
    end = starts[number + 1] if number + 1 < len(starts) else len(rows)
    if (len(block) != end - start or any(item is not rows[start + index] for index, item in enumerate(block)) or
            not _captured_match(root, block[0], ROOT_PATTERN, 1) or root[1] not in roots or
            not block[1].startswith(" configuration={") or not block[1].endswith("}")):
        return None
    # Never use value-based .index(): duplicate row bodies need not identify
    # the actual refusing iteration. The original block preserves references.
    row_indices = [index for index, item in enumerate(rows) if item is row]
    if len(row_indices) != 1 or not start + 2 <= row_indices[0] < end:
        return None
    rejected_index = row_indices[0]
    # Every earlier nonempty child row must have passed the unchanged unique-ID
    # gate to reach this frame. Check its count, not its IDs or a second parser.
    prior_leaf_rows = rejected_index - 2 * (number + 1)
    if len(children) != prior_leaf_rows or (child is not None and
            not _captured_match(child, row, CHILD_PATTERN, 4)):
        return None
    grammar = child is not None
    unique_id = child[1] not in children if grammar else None
    known_leaf = child[2] != "unknown" if unique_id is True else None
    operands = {"child_grammar_match": grammar, "child_id_not_previously_seen": unique_id,
                "leaf_label_not_literal_unknown": known_leaf}
    first_false = next((name for name, value in operands.items() if value is False), None)
    if first_false is None:
        return None  # Captured locals disagree with the original False require.
    row_payload = row.encode("utf-8")
    return {
        "schema": "nativecmpkit.camera-live-leaf-refusal.v1", "require_call_origin": origin,
        "guard": "live-leaf-admission", "original_require_condition": False,
        "captured_state_operand_matches": operands,
        "source_short_circuit_evaluated": {"child_grammar_match": True,
            "child_id_not_previously_seen": grammar, "leaf_label_not_literal_unknown": unique_id is True},
        "captured_state_first_false_operand": first_false,
        "payload_bytes": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "nonempty_row_count": len(rows), "split_row_count": len(split_rows),
        "omitted_empty_rows": split_rows.count(""), "root_block_count": len(starts),
        "rejected_block_index": number, "captured_seen_root_id_count": len(roots),
        "captured_seen_child_id_count": len(children), "source_conditional_prior_leaf_rows": prior_leaf_rows,
        "rejected_row": {"nonempty_index": rejected_index, "bytes": len(row_payload),
            "sha256": hashlib.sha256(row_payload).hexdigest(), "ascii_only": row.isascii(),
            "leading_ascii_spaces": len(row) - len(row.lstrip(" ")),
            "trailing_ascii_spaces": len(row) - len(row.rstrip(" ")),
            "fixed_marker_counts": {marker: row.count(marker) for marker in FIXED_ROW_MARKERS}},
        "original_live_frame_and_returned_query_bound": True,
        "captured_match_is_not_a_new_grammar_parse": True,
        "original_reader_still_refused": True, "new_queries_or_native_operations": 0,
        "parser_retried": False, "instruction_trace_or_atomic_freeze_verified": False,
        "live_task_absence_verified": False, "task_ownership_verified": False,
        "installed_image_or_HOME_provenance_verified": False, "original_scalar_or_cause_inferred": False,
        "native_acceptance_inferred": False, "admission_changed": False,
        "raw_rows_identifiers_leaf_labels_components_affinity_paths_or_environment_exported": False,
    }
