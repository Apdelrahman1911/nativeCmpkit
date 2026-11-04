# SPDX-License-Identifier: Apache-2.0
"""Exact image-launch ingress for offline source/history controls only.

One newest raw boundary precedes the unchanged calendar, camera and launcher
pins. Nested readers only peel the complete image or pass a fixed pinned
ancestor. No native selector executes reconstructed source, and no old pin,
observer, launch, deadline, finally or unknown-observation behavior is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

ROOT = Path(__file__).resolve().parents[2]
SPEC_RELATIVE = "scripts/ci/fixtures/apple-image-launcher-source-inverse.json"
SPEC_PATH = Path(__file__).parent / "fixtures/apple-image-launcher-source-inverse.json"
SPEC_SHA256 = "7fd94a3f2249840fb61a6cbe835bc8d3fe0809951dd3e3ed77cb33f422f55cef"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_SPEC_BYTES = 512 * 1024
LAUNCHER = "scripts/ci/ios_ui_application.py"
SELECTOR = "scripts/ci/calendar_share_selector_source_projection.py"
CONTROL = "scripts/ci/test_calendar_share_selector_source_projection.py"
BOUND_PATHS = {LAUNCHER, SELECTOR, CONTROL}
ADDED_PATHS = {
    "scripts/ci/apple_image_launch_readiness.py",
    "scripts/ci/test_apple_image_launch_readiness.py",
}
# Only existing whole-launcher pins, not a query of Git or arbitrary history.
# The raw boundary below rejects every one of these as a current image.
PINNED_LAUNCHER_ANCESTORS = {
    "4e407426bc8535ea547eb5fbee74f7a801c87f222add88de94e26966f65690ae",
    "edc4e95464413288a15693fc4398c7502ff6de9db72d27731ca6dabd753c4b3a",
    "8b86b780e6745ae289bfd64acaf3b51c8272633a11b6a1292c5fe3257501dc2c",
    "92f2ce889f6b5cc31e6319584dd1385c403b416f23ae94db0ba895cc55c9bce6",
    "42056448d9f023ab3c136d164956350900117a30610457c91ee0b16de85f3244",
}


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate image-launch ingress manifest field")
        result[key] = value
    return result


def _document():
    before = SPEC_PATH.lstat()
    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or
            not 0 < before.st_size <= MAX_SPEC_BYTES):
        raise ValueError("One ordinary bounded image-launch ingress manifest is required")
    from ios_popover_anchor_plan import _ordinary_bytes
    raw = _ordinary_bytes(SPEC_PATH.parent, SPEC_PATH.name)[0]
    if not 0 < len(raw) <= MAX_SPEC_BYTES or hashlib.sha256(raw).hexdigest() != SPEC_SHA256:
        raise ValueError("The exact image-launch ingress manifest changed")
    document = json.loads(raw, object_pairs_hook=_unique)
    if (type(document) is not dict or type(document.get("schema_version")) is not int or
            document["schema_version"] != 1 or type(document.get("bindings")) is not dict or
            set(document["bindings"]) != BOUND_PATHS or
            type(document.get("added_inputs")) is not dict or set(document["added_inputs"]) != ADDED_PATHS or
            type(document.get("unchanged_inputs")) is not dict):
        raise ValueError("The exact finite image-launch ingress manifest schema is required")
    for name, row in document["bindings"].items():
        if (type(row) is not dict or any(type(row.get(key)) is not int or
                not 0 < row[key] <= MAX_SOURCE_BYTES for key in ("before_bytes", "after_bytes")) or
                any(type(row.get(key)) is not str or not re.fullmatch(r"[0-9a-f]{64}", row[key])
                    for key in ("before_sha256", "after_sha256")) or
                type(row.get("fragments")) is not list or not 0 < len(row["fragments"]) <= 8):
            raise ValueError("Exact complete image-launch ingress bindings are required")
    return document


def _identity(relative, payload):
    if type(relative) is not str or type(payload) is not bytes:
        raise ValueError("Exact image-launch source identity and ordinary bytes are required")


def source_before_image_launch(relative, payload):
    """Complete exact inverse, or its one exact preimage; never raw admission."""
    _identity(relative, payload)
    from ios_ui_related_source_projection import peel_ui_related_for_history
    payload = peel_ui_related_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # Unlisted bytes are not certified, guessed or rewritten.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded image-launch source bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload  # Exact ancestor idempotence only.
    if observed != binding["after_sha256"] or len(payload) != binding["after_bytes"]:
        raise ValueError("Unreviewed image-launch source is not its complete afterimage")
    restored = payload
    for fragment in reversed(binding["fragments"]):
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if (not before or not after or
                hashlib.sha256(before).hexdigest() != fragment["before_fragment_sha256"] or
                hashlib.sha256(after).hexdigest() != fragment["after_fragment_sha256"] or
                restored.count(after) != 1):
            raise ValueError("Exact finite unique image-launch inverse fragments are required")
        restored = restored.replace(after, before, 1)
    if (hashlib.sha256(restored).hexdigest() != binding["before_sha256"] or
            len(restored) != binding["before_bytes"]):
        raise ValueError("Image-launch inverse did not restore its complete prior source")
    forward = restored
    for fragment in binding["fragments"]:
        before, after = fragment["before"].encode(), fragment["after"].encode()
        if forward.count(before) != 1:
            raise ValueError("Exact finite unique image-launch forward fragments are required")
        forward = forward.replace(before, after, 1)
    if forward != payload:
        raise ValueError("Image-launch complete source round trip differs")
    return restored


def current_source_before_image_launch(relative, payload):
    """The one raw ingress: old/partial/unknown images can never be current."""
    _identity(relative, payload)
    from ios_ui_related_source_projection import current_source_before_ui_related
    payload = current_source_before_ui_related(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is not None and (hashlib.sha256(payload).hexdigest() != binding["after_sha256"] or
                                len(payload) != binding["after_bytes"]):
        raise ValueError("An old/unknown image cannot replace exact current image-launch source")
    return source_before_image_launch(relative, payload)


def peel_image_launch_for_history(relative, payload):
    """Ancestor-only: fixed whole pins, never arbitrary historical fallback."""
    _identity(relative, payload)
    from ios_ui_related_source_projection import peel_ui_related_for_history
    payload = peel_ui_related_for_history(relative, payload)
    binding = _document()["bindings"].get(relative)
    if binding is None:
        return payload  # No admission for an unlisted identity.
    if not 0 < len(payload) <= MAX_SOURCE_BYTES:
        raise ValueError("Bounded image-launch ancestor bytes are required")
    observed = hashlib.sha256(payload).hexdigest()
    if observed == binding["after_sha256"]:
        return source_before_image_launch(relative, payload)
    if observed == binding["before_sha256"] and len(payload) == binding["before_bytes"]:
        return payload
    if relative == LAUNCHER and observed in PINNED_LAUNCHER_ANCESTORS:
        return payload  # Its next unchanged dated reader still owns acceptance.
    raise ValueError("Unknown image-launch bytes cannot satisfy exact current source or a fixed pinned ancestor")


def read_current_source_for_history(path: Path, root: Path):
    """New confined ordinary path boundary; the unchanged bridge admits once."""
    if (type(path) is not type(ROOT) or type(root) is not type(ROOT) or
            not root.is_absolute() or not path.is_absolute() or
            root.absolute() != root.resolve(strict=True)):
        raise ValueError("An exact ordinary image-launch checkout and path are required")
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        raise ValueError("A foreign image-launch path is not a checkout input") from None
    if relative not in BOUND_PATHS or path != root / relative:
        raise ValueError("Only the exact bound image-launch source path is admitted")
    from ios_popover_anchor_plan import _ordinary_bytes
    payload = _ordinary_bytes(root, relative)[0]
    import android_external328_source_projection as bridge
    return bridge.current_source_for_history(relative, payload)


def validate_current_sources(root: Path):
    """Latest complete input custody only, never compiler/native acceptance.

The implementation and NEW control have explicit independent source pins in
the NEW control and held review map, avoiding self-referential manifest hashes.
"""
    import ios_ui_related_source_projection as ui_history
    ui_history.validate_current_sources(root)
    document = _document()
    expected = ({name: row["after_sha256"] for name, row in document["bindings"].items()} |
                document["added_inputs"] | document["unchanged_inputs"] | {SPEC_RELATIVE: SPEC_SHA256})
    from ios_popover_anchor_plan import _ordinary_bytes
    for name, digest in expected.items():
        if hashlib.sha256(ui_history.peel_ui_related_for_history(name, _ordinary_bytes(root, name)[0])).hexdigest() != digest:
            raise ValueError("Current image-launch input differs from its exact owning image: " + name)
    return True
