# SPDX-License-Identifier: Apache-2.0
"""The failed bar-case compiler receipt is not native or whole-issue acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ios_popover_anchor_plan import RECEIPT, SOURCES, _ordinary_bytes, _unique_object

FOCUS = "ui-native-popover-bar-recovery"


def validate_compilation(root: Path, started_ns: int, ended_ns: int) -> bool:
    """Require this exact new focus; all native/XML/runtime/cleanup gates still apply."""
    if type(started_ns) is not int or type(ended_ns) is not int or started_ns <= 0 or ended_ns < started_ns:
        return False
    try:
        raw, info = _ordinary_bytes(root, RECEIPT)
        if not started_ns - 2_000_000_000 <= info.st_mtime_ns <= ended_ns + 2_000_000_000:
            return False
        document = json.loads(raw, object_pairs_hook=_unique_object,
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite compiler receipt")))
        expected = {
            "task": ":calf-ui:compileTestKotlinIosSimulatorArm64",
            "focus": FOCUS,
            "source_sha256": {name: hashlib.sha256(_ordinary_bytes(root, name)[0]).hexdigest() for name in SOURCES},
            "effective_sources": list(SOURCES),
            "excluded_unrelated_test_sources": True,
            "production_source_sets_changed": False,
            "native_tests_executed": 0,
            "scope": "Actual precompiler source admission only; compiler exit and fresh native XML decide outcomes",
        }
        return (type(document) is dict and document == expected and
                type(document.get("native_tests_executed")) is int and
                type(document.get("excluded_unrelated_test_sources")) is bool and
                type(document.get("production_source_sets_changed")) is bool)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return False
