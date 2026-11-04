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
MAX_TAIL_ROWS = 64
MAX_TAIL_ROW_BYTES = 2048
QUERY_ARGUMENTS = ("-s", camera.SERIAL, "shell", "dumpsys", "activity",
                   "-p", "com.android.settings", "recents")


def tail_structure(rows: list[str]) -> dict:
    """Count bounded, source-template row shapes without accepting any task.

    Android-15 RecentTasks.dump prints a raw package-filtered list; its filter
    also considers mCallingPackage. Task.dump/toString supplies these templates.
    They are NOT provenance for the installed image, a complete task parser or
    evidence that a matching HOME record is safe to ignore. Never export actual
    task/object IDs, component/intent text, callers, paths or unknown row bodies.
    Budgets are cooperative finite work/input bounds, not hard time guarantees.
    """
    if type(rows) is not list or any(type(row) is not str for row in rows):
        return {"available": False, "reason": "nonordinary-tail", "admission_changed": False}
    if len(rows) > MAX_TAIL_ROWS:
        return {"available": False, "reason": "tail-row-budget", "admission_changed": False}
    if any(len(row.encode("utf-8")) > MAX_TAIL_ROW_BYTES for row in rows):
        return {"available": False, "reason": "row-byte-budget", "admission_changed": False}
    task_types = {kind: 0 for kind in ("standard", "home", "recents", "assistant", "dream", "undefined")}
    roles = {kind: 0 for kind in (
        "raw_header", "visible_header", "nothing", "hidden_tasks", "task_header", "identity",
        "affinity", "intent", "affinity_intent", "original_component", "component", "activity_policy",
        "root_policy", "activities", "task_ids", "pip_child", "visibility", "resize_policy", "last_active",
    )}
    identity_matches = {kind: 0 for kind in (
        "user_zero", "effective_uid_1000", "caller_uid_0", "caller_uid_1000", "caller_uid_2000",
        "caller_android", "caller_settings", "caller_shell", "setup_true", "feature_null",
    )}
    component_rows = {"settings_fallback_home": 0, "settings_development": 0}
    header_ids, dump_ids = [], []
    empty_activities = unknown = 0
    # Recognition only: no pattern is an admission or normalization operation.
    patterns = (
        ("affinity", r"    affinity=[^\r\n]{1,1800}"),
        ("intent", r"    intent=\{[^\r\n]{0,1800}}"),
        ("affinity_intent", r"    affinityIntent=\{[^\r\n]{0,1800}}"),
        ("original_component", r"    origActivity=[^\s{}]{1,1800}"),
        ("component", r"    mActivityComponent=[^\s{}]{1,1800}"),
        ("activity_policy", r"    autoRemoveRecents=(true|false) isPersistable=(true|false) activityType=[0-9]{1,10}"),
        ("root_policy", r"    rootWasReset=(true|false) mNeverRelinquishIdentity=(true|false) mReuseTask=(true|false) mLockTaskAuth=[^\s]{1,128}"),
        ("activities", r"    Activities=\[[^\r\n]{0,1800}]"),
        ("pip_child", r"    hasChildPipActivity=(true|false)"),
        ("visibility", r"    mHasBeenVisible=(true|false)"),
        ("resize_policy", r"    mResizeMode=[^\s]{1,128} mSupportsPictureInPicture=(true|false) isResizeable=(true|false)"),
        ("last_active", r"    lastActiveTime=[0-9]{1,20} \(inactive for [0-9]{1,20}s\)"),
    )
    for row in rows:
        exact_role = {
            "  Recent tasks:": "raw_header",
            "  Visible recent tasks (most recent first):": "visible_header",
            "  (nothing)": "nothing",
        }.get(row)
        if exact_role is not None:
            roles[exact_role] += 1
            continue
        header = re.fullmatch(
            r"  \* Recent #[0-9]{1,10}: Task\{[a-f0-9]{1,16} #([1-9][0-9]{0,9}) "
            r"type=(standard|home|recents|assistant|dream|undefined)(?: (?:A|I|aI)=[^{}\r\n]{1,256})?}", row)
        if header is not None:
            roles["task_header"] += 1
            task_types[header[2]] += 1
            header_ids.append(int(header[1]) if int(header[1]) <= 2147483647 else None)
            continue
        identity = re.fullmatch(
            r"    userId=([0-9]{1,10}) effectiveUid=(\S{1,128}) mCallingUid=(\S{1,128}) "
            r"mUserSetupComplete=(true|false) mCallingPackage=(\S{1,128}) mCallingFeatureId=(\S{1,128})", row)
        if identity is not None:
            roles["identity"] += 1
            values = {
                "user_zero": identity[1] == "0", "effective_uid_1000": identity[2] == "1000",
                "caller_uid_0": identity[3] == "0", "caller_uid_1000": identity[3] == "1000",
                "caller_uid_2000": identity[3] == "2000", "setup_true": identity[4] == "true",
                "caller_android": identity[5] == "android", "caller_settings": identity[5] == "com.android.settings",
                "caller_shell": identity[5] == "com.android.shell", "feature_null": identity[6] == "null",
            }
            for key, matches in values.items():
                identity_matches[key] += int(matches)
            continue
        ids = re.fullmatch(r"    taskId=([1-9][0-9]{0,9}) rootTaskId=([1-9][0-9]{0,9})", row)
        if ids is not None:
            roles["task_ids"] += 1
            dump_ids.append(int(ids[1]) if max(int(ids[1]), int(ids[2])) <= 2147483647 else None)
            continue
        if re.fullmatch(r"mHiddenTasks=\[[^\r\n]{0,1800}]", row) is not None:
            roles["hidden_tasks"] += 1
            continue
        for role, pattern in patterns:
            if re.fullmatch(pattern, row) is not None:
                roles[role] += 1
                empty_activities += int(row == "    Activities=[]")
                component_rows["settings_fallback_home"] += int(row == "    mActivityComponent=com.android.settings/.FallbackHome")
                component_rows["settings_development"] += int(row == "    mActivityComponent=com.android.settings/.Settings$DevelopmentSettingsActivity")
                break
        else:
            unknown += 1
    ids_match = None
    if len(header_ids) == len(dump_ids) == 1 and header_ids[0] is not None and dump_ids[0] is not None:
        ids_match = header_ids[0] == dump_ids[0]
    return {
        "available": True, "schema": "nativecmpkit.camera-recents-tail-shapes.v1",
        "tail_rows_observed": len(rows), "known_row_role_counts": roles, "unknown_rows": unknown,
        "task_type_rows": task_types, "identity_rows": roles["identity"], "identity_matches": identity_matches,
        "fixed_component_rows": component_rows, "empty_activities_rows": empty_activities,
        "single_task_header_dump_ids_match": ids_match,
        "task_ownership_verified": False, "system_image_provenance_verified": False, "admission_changed": False,
    }


def recents_refusal(error: BaseException) -> dict | None:
    """Observe one exact live refusing parse_recents frame, not caller metadata.

    Budgets are finite iteration/input bounds, not hard wall-clock guarantees.
    No filesystem, network, shell, process, registry or native operation occurs.
    Missing/foreign/unsafe/partial observations are unavailable, never zero.
    """
    if type(error) is not ValueError:
        return None
    if error.args != ("Settings recent task absence is unproved",):
        from android_camera_home_refusal_observation import home_refusal
        return home_refusal(error)
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
                "tail_structure": tail_structure(tail),
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
