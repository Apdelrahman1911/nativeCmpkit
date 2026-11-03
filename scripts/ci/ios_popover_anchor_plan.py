# SPDX-License-Identifier: Apache-2.0
"""Fresh focused-compiler admission, not native or rotation/split-view acceptance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat

FOCUS = "ui-native-popover-anchor"
SOURCES = (
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/dialog/NativePopoverAnchorTest.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeXcuiInput.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeUiApplicationHost.kt",
    "calf-ui/src/iosTest/kotlin/com/mohamedrejeb/calf/ui/internal/NativeObjectIdentity.kt",
)
RECEIPT = "build/ci-verification/ios-focused-compilation.json"
MAX_BYTES = 2 * 1024 * 1024


def _ordinary_bytes(root: Path, relative: str):
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("An exact confined ordinary compiler input is required")
    file = root / path
    if file.absolute() != file.resolve(strict=True) or not file.resolve().is_relative_to(root.resolve()):
        raise ValueError("Aliased compiler inputs are forbidden")
    before = file.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= MAX_BYTES:
        raise ValueError("An ordinary bounded compiler input is required")
    raw = file.read_bytes()
    after = file.lstat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_nlink", "st_mode")
    if any(getattr(before, key) != getattr(after, key) for key in fields) or len(raw) != before.st_size:
        raise ValueError("Compiler input changed while reading")
    return raw, before


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate compiler receipt fields are forbidden")
        result[key] = value
    return result


def validate_compilation(root: Path, started_ns: int, ended_ns: int) -> bool:
    """Fail closed; the independent application/XML/runtime/cleanup gates still apply."""
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
        # Python bool is an int subclass; JSON true is not zero native executions.
        return (type(document) is dict and document == expected and
                type(document.get("native_tests_executed")) is int and
                type(document.get("excluded_unrelated_test_sources")) is bool and
                type(document.get("production_source_sets_changed")) is bool)
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        return False
