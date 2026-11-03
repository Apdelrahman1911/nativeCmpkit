# SPDX-License-Identifier: Apache-2.0
"""Read-only boot handoff before the sole camera original-state capture.

Android's HOME resolver can change before Settings.FallbackHome has left the
activity hierarchy. A reference-shaped FallbackHome marker is an opportunity to
wait, NEVER proof of absence or permission to initialize Settings. The existing
strict all-activity parser, original double snapshot, native/scalar ownership,
reporter identity, native method and cleanup remain the admission gates.
"""
from __future__ import annotations

import hashlib
import math
from pathlib import PurePosixPath
import re
import subprocess

import android_camera_developer_prerequisite as camera

ACTIVITIES = ("shell", "dumpsys", "activity", "-p", "com.android.settings", "activities")
BUDGET_SECONDS = 60.0
CADENCE_SECONDS = 0.5


def fallback_marker_facts(payload: bytes) -> dict:
    """Fixed counts of reference syntax, not component/process ownership.

    Android15 ActivityRecord.toString has a first-use unterminated-name branch
    and a cached task/finishing/exiting branch. Both are recognized only for
    user0's exact canonical FallbackHome name. No row text, identifiers, other
    components, error text or command/environment data are returned.
    """
    camera.require(type(payload) is bytes and 0 < len(payload) <= camera.CONTROL_BYTES,
                   "A bounded ordinary activity observation is required")
    camera.require(not any(byte in payload for byte in (b"\r", b"\0", b"\x1b")),
                   "Unsafe boot activity observation")
    rows = payload.decode("utf-8").removesuffix("\n").split("\n")
    displays = []
    display_shapes_valid = True
    for row in rows:
        if row.lstrip(" ").startswith("Display #"):
            match = re.fullmatch(r"Display #(0|[1-9][0-9]{0,9}) \(activities from top to bottom\):", row)
            if match is None or int(match[1]) > 2147483647:
                display_shapes_valid = False
            else:
                displays.append(int(match[1]))
    outer_shape = (len(rows) >= 3 and rows[0] == camera.ACTIVITIES_HEADER and
                   rows.count(camera.ACTIVITIES_HEADER) == 1 and rows[-1] == "  (nothing)" and
                   rows.count("  (nothing)") == 1 and bool(displays) and
                   display_shapes_valid and len(displays) == len(set(displays)))
    marker_rows = [row for row in rows if "ActivityRecord{" in row]
    # The finishing branch includes its own '}', followed by the final '}'.
    descriptor = re.compile(
        r"ActivityRecord\{[0-9a-f]{1,8} u0 com\.android\.settings/\.FallbackHome"
        r"(?: t(-1|0|[1-9][0-9]{0,9})(?: f\})?(?: isExiting)?\})?"
    )
    fallback_rows = 0
    for row in marker_rows:
        if row.count("ActivityRecord{") != 1:
            continue
        match = descriptor.fullmatch(row[row.index("ActivityRecord{"):])
        if match is not None and (match[1] is None or -1 <= int(match[1]) <= 2147483647):
            fallback_rows += 1
    return {
        "activity_record_marker_rows": len(marker_rows),
        "reference_fallback_marker_rows": fallback_rows,
        "unqualified_marker_rows": len(marker_rows) - fallback_rows,
        "known_header_footer_and_displays": outer_shape,
        "only_reference_fallback_markers": outer_shape and bool(marker_rows) and fallback_rows == len(marker_rows),
        "detailed_body_grammar_certified": False,
        "activity_absence_inferred": False,
        "actual_image_producer_or_ownership_inferred": False,
    }


def wait_for_owned_boot_handoff(owner: camera.OwnedDeveloperPrerequisite) -> dict:
    """One cooperative60s read-only preflight; no startup/native-gate waiver.

    Every command is confined to the captured owned guest. The exact epoch,
    shell user and runtime are bracketed, command timeouts are clamped, late or
    backwards clocks refuse, and neither parser nor publication failures may
    admit a native test. Dumps without exclusively recognized marker syntax
    fail immediately. Detailed rows may only wait for a later STRICT empty dump;
    their complete producer grammar and actual owners are not certified.
    The original capture then independently repeats all its old checks.
    """
    camera.require(type(owner) is camera.OwnedDeveloperPrerequisite and
                   owner.original is None and not owner.closed and
                   owner.receipt["prepare_status"] == "not-started" and
                   owner.receipt.get("focus") == camera.FOCUS and
                   type(owner.receipt.get("api_level")) is int and owner.receipt["api_level"] == 35 and
                   owner.startup_deadline is None and owner.deadline is None and
                   not owner._pre_reporter_capture_attempted and
                   not vars(owner).get("_boot_handoff_attempted", False),
                   "Only one fresh sole-C1 preflight before original capture is admitted")
    owner._boot_handoff_attempted = True
    receipt = {
        "schema": "nativecmpkit.camera-boot-handoff.v1",
        "status": "running", "budget_seconds": BUDGET_SECONDS,
        "cadence_seconds": CADENCE_SECONDS, "activity_observations": 0,
        "fallback_wait_observations": 0, "strict_absence_observed": False,
        "read_only": True, "native_acceptance_inferred": False,
        "original_snapshot_or_scalar_values_inferred": False,
        "raw_rows_components_identifiers_or_environment_exported": False,
    }
    owner.receipt["boot_handoff_preflight"] = receipt
    last_clock = deadline = None

    def remaining() -> float:
        nonlocal last_clock
        now = owner.clock()
        camera.require(type(now) in (int, float) and math.isfinite(now) and now >= last_clock,
                       "Boot handoff clock changed or moved backwards")
        last_clock = now
        if now >= deadline:
            raise TimeoutError("Owned boot handoff exceeded its read-only budget")
        return deadline - now

    def control(*arguments: str, limit=camera.CONTROL_BYTES):
        value = owner.control(*arguments, timeout=min(10.0, remaining()), limit=limit)
        remaining()  # A late successful result is never admitted.
        return value

    def guard(expected_boot: str | None) -> str:
        remaining()
        owner.guest.verify_live()
        owner.devices()  # Existing exact entire-table/ready-serial gate.
        remaining()
        epoch = camera.line(control("shell", "cat", "/proc/sys/kernel/random/boot_id"), 512,
                            rb"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}").decode()
        camera.require(epoch != "00000000-0000-0000-0000-000000000000" and
                       (expected_boot is None or epoch == expected_boot),
                       "Boot handoff kernel lifetime changed")
        camera.require(camera.owned_avd_console_name(control("emu", "avd", "name"), owner.guest.name)
                       == owner.guest.name.encode(), "Boot handoff AVD ownership changed")
        camera.require(camera.line(control("shell", "id", "-u"), 512, rb"2000") == b"2000",
                       "Boot handoff requires the non-root shell UID2000")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                              ("sys.boot_completed", b"1")):
            camera.require(camera.line(control("shell", "getprop", key), 512, re.escape(expected)) == expected,
                           "Boot handoff runtime changed")
        camera.require(camera.line(control("shell", "getenforce"), 512, rb"Enforcing") == b"Enforcing",
                       "Boot handoff refuses a non-enforcing guest")
        camera.require(camera.line(control("shell", "am", "get-current-user"), 512, rb"0") == b"0",
                       "Boot handoff user changed")
        owner.guest.verify_live()
        remaining()
        return epoch

    try:
        last_clock = owner.clock()
        camera.require(type(last_clock) in (int, float) and math.isfinite(last_clock),
                       "Finite boot handoff clock required")
        deadline = last_clock + BUDGET_SECONDS
        owner.publish()  # Before the first observation; no native action exists here.
        epoch = guard(None)
        while True:
            guard(epoch)
            result = control(*ACTIVITIES)
            receipt["activity_observations"] += 1
            try:
                camera.parse_settings_activity_absence(result)
            except ValueError as error:
                try:
                    observation = activity_refusal(error)
                    if observation is not None:
                        receipt["parser_refusal"] = observation
                except BaseException:
                    pass  # Observation never replaces the original strict refusal.
                origin = camera.require_call_origin(error)
                # Only the unchanged interior-row refusal can be provisional.
                # Unsafe bytes, status/stderr, headers, duplicate displays and
                # truncation keep their exact original error and fail fast.
                if origin != {"source": "android_camera_developer_prerequisite.py",
                              "symbol": "parse_settings_activity_absence", "line": 307}:
                    raise
                facts = fallback_marker_facts(camera.result_bytes(result, camera.CONTROL_BYTES))
                receipt["last_marker_facts"] = facts
                receipt["last_interior_refusal_origin"] = origin
                if not facts["only_reference_fallback_markers"]:
                    raise
                receipt["fallback_wait_observations"] += 1
                guard(epoch)
                owner.publish()
                duration = min(CADENCE_SECONDS, remaining())
                before_sleep = last_clock
                owner.sleep(duration)
                remaining()
                camera.require(last_clock - before_sleep >= duration,
                               "Boot handoff sleep returned before its requested cadence")
            else:
                guard(epoch)
                receipt.update(status="passed", strict_absence_observed=True)
                remaining()
                owner.publish()  # Failure here must still refuse original capture.
                return dict(receipt)
    except BaseException as error:
        receipt["status"] = "failed"
        try:
            receipt["primary_require_call_origin"] = camera.require_call_origin(error)
        except BaseException:
            pass  # Unavailable callsite facts do not change failure or cleanup.
        try:
            owner.publish()
        except BaseException:
            pass  # Secondary journal failure never masks the primary refusal.
        raise


def activity_refusal(error: BaseException) -> dict | None:
    """Bounded facts from the genuine refusing parser's already-returned query.

    In camera495, the first boot Activity observation refused before the old
    interior-only observer could run. Inspect its real frame and exact SDK/guest
    query; do not repeat, trim, normalize, parse for acceptance, or expose rows.
    Missing envelope/rows are unavailable, never evidence of native absence.
    """
    if type(error) not in (ValueError, UnicodeDecodeError):
        return None
    trace = error.__traceback__
    for _ in range(64):
        if trace is None:
            return None
        if trace.tb_frame.f_code is camera.parse_settings_activity_absence.__code__:
            result = trace.tb_frame.f_locals.get("result")
            if (type(result) is not subprocess.CompletedProcess or type(result.args) is not list or
                    len(result.args) != 9 or any(type(arg) is not str for arg in result.args) or
                    tuple(result.args[1:]) != ("-s", camera.SERIAL, *ACTIVITIES) or
                    type(result.stdout) is not bytes or type(result.stderr) is not bytes or
                    len(result.stdout) + len(result.stderr) > camera.CONTROL_BYTES or
                    type(result.returncode) is not int or not -2147483648 <= result.returncode <= 2147483647):
                return None
            tool = PurePosixPath(result.args[0])
            if (not tool.is_absolute() or ".." in tool.parts or tool.name != "adb" or
                    tool.parent.name != "platform-tools" or
                    any(char in result.args[0] for char in ("\0", "\r", "\n", "\x1b"))):
                return None
            payload = result.stdout
            if trace.tb_frame.f_locals.get("payload", payload) is not payload:
                return None  # A changed CompletedProcess cannot describe the refused bytes.
            rows = trace.tb_frame.f_locals.get("rows")
            try:
                decoded = payload.decode("utf-8")
            except UnicodeError:
                decoded = None
            rows_available = (decoded is not None and type(rows) is list and
                              all(type(row) is str for row in rows) and
                              rows == decoded.removesuffix("\n").split("\n"))
            observation = {
                "schema": "nativecmpkit.camera-boot-activity-refusal.v1",
                "parser_frame_line": trace.tb_lineno,
                "require_call_origin": camera.require_call_origin(error),
                "stdout_bytes": len(payload), "stdout_sha256": hashlib.sha256(payload).hexdigest(),
                "stderr_bytes": len(result.stderr), "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
                "command_exit_code": result.returncode,
                "unsafe_control_bytes": any(byte in payload for byte in (b"\r", b"\0", b"\x1b")),
                "decoded_utf8": decoded is not None, "original_rows_available": rows_available,
                "read_only_returned_query": True, "new_queries_or_native_operations": 0,
                "parser_retried": False, "original_reader_still_refused": True,
                "activity_absence_verified": False, "actual_producer_or_cause_inferred": False,
                "raw_rows_identifiers_paths_or_environment_exported": False,
            }
            if rows_available:
                observation.update(
                    row_count=len(rows), header_occurrences=rows.count(camera.ACTIVITIES_HEADER),
                    footer_occurrences=rows.count("  (nothing)"),
                    empty_rows=rows.count(""),
                    original_header_footer_operands={
                        "minimum_three_rows": len(rows) >= 3,
                        "header": bool(rows) and rows[0] == camera.ACTIVITIES_HEADER,
                        "unique_header": rows.count(camera.ACTIVITIES_HEADER) == 1,
                        "footer": bool(rows) and rows[-1] == "  (nothing)",
                        "unique_footer": rows.count("  (nothing)") == 1,
                    },
                    observed_rows=[{
                        "index": index, "bytes": len(row.encode("utf-8")),
                        "sha256": hashlib.sha256(row.encode("utf-8")).hexdigest(),
                        "leading_ascii_spaces": len(row) - len(row.lstrip(" ")),
                        "trailing_ascii_spaces": len(row) - len(row.rstrip(" ")),
                        "ascii_only": row.isascii(), "empty": row == "",
                    } for index, row in enumerate(rows[:8])],
                )
            return observation
        trace = trace.tb_next
    return None
