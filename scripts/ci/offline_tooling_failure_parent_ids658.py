"""Bounded lexical FAIL/ERROR parent IDs from an already sampled failed prefix.

This is a diagnostic companion to offline_tooling_failure_evidence711. It reuses
that exact parent grammar and credential filter, not the older header inventory.
No ANSI/indent normalization, subtest/message/header/traceback parsing, source
lookup, environment, filesystem, subprocess or network access is performed.
Neither tokens nor IDs authenticate a test, completion, current method or cause.
Only newline-terminated parent lines may retain IDs; unterminated terminal-looking
suffixes are counted as omitted unqualified candidates. One bounded metadata JSON
may be written to the explicitly supplied stream.
"""
import io
import json
import re

import offline_tooling_failure_evidence711 as qualified

MAX_INPUT_BYTES = 16 * 1024**2
MAX_LINES = 200000
MAX_LINE_BYTES = 4096
MAX_ID_BYTES = 384
MAX_UNIQUE_IDS = 256
MAX_PUBLIC_BYTES = 65536
PREFIX = "[offline-failure-parent-ids] "
SCHEMA = "nativecmpkit-offline-failure-parent-ids658-v1"
PHASES = ("startup", "retain-child", "wait-clock", "wait-output", "wait-guard",
          "wait-sleep", "cleanup", "post-cleanup-summary")
KINDS = ("FAIL", "ERROR")
LINE_OMISSIONS = ("not_parent_progress", "unqualified_progress", "credential_shaped_id",
                  "non_fail_error_progress", "non_utf8_line", "line_byte_cap",
                  "unterminated_fail_error_progress")
LIMITS = ("input_byte_cap", "line_cap", "line_byte_cap", "non_utf8_line",
          "unqualified_progress", "credential_shaped_id", "unique_id_cap", "public_byte_cap",
          "unterminated_fail_error_progress")
FIELDS = ("sample_prefix_bytes", "input_bytes_omitted", "scanned_prefix_bytes",
          "prefix_bytes_uninspected", "scanned_lines", "line_omission_counts",
          "observed_parent_token_counts", "retained_parent_token_counts",
          "omitted_parent_token_counts", "omitted_for_unique_id_cap",
          "omitted_for_public_byte_cap", "omitted_unterminated_suffix_candidate_counts",
          "retained_unique_parent_ids", "unique_ids_omitted_for_public_byte_cap",
          "unique_ids_omitted_at_id_cap", "limits_observed", "records")
_ID = re.compile(qualified._IDENTIFIER + r"(?:\." + qualified._IDENTIFIER + r")+\Z")


def _valid_id(identifier):
    return (type(identifier) is str and identifier.isascii() and len(identifier) <= MAX_ID_BYTES
            and _ID.fullmatch(identifier) is not None
            and identifier.rsplit(".", 1)[-1].startswith("test_")
            and qualified._CREDENTIAL.search(identifier) is None)


def observe_failure_parent_ids(output):
    """Count observations, retaining at most 256 distinct qualified parent IDs.

    Only newline-terminated FAIL/ERROR lines qualify. Unterminated exact suffixes
    are omitted candidate counts, not qualified tokens or retained IDs. Omitted
    qualified token counts are exact within the scanned prefix. Distinct IDs beyond
    the ID cap are deliberately not retained/countable; None is not zero. Bytes
    beyond byte/line caps are counted as uninspected, never scanned for more IDs.
    """
    if type(output) is not bytes:
        raise ValueError("Failure parent observation requires original byte data")
    prefix = output[:MAX_INPUT_BYTES]
    limits = {name: False for name in LIMITS}
    limits["input_byte_cap"] = len(output) > MAX_INPUT_BYTES
    omitted_lines = {name: 0 for name in LINE_OMISSIONS}
    totals, omitted_ids, unterminated = ({kind: 0 for kind in KINDS} for _ in range(3))
    records, scanned_bytes, scanned_lines = {}, 0, 0
    for index, raw in enumerate(io.BytesIO(prefix)):
        if index >= MAX_LINES:
            limits["line_cap"] = True
            break
        scanned_bytes += len(raw)
        scanned_lines += 1
        if len(raw) > MAX_LINE_BYTES:
            limits["line_byte_cap"] = True
            omitted_lines["line_byte_cap"] += 1
            continue
        try:
            line = raw.decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            limits["non_utf8_line"] = True
            omitted_lines["non_utf8_line"] += 1
            continue
        # Exact original711 parent grammar: no ANSI/lstrip/subtest/message parsing.
        if not line.startswith("test_"):
            omitted_lines["not_parent_progress"] += 1
            continue
        match = qualified._PROGRESS.fullmatch(line)
        if match is None or any(ord(char) < 32 or ord(char) == 127 for char in line):
            limits["unqualified_progress"] = True
            omitted_lines["unqualified_progress"] += 1
            continue
        display, identifier, suffix = match.groups()
        if (not identifier.isascii() or len(identifier) > MAX_ID_BYTES
                or display != identifier.rsplit(".", 1)[-1]):
            limits["unqualified_progress"] = True
            omitted_lines["unqualified_progress"] += 1
            continue
        if qualified._CREDENTIAL.search(identifier):
            limits["credential_shaped_id"] = True
            omitted_lines["credential_shaped_id"] += 1
            continue
        if suffix not in (" FAIL", " ERROR"):
            omitted_lines["non_fail_error_progress"] += 1
            continue
        kind = suffix[1:]
        if not raw.endswith(b"\n"):
            unterminated[kind] += 1
            omitted_lines["unterminated_fail_error_progress"] += 1
            limits["unterminated_fail_error_progress"] = True
            continue
        totals[kind] += 1
        if identifier in records:
            records[identifier][kind] += 1
        elif len(records) < MAX_UNIQUE_IDS:
            records[identifier] = {"parent_id": identifier, "FAIL": int(kind == "FAIL"),
                                   "ERROR": int(kind == "ERROR")}
        else:
            limits["unique_id_cap"] = True
            omitted_ids[kind] += 1
    kept = {kind: totals[kind] - omitted_ids[kind] for kind in KINDS}
    return {"sample_prefix_bytes": len(prefix), "input_bytes_omitted": len(output) - len(prefix),
            "scanned_prefix_bytes": scanned_bytes, "prefix_bytes_uninspected": len(prefix) - scanned_bytes,
            "scanned_lines": scanned_lines, "line_omission_counts": omitted_lines,
            "observed_parent_token_counts": totals, "retained_parent_token_counts": kept,
            "omitted_parent_token_counts": dict(omitted_ids), "omitted_for_unique_id_cap": omitted_ids,
            "omitted_for_public_byte_cap": {kind: 0 for kind in KINDS},
            "omitted_unterminated_suffix_candidate_counts": unterminated,
            "retained_unique_parent_ids": len(records), "unique_ids_omitted_for_public_byte_cap": 0,
            "unique_ids_omitted_at_id_cap": None if limits["unique_id_cap"] else 0,
            "limits_observed": limits, "records": list(records.values())}


def _valid_observation(found, output):
    """Reject unknown/miswired metadata rather than serialize private values."""
    if type(found) is not dict or set(found) != set(FIELDS):
        return False
    prefix_bytes = min(len(output), MAX_INPUT_BYTES)
    for name in ("sample_prefix_bytes", "input_bytes_omitted", "scanned_prefix_bytes",
                 "prefix_bytes_uninspected", "scanned_lines", "retained_unique_parent_ids",
                 "unique_ids_omitted_for_public_byte_cap"):
        if type(found[name]) is not int or found[name] < 0:
            return False
    if (found["sample_prefix_bytes"] != prefix_bytes
            or found["input_bytes_omitted"] != len(output) - prefix_bytes
            or found["scanned_prefix_bytes"] + found["prefix_bytes_uninspected"] != prefix_bytes
            or found["scanned_lines"] > MAX_LINES
            or found["retained_unique_parent_ids"] > MAX_UNIQUE_IDS
            or found["unique_ids_omitted_for_public_byte_cap"] != 0):
        return False
    limits = found["limits_observed"]
    if (type(limits) is not dict or set(limits) != set(LIMITS)
            or any(type(value) is not bool for value in limits.values())
            or limits["input_byte_cap"] != (len(output) > MAX_INPUT_BYTES)
            or limits["public_byte_cap"] is not False):
        return False
    omitted = found["line_omission_counts"]
    if (type(omitted) is not dict or set(omitted) != set(LINE_OMISSIONS)
            or any(type(value) is not int or not 0 <= value <= MAX_LINES for value in omitted.values())):
        return False
    for name in ("observed_parent_token_counts", "retained_parent_token_counts",
                 "omitted_parent_token_counts", "omitted_for_unique_id_cap",
                 "omitted_for_public_byte_cap", "omitted_unterminated_suffix_candidate_counts"):
        values = found[name]
        if (type(values) is not dict or set(values) != set(KINDS)
                or any(type(value) is not int or not 0 <= value <= MAX_LINES for value in values.values())):
            return False
    if (sum(omitted.values()) > found["scanned_lines"]
            or found["scanned_lines"] > found["scanned_prefix_bytes"]
            or (found["scanned_lines"] == 0) != (found["scanned_prefix_bytes"] == 0)
            or limits["line_cap"] != (found["prefix_bytes_uninspected"] > 0)
            or any(limits[name] != (omitted[name] > 0) for name in
                   ("line_byte_cap", "non_utf8_line", "unqualified_progress", "credential_shaped_id",
                    "unterminated_fail_error_progress"))
            or sum(found["omitted_unterminated_suffix_candidate_counts"].values()) > 1
            or sum(found["omitted_unterminated_suffix_candidate_counts"].values()) != omitted["unterminated_fail_error_progress"]
            or (found["prefix_bytes_uninspected"] > 0
                and sum(found["omitted_unterminated_suffix_candidate_counts"].values()) != 0)):
        return False
    records = found["records"]
    if type(records) is not list or len(records) != found["retained_unique_parent_ids"]:
        return False
    seen, retained = set(), {kind: 0 for kind in KINDS}
    for row in records:
        if (type(row) is not dict or set(row) != {"parent_id", *KINDS}
                or not _valid_id(row["parent_id"]) or row["parent_id"] in seen
                or any(type(row[kind]) is not int or not 0 <= row[kind] <= MAX_LINES for kind in KINDS)
                or sum(row[kind] for kind in KINDS) == 0):
            return False
        seen.add(row["parent_id"])
        for kind in KINDS:
            retained[kind] += row[kind]
    if retained != found["retained_parent_token_counts"]:
        return False
    if sum(found["observed_parent_token_counts"].values()) + sum(omitted.values()) != found["scanned_lines"]:
        return False
    for kind in KINDS:
        if (found["omitted_for_public_byte_cap"][kind] != 0
                or found["omitted_parent_token_counts"][kind] != found["omitted_for_unique_id_cap"][kind]
                or retained[kind] + found["omitted_parent_token_counts"][kind] != found["observed_parent_token_counts"][kind]):
            return False
    cap = sum(found["omitted_for_unique_id_cap"].values()) > 0
    return (limits["unique_id_cap"] == cap
            and (not cap or len(records) == MAX_UNIQUE_IDS)
            and (found["unique_ids_omitted_at_id_cap"] is None if cap
                 else type(found["unique_ids_omitted_at_id_cap"]) is int and found["unique_ids_omitted_at_id_cap"] == 0))


def emit_failure_parent_ids(output, *, scope_index, phase, sampled_after_refusal, stream):
    """One <=64KiB JSON from that same buffer; refusal never changes the primary."""
    try:
        if (type(scope_index) is not int or not 1 <= scope_index <= 10
                or type(phase) is not str or phase not in PHASES
                or type(sampled_after_refusal) is not bool
                or type(output) is not bytes or len(output) > MAX_INPUT_BYTES + 1):
            return False
        found = observe_failure_parent_ids(output)
        if not _valid_observation(found, output):
            return False
        record = {"schema": SCHEMA, "diagnostic_only": True, "scope_index": scope_index,
                  "phase": phase, "sample_is_after_refusal": sampled_after_refusal,
                  "stream_observation": "same-original-merged-stdout-stderr-prefix",
                  "complete_output": False, "incomplete": True,
                  "identities_authenticated": False, "identities_current_or_completed_tests": False,
                  "identities_failure_causes": False,
                  "counts_are_parent_token_observations_not_tests": True,
                  "only_newline_terminated_parent_ids_retained": True,
                  "unterminated_suffix_counts_are_omitted_unqualified_candidates": True,
                  "omitted_counts_are_observations_not_unique_ids": True,
                  "raw_messages_parameters_environment_tracebacks_exported": False,
                  "reusable_certificate": False, "inventory": found}
        while True:
            record["capped"] = any(found["limits_observed"][name] for name in
                                  ("input_byte_cap", "line_cap", "line_byte_cap", "unique_id_cap", "public_byte_cap"))
            line = PREFIX + json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            if len((line + "\n").encode("ascii")) <= MAX_PUBLIC_BYTES:
                public = line + "\n"
                if type(written := stream.write(public)) is not int or written != len(public):
                    return False  # No retry/repair of an unknown or partial secondary stream write.
                stream.flush()
                return True
            if not found["records"]:
                return False  # Never truncate into invalid JSON or discard the omission counters.
            row = found["records"].pop()
            found["retained_unique_parent_ids"] -= 1
            found["unique_ids_omitted_for_public_byte_cap"] += 1
            found["limits_observed"]["public_byte_cap"] = True
            for kind in KINDS:
                found["retained_parent_token_counts"][kind] -= row[kind]
                found["omitted_parent_token_counts"][kind] += row[kind]
                found["omitted_for_public_byte_cap"][kind] += row[kind]
    except BaseException:
        return False
