"""Parse an actual root-daemon marker. No shell java-version inference or paths."""
from __future__ import annotations
import json
from pathlib import Path

PREFIX = "NATIVECMPKIT_DAEMON_JVM "
FIELDS = {"schema_version", "major", "java_version", "java_vendor", "runtime_version", "gradle_version",
          "launcher_home_configured", "launcher_home_matches_daemon"}


def unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate daemon observation field")
        result[key] = value
    return result


def observation(log: Path) -> dict:
    records = []
    with log.open(encoding="utf-8", errors="strict") as source:
        for line in source:
            if line.startswith(PREFIX):
                if len(line) > 4096 or records:
                    raise ValueError("Expected exactly one bounded real root-daemon marker")
                records.append(json.loads(line[len(PREFIX):], object_pairs_hook=unique_object))
    if len(records) != 1:
        raise ValueError("Actual root-daemon observation is missing")
    result = records[0]
    if not isinstance(result, dict) or set(result) != FIELDS:
        raise ValueError("Unexpected daemon observation schema")
    if type(result["schema_version"]) is not int or result["schema_version"] != 1 or type(result["major"]) is not int or result["major"] != 17:
        raise ValueError("Verification requires a recorded actual JDK17 daemon")
    for key in ("java_version", "java_vendor", "runtime_version", "gradle_version"):
        if not isinstance(result[key], str) or not 0 < len(result[key]) <= 128 or any(ord(c) < 32 for c in result[key]):
            raise ValueError("Invalid bounded daemon version/vendor observation")
    if type(result["launcher_home_configured"]) is not bool or (
        result["launcher_home_configured"] and type(result["launcher_home_matches_daemon"]) is not bool
    ) or (not result["launcher_home_configured"] and result["launcher_home_matches_daemon"] is not None):
        raise ValueError("Daemon/launcher correspondence must be an actual boolean observation")
    return result
