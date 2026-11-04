# SPDX-License-Identifier: Apache-2.0
"""Observe the original HOME-parser refusal, never retry or admit its payload.

Camera576 refused in a separate pure-parser module not recognized by the older
prerequisite require-origin recorder. This observer accepts only that module's
actual terminal require and registered caller code. It emits bounded source
locations, hashes and fixed predicate/row-role facts, never rows, IDs or paths.
Query exit, guest custody and restoration remain independent controller checks.
"""
from __future__ import annotations

import hashlib
import re

import android_camera_home_baseline as home

MAX_FRAMES = 64
MAX_ROWS = 70
MAX_OBSERVED_ROWS = 8
GUARDS = {
    "Bounded completed recent-task payload required": ("parse_recent_home_baseline", "payload-bound"),
    "Unsafe recent-task bytes": ("parse_recent_home_baseline", "ascii-bytes"),
    "Exact complete recent-task row count required": ("parse_recent_home_baseline", "recent-row-count"),
    "Exact complete recent-task framing required": ("parse_recent_home_baseline", "recent-framing"),
    "Only the complete raw task list can preserve a HOME baseline": ("parse_recent_home_baseline", "raw-task-header"),
    "Complete bounded ASCII fallback HOME task required": ("parse_home_task", "home-row-count-or-bytes"),
    "Exact fallback HOME header required": ("parse_home_task", "home-header"),
    "Fallback HOME rank/task ID overflow": ("parse_home_task", "home-header-id-bounds"),
    "Exact bootstrap user/UID/caller required": ("parse_home_task", "bootstrap-identity"),
    "Exact HOME affinity/intent/component required": ("parse_home_task", "home-component"),
    "Exact printed HOME policies required": ("parse_home_task", "home-policy"),
    "A live or nested Activity cannot be an empty HOME baseline": ("parse_home_task", "home-activities"),
    "Exact bounded matching leaf and preserved root identities required": ("parse_home_task", "home-task-id-bounds"),
    "Exact empty HOME child/visibility/resize policies required": ("parse_home_task", "home-child-policy"),
    "Exact bounded HOME clock required": ("parse_home_task", "home-clock"),
}


def _original_frames(error):
    if (type(error) is not ValueError or type(error.args) is not tuple or len(error.args) != 1 or
            type(error.args[0]) is not str or error.args[0] not in GUARDS):
        return None
    expected_symbol, guard = GUARDS[error.args[0]]
    previous, node, recent, task = None, error.__traceback__, None, None
    for _ in range(MAX_FRAMES):
        if node is None:
            return None
        code = node.tb_frame.f_code
        if code is home.parse_recent_home_baseline.__code__:
            if recent is not None:
                return None
            recent = node
        if code is home.parse_home_task.__code__:
            if task is not None:
                return None
            task = node
        if code is home.require.__code__:
            if previous is None or node.tb_next is not None or recent is None:
                return None
            caller = previous.tb_frame.f_code
            function = home.parse_recent_home_baseline if expected_symbol == "parse_recent_home_baseline" else home.parse_home_task
            if (caller is not function.__code__ or caller.co_filename != code.co_filename or
                    type(previous.tb_lineno) is not int or not 0 < previous.tb_lineno < 20000 or
                    not any(start <= previous.tb_lasti < stop and line == previous.tb_lineno
                            for start, stop, line in caller.co_lines())):
                return None
            values = node.tb_frame.f_locals
            if (values.get("message") != error.args[0] or type(values.get("condition")) is not bool or
                    values["condition"] is not False):
                return None
            if (expected_symbol == "parse_home_task") != (task is not None):
                return None
            return ({"source": "android_camera_home_baseline.py", "symbol": expected_symbol,
                     "line": previous.tb_lineno}, guard, recent, task)
        previous, node = node, node.tb_next
    return None


def _task_operand_facts(rows):
    if len(rows) != 13 or any(len(row) > home.MAX_ROW_LENGTH for row in rows):
        return {"available": False, "reason": "home-row-budget"}
    header, ids, clock = home.HEADER.fullmatch(rows[0]), home.IDS.fullmatch(rows[8]), home.LAST_ACTIVE.fullmatch(rows[12])
    return {"available": True, "matches": {
        "home_header": header is not None,
        "header_rank_and_task_bounds": header is not None and int(header[1]) <= home.MAX_INT and int(header[3]) <= home.MAX_INT,
        "bootstrap_identity": rows[1] == "    userId=0 effectiveUid=1000 mCallingUid=0 mUserSetupComplete=false mCallingPackage=null mCallingFeatureId=null",
        "home_affinity": header is not None and rows[2] == "    affinity=" + header[4],
        "home_intent": home.INTENT.fullmatch(rows[3]) is not None,
        "home_component": rows[4] == "    mActivityComponent=com.android.settings/.FallbackHome",
        "activity_policy": home.POLICY.fullmatch(rows[5]) is not None,
        "root_policy": home.ROOT_POLICY.fullmatch(rows[6]) is not None,
        "root_policy_print_condition": rows[6] != "    rootWasReset=false mNeverRelinquishIdentity=false mReuseTask=false mLockTaskAuth=LOCK_TASK_AUTH_PINNABLE",
        "empty_activities": rows[7] == "    Activities=[]",
        "task_id_matches_header": ids is not None and header is not None and int(ids[1]) == int(header[3]),
        "root_task_id_bound": ids is not None and int(ids[2]) <= home.MAX_INT,
        "empty_pip_child": rows[9] == "    hasChildPipActivity=false",
        "visibility_policy": re.fullmatch(r"    mHasBeenVisible=(true|false)", rows[10]) is not None,
        "resize_policy": home.RESIZE_POLICY.fullmatch(rows[11]) is not None,
        "clock_shape_and_bounds": clock is not None and int(clock[1]) <= home.MAX_LONG and int(clock[2]) <= home.MAX_LONG,
    }}


def home_refusal(error: BaseException) -> dict | None:
    """Finite cooperative traceback/input work, not a hard deadline or sandbox.

Missing, modified, nonordinary, unsafe or over-budget inputs return unavailable
(None), not absence/zero. No filesystem, shell, native or parser call occurs.
The original failed parser frame binds the bytes; it is not a separate witness
that an adb command completed or that any task belongs to this owned guest.
"""
    original = _original_frames(error)
    if original is None:
        return None
    origin, guard, recent, task = original
    values = recent.tb_frame.f_locals
    payload, rows = values.get("payload"), values.get("rows")
    if (type(payload) is not bytes or not 0 < len(payload) <= home.MAX_REPLY_BYTES or
            any(c != 10 and not 32 <= c <= 126 for c in payload) or
            payload.count(b"\n") > MAX_ROWS or type(rows) is not list or
            not 1 <= len(rows) <= MAX_ROWS or any(type(row) is not str for row in rows) or
            rows != payload.decode("ascii").removesuffix("\n").split("\n")):
        return None
    task_rows = rows[6:]
    if task is not None:
        live = task.tb_frame.f_locals.get("rows")
        if type(live) not in (list, tuple) or list(live) != task_rows:
            return None
    def field(index, pattern):
        return len(rows) > index and len(rows[index]) <= home.MAX_ROW_LENGTH and re.fullmatch(pattern, rows[index]) is not None
    uid = field(1, r"mRecentsUid=(0|[1-9][0-9]{0,9})")
    framing = {
        "header": rows[0] == "ACTIVITY MANAGER RECENT TASKS (dumpsys activity recents)",
        "uid_syntax": uid,
        "uid_bound": uid and int(rows[1].split("=", 1)[1]) <= home.MAX_INT,
        "component": field(2, r"mRecentsComponent=ComponentInfo\{[^{}]+}"),
        "freeze_flag": field(3, r"mFreezeTaskListReordering=(true|false)"),
        "pending_timeout_flag": field(4, r"mFreezeTaskListReorderingPendingTimeout=(true|false)"),
    }
    from android_camera_recents_observation import tail_structure
    return {
        "schema": "nativecmpkit.camera-home-baseline-refusal.v1",
        "require_call_origin": origin, "guard": guard,
        "payload_bytes": len(payload), "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "row_count": len(rows), "task_row_count": len(task_rows),
        "original_row_count_matches": len(rows) in (5, 6, 19),
        "original_row_lengths_match": all(len(row) <= home.MAX_ROW_LENGTH for row in rows),
        "original_framing_matches": framing,
        "raw_task_header_matches": len(rows) > 5 and rows[5] == "  Recent tasks:",
        "task_operand_facts": _task_operand_facts(task_rows),
        "tail_structure": tail_structure(rows[5:]),
        "observed_rows": [{"index": index, "bytes": len(row), "sha256": hashlib.sha256(row.encode("ascii")).hexdigest(),
                           "leading_ascii_spaces": len(row) - len(row.lstrip(" ")),
                           "trailing_ascii_spaces": len(row) - len(row.rstrip(" ")),
                           "empty": row == ""} for index, row in enumerate(rows[:MAX_OBSERVED_ROWS])],
        "original_live_parser_payload_bound": True,
        "new_queries_or_native_operations": 0, "parser_retried": False,
        "original_reader_still_refused": True, "recents_absence_verified": False,
        "query_exit_or_owner_inferred": False, "original_scalar_or_cause_inferred": False,
        "raw_rows_identifiers_paths_or_environment_exported": False,
    }
